<!-- views/MentalHealth.vue -->
<template>
  <div class="mental-health-container">
    <dv-border-box-10>
      <div class="naca">
        <!-- 主要内容 -->
        <div class="mental-content">
          <!-- 左侧统计 -->
          <div class="left-panel">
            <dv-border-box-12>
              <div style="padding: 15px">
                <div class="title">心理健康概览</div>
                <div class="stats-grid">
                  <div class="stat-item">
                    <dv-digital-flop :config="userCountConfig" style="height: 60px" />
                    <div class="stat-label">总用户数</div>
                  </div>
                  <div class="stat-item">
                    <dv-digital-flop :config="recordCountConfig" style="height: 60px" />
                    <div class="stat-label">情绪记录</div>
                  </div>
                  <div class="stat-item">
                    <dv-digital-flop :config="avgScoreConfig" style="height: 60px" />
                    <div class="stat-label">平均情绪分</div>
                  </div>
                  <div class="stat-item">
                    <dv-digital-flop :config="riskCountConfig" style="height: 60px" />
                    <div class="stat-label">高危用户</div>
                  </div>
                </div>
              </div>
            </dv-border-box-12>

            <dv-border-box-8 style="margin-top: 20px">
              <div style="padding: 15px">
                <div class="title">情绪分布</div>
                <div v-if="loadingEmotion" class="loading-text">加载中...</div>
                <div v-else ref="emotionChart" style="width: 100%; height: 200px"></div>
              </div>
            </dv-border-box-8>
          </div>

          <!-- 中间导航 -->
          <div class="center-panel">
            <div class="nav-grid">
              <div class="nav-card" @click="navigateTo('/mental/emotion')">
                <div class="nav-icon">😊</div>
                <div class="nav-title">情绪记录</div>
                <div class="nav-desc">记录每日情绪变化</div>
              </div>
              <div class="nav-card" @click="navigateTo('/mental/assessment')">
                <div class="nav-icon">📊</div>
                <div class="nav-title">心理测评</div>
                <div class="nav-desc">专业心理评估</div>
              </div>
              <div class="nav-card" @click="navigateTo('/mental/ai')">
                <div class="nav-icon">🤖</div>
                <div class="nav-title">AI陪伴</div>
                <div class="nav-desc">智能心理支持</div>
              </div>
              <div class="nav-card" @click="navigateTo('/mental/growth')">
                <div class="nav-icon">📈</div>
                <div class="nav-title">成长计划</div>
                <div class="nav-desc">个性化心理成长</div>
              </div>
            </div>

            <dv-border-box-13 style="margin-top: 20px">
              <div style="padding: 15px">
                <div class="title">风险等级分布</div>
                <div v-if="loadingRisk" class="loading-text">加载中...</div>
                <div v-else ref="riskChart" style="width: 100%; height: 180px"></div>
              </div>
            </dv-border-box-13>
          </div>

          <!-- 右侧信息 -->
          <div class="right-panel">
            <dv-border-box-9>
              <div style="padding: 15px">
                <div class="title">实时动态</div>
                <div class="activity-list">
                  <div v-if="loadingActivities" class="loading-text">加载动态中...</div>
                  <div v-else-if="activities.length === 0" class="empty-text">暂无动态</div>
                  <div v-else v-for="(activity, index) in activities" :key="index" class="activity-item">
                    <div class="activity-time">{{ activity.time }}</div>
                    <div class="activity-content">{{ activity.content }}</div>
                  </div>
                </div>
              </div>
            </dv-border-box-9>

            <dv-border-box-3 style="margin-top: 20px">
              <div style="padding: 15px">
                <div class="title">紧急联系</div>
                <div class="emergency-info">
                  <div class="emergency-item">
                    <div class="emergency-title">心理危机干预热线</div>
                    <div class="emergency-number">400-161-9995</div>
                  </div>
                  <div class="emergency-item">
                    <div class="emergency-title">希望24热线</div>
                    <div class="emergency-number">400-161-9995</div>
                  </div>
                </div>
              </div>
            </dv-border-box-3>
          </div>
        </div>
      </div>
    </dv-border-box-10>
  </div>
</template>

<script>
// 导入统一配置的 $http 实例（路径根据实际项目结构调整）
import $http from '@/utils/request'

