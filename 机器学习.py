"""
================================================================================
医疗疾病预测系统 - BERT双塔编码器训练脚本
================================================================================
功能模块：
1. 对比学习训练双塔编码器（Query-Document匹配）
2. 构建疾病索引（包含语义向量和IDF权重）
3. 混合检索（BERT语义相似度 + 词面重叠）

技术栈：
- PyTorch + Transformers（BERT模型）
- 对比学习（InfoNCE损失）
- 多字段结构化表示（症状/描述/病因/科室）
- IDF加权词面匹配

作者：Your Name
日期：2024-01-XX
版本：v3.0（字段标记 + IDF加权 + 混合检索）
================================================================================
"""

# ==================== 第1部分：依赖导入 ====================
import os  # 文件路径操作
import ast  # 安全解析Python字面量（如字符串形式的列表）
import argparse  # 命令行参数解析
import json  # JSON数据处理
import random  # 随机数生成（用于数据集划分）
import numpy as np  # 数值计算（向量操作）
import pandas as pd  # 数据表格处理（读取CSV）
import torch  # PyTorch深度学习框架
from torch.utils.data import Dataset, DataLoader  # 数据集和数据加载器
from torch.optim import AdamW  # AdamW优化器（带权重衰减的Adam）
from transformers import (
    BertTokenizer,  # BERT分词器
    BertModel,  # BERT预训练模型
    get_linear_schedule_with_warmup  # 学习率调度器（线性预热+线性衰减）
)
from tqdm import tqdm  # 进度条显示
from math import log  # 数学对数函数（计算IDF）

# ==================== 第2部分：路径和超参数配置 ====================

# ===== 路径配置 =====
MODEL_PATH = r'C:\bert-base-chinese'  # BERT预训练模型路径（本地模型）
DATA_PATH = r'C:\Users\Gustav  Adolf\Music\基于python医疗疾病数据分析大屏可视化系统\medical.csv'  # 医疗数据CSV文件路径
OUT_DIR = r'C:\medical_biencoder'  # 输出目录（保存训练后的模型和索引）
INDEX_PATH = os.path.join(OUT_DIR, 'biencoder_index.npz')  # 疾病索引文件路径（NumPy压缩格式）

# ===== 训练超参数 =====
MAX_LEN = 128  # BERT输入序列的最大长度（超过会截断）
BATCH_SIZE = 16  # 训练批次大小（每次前向传播的样本数）
EPOCHS = 1  # 训练轮数（遍历整个数据集的次数）
LR = 2e-5  # 学习率（AdamW优化器的初始学习率）
WARMUP = 0.1  # 预热步数比例（总步数的10%用于线性预热）
TEMP = 0.05  # 对比学习温度参数（控制相似度分布的平滑程度）
SEED = 42  # 随机种子（确保实验可复现）

# ===== 字段标记（结构化表示） =====
# 用于区分文本中的不同字段（症状/描述/病因/科室）
# 示例："[SYM] 头痛 发热 [SEP] [DESC] 常见感冒症状 [SEP] [CAT] 呼吸内科"
FIELD_TAGS = ['[SYM]', '[DESC]', '[CAUSE]', '[CAT]']

# ===== 初始化 =====
os.makedirs(OUT_DIR, exist_ok=True)  # 创建输出目录（如果不存在）
random.seed(SEED)  # 设置Python随机种子
np.random.seed(SEED)  # 设置NumPy随机种子
torch.manual_seed(SEED)  # 设置PyTorch随机种子

# ==================== 第3部分：数据预处理函数 ====================

def parse_list_str(x):
    """
    安全解析字符串形式的列表（兼容多种格式）
    
    参数：
        x: 可能的输入类型
            - None/NaN: 返回空列表
            - "['头痛', '发热']": 解析为Python列表
            - "头痛": 返回单元素列表
    
    返回：
        list[str]: 字符串列表（空列表或包含元素）
    
    示例：
        >>> parse_list_str("['头痛', '发热']")
        ['头痛', '发热']
        
        >>> parse_list_str("头痛")
        ['头痛']
        
        >>> parse_list_str(None)
        []
    """
    # 1. 处理None值
    if x is None:
        return []
    
    # 2. 处理NaN值（pandas的缺失值）
    if isinstance(x, float) and np.isnan(x):
        return []
    
    # 3. 转为字符串
    s = str(x)
    
    try:
        # 4. 尝试用ast.literal_eval安全解析（避免eval的安全风险）
        # 输入："['头痛', '发热']" → 输出：['头痛', '发热']
        v = ast.literal_eval(s)
        if isinstance(v, list):
            # 过滤空字符串并去除首尾空格
            return [str(i).strip() for i in v if str(i).strip()]
    except Exception:
        # 解析失败（如普通字符串"头痛"）
        pass
    
    # 5. 作为单个字符串处理
    return [s.strip()] if s.strip() else []

def format_query(symps):
    """
    格式化用户查询（添加字段标记）
    
    参数：
        symps (list[str]): 症状列表，如 ['头痛', '发热']
    
    返回：
        str: 格式化后的查询文本，如 "[SYM] 头痛 发热"
    
    示例：
        >>> format_query(['头痛', '发热'])
        '[SYM] 头痛 发热'
    """
    # 1. 过滤空字符串
    symps = [t for t in symps if t]
    
    # 2. 如果没有症状，返回空字符串
    if not symps:
        return ''
    
    # 3. 添加症状字段标记
    return f"{FIELD_TAGS[0]} " + ' '.join(symps)

