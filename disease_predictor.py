"""
================================================================================
医疗疾病预测模块 - 症状预测疾病（命令行 + Flask 双模式）
================================================================================
功能：
1. 基于BERT语义理解的疾病检索
2. 混合评分系统（语义相似度 + 词面匹配 + 医学规则）
3. 单症状/多症状自适应优化
4. 完全匹配奖励 + 罕见病降权 + 常见病加权

技术栈：
- PyTorch + Transformers（BERT模型）
- 对比学习训练的双塔编码器
- IDF加权词面匹配
- 多层规则引擎

使用方式：
1. 命令行：python disease_predictor.py --query "头痛 发热" --topk 5
2. Flask：from disease_predictor import predict_disease

作者：Your Name
日期：2024-01-XX
版本：v3.1（完全匹配优化版）
================================================================================
"""

# ==================== 第1部分：依赖导入 ====================
import os  # 文件路径操作
import sys  # 系统参数（未使用，保留兼容性）
import json  # JSON数据解析（症状列表）
import argparse  # 命令行参数解析
import numpy as np  # 数值计算（向量操作）
import torch  # PyTorch深度学习框架
from transformers import (
    BertTokenizer,  # BERT分词器
    BertModel  # BERT预训练模型
)

# ==================== 第2部分：路径配置 ====================
"""
路径说明：
- PROJECT_ROOT: 项目根目录
- MODEL_DIR: 训练后的BERT模型目录（包含config.json、pytorch_model.bin等）
- INDEX_PATH: 疾病索引文件（包含所有疾病的BERT向量、名称、症状等）

⚠️  这些路径必须与训练脚本一致！
"""

# ==================== 第2部分：路径配置（相对路径版） ====================
# ==================== 第2部分：路径配置 ====================
"""
路径说明：
- SCRIPT_DIR: 当前脚本所在目录
- PROJECT_ROOT: 项目根目录（自动识别）
- MODEL_DIR: BERT模型目录
- INDEX_PATH: 疾病索引文件

⚠️  自动适配任何环境，无需手动修改！
"""
import os

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 项目根目录（假设脚本在项目根目录下）
PROJECT_ROOT = SCRIPT_DIR

# 模型目录（相对路径）
MODEL_DIR = os.path.join(PROJECT_ROOT, 'models', 'medical_biencoder', 'biencoder')

# 索引文件路径
INDEX_PATH = os.path.join(PROJECT_ROOT, 'models', 'medical_biencoder', 'biencoder_index.npz')


# ==================== 第3部分：超参数配置 ====================
"""
超参数说明：
- MAX_LEN: BERT输入序列的最大长度（超过会截断）
- FIELD_TAGS: 字段标记（用于区分症状/描述/病因/科室）

⚠️  必须与训练时的参数一致！
"""
MAX_LEN = 128  # BERT最大输入长度（token数）
FIELD_TAGS = ['[SYM]', '[DESC]', '[CAUSE]', '[CAT]']  # 症状、描述、病因、科室标记

# ==================== 第4部分：全局缓存 ====================
"""
全局缓存机制：
- 作用：避免每次预测都重新加载模型（减少启动时间）
- 实现：首次调用时加载，后续调用直接使用缓存
- 适用场景：Flask服务（多次调用predict_disease）

缓存变量：
- _tokenizer: BERT分词器
- _model: BERT模型
- _index_data: 疾病索引数据（NumPy数组）
"""
_tokenizer = None  # 分词器缓存
_model = None  # 模型缓存
_index_data = None  # 索引数据缓存

# ==================== 第5部分：工具函数 ====================

def mean_pooling(last_hidden_state, attention_mask):
    """
    平均池化（将BERT输出的序列向量转为单个向量）
    
    参数：
        last_hidden_state (Tensor): BERT最后一层隐藏状态
            形状：(batch_size, seq_len, hidden_dim)
            示例：(1, 128, 768) → 1个句子，128个token，每个token 768维向量
        
        attention_mask (Tensor): 注意力掩码
            形状：(batch_size, seq_len)
            示例：[1, 1, 1, 1, 0, 0, ...] → 前4个token有效，后面是padding
    
    返回：
        Tensor: 池化后的向量
            形状：(batch_size, hidden_dim)
            示例：(1, 768) → 1个句子的768维向量
    
    计算方法：
        1. 对非padding位置的向量求和
        2. 除以有效token数量（忽略padding）
    
    示例：
        输入：[CLS] 头 痛 [SEP] [PAD] [PAD]  (hidden_dim=768)
        输出：4个token的平均向量（忽略[PAD]）
    """
    # 1. 将attention_mask从2D扩展为3D：(batch, seq_len) → (batch, seq_len, 1)
    #    作用：便于与last_hidden_state逐元素相乘
    mask = attention_mask.unsqueeze(-1).float()
    
    # 2. 对有效位置的向量求和：(batch, seq_len, hidden_dim) → (batch, hidden_dim)
    #    mask * last_hidden_state：将padding位置的向量置零
    #    sum(dim=1)：对seq_len维度求和
    summed = (last_hidden_state * mask).sum(dim=1)
    
    # 3. 计算有效token数量：(batch, seq_len, 1) → (batch, 1)
    #    clamp(min=1e-9)：防止除以0（如果整句都是padding）
    counts = mask.sum(dim=1).clamp(min=1e-9)
    
    # 4. 返回平均向量：(batch, hidden_dim) / (batch, 1) → (batch, hidden_dim)
    return summed / counts

