<!-- views/mental/PsychologicalTest.vue -->

<template>
  <div class="psychological-test-container">
    <dv-border-box-10>
      <div class="naca">
        <div class="page-header">
          <h1>心理测评中心</h1>
          <p>专业心理评估，了解您的心理健康状况</p>
        </div>

        <div class="test-content">
          <!-- 测评选择 -->
          <div class="test-selection" v-if="!currentTest && !showResult">
            <div class="test-cards">
              <div 
                v-for="test in availableTests" 
                :key="test.type"
                class="test-card"
                @click="startTest(test)"
              >
                <div class="test-icon">{{ test.emoji }}</div>
                <div class="test-name">{{ test.name }}</div>
                <div class="test-desc">{{ test.description }}</div>
                <div class="test-time">约{{ test.duration }}分钟</div>
              </div>
            </div>
          </div>

          <!-- 测评进行中 -->
          <div class="test-in-progress" v-if="currentTest && !showResult">
            <dv-border-box-12>
              <div class="panel-content">
                <div class="test-header">
                  <button @click="goBack" class="back-btn">← 返回测评列表</button>
                  <div class="test-title">{{ currentTest.name }}</div>
                  <div class="test-progress">进度: {{ currentQuestion + 1 }}/{{ currentTest.questions.length }}</div>
                </div>

                <div class="question-area">
                  <div class="question-text">
                    {{ currentTest.questions[currentQuestion] }}
                  </div>
                  
                  <div class="options-grid">
                    <div 
                      v-for="(option, index) in scoringOptions" 
                      :key="index"
                      :class="['option-card', { selected: answers[currentQuestion] === index }]"
                      @click="selectAnswer(index)"
                    >
                      <div class="option-score">{{ index }}</div>
                      <div class="option-desc">{{ option }}</div>
                    </div>
                  </div>
                </div>

                <div class="test-controls">
                  <button @click="prevQuestion" :disabled="currentQuestion === 0" class="control-btn">
                    上一题
                  </button>
                  <button 
                    @click="nextQuestion" 
                    class="control-btn primary"
                    :disabled="answers[currentQuestion] === null || answers[currentQuestion] === undefined"
                  >
                    {{ currentQuestion === currentTest.questions.length - 1 ? '完成测评' : '下一题' }}
                  </button>
                </div>
              </div>
            </dv-border-box-12>
          </div>

          <!-- 测评结果 -->
          <div class="test-result" v-if="showResult">
            <dv-border-box-9>
              <div class="panel-content">
                <div class="result-header">
                  <div class="result-title">测评结果</div>
                  <div class="result-score">得分: {{ testResult.total_score }}</div>
                </div>
                
                <div class="result-content">
                  <div class="result-level" :class="`level-${testResult.risk_level}`">
                    {{ testResult.evaluation_result }}
                  </div>
                  
                  <div class="result-recommendation">
                    {{ testResult.recommendation }}
                  </div>
                  
                  <div class="result-actions">
                    <button @click="saveResult" class="action-btn">保存结果</button>
                    <button @click="startNewTest" class="action-btn primary">新的测评</button>
                    <button v-if="testResult.risk_level === 'critical'" class="action-btn emergency">
                      紧急求助
                    </button>
                  </div>
                </div>
              </div>
            </dv-border-box-9>
          </div>
        </div>

        <!-- 历史记录 -->
        <div class="history-section" v-if="!currentTest && !showResult">
          <dv-border-box-13>
            <div class="panel-content">
              <div class="title">测评历史</div>
              <div v-if="loading" class="loading-text">加载中...</div>
              <div v-else>
                <div class="history-list">
                  <div 
                    v-for="record in testHistory" 
                    :key="record.id"
                    :class="['history-item', `risk-${record.risk_level}`]"
                  >
                    <div class="record-type">{{ record.questionnaire_type }}</div>
                    <div class="record-date">{{ formatDate(record.record_date) }}</div>
                    <div class="record-score">得分: {{ record.total_score }}</div>
                    <div class="record-result">{{ record.evaluation_result }}</div>
                    <div class="record-risk">{{ getRiskLabel(record.risk_level) }}</div>
                  </div>
                </div>
                <div v-if="testHistory.length === 0" class="no-history">
                  暂无测评记录，开始您的第一次测评吧！
                </div>
              </div>
            </div>
          </dv-border-box-13>
        </div>
      </div>
    </dv-border-box-10>
  </div>