def format_doc(symps, desc, cause, cat):
    """
    格式化文档（多字段结构化表示）
    
    参数：
        symps (list[str]): 症状列表
        desc (str): 疾病描述
        cause (str): 病因
        cat (str): 科室分类
    
    返回：
        str: 格式化后的文档文本
    
    格式：
        "[SYM] 症状1 症状2 [SEP] [DESC] 描述文本 [SEP] [CAUSE] 病因文本 [SEP] [CAT] 科室"
    
    示例：
        >>> format_doc(['头痛', '发热'], '常见感冒症状', '病毒感染', '呼吸内科')
        '[SYM] 头痛 发热 [SEP] [DESC] 常见感冒症状 [SEP] [CAUSE] 病毒感染 [SEP] [CAT] 呼吸内科'
    """
    parts = []  # 存储各个字段
    
    # 1. 症状字段（必有）
    symp_str = ' '.join([t for t in symps if t])
    parts.append(f"{FIELD_TAGS[0]} {symp_str}".strip())
    
    # 2. 描述字段（可选）
    if desc:
        parts.append(f"[SEP] {FIELD_TAGS[1]} {desc}".strip())
    
    # 3. 病因字段（可选）
    if cause:
        parts.append(f"[SEP] {FIELD_TAGS[2]} {cause}".strip())
    
    # 4. 科室字段（可选）
    if cat:
        parts.append(f"[SEP] {FIELD_TAGS[3]} {cat}".strip())
    
    # 5. 用空格连接所有字段
    return ' '.join(parts).strip()

def build_rows(df):
    """
    从DataFrame构建训练样本（Query-Document对）
    
    参数：
        df (pd.DataFrame): 医疗数据表格，包含以下列：
            - name: 疾病名称
            - symptom: 症状列表（字符串形式）
            - desc: 疾病描述
            - cause: 病因
            - category: 科室分类（字符串形式列表）
    
    返回：
        list[dict]: 训练样本列表，每个样本包含：
            - query: 查询文本（症状）
            - doc: 文档文本（多字段结构化）
            - name: 疾病名称
            - category: 科室
            - symptoms: 症状列表
    
    示例：
        >>> rows = build_rows(df)
        >>> rows[0]
        {
            'query': '[SYM] 头痛 发热',
            'doc': '[SYM] 头痛 发热 [SEP] [DESC] ...',
            'name': '感冒',
            'category': '呼吸内科',
            'symptoms': ['头痛', '发热', '咳嗽']
        }
    """
    rows = []
    
    # 遍历每一行疾病数据
    for _, r in df.iterrows():
        # 1. 提取疾病名称
        name = str(r.get('name', '')).strip()
        
        # 2. 提取描述和病因（可能为空）
        desc = '' if pd.isna(r.get('desc')) else str(r.get('desc'))
        cause = '' if pd.isna(r.get('cause')) else str(r.get('cause'))
        
        # 3. 解析症状列表
        symps = parse_list_str(r.get('symptom'))
        
        # 4. 解析科室分类（取最后一级）
        cats = parse_list_str(r.get('category'))
        cat = cats[-1] if len(cats) > 0 else ''
        
        # 5. 格式化查询文本（仅症状）
        q = format_query(symps)
        
        # 6. 如果没有症状，跳过该疾病
        if not q:
            continue
        
        # 7. 格式化文档文本（多字段）
        doc = format_doc(symps, desc, cause, cat)
        
        # 8. 构建样本字典
        rows.append({
            'query': q,
            'doc': doc,
            'name': name,
            'category': cat,
            'symptoms': symps
        })
    
    return rows

# ==================== 第4部分：BERT模型相关 ====================

def mean_pooling(last_hidden_state, attention_mask):
    """
    平均池化（将BERT输出的序列向量转为单个向量）
    
    参数：
        last_hidden_state (Tensor): BERT最后一层隐藏状态，形状 (batch, seq_len, hidden_dim)
        attention_mask (Tensor): 注意力掩码，形状 (batch, seq_len)，0表示padding位置
    
    返回：
        Tensor: 池化后的向量，形状 (batch, hidden_dim)
    
    计算方法：
        1. 对非padding位置的向量求和
        2. 除以有效token数量（忽略padding）
    
    示例：
        输入：[CLS] 头 痛 [SEP] [PAD] [PAD]  (hidden_dim=768)
        输出：4个token的平均向量（忽略[PAD]）
    """
    # 1. 将attention_mask扩展为3D张量 (batch, seq_len, 1)
    mask = attention_mask.unsqueeze(-1).float()
    
    # 2. 对有效位置的向量求和 (batch, hidden_dim)
    summed = (last_hidden_state * mask).sum(dim=1)
    
    # 3. 计算有效token数量 (batch, 1)
    counts = mask.sum(dim=1).clamp(min=1e-9)  # 防止除以0
    
    # 4. 返回平均向量 (batch, hidden_dim)
    return summed / counts

