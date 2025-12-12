<!-- views/mental/EmotionRecord.vue -->

<template>
  <div class="emotion-record-container">
    <dv-border-box-10>
      <div class="naca">
        <div class="page-header">
          <h1>情绪记录与分析</h1>
          <p>记录您的情绪变化，了解心理状态</p>
        </div>

        <div class="emotion-content">
          <!-- 左侧情绪记录 -->
          <div class="left-panel">
            <dv-border-box-12>
              <div class="panel-content">
                <div class="title">记录今日情绪</div>
                <div class="emotion-input">
                  <textarea 
                    v-model="emotionDescription" 
                    placeholder="描述您今天的心情和感受..."
                    class="emotion-textarea"
                  ></textarea>
                  
                  <div class="emotion-tags">
                    <div 
                      v-for="tag in emotionTags" 
                      :key="tag.name"
                      :class="['emotion-tag', { active: selectedTag === tag.name }]"
                      @click="selectTag(tag.name)"
                    >
                      {{ tag.emoji }} {{ tag.label }}
                    </div>
                  </div>

                  <div class="selected-tag-info" v-if="selectedTag">
                    已选择: {{ getSelectedTagLabel() }}
                  </div>

                  <button @click="recordEmotion" class="record-btn" :disabled="!canSubmit">
                    {{ canSubmit ? '记录情绪' : '请选择情绪标签并输入描述' }}
                  </button>
                </div>
              </div>
            </dv-border-box-12>

            <!-- 在模板中调整日历图表容器高度 -->
<dv-border-box-8 style="margin-top: 20px">
  <div class="panel-content">
    <div class="title">情绪日历</div>
    <div class="chart-container">
      <div class="calendar-header">
        <div class="calendar-title">本月情绪记录</div>
        <div class="calendar-nav">
          <button class="nav-btn" @click="changeMonth(-1)">上个月</button>
          <button class="nav-btn" @click="changeMonth(1)">下个月</button>
        </div>
      </div>
      <div ref="calendarChart" style="width: 100%; height: 220px"></div>
    </div>
  </div>
</dv-border-box-8>
          </div>

          <!-- 右侧情绪分析 -->
          <div class="right-panel">
            <dv-border-box-9>
              <div class="panel-content">
                <div class="title">情绪趋势分析</div>
                <div ref="trendChart" style="width: 100%; height: 250px"></div>
              </div>
            </dv-border-box-9>

            <dv-border-box-3 style="margin-top: 20px">
              <div class="panel-content">
                <div class="title">情绪统计</div>
                <div class="emotion-stats">
                  <div class="stat-card">
                    <div class="stat-value">{{ emotionStats.positive }}</div>
                    <div class="stat-label">积极天数</div>
                  </div>
                  <div class="stat-card">
                    <div class="stat-value">{{ emotionStats.neutral }}</div>
                    <div class="stat-label">平静天数</div>
                  </div>
                  <div class="stat-card">
                    <div class="stat-value">{{ emotionStats.negative }}</div>
                    <div class="stat-label">消极天数</div>
                  </div>
                </div>
              </div>
            </dv-border-box-3>
          </div>
        </div>

        <!-- 历史记录 -->
        <div class="history-section">
          <dv-border-box-13>
            <div class="panel-content">
              <div class="title">情绪记录历史</div>
              <div class="history-list">
                <div
                  v-for="record in emotionHistory"
                  :key="record.id"
                  :class="['history-item', `emotion-${record.type}`]"
                >
                  <div class="record-date">{{ formatDate(record.date) }}</div>
                  <div class="record-emoji">{{ getEmoji(record.type) }}</div>
                  <div class="record-description">{{ record.description }}</div>
                  <div class="record-score">评分: {{ record.score }}/10</div>
                </div>
                <div v-if="emotionHistory.length === 0" class="no-data">
                  暂无情绪记录，开始记录您的心情吧！
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
// 导入http（如果全局挂载了this.$http可忽略，这里确保可用性）
// import $http from '@/utils/request'