def format_query(tokens):
    """
    格式化用户查询（添加症状字段标记）
    
    参数：
        tokens (list[str]): 症状词列表
            示例：['头痛', '发热', '咳嗽']
    
    返回：
        str: 格式化后的查询文本
            示例："[SYM] 头痛 发热 咳嗽"
    
    作用：
        将用户输入的症状列表转换为BERT可理解的格式
        [SYM]标记告诉模型："后面的词是症状"
    
    示例：
        >>> format_query(['头痛', '发热'])
        '[SYM] 头痛 发热'
        
        >>> format_query([''])
        ''
    """
    # 1. 过滤空字符串
    tokens = [t for t in tokens if t]
    
    # 2. 如果没有有效token，返回空字符串
    if not tokens:
        return ''
    
    # 3. 添加[SYM]标记 + 拼接所有症状词
    return f"{FIELD_TAGS[0]} " + ' '.join(tokens)

def _tokens_from_query_text(text):
    """
    从查询文本中提取症状词（去除字段标记）
    
    参数：
        text (str): 格式化后的查询文本
            示例："[SYM] 头痛 发热 [SEP] [DESC]"
    
    返回：
        list[str]: 纯症状词列表
            示例：['头痛', '发热']
    
    作用：
        用于词面匹配时，去除格式标记，只保留实际症状词
    
    示例：
        >>> _tokens_from_query_text("[SYM] 头痛 发热")
        ['头痛', '发热']
        
        >>> _tokens_from_query_text("[SYM] 头痛 [SEP] [DESC] 常见症状")
        ['头痛', '常见症状']  # ⚠️ 会保留描述内容（但实际使用中不会传入描述）
    """
    # 遍历所有token，过滤掉字段标记和分隔符
    return [
        t for t in text.strip().split()  # 按空格分割
        if t not in FIELD_TAGS  # 排除 [SYM]、[DESC]、[CAUSE]、[CAT]
        and t != '[SEP]'  # 排除分隔符
    ]

def _char_ngrams(s, n=2):
    """
    生成字符级n-gram集合（用于模糊匹配）
    
    参数：
        s (str): 输入字符串
            示例："偏头痛"
        n (int): n-gram长度（默认2）
    
    返回：
        set[str]: n-gram集合
            示例：{"偏头", "头痛"}
    
    作用：
        将词拆分为字符级的滑动窗口片段，用于计算字符重叠度
        适用场景：用户输入"偏头痛"，数据库有"头痛"，可以部分匹配
    
    示例：
        >>> _char_ngrams("头痛", 2)
        {'头痛'}
        
        >>> _char_ngrams("偏头痛", 2)
        {'偏头', '头痛'}
        
        >>> _char_ngrams("急性肺炎", 2)
        {'急性', '性肺', '肺炎'}
    """
    # 1. 去除标点符号和空格
    s = str(s).replace('、', '').replace('，', '').replace('。', '').replace(' ', '')
    
    # 2. 处理空字符串或长度小于n的字符串
    if not s or len(s) < n:
        return {s} if s else set()  # 返回整个字符串或空集合
    
    # 3. 生成滑动窗口n-gram
    # 示例："偏头痛" (n=2) → i=0: "偏头", i=1: "头痛"
    return {s[i:i+n] for i in range(len(s) - n + 1)}