class BiEncoder(torch.nn.Module):
    """
    双塔编码器（Query和Document共享BERT参数）
    
    架构：
        Query → BERT → Mean Pooling → L2归一化 → Query向量
        Doc   → BERT → Mean Pooling → L2归一化 → Doc向量
    
    训练目标：
        最大化正样本对(q, d+)的余弦相似度
        最小化负样本对(q, d-)的余弦相似度
    """
    def __init__(self, model_path):
        """
        初始化双塔编码器
        
        参数：
            model_path (str): BERT模型路径（本地或HuggingFace）
        """
        super().__init__()
        # 加载预训练BERT模型（仅编码器部分）
        self.bert = BertModel.from_pretrained(model_path, local_files_only=True)
    
    def encode(self, input_ids, attention_mask):
        """
        编码文本为向量
        
        参数：
            input_ids (Tensor): 输入token ID，形状 (batch, seq_len)
            attention_mask (Tensor): 注意力掩码，形状 (batch, seq_len)
        
        返回：
            Tensor: L2归一化后的向量，形状 (batch, hidden_dim)
        """
        # 1. BERT前向传播
        out = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True
        )
        
        # 2. 平均池化
        pooled = mean_pooling(out.last_hidden_state, attention_mask)
        
        # 3. L2归一化（使余弦相似度等于点积）
        return torch.nn.functional.normalize(pooled, p=2, dim=1)

class PairDataset(Dataset):
    """
    Query-Document对数据集（用于对比学习）
    
    数据格式：
        [
            {'query': '[SYM] 头痛', 'doc': '[SYM] 头痛 [SEP] [DESC] ...', ...},
            {'query': '[SYM] 发热', 'doc': '[SYM] 发热 [SEP] [DESC] ...', ...},
            ...
        ]
    """
    def __init__(self, rows):
        """
        初始化数据集
        
        参数：
            rows (list[dict]): 样本列表（由build_rows生成）
        """
        self.rows = rows
    
    def __len__(self):
        """返回数据集大小"""
        return len(self.rows)
    
    def __getitem__(self, idx):
        """
        获取单个样本
        
        参数：
            idx (int): 样本索引
        
        返回：
            dict: 包含 query、doc、name、category、symptoms 的字典
        """
        return self.rows[idx]

def collate_fn(batch, tokenizer):
    """
    批量数据处理函数（将多个样本合并为batch）
    
    参数：
        batch (list[dict]): 批次样本列表
        tokenizer (BertTokenizer): BERT分词器
    
    返回：
        dict: 包含以下键值对：
            - q_input_ids: Query的token ID (batch, seq_len)
            - q_attn_mask: Query的注意力掩码 (batch, seq_len)
            - d_input_ids: Document的token ID (batch, seq_len)
            - d_attn_mask: Document的注意力掩码 (batch, seq_len)
    
    工作流程：
        1. 提取所有query和doc文本
        2. 使用tokenizer批量编码（自动padding）
        3. 返回PyTorch张量
    """
    # 1. 提取文本列表
    q_texts = [b['query'] for b in batch]  # ['[SYM] 头痛', '[SYM] 发热', ...]
    d_texts = [b['doc'] for b in batch]    # ['[SYM] 头痛 [SEP] ...', ...]
    
    # 2. 批量编码Query（自动padding到batch内最大长度）
    q_enc = tokenizer(
        q_texts,
        max_length=MAX_LEN,  # 最大长度128
        truncation=True,     # 超过最大长度时截断
        padding=True,        # padding到batch内最大长度
        return_tensors='pt'  # 返回PyTorch张量
    )
    
    # 3. 批量编码Document
    d_enc = tokenizer(
        d_texts,
        max_length=MAX_LEN,
        truncation=True,
        padding=True,
        return_tensors='pt'
    )
    
    # 4. 返回batch字典
    return {
        'q_input_ids': q_enc['input_ids'],      # Query的token ID
        'q_attn_mask': q_enc['attention_mask'],  # Query的注意力掩码
        'd_input_ids': d_enc['input_ids'],       # Document的token ID
        'd_attn_mask': d_enc['attention_mask']   # Document的注意力掩码
    }

def add_field_tags_to_tokenizer_and_model(tokenizer, model_bert):
    """
    添加字段标记到tokenizer和BERT模型
    
    参数：
        tokenizer (BertTokenizer): BERT分词器
        model_bert (BertModel): BERT模型
    
    返回：
        int: 新增token的数量
    
    作用：
        将 [SYM]、[DESC]、[CAUSE]、[CAT] 添加到词表中
        并调整BERT嵌入层维度（扩展token嵌入矩阵）
    """
    # 1. 添加特殊token到分词器
    num_added = tokenizer.add_special_tokens({
        'additional_special_tokens': FIELD_TAGS  # ['[SYM]', '[DESC]', '[CAUSE]', '[CAT]']
    })
    
    # 2. 如果有新增token，调整模型嵌入层维度
    if num_added > 0:
        model_bert.resize_token_embeddings(len(tokenizer))
    
    return num_added