export default {
  name: 'EmotionRecord',
  data() {
    return {
      emotionDescription: '',
      selectedTag: '',
      emotionTags: [
        { name: 'positive', emoji: '😊', label: '积极' },
        { name: 'neutral', emoji: '😐', label: '平静' },
        { name: 'negative', emoji: '😔', label: '消极' }
      ],
      emotionStats: {
        positive: 0,
        neutral: 0,
        negative: 0
      },
      emotionHistory: [],
      currentCalendarMonth: new Date().getMonth() + 1,
      currentCalendarYear: new Date().getFullYear()
    }
  },
  computed: {
    canSubmit() {
      return this.selectedTag && this.emotionDescription.trim().length > 0
    }
  },
  methods: {
    selectTag(tagName) {
      this.selectedTag = tagName
      console.log('选择的情绪标签:', tagName)
    },

    getSelectedTagLabel() {
      const tag = this.emotionTags.find(t => t.name === this.selectedTag)
      return tag ? tag.label : ''
    },
    
    changeMonth(direction) {
      let newMonth = this.currentCalendarMonth + direction
      let newYear = this.currentCalendarYear
      
      if (newMonth < 1) {
        newMonth = 12
        newYear--
      } else if (newMonth > 12) {
        newMonth = 1
        newYear++
      }
      
      this.currentCalendarMonth = newMonth
      this.currentCalendarYear = newYear
      
      // 重新渲染日历图表
      this.$nextTick(() => {
        this.initCalendarChart()
      })
    },

    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return `${date.getMonth() + 1}月${date.getDate()}日`
    },

    async recordEmotion() {
  console.log('开始记录情绪...')
  console.log('描述:', this.emotionDescription)
  console.log('标签:', this.selectedTag)

  if (!this.emotionDescription.trim()) {
    this.showMessage('请输入情绪描述', 'warning')
    return
  }

  if (!this.selectedTag) {
    this.showMessage('请选择情绪标签', 'warning')
    return
  }

  try {
    console.log('发送请求到后端...')
    
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
      userId = 1; // 默认用户
    }
    
    console.log('用户ID:', userId);
    
    // 发送请求
    const res = await this.$http.post('/api/mental/emotion/record', {
      user_id: userId,
      description: this.emotionDescription,
      emotion_type: this.selectedTag
    })

    console.log('后端响应:', res)

    // 处理响应 - $http 已经返回 response.data
    if (res) {
      // 检查响应码
      if (res.code !== undefined && res.code !== 200) {
        throw new Error(res.message || '记录失败');
      }
      
      // 提取数据
      const resultData = res.data || res;
      
      // 记录成功
      this.showMessage(`情绪记录成功！${this.getSelectedTagLabel()} ${resultData.score || 5}/10`, 'success')

      // 创建新记录对象
      const newRecord = {
        id: Date.now(),
        date: new Date().toISOString().split('T')[0],
        type: resultData.emotion_type || this.selectedTag,
        description: this.emotionDescription,
        score: resultData.score || 5
      }

      // 添加到历史记录开头
      this.emotionHistory.unshift(newRecord)
      
      // 重新计算统计
      this.calculateStatsFromHistory()
      
      // 刷新图表
      this.$nextTick(() => {
        this.initCharts()
      })

      // 清空表单
      this.emotionDescription = ''
      this.selectedTag = ''
    }
  } catch (error) {
    console.error('记录情绪失败:', error)
    
    if (error.response) {
      console.error('响应数据:', error.response.data)
      console.error('响应状态:', error.response.status)
      
      // 根据不同的错误状态给出提示
      if (error.response.status === 400) {
        this.showMessage('请求格式错误，请检查输入', 'error')
      } else if (error.response.status === 500) {
        this.showMessage('服务器内部错误，请稍后重试', 'error')
      } else {
        this.showMessage('记录失败: ' + (error.response.data?.message || '未知错误'), 'error')
      }
    } else {
      // 网络错误或请求未发出
      this.showMessage('网络错误，请检查连接', 'error')
      
      // 网络错误时使用本地模拟
      const mockRecord = {
        id: Date.now(),
        date: new Date().toISOString().split('T')[0],
        type: this.selectedTag,
        description: this.emotionDescription,
        score: this.selectedTag === 'positive' ? Math.floor(Math.random() * 5) + 6 :
               this.selectedTag === 'negative' ? Math.floor(Math.random() * 5) + 1 : 5
      }
      
      // 添加到本地历史
      this.emotionHistory.unshift(mockRecord)
      // 重新计算统计
      this.calculateStatsFromHistory()
      // 刷新图表
      this.$nextTick(() => {
        this.initCharts()
      })
      // 清空表单
      this.emotionDescription = ''
      this.selectedTag = ''
    }
  }
},