def _lexical_score(query_tokens, doc_symptoms, mode='fuzzy', idf=None):
    """
    计算词面匹配得分（支持多种模式）
    
    参数：
        query_tokens (list[str]): 查询症状词列表
            示例：['头痛', '发热']
        
        doc_symptoms (list[str]): 文档症状词列表
            示例：['头痛', '发烧', '咽痛']
        
        mode (str): 匹配模式
            - 'none': 禁用词面匹配（纯语义检索）
            - 'exact': 精确匹配（Jaccard相似度）
            - 'wexact': 加权精确匹配（IDF加权Jaccard）
            - 'fuzzy': 模糊匹配（字符级2-gram Jaccard）
        
        idf (dict): IDF权重字典
            示例：{'头痛': 1.5, '发热': 2.0, ...}
            作用：常见症状权重低，罕见症状权重高
    
    返回：
        float: 词面匹配得分（范围0~1）
    
    模式详解：
    
    1️⃣  精确匹配（exact）：
        公式：Jaccard = |Q ∩ D| / |Q ∪ D|
        示例：
            Q = {'头痛', '发热'}
            D = {'头痛', '咽痛'}
            交集 = {'头痛'} → |交集| = 1
            并集 = {'头痛', '发热', '咽痛'} → |并集| = 3
            Jaccard = 1/3 = 0.333
    
    2️⃣  加权精确匹配（wexact）：
        公式：Jaccard = Σ_i IDF(word_i) for word_i in (Q∩D) / Σ_i IDF(word_i) for word_i in (Q∪D)
        示例：
            Q = {'头痛', '发热'}
            D = {'头痛', '咽痛'}
            IDF = {'头痛':1.5, '发热':2.0, '咽痛':2.5}
            交集加权和 = IDF('头痛') = 1.5
            并集加权和 = IDF('头痛') + IDF('发热') + IDF('咽痛') = 1.5+2.0+2.5 = 6.0
            Jaccard = 1.5/6.0 = 0.25
    
    3️⃣  模糊匹配（fuzzy）：
        公式：将每个词转为字符级2-gram，然后计算Jaccard
        示例：
            Q = {'偏头痛'}
            D = {'头痛'}
            Q_ngrams = {'偏头', '头痛'}
            D_ngrams = {'头痛'}
            Jaccard = |{'头痛'}| / |{'偏头', '头痛'}| = 1/2 = 0.5
    """
    # 1. 过滤空字符串
    q_tokens = [t for t in query_tokens if t]
    d_tokens = [t for t in doc_symptoms if t]
    
    # 2. 如果任一为空，返回0
    if not q_tokens or not d_tokens:
        return 0.0

    # 3. 禁用词面匹配
    if mode == 'none':
        return 0.0

    # 4. 精确匹配（Jaccard相似度）
    if mode == 'exact':
        q_set, d_set = set(q_tokens), set(d_tokens)  # 转为集合（去重）
        inter, union = len(q_set & d_set), len(q_set | d_set)  # 交集和并集大小
        return (inter / union) if union > 0 else 0.0

    # 5. 加权精确匹配（IDF加权Jaccard）
    if mode == 'wexact':
        q_set, d_set = set(q_tokens), set(d_tokens)
        inter, union = q_set & d_set, q_set | d_set  # 交集和并集
        
        if not union:
            return 0.0
        
        def wsum(ts):
            """计算词集合的IDF加权和"""
            if not idf:
                return float(len(ts))  # 没有IDF时，使用词数
            # 对每个词查询IDF，取最大值为0（防止负数）
            return sum(max(0.0, float(idf.get(t, 0.0))) for t in ts)
        
        # 加权Jaccard = 交集加权和 / 并集加权和
        return (wsum(inter) / max(1e-9, wsum(union)))

    # 6. 模糊匹配（字符级2-gram Jaccard）
    # 场景：用户输入"偏头痛"，数据库有"头痛"，应该部分匹配
    q_ngrams = set()
    for t in q_tokens:
        q_ngrams |= _char_ngrams(t, 2)  # 合并所有词的2-gram
    
    d_ngrams = set()
    for t in d_tokens:
        d_ngrams |= _char_ngrams(t, 2)
    
    if not q_ngrams or not d_ngrams:
        return 0.0
    
    inter = len(q_ngrams & d_ngrams)  # 交集大小
    union = len(q_ngrams | d_ngrams)  # 并集大小
    return (inter / union) if union > 0 else 0.0

# ==================== 第6部分：模型加载 ====================