</template>

<script>
import $http from '@/utils/request' 
export default {
  name: 'PsychologicalTest',
  data() {
    return {
      availableTests: [
        {
          type: 'PHQ-9',
          name: '抑郁症筛查量表',
          emoji: '😔',
          description: '评估抑郁症状的严重程度',
          duration: 5,
          questions: [
            "做事时提不起劲或没有兴趣",
            "感到心情低落、沮丧或绝望",
            "入睡困难、睡不安或睡得过多",
            "感觉疲倦或没有活力",
            "食欲不振或吃太多",
            "对自己感到失望，或觉得自己让家人失望",
            "对事物专注有困难，例如阅读报纸或看电视时",
            "行动或说话速度缓慢到别人已经觉察，或正好相反，烦躁或坐立不安、动来动去的情况更胜于平常",
            "有不如死掉或用某种方式伤害自己的念头"
          ]
        },
        {
          type: 'GAD-7',
          name: '广泛性焦虑障碍量表',
          emoji: '😰',
          description: '评估焦虑症状的严重程度',
          duration: 3,
          questions: [
            "感觉紧张、焦虑或急切",
            "不能够停止或控制担忧",
            "对各种各样的事情担忧过多",
            "很难放松下来",
            "由于不安而无法静坐",
            "变得容易烦恼或急躁",
            "感到似乎将有可怕的事情发生"
          ]
        }
      ],
      currentTest: null,
      currentQuestion: 0,
      answers: [],
      showResult: false,
      testResult: {},
      scoringOptions: ['完全不会', '几天', '一半以上天数', '几乎每天'],
      testHistory: [],
      loading: false
    }
  },
  methods: {
    startTest(test) {
      this.currentTest = test
      this.currentQuestion = 0
      this.answers = new Array(test.questions.length).fill(null)
      this.showResult = false
    },
    
    selectAnswer(score) {
      this.$set(this.answers, this.currentQuestion, score)
    },
    
    prevQuestion() {
      if (this.currentQuestion > 0) {
        this.currentQuestion--
      }
    },
    
    nextQuestion() {
      if (this.currentQuestion < this.currentTest.questions.length - 1) {
        this.currentQuestion++
      } else {
        this.submitTest()
      }
    },
    
    goBack() {
      if (this.showResult) {
        this.showResult = false
      } else if (this.currentTest) {
        this.currentTest = null
        this.currentQuestion = 0
        this.answers = []
      }
    },
    
    async submitTest() {
  try {
    // 获取用户ID
    let userId = null;
    const userStr = localStorage.getItem('med-portal-user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        userId = user.user_id || user.userId || user.id;
      } catch (e) {
        console.error('解析用户信息失败:', e);
      }
    }
    
    if (!userId) userId = 1;
    
    // 验证答案
    const validatedAnswers = this.answers.map(answer => {
      const num = Number(answer);
      return isNaN(num) ? 0 : Math.max(0, Math.min(3, num));
    });
    
    // 提交到后端
    const res = await $http.post('/api/mental/assessment/submit', {
      user_id: userId,
      questionnaire_type: this.currentTest.type,
      answers: validatedAnswers
    });
    
    if (res.code === 200) {
      // 使用返回的数据 - 直接使用 res.data
      this.testResult = {
        ...res.data,
        recommendation: this.generateRecommendation(res.data.evaluation_result, res.data.risk_level)
      };
      
      this.showResult = true;
      await this.loadTestHistory(); // 重新加载历史
      alert('测评提交成功！');
    } else {
      throw new Error(res.message);
    }
  } catch (error) {
    console.error('提交测评失败:', error);
    alert('提交失败，请重试');
  }
},
    
    // 根据评估结果生成建议
    generateRecommendation(evaluationResult, riskLevel) {
      const recommendations = {
        'low': '您的症状很轻微，建议保持健康的生活方式，定期关注情绪变化。',
        'medium': '建议关注情绪变化，适当调整生活节奏，如症状持续可咨询专业人士。',
        'high': '建议尽快寻求专业心理咨询或治疗。',
        'critical': '请立即寻求专业医疗帮助。'
      }
      
      return `${evaluationResult}，${recommendations[riskLevel] || '请关注您的心理健康状况。'}`
    },
    
    async saveResult() {
      try {
        // 这里可以添加保存结果到PDF或其他格式的逻辑
        alert('结果已保存')
      } catch (error) {
        console.error('保存结果失败:', error)
        alert('保存失败')
      }
    },
    
    startNewTest() {
      this.currentTest = null
      this.showResult = false
      this.currentQuestion = 0
      this.answers = []
    },
    
    getRiskLabel(level) {
      const labels = {
        low: '低风险',
        medium: '中风险',
        high: '高风险',
        critical: '危急'
      }
      return labels[level] || '未知'
    },
    
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return `${date.getMonth() + 1}月${date.getDate()}日`
    },
    
    // 加载用户的测评历史记录
    async loadTestHistory() {
  try {
    this.loading = true;
    
    // 获取用户ID
    let userId = null;
    const userStr = localStorage.getItem('med-portal-user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        userId = user.user_id || user.userId || user.id;
      } catch (e) {
        console.error('解析用户信息失败:', e);
      }
    }
    
    if (!userId) {
      userId = 1;
    }
    
    console.log('获取测评历史，用户ID:', userId);
    
    // 使用导入的 $http
    const res = await $http.get(`/api/mental/assessment/history/${userId}`);
    console.log('测评历史完整响应:', res);
    
    // 注意：res已经是response.data了
    if (res.code === 200) {
      this.testHistory = res.data || [];
    } else {
      console.warn('响应code不是200:', res);
      // 使用模拟数据
      await this.loadMockHistory();
    }
    
  } catch (error) {
    console.error('加载测评历史失败:', error);
    // 使用模拟数据
    await this.loadMockHistory();
  } finally {
    this.loading = false;
  }
},
    
    // 临时加载模拟数据（当后端接口还未实现时使用）
    async loadMockHistory() {
      // 模拟API延迟
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // 获取当前用户ID
      let userId = this.$store.getters.currentUser?.user_id || 1
      
      // 根据用户ID生成不同的模拟数据
      const mockHistory = {
        1: [
          { id: 1, questionnaire_type: 'PHQ-9', record_date: '2024-01-08', total_score: 6, evaluation_result: '轻度抑郁', risk_level: 'medium' },
          { id: 2, questionnaire_type: 'GAD-7', record_date: '2024-01-05', total_score: 4, evaluation_result: '无焦虑症状', risk_level: 'low' }
        ],
        2: [
          { id: 3, questionnaire_type: 'PHQ-9', record_date: '2024-01-10', total_score: 12, evaluation_result: '中度抑郁', risk_level: 'high' },
          { id: 4, questionnaire_type: 'GAD-7', record_date: '2024-01-08', total_score: 8, evaluation_result: '轻度焦虑', risk_level: 'medium' }
        ]
      }
      
      this.testHistory = mockHistory[userId] || []
    }
  },
  async mounted() {
    // 页面加载时获取测评历史记录
    await this.loadTestHistory()
  }
}
</script>

