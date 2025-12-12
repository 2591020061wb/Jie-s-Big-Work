<template>
  <dv-border-box-10 class="panel ai-coach-panel">
    <div class="panel-header">
      <div class="panel-title">AI 健康助手</div>
      <small>个性化建议与健康提醒</small>
    </div>
    <div class="message-list">
      <div v-for="message in coachList" :key="message.id" class="message-card">
        <div class="message-tag">{{ message.tag }}</div>
        <div class="message-title">{{ message.title }}</div>
        <div class="message-content">{{ message.desc }}</div>
        <div class="message-time">{{ message.time }}</div>
      </div>
      
      <div v-if="!coachList.length" class="empty-message">
        暂无AI助手消息，请继续保持健康监测
      </div>
    </div>
    
    <div class="coach-input">
      <input 
        type="text" 
        v-model="question" 
        placeholder="输入健康问题，AI助手为您解答..." 
        @keyup.enter="submitQuestion"
        :disabled="isLoading"
      />
      <button @click="submitQuestion" :disabled="!question || isLoading">
        {{ isLoading ? '处理中...' : '发送' }}
      </button>
    </div>
  </dv-border-box-10>
</template>

<script>
  /**
   * ========================================================================
   * AI 健康助手组件 - 基于豆包大模型的医学对话系统
   * ========================================================================
   * 功能：
   * 1. 用户输入健康问题（症状、疾病咨询等）
   * 2. 调用豆包（火山引擎）大模型API
   * 3. 返回AI医学建议（症状分析、可能疾病、就医建议）
   * 4. 维护对话历史（上下文记忆）
   * 5. 显示消息列表（历史消息）
   * 
   * 技术栈：
   * - Vue 2.x（组件化开发）
   * - 豆包大模型（火山引擎 ARK API）
   * - Fetch API（HTTP请求）
   * 
   * 作者：Your Name
   * 日期：2024-01-XX
   * 版本：v1.0
   * ========================================================================
   */
  
  export default {
    // ==================== 组件配置 ====================
    
    /**
     * 组件名称
     * 用途：Vue DevTools调试、组件引用
     */
    name: 'AiCoachPlan',
    
    // ==================== 组件属性（Props） ====================
    
    /**
     * 父组件传入的属性
     * 
     * props说明：
     * - coachList: 历史消息列表（从父组件传入）
     *   类型：Array
     *   默认值：空数组
     *   结构：[
     *     {
     *       id: 1,
     *       tag: '饮食建议',
     *       title: '今日饮食提醒',
     *       desc: '建议增加蔬菜摄入...',
     *       time: '2024-01-15 10:00'
     *     },
     *     ...
     *   ]
     * 
     * 使用场景：
     * - 父组件传入历史消息
     * - 组件内部只读（不修改）
     * - 通过v-for渲染消息列表
     */
    props: {
      coachList: {
        type: Array,  // 数组类型
        default: () => []  // 默认返回空数组（工厂函数，避免引用共享）
      }
    },
    
    // ==================== 组件数据（Data） ====================
    
    /**
     * 组件内部状态
     * 
     * 响应式数据说明：
     * - question: 用户输入的问题（绑定到输入框）
     * - isLoading: 是否正在请求API（控制按钮禁用状态）
     * - conversationHistory: 对话历史记录（用于上下文记忆）
     * - apiConfig: API配置（URL、密钥、模型ID）
     */
    data() {
      return {
        // ===== 用户输入 =====
        /**
         * question: 当前用户输入的问题
         * 类型：String
         * 初始值：空字符串
         * 绑定：v-model（双向绑定到输入框）
         * 
         * 示例：
         * - 用户输入："头痛 发热"
         * - this.question 变为 "头痛 发热"
         */
        question: '',
        
        // ===== 加载状态 =====
        /**
         * isLoading: 是否正在请求API
         * 类型：Boolean
         * 初始值：false
         * 作用：
         * - 请求开始时设为true（禁用按钮和输入框）
         * - 请求结束时设为false（恢复交互）
         * 
         * 状态流转：
         * false（初始） → true（请求中） → false（完成/失败）
         */
        isLoading: false,
        
        // ===== 对话历史 =====
        /**
         * conversationHistory: 对话历史记录
         * 类型：Array
         * 初始值：空数组
         * 结构：[
         *   { role: 'user', content: '头痛 发热' },
         *   { role: 'assistant', content: '可能是感冒...' },
         *   { role: 'user', content: '需要吃药吗' },
         *   { role: 'assistant', content: '建议...' },
         *   ...
         * ]
         * 
         * 作用：
         * - 维护上下文（让AI记住之前的对话）
         * - 限制长度（最多保留8条消息）
         * - 提升对话连贯性
         * 
         * 示例：
         * 用户："头痛 发热"
         * AI："可能是感冒，建议休息"
         * 用户："需要吃药吗"（AI能记住上文"感冒"）
         * AI："可以吃退烧药"
         */
        conversationHistory: [],
        
        // ===== API配置 =====
        /**
         * apiConfig: 豆包大模型API配置
         * 类型：Object
         * 
         * 配置说明：
         * - url: API端点地址（火山引擎ARK平台）
         * - key: API密钥（从豆包平台获取）
         * - model: 模型ID/接入点ID（从豆包平台创建）
         * 
         * ⚠️  安全提示：
         * - 生产环境不要硬编码密钥
         * - 建议存储在环境变量或后端服务器
         * - 当前配置仅用于演示
         */
        apiConfig: {
          // API端点（火山引擎北京区域）
          url: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
          
          // API密钥（⚠️ 生产环境需保密）
          key: '2c9f9e15-5895-44db-858d-0d5e6dd7ac97',
          
          // 模型ID（接入点ID，在豆包平台创建）
          model: 'ep-20251121103725-r4j64'
        }
      };
    },
    
    // ==================== 组件方法（Methods） ====================
    
    methods: {
      /**
       * ========================================================================
       * submitQuestion - 提交用户问题并调用AI（核心方法）
       * ========================================================================
       * 
       * 功能：
       * 1. 验证用户输入（非空且未加载中）
       * 2. 构建消息列表（系统提示词 + 历史对话 + 当前问题）
       * 3. 调用豆包API（HTTP POST请求）
       * 4. 解析AI回复
       * 5. 更新对话历史
       * 6. 触发父组件事件（通知父组件更新UI）
       * 7. 异常处理（API失败、网络错误等）
       * 
       * 参数：无
       * 返回：Promise<void>
       * 
       * 调用时机：
       * - 用户点击"发送"按钮
       * - 用户在输入框按下回车键（@keyup.enter）
       * 
       * 流程图：
       * 用户输入 → 验证 → 构建消息 → 调用API → 解析响应 → 更新历史 → 触发事件
       */
      async submitQuestion() {
        // ===== 第1步：验证输入 =====
        /**
         * 验证条件：
         * 1. 问题不能为空（!this.question）
         * 2. 不能重复提交（isLoading=true时禁止）
         * 
         * 如果不满足条件，直接返回（不执行后续逻辑）
         */
        if (!this.question || this.isLoading) return;
        
        // ===== 第2步：保存问题并清空输入框 =====
        /**
         * 操作顺序：
         * 1. 保存当前问题到局部变量（trim去除首尾空格）
         * 2. 清空输入框（this.question = ''）
         * 3. 设置加载状态（禁用交互）
         * 
         * 为什么先保存再清空？
         * - 让用户立即看到输入框已清空（UX优化）
         * - 避免用户重复提交相同问题
         */
        const userQuestion = this.question.trim();  // 保存并去除空格
        this.question = '';  // 清空输入框（立即反馈）
        this.isLoading = true;  // 设置加载状态（禁用按钮）
        
        // ===== 第3步：调用AI API（try-catch异常处理） =====
        try {
          // ----- 3.1 构建消息列表 -----
          /**
           * messages: AI对话的完整上下文
           * 类型：Array<Object>
           * 结构：[
           *   { role: 'system', content: '系统提示词' },  // AI的角色定位
           *   { role: 'user', content: '历史问题1' },     // 用户历史问题
           *   { role: 'assistant', content: '历史回复1' }, // AI历史回复
           *   { role: 'user', content: '当前问题' }       // 当前用户问题
           * ]
           * 
           * 角色说明：
           * - system: 系统提示词（定义AI的角色、回复格式）
           * - user: 用户消息
           * - assistant: AI回复
           * 
           * 为什么包含历史对话？
           * - 让AI理解上下文（记忆之前的对话）
           * - 提升对话连贯性
           * 
           * 示例：
           * 用户："头痛 发热"
           * AI："可能是感冒"
           * 用户："需要吃药吗"（AI能记住"感冒"）
           * AI："可以吃退烧药"
           */
          const messages = [
            // ===== 系统提示词（定义AI角色） =====
            {
              role: 'system',  // 角色：系统（定义AI行为）
              content: `你是一个专业的医学辅助诊断助手，专注于内科和外科疾病筛查。
              根据症状分析可能的疾病，提供就医建议。回复格式：
              症状分析 | 可能疾病 | 建议科室 | 紧急程度 | 就医建议`
            },
            
            // ===== 历史对话（上下文记忆） =====
            /**
             * 扩展运算符（...）：
             * - 将数组元素展开（解包）
             * - 示例：
             *   conversationHistory = [
             *     { role: 'user', content: 'A' },
             *     { role: 'assistant', content: 'B' }
             *   ]
             *   
             *   展开后：
             *   messages = [
             *     { role: 'system', content: '...' },
             *     { role: 'user', content: 'A' },
             *     { role: 'assistant', content: 'B' },
             *     { role: 'user', content: 'C' }
             *   ]
             */
            ...this.conversationHistory,
            
            // ===== 当前用户问题 =====
            { role: 'user', content: userQuestion }
          ];
          
          // ----- 3.2 调用豆包API（HTTP POST请求） -----
          /**
           * fetch(): 现代浏览器的HTTP请求API
           * 替代：XMLHttpRequest、axios
           * 优点：原生支持、Promise、简洁
           * 
           * 请求配置：
           * - method: 'POST'（发送数据）
           * - headers: 请求头
           *   - Content-Type: 告诉服务器请求体是JSON格式
           *   - Authorization: API密钥（Bearer Token认证）
           * - body: 请求体（JSON字符串）
           *   - model: 模型ID
           *   - messages: 对话历史
           *   - max_tokens: 最大回复长度（500个token）
           *   - temperature: 随机性（0.7，范围0~1）
           *   - stream: 是否流式输出（false）
           */
          const response = await fetch(this.apiConfig.url, {
            method: 'POST',  // HTTP方法
            
            // ===== 请求头 =====
            headers: {
              // Content-Type: 声明请求体格式为JSON
              'Content-Type': 'application/json',
              
              // Authorization: API密钥认证（Bearer Token模式）
              // 格式：Bearer <密钥>
              'Authorization': `Bearer ${this.apiConfig.key}`
            },
            
            // ===== 请求体 =====
            /**
             * JSON.stringify(): 将对象转为JSON字符串
             * 
             * 参数说明：
             * - model: 模型ID（接入点ID）
             * - messages: 对话历史（包含系统提示词）
             * - max_tokens: 最大回复长度
             *   - 范围：1~4096
             *   - 建议：500（平衡回复质量和速度）
             *   - 说明：1 token ≈ 1.5个汉字
             * - temperature: 随机性/创造性
             *   - 范围：0~1
             *   - 0: 确定性回复（每次相同）
             *   - 1: 高随机性（每次不同）
             *   - 0.7: 平衡（推荐）
             * - stream: 是否流式输出
             *   - false: 一次性返回完整回复
             *   - true: 逐字返回（需处理SSE）
             */
            body: JSON.stringify({
              model: this.apiConfig.model,  // 模型ID
              messages: messages,  // 对话历史
              max_tokens: 500,  // 最大回复长度（约750个汉字）
              temperature: 0.7,  // 随机性（平衡模式）
              stream: false  // 非流式（一次性返回）
            })
          });
          
          // ----- 3.3 检查HTTP响应状态 -----
          /**
           * response.ok: 快速检查HTTP状态码
           * - true: 2xx（成功）
           * - false: 4xx/5xx（失败）
           * 
           * 常见错误：
           * - 401: 认证失败（密钥错误）
           * - 403: 权限不足（密钥未授权）
           * - 404: 接入点不存在
           * - 429: 请求频率超限
           * - 500: 服务器错误
           */
          if (!response.ok) {
            // 解析错误响应体
            const errorData = await response.json();
            
            // 抛出自定义错误（包含状态码和错误详情）
            throw new Error(`API失败: ${response.status} - ${JSON.stringify(errorData)}`);
          }
          
          // ----- 3.4 解析成功响应 -----
          /**
           * 响应格式（豆包API）：
           * {
           *   "choices": [
           *     {
           *       "message": {
           *         "role": "assistant",
           *         "content": "根据您的症状..."
           *       }
           *     }
           *   ]
           * }
           */
          const data = await response.json();  // 解析JSON响应体
          const aiReply = data.choices[0].message.content;  // 提取AI回复内容
          
          // ----- 3.5 更新对话历史 -----
          /**
           * 作用：
           * - 保存当前对话到历史记录
           * - 用于下次请求的上下文
           * 
           * 添加内容：
           * 1. 用户问题 { role: 'user', content: '...' }
           * 2. AI回复 { role: 'assistant', content: '...' }
           */
          this.conversationHistory.push(
            { role: 'user', content: userQuestion },  // 用户问题
            { role: 'assistant', content: aiReply }  // AI回复
          );
          
          // ----- 3.6 限制历史长度（防止上下文过长） -----
          /**
           * 为什么限制长度？
           * - API有token限制（输入+输出不能超过模型上限）
           * - 过长的历史会增加请求成本
           * - 太旧的对话不再相关
           * 
           * 策略：
           * - 最多保留8条消息（4轮对话）
           * - 超过时，删除最早的对话
           * 
           * slice(-8): 从末尾取8个元素
           * 示例：
           * [1,2,3,4,5,6,7,8,9,10].slice(-8) → [3,4,5,6,7,8,9,10]
           */
          if (this.conversationHistory.length > 8) {
            this.conversationHistory = this.conversationHistory.slice(-8);
          }
          
          // ----- 3.7 触发父组件事件（通知UI更新） -----
          /**
           * $emit(): Vue事件触发器
           * 作用：通知父组件处理AI回复
           * 
           * 参数：
           * - 事件名：'ask-question'
           * - 事件数据：{ question, answer }
           * 
           * 父组件监听：
           * <ai-coach-plan @ask-question="handleAiReply"></ai-coach-plan>
           * 
           * methods: {
           *   handleAiReply(data) {
           *     console.log(data.question, data.answer);
           *     // 将消息添加到coachList显示
           *   }
           * }
           */
          this.$emit('ask-question', {
            question: userQuestion,  // 用户问题
            answer: aiReply  // AI回复
          });
          
        // ===== 第4步：异常处理 =====
        } catch (error) {
          /**
           * 捕获所有可能的错误：
           * - 网络错误（无法连接服务器）
           * - HTTP错误（4xx/5xx状态码）
           * - 解析错误（响应体不是JSON）
           * - 超时错误（请求超时）
           */
          
          // 打印错误日志（便于调试）
          console.error('AI调用失败:', error);
          
          // 通知父组件显示错误消息
          this.$emit('ask-question', {
            question: userQuestion,  // 用户问题
            answer: '抱歉，AI助手暂时无法回复。请稍后再试或直接咨询医生。',  // 友好错误提示
            error: true  // 标记为错误（父组件可以显示不同样式）
          });
          
        // ===== 第5步：最终清理（finally） =====
        } finally {
          /**
           * finally块：
           * - 无论成功或失败都会执行
           * - 用于清理资源、恢复状态
           * 
           * 作用：
           * - 恢复加载状态（isLoading = false）
           * - 重新启用按钮和输入框
           */
          this.isLoading = false;
        }
      }
    }
  };