def load_model():
    """
    加载BERT模型和疾病索引（带缓存机制）
    
    返回：
        tuple: (tokenizer, model, index_data)
            - tokenizer: BertTokenizer实例
            - model: BertModel实例（已移动到GPU/CPU）
            - index_data: dict-like对象（包含embeddings、names、symptoms等）
    
    缓存机制：
        1. 首次调用：加载模型并缓存到全局变量
        2. 后续调用：直接返回缓存（避免重复加载）
        3. 适用场景：Flask服务（多次预测）
    
    加载内容：
        1. 疾病索引（.npz文件）：
           - embeddings: 所有疾病的BERT向量 (N, 768)
           - names: 疾病名称列表
           - categories: 科室列表
           - symptoms: 症状列表（JSON字符串）
           - idf_terms: IDF词表
           - idf_vals: IDF值
        
        2. BERT模型：
           - config.json: 模型配置
           - pytorch_model.bin: 模型权重
           - vocab.txt: 词表
    
    异常处理：
        - FileNotFoundError: 索引文件或模型目录不存在
    
    示例：
        >>> tok, enc, data = load_model()
        🔍 检查路径...
           模型目录: C:\...\biencoder
           索引文件: C:\...\biencoder_index.npz
        ✅ 路径检查通过
        ✅ 加载索引: 8807 个疾病
        ✅ 模型加载完成 (设备: cpu)
    """
    global _tokenizer, _model, _index_data  # 声明使用全局变量
    
    # ===== 检查缓存 =====
    if _tokenizer is not None:
        # 已缓存，直接返回
        return _tokenizer, _model, _index_data
    
    # ===== 验证路径 =====
    print(f"🔍 检查路径...")
    print(f"   模型目录: {MODEL_DIR}")
    print(f"   索引文件: {INDEX_PATH}")
    
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError(f'索引文件不存在: {INDEX_PATH}')
    
    if not os.path.isdir(MODEL_DIR):
        raise FileNotFoundError(f'模型目录不存在: {MODEL_DIR}')
    
    print("✅ 路径检查通过")
    
    # ===== 加载索引文件 =====
    # np.load返回一个dict-like对象，可以用data['key']访问
    _index_data = np.load(INDEX_PATH, allow_pickle=True)
    print(f"✅ 加载索引: {len(_index_data['names'])} 个疾病")
    
    # ===== 加载BERT模型 =====
    # 1. 加载分词器（从训练后的模型目录）
    _tokenizer = BertTokenizer.from_pretrained(
        MODEL_DIR,
        local_files_only=True  # 仅使用本地文件（不从HuggingFace下载）
    )
    
    # 2. 加载BERT模型（从训练后的模型目录）
    _model = BertModel.from_pretrained(
        MODEL_DIR,
        local_files_only=True
    )
    
    # 3. 添加字段标记到分词器（训练时添加的特殊token）
    _tokenizer.add_special_tokens({
        'additional_special_tokens': FIELD_TAGS  # ['[SYM]', '[DESC]', '[CAUSE]', '[CAT]']
    })
    
    # 4. 调整模型嵌入层维度（匹配新词表大小）
    _model.resize_token_embeddings(len(_tokenizer))
    
    # 5. 移动到设备并设置为评估模式
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    _model.to(device).eval()  # .eval()禁用dropout
    print(f"✅ 模型加载完成 (设备: {device})")
    
    # ===== 返回缓存 =====
    return _tokenizer, _model, _index_data

# ==================== 第7部分：核心预测函数 ====================

