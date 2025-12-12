<template>
  <div class="metrics-page">
    <transition name="fade" mode="out-in">
      <dv-loading v-if="loading">Loading...</dv-loading>
      <div v-else class="metrics-content">
        <div v-if="error" class="error-banner">{{ error }}</div>

        <dv-border-box-12 class="panel">
          <div class="panel-header">
            <div class="panel-title">筛选条件</div>
            <small>支持日期区间、来源筛选与关键字模糊搜索</small>
          </div>
          <div class="filter-form">
            <label>
              起始日期
              <input type="date" v-model="filters.startDate" />
            </label>
            <label>
              结束日期
              <input type="date" v-model="filters.endDate" />
            </label>
            <label>
              数据来源
              <select v-model="filters.source">
                <option value="all">全部</option>
                <option value="wearable">可穿戴</option>
                <option value="manual">手动录入</option>
                <option value="hospital">医院体检</option>
                <option value="app">手机APP</option>
              </select>
            </label>
            <label>
              关键词
              <input
                type="text"
                v-model.trim="filters.keyword"
                placeholder="例：高压/失眠/血糖"
              />
            </label>
            <div class="filter-actions">
              <button :disabled="listLoading" @click="applyFilter">
                {{ listLoading ? '筛选中...' : '应用筛选' }}
              </button>
              <button
                type="button"
                class="ghost"
                :disabled="listLoading"
                @click="resetFilters"
              >
                重置
              </button>
            </div>
          </div>
        </dv-border-box-12>

        <div class="overview-grid">
          <dv-border-box-11 class="panel persona-panel">
            <div class="panel-header">
              <div class="panel-title">健康画像</div>
              <small>最新概览</small>
            </div>
            <div v-if="overview" class="persona">
              <div class="persona-row">
                <div>
                  <div class="persona-name">
                    {{ overview.username || '未知用户' }}
                  </div>
                  <div class="persona-meta">
                    <span>{{ overview.gender || '未知' }}</span>
                    <span v-if="overview.age">{{ overview.age }} 岁</span>
                    <span v-if="overview.bmi">BMI {{ overview.bmi }}</span>
                  </div>
                </div>
                <div class="persona-bp">
                  <span>血压</span>
                  <strong>{{ overview.bloodPressure || '--/--' }}</strong>
                </div>
              </div>
              <div class="persona-tags">
                <span
                  v-for="tag in overview.tags"
                  :key="tag"
                  class="tag-chip"
                >
                  {{ tag }}
                </span>
                <span v-if="!overview.tags || !overview.tags.length"
                  >暂无标签</span
                >
              </div>
              <p class="persona-summary">
                {{ overview.summary || '暂无健康摘要' }}
              </p>
            </div>
            <div v-else class="panel-empty">暂无健康画像</div>
          </dv-border-box-11>

          <dv-border-box-11 class="panel lastmetric-panel">
            <div class="panel-header">
              <div class="panel-title">最近一次记录</div>
              <small>{{ lastMetricTime }}</small>
            </div>
            <div v-if="lastMetricEntries.length" class="last-metric">
              <div class="metric-grid">
                <div
                  v-for="entry in lastMetricEntries"
                  :key="entry.label"
                  class="metric-chip"
                >
                  <span>{{ entry.label }}</span>
                  <strong>{{ entry.value }}</strong>
                </div>
              </div>
            </div>
            <div v-else class="panel-empty">暂无记录</div>

            <div class="alerts-block">
              <div class="alerts-header">
                <div class="panel-subtitle">最新预警</div>
                <button
                  type="button"
                  class="link-btn"
                  :disabled="dashboardLoading"
                  @click="fetchDashboard"
                >
                  {{ dashboardLoading ? '刷新中...' : '刷新' }}
                </button>
              </div>
              <div v-if="alerts.length" class="alerts-list">
                <div v-for="alert in alerts" :key="alert.id" class="alert-item">
                  <span class="alert-level" :class="alert.level">
                    {{ levelLabel(alert.level) }}
                  </span>
                  <div>
                    <div class="alert-time">{{ alert.time }}</div>
                    <div class="alert-message">{{ alert.message }}</div>
                  </div>
                </div>
              </div>
              <div v-else class="panel-empty small">暂无预警</div>
            </div>
          </dv-border-box-11>

          <dv-border-box-11 class="panel knowledge-panel">
            <div class="panel-header">
              <div class="panel-title">知识推荐</div>
              <small>关联健康状况</small>
            </div>
            <div v-if="knowledge.length" class="knowledge-cards">
              <div
                v-for="item in knowledge"
                :key="item.id"
                class="knowledge-card"
              >
                <span class="knowledge-tag">{{ item.tag }}</span>
                <div class="knowledge-title">{{ item.title }}</div>
                <p class="knowledge-desc">{{ item.desc }}</p>
              </div>
            </div>
            <div v-else class="panel-empty">暂无推荐</div>
          </dv-border-box-11>
        </div>

        <dv-border-box-12 class="panel monitoring-panel">
          <div class="panel-header">
            <div class="panel-title">监测指标状态</div>
            <small>与目标范围对比</small>
          </div>
          <div v-if="monitoringMetrics.length" class="monitoring-grid">
            <div
              v-for="item in monitoringMetrics"
              :key="item.field"
              class="monitoring-card"
              :class="statusClass(item.status)"
            >
              <div class="monitoring-label">{{ item.label }}</div>
              <div class="monitoring-value">
                {{ safeMetric(item.value) }}
              </div>
              <div class="monitoring-target">目标 {{ item.target }}</div>
              <div class="monitoring-status">{{ item.status }}</div>
            </div>
          </div>
          <div v-else class="panel-empty">暂无监测数据</div>
        </dv-border-box-12>

        <div class="stats-grid">
          <dv-border-box-11 class="panel">
            <div class="panel-header">
              <div class="panel-title">关键指标均值</div>
              <small>最近 30 天</small>
            </div>
            <div class="stat-cards">
              <div class="stat-card">
                <span class="label">平均心率</span>
                <strong>{{ stats.avgHeartRate }} bpm</strong>
              </div>
              <div class="stat-card">
                <span class="label">平均血压</span>
                <strong>{{ stats.avgBloodPressure }}</strong>
              </div>
              <div class="stat-card">
                <span class="label">平均血糖</span>
                <strong>{{ stats.avgGlucose }} mmol/L</strong>
              </div>
              <div class="stat-card">
    <span class="label">平均体温</span>
    <strong>{{ stats.avgTemperature }} ℃</strong>
  </div>
              <div class="stat-card">
                <span class="label">高风险天数</span>
                <strong>{{ stats.highRiskCount }} 天</strong>
              </div>
            </div>
          </dv-border-box-11>

          <dv-border-box-13 class="panel board-panel">
            <div class="panel-header">
              <div class="panel-title">监测记录表</div>
              <small>滚动展示全部记录</small>
            </div>
            <div v-if="listLoading" class="panel-loading">记录加载中...</div>
            <dv-scroll-board
              v-else
              :config="tableConfig"
              style="width: 100%; height: 280px"
            />
          </dv-border-box-13>
        </div>

        <dv-border-box-10 class="panel timeline-panel">
          <div class="panel-header">
            <div class="panel-title">时间轴 / 事件摘要</div>
            <small>按时间倒序显示重点记录</small>
          </div>
          <div class="timeline">
            <div
              v-for="record in filteredRecords"
              :key="record.id"
              class="timeline-item"
            >
              <div class="timeline-dot" :class="record.severity"></div>
              <div class="timeline-content">
                <div class="timeline-time">{{ record.date }}</div>
                <div class="timeline-source">
                  {{ sourceLabel(record.source) }}
                </div>
                <div class="timeline-metrics">
                  心率 {{ safeMetric(record.metrics.heart_rate, 'bpm') }} ·
                  血压
                  {{
                    safeMetric(record.metrics.blood_pressure_systolic)
                  }}/{{ safeMetric(record.metrics.blood_pressure_diastolic) }}
                  mmHg · 血糖
                  {{ safeMetric(record.metrics.glucose, 'mmol/L') }} ·
                  血氧
                  {{ safeMetric(record.metrics.blood_oxygen, '%') }} ·
                  体温
                  {{ safeMetric(record.metrics.temperature, '℃') }}
                </div>
                <div class="timeline-tags">
                  <span
                    v-for="tag in record.tags"
                    :key="`${record.id}-${tag}`"
                    class="tag"
                  >
                    {{ tag }}
                  </span>
                </div>
              </div>
            </div>
            <div v-if="!filteredRecords.length" class="timeline-empty">
              暂无符合条件的记录
            </div>
          </div>
        </dv-border-box-10>
      </div>
    </transition>
  </div>