showMessage(message, type = 'info') {
  // 使用统一的样式显示消息
  const icon = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  }[type] || 'ℹ️'
  
  alert(`${icon} ${message}`)
},
    showMessage(message, type = 'info') {
      // 使用浏览器原生alert
      alert(`${type === 'success' ? '✅' : type === 'error' ? '❌' : '⚠️'} ${message}`)
    },

    getEmoji(type) {
      const tag = this.emotionTags.find(t => t.name === type)
      return tag ? tag.emoji : '😐'
    },

    async loadEmotionHistory() {
  try {
    console.log('加载情绪历史记录（无登录状态）...');
    
    // 移除用户ID相关逻辑，直接请求通用接口
    const res = await this.$http.get('/api/mental/emotion/trend');
    console.log('情绪历史完整响应:', res);
    
    // 修改这里：直接使用 res.code，不是 res.data.code
    if (res.code === 200) {
      // 处理数据
      const data = res.data || res;
      const records = data.records || [];
      
      this.emotionHistory = records.map((record, index) => ({
        id: record.id || index + 1,
        date: record.date || new Date().toISOString().split('T')[0],
        type: record.emotion_type || 'neutral',
        description: record.description || '无描述',
        score: record.score || 5
      }));
      
    } else {
      console.warn('响应code不是200，使用模拟数据');
      // 使用模拟数据
      this.emotionHistory = [
        { id: 1, date: '2024-01-10', type: 'positive', description: '今天工作很顺利，心情很好', score: 8 },
        { id: 2, date: '2024-01-09', type: 'neutral', description: '普通的一天，没什么特别', score: 5 },
        { id: 3, date: '2024-01-08', type: 'negative', description: '遇到一些工作压力', score: 3 }
      ];
    }
    
  } catch (error) {
    console.error('加载情绪历史失败，使用模拟数据:', error);
    // 使用模拟数据
    this.emotionHistory = [
      { id: 1, date: '2024-01-10', type: 'positive', description: '今天工作很顺利，心情很好', score: 8 },
      { id: 2, date: '2024-01-09', type: 'neutral', description: '普通的一天，没什么特别', score: 5 },
      { id: 3, date: '2024-01-08', type: 'negative', description: '遇到一些工作压力', score: 3 }
    ];
  }
},

    async loadEmotionStats() {
  try {
    console.log('加载情绪统计数据（无登录状态）...')
    
    // 移除用户ID，请求通用统计接口
    const res = await this.$http.get('/api/mental/emotion/stats');
    console.log('情绪统计响应:', res)  // 注意：res已经是response.data了

    // 修改这里：直接使用 res.code，不是 res.data.code
    if (res.code === 200) {
      this.emotionStats = res.data
      console.log('情绪统计数据:', this.emotionStats)
    } else {
      throw new Error(res.message || '加载统计失败');
    }
  } catch (error) {
    console.error('加载情绪统计失败，从历史记录计算:', error);
    // 从历史记录计算统计数据
    this.calculateStatsFromHistory();
  }
},

    calculateStatsFromHistory() {
      const stats = { positive: 0, neutral: 0, negative: 0 }
      this.emotionHistory.forEach(record => {
        if (stats[record.type] !== undefined) {
          stats[record.type]++
        }
      })
      this.emotionStats = stats
      console.log('计算出的统计数据:', this.emotionStats)
    },

    initCharts() {
      console.log('初始化图表...')
      this.initTrendChart()
      this.initCalendarChart()
    },

    initTrendChart() {
      const chartDom = this.$refs.trendChart
      if (!chartDom) {
        console.log('趋势图表容器未找到')
        return
      }

      console.log('初始化趋势图表...')
      const myChart = this.$echarts.init(chartDom)

      // 使用真实数据
      const dates = this.emotionHistory.map(record => this.formatDate(record.date)).reverse()
      const scores = this.emotionHistory.map(record => record.score).reverse()

      console.log('趋势图数据 - 日期:', dates)
      console.log('趋势图数据 - 分数:', scores)

      // 如果没有数据，使用默认数据
      const displayDates = dates.length > 0 ? dates : ['1月10日', '1月9日', '1月8日', '1月7日', '1月6日', '1月5日', '1月4日']
      const displayScores = scores.length > 0 ? scores : [7, 5, 8, 3, 6, 9, 7]

      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: function (params) {
            return `日期: ${params[0].name}<br>情绪分: ${params[0].value}`
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: displayDates,
          axisLabel: {
            color: '#fff',
            fontSize: 12
          }
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 10,
          axisLabel: {
            color: '#fff',
            fontSize: 12
          }
        },
        series: [
          {
            name: '情绪分数',
            type: 'line',
            smooth: true,
            data: displayScores,
            itemStyle: {
              color: '#3de7c9'
            },
            lineStyle: {
              width: 3
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [{
                  offset: 0, color: 'rgba(61, 231, 201, 0.3)'
                }, {
                  offset: 1, color: 'rgba(61, 231, 201, 0.1)'
                }]
              }
            }
          }
        ]
      }

      myChart.setOption(option)
      console.log('趋势图表设置完成')
    },
    
    getCurrentMonthRange() {
      const now = new Date()
      const year = now.getFullYear()
      const month = now.getMonth() + 1 // 0-11 -> 1-12
      return `${year}-${month.toString().padStart(2, '0')}`
    },

    initCalendarChart() {
      const chartDom = this.$refs.calendarChart
      if (!chartDom) {
        console.log('日历图表容器未找到')
        return
      }

      console.log('初始化日历图表...')
      const myChart = this.$echarts.init(chartDom)

      // 使用真实数据生成日历热力图
      const heatmapData = this.emotionHistory.map(record => [
        record.date,
        record.score
      ])

      console.log('日历图数据:', heatmapData)

      // 获取当前月份范围
      const currentRange = `${this.currentCalendarYear}-${this.currentCalendarMonth.toString().padStart(2, '0')}`

      const option = {
        tooltip: {
          position: 'top',
          formatter: function (params) {
            return `日期: ${params.data[0]}<br>情绪分: ${params.data[1]}`
          },
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          borderColor: '#3de7c9',
          textStyle: {
            color: '#fff'
          }
        },
        visualMap: {
          min: 0,
          max: 10,
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          top: 0, // 调整到顶部
          padding: [0, 20, 0, 20], // 增加内边距
          inRange: {
            color: ['#ff4444', '#ffaa00', '#00ff88']
          },
          textStyle: {
            color: '#fff',
            fontSize: 10
          },
          itemWidth: 12,
          itemHeight: 200,
        },
        calendar: {
          top: 50, // 增加顶部间距，避开visualMap
          left: 30,
          right: 20,
          bottom: 20,
          cellSize: ['auto', 16],
          range: currentRange,
          itemStyle: {
            borderWidth: 1,
            borderColor: 'rgba(255, 255, 255, 0.2)',
            borderRadius: 2
          },
          yearLabel: {
            show: true,
            color: '#3de7c9',
            fontSize: 14,
            fontWeight: 'bold',
            margin: 5,
            position: 'right', // 将年份标签放在日历右侧
          },
          monthLabel: {
            nameMap: 'cn',
            color: '#fff',
            fontSize: 12,
            margin: 5,
            fontWeight: 'normal'
          },
          dayLabel: {
            color: '#ccc',
            fontSize: 10,
            firstDay: 1,
            nameMap: ['日', '一', '二', '三', '四', '五', '六']
          }
        },
        series: {
          type: 'heatmap',
          coordinateSystem: 'calendar',
          data: heatmapData.length > 0 ? heatmapData : this.getVirtulData(this.currentCalendarYear, this.currentCalendarMonth),
          emphasis: {
            itemStyle: {
              borderWidth: 2,
              borderColor: '#fff',
              shadowBlur: 4,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          itemStyle: {
            borderWidth: 1,
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: 2
          }
        }
      }

      myChart.setOption(option)
      
      // 添加窗口大小变化时的响应式调整
      window.addEventListener('resize', () => {
        myChart.resize()
      })
      
      console.log('日历图表设置完成')
    },

    // 修改虚拟数据生成函数，使其适应动态月份
    getVirtulData(year, month) {
      const date = +this.$echarts.number.parseDate(year + '-' + month)
      const end = +this.$echarts.number.parseDate((+year + (month === 12 ? 1 : 0)) + '-' + (month === 12 ? 1 : month + 1))
      const dayTime = 3600 * 24 * 1000
      const data = []

      for (let time = date; time < end; time += dayTime) {
        data.push([
          this.$echarts.format.formatTime('yyyy-MM-dd', time),
          Math.floor(Math.random() * 10)
        ])
      }

      return data
    }
  },
  async mounted() {
    console.log('EmotionRecord 组件挂载完成')

    // 页面加载时获取情绪历史数据（无登录检查）
    await this.loadEmotionHistory()
    await this.loadEmotionStats()

    this.$nextTick(() => {
      this.initCharts()
    })
  }
}
</script>

