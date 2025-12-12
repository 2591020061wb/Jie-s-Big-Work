<template>
  <div class="ai-companion-container">
    <dv-border-box-10>
      <div class="naca">
        <div class="page-header">
          <h1>AI心理陪伴助手</h1>
          <p>24小时在线的智能心理支持伙伴</p>
        </div>

        <div class="ai-content">
          <!-- 左侧聊天区域 -->
          <div class="chat-panel">
            <dv-border-box-12>
              <div class="panel-content">
                <div class="chat-header">
                  <div class="ai-avatar">🤖</div>
                  <div class="ai-info">
                    <div class="ai-name">心理健康助手</div>
                    <div class="ai-status">在线 · 随时为您服务</div>
                  </div>
                </div>

                <div class="chat-messages-container">
                  <div class="chat-messages" ref="messagesContainer">
                    <div 
                      v-for="(message, index) in chatMessages" 
                      :key="index"
                      :class="['message', message.type]"
                    >
                      <div class="message-content">
                        {{ message.content }}
                      </div>
                      <div class="message-time">{{ message.time }}</div>
                    </div>
                    <div v-if="isLoading" class="message ai">
                      <div class="message-content">
                        <div class="loading-dots">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="chat-input-area">
                  <div class="quick-replies">
                    <div 
                      v-for="reply in quickReplies" 
                      :key="reply"
                      class="quick-reply"
                      @click="sendQuickReply(reply)"
                    >
                      {{ reply }}
                    </div>
                  </div>
                  
                  <div class="input-container">
                    <input 
                      v-model="userInput" 
                      @keyup.enter="sendMessage"
                      placeholder="告诉我您的心情和想法..."
                      class="chat-input"
                      :disabled="isLoading"
                    />
                    <button @click="sendMessage" class="send-btn" :disabled="isLoading">
                      {{ isLoading ? '发送中...' : '发送' }}
                    </button>
                  </div>
                </div>
              </div>
            </dv-border-box-12>
          </div>

          <!-- 右侧功能区域 -->
          <div class="function-panel">
            <dv-border-box-9>
              <div class="panel-content">
                <div class="title">情绪分析</div>
                <div class="emotion-analysis">
                  <div class="emotion-score">
                    <div class="score-value">{{ currentEmotion.score }}/10</div>
                    <div class="score-label">情绪分数</div>
                  </div>
                  <div class="emotion-type">
                    <div class="type-value">{{ currentEmotion.type }}</div>
                    <div class="type-label">情绪类型</div>
                  </div>
                </div>
              </div>
            </dv-border-box-9>

            <dv-border-box-3 style="margin-top: 20px">
              <div class="panel-content">
                <div class="title">放松工具</div>
                <div class="relaxation-tools">
                  <div class="tool-card" @click="startBreathingExercise">
                    <div class="tool-icon">🌬️</div>
                    <div class="tool-name">呼吸练习</div>
                  </div>
                  <div class="tool-card" @click="playRelaxationMusic">
                    <div class="tool-icon">{{ isMusicPlaying ? '⏸️' : '🎵' }}</div>
                    <div class="tool-name">{{ isMusicPlaying ? '暂停音乐' : '放松音乐' }}</div>
                    <!-- 添加播放状态指示器 -->
                    <div v-if="isMusicPlaying" class="music-status-indicator">
                      <div class="playing-animation">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                  <div class="tool-card" @click="showMindfulnessTips">
                    <div class="tool-icon">🧘</div>
                    <div class="tool-name">正念提示</div>
                  </div>
                </div>
              </div>
            </dv-border-box-3>

            <dv-border-box-8 style="margin-top: 20px">
              <div class="panel-content">
                <div class="title">今日建议</div>
                <div class="daily-tips">
                  <div class="tip-item" v-for="(tip, index) in dailyTips" :key="index">
                    {{ tip }}
                  </div>
                </div>
              </div>
            </dv-border-box-8>
          </div>
        </div>
      </div>
    </dv-border-box-10>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AICompanion',
  data() {
    return {
      userInput: '',
      chatMessages: [
        {
          type: 'ai',
          content: '您好！我是您的心理健康助手，今天有什么想和我聊聊的吗？',
          time: this.getCurrentTime()
        }
      ],
      quickReplies: [
        '我今天心情不太好',
        '感觉压力很大',
        '睡不着怎么办',
        '如何缓解焦虑'
      ],
      currentEmotion: {
        score: 5,
        type: '中性'
      },
      dailyTips: [
        '尝试深呼吸5分钟缓解压力',
        '记录三件今天让您感恩的事情',
        '适当运动有助于改善情绪',
        '保持规律的作息时间'
      ],
      isLoading: false,
      // API 配置
      apiConfig: {
        baseURL: 'https://ark.cn-beijing.volces.com/api/v3',
        apiKey: '2c9f9e15-5895-44db-858d-0d5e6dd7ac97',
        model: 'ep-20251121103725-r4j64'
      },
      audio: null,
      isMusicPlaying: false,
      musicSrc: '/music/River Flows in You.mp3',
    }
  },
  methods: {
    async sendMessage() {
      if (!this.userInput.trim() || this.isLoading) return
      
      // 添加用户消息
      this.addUserMessage(this.userInput)
      const userMessage = this.userInput
      this.userInput = ''
      this.isLoading = true
      
      try {
        // 发送到 AI
        const response = await this.callAIAPI(userMessage)
        this.addAIMessage(response)
        
        // 分析情绪
        this.analyzeEmotion(userMessage)
        
      } catch (error) {
        console.error('AI回复失败:', error)
        this.addAIMessage('抱歉，我现在遇到了一些技术问题。您可以尝试重新发送消息，或者稍后再试。')
      } finally {
        this.isLoading = false
      }
    },
    
    async callAIAPI(message) {
      try {
        const response = await axios.post(`${this.apiConfig.baseURL}/chat/completions`, {
          model: this.apiConfig.model,
          messages: [
            {
              role: 'system',
              content: `你是一个专业的心理健康助手，具有以下特点：
              1. 用温暖、支持性、共情的语言回应
              2. 提供心理支持但不进行医疗诊断
              3. 鼓励积极的应对策略
              4. 在必要时建议寻求专业帮助
              5. 保持回复简洁明了（100-200字）
              6. 使用中文回复
              
              请记住：你不是医生，不能提供医疗建议。如果用户提到自杀、自伤等紧急情况，请建议立即联系专业帮助。`
            },
            {
              role: 'user',
              content: message
            }
          ],
          max_tokens: 500,
          temperature: 0.7,
          stream: false
        }, {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.apiConfig.apiKey}`
          }
        })

        return response.data.choices[0].message.content
      } catch (error) {
        console.error('API调用失败:', error)
        throw new Error('API请求失败')
      }
    },
    
    addUserMessage(content) {
      this.chatMessages.push({
        type: 'user',
        content: content,
        time: this.getCurrentTime()
      })
      this.scrollToBottom()
    },
    
    addAIMessage(content) {
      this.chatMessages.push({
        type: 'ai',
        content: content,
        time: this.getCurrentTime()
      })
      this.scrollToBottom()
    },
    
    analyzeEmotion(message) {
      // 简单的情绪分析逻辑
      const positiveWords = ['开心', '高兴', '快乐', '满意', '幸福', '兴奋', '很好', '不错']
      const negativeWords = ['难过', '悲伤', '痛苦', '抑郁', '焦虑', '紧张', '愤怒', '恐惧', '压力', '睡不着', '难受']
      
      let positiveCount = 0
      let negativeCount = 0
      
      positiveWords.forEach(word => {
        if (message.includes(word)) positiveCount++
      })
      
      negativeWords.forEach(word => {
        if (message.includes(word)) negativeCount++
      })
      
      if (positiveCount > negativeCount) {
        this.currentEmotion = { score: 8, type: '积极' }
      } else if (negativeCount > positiveCount) {
        this.currentEmotion = { score: 3, type: '消极' }
      } else {
        this.currentEmotion = { score: 5, type: '中性' }
      }
    },
    
    sendQuickReply(reply) {
      this.userInput = reply
      this.sendMessage()
    },
    
    startBreathingExercise() {
      this.addAIMessage('让我们开始呼吸练习：吸气4秒，屏息4秒，呼气6秒。重复5次，感受身体的放松。专注于呼吸的节奏，让思绪慢慢平静下来。')
    },
    
    playRelaxationMusic() {
    if (!this.audio) {
      this.initAudio()
    }

    try {
      if (this.isMusicPlaying) {
      // 如果正在播放，则暂停
        this.audio.pause()
        this.isMusicPlaying = false
        this.addAIMessage('已暂停播放放松音乐。需要时请再次点击播放按钮。')
      } else {
      // 如果未播放，则开始播放
        this.audio.play().then(() => {
        this.isMusicPlaying = true
        this.addAIMessage('正在为您播放放松音乐《River Flows in You》。这首钢琴曲能帮助您放松心情，缓解压力。')
        }).catch(error => {
          console.error('播放失败:', error)
        // 处理自动播放策略限制
            if (error.name === 'NotAllowedError') {
              this.addAIMessage('为了播放音乐，请先点击页面其他地方激活音频播放权限，然后再点击放松音乐按钮。')
            }
          })
        }
      }   catch (error) {
        console.error('音乐播放错误:', error)
        this.addAIMessage('音乐播放失败，请稍后再试')
      }
    },
    
    showMindfulnessTips() {
      this.addAIMessage('正念提示：专注于当下的感受，不加评判地观察您的想法和情绪。尝试将注意力集中在呼吸上，感受空气进出身体的感觉。')
    },
    
    getCurrentTime() {
      return new Date().toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    },
    initAudio() {
    // 注意：浏览器不支持直接使用本地文件路径
    // 需要将音乐文件放到 public 目录下，然后使用相对路径
      this.audio = new Audio('/music/River Flows in You.mp3')
      this.audio.loop = true // 设置为循环播放

    // 添加事件监听
      this.audio.addEventListener('play', () => {
      this.isMusicPlaying = true
      })

      this.audio.addEventListener('pause', () => {
      this.isMusicPlaying = false
      })

    // 错误处理
      this.audio.addEventListener('error', (e) => {
      console.error('音频加载失败:', e)
      this.addAIMessage('音乐加载失败，请检查音乐文件路径')
      })
    }
  },
  beforeDestroy() {
    if (this.audio) {
      this.audio.pause()
      this.audio = null
    }
  },
  mounted() {
    this.scrollToBottom()
    this.initAudio()
  }
}
</script>

<style lang="less" scoped>
.ai-companion-container {
  width: 100%;
  min-height: 100vh;
  padding: 20px;
  box-sizing: border-box;
}

.naca {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
  padding: 0 20px;
  
  h1 {
    color: #3de7c9;
    font-size: 28px;
    margin-bottom: 10px;
  }
  
  p {
    color: #ccc;
    font-size: 16px;
  }
}

.ai-content {
  display: flex;
  padding: 20px;
  gap: 20px;
  flex: 1;
  min-height: 600px;
}

.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 600px;
  height: 65vh; 
}

.function-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
}

.panel-content {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.chat-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.ai-avatar {
  font-size: 32px;
  margin-right: 15px;
}

.ai-name {
  color: #3de7c9;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 4px;
}

.ai-status {
  color: #00ff88;
  font-size: 12px;
}

/* 修复聊天消息区域的滚动问题 */
.chat-messages-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin-bottom: 20px;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding-right: 10px;
  min-height: 300px;
  max-height: 500px;
  
  /* 自定义滚动条样式 */
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #3de7c9;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: #2bc7a9;
  }
}

.message {
  margin-bottom: 15px;
  max-width: 80%;
  
  &.user {
    margin-left: auto;
    
    .message-content {
      background: linear-gradient(45deg, #3de7c9, #568aea);
      color: #000;
    }
  }
  
  &.ai {
    margin-right: auto;
    
    .message-content {
      background: rgba(255, 255, 255, 0.1);
      color: #fff;
    }
  }
}

.message-content {
  padding: 12px 16px;
  border-radius: 18px;
  line-height: 1.4;
  word-wrap: break-word;
}

.message-time {
  font-size: 11px;
  color: #888;
  margin-top: 4px;
  text-align: right;
}

.user .message-time {
  text-align: right;
}

.ai .message-time {
  text-align: left;
}

.loading-dots {
  display: flex;
  gap: 4px;
  
  span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #3de7c9;
    animation: bounce 1.4s infinite ease-in-out both;
    
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
}

@keyframes bounce {
  0%, 80%, 100% { 
    transform: scale(0);
  } 40% { 
    transform: scale(1.0);
  }
}

/* 修复输入区域在边框内的问题 */
.chat-input-area {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 15px;
  flex-shrink: 0;
  margin-top: auto;
}

.quick-replies {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 15px;
}

.quick-reply {
  background: rgba(255, 255, 255, 0.1);
  color: #ccc;
  padding: 6px 12px;
  border-radius: 15px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(61, 231, 201, 0.2);
    color: #3de7c9;
  }
}

.input-container {
  display: flex;
  gap: 10px;
  align-items: center;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #3de7c9;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 14px;
  
  &::placeholder {
    color: #888;
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.send-btn {
  padding: 12px 24px;
  background: #3de7c9;
  border: none;
  border-radius: 8px;
  color: #000;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  
  &:hover:not(:disabled) {
    background: #2bc7a9;
    transform: translateY(-2px);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
}

.emotion-analysis {
  display: flex;
  justify-content: space-around;
  margin-top: 15px;
}

.emotion-score,
.emotion-type {
  text-align: center;
}

.score-value,
.type-value {
  color: #3de7c9;
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.score-label,
.type-label {
  color: #ccc;
  font-size: 12px;
}

.relaxation-tools {
  display: flex;
  justify-content: space-around;
  margin-top: 15px;
}
.music-status-indicator {
  position: absolute;
  top: 5px;
  right: 5px;
}

.playing-animation {
  display: flex;
  align-items: flex-end;
  height: 15px;
  gap: 2px;
}

.playing-animation span {
  width: 3px;
  background-color: #3de7c9;
  border-radius: 1px;
  animation: music-bars 1.4s ease-in-out infinite;
}

.playing-animation span:nth-child(1) {
  height: 4px;
  animation-delay: 0s;
}
.playing-animation span:nth-child(2) {
  height: 8px;
  animation-delay: 0.2s;
}
.playing-animation span:nth-child(3) {
  height: 4px;
  animation-delay: 0.4s;
}

@keyframes music-bars {
  0%, 100% {
    transform: scaleY(1);
  }
  50% {
    transform: scaleY(0.5);
  }
}

.tool-card {
  position: relative;
  text-align: center;
  padding: 15px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(61, 231, 201, 0.2);
    transform: translateY(-2px);
  }
}

.tool-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.tool-name {
  color: #fff;
  font-size: 12px;
}

.daily-tips {
  margin-top: 15px;
}

.tip-item {
  color: #ccc;
  font-size: 14px;
  line-height: 1.5;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  &:last-child {
    border-bottom: none;
  }
}

.title {
  color: #3f96a5;
  font-size: 18px;
  text-align: center;
  margin-bottom: 15px;
  font-weight: bold;
}
</style>