@torch.no_grad()  # 禁用梯度计算（推理模式）
def embed_texts_with_bert(bert_model, tokenizer, texts, device, desc='Encode'):
    """
    批量编码文本为向量（推理模式）
    
    参数：
        bert_model (BertModel): BERT模型
        tokenizer (BertTokenizer): 分词器
        texts (list[str]): 文本列表
        device (torch.device): 设备（CPU或GPU）
        desc (str): 进度条描述
    
    返回：
        np.ndarray: 向量矩阵，形状 (len(texts), hidden_dim)
    
    工作流程：
        1. 分批处理（避免显存溢出）
        2. 编码每批文本
        3. 拼接所有向量
    """
    vecs = []  # 存储所有向量
    bert_model.eval()  # 设置为评估模式（禁用dropout）
    
    # 分批处理（每批BATCH_SIZE个样本）
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc=desc):
        batch = texts[i:i+BATCH_SIZE]  # 获取当前批次
        
        # 编码当前批次
        enc = tokenizer(
            batch,
            max_length=MAX_LEN,
            truncation=True,
            padding=True,
            return_tensors='pt'
        )
        
        # 移动到指定设备
        enc = {k: v.to(device) for k, v in enc.items()}
        
        # BERT前向传播
        out = bert_model(**enc, return_dict=True)
        
        # 平均池化
        pooled = mean_pooling(out.last_hidden_state, enc['attention_mask'])
        
        # L2归一化
        pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
        
        # 转为NumPy并存储
        vecs.append(pooled.cpu().numpy())
    
    # 拼接所有批次的向量 (N, hidden_dim)
    return np.vstack(vecs)

# ==================== 第5部分：训练和评估 ====================

def grouped_split_by_name(rows, val_ratio=0.1, seed=SEED):
    """
    按疾病名称分组划分训练集和验证集（避免同病泄漏）
    
    参数：
        rows (list[dict]): 样本列表
        val_ratio (float): 验证集比例
        seed (int): 随机种子
    
    返回：
        tuple: (train_rows, val_rows)
    
    划分策略：
        1. 将同一疾病的所有样本分为一组
        2. 按疾病名称随机划分训练集和验证集
        3. 确保同一疾病不会同时出现在训练集和验证集
    
    示例：
        输入：[
            {'name': '感冒', ...},
            {'name': '感冒', ...},
            {'name': '发烧', ...}
        ]
        输出：
            训练集：[{'name': '感冒', ...}, {'name': '感冒', ...}]
            验证集：[{'name': '发烧', ...}]
    """
    from collections import defaultdict
    
    # 1. 按疾病名称分组
    groups = defaultdict(list)  # {'感冒': [0, 1], '发烧': [2], ...}
    for i, r in enumerate(rows):
        groups[r['name']].append(i)
    
    # 2. 获取所有疾病名称
    names = list(groups.keys())
    
    # 3. 随机打乱疾病顺序
    random.Random(seed).shuffle(names)
    
    # 4. 计算训练集疾病数量
    cut = max(1, int(len(names) * (1 - val_ratio)))
    
    # 5. 划分疾病名称
    train_names = set(names[:cut])  # 前90%的疾病
    
    # 6. 收集训练集和验证集的样本索引
    train_idx = [i for n in train_names for i in groups[n]]
    val_idx = [i for n in names[cut:] for i in groups[n]]
    
    # 7. 返回样本列表
    return [rows[i] for i in train_idx], [rows[i] for i in val_idx]