@torch.no_grad()  # 禁用梯度计算（推理模式，节省显存）
def predict_disease(
    symptoms,  # 用户输入的症状文本
    topk=5,  # 返回前K个结果
    min_score=0.3,  # 最低相似度阈值
    alpha=0.7,  # 语义权重（已废弃，保留兼容性）
    lexical='fuzzy',  # 词面匹配模式
    return_dict=False  # 返回格式（False=纯文本，True=字典列表）
):
    """
    症状预测疾病（混合系统：BERT语义 + 词面匹配 + 医学规则）
    
    参数详解：
    ========
    symptoms (str): 用户输入的症状文本
        格式：空格分隔的症状词
        示例：
            - "头痛 发热"
            - "头痛 发热 咳嗽"
            - "胸痛 呼吸困难 气短"
    
    topk (int): 返回前K个结果
        默认：5
        范围：1~100
        说明：根据最终得分排序后，返回前K个疾病
    
    min_score (float): 最低相似度阈值
        默认：0.3（30%）
        范围：0.0~1.0
        说明：过滤掉得分低于此值的结果
        建议：
            - 0.25：宽松（召回高，准确率低）
            - 0.30：平衡（推荐）
            - 0.40：严格（召回低，准确率高）
    
    alpha (float): 语义权重（已废弃）
        ⚠️  当前版本此参数无效（保留兼容性）
        原逻辑：final = alpha*语义 + (1-alpha)*词面
        新逻辑：final = 语义（规则引擎直接调整）
    
    lexical (str): 词面匹配模式
        可选值：
            - 'fuzzy': 模糊匹配（字符级2-gram Jaccard）
            - 'exact': 精确匹配（Jaccard相似度）
            - 'wexact': 加权精确匹配（IDF加权Jaccard）
            - 'none': 禁用词面匹配（纯语义检索）
        推荐：'fuzzy'（兼顾精确和容错）
    
    return_dict (bool): 返回格式
        - False（默认）: 返回纯文本字符串（命令行用）
        - True: 返回字典列表（Flask API用）
    
    返回值：
    ======
    - return_dict=False时：
        str: 格式化的纯文本字符串
        示例：
            ```
            🔍 查询: 头痛 发热
             1. 感冒  [呼吸内科]  相似度: 0.7234
                症状: 头痛、发热、咳嗽、鼻塞、流涕
             2. 流感  [呼吸内科]  相似度: 0.6891
                症状: 发热、头痛、全身酸痛
            ```
    
    - return_dict=True时：
        list[dict]: 疾病列表
        示例：
            ```python
            [
                {
                    'name': '感冒',
                    'category': '呼吸内科',
                    'score': 0.7234,
                    'semantic_score': 0.6543,
                    'lexical_score': 0.3456,
                    'symptoms': ['头痛', '发热', '咳嗽', '鼻塞', '流涕']
                },
                ...
            ]
            ```
    
    预测流程：
    ========
    1️⃣  加载模型和索引
    2️⃣  编码查询文本（BERT向量）
    3️⃣  计算语义相似度（余弦相似度）
    4️⃣  计算词面匹配得分
    5️⃣  融合基础分数
    6️⃣  应用医学规则引擎：
        - 单症状查询：常见病加权
        - 多症状查询：完全匹配奖励 + 非核心病降权
        - 通用规则：罕见病降权 + 专科病降权 + 常见病加权
    7️⃣  排序并返回Top-K
    
    示例用法：
    =========
    命令行：
        >>> result = predict_disease("头痛 发热", topk=5, min_score=0.3)
        >>> print(result)
    
    Flask API：
        >>> results = predict_disease("头痛 发热", topk=5, return_dict=True)
        >>> for r in results:
        >>>     print(f"{r['name']} - {r['score']:.2f}")
    """
    try:
        # ==================== 第1步：加载模型和索引 ====================
        tok, enc, data = load_model()
        
        # 提取索引数据
        embs = data['embeddings']  # (N, 768) 所有疾病的BERT向量
        names = data['names']  # (N,) 疾病名称数组
        cats = data['categories']  # (N,) 科室数组
        symps = [json.loads(s) for s in data['symptoms']]  # list[list[str]] 症状列表
        
        # 读取IDF字典（用于加权词面匹配）
        idf = {}
        if 'idf_terms' in data and 'idf_vals' in data:
            terms = data['idf_terms']  # 症状词表
            vals = data['idf_vals']  # 对应IDF值
            idf = {str(k): float(v) for k, v in zip(terms, vals)}
        
        # 获取设备
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # ==================== 第2步：编码查询文本 ====================
        # 1. 预处理：提取症状词
        raw_tokens = [t for t in symptoms.strip().split() if t]
        
        # 2. 格式化：添加字段标记
        wrapped_query = format_query(raw_tokens)  # "头痛 发热" → "[SYM] 头痛 发热"
        
        # 3. 分词编码
        enc_in = tok(
            [wrapped_query],  # 输入文本列表（batch_size=1）
            max_length=MAX_LEN,  # 最大长度128
            truncation=True,  # 超过最大长度时截断
            padding=True,  # padding到最大长度
            return_tensors='pt'  # 返回PyTorch张量
        )
        
        # 4. 移动到设备
        enc_in = {k: v.to(device) for k, v in enc_in.items()}
        
        # 5. BERT前向传播
        out = enc(**enc_in, return_dict=True)
        
        # 6. 平均池化 + L2归一化
        q = mean_pooling(out.last_hidden_state, enc_in['attention_mask'])
        q = torch.nn.functional.normalize(q, p=2, dim=1).cpu().numpy()[0]
        # q: (768,) 查询向量（已L2归一化）
        
        # ==================== 第3步：计算语义相似度 ====================
        # 余弦相似度 = 向量点积（因为已L2归一化）
        sims = embs @ q  # (N,) 所有疾病与查询的相似度
        
        # ==================== 第4步：计算词面匹配得分 ====================
        q_tokens = _tokens_from_query_text(wrapped_query)  # 提取症状词
        lex_scores = np.zeros_like(sims)  # (N,) 初始化为0
        
        for i, s in enumerate(symps):
            lex_scores[i] = _lexical_score(q_tokens, s, mode=lexical, idf=idf)
        
        # ==================== 第5步：融合基础分数 ====================
        # ⚠️  原逻辑：final = alpha*语义 + (1-alpha)*词面
        # ✅  新逻辑：仅使用语义分（规则引擎会调整）
        final_scores = sims  # (N,) 基础分 = 语义相似度
        
        # 转换为集合（用于后续规则判断）
        q_token_set = set(q_tokens)
        
        # ==================== 第6步：医学规则引擎 ====================
        
        # ===== 🎯 规则1：单症状查询特殊处理 =====
        if len(q_token_set) == 1:
            """
            单症状策略：
            - 用户只输入一个症状时（如"头痛"），倾向于返回常见病
            - 原因：单症状信息量少，应避免推荐罕见病
            
            实现：
            - 定义【症状→常见病集合】映射
            - 如果疾病在集合中，加权 × 1.50（+50%）
            """
            single_symptom = list(q_token_set)[0]
            
            # 症状-常见病映射表
            # 说明：每个症状对应一组典型的常见病
            SYMPTOM_COMMON_MAP = {
                '发热': {
                    '感冒', '流行性感冒', '上呼吸道感染', 
                    '急性扁桃体炎', '急性咽炎', '急性支气管炎', 
                    '肺炎', '扁桃体炎'
                },
                '发烧': {
                    '感冒', '流行性感冒', '上呼吸道感染', 
                    '急性扁桃体炎', '急性咽炎', '急性支气管炎', '肺炎'
                },
                '头痛': {
                    '感冒', '偏头痛', '紧张性头痛', '神经性头痛', 
                    '流行性感冒', '上呼吸道感染', '高血压'
                },
                '头疼': {
                    '感冒', '偏头痛', '紧张性头痛', '神经性头痛', 
                    '流行性感冒', '上呼吸道感染'
                },
                '咳嗽': {
                    '急性支气管炎', '肺炎', '感冒', '咽炎', 
                    '流行性感冒', '支气管炎', '慢性支气管炎'
                },
                '咽痛': {
                    '急性咽炎', '急性扁桃体炎', '感冒', 
                    '流行性感冒', '上呼吸道感染'
                },
                '鼻塞': {
                    '感冒', '过敏性鼻炎', '鼻炎', '鼻窦炎', '上呼吸道感染'
                },
                '腹痛': {
                    '急性胃肠炎', '急性胃炎', '胃溃疡', '肠炎', '阑尾炎'
                },
                '腹泻': {
                    '急性胃肠炎', '肠炎', '急性肠炎', '病毒性肠炎'
                },
                '呕吐': {
                    '急性胃肠炎', '急性胃炎', '食物中毒', '胃炎'
                },
                '胸痛': {
                    '冠心病', '心绞痛', '肺炎', '肋间神经痛', '胸膜炎'
                },
                '呼吸困难': {
                    '哮喘', '肺炎', '心力衰竭', '支气管炎'
                },
            }
            
            # 查找当前症状对应的常见病集合
            SYMPTOM_COMMON = set()
            for key, diseases in SYMPTOM_COMMON_MAP.items():
                if key in single_symptom:  # 模糊匹配（"头痛"匹配"头疼"）
                    SYMPTOM_COMMON.update(diseases)
            
            # 单症状常见病加权
            for i, name in enumerate(names):
                dn = str(name)
                if dn in SYMPTOM_COMMON:
                    final_scores[i] *= 1.50  # +50%奖励
        
        # ===== 🎯 规则2：多症状匹配逻辑（关键优化） =====
        else:
            """
            多症状策略：
            - 用户输入2个或更多症状时，计算精确匹配度和模糊匹配度
            - 根据匹配情况进行差异化加权
            
            匹配指标：
            1. 精确匹配数：查询症状词在文档症状词中的精确匹配数量
            2. 模糊匹配数：包含关系匹配（如"头痛"匹配"偏头痛"）
            3. 匹配率：综合考虑查询侧和文档侧的匹配比例
            
            加权策略：
            - 完全匹配（所有症状都精确匹配）: × 1.40（+40%）
            - 高匹配率（≥70%）: × 1.15（+15%）
            - 中匹配率（50~70%）: × 1.08（+8%）
            - 低匹配率（30~50%）: × 1.00（不变）
            - 极低匹配率（<30%）: × 0.60（-40%）
            """
            # 存储每个疾病的匹配信息
            match_info = []
            
            for i, s in enumerate(symps):
                if not s:
                    # 如果疾病没有症状列表，跳过
                    match_info.append({'exact_count': 0, 'match_ratio': 0.0})
                    continue
                
                d_token_set = set(s)  # 文档症状词集合
                
                # 1️⃣ 精确匹配
                exact_matches = q_token_set & d_token_set  # 交集
                exact_count = len(exact_matches)
                
                # 2️⃣ 模糊匹配（包含关系）
                matched_count = exact_count  # 初始化为精确匹配数
                remaining_q = q_token_set - exact_matches  # 未精确匹配的查询症状
                remaining_d = d_token_set - exact_matches  # 未精确匹配的文档症状
                
                # 遍历未精确匹配的查询症状，检查是否被文档症状包含
                for qt in remaining_q:
                    if any(qt in dt or dt in qt for dt in remaining_d):
                        matched_count += 0.5  # 模糊匹配计0.5分
                
                # 3️⃣ 计算匹配率（调和平均）
                # 查询侧匹配率 = 匹配数 / 查询症状数
                match_ratio_q = matched_count / max(1, len(q_token_set))
                
                # 文档侧匹配率 = 匹配数 / 文档症状数
                match_ratio_d = matched_count / max(1, len(d_token_set))
                
                # 调和平均（平衡两侧）
                if match_ratio_q > 0 or match_ratio_d > 0:
                    match_ratio = 2 * (match_ratio_q * match_ratio_d) / \
                                  max(1e-9, match_ratio_q + match_ratio_d)
                else:
                    match_ratio = 0.0
                
                # 存储匹配信息
                match_info.append({
                    'exact_count': exact_count,
                    'match_ratio': match_ratio
                })
            
            # 🔥 根据匹配信息加权
            for i, info in enumerate(match_info):
                # ⭐⭐⭐ 完全匹配大幅奖励（新增）
                # 条件：精确匹配数 = 查询症状数 且 查询症状数 ≥ 2
                if info['exact_count'] == len(q_token_set) and len(q_token_set) >= 2:
                    final_scores[i] *= 1.40  # +40%奖励
                    print(f"[DEBUG] 完全匹配: {names[i]} (精确匹配{info['exact_count']}个症状，分数 × 1.40)")
                
                # 其他匹配率加权
                elif info['match_ratio'] >= 0.7:
                    final_scores[i] *= 1.15  # 高匹配率 +15%
                elif info['match_ratio'] >= 0.5:
                    final_scores[i] *= 1.08  # 中匹配率 +8%
                elif info['match_ratio'] >= 0.3:
                    final_scores[i] *= 1.00  # 低匹配率 不变
                else:
                    final_scores[i] *= 0.60  # 极低匹配率 -40%
            
            # ⭐⭐⭐ 非核心常见病降权（新增）
            """
            策略：
            - 在多症状查询时，避免过度推荐"感冒"等高频病
            - 只保留核心常见病的高权重，其他病降权
            """
            VERY_COMMON = {
                '感冒', '流行性感冒', '上呼吸道感染', '急性胃肠炎', 
                '急性支气管炎', '肺炎', '急性咽炎', '急性扁桃体炎',
                '急性胃炎', '偏头痛', '紧张性头痛'
            }
            
            for i, name in enumerate(names):
                dn = str(name)
                if dn not in VERY_COMMON:
                    final_scores[i] *= 0.88  # 非核心病降权12%
        
        # ==================== 第7步：通用降权（单/多症状都生效） ====================
        
        # ===== 🎯 规则3：罕见病降权 =====
        """
        策略：
        - 定义罕见病列表（发病率低、专科病、测试病等）
        - 在所有查询中，大幅降权罕见病（× 0.35，即-65%）
        
        作用：
        - 避免推荐低概率疾病（如"骨髓炎"、"败血症"等）
        - 提升用户体验（优先推荐常见病）
        """
        RARE_DISEASES = {
            '第1跖趾骨关节炎', '开放性骨折', '水痛症', '立克次体病', 
            '骨髓炎', '败血症', '脓毒血症', '肢端肥大症性心肌病',
            '密集恐惧症', '念珠菌性包皮龟头炎', '白屑风', '头风病',
            '股骨粗隆间骨折', '股骨转子间骨折', '踝部骨折',
            '混合型卟啉病', '黄体血肿', '肾胚胎瘤',
            '陈旧性肺结核', '婴幼儿脐疝',
            '泛细支气管炎-测试', '念珠菌性包皮龟头炎-测试',
        }
        
        for i, name in enumerate(names):
            dn = str(name)
            
            # 罕见病降权
            if dn in RARE_DISEASES:
                final_scores[i] *= 0.35  # -65%（大幅降权）
            
            # ===== 🎯 规则4：专科病在通用症状下降权 =====
            """
            策略：
            - 如果查询症状数 ≤ 2（通用症状）
            - 且疾病属于专科（骨科、男科、泌尿外科等）
            - 且症状中不包含专科关键词（如"骨折"、"阴茎"等）
            - 则降权（× 0.45，即-55%）
            
            作用：
            - 避免"头痛"查询时推荐"股骨骨折"等专科病
            - 提升推荐的相关性
            """
            if len(q_token_set) <= 2:
                # 专科科室列表
                specialist_depts = ['骨外科', '骨科', '男科', '泌尿外科', 
                                   '血液科', '小儿外科']
                
                # 专科关键词（如果症状中包含这些词，不降权）
                specialist_keywords = ['骨折', '骨痛', '阴茎', '包皮', 
                                      '龟头', '血液', '贫血', '脐']
                
                # 判断是否需要降权
                if str(cats[i]) in specialist_depts and \
                   not any(k in ' '.join(q_tokens) for k in specialist_keywords):
                    final_scores[i] *= 0.45  # -55%
        
        # ==================== 第8步：通用常见病加权（所有查询生效） ====================
        """
        策略：
        - 定义常见病列表及对应权重
        - 在所有查询中，对常见病进行加权
        
        权重设计：
        - 极常见病（如"感冒"）: × 1.35（+35%）
        - 常见病（如"流感"）: × 1.25~1.30（+25%~30%）
        - 较常见病（如"肺炎"）: × 1.15~1.20（+15%~20%）
        
        作用：
        - 提升常见病的排序位置
        - 符合医学统计规律（常见病更常见）
        """
        COMMON_DISEASES = {
            '感冒': 1.35,  # ⬅️ 从1.30提升到1.35（+35%）
            '流行性感冒': 1.28,  # ⬅️ 从1.25提升到1.28（+28%）
            '上呼吸道感染': 1.25,  # ⬅️ 从1.22提升到1.25（+25%）
            '急性扁桃体炎': 1.20,  # +20%
            '急性咽炎': 1.20,
            '急性支气管炎': 1.18,  # +18%
            '肺炎': 1.15,  # +15%
            '急性胃肠炎': 1.18,
            '急性胃炎': 1.15,
            '偏头痛': 1.20,
            '紧张性头痛': 1.18,
            '咽炎': 1.15,
            '支气管炎': 1.15,
            '扁桃体炎': 1.18,
            '慢性支气管炎': 1.12,  # +12%
        }
        
        for i, name in enumerate(names):
            if str(name) in COMMON_DISEASES:
                final_scores[i] *= COMMON_DISEASES[str(name)]
        
        # ==================== 第9步：排序并收集结果 ====================
        # 1. 按最终得分降序排序
        order = np.argsort(-final_scores)
        
        # 2. 收集结果
        results = []
        for idx in order:
            # 过滤低分结果
            if final_scores[idx] < min_score:
                continue
            
            # 添加结果
            results.append({
                'name': str(names[idx]),  # 疾病名称
                'category': str(cats[idx]),  # 科室
                'score': float(final_scores[idx]),  # 最终得分
                'semantic_score': float(sims[idx]),  # 语义得分
                'lexical_score': float(lex_scores[idx]),  # 词面得分
                'symptoms': symps[idx][:5]  # 症状列表（最多5个）
            })
            
            # 达到Top-K后停止
            if len(results) >= topk:
                break
        
        # ==================== 第10步：返回结果 ====================
        # 根据return_dict参数决定返回格式
        if return_dict:
            # Flask模式：返回字典列表
            return results
        else:
            # 命令行模式：返回格式化文本
            if results:
                lines = [f"\n🔍 查询: {' '.join(raw_tokens)}"]
                for i, r in enumerate(results, 1):
                    lines.append(
                        f"{i:>2}. {r['name']}  [{r['category']}]  "
                        f"相似度: {r['score']:.4f}"
                    )
                    if r['symptoms']:
                        lines.append(f"    症状: {'、'.join(r['symptoms'][:8])}")
                return '\n'.join(lines)
            else:
                return "⚠️  未找到达到阈值的结果"
        
    except Exception as e:
        # 异常处理
        import traceback
        traceback.print_exc()  # 打印完整堆栈跟踪
        return [] if return_dict else f"❌ 预测失败: {str(e)}"