<style lang="less" scoped>
.emotion-record-container {
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
  margin-bottom: 15px;

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

.emotion-content {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  flex: 1;
}

.left-panel {
  width: 400px;
  display: flex;
  flex-direction: column;
}

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.panel-content {
  padding: 20px;
}

.emotion-input {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.emotion-textarea {
  width: 95%;
  height: 100px;
  padding: 12px;
  border: 1px solid #3de7c9;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  resize: none;
  font-family: inherit;

  &:focus {
    outline: none;
    border-color: #00ff88;
    box-shadow: 0 0 5px rgba(61, 231, 201, 0.5);
  }

  &::placeholder {
    color: #888;
  }
}

.emotion-tags {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.emotion-tag {
  padding: 10px 20px;
  border: 2px solid #3de7c9;
  border-radius: 20px;
  color: #3de7c9;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  min-width: 80px;
  text-align: center;
  user-select: none;

  &.active {
    background: #3de7c9;
    color: #000;
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(61, 231, 201, 0.3);
  }

  &:hover {
    background: rgba(61, 231, 201, 0.2);
    transform: translateY(-2px);
  }
}

.selected-tag-info {
  text-align: center;
  color: #3de7c9;
  font-weight: bold;
  padding: 8px;
  background: rgba(61, 231, 201, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(61, 231, 201, 0.3);
}

.record-btn {
  padding: 12px 24px;
  background: linear-gradient(45deg, #3de7c9, #568aea);
  border: none;
  border-radius: 8px;
  color: #000;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 16px;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(61, 231, 201, 0.3);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    background: #666;
    color: #999;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
}

.emotion-stats {
  display: flex;
  justify-content: space-around;
  height: 100%;
  margin-top: 20px;
}

.stat-card {
  text-align: center;
  padding: 15px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  min-width: 80px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-value {
  color: #3de7c9;
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  color: #ccc;
  font-size: 12px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.history-section {
  margin-top: 20px;
}

.history-list {
  max-height: 300px;
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
}

.history-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateX(5px);
  }

  &.emotion-positive {
    border-left: 4px solid #00ff88;
  }

  &.emotion-neutral {
    border-left: 4px solid #ffaa00;
  }

  &.emotion-negative {
    border-left: 4px solid #ff4444;
  }
}

.record-date {
  color: #888;
  font-size: 12px;
  width: 80px;
  flex-shrink: 0;
}

.record-emoji {
  font-size: 20px;
  width: 40px;
  text-align: center;
  flex-shrink: 0;
}

.record-description {
  flex: 1;
  color: #fff;
  font-size: 14px;
  margin: 0 15px;
  line-height: 1.4;
}

.record-score {
  color: #3de7c9;
  font-size: 14px;
  font-weight: bold;
  width: 80px;
  text-align: right;
  flex-shrink: 0;
}

.no-data {
  text-align: center;
  color: #888;
  padding: 40px;
  font-style: italic;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin: 10px;
}

.title {
  color: #3f96a5;
  font-size: 18px;
  text-align: center;
  margin-top: 15px;
  margin-bottom: 30px;
  font-weight: bold;
}

// 在<style>标签中添加以下样式
.chart-container {
  position: relative;
  
  .calendar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding: 0 10px;
    
    .calendar-title {
      color: #3de7c9;
      font-size: 14px;
      font-weight: bold;
    }
    
    .calendar-nav {
      display: flex;
      gap: 10px;
      
      .nav-btn {
        background: rgba(61, 231, 201, 0.1);
        border: 1px solid #3de7c9;
        color: #3de7c9;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.3s;
        
        &:hover {
          background: #3de7c9;
          color: #000;
        }
      }
    }
  }
}
</style>