</template>

<script>
import { getMetricsDashboard, getMetricsList } from '@/api/metrics';

export default {
  name: 'PhysiologyMetrics',
  data() {
    return {
      loading: true,
      listLoading: false,
      dashboardLoading: false,
      error: '',
      overview: null,
      lastMetric: {},
      monitoringMetrics: [],
      alerts: [],
      knowledge: [],
      filters: {
        startDate: '',
        endDate: '',
        source: 'all',
        keyword: ''
      },
      stats: {
        avgHeartRate: '--',
        avgBloodPressure: '--/--',
        avgGlucose: '--',
        avgTemperature: '--',
        avgSleep: '--',
        highRiskCount: '--'
      },
      records: [],
      filteredRecords: [],
      tableConfig: {
        header: ['时间', '来源', '心率', '血压', '血糖', '血氧', '睡眠', '压力', '体重', '标签'],
        data: [],
        index: true,
        align: ['center', 'center', 'center', 'center', 'center', 'center', 'center', 'center', 'center', 'left'],
        rowNum: 8
      }
    };
  },
  computed: {
    lastMetricEntries() {
      if (!this.lastMetric || !Object.keys(this.lastMetric).length) {
        return [];
      }
      return [
        {
          label: '心率',
          value: this.safeMetric(this.lastMetric.heart_rate, 'bpm')
        },
        {
          label: '收缩压',
          value: this.safeMetric(this.lastMetric.blood_pressure_systolic, 'mmHg')
        },
        {
          label: '舒张压',
          value: this.safeMetric(this.lastMetric.blood_pressure_diastolic, 'mmHg')
        },
        {
          label: '血氧',
          value: this.safeMetric(this.lastMetric.blood_oxygen, '%')
        },
        {
          label: '呼吸频率',
          value: this.safeMetric(this.lastMetric.resp_rate, '次/分')
        },
        {
          label: '体温',
          value: this.safeMetric(this.lastMetric.temperature, '℃')
        },
        {
          label: '血糖',
          value: this.safeMetric(this.lastMetric.glucose, 'mmol/L')
        },
        {
          label: '睡眠',
          value: this.safeMetric(this.lastMetric.sleep_duration, 'h')
        },
        {
          label: '压力',
          value: this.safeMetric(this.lastMetric.stress_level)
        },
        {
          label: '体重',
          value: this.safeMetric(this.lastMetric.weight_kg, 'kg')
        },
        {
          label: 'BMI',
          value: this.safeMetric(this.lastMetric.bmi)
        }
      ];
    },
    lastMetricTime() {
      return this.lastMetric?.recorded_at || '无记录';
    }
  },
  watch: {
    'filters.keyword'() {
      this.applyKeywordFilter();
    }
  },
  created() {
    this.fetchAllData();
  },
  methods: {
    async fetchAllData() {
      this.loading = true;
      this.error = '';
      try {
        await Promise.all([this.fetchDashboard(), this.fetchRecords()]);
      } finally {
        this.loading = false;
      }
    },
    async fetchDashboard() {
      this.dashboardLoading = true;
      this.error = '';
      try {
        const res = await getMetricsDashboard();
        this.overview = res?.overview || null;
        this.lastMetric = res?.lastMetric || {};
        this.monitoringMetrics = res?.monitoring?.metrics || [];
        this.alerts = res?.monitoring?.alerts || [];
        this.knowledge = res?.knowledge || [];
      } catch (err) {
        this.handleError('获取仪表板数据失败', err);
      } finally {
        this.dashboardLoading = false;
      }
    },
    async fetchRecords() {
      this.listLoading = true;
      this.error = '';
      try {
        const params = {
          start_date: this.filters.startDate || undefined,
          end_date: this.filters.endDate || undefined,
          source: this.filters.source || 'all'
        };
        const res = await getMetricsList(params);
        const stats = res?.stats || {};
        this.stats = {
          avgHeartRate: stats.avgHeartRate ?? '--',
          avgBloodPressure: stats.avgBloodPressure ?? '--/--',
          avgGlucose: stats.avgGlucose ?? '--',
          avgSleep: stats.avgSleep ?? '--',
          highRiskCount: stats.highRiskCount ?? '--'
        };
        this.records = res?.records || [];
        this.applyKeywordFilter();
      } catch (err) {
        this.handleError('获取监测记录失败', err);
      } finally {
        this.listLoading = false;
      }
    },
    applyFilter() {
      this.fetchRecords();
    },
    resetFilters() {
      this.filters = {
        startDate: '',
        endDate: '',
        source: 'all',
        keyword: ''
      };
      this.fetchRecords();
    },
    applyKeywordFilter() {
      if (!this.records || !this.records.length) {
        this.filteredRecords = [];
        this.refreshBoard();
        return;
      }
      const keyword = this.filters.keyword?.trim();
      if (!keyword) {
        this.filteredRecords = [...this.records];
      } else {
        this.filteredRecords = this.records.filter((record) => {
          const tagHit = (record.tags || []).some((tag) =>
            tag.includes(keyword)
          );
          const metricHit = record.metrics
            ? Object.values(record.metrics).some(
                (val) =>
                  val !== null &&
                  val !== undefined &&
                  String(val).includes(keyword)
              )
            : false;
          return tagHit || metricHit;
        });
      }
      this.refreshBoard();
    },
    refreshBoard() {
      const rows = this.filteredRecords.map((item) => [
        item.date || '--',
        this.sourceLabel(item.source),
        this.safeMetric(item.metrics?.heart_rate, 'bpm'),
        `${this.safeMetric(
          item.metrics?.blood_pressure_systolic
        )}/${this.safeMetric(item.metrics?.blood_pressure_diastolic)}`,
        this.safeMetric(item.metrics?.glucose, 'mmol/L'),
        this.safeMetric(item.metrics?.blood_oxygen, '%'),
        this.safeMetric(item.metrics?.sleep_duration, 'h'),
        this.safeMetric(item.metrics?.stress_level),
        this.safeMetric(item.metrics?.weight_kg, 'kg'),
        (item.tags || []).join('、')
      ]);
      this.tableConfig = {
        ...this.tableConfig,
        data: rows
      };
    },
    safeMetric(value, suffix = '') {
      if (value === null || value === undefined || value === '') {
        return '--';
      }
      return suffix ? `${value} ${suffix}` : `${value}`;
    },
    sourceLabel(source) {
      const map = {
        wearable: '可穿戴',
        manual: '手动录入',
        hospital: '医院体检',
        app: '手机APP'
      };
      return map[source] || '其他';
    },
    statusClass(status) {
      switch (status) {
        case '正常':
          return 'ok';
        case '偏高':
          return 'high';
        case '偏低':
          return 'low';
        default:
          return 'unknown';
      }
    },
    levelLabel(level) {
      const map = {
        danger: '危险',
        warning: '预警',
        info: '提醒'
      };
      return map[level] || '提醒';
    },
    handleError(message, err) {
      console.error(message, err);
      this.error = message;
      if (this.$message && typeof this.$message.error === 'function') {
        this.$message.error(message);
      }
    }
  }
};
</script>