# ==================== 第8部分：命令行入口 ====================

def main():
    """
    命令行接口主函数
    
    用法示例：
    =========
    基础查询：
        python disease_predictor.py --query "头痛 发热"
    
    调整参数：
        python disease_predictor.py --query "头痛 发热" --topk 10 --min_score 0.25
    
    测试模式：
        python disease_predictor.py --test
    
    帮助信息：
        python disease_predictor.py --help
    """
    # 创建参数解析器
    ap = argparse.ArgumentParser(
        description='症状预测疾病（混合系统：BERT + 规则引擎）'
    )
    
    # 定义命令行参数
    ap.add_argument('--query', type=str, 
                    help='症状文本（空格分隔），如 "头痛 发热"')
    ap.add_argument('--topk', type=int, default=5,
                    help='返回前K个结果（默认5）')
    ap.add_argument('--min_score', type=float, default=0.25,
                    help='最低相似度阈值（默认0.25）')
    ap.add_argument('--alpha', type=float, default=0.60,
                    help='语义权重（已废弃，保留兼容性）')
    ap.add_argument('--lexical', type=str, default='wexact',
                    choices=['fuzzy', 'exact', 'wexact', 'none'],
                    help='词面匹配模式（默认wexact）')
    ap.add_argument('--test', action='store_true',
                    help='测试模式（运行预定义查询）')
    
    # 解析参数
    args = ap.parse_args()
    
    # 执行操作
    if args.test:
        # ===== 测试模式 =====
        # 运行多个预定义查询
        test_queries = [
            "头痛 发热",  # 测试单/双症状
            "头痛 发热 咳嗽",  # 测试三症状
            "胸痛 呼吸困难",  # 测试心血管症状
            "腹痛 呕吐"  # 测试消化系统症状
        ]
        
        for query in test_queries:
            result = predict_disease(
                query,
                args.topk,
                args.min_score,
                args.alpha,
                args.lexical
            )
            print(result)
            print("=" * 70)
    
    elif args.query:
        # ===== 单次查询模式 =====
        result = predict_disease(
            args.query,
            args.topk,
            args.min_score,
            args.alpha,
            args.lexical
        )
        print(result)
    
    else:
        # ===== 显示帮助信息 =====
        ap.print_help()

# ==================== 第9部分：程序入口 ====================
if __name__ == '__main__':
    """
    程序入口点
    
    说明：
    - 仅当直接运行此脚本时执行（python disease_predictor.py）
    - 作为模块导入时不执行（from disease_predictor import predict_disease）
    """
    main()