def train(epochs=EPOCHS):
    """
    训练双塔编码器（对比学习）
    
    参数：
        epochs (int): 训练轮数
    
    训练流程：
        1. 加载数据并构建Query-Document对
        2. 划分训练集和验证集（按疾病名称分组）
        3. 初始化BERT模型和分词器
        4. 对比学习训练（InfoNCE损失）
        5. 评估验证集Recall@10
        6. 保存最佳模型
    
    对比学习损失：
        L = -log( exp(q·d+/τ) / Σexp(q·di/τ) )
        其中：
        - q: query向量
        - d+: 正样本document向量
        - di: batch内所有document向量（包括负样本）
        - τ: 温度参数（TEMP=0.05）
    """
    # ===== 第1步：加载数据 =====
    print('📂 读取数据...')
    df = pd.read_csv(DATA_PATH, encoding='utf-8')
    rows = build_rows(df)  # 构建训练样本
    print(f'✓ 可训练条目: {len(rows)}')

    if len(rows) < 2:
        raise RuntimeError('没有足够的有症状条目用于训练')

    # ===== 第2步：划分数据集 =====
    # 使用分组划分（避免同一疾病同时出现在训练集和验证集）
    train_rows, val_rows = grouped_split_by_name(rows, val_ratio=0.1, seed=SEED)

    # ===== 第3步：初始化模型和分词器 =====
    tokenizer = BertTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
    model = BiEncoder(MODEL_PATH)
    
    # 添加字段标记到分词器和模型
    add_field_tags_to_tokenizer_and_model(tokenizer, model.bert)

    # ===== 第4步：设置设备 =====
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    print(f'✓ 设备: {device}')

    # ===== 第5步：创建数据加载器 =====
    train_ds = PairDataset(train_rows)
    val_ds = PairDataset(val_rows)
    
    train_loader = DataLoader(
        train_ds,
        batch_size=BATCH_SIZE,
        shuffle=True,  # 训练集打乱
        collate_fn=lambda b: collate_fn(b, tokenizer)
    )
    
    val_loader = DataLoader(
        val_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,  # 验证集不打乱
        collate_fn=lambda b: collate_fn(b, tokenizer)
    )

    # ===== 第6步：初始化优化器和学习率调度器 =====
    optimizer = AdamW(
        model.parameters(),
        lr=LR,  # 学习率2e-5
        weight_decay=0.01  # 权重衰减（L2正则化）
    )
    
    total_steps = max(1, len(train_loader) * epochs)  # 总训练步数
    warmup_steps = int(total_steps * WARMUP)  # 预热步数（10%）
    
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,  # 预热阶段学习率线性增长
        num_training_steps=total_steps  # 训练阶段学习率线性衰减
    )
    
    ce = torch.nn.CrossEntropyLoss()  # 交叉熵损失（用于对比学习）

    # ===== 第7步：训练循环 =====
    best_r10 = 0.0  # 记录最佳Recall@10
    
    for epoch in range(epochs):
        # ===== 训练阶段 =====
        model.train()  # 设置为训练模式（启用dropout）
        pbar = tqdm(train_loader, desc=f'🔧 训练 {epoch+1}/{epochs}')
        loss_running = 0.0  # 累计损失
        seen = 0  # 已处理样本数
        
        for batch in pbar:
            # 1. 获取batch数据并移动到设备
            q_ids = batch['q_input_ids'].to(device)
            q_ms = batch['q_attn_mask'].to(device)
            d_ids = batch['d_input_ids'].to(device)
            d_ms = batch['d_attn_mask'].to(device)

            # 2. 编码query和document
            q_vec = model.encode(q_ids, q_ms)  # (batch, hidden_dim)
            d_vec = model.encode(d_ids, d_ms)  # (batch, hidden_dim)

            # 3. 计算相似度矩阵（query-document）
            logits_qd = (q_vec @ d_vec.t()) / TEMP  # (batch, batch)
            # 对角线元素是正样本对的相似度
            # 非对角线元素是负样本对的相似度
            
            # 4. 构造标签（对角线为正样本）
            labels = torch.arange(logits_qd.size(0), device=device)
            # labels = [0, 1, 2, ...] 表示第i个query对应第i个document
            
            # 5. 计算query→document的对比损失
            loss1 = ce(logits_qd, labels)

            # 6. 计算document→query的对比损失（对称损失）
            logits_dq = (d_vec @ q_vec.t()) / TEMP  # (batch, batch)
            loss2 = ce(logits_dq, labels)

            # 7. 最终损失（双向对比损失的平均）
            loss = 0.5 * (loss1 + loss2)

            # 8. 反向传播和优化
            optimizer.zero_grad()  # 清空梯度
            loss.backward()  # 反向传播
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # 梯度裁剪（防止梯度爆炸）
            optimizer.step()  # 更新参数
            scheduler.step()  # 更新学习率

            # 9. 记录损失
            loss_running += loss.item() * q_ids.size(0)
            seen += q_ids.size(0)
            pbar.set_postfix({'loss': f'{loss_running / max(1, seen):.4f}'})

        # ===== 验证阶段 =====
        r10 = eval_recall(model, tokenizer, val_rows, device, topk=10)
        print(f'📊 验证集 Recall@10: {r10:.4f}')
        
        # ===== 保存最佳模型 =====
        if r10 > best_r10:
            best_r10 = r10
            save_path = os.path.join(OUT_DIR, 'biencoder')
            model.bert.save_pretrained(save_path)  # 保存BERT参数
            tokenizer.save_pretrained(save_path)  # 保存分词器
            print(f'✅ 保存最佳模型到: {save_path} (R@10={best_r10:.4f})')

    print(f'🎉 训练完成！最佳 R@10={best_r10:.4f}')

@torch.no_grad()  # 禁用梯度计算
def eval_recall(model, tokenizer, rows, device, topk=10, max_eval=512):
    """
    评估验证集的Recall@K（召回率）
    
    参数：
        model (BiEncoder): 双塔编码器
        tokenizer (BertTokenizer): 分词器
        rows (list[dict]): 验证集样本
        device (torch.device): 设备
        topk (int): 计算Recall@K
        max_eval (int): 最多评估的样本数（避免显存溢出）
    
    返回：
        float: Recall@K（范围0~1）
    
    评估方法：
        1. 编码所有query和document
        2. 计算相似度矩阵 (N, N)
        3. 对每个query，找到Top-K最相似的document
        4. 如果正样本在Top-K中，计为命中
        5. Recall@K = 命中数 / 总样本数
    """
    model.eval()  # 设置为评估模式
    
    # 1. 采样（如果样本太多，只评估前max_eval个）
    sample = rows[:max_eval] if len(rows) > max_eval else rows
    
    # 2. 提取query和document文本
    q_texts = [r['query'] for r in sample]
    d_texts = [r['doc'] for r in sample]

    # 3. 编码为向量
    q_vecs = embed_texts_with_bert(model.bert, tokenizer, q_texts, device, desc='评估查询')
    d_vecs = embed_texts_with_bert(model.bert, tokenizer, d_texts, device, desc='评估文档')

    # 4. 计算相似度矩阵 (N, N)
    sims = q_vecs @ d_vecs.T
    
    # 5. 对每行排序，找到Top-K document
    idxs = np.argsort(-sims, axis=1)[:, :topk]  # (N, topk)
    
    # 6. 计算命中数
    hits = 0
    for i in range(idxs.shape[0]):
        if i in idxs[i]:  # 如果正样本（第i个document）在Top-K中
            hits += 1
    
    # 7. 返回召回率
    return hits / idxs.shape[0]

# ==================== 第6部分：构建索引 ====================