export default {
  name: 'MentalHealth',
  data() {
    return {
      loadingDashboard: false,
      loadingEmotion: false,
      loadingRisk: false,
      loadingActivities: false,
      dataPollingInterval: null, // 轮询定时器
      userCountConfig: {
        number: [0],
        content: '{nt}',
        style: {
          fontSize: 24,
          fill: '#3de7c9'
        },
        formatter: null,
        toFixed: 0,
        duration: 1500
      },
      recordCountConfig: {
        number: [0],
        content: '{nt}',
        style: {
          fontSize: 24,
          fill: '#3de7c9'
        },
        formatter: null,
        toFixed: 0,
        duration: 1500
      },
      avgScoreConfig: {
        number: [0],
        content: '{nt}',
        style: {
          fontSize: 24,
          fill: '#3de7c9'
        },
        formatter: null,
        toFixed: 1,
        duration: 1500
      },
      riskCountConfig: {
        number: [0],
        content: '{nt}',
        style: {
          fontSize: 24,
          fill: '#ff4d4f'
        },
        formatter: null,
        toFixed: 0,
        duration: 1500
      },
      activities: [],
      emotionChartData: [],
      riskChartData: [],
      // 缓存图表实例，方便销毁
      emotionChartInstance: null,
      riskChartInstance: null
    }
  },
  methods: {
    initCharts() {
      this.initEmotionChart()
      this.initRiskChart()
    },
    
    initEmotionChart() {
      const chartDom = this.$refs.emotionChart
      if (!chartDom) return
      
      // 销毁旧实例，避免内存泄漏
      if (this.emotionChartInstance) {
        this.emotionChartInstance.dispose()
      }
      
      this.emotionChartInstance = this.$echarts.init(chartDom)
      
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          top: '5%',
          left: 'center',
          textStyle: {
            color: '#fff'
          }
        },
        series: [
          {
            name: '情绪分布',
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 16,
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: this.emotionChartData.length > 0 ? this.emotionChartData : [
              { value: 35, name: '积极', itemStyle: { color: '#00ff88' } },
              { value: 25, name: '中性', itemStyle: { color: '#ffaa00' } },
              { value: 15, name: '消极', itemStyle: { color: '#ff4444' } }
            ]
          }
        ]
      }
      
      this.emotionChartInstance.setOption(option)
      
      // 监听窗口变化，重新调整图表大小
      const resizeHandler = () => {
        this.emotionChartInstance && this.emotionChartInstance.resize()
      }
      window.addEventListener('resize', resizeHandler)
      // 缓存销毁函数
      this.emotionChartInstance.resizeHandler = resizeHandler
    },
    
    initRiskChart() {
      const chartDom = this.$refs.riskChart
      if (!chartDom) return
      
      // 销毁旧实例，避免内存泄漏
      if (this.riskChartInstance) {
        this.riskChartInstance.dispose()
      }
      
      this.riskChartInstance = this.$echarts.init(chartDom)
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          },
          formatter: '{b}: {c}人'
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: this.riskChartData.length > 0 ? this.riskChartData.map(item => item.name) : ['低风险', '中风险', '高风险', '危急'],
          axisLabel: {
            color: '#fff',
            rotate: 0
          }
        },
        yAxis: {
          type: 'value',
          name: '人数',
          axisLabel: {
            color: '#fff'
          },
          splitLine: {
            lineStyle: {
              color: 'rgba(255, 255, 255, 0.1)'
            }
          }
        },
        series: [
          {
            name: '用户数量',
            type: 'bar',
            barWidth: '60%',
            data: this.riskChartData.length > 0 ? this.riskChartData : [
              { value: 120, name: '低风险', itemStyle: { color: '#00ff88' } },
              { value: 60, name: '中风险', itemStyle: { color: '#ffaa00' } },
              { value: 25, name: '高风险', itemStyle: { color: '#ff6b00' } },
              { value: 8, name: '危急', itemStyle: { color: '#ff4444' } }
            ]
          }
        ]
      }
      
      this.riskChartInstance.setOption(option)
      
      // 监听窗口变化，重新调整图表大小
      const resizeHandler = () => {
        this.riskChartInstance && this.riskChartInstance.resize()
      }
      window.addEventListener('resize', resizeHandler)
      // 缓存销毁函数
      this.riskChartInstance.resizeHandler = resizeHandler
    },
    
    async loadDashboardData() {
      this.loadingDashboard = true
      try {
        // 使用统一的 $http 实例请求接口（后端 3000 端口）
        const res = await $http.get('/api/mental/overview')
        const data = res.data || {}
        
        console.log('概览数据:', data)
        
        // 更新数字翻牌器配置
        this.userCountConfig = {
          ...this.userCountConfig,
          number: [Number(data.total_users) || 0]
        }
        
        this.recordCountConfig = {
          ...this.recordCountConfig,
          number: [Number(data.total_records) || 0]
        }
        
        this.avgScoreConfig = {
          ...this.avgScoreConfig,
          number: [Number(data.avg_emotion_score) || 0]
        }
        
        this.riskCountConfig = {
          ...this.riskCountConfig,
          number: [Number(data.high_risk_cases) || 0]
        }
        
      } catch (error) {
        console.error('加载概览数据失败:', error)
        // 统一的错误提示（适配 Axios 拦截器的提示逻辑）
        this.$message({
          type: 'error',
          message: '加载概览数据失败，请稍后重试'
        })
      } finally {
        this.loadingDashboard = false
      }
    },
    
    async loadEmotionDistribution() {
      this.loadingEmotion = true
      try {
        // 请求情绪分布接口
        const res = await $http.get('/api/mental/emotion/stats/global')
        const data = res.data || {}
        
        // 格式化数据用于图表
        this.emotionChartData = [
          { 
            value: data.positive || 0, 
            name: '积极', 
            itemStyle: { color: '#00ff88' } 
          },
          { 
            value: data.neutral || 0, 
            name: '中性', 
            itemStyle: { color: '#ffaa00' } 
          },
          { 
            value: data.negative || 0, 
            name: '消极', 
            itemStyle: { color: '#ff4444' } 
          }
        ]
        
      } catch (error) {
        console.error('加载情绪分布数据失败:', error)
        // 降级使用默认数据
        this.emotionChartData = [
          { value: 35, name: '积极', itemStyle: { color: '#00ff88' } },
          { value: 25, name: '中性', itemStyle: { color: '#ffaa00' } },
          { value: 15, name: '消极', itemStyle: { color: '#ff4444' } }
        ]
      } finally {
        this.loadingEmotion = false
        this.$nextTick(() => {
          this.initEmotionChart()
        })
      }
    },
    
    async fallbackLoadEmotionData() {
      try {
        // 备选方案：从用户列表统计情绪数据
        const usersRes = await $http.get('/api/users')
        const users = usersRes.data.data || []
        
        let positiveCount = 0
        let neutralCount = 0
        let negativeCount = 0
        
        // 限制前10个用户，避免请求过多
        for (const user of users.slice(0, 10)) {
          try {
            const emotionRes = await $http.get(`/mental/emotion/stats/${user.user_id}`)
            const stats = emotionRes.data.data || {}
            
            positiveCount += stats.positive || 0
            neutralCount += stats.neutral || 0
            negativeCount += stats.negative || 0
          } catch (err) {
            console.warn(`获取用户 ${user.user_id} 情绪数据失败:`, err)
          }
        }
        
        this.emotionChartData = [
          { value: positiveCount || 35, name: '积极', itemStyle: { color: '#00ff88' } },
          { value: neutralCount || 25, name: '中性', itemStyle: { color: '#ffaa00' } },
          { value: negativeCount || 15, name: '消极', itemStyle: { color: '#ff4444' } }
        ]
        
      } catch (error) {
        console.error('备选加载情绪数据失败:', error)
        this.emotionChartData = [
          { value: 35, name: '积极', itemStyle: { color: '#00ff88' } },
          { value: 25, name: '中性', itemStyle: { color: '#ffaa00' } },
          { value: 15, name: '消极', itemStyle: { color: '#ff4444' } }
        ]
      }
    },
    
    async loadRiskDistribution() {
      this.loadingRisk = true
      try {
        // 请求风险分布接口
        const res = await $http.get('/api/mental/assessment/risk-distribution')
        const data = res.data || {}
        
        // 格式化数据用于图表
        this.riskChartData = [
          { value: data.low || 0, name: '低风险', itemStyle: { color: '#00ff88' } },
          { value: data.medium || 0, name: '中风险', itemStyle: { color: '#ffaa00' } },
          { value: data.high || 0, name: '高风险', itemStyle: { color: '#ff6b00' } },
          { value: data.critical || 0, name: '危急', itemStyle: { color: '#ff4444' } }
        ]
        
      } catch (error) {
        console.error('加载风险分布数据失败:', error)
        // 降级使用默认数据
        this.riskChartData = [
          { value: 120, name: '低风险', itemStyle: { color: '#00ff88' } },
          { value: 60, name: '中风险', itemStyle: { color: '#ffaa00' } },
          { value: 25, name: '高风险', itemStyle: { color: '#ff6b00' } },
          { value: 8, name: '危急', itemStyle: { color: '#ff4444' } }
        ]
      } finally {
        this.loadingRisk = false
        this.$nextTick(() => {
          this.initRiskChart()
        })
      }
    },
    
    async fallbackLoadRiskData() {
      try {
        // 备选方案：从所有测评记录统计风险等级
        const res = await $http.get('/mental/assessment/all-records')
        const records = res.data.data || []
        
        const riskCounts = {
          low: 0,
          medium: 0,
          high: 0,
          critical: 0
        }
        
        records.forEach(record => {
          const riskLevel = record.risk_level || 'low'
          if (riskCounts.hasOwnProperty(riskLevel)) {
            riskCounts[riskLevel]++
          }
        })
        
        this.riskChartData = [
          { value: riskCounts.low || 120, name: '低风险', itemStyle: { color: '#00ff88' } },
          { value: riskCounts.medium || 60, name: '中风险', itemStyle: { color: '#ffaa00' } },
          { value: riskCounts.high || 25, name: '高风险', itemStyle: { color: '#ff6b00' } },
          { value: riskCounts.critical || 8, name: '危急', itemStyle: { color: '#ff4444' } }
        ]
        
      } catch (error) {
        console.error('备选加载风险数据失败:', error)
        this.riskChartData = [
          { value: 120, name: '低风险', itemStyle: { color: '#00ff88' } },
          { value: 60, name: '中风险', itemStyle: { color: '#ffaa00' } },
          { value: 25, name: '高风险', itemStyle: { color: '#ff6b00' } },
          { value: 8, name: '危急', itemStyle: { color: '#ff4444' } }
        ]
      }
    },
    
    async loadRecentActivities() {
      this.loadingActivities = true
      try {
        // 并行请求情绪和测评的最新记录
        const [emotionRes, assessmentRes] = await Promise.all([
          $http.get('/api/mental/emotion/recent'),
          $http.get('/api/mental/assessment/recent')
        ])
        
        const emotionActivities = emotionRes.data.data || []
        const assessmentActivities = assessmentRes.data.data || []
        
        // 合并并格式化活动数据
        const allActivities = []
        
        // 处理情绪记录
        emotionActivities.forEach(item => {
          if (item.description) {
            allActivities.push({
              time: item.time || '00:00',
              content: `${item.username}记录了情绪: ${item.description.substring(0, 20)}${item.description.length > 20 ? '...' : ''}`,
              timestamp: new Date(item.created_at || item.date || new Date()).getTime()
            })
          }
        })
        
        // 处理测评记录
        assessmentActivities.forEach(item => {
          allActivities.push({
            time: item.time || '00:00',
            content: `${item.username}完成了${item.questionnaire_cn}，得分: ${item.total_score}`,
            timestamp: new Date(item.created_at || item.record_date || new Date()).getTime()
          })
        })
        
        // 按时间排序并取前10条
        const recentActivities = allActivities
          .sort((a, b) => b.timestamp - a.timestamp)
          .slice(0, 10)
          .map(item => ({
            time: item.time,
            content: item.content
          }))
        
        this.activities = recentActivities.length > 0 ? recentActivities : [
          { time: '10:30', content: '用户小明完成了PHQ-9测评' },
          { time: '09:15', content: '用户小红记录了今日情绪' },
          { time: '08:45', content: 'AI陪伴机器人服务了5名用户' },
          { time: '08:00', content: '系统自动生成了3个成长计划' }
        ]
        
      } catch (error) {
        console.error('加载活动数据失败:', error)
        // 降级使用默认数据
        this.activities = [
          { time: '10:30', content: '用户小明完成了PHQ-9测评' },
          { time: '09:15', content: '用户小红记录了今日情绪' },
          { time: '08:45', content: 'AI陪伴机器人服务了5名用户' },
          { time: '08:00', content: '系统自动生成了3个成长计划' }
        ]
      } finally {
        this.loadingActivities = false
      }
    },
    
    navigateTo(path) {
      this.$router.push(path)
    },
    
    // 启动数据轮询
    startDataPolling() {
      // 每5分钟更新一次数据
      this.dataPollingInterval = setInterval(() => {
        this.loadDashboardData()
        this.loadEmotionDistribution()
        this.loadRiskDistribution()
        this.loadRecentActivities()
      }, 5 * 60 * 1000)
    },
    
    // 停止数据轮询
    stopDataPolling() {
      if (this.dataPollingInterval) {
        clearInterval(this.dataPollingInterval)
        this.dataPollingInterval = null
      }
    }
  },
  async mounted() {
    // 并行加载所有初始数据
    await Promise.all([
      this.loadDashboardData(),
      this.loadEmotionDistribution(),
      this.loadRiskDistribution(),
      this.loadRecentActivities()
    ])
    
    // 初始化图表
    this.$nextTick(() => {
      this.initCharts()
    })
    
    // 启动轮询
    this.startDataPolling()
  },
  
  beforeDestroy() {
    // 清理轮询定时器
    this.stopDataPolling()
    
    // 销毁图表实例和事件监听
    if (this.emotionChartInstance) {
      window.removeEventListener('resize', this.emotionChartInstance.resizeHandler)
      this.emotionChartInstance.dispose()
      this.emotionChartInstance = null
    }
    
    if (this.riskChartInstance) {
      window.removeEventListener('resize', this.riskChartInstance.resizeHandler)
      this.riskChartInstance.dispose()
      this.riskChartInstance = null
    }
  }
}
</script>