</script>

  

<style lang="less" scoped>
.panel {
  padding: 15px;
  box-sizing: border-box;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.panel-title {
  font-size: 18px;
  font-weight: bold;
}
.message-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 15px;
  padding-right: 5px;
}
.message-card {
  padding: 12px;
  border-radius: 12px;
  background: rgba(16, 45, 80, 0.6);
  transition: all 0.3s;
}
.message-card:hover {
  background: rgba(16, 45, 80, 0.8);
}
.message-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(57, 175, 253, 0.3);
  color: #39affd;
  font-size: 12px;
  margin-bottom: 8px;
}
.message-title {
  font-weight: bold;
  margin-bottom: 8px;
}
.message-content {
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 8px;
}
.message-time {
  font-size: 12px;
  color: #6ea1ff;
  text-align: right;
}
.empty-message {
  padding: 30px;
  text-align: center;
  color: #6ea1ff;
}
.coach-input {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
.coach-input input {
  flex: 1;
  border-radius: 20px;
  border: 1px solid rgba(57, 175, 253, 0.5);
  background: rgba(255, 255, 255, 0.1);
  padding: 8px 15px;
  color: #fff;
}
.coach-input input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.coach-input button {
  padding: 0 15px;
  border-radius: 20px;
  border: none;
  background: linear-gradient(90deg, #2af7ff, #26b3ff);
  color: #142c4d;
  cursor: pointer;
}
.coach-input button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