@torch.no_grad()
def build_index():
    """
    构建疾病索引（包含语义向量和IDF权重）
    
    索引内容：
        - embeddings: 所有疾病的BERT向量 (N, hidden_dim)
        - names: 疾病名称列表 (N,)
        - categories: 科室列表 (N,)
        - symptoms: 症状列表（JSON字符串） (N,)
        - docs: 文档文本列表 (N,)
        - idf_terms: IDF词表（症状词）
        - idf_vals: IDF值
    
    工作流程：
        1. 加载训练后的BERT模型
        2. 读取医疗数据
        3. 编码所有疾病文档
        4. 计算症状IDF权重
        5. 保存为压缩的NumPy文件
    """
    # ===== 第1步：加载训练后的模型 =====
    print('📦 载入训练后的编码器...')
    enc_path = os.path.join(OUT_DIR, 'biencoder')
    
    if not os.path.isdir(enc_path):
        raise FileNotFoundError(f'未找到训练模型: {enc_path}。请先运行 --train')
    
    tok = BertTokenizer.from_pretrained(enc_path, local_files_only=True)
    enc = BertModel.from_pretrained(enc_path, local_files_only=True)

    # 添加字段标记
    tok.add_special_tokens({'additional_special_tokens': FIELD_TAGS})
    enc.resize_token_embeddings(len(tok))

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    enc.to(device).eval()

    # ===== 第2步：读取数据 =====
    print('📂 读取数据并构建文档...')
    df = pd.read_csv(DATA_PATH, encoding='utf-8')
    rows = build_rows(df)
    
    names = [r['name'] for r in rows]  # 疾病名称列表
    cats = [r['category'] for r in rows]  # 科室列表
    symps = [r['symptoms'] for r in rows]  # 症状列表
    docs = [r['doc'] for r in rows]  # 文档列表

    # ===== 第3步：计算症状IDF权重 =====
    # IDF（逆文档频率）= log((N+1) / (DF+1)) + 1
    # 其中：
    # - N: 总疾病数
    # - DF: 包含该症状的疾病数
    # 
    # 作用：
    # - 常见症状（如"发热"）IDF较低，权重小
    # - 罕见症状（如"牙龈出血"）IDF较高，权重大
    
    N = len(rows)  # 总疾病数
    df_counts = {}  # 统计每个症状的文档频率
    
    # 统计文档频率
    for r in rows:
        for s in set([t for t in r['symptoms'] if t]):
            df_counts[s] = df_counts.get(s, 0) + 1
    
    # 计算IDF
    idf_terms = []  # 症状词表
    idf_vals = []  # IDF值
    
    for s, dfc in df_counts.items():
        idf_terms.append(s)
        # IDF公式：log((N+1)/(DF+1)) + 1
        # +1平滑避免log(0)，+1偏置确保非负
        idf_vals.append(log((N + 1.0) / (dfc + 1.0)) + 1.0)
    
    idf_terms = np.array(idf_terms, dtype=object)
    idf_vals = np.array(idf_vals, dtype=np.float32)

    # ===== 第4步：编码所有文档 =====
    print(f'🤖 编码 {len(docs)} 个文档向量...')
    vecs = embed_texts_with_bert(enc, tok, docs, device, desc='编码文档')

    # ===== 第5步：保存索引 =====
    np.savez_compressed(
        INDEX_PATH,
        embeddings=vecs,  # (N, hidden_dim)
        names=np.array(names, dtype=object),
        categories=np.array(cats, dtype=object),
        symptoms=np.array([json.dumps(s, ensure_ascii=False) for s in symps], dtype=object),
        docs=np.array(docs, dtype=object),
        idf_terms=idf_terms,  # 症状词表
        idf_vals=idf_vals  # IDF值
    )
    
    print(f'✅ 索引已保存到: {INDEX_PATH}')

# ==================== 第7部分：检索和词面匹配 ====================

def _tokens_from_query_text(text):
    """
    从查询文本中提取症状词（去除字段标记）
    
    参数：
        text (str): 查询文本，如 "[SYM] 头痛 发热"
    
    返回：
        list[str]: 症状词列表，如 ['头痛', '发热']
    
    示例：
        >>> _tokens_from_query_text("[SYM] 头痛 发热 [SEP] [DESC]")
        ['头痛', '发热']
    """
    toks = []
    for t in text.strip().split():
        # 跳过字段标记和分隔符
        if t in FIELD_TAGS or t == '[SEP]':
            continue
        toks.append(t)
    return toks

def _char_ngrams(s, n=2):
    """
    生成字符级n-gram集合（用于模糊匹配）
    
    参数：
        s (str): 输入字符串
        n (int): n-gram长度（默认2）
    
    返回：
        set[str]: n-gram集合
    
    示例：
        >>> _char_ngrams("头痛", 2)
        {'头痛'}
        
        >>> _char_ngrams("偏头痛", 2)
        {'偏头', '头痛'}
    """
    # 去除标点符号和空格
    s = str(s).replace('、', '').replace('，', '').replace('。', '').replace(' ', '')
    
    if not s:
        return set()
    
    # 如果字符串长度小于n，返回整个字符串
    if len(s) < n:
        return {s}
    
    # 生成滑动窗口n-gram
    return {s[i:i+n] for i in range(len(s) - n + 1)}

