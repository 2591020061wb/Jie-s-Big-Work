// utils/doubao.js
export const DoubaoAPI = {
    apiKey: '2c9f9e15-5895-44db-858d-0d5e6dd7ac97',
    apiUrl: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
    
    async sendMessage(message, conversationHistory = []) {
      const messages = [
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
        ...conversationHistory,
        {
          role: 'user',
          content: message
        }
      ]
      
      const requestBody = {
        model: 'doubao-1.0-pro-256k', // 根据实际可用模型调整
        messages: messages,
        max_tokens: 500,
        temperature: 0.7,
        stream: false
      }
      
      try {
        const response = await fetch(this.apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.apiKey}`
          },
          body: JSON.stringify(requestBody)
        })
        
        if (!response.ok) {
          throw new Error(`API请求失败: ${response.status}`)
        }
        
        const data = await response.json()
        return data.choices[0].message.content
      } catch (error) {
        console.error('豆包API调用失败:', error)
        throw error
      }
    }
  }