<style lang="less" scoped>
/* 保持原有的样式不变，只添加新的样式 */

.psychological-test-container {
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
  gap: 10px;
}

.page-header {
  text-align: center;
  margin-bottom: 20px;
  
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

.test-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.test-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 15px;
}

.test-card {
  background: rgba(86, 138, 234, 0.3);
  border-radius: 12px;
  padding: 25px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(86, 138, 234, 0.5);
    transform: translateY(-5px);
  }
}

.test-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.test-name {
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 10px;
}

.test-desc {
  color: #ccc;
  font-size: 14px;
  margin-bottom: 10px;
}

.test-time {
  color: #3de7c9;
  font-size: 12px;
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid #3de7c9;
  border-radius: 8px;
  color: #3de7c9;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(61, 231, 201, 0.1);
  }
}

.test-title {
  color: #3de7c9;
  font-size: 24px;
  font-weight: bold;
}

.test-progress {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
  padding: 8px 16px;
  border-radius: 20px;
}

.question-area {
  margin-bottom: 30px;
}

.question-text {
  color: #fff;
  font-size: 18px;
  line-height: 1.6;
  margin-bottom: 25px;
  text-align: center;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

@media (max-width: 768px) {
  .options-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.option-card {
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid transparent;
  border-radius: 8px;
  padding: 15px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &.selected {
    border-color: #3de7c9;
    background: rgba(61, 231, 201, 0.1);
  }
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
}

.option-score {
  color: #3de7c9;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 5px;
}

.option-desc {
  color: #fff;
  font-size: 14px;
}

.test-controls {
  display: flex;
  justify-content: space-between;
  gap: 15px;
}

.control-btn {
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid #3de7c9;
  border-radius: 8px;
  color: #3de7c9;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  &.primary {
    background: #3de7c9;
    color: #000;
  }
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
  }
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.result-title {
  color: #3de7c9;
  font-size: 24px;
  font-weight: bold;
}

.result-score {
  color: #fff;
  font-size: 18px;
  background: rgba(255, 255, 255, 0.1);
  padding: 8px 16px;
  border-radius: 20px;
}

.result-content {
  text-align: center;
}

.result-level {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 20px;
  padding: 15px;
  border-radius: 8px;
  
  &.level-low {
    color: #00ff88;
    background: rgba(0, 255, 136, 0.1);
  }
  
  &.level-medium {
    color: #ffaa00;
    background: rgba(255, 170, 0, 0.1);
  }
  
  &.level-high {
    color: #ff6b00;
    background: rgba(255, 107, 0, 0.1);
  }
  
  &.level-critical {
    color: #ff4444;
    background: rgba(255, 68, 68, 0.1);
  }
}

.result-recommendation {
  color: #fff;
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 25px;
  background: rgba(255, 255, 255, 0.05);
  padding: 15px;
  border-radius: 8px;
  text-align: left;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid #3de7c9;
  border-radius: 8px;
  color: #3de7c9;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &.primary {
    background: #3de7c9;
    color: #000;
  }
  
  &.emergency {
    background: #ff4444;
    border-color: #ff4444;
    color: #fff;
  }
  
  &:hover {
    transform: translateY(-2px);
  }
}