<style lang="less" scoped>
.mental-health-container {
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

.mental-content {
  display: flex;
  padding: 20px;
  gap: 20px;
  flex: 1;
}

.left-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
}

.center-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.right-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-top: 15px;
}

.stat-item {
  text-align: center;
  padding: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  min-height: 100px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-label {
  color: #fff;
  font-size: 12px;
  margin-top: 5px;
}

.nav-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
}

.nav-card {
  background: rgba(86, 138, 234, 0.3);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(86, 138, 234, 0.5);
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  }
}

.nav-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.nav-title {
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 5px;
}

.nav-desc {
  color: #ccc;
  font-size: 12px;
}

.activity-list {
  max-height: 200px;
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #3de7c9;
    border-radius: 2px;
  }
}

.activity-item {
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  &:last-child {
    border-bottom: none;
  }
}

.activity-time {
  color: #3de7c9;
  font-size: 12px;
  font-weight: bold;
}

.activity-content {
  color: #fff;
  font-size: 14px;
  margin-top: 2px;
  line-height: 1.4;
}

.emergency-info {
  margin-top: 15px;
}

.emergency-item {
  background: rgba(255, 77, 79, 0.2);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  border: 1px solid #ff4d4f;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 77, 79, 0.3);
    transform: translateX(5px);
  }
}

.emergency-title {
  color: #fff;
  font-size: 14px;
  margin-bottom: 5px;
  font-weight: bold;
}

.emergency-number {
  color: #ff4d4f;
  font-size: 18px;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(255, 77, 79, 0.5);
}

.title {
  color: #3f96a5;
  font-size: 18px;
  text-align: center;
  margin-bottom: 15px;
  font-weight: bold;
  text-shadow: 0 0 5px rgba(63, 150, 165, 0.5);
}

.loading-text {
  color: #3de7c9;
  text-align: center;
  padding: 20px;
  font-size: 14px;
}

.empty-text {
  color: #ccc;
  text-align: center;
  padding: 20px;
  font-size: 14px;
}

// 响应式设计
@media (max-width: 1200px) {
  .mental-content {
    flex-direction: column;
  }
  
  .left-panel,
  .center-panel,
  .right-panel {
    width: 100%;
  }
  
  .nav-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .mental-health-container {
    padding: 10px;
  }
  
  .mental-content {
    padding: 10px;
  }
  
  .nav-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>