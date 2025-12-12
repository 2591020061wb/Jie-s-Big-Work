<!-- views/mental/GrowthPlan.vue -->
<template>
  <div class="growth-plan-container">
    <dv-border-box-10>
      <div class="naca">
        <div class="page-header">
          <h1>个性化心理成长计划</h1>
          <p>定制专属的心理健康提升方案</p>
        </div>

        <div class="loading-overlay" v-if="loading">
          <div class="loading-content">
            加载中...
          </div>
        </div>

        <div class="growth-content">
          <!-- 活跃计划列表 -->
          <div class="active-plans-section" v-if="!selectedPlanId && !loading">
            <dv-border-box-12>
              <div class="panel-content">
                <div class="title">我的活跃计划</div>
                <div v-if="activePlansLoading" class="loading-text">加载计划中...</div>
                <div v-else>
                  <div class="plans-grid">
                    <div 
                      v-for="plan in activePlans" 
                      :key="plan.id"
                      class="plan-card"
                      @click="openPlanDetail(plan.id)"
                    >
                      <div class="plan-card-header">
                        <div class="plan-card-emoji">{{ getPlanEmoji(plan.plan_type) }}</div>
                        <div class="plan-card-info">
                          <div class="plan-card-name">{{ plan.plan_name }}</div>
                          <div class="plan-card-duration">{{ plan.duration }}天计划</div>
                        </div>
                      </div>
                      <div class="plan-card-progress">
                        <div class="progress-text">
                          {{ getCompletionRate(plan) }}% 完成
                        </div>
                        <div class="progress-bar">
                          <div 
                            class="progress-fill" 
                            :style="{ width: getCompletionRate(plan) + '%' }"
                          ></div>
                        </div>
                      </div>
                      <div class="plan-card-date">
                        开始于: {{ formatDate(plan.start_date) }}
                      </div>
                    </div>
                    
                    <!-- 新增计划卡片 -->
                    <div class="add-plan-card" @click="showPlanTemplates = true">
                      <div class="add-icon">+</div>
                      <div class="add-text">创建新计划</div>
                    </div>
                  </div>
                  
                  <div v-if="activePlans.length === 0" class="no-active-plans">
                    暂无活跃计划，点击"创建新计划"开始您的第一个成长计划！
                  </div>
                </div>
              </div>
            </dv-border-box-12>
          </div>

          <!-- 计划模板选择 -->
          <div class="plan-creation" v-if="showPlanTemplates && !selectedPlanId && !loading">
            <dv-border-box-12>
              <div class="panel-content">
                <div class="title-header">
                  <div class="title">选择成长计划</div>
                  <button @click="showPlanTemplates = false" class="back-btn">← 返回计划列表</button>
                </div>
                <div class="plan-options">
                  <div 
                    v-for="plan in planTemplates" 
                    :key="plan.type"
                    :class="['plan-option', { recommended: plan.recommended }]"
                    @click="createNewPlan(plan)"
                  >
                    <div class="plan-badge" v-if="plan.recommended">推荐</div>
                    <div class="plan-icon">{{ plan.emoji }}</div>
                    <div class="plan-name">{{ plan.name }}</div>
                    <div class="plan-duration">{{ plan.duration }}天计划</div>
                    <div class="plan-desc">{{ plan.description }}</div>
                    <div class="plan-features">
                      <div v-for="feature in plan.features" :key="feature" class="feature">
                        ✓ {{ feature }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </dv-border-box-12>
          </div>

          <!-- 计划详情 -->
          <div class="plan-details" v-if="selectedPlanId && !loading">
            <div class="plan-header">
              <dv-border-box-9>
                <div class="panel-content">
                  <div class="plan-info">
                    <div class="plan-title">
                      <span class="plan-emoji">{{ getPlanEmoji(selectedPlan?.plan_type) }}</span>
                      {{ selectedPlan?.plan_name }}
                    </div>
                    <div class="plan-progress">
                      <div class="progress-text">
                        进度: {{ completedTasks }}/{{ totalTasks }} 任务
                      </div>
                      <div class="progress-bar">
                        <div 
                          class="progress-fill" 
                          :style="{ width: progressPercentage + '%' }"
                        ></div>
                      </div>
                      <div class="progress-percentage">{{ progressPercentage }}%</div>
                    </div>
                    <div class="plan-actions">
                      <button @click="backToPlanList" class="back-btn">← 返回计划列表</button>
                      <button @click="archivePlan" class="archive-btn" v-if="progressPercentage >= 100">
                        ✅ 标记为完成
                      </button>
                    </div>
                  </div>
                </div>
              </dv-border-box-9>
            </div>

            <div class="plan-content">
              <!-- 左侧任务列表 -->
              <div class="tasks-panel">
                <dv-border-box-8>
                  <div class="panel-content">
                    <div class="title">每日任务</div>
                    <div class="tasks-list">
                      <div 
                        v-for="task in currentTasks" 
                        :key="task.id"
                        :class="['task-item', { completed: task.completed }]"
                        @click="toggleTask(task)"
                      >
                        <div class="task-checkbox">
                          <div v-if="task.completed" class="checkmark">✓</div>
                        </div>
                        <div class="task-content">
                          <div class="task-day">第{{ task.day }}天</div>
                          <div class="task-text">{{ task.content }}</div>
                          <div class="task-type">{{ task.type }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </dv-border-box-8>
              </div>

              <!-- 右侧统计和激励 -->
              <div class="stats-panel">
                <dv-border-box-3>
                  <div class="panel-content">
                    <div class="title">成就统计</div>
                    <div class="achievement-stats">
                      <div class="stat-item">
                        <div class="stat-number">{{ streakDays }}</div>
                        <div class="stat-label">连续打卡</div>
                      </div>
                      <div class="stat-item">
                        <div class="stat-number">{{ completedTasks }}</div>
                        <div class="stat-label">完成任务</div>
                      </div>
                      <div class="stat-item">
                        <div class="stat-number">{{ milestoneCount }}</div>
                        <div class="stat-label">达成里程碑</div>
                      </div>
                    </div>
                  </div>
                </dv-border-box-3>

                <dv-border-box-13 style="margin-top: 20px">
                  <div class="panel-content">
                    <div class="title">今日激励</div>
                    <div class="motivation-message">
                      {{ motivationMessage }}
                    </div>
                    <div class="milestone-list">
                      <div 
                        v-for="milestone in milestones" 
                        :key="milestone.day"
                        :class="['milestone-item', { achieved: milestone.achieved }]"
                      >
                        <div class="milestone-day">第{{ milestone.day }}天</div>
                        <div class="milestone-reward">{{ milestone.reward }}</div>
                      </div>
                    </div>
                  </div>
                </dv-border-box-13>
              </div>
            </div>
          </div>
        </div>

        <!-- 历史计划 -->
        <div class="history-section" v-if="!selectedPlanId && !loading && !showPlanTemplates">
          <dv-border-box-13>
            <div class="panel-content">
              <div class="title">历史计划</div>
              <div v-if="historyPlansLoading" class="loading-text">加载历史记录中...</div>
              <div v-else>
                <div class="history-plans">
                  <div 
                    v-for="plan in historyPlans" 
                    :key="plan.id"
                    class="history-plan"
                  >
                    <div class="plan-summary">
                      <div class="plan-name">{{ plan.plan_name }}</div>
                      <div class="plan-date">{{ formatDate(plan.start_date) }} 至 {{ formatDate(plan.end_date) }}</div>
                      <div class="plan-completion">完成度: {{ plan.completion_rate || 0 }}%</div>
                    </div>
                    <div class="plan-status" :class="plan.status">
                      {{ getStatusText(plan.status) }}
                    </div>
                  </div>
                </div>
                <div v-if="historyPlans.length === 0" class="no-history">
                  暂无历史计划
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
  export default {
    name: 'GrowthPlan',
    data() {
      return {
        planTemplates: [
          {
            type: '21_day_stress',
            name: '21天压力管理',
            emoji: '🌊',
            duration: 21,
            description: '学习有效管理压力，建立健康应对机制',
            recommended: true,
            features: [
              '压力识别训练',
              '放松技巧学习',
              '积极思维培养',
              '健康习惯建立'
            ]
          },
          {
            type: '21_day_mindfulness',
            name: '21天正念练习',
            emoji: '🧘',
            duration: 21,
            description: '培养正念意识，提升情绪调节能力',
            recommended: false,
            features: [
              '正念冥想练习',
              '情绪觉察训练',
              '专注力提升',
              '自我接纳培养'
            ]
          },
          {
            type: '90_day_wellness',
            name: '90天全面健康',
            emoji: '🌟',
            duration: 90,
            description: '全面提升心理健康的综合计划',
            recommended: false,
            features: [
              '情绪管理',
              '压力应对',
              '人际关系',
              '自我成长'
            ]
          }
        ],
        // 当前选中的计划ID
        selectedPlanId: null,
        // 当前选中的计划详情
        selectedPlan: null,
        // 当前计划的任务列表
        currentTasks: [],
        // 活跃计划列表
        activePlans: [],
        streakDays: 0,
        milestoneCount: 0,
        motivationMessage: '欢迎开始成长计划！每一步都是进步的开始。',
        milestones: [
          { day: 7, reward: '初级成就徽章', achieved: false },
          { day: 14, reward: '坚持之星徽章', achieved: false },
          { day: 21, reward: '计划完成证书', achieved: false }
        ],
        historyPlans: [],
        loading: false,
        activePlansLoading: false,
        historyPlansLoading: false,
        showPlanTemplates: false
      }
    },
    computed: {
      completedTasks() {
        return this.currentTasks.filter(task => task.completed).length
      },
      totalTasks() {
        return this.currentTasks.length
      },
      progressPercentage() {
        return this.totalTasks > 0 ? Math.round((this.completedTasks / this.totalTasks) * 100) : 0
      }
    },
    methods: {
      // 获取计划类型对应的emoji
      getPlanEmoji(planType) {
        const template = this.planTemplates.find(t => t.type === planType)
        return template ? template.emoji : '📝'
      },
      
      // 获取计划完成率
      getCompletionRate(plan) {
        if (plan.total_tasks && plan.total_tasks > 0) {
          return Math.round((plan.completed_tasks || 0) / plan.total_tasks * 100)
        }
        return 0
      },
      
      // 打开计划详情
      async openPlanDetail(planId) {
        this.selectedPlanId = planId
        await this.loadPlanDetail(planId)
      },
      
      // 创建新计划
      async createNewPlan(planTemplate) {
        try {
          this.loading = true
          
          // 获取当前用户ID
          let userId = this.$store.getters.currentUser?.user_id
          if (!userId) {
            userId = 1
          }
          
          console.log('开始创建计划:', planTemplate.type, '用户ID:', userId)
          
          // 调用后端创建计划接口
          const res = await this.$http.post('/api/mental/growth/plan/create', {
            user_id: userId,
            plan_type: planTemplate.type
          })
          
          console.log('创建计划完整响应:', res)  // $http 返回的是 response.data
          
          // 注意：这里直接使用 res.code，不是 res.data.code
          if (res.code === 200) {
            // 创建成功后，打开新创建的计划
            // 注意：这里直接使用 res.data，不是 res.data.data
            this.selectedPlanId = res.data.plan_id || res.data.id
            await this.loadPlanDetail(this.selectedPlanId)
            this.showPlanTemplates = false
            
            // 重新加载活跃、历史计划列表
            await this.loadActivePlans()
            await this.loadHistoryPlans()
            
            alert('计划创建成功！')
          } else {
            throw new Error(res.message || '创建计划失败')
          }
        } catch (error) {
          console.error('创建计划失败:', error)
          
          if (error.response) {
            console.error('响应数据:', error.response.data)
            console.error('响应状态:', error.response.status)
            
            if (error.response.status === 400) {
              alert('创建计划失败: 请求格式错误')
            } else if (error.response.status === 500) {
              alert('创建计划失败: 服务器内部错误')
            } else {
              alert('创建计划失败: ' + (error.response.data?.message || error.message))
            }
          } else if (error.request) {
            alert('网络错误，请检查后端服务是否启动')
          } else {
            alert('创建计划失败: ' + error.message)
          }
        } finally {
          this.loading = false
        }
      },
      
      // 返回计划列表
      backToPlanList() {
        this.selectedPlanId = null
        this.selectedPlan = null
        this.currentTasks = []
        this.showPlanTemplates = false
        // 重新加载活跃计划列表
        this.loadActivePlans()
      },
      
      // 加载计划详情
      async loadPlanDetail(planId) {
        try {
          this.loading = true
          
          // 调用后端获取计划详情接口
          const res = await this.$http.get(`/api/mental/growth/plan/detail/${planId}`)
          
          console.log('计划详情响应:', res)
          
          // 注意：这里直接使用 res.code，不是 res.data.code
          if (res.code === 200) {
            // 注意：这里直接使用 res.data，不是 res.data.data
            const planData = res.data
            
            this.selectedPlan = {
              id: planData.id,
              plan_type: planData.plan_type,
              plan_name: planData.plan_name,
              duration: planData.duration,
              start_date: planData.start_date
            }
            
            // 设置任务
            this.currentTasks = planData.tasks || []
            
            // 更新统计数据和激励信息
            this.updateStats()
            this.checkMilestones()
            this.updateMotivation()
          } else {
            throw new Error(res.message || '加载计划详情失败')
          }
        } catch (error) {
          console.error('加载计划详情失败:', error)
          alert('加载计划详情失败: ' + (error.response?.data?.message || error.message))
          this.backToPlanList()
        } finally {
          this.loading = false
        }
      },
      
      // 加载活跃计划列表
      async loadActivePlans() {
        try {
          this.activePlansLoading = true
          
          // 获取当前用户ID
          let userId = this.$store.getters.currentUser?.user_id
          if (!userId) {
            userId = 1
          }
          
          // 调用后端获取活跃计划列表接口
          const res = await this.$http.get(`/api/mental/growth/plans/active/${userId}`)
          
          console.log('活跃计划响应:', res)
          
          // 注意：这里直接使用 res.code，不是 res.data.code
          if (res.code === 200) {
            // 注意：这里直接使用 res.data，不是 res.data.data
            this.activePlans = res.data || []
          } else {
            throw new Error(res.message || '加载活跃计划失败')
          }
        } catch (error) {
          console.error('加载活跃计划列表失败:', error)
          this.activePlans = []
        } finally {
          this.activePlansLoading = false
        }
      },
      
      // 归档计划（标记为完成）
      async archivePlan() {
        try {
          const confirmed = confirm('确定要标记这个计划为完成吗？')
          if (!confirmed) return
          
          const res = await this.$http.post(`/api/mental/growth/plan/archive/${this.selectedPlanId}`)
          
          console.log('归档计划响应:', res)
          
          // 注意：这里直接使用 res.code，不是 res.data.code
          if (res.code === 200) {
            alert('计划已标记为完成！')
            this.backToPlanList()
          } else {
            throw new Error(res.message || '归档计划失败')
          }
          await this.loadActivePlans()
          await this.loadHistoryPlans()
        } catch (error) {
          console.error('归档计划失败:', error)
          alert('归档计划失败: ' + (error.response?.data?.message || error.message))
        }
      },
      
      async toggleTask(task) {
        try {
          // 获取当前用户ID
          let userId = this.$store.getters.currentUser?.user_id
          if (!userId) {
            userId = 1
          }
          
          // 调用后端更新任务状态接口
          const res = await this.$http.post('/api/mental/growth/task/update', {
            user_id: userId,
            task_id: task.id,
            completed: !task.completed
          })
          
          console.log('更新任务响应:', res)
          
          // 注意：这里直接使用 res.code，不是 res.data.code
          if (res.code === 200) {
            // 更新本地任务状态
            task.completed = !task.completed
            
            // 更新统计数据
            this.updateStats()
            
            // 检查里程碑
            this.checkMilestones()
            
            // 更新激励信息
            this.updateMotivation()
            
            // 更新活跃计划列表中的完成状态
            this.updateActivePlanProgress()
          } else {
            throw new Error(res.message || '更新任务状态失败')
          }
        } catch (error) {
          console.error('更新任务状态失败:', error)
          
          if (error.response?.data?.message) {
            alert('更新任务状态失败: ' + error.response.data.message)
          } else {
            alert('更新任务状态失败: ' + error.message)
          }
        }
      },
      
      // 更新活跃计划列表中的进度
      updateActivePlanProgress() {
        const planIndex = this.activePlans.findIndex(p => p.id === this.selectedPlanId)
        if (planIndex !== -1) {
          this.activePlans[planIndex].completed_tasks = this.completedTasks
          this.activePlans[planIndex].total_tasks = this.totalTasks
          this.$set(this.activePlans, planIndex, { ...this.activePlans[planIndex] })
        }
      },
      
      updateStats() {
        // 计算连续打卡天数
        let streak = 0
        const today = new Date().toISOString().split('T')[0]
        // 找到最后一个已完成任务的索引
        let lastCompletedIndex = -1
        for (let i = this.currentTasks.length - 1; i >= 0; i--) {
          if (this.currentTasks[i].completed) {
            lastCompletedIndex = i
            break
          }
        }
        
        for (let i = lastCompletedIndex; i >= 0; i--) {
          const task = this.currentTasks[i]
          if (task.completed) {
            streak++
          } else {
            break
          }
        }
        
        this.streakDays = streak
        
        // 计算里程碑达成数
        this.milestoneCount = this.milestones.filter(m => m.achieved).length
      },
      
      checkMilestones() {
        const completedDays = this.currentTasks.filter(task => task.completed).length
        
        this.milestones.forEach(milestone => {
          milestone.achieved = completedDays >= milestone.day
        })
      },
      
      updateMotivation() {
        const completionRate = this.progressPercentage
        const streak = this.streakDays
        
        if (completionRate >= 90) {
          this.motivationMessage = '太棒了！您即将完成整个计划，坚持就是胜利！'
        } else if (completionRate >= 70) {
          this.motivationMessage = '做得很好！您已经完成了大部分任务，继续保持！'
        } else if (completionRate >= 50) {
          this.motivationMessage = '进度不错！您已经完成了一半，继续加油！'
        } else if (completionRate >= 30) {
          this.motivationMessage = '良好的开始！每天进步一点点，坚持下去！'
        } else if (streak >= 3) {
          this.motivationMessage = `您已经连续打卡${streak}天了，继续保持这个好习惯！`
        } else {
          this.motivationMessage = '欢迎开始成长计划！每一步都是进步的开始。'
        }
      },
      
      getStatusText(status) {
        const statusMap = {
          'completed': '已完成',
          'active': '进行中',
          'paused': '已暂停'
        }
        return statusMap[status] || status
      },
      
      formatDate(dateString) {
        if (!dateString) return ''
        const date = new Date(dateString)
        return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
      },
      
      // 加载用户的历史计划
      async loadHistoryPlans() {
        try {
          this.historyPlansLoading = true
          
          // 获取当前用户ID
          let userId = this.$store.getters.currentUser?.user_id
          if (!userId) {
            userId = 1
          }
          
          const res = await this.$http.get(`/api/mental/growth/plan/history/${userId}`)
          
          console.log('历史计划响应:', res)
          
          // 注意：这里直接使用 res.code，不是 res.data.code
          if (res.code === 200) {
            // 注意：这里直接使用 res.data，不是 res.data.data
            this.historyPlans = res.data || []
          } else {
            throw new Error(res.message || '加载历史计划失败')
          }
        } catch (error) {
          console.error('加载历史计划失败:', error)
          this.historyPlans = []
        } finally {
          this.historyPlansLoading = false
        }
      },
  
      // 辅助方法：处理响应（可选，可以使代码更清晰）
      handleResponse(res, successCallback) {
        if (res.code === 200) {
          if (successCallback) {
            successCallback(res.data)
          }
          return true
        } else {
          throw new Error(res.message || '请求失败')
        }
      },
  
      // 使用辅助方法的示例（可选）
      async createNewPlanWithHelper(planTemplate) {
        try {
          this.loading = true
          
          let userId = this.$store.getters.currentUser?.user_id
          if (!userId) userId = 1
          
          const res = await this.$http.post('/api/mental/growth/plan/create', {
            user_id: userId,
            plan_type: planTemplate.type
          })
          
          this.handleResponse(res, (data) => {
            this.selectedPlanId = data.plan_id || data.id
            this.loadPlanDetail(this.selectedPlanId)
            this.showPlanTemplates = false
            this.loadActivePlans()
            this.loadHistoryPlans()
            alert('计划创建成功！')
          })
        } catch (error) {
          console.error('创建计划失败:', error)
          alert('创建计划失败: ' + error.message)
        } finally {
          this.loading = false
        }
      }
    },
    async mounted() {
      console.log('GrowthPlan 组件挂载完成')
      
      // 页面加载时获取活跃计划列表和历史计划
      try {
        await this.loadActivePlans()
        await this.loadHistoryPlans()
      } catch (error) {
        console.log('页面加载失败，使用模拟数据:', error)
        
        // 如果网络请求失败，使用模拟数据
        this.activePlans = [
          {
            id: 1,
            plan_type: '21_day_stress',
            plan_name: '21天压力管理',
            duration: 21,
            start_date: '2024-01-10',
            total_tasks: 21,
            completed_tasks: 7,
            status: 'active'
          }
        ]
        
        this.historyPlans = [
          {
            id: 2,
            plan_type: '21_day_mindfulness',
            plan_name: '21天正念练习',
            duration: 21,
            start_date: '2023-12-01',
            end_date: '2023-12-21',
            status: 'completed',
            completion_rate: 95
          }
        ]
      }
      
      console.log('初始化完成，活跃计划数:', this.activePlans.length)
      console.log('历史计划数:', this.historyPlans.length)
    }
  }
  </script>

<style lang="less" scoped>
/* 保持原有的样式不变，只添加新的样式 */

.growth-plan-container {
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

.growth-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.plan-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.plan-option {
  background: rgba(86, 138, 234, 0.3);
  border-radius: 12px;
  padding: 25px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  
  &:hover {
    background: rgba(86, 138, 234, 0.5);
    transform: translateY(-5px);
  }
  
  &.recommended {
    border: 2px solid #3de7c9;
  }
}

.plan-badge {
  position: absolute;
  top: -10px;
  right: 20px;
  background: #3de7c9;
  color: #000;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.plan-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.plan-name {
  color: #fff;
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 8px;
}

.plan-duration {
  color: #3de7c9;
  font-size: 14px;
  margin-bottom: 12px;
}

.plan-desc {
  color: #ccc;
  font-size: 14px;
  margin-bottom: 15px;
  line-height: 1.4;
}

.plan-features {
  text-align: left;
}

.feature {
  color: #fff;
  font-size: 12px;
  margin-bottom: 6px;
}

.plan-header {
  margin-bottom: 20px;
}

.plan-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

.plan-title {
  color: #3de7c9;
  font-size: 24px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 10px;
}

.plan-emoji {
  font-size: 32px;
}

.plan-progress {
  display: flex;
  align-items: center;
  gap: 15px;
  flex: 1;
  justify-content: center;
}

.progress-text {
  color: #fff;
  font-size: 14px;
}

.progress-bar {
  width: 200px;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(45deg, #3de7c9, #568aea);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-percentage {
  color: #3de7c9;
  font-weight: bold;
  min-width: 40px;
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

.plan-content {
  display: flex;
  gap: 20px;
  flex: 1;
}

.tasks-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.stats-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
}

.tasks-list {
  max-height: 500px;
  overflow-y: auto;
  flex: 1;
}

.task-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  &.completed {
    opacity: 0.7;
    
    .task-text {
      text-decoration: line-through;
    }
  }
}

.task-checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid #3de7c9;
  border-radius: 4px;
  margin-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .checkmark {
    color: #3de7c9;
    font-weight: bold;
  }
}

.task-content {
  flex: 1;
}

.task-day {
  color: #3de7c9;
  font-size: 12px;
  font-weight: bold;
  margin-bottom: 4px;
}

.task-text {
  color: #fff;
  font-size: 14px;
  margin-bottom: 4px;
}

.task-type {
  color: #888;
  font-size: 11px;
}

.achievement-stats {
  display: flex;
  justify-content: space-around;
  margin-top: 15px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  color: #3de7c9;
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  color: #ccc;
  font-size: 12px;
}

.motivation-message {
  color: #fff;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 15px;
  padding: 12px;
  background: rgba(61, 231, 201, 0.1);
  border-radius: 8px;
  text-align: center;
}

.milestone-list {
  margin-top: 15px;
}

.milestone-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  &:last-child {
    border-bottom: none;
  }
  
  &.achieved {
    .milestone-day,
    .milestone-reward {
      color: #3de7c9;
    }
  }
}

.milestone-day {
  color: #ccc;
  font-size: 12px;
}

.milestone-reward {
  color: #ccc;
  font-size: 12px;
  font-weight: bold;
}

.history-section {
  margin-top: 30px;
}

.history-plans {
  max-height: 300px;
  overflow-y: auto;
  
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

.history-plan {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.plan-summary {
  flex: 1;
}

.plan-name {
  color: #fff;
  font-weight: bold;
  margin-bottom: 4px;
}

.plan-date {
  color: #888;
  font-size: 12px;
  margin-bottom: 4px;
}

.plan-completion {
  color: #3de7c9;
  font-size: 12px;
}

.plan-status {
  padding: 6px 12px;
  border-radius: 15px;
  font-size: 12px;
  font-weight: bold;
  
  &.completed {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }
  
  &.active {
    background: rgba(255, 170, 0, 0.2);
    color: #ffaa00;
  }
  
  &.paused {
    background: rgba(255, 68, 68, 0.2);
    color: #ff4444;
  }
}

.title {
  color: #3f96a5;
  font-size: 18px;
  text-align: center;
  margin-bottom: 15px;
  font-weight: bold;
}

.panel-content {
  padding: 20px;
}

/* 新增样式 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  color: #3de7c9;
  font-size: 20px;
  padding: 30px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 10px;
  border: 2px solid #3de7c9;
}

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

/* 活跃计划部分样式 */
.active-plans-section {
  margin-bottom: 30px;
}

.plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.plan-card {
  background: rgba(86, 138, 234, 0.2);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
  
  &:hover {
    background: rgba(86, 138, 234, 0.3);
    transform: translateY(-5px);
    border-color: #3de7c9;
  }
}

.plan-card-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.plan-card-emoji {
  font-size: 36px;
  margin-right: 15px;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.plan-card-info {
  flex: 1;
}

.plan-card-name {
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 5px;
}

.plan-card-duration {
  color: #3de7c9;
  font-size: 12px;
}

.plan-card-progress {
  margin-bottom: 15px;
}

.plan-card-date {
  color: #888;
  font-size: 12px;
  text-align: center;
}

.add-plan-card {
  background: rgba(255, 255, 255, 0.05);
  border: 2px dashed #3de7c9;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  min-height: 180px;
  
  &:hover {
    background: rgba(61, 231, 201, 0.1);
    border-color: #568aea;
  }
}

.add-icon {
  font-size: 40px;
  color: #3de7c9;
  margin-bottom: 10px;
}

.add-text {
  color: #3de7c9;
  font-size: 14px;
  font-weight: bold;
}

.no-active-plans {
  text-align: center;
  color: #888;
  padding: 40px 20px;
  font-style: italic;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin-top: 10px;
  border: 1px dashed #3de7c9;
}

/* 计划模板选择页面的标题布局 */
.title-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  .title {
    margin-bottom: 0;
    flex: 1;
  }
}

/* 计划详情页的操作按钮组 */
.plan-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.archive-btn {
  background: rgba(0, 255, 136, 0.2);
  border: 1px solid #00ff88;
  border-radius: 8px;
  color: #00ff88;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 12px;
  
  &:hover {
    background: rgba(0, 255, 136, 0.3);
  }
}

/* 计划卡片的进度条样式 */
.plan-card-progress {
  .progress-text {
    color: #fff;
    font-size: 12px;
    margin-bottom: 6px;
    text-align: center;
  }
  
  .progress-bar {
    width: 100%;
    height: 6px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(45deg, #3de7c9, #568aea);
    border-radius: 3px;
    transition: width 0.3s ease;
  }
}

/* 响应式调整 */
@media (max-width: 768px) {
  .plans-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 15px;
  }
  
  .plan-card {
    padding: 15px;
  }
  
  .plan-card-emoji {
    font-size: 28px;
    width: 40px;
    height: 40px;
    margin-right: 10px;
  }
  
  .plan-card-name {
    font-size: 14px;
  }
  
  .plan-actions {
    flex-wrap: wrap;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .plans-grid {
    grid-template-columns: 1fr;
  }
}

</style>