def _lexical_score(query_tokens, doc_symptoms, mode='fuzzy', idf=None):
    """
    计算词面匹配得分（支持多种模式）
    
    参数：
        query_tokens (list[str]): 查询症状词
        doc_symptoms (list[str]): 文档症状词
        mode (str): 匹配模式
            - 'none': 禁用词面匹配
            - 'exact': 精确匹配（Jaccard相似度）
            - 'wexact': 加权精确匹配（IDF加权Jaccard）
            - 'fuzzy': 模糊匹配（字符级2-gram Jaccard）
        idf (dict): IDF字典 {词: IDF值}
    
    返回：
        float: 词面匹配得分（范围0~1）
    
    模式说明：
        1. 精确匹配（exact）：
           Jaccard = |Q ∩ D| / |Q ∪ D|
           示例：Q=['头痛', '发热'], D=['头痛', '咳嗽']
                 Jaccard = 1/3 = 0.333
        
        2. 加权精确匹配（wexact）：
           Jaccard = Σ_i IDF(word_i) for word_i in Q∩D / Σ_i IDF(word_i) for word_i in Q∪D
           示例：Q=['头痛', '发热'], D=['头痛', '咳嗽']
                 IDF('头痛')=1.5, IDF('发热')=2.0, IDF('咳嗽')=2.5
                 Jaccard = 1.5 / (1.5+2.0+2.5) = 0.25
        
        3. 模糊匹配（fuzzy）：
           将每个词转为字符级2-gram，然后计算Jaccard
           示例：Q=['偏头痛'], D=['头痛']
                 Q_ngrams={'偏头', '头痛'}, D_ngrams={'头痛'}
                 Jaccard = 1/2 = 0.5
    """
    # 1. 过滤空字符串
    q_tokens = [t for t in query_tokens if t]
    d_tokens = [t for t in doc_symptoms if t]
    
    if not q_tokens or not d_tokens:
        return 0.0

    # 2. 禁用词面匹配
    if mode == 'none':
        return 0.0

    # 3. 精确匹配（Jaccard相似度）
    if mode == 'exact':
        q_set, d_set = set(q_tokens), set(d_tokens)
        inter, union = len(q_set & d_set), len(q_set | d_set)
        return (inter / union) if union > 0 else 0.0

    # 4. 加权精确匹配（IDF加权Jaccard）
    if mode == 'wexact':
        q_set, d_set = set(q_tokens), set(d_tokens)
        inter = q_set & d_set  # 交集
        union = q_set | d_set  # 并集
        
        if not union:
            return 0.0
        
        def wsum(ts):
            """计算词集合的IDF加权和"""
            if not idf:
                return float(len(ts))  # 没有IDF时，使用词数
            return sum(max(0.0, float(idf.get(t, 0.0))) for t in ts)
        
        # 加权Jaccard
        return (wsum(inter) / max(1e-9, wsum(union)))

    # 5. 模糊匹配（字符级2-gram Jaccard）
    # 场景：查询"偏头痛"，文档有"头痛"，应该部分匹配
    q_ngrams = set()
    for t in q_tokens:
        q_ngrams |= _char_ngrams(t, 2)  # 合并所有词的2-gram
    
    d_ngrams = set()
    for t in d_tokens:
        d_ngrams |= _char_ngrams(t, 2)
    
    if not q_ngrams or not d_ngrams:
        return 0.0
    
    inter = len(q_ngrams & d_ngrams)
    union = len(q_ngrams | d_ngrams)
    return (inter / union) if union > 0 else 0.0

# ==================== 第8部分：检索接口 ====================

