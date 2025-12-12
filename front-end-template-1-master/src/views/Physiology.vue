<template>
    <div class="physiology-page">
      <transition name="fade" mode="out-in">
        <dv-loading v-if="loading">Loading...</dv-loading>
        <div v-else class="physiology-grid">
          <div class="column column-left">
            <dv-border-box-12 class="panel">
              <div class="panel-header">
                <div>
                  <div class="panel-title">健康数据采集</div>
                  <small>实时监测 + 手动录入</small>
                </div>
                <dv-decoration-5 class="dec-line" :color="['#39affd', '#142c4d']" />
              </div>
              <div class="metric-form">
                <div class="form-row">
                  <label>心率(bpm)
                    <input type="number" v-model.number="metricForm.heart_rate" placeholder="78" />
                  </label>
                  <label>收缩压(mmHg)
                    <input type="number" v-model.number="metricForm.blood_pressure_systolic" placeholder="120" />
                  </label>
                  <label>舒张压(mmHg)
                    <input type="number" v-model.number="metricForm.blood_pressure_diastolic" placeholder="78" />
                  </label>
                </div>
                <div class="form-row">
                  <label>血氧(%)
                    <input type="number" v-model.number="metricForm.blood_oxygen" placeholder="98" />
                  </label>
                  <label>睡眠时长(h)
                    <input type="number" v-model.number="metricForm.sleep_duration" step="0.1" placeholder="7.2" />
                  </label>
                  <label>压力指数(0-100)
                    <input type="number" v-model.number="metricForm.stress_level" placeholder="35" />
                  </label>
                </div>
                <div class="form-row">
                  <label>步数(今日)
                    <input type="number" v-model.number="metricForm.steps" placeholder="5200" />
                  </label>
                  <label>备注
                    <input type="text" v-model="metricForm.notes" placeholder="感觉轻微胸闷" />
                  </label>
                </div>
              </div>
              <div class="form-actions">
                <button :disabled="submitLoading" @click="submitMetricForm">
                  {{ submitLoading ? '提交中...' : '提交监测数据' }}
                </button>
                <button type="button" class="ghost" @click="resetMetricForm">重置</button>
              </div>
              <div class="board-wrapper">
                <dv-scroll-board :config="monitorBoardConfig" style="width:100%;height:180px" />
              </div>
            </dv-border-box-12>
  
            <dv-border-box-12 class="panel">
              <div class="panel-header">
                <div class="panel-title">实时预警 & 病理知识推荐</div>
                <dv-decoration-3 style="width:120px;height:5px" :color="['#39affd', '#142c4d']" />
              </div>
              <div class="alert-list">
                <div
                  v-for="alert in alerts"
                  :key="alert.id"
                  class="alert-item"
                  :class="alert.level"
                >
                  <span class="alert-time">{{ alert.time }}</span>
                  <span class="alert-text">{{ alert.message }}</span>
                </div>
                <div v-if="!alerts.length" class="alert-empty">暂无预警，继续保持健康生活方式</div>
              </div>
              <div class="knowledge-list">
                <div v-for="item in knowledgeList" :key="item.id" class="knowledge-card">
                  <div class="knowledge-title">{{ item.title }}</div>
                  <div class="knowledge-tag">{{ item.tag }}</div>
                  <p>{{ item.desc }}</p>
                  <button type="button" class="ghost" @click="handleTagClick(item.tag)">
                    加入画像标签
                  </button>
                </div>
              </div>
            </dv-border-box-12>
          </div>
  
          <div class="column column-center">
            <dv-border-box-13 class="panel">
              <div class="panel-header">
                <div class="panel-title">客户健康画像</div>
                <small>{{ persona.summary }}</small>
              </div>
              <div class="persona">
                <div class="persona-main">
                  <div class="persona-name">{{ persona.username }}</div>
                  <div class="persona-meta">
                    <span>年龄：{{ persona.age }}</span>
                    <span>性别：{{ persona.gender }}</span>
                    <span>BMI：{{ persona.bmi }}</span>
                    <span>血压：{{ persona.bloodPressure }}</span>
                  </div>
                </div>
                <div class="persona-tags">
                  <span v-for="tag in persona.tags" :key="tag" class="tag">{{ tag }}</span>
                </div>
              </div>
            </dv-border-box-13>
  
            <dv-border-box-13 class="panel">
              <div class="panel-header">
                <div class="panel-title">风险预测中心</div>
                <small>基于历史数据的 6 个月趋势 + 多疾病评估</small>
              </div>
              <div class="trend-area">
                <div ref="trendChart" class="chart-block"></div>
                <div class="disease-risk-list">
                  <div v-for="item in diseaseRisks" :key="item.disease" class="risk-item">
                    <div class="risk-name">{{ item.disease }}</div>
                    <div class="risk-score">{{ (item.risk * 100).toFixed(0) }}%</div>
                    <div class="risk-desc">{{ item.desc }}</div>
                  </div>
                </div>
              </div>
            </dv-border-box-13>
  
            <dv-border-box-8 class="panel">
              <div class="panel-header">
                <div class="panel-title">个性化风险因素分析</div>
              </div>
              <dv-scroll-board :config="riskBoardConfig" style="width:100%;height:220px" />
            </dv-border-box-8>
          </div>
  
          <div class="column column-right">
            <dv-border-box-12 class="panel">
              <div class="panel-header">
                <div class="panel-title">生物钟优化与睡眠质量</div>
                <small>目标睡眠窗口：{{ chronobiology.target }}</small>
              </div>
              <div class="chrono-tip">{{ chronobiology.tip }}</div>
              <div class="schedule-list">
                <div v-for="item in chronobiology.schedule" :key="item.day" class="schedule-item">
                  <span>{{ item.day }}</span>
                  <span>{{ item.sleep }} - {{ item.wake }}</span>
                  <span>遵循度 {{ item.adherence }}%</span>
                  <span>{{ item.note }}</span>
                </div>
              </div>
              <div ref="sleepChart" class="chart-block compact"></div>
            </dv-border-box-12>
  
            <dv-border-box-11 class="panel">
              <div class="panel-header">
                <div class="panel-title">个性化运动处方</div>
                <small>{{ workoutPlan.goal }}</small>
              </div>
              <div class="progress">
                <div class="progress-bar">
                  <div class="progress-value" :style="{ width: workoutProgressWidth }"></div>
                </div>
                <span>{{ workoutPlan.progress }}%</span>
              </div>
              <div class="session-list">
                <div v-for="session in workoutPlan.sessions" :key="session.name" class="session-item">
                  <div class="session-title">{{ session.name }} · {{ session.date }}</div>
                  <div class="session-meta">
                    <span>{{ session.status }}</span>
                    <span>{{ session.metrics }}</span>
                  </div>
                </div>
              </div>
            </dv-border-box-11>
  
            <dv-border-box-11 class="panel">
              <div class="panel-header">
                <div class="panel-title">膳食营养</div>
                <small>每日能量 {{ nutritionPlan.energy }} kcal</small>
              </div>
              <div class="nutrition">
                <div ref="macroChart" class="macro-chart"></div>
                <div class="meal-list">
                  <div v-for="meal in nutritionPlan.meals" :key="meal.name" class="meal-item">
                    <div class="meal-title">{{ meal.name }}</div>
                    <small>{{ meal.desc }}</small>
                    <span>{{ meal.kcal }} kcal</span>
                  </div>
                  <div class="micros">
                    重点微量营养素：{{ nutritionPlan.micronutrients.join(' / ') }}
                  </div>
                </div>
              </div>
            </dv-border-box-11>
  
            <dv-border-box-10 class="panel">
              <div class="panel-header">
                <div class="panel-title">AI 资讯 / 大屏快照</div>
              </div>
              <div class="articles">
                <div v-for="article in aiArticles" :key="article.id" class="article-item">
                  <div>
                    <div class="article-title">{{ article.title }}</div>
                    <small>{{ article.source }} · {{ article.time }}</small>
                  </div>
                </div>
              </div>
              <div class="snapshot">
                <div v-for="item in snapshot" :key="item.label" class="snapshot-card">
                  <div class="snapshot-value">{{ item.value }}</div>
                  <div class="snapshot-label">{{ item.label }}</div>
                </div>
              </div>
            </dv-border-box-10>
          </div>
        </div>
      </transition>
    </div>
  </template>
  
  <script>
  const mockDashboard = {
    overview: {
      username: '王敏',
      gender: '女',
      age: 34,
      bmi: 21.6,
      bloodPressure: '128/84',
      summary: '近期项目冲刺导致睡眠不足，存在久坐与高盐饮食习惯',
      tags: ['久坐', '睡眠不足', '高盐饮食']
    },
    lastMetric: {
      heart_rate: 78,
      blood_pressure_systolic: 126,
      blood_pressure_diastolic: 82,
      blood_oxygen: 98,
      sleep_duration: 6.8,
      stress_level: 42,
      steps: 5600,
      notes: ''
    },
    monitoring: {
      metrics: [
        { field: 'heart_rate', label: '心率', value: 78, target: '55-95', status: '正常' },
        { field: 'blood_pressure_systolic', label: '收缩压', value: 126, target: '90-130', status: '关注' },
        { field: 'blood_pressure_diastolic', label: '舒张压', value: 82, target: '60-85', status: '正常' },
        { field: 'blood_oxygen', label: '血氧', value: 98, target: '95-100', status: '正常' },
        { field: 'sleep_duration', label: '睡眠时长', value: 6.8, target: '7-8', status: '偏低' },
        { field: 'stress_level', label: '压力指数', value: 42, target: '<40', status: '偏高' }
      ],
      alerts: [
        { id: 1, level: 'warning', time: '2025-11-23 23:40', message: '23:00 后仍处于高交感神经激活状态' },
        { id: 2, level: 'danger', time: '2025-11-22 08:10', message: '晨间收缩压超过 135 mmHg' },
        { id: 3, level: 'info', time: '2025-11-21 21:00', message: '建议 21:30 后减少蓝光暴露' }
      ]
    },
    knowledge: [
      { id: 'k1', title: '晨峰血压管理策略', tag: '高血压', desc: '起床后 1 小时内完成拉伸 + 温水，减少交感兴奋。' },
      { id: 'k2', title: '减压呼吸法', tag: '压力应对', desc: '4-7-8 呼吸法可迅速降低交感张力，助眠。' },
      { id: 'k3', title: '钾镁调压食谱', tag: '营养', desc: '多吃深绿色蔬菜、坚果，控制每日钠摄入 < 5g。' }
    ],
    riskTrend: {
      months: ['11月', '12月', '1月', '2月', '3月', '4月'],
      values: [0.48, 0.46, 0.43, 0.39, 0.37, 0.34]
    },
    diseaseRisks: [
      { disease: '高血压', risk: 0.68, desc: '晨间收缩压波动大，夜间交感活跃' },
      { disease: '睡眠呼吸暂停', risk: 0.34, desc: '睡眠效率下降，夜间心率波动' },
      { disease: '代谢综合征', risk: 0.42, desc: '腰臀比偏高，久坐导致胰岛负荷' }
    ],
    riskFactors: [
      { factor: '收缩压波动', weight: 0.28 },
      { factor: '睡眠不足', weight: 0.22 },
      { factor: '久坐缺乏运动', weight: 0.18 },
      { factor: '家族史', weight: 0.17 },
      { factor: '高盐饮食', weight: 0.15 }
    ],
    chronobiology: {
      target: '23:00 - 07:00',
      tip: '21:30 关闭强光屏幕，睡前补充镁，23:00 前完成轻瑜伽拉伸。',
      schedule: [
        { day: '周一', sleep: '22:45', wake: '06:50', adherence: 92, note: '保持良好' },
        { day: '周二', sleep: '23:30', wake: '06:40', adherence: 70, note: '加班需调整' },
        { day: '周三', sleep: '23:10', wake: '06:55', adherence: 85, note: '建议提前 10 分钟' },
        { day: '周四', sleep: '22:40', wake: '06:35', adherence: 95, note: '符合目标' },
        { day: '周五', sleep: '00:10', wake: '07:30', adherence: 60, note: '周末熬夜需控制' }
      ],
      sleepScores: {
        nights: ['周一', '周二', '周三', '周四', '周五'],
        质量: [82, 74, 79, 88, 91],
        效率: [88, 80, 83, 92, 93]
      }
    },
    workouts: {
      goal: '强化心肺 + 降压 + 提升代谢',
      progress: 62,
      sessions: [
        { name: '低冲击有氧', date: '周一', status: '完成', metrics: '心率区 60-70%' },
        { name: '力量循环', date: '周三', status: '完成', metrics: 'RPE 7' },
        { name: 'HIIT 间歇', date: '周五', status: '计划', metrics: '心率区 80%' }
      ]
    },
    nutrition: {
      energy: 1800,
      macros: { carb: 45, protein: 30, fat: 25 },
      micronutrients: ['钾', '镁', '维生素 B6'],
      meals: [
        { name: '早餐', desc: '牛油果全麦吐司 + 水煮蛋 + 低脂牛奶', kcal: 430 },
        { name: '午餐', desc: '清蒸鱼 + 藜麦蔬菜沙拉', kcal: 520 },
        { name: '晚餐', desc: '鸡胸肉 + 西蓝花 + 糙米', kcal: 480 }
      ]
    },
    articles: [
      { id: 'a1', title: 'AI 辅助睡眠分期识别准确率突破 95%', source: 'MedGPT Lab', time: '1 小时前' },
      { id: 'a2', title: '多模态可穿戴数据预测血压新算法', source: 'BioChrono', time: '3 小时前' },
      { id: 'a3', title: '个性化运动处方的闭环调优案例', source: 'SportsAI', time: '今天' }
    ],
    snapshot: [
      { label: '本周运动完成度', value: '86%' },
      { label: '高压异常次数', value: '2 次' },
      { label: '平均睡眠效率', value: '88%' }
    ]
  };
  
  export default {
    name: 'Physiology',
    data() {
      return {
        loading: true,
        submitLoading: false,
        persona: { tags: [] },
        metricForm: {
          heart_rate: null,
          blood_pressure_systolic: null,
          blood_pressure_diastolic: null,
          blood_oxygen: null,
          sleep_duration: null,
          stress_level: null,
          steps: null,
          notes: ''
        },
        liveMetrics: [],
        alerts: [],
        knowledgeList: [],
        diseaseRisks: [],
        riskTrend: { months: [], values: [] },
        riskFactors: [],
        chronobiology: {
          target: '',
          tip: '',
          schedule: [],
          sleepScores: { nights: [], 质量: [], 效率: [] }
        },
        workoutPlan: { progress: 0, sessions: [], goal: '' },
        nutritionPlan: { energy: 0, macros: {}, meals: [], micronutrients: [] },
        aiArticles: [],
        snapshot: [],
        monitorBoardConfig: {
          header: ['指标', '当前值', '目标值', '状态'],
          data: [],
          index: true,
          columnWidth: [80, 100, 100, 80],
          align: ['center', 'center', 'center', 'center'],
          rowNum: 6
        },
        riskBoardConfig: {
          header: ['风险因素', '贡献度'],
          data: [],
          align: ['left', 'center'],
          rowNum: 6
        },
        charts: {}
      };
    },
    computed: {
      workoutProgressWidth() {
        return `${this.workoutPlan.progress || 0}%`;
      }
    },
    watch: {
      metricForm: {
        deep: true,
        handler() {
          this.refreshMonitorBoard();
        }
      },
      liveMetrics() {
        this.refreshMonitorBoard();
      }
    },
    created() {
      this.fetchDashboard();
      window.addEventListener('resize', this.handleResize);
    },
    beforeDestroy() {
      this.disposeCharts();
      window.removeEventListener('resize', this.handleResize);
    },
    methods: {
      async fetchDashboard() {
        try {
          const { data } = await this.$http.get('/physiology/dashboard');
          this.consumePayload(data);
        } catch (error) {
          console.warn('[Physiology] 使用 mock 数据', error);
          this.consumePayload(mockDashboard);
        } finally {
          this.loading = false;
          this.$nextTick(() => this.initCharts());
        }
      },
      consumePayload(payload) {
        this.persona = payload.overview || {};
        this.metricForm = { ...this.metricForm, ...payload.lastMetric };
        this.liveMetrics = payload.monitoring ? payload.monitoring.metrics || [] : [];
        this.alerts = payload.monitoring ? payload.monitoring.alerts || [] : [];
        this.knowledgeList = payload.knowledge || [];
        this.diseaseRisks = payload.diseaseRisks || [];
        this.riskTrend = payload.riskTrend || { months: [], values: [] };
        this.riskFactors = payload.riskFactors || [];
        this.chronobiology = payload.chronobiology || this.chronobiology;
        this.workoutPlan = payload.workouts || this.workoutPlan;
        this.nutritionPlan = payload.nutrition || this.nutritionPlan;
        this.aiArticles = payload.articles || [];
        this.snapshot = payload.snapshot || [];
        this.refreshMonitorBoard();
        this.refreshRiskBoard();
      },
      refreshMonitorBoard() {
        const rows = this.liveMetrics.map((item) => {
          const value = this.metricForm[item.field] !== undefined ? this.metricForm[item.field] : item.value;
          return [item.label, value ?? '-', item.target ?? '-', item.status ?? '-'];
        });
        this.monitorBoardConfig = { ...this.monitorBoardConfig, data: rows };
      },
      refreshRiskBoard() {
        const rows = this.riskFactors.map((item) => [item.factor, `${(item.weight * 100).toFixed(1)}%`]);
        this.riskBoardConfig = { ...this.riskBoardConfig, data: rows };
      },
      async submitMetricForm() {
        this.submitLoading = true;
        try {
          await this.$http.post('/physiology/metrics', this.metricForm);
          this.$message && this.$message.success('已提交到生理监测中心');
        } catch (error) {
          console.warn('[Physiology] 提交失败', error);
          this.$message && this.$message.warning('提交失败：请检查网络或稍后重试');
        } finally {
          this.submitLoading = false;
        }
      },
      resetMetricForm() {
        this.metricForm = { ...mockDashboard.lastMetric };
      },
      handleTagClick(tag) {
        if (!this.persona.tags) {
          this.$set(this.persona, 'tags', []);
        }
        if (!this.persona.tags.includes(tag)) {
          this.persona.tags.push(tag);
        }
      },
      initCharts() {
        this.initTrendChart();
        this.initSleepChart();
        this.initMacroChart();
      },
      initTrendChart() {
        if (!this.riskTrend.months.length) return;
        const option = {
          tooltip: { trigger: 'axis', formatter: '{b}<br/>风险: {c}' },
          grid: { left: '6%', right: '4%', top: '12%', bottom: '15%' },
          xAxis: {
            type: 'category',
            data: this.riskTrend.months,
            boundaryGap: false,
            axisLine: { lineStyle: { color: '#39affd' } },
            axisLabel: { color: '#cfe7ff' }
          },
          yAxis: {
            type: 'value',
            min: 0,
            max: 1,
            axisLabel: { color: '#cfe7ff', formatter: (val) => `${Math.round(val * 100)}%` },
            splitLine: { lineStyle: { color: 'rgba(57,175,253,0.2)' } }
          },
          series: [
            {
              name: '风险评分',
              type: 'line',
              smooth: true,
              symbol: 'circle',
              symbolSize: 8,
              lineStyle: { color: '#0efcff' },
              itemStyle: { color: '#0efcff' },
              areaStyle: { color: 'rgba(14,252,255,0.25)' },
              data: this.riskTrend.values
            }
          ]
        };
        this.setChart('trend', this.$refs.trendChart, option);
      },
      initSleepChart() {
        const sleep = this.chronobiology.sleepScores || { nights: [], 质量: [], 效率: [] };
        if (!sleep.nights.length) return;
        const option = {
          tooltip: { trigger: 'axis' },
          legend: { data: ['睡眠质量', '睡眠效率'], textStyle: { color: '#cfe7ff' } },
          grid: { left: '6%', right: '4%', top: '18%', bottom: '12%' },
          xAxis: {
            type: 'category',
            data: sleep.nights,
            axisLine: { lineStyle: { color: '#39affd' } },
            axisLabel: { color: '#cfe7ff' }
          },
          yAxis: {
            type: 'value',
            max: 100,
            axisLabel: { color: '#cfe7ff' },
            splitLine: { lineStyle: { color: 'rgba(57,175,253,0.2)' } }
          },
          series: [
            {
              name: '睡眠质量',
              type: 'line',
              smooth: true,
              data: sleep.质量,
              itemStyle: { color: '#14c5ff' },
              areaStyle: { color: 'rgba(20,197,255,0.25)' }
            },
            {
              name: '睡眠效率',
              type: 'line',
              smooth: true,
              data: sleep.效率,
              itemStyle: { color: '#f6c94a' }
            }
          ]
        };
        this.setChart('sleep', this.$refs.sleepChart, option);
      },
      initMacroChart() {
        if (!this.nutritionPlan.macros) return;
        const macros = this.nutritionPlan.macros;
        const option = {
          tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
          legend: { orient: 'vertical', right: 0, top: 'center', textStyle: { color: '#cfe7ff' } },
          series: [
            {
              type: 'pie',
              radius: ['45%', '70%'],
              center: ['38%', '50%'],
              data: [
                { value: macros.carb || 0, name: '碳水' },
                { value: macros.protein || 0, name: '蛋白质' },
                { value: macros.fat || 0, name: '脂肪' }
              ],
              label: { color: '#fff', formatter: '{b}\n{d}%' },
              itemStyle: { borderColor: '#020a2b', borderWidth: 2 }
            }
          ]
        };
        this.setChart('macro', this.$refs.macroChart, option);
      },
      setChart(name, dom, option) {
        if (!dom) return;
        if (this.charts[name]) this.charts[name].dispose();
        const chart = this.$echarts.init(dom);
        chart.setOption(option);
        this.charts[name] = chart;
      },
      handleResize() {
        Object.values(this.charts).forEach((chart) => chart && chart.resize());
      },
      disposeCharts() {
        Object.values(this.charts).forEach((chart) => chart && chart.dispose());
        this.charts = {};
      }
    }
  };
  </script>
  
  <style lang="less" scoped>
  .physiology-page {
    width: 100%;
    min-height: calc(100vh - 80px);
    color: #cfe7ff;
  }
  .physiology-grid {
    display: grid;
    grid-template-columns: 1.1fr 1.2fr 1fr;
    gap: 15px;
  }
  .column {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  .panel {
    padding: 15px;
    box-sizing: border-box;
  }
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  .panel-title {
    font-size: 18px;
    font-weight: bold;
  }
  .metric-form {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .form-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }
  .form-row label {
    display: flex;
    flex-direction: column;
    font-size: 13px;
    color: #70c8ff;
  }
  .form-row input {
    margin-top: 6px;
    border-radius: 12px;  /* 将逗号改为分号 */
    border: none;
    padding: 6px 10px;
    background: rgba(255, 255, 255, 0.08);
    color: #fff;
}
  .form-actions {
    margin-top: 10px;
    display: flex;
    gap: 10px;
  }
  .form-actions button {
    flex: 1;
    border: none;
    border-radius: 20px;
    padding: 8px 0;
    cursor: pointer;
    color: #020a2b;
    background: linear-gradient(90deg, #2af7ff, #26b3ff);
  }
  .form-actions .ghost {
    background: transparent;
    color: #39affd;
    border: 1px solid #39affd;
  }
  .board-wrapper {
    margin-top: 15px;
  }
  .alert-list {
    max-height: 120px;
    overflow: auto;
  }
  .alert-item {
    display: flex;
    justify-content: space-between;
    padding: 6px 10px;
    margin-bottom: 6px;
    border-radius: 12px;
    font-size: 13px;
  }
  .alert-item.warning { background: rgba(255, 196, 0, 0.15); }
  .alert-item.danger { background: rgba(255, 0, 76, 0.15); }
  .alert-item.info { background: rgba(58, 173, 255, 0.15); }
  .alert-empty {
    text-align: center;
    padding: 20px 0;
    color: #6686aa;
  }
  .knowledge-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 10px;
    margin-top: 10px;
  }
  .knowledge-card {
    padding: 10px;
    border-radius: 12px;
    background: rgba(16, 45, 80, 0.6);
    font-size: 13px;
  }
  .knowledge-title { font-weight: bold; margin-bottom: 6px; }
  .knowledge-tag { color: #0efcff; margin-bottom: 6px; }
  .knowledge-card button {
    margin-top: 8px;
    border: 1px solid #39affd;
    background: transparent;
    border-radius: 12px;
    padding: 4px 10px;
    color: #39affd;
    cursor: pointer;
  }
  .persona { display: flex; flex-direction: column; gap: 8px; }
  .persona-name { font-size: 24px; font-weight: bold; }
  .persona-meta span { margin-right: 15px; }
  .persona-tags { display: flex; flex-wrap: wrap; gap: 8px; }
  .tag {
    padding: 4px 10px;
    border-radius: 16px;
    border: 1px solid rgba(57, 175, 253, 0.6);
  }
  .trend-area { display: flex; gap: 10px; }
  .chart-block { flex: 1; height: 240px; }
  .chart-block.compact { height: 180px; margin-top: 15px; }
  .disease-risk-list { width: 220px; display: flex; flex-direction: column; gap: 10px; }
  .risk-item { padding: 10px; border-radius: 12px; background: rgba(16, 45, 80, 0.6); }
  .risk-name { font-weight: bold; }
  .risk-score { font-size: 28px; margin: 4px 0; color: #0efcff; }
  .schedule-list { display: flex; flex-direction: column; gap: 6px; }
  .schedule-item {
    display: grid;
    grid-template-columns: repeat(4, auto);
    justify-content: space-between;
    font-size: 13px;
  }
  .progress { display: flex; align-items: center; gap: 10px; }
  .progress-bar { flex: 1; height: 10px; border-radius: 10px; background: rgba(57, 175, 253, 0.2); }
  .progress-value {
    height: 100%;
    border-radius: 10px;
    background: linear-gradient(90deg, #39affd, #0efcff);
  }
  .session-list { margin-top: 10px; display: flex; flex-direction: column; gap: 8px; }
  .session-item { padding: 10px; border-radius: 10px; background: rgba(16, 45, 80, 0.6); }
  .session-meta { display: flex; justify-content: space-between; font-size: 12px; color: #6ea1ff; }
  .nutrition { display: flex; gap: 15px; }
  .macro-chart { width: 200px; height: 200px; }
  .meal-list { flex: 1; display: flex; flex-direction: column; gap: 8px; }
  .meal-item { padding: 8px; border-radius: 10px; background: rgba(16, 45, 80, 0.6); }
  .micros { margin-top: 6px; font-size: 12px; color: #6ea1ff; }
  .articles { max-height: 120px; overflow: auto; display: flex; flex-direction: column; gap: 8px; }
  .article-item { padding: 8px; border-radius: 10px; background: rgba(16, 45, 80, 0.6); }
  .article-title { font-weight: bold; }
  .snapshot { display: flex; gap: 10px; margin-top: 10px; }
  .snapshot-card {
    flex: 1;
    padding: 10px;
    border-radius: 12px;
    background: rgba(16, 45, 80, 0.8);
    text-align: center;
  }
  .snapshot-value { font-size: 24px; color: #0efcff; }
  @media (max-width: 1600px) {
    .physiology-grid { grid-template-columns: 1fr; }
  }
  </style>
  