<style lang="less" scoped>
.metrics-page {
  width: 100%;
  min-height: calc(100vh - 120px);
  color: #cfe7ff;
}
.metrics-content {
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
.panel-subtitle {
  font-size: 14px;
  color: #89c5ff;
}
.error-banner {
  padding: 10px 14px;
  border-radius: 8px;
  background: rgba(255, 107, 107, 0.12);
  border: 1px solid rgba(255, 107, 107, 0.4);
}
.filter-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}
.filter-form label {
  display: flex;
  flex-direction: column;
  font-size: 13px;
  color: #70c8ff;
}
.filter-form input,
.filter-form select {
  margin-top: 6px;
  border-radius: 12px;
  border: none;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}
.filter-actions {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}
.filter-actions button {
  flex: 1;
  border: none;
  border-radius: 20px;
  padding: 8px 0;
  cursor: pointer;
  background: linear-gradient(90deg, #2af7ff, #26b3ff);
  color: #020a2b;
}
.filter-actions .ghost {
  background: transparent;
  border: 1px solid #39affd;
  color: #39affd;
}
.filter-actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.link-btn {
  background: transparent;
  border: none;
  color: #39affd;
  cursor: pointer;
  font-size: 12px;
}
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 15px;
}
.persona {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.persona-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.persona-name {
  font-size: 20px;
  font-weight: bold;
}
.persona-meta {
  display: flex;
  gap: 8px;
  font-size: 13px;
  color: #8ac4ff;
}
.persona-bp {
  text-align: right;
}
.persona-bp strong {
  display: block;
  font-size: 22px;
  color: #0efcff;
}
.persona-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.tag-chip {
  padding: 2px 10px;
  border-radius: 12px;
  border: 1px solid rgba(57, 175, 253, 0.6);
  font-size: 12px;
}
.persona-summary {
  font-size: 13px;
  line-height: 1.5;
  color: #9ecaff;
}
.lastmetric-panel .metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
}
.metric-chip {
  padding: 10px;
  border-radius: 12px;
  background: rgba(16, 45, 80, 0.55);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.metric-chip span {
  font-size: 13px;
  color: #7bb9ff;
}
.metric-chip strong {
  font-size: 18px;
  color: #0efcff;
}
.alerts-block {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.alert-item {
  display: flex;
  gap: 10px;
  padding: 8px;
  border-radius: 10px;
  background: rgba(6, 19, 41, 0.7);
}
.alert-level {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  text-transform: uppercase;
}
.alert-level.danger {
  background: rgba(255, 79, 129, 0.2);
  color: #ff4f81;
}
.alert-level.warning {
  background: rgba(246, 201, 74, 0.2);
  color: #f6c94a;
}
.alert-level.info {
  background: rgba(38, 179, 255, 0.2);
  color: #26b3ff;
}
.alert-time {
  font-size: 12px;
  color: #86b5ff;
}
.alert-message {
  font-size: 13px;
}
.knowledge-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}
.knowledge-card {
  padding: 12px;
  border-radius: 14px;
  background: rgba(16, 45, 80, 0.55);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.knowledge-tag {
  font-size: 12px;
  color: #39affd;
}
.knowledge-title {
  font-weight: bold;
}
.knowledge-desc {
  font-size: 13px;
  color: #9dc9ff;
  line-height: 1.4;
}
.monitoring-panel .monitoring-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}
.monitoring-card {
  padding: 10px;
  border-radius: 12px;
  background: rgba(6, 23, 50, 0.65);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.monitoring-card.ok {
  border: 1px solid rgba(46, 198, 148, 0.7);
}
.monitoring-card.high {
  border: 1px solid rgba(255, 145, 99, 0.7);
}
.monitoring-card.low {
  border: 1px solid rgba(121, 198, 255, 0.7);
}
.monitoring-card.unknown {
  border: 1px solid rgba(105, 120, 160, 0.5);
}
.monitoring-label {
  font-size: 13px;
  color: #7bb9ff;
}
.monitoring-value {
  font-size: 20px;
  font-weight: bold;
  color: #0efcff;
}
.monitoring-target {
  font-size: 12px;
  color: #8ab8ff;
}
.monitoring-status {
  font-size: 12px;
}
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}
.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 12px;
}
.stat-card {
  padding: 12px;
  border-radius: 14px;
  background: rgba(16, 45, 80, 0.65);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.stat-card .label {
  font-size: 13px;
  color: #6fa6ff;
}
.stat-card strong {
  font-size: 22px;
  color: #0efcff;
}
.board-panel {
  min-height: 340px;
  position: relative;
}
.panel-loading {
  position: absolute;
  inset: 50% auto auto 50%;
  transform: translate(-50%, -50%);
  color: #9dc9ff;
}
.timeline-panel {
  min-height: 320px;
}
.timeline {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.timeline-item {
  display: flex;
  gap: 15px;
  align-items: flex-start;
}
.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 6px;
}
.timeline-dot.info {
  background: #26b3ff;
}
.timeline-dot.warning {
  background: #f6c94a;
}
.timeline-dot.danger {
  background: #ff4f81;
}
.timeline-content {
  flex: 1;
  padding: 10px;
  border-radius: 12px;
  background: rgba(16, 45, 80, 0.55);
}
.timeline-time {
  font-weight: bold;
  margin-bottom: 4px;
}
.timeline-source {
  font-size: 13px;
  color: #6ea1ff;
  margin-bottom: 6px;
}
.timeline-metrics {
  font-size: 13px;
  margin-bottom: 8px;
}
.timeline-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.tag {
  padding: 2px 10px;
  border-radius: 12px;
  border: 1px solid rgba(57, 175, 253, 0.6);
  font-size: 12px;
}
.panel-empty {
  text-align: center;
  color: #7aa8e6;
  padding: 20px 0;
}
.panel-empty.small {
  padding: 8px 0;
}
.timeline-empty {
  text-align: center;
  color: #6ea1ff;
  padding: 30px 0;
}
@media (max-width: 1400px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>