@torch.no_grad()
def search(query, topk=5, min_score=0.0, alpha=0.7, lexical='fuzzy', debug=False):
    """
    混合检索（BERT语义相似度 + 词面匹配）
    
    参数：
        query (str): 查询文本（症状，空格分隔）
        topk (int): 返回前K个结果
        min_score (float): 最低得分阈值
        alpha (float): 语义权重（最终分 = alpha*语义 + (1-alpha)*词面）
        lexical (str): 词面匹配模式（fuzzy/exact/wexact/none）
        debug (bool): 是否打印调试信息
    
    返回：
        None（直接打印结果）
    
    检索流程：
        1. 加载索引和模型
        2. 编码查询文本
        3. 计算语义相似度（余弦相似度）
        4. 计算词面匹配得分
        5. 融合两种得分
        6. 排序并返回Top-K
    
    示例：
        >>> search("头痛 发热", topk=5, alpha=0.7, lexical='fuzzy')
        🔍 查询: 头痛 发热
         1. 感冒  [呼吸内科]  相似度: 0.7234
            症状: 头痛、发热、咳嗽
         2. 流感  [呼吸内科]  相似度: 0.6891
            症状: 发热、头痛、全身酸痛
    """
    # ===== 第1步：加载索引 =====
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError('索引文件不存在。请先运行 --build_index')
    
    data = np.load(INDEX_PATH, allow_pickle=True)
    embs = data['embeddings']  # (N, hidden_dim)
    names = data['names']  # (N,)
    cats = data['categories']  # (N,)
    symps = [json.loads(s) for s in data['symptoms']]  # list[list[str]]
    
    # 读取IDF字典
    idf = {}
    if 'idf_terms' in data and 'idf_vals' in data:
        terms = data['idf_terms']
        vals = data['idf_vals']
        for k, v in zip(terms, vals):
            idf[str(k)] = float(v)

    # ===== 第2步：加载模型 =====
    enc_path = os.path.join(OUT_DIR, 'biencoder')
    tok = BertTokenizer.from_pretrained(enc_path, local_files_only=True)
    enc = BertModel.from_pretrained(enc_path, local_files_only=True)
    
    # 添加字段标记
    tok.add_special_tokens({'additional_special_tokens': FIELD_TAGS})
    enc.resize_token_embeddings(len(tok))

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    enc.to(device).eval()

    # ===== 第3步：预处理查询文本 =====
    # 提取症状词
    raw_query_tokens = [t for t in query.strip().split() if t]
    
    # 如果查询文本已包含字段标记，保持原样；否则添加[SYM]标记
    wrapped_query = query if any(t in query for t in FIELD_TAGS) else format_query(raw_query_tokens)

    # ===== 第4步：编码查询 =====
    enc_in = tok(
        [wrapped_query],
        max_length=MAX_LEN,
        truncation=True,
        padding=True,
        return_tensors='pt'
    )
    enc_in = {k: v.to(device) for k, v in enc_in.items()}
    
    # BERT前向传播
    out = enc(**enc_in, return_dict=True)
    
    # 平均池化 + L2归一化
    q = mean_pooling(out.last_hidden_state, enc_in['attention_mask'])
    q = torch.nn.functional.normalize(q, p=2, dim=1).cpu().numpy()[0]

    # ===== 第5步：计算语义相似度 =====
    sims = embs @ q  # (N,) 余弦相似度（因为向量已L2归一化）

    # ===== 第6步：计算词面匹配得分 =====
    q_tokens = _tokens_from_query_text(wrapped_query)  # 提取症状词
    lex_scores = np.zeros_like(sims)  # (N,)
    
    for i, s in enumerate(symps):
        lex_scores[i] = _lexical_score(q_tokens, s, mode=lexical, idf=idf)

    # ===== 第7步：融合两种得分 =====
    # 最终分 = alpha * 语义相似度 + (1-alpha) * 词面匹配分
    final_scores = alpha * sims + (1.0 - alpha) * lex_scores

    # ===== 第8步：排序并返回Top-K =====
    order = np.argsort(-final_scores)  # 降序排序

    # ===== 第9步：打印结果 =====
    print(f'\n🔍 查询: {" ".join(raw_query_tokens) if raw_query_tokens else query}')
    shown = 0
    
    for idx in order:
        # 过滤低分结果
        if final_scores[idx] < min_score:
            continue
        
        # 调试模式：打印详细得分
        if debug:
            print(f'{shown+1:>2}. {names[idx]} [{cats[idx]}] '
                  f'final={final_scores[idx]:.4f} cos={sims[idx]:.4f} lex={lex_scores[idx]:.4f}')
        else:
            # 正常模式：仅打印最终得分
            print(f'{shown+1:>2}. {names[idx]}  [{cats[idx]}]  相似度: {final_scores[idx]:.4f}')
        
        # 打印症状列表（最多8个）
        if len(symps[idx]) > 0:
            print(f'    症状: {"、".join(symps[idx][:8])}')
        
        shown += 1
        
        # 达到Top-K后停止
        if shown >= topk:
            break
    
    # 无结果提示
    if shown == 0:
        print('⚠️  未找到达到阈值的结果')
        print('💡 提示：调整 --min_score 或设置 --lexical none 以仅用语义相似度')

# ==================== 第9部分：命令行接口 ====================

def main():
    """
    命令行接口
    
    用法示例：
        # 训练模型
        python script.py --train --epochs 3
        
        # 构建索引
        python script.py --build_index
        
        # 检索（精确匹配）
        python script.py --query "头痛 发热" --lexical exact --alpha 0.5
        
        # 检索（模糊匹配）
        python script.py --query "偏头痛" --lexical fuzzy --alpha 0.7
        
        # 调试模式
        python script.py --query "头痛" --debug
    """
    ap = argparse.ArgumentParser(description='医疗疾病预测系统 - BERT双塔编码器')
    
    # ===== 模式参数 =====
    ap.add_argument('--train', action='store_true',
                    help='训练双塔编码器（对比学习）')
    ap.add_argument('--build_index', action='store_true',
                    help='用训练后的编码器重建索引（含IDF）')
    ap.add_argument('--query', type=str,
                    help='症状查询文本（空格分隔），支持已带字段标记的输入')
    
    # ===== 训练参数 =====
    ap.add_argument('--epochs', type=int, default=EPOCHS,
                    help='训练轮数（默认1）')
    
    # ===== 检索参数 =====
    ap.add_argument('--topk', type=int, default=5,
                    help='返回前K个结果（默认5）')
    ap.add_argument('--min_score', type=float, default=0.0,
                    help='最低相似度阈值，作用于重排后分数（默认0.0）')
    ap.add_argument('--alpha', type=float, default=0.7,
                    help='语义权重，最终分=alpha*cos + (1-alpha)*lexical（默认0.7）')
    ap.add_argument('--lexical', type=str, default='fuzzy',
                    choices=['fuzzy', 'exact', 'wexact', 'none'],
                    help='词面重叠模式：fuzzy(模糊), exact(精确), wexact(IDF加权), none(禁用)')
    ap.add_argument('--debug', action='store_true',
                    help='打印 cos/lex/final 调试信息')
    
    args = ap.parse_args()

    # ===== 执行对应操作 =====
    if args.train:
        train(epochs=args.epochs)
    
    if args.build_index:
        build_index()
    
    if args.query:
        search(
            args.query,
            args.topk,
            args.min_score,
            args.alpha,
            args.lexical,
            args.debug
        )
    
    # 如果没有任何参数，打印帮助信息
    if not (args.train or args.build_index or args.query):
        ap.print_help()

# ==================== 第10部分：程序入口 ====================
if __name__ == '__main__':
    main()