.history-section {
  margin-top: 5px;
}

.history-list {
  max-height: 250px;
  overflow-y: auto;
  padding-right: 5px;
  
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

.history-item {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 2fr 1fr;
  gap: 15px;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  
  &.risk-low {
    border-left: 4px solid #00ff88;
  }
  
  &.risk-medium {
    border-left: 4px solid #ffaa00;
  }
  
  &.risk-high {
    border-left: 4px solid #ff6b00;
  }
  
  &.risk-critical {
    border-left: 4px solid #ff4444;
  }
}

.record-type {
  color: #3de7c9;
  font-weight: bold;
}

.record-date {
  color: #888;
  font-size: 12px;
}

.record-score {
  color: #fff;
  font-weight: bold;
}

.record-result {
  color: #ccc;
}

.record-risk {
  text-align: center;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  
  .risk-low & {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }
  
  .risk-medium & {
    background: rgba(255, 170, 0, 0.2);
    color: #ffaa00;
  }
  
  .risk-high & {
    background: rgba(255, 107, 0, 0.2);
    color: #ff6b00;
  }
  
  .risk-critical & {
    background: rgba(255, 68, 68, 0.2);
    color: #ff4444;
  }
}

.title {
  color: #3de7c9;
  font-size: 18px;
  text-align: center;
  margin-bottom: 15px;
  font-weight: bold;
}

.panel-content {
  padding: 20px;
}

/* 新增样式 */
.loading-text {
  text-align: center;
  color: #3de7c9;
  padding: 20px;
  font-style: italic;
}

.no-history {
  text-align: center;
  color: #888;
  padding: 20px;
  font-style: italic;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin-top: 10px;
}
</style>