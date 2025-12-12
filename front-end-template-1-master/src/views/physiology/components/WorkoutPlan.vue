<template>
  <dv-border-box-12 class="panel plan-panel">
    <div class="panel-header">
      <div>
        <div class="panel-title">运动干预计划</div>
        <small>{{ planData.goal || '暂无个性化目标' }}</small>
      </div>
      <button class="text-btn" :disabled="loading" @click="refreshAll">
        {{ loading ? '刷新中…' : '刷新' }}
      </button>
    </div>

    <div v-if="loading" class="panel-empty">正在获取最新计划…</div>
    <template v-else>
      <div class="plan-body">
        <div class="plan-progress">
          <span>完成度 {{ planData.progress || 0 }}%</span>
          <div class="progress-bar">
            <div class="progress-value" :style="{ width: progressWidth }"></div>
          </div>
        </div>

        <div class="phase-list">
          <div v-for="phase in planData.phases" :key="phase.name" class="phase-card">
            <div class="phase-name">{{ phase.name }}</div>
            <div class="phase-desc">{{ phase.desc }}</div>
            <div class="phase-meta">持续：{{ phase.duration }} · 目标：{{ phase.target }}</div>
          </div>
          <div v-if="!planData.phases.length" class="phase-card ghost">暂无阶段信息</div>
        </div>

        <div class="session-list">
          <div
            v-for="(session, index) in planData.sessions"
            :key="`${session.name}-${index}`"
            class="session-item"
          >
            <div class="session-title">{{ session.name }} · {{ session.date }}</div>
            <div class="session-meta">
              <span>{{ session.status }}</span>
              <span v-if="session.metrics">{{ session.metrics }}</span>
            </div>
          </div>
          <div v-if="!planData.sessions.length" class="session-item ghost">暂无即将开始或最近完成的训练</div>
        </div>
      </div>

      <div class="session-section">
        <div class="session-section-header">
          <div class="panel-title">训练执行记录</div>
          <div class="filter-tabs">
            <button
              v-for="tab in statusTabs"
              :key="tab.value"
              class="tab-btn"
              :class="{ active: sessionStatus === tab.value }"
              @click="switchStatus(tab.value)"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>

        <div v-if="sessionsLoading" class="panel-empty">加载训练记录…</div>
        <div v-else-if="!sessionList.length" class="panel-empty">暂无训练记录</div>
        <div v-else class="session-table">
          <div class="session-row session-header">
            <span>训练内容</span>
            <span>计划/实际</span>
            <span>状态</span>
            <span>关键指标</span>
            <span class="actions-col">操作</span>
          </div>
          <div v-for="session in sessionList" :key="session.id" class="session-row">
            <div class="col col-activity">
              <div class="name">{{ session.activity }}</div>
              <div class="meta">{{ session.day }} · {{ session.intensityText }}</div>
            </div>
            <div class="col col-date">
              <span>计划：{{ session.scheduledDate }}</span>
              <span v-if="session.actualDate">完成：{{ session.actualDate }}</span>
            </div>
            <div class="col col-status" :class="statusClass(session.status)">
              {{ session.status }}
              <span v-if="session.adherence !== null" class="adherence">遵从度 {{ session.adherence }}%</span>
            </div>
            <div class="col col-metrics">
              <span v-for="line in formatMetricDisplay(session.metrics)" :key="line">{{ line }}</span>
              <span v-if="session.feedback" class="feedback">{{ session.feedback }}</span>
            </div>
            <div class="col col-actions">
              <button
                v-if="session.status === '计划'"
                class="primary-btn"
                @click="openComplete(session)"
              >
                完成
              </button>
              <button
                v-if="session.status === '计划'"
                class="ghost-btn"
                @click="openSkip(session)"
              >
                跳过
              </button>
            </div>
          </div>
        </div>

        <div v-if="sessionTotal > pagination.pageSize" class="pagination">
          <button :disabled="pagination.page === 1" @click="changePage(pagination.page - 1)">上一页</button>
          <span>{{ pagination.page }} / {{ totalPages }}</span>
          <button :disabled="pagination.page >= totalPages" @click="changePage(pagination.page + 1)">下一页</button>
        </div>
      </div>

      <div v-if="actionSession" class="action-panel">
        <div class="panel-header">
          <div class="panel-title">
            {{ actionMode === 'complete' ? '记录训练完成情况' : '跳过训练说明' }}
          </div>
          <button class="text-btn" @click="closeAction">关闭</button>
        </div>

        <div v-if="actionMode === 'complete'" class="action-form">
          <div class="form-grid">
            <label>
              实际时长（分钟）
              <input v-model.number="completeForm.duration_min" type="number" min="0" placeholder="30">
            </label>
            <label>
              心率区（%）
              <input v-model.number="completeForm.heart_rate_zone" type="number" min="0" max="100" placeholder="70">
            </label>
            <label>
              RPE（1-10）
              <input v-model.number="completeForm.rpe" type="number" min="1" max="10" placeholder="6">
            </label>
            <label>
              消耗热量（千卡）
              <input v-model.number="completeForm.calories" type="number" min="0" placeholder="200">
            </label>
          </div>
          <label class="textarea-label">
            训练备注
            <textarea v-model.trim="completeForm.notes" rows="3" placeholder="可选：补充动作质量/身体反馈"></textarea>
          </label>
          <div class="form-actions">
            <button class="primary-btn" :disabled="actionSubmitting" @click="submitComplete">
              {{ actionSubmitting ? '提交中…' : '提交' }}
            </button>
            <button class="ghost-btn" :disabled="actionSubmitting" @click="closeAction">取消</button>
          </div>
        </div>

        <div v-else class="action-form">
          <label class="textarea-label">
            跳过原因
            <textarea
              v-model.trim="skipForm.reason"
              rows="3"
              placeholder="请输入跳过原因，例如：身体不适、临时出差等"
            ></textarea>
          </label>
          <div class="form-actions">
            <button
              class="primary-btn"
              :disabled="actionSubmitting || !skipForm.reason"
              @click="submitSkip"
            >
              {{ actionSubmitting ? '提交中…' : '确认跳过' }}
            </button>
            <button class="ghost-btn" :disabled="actionSubmitting" @click="closeAction">取消</button>
          </div>
        </div>
      </div>
    </template>
  </dv-border-box-12>
</template>

<script>
import {
  getPlan as getWorkoutPlan,
  getSessions as getWorkoutSessions,
  completeSession as completeWorkoutSession,
  skipSession as skipWorkoutSession
} from '@/api/workout';

export default {
  name: 'WorkoutPlan',
  props: {
    plan: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      loading: false,
      planData: {
        goal: '',
        progress: 0,
        phases: [],
        sessions: []
      },
      sessionsLoading: false,
      sessionStatus: 'all',
      statusTabs: [
        { label: '全部', value: 'all' },
        { label: '计划', value: 'pending' },
        { label: '完成', value: 'completed' },
        { label: '跳过', value: 'skipped' }
      ],
      sessionList: [],
      sessionTotal: 0,
      pagination: { page: 1, pageSize: 6 },
      actionSession: null,
      actionMode: null,
      actionSubmitting: false,
      completeForm: { duration_min: null, heart_rate_zone: null, rpe: null, calories: null, notes: '' },
      skipForm: { reason: '' }
    };
  },
  computed: {
    progressWidth() {
      const value = Math.max(0, Math.min(100, Number(this.planData.progress) || 0));
      return `${value}%`;
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.sessionTotal / this.pagination.pageSize));
    }
  },
  watch: {
    plan: {
      handler(val) {
        if (val && Object.keys(val).length) {
          this.planData = this.normalizePlan(val);
        }
      },
      deep: true,
      immediate: true
    }
  },
  created() {
    this.refreshAll();
  },
  methods: {
    normalizePlan(payload = {}) {
      return {
        goal: payload.goal || '暂无个性化目标',
        progress: Number(payload.progress) || 0,
        phases: Array.isArray(payload.phases) ? payload.phases : [],
        sessions: Array.isArray(payload.sessions) ? payload.sessions : []
      };
    },
    async refreshAll() {
      await Promise.all([this.loadPlan(), this.loadSessions()]);
    },
    async loadPlan() {
      this.loading = true;
      try {
        const response = await getWorkoutPlan();
        const data = response?.data ?? response;
        this.planData = this.normalizePlan(data);
      } catch (error) {
        console.error('获取运动计划失败', error);
        this.$message && this.$message.error('获取运动计划失败，请稍后重试');
      } finally {
        this.loading = false;
      }
    },
    async loadSessions() {
      this.sessionsLoading = true;
      try {
        const params = {
          limit: this.pagination.pageSize,
          offset: (this.pagination.page - 1) * this.pagination.pageSize
        };
        if (this.sessionStatus !== 'all') params.status = this.sessionStatus;

        const response = await getWorkoutSessions(params);
        const payload = response?.data ?? response;
        this.sessionTotal = payload?.total || 0;
        this.sessionList = (payload?.sessions || []).map((session) => ({
          ...session,
          intensityText: this.formatIntensity(session.intensity),
          metrics: this.parseMetrics(session.metrics),
          adherence:
            session.adherence === null || session.adherence === undefined
              ? null
              : Math.round(Number(session.adherence))
        }));
      } catch (error) {
        console.error('获取训练会话失败', error);
        this.$message && this.$message.error('获取训练记录失败，请稍后重试');
      } finally {
        this.sessionsLoading = false;
      }
    },
    switchStatus(value) {
      if (this.sessionStatus === value) return;
      this.sessionStatus = value;
      this.pagination.page = 1;
      this.loadSessions();
    },
    changePage(page) {
      if (page < 1 || page > this.totalPages) return;
      this.pagination.page = page;
      this.loadSessions();
    },
    parseMetrics(metrics) {
      if (!metrics) return {};
      if (typeof metrics === 'string') {
        try {
          return JSON.parse(metrics);
        } catch (error) {
          return { summary: metrics };
        }
      }
      return metrics;
    },
    formatMetricDisplay(metricsObj) {
      if (!metricsObj || !Object.keys(metricsObj).length) return ['暂无记录'];
      const labels = {
        heart_rate_zone: '心率区',
        rpe: 'RPE',
        calories: '消耗',
        duration_min: '时长'
      };
      return Object.keys(metricsObj).map((key) => {
        const label = labels[key] || key;
        return `${label} ${metricsObj[key]}`;
      });
    },
    formatIntensity(level) {
      const map = { low: '低强度', medium: '中等强度', high: '高强度' };
      return map[level] || level || '未标注';
    },
    statusClass(statusLabel) {
      return {
        'is-pending': statusLabel === '计划',
        'is-completed': statusLabel === '完成',
        'is-skipped': statusLabel === '跳过'
      };
    },
    openComplete(session) {
      this.actionSession = session;
      this.actionMode = 'complete';
      this.completeForm = {
        duration_min: session.duration || null,
        heart_rate_zone: session.metrics?.heart_rate_zone || null,
        rpe: session.metrics?.rpe || null,
        calories: session.metrics?.calories || null,
        notes: ''
      };
    },
    openSkip(session) {
      this.actionSession = session;
      this.actionMode = 'skip';
      this.skipForm.reason = '';
    },
    closeAction() {
      if (this.actionSubmitting) return;
      this.actionSession = null;
      this.actionMode = null;
      this.completeForm = { duration_min: null, heart_rate_zone: null, rpe: null, calories: null, notes: '' };
      this.skipForm.reason = '';
    },
    buildCompletePayload() {
      const payload = { session_id: this.actionSession?.id };
      ['duration_min', 'heart_rate_zone', 'rpe', 'calories'].forEach((key) => {
        const value = this.completeForm[key];
        if (value !== null && value !== '' && !Number.isNaN(value)) {
          payload[key] = value;
        }
      });
      if (this.completeForm.notes) {
        payload.metric_notes = this.completeForm.notes;
      }
      return payload;
    },
    async submitComplete() {
      if (!this.actionSession) return;
      this.actionSubmitting = true;
      try {
        const payload = this.buildCompletePayload();
        await completeWorkoutSession(payload);
        this.$message && this.$message.success('训练完成情况已记录');
        this.closeAction();
        this.refreshAll();
      } catch (error) {
        console.error('记录训练完成失败', error);
        this.$message && this.$message.error('提交失败，请稍后再试');
      } finally {
        this.actionSubmitting = false;
      }
    },
    async submitSkip() {
      if (!this.actionSession) return;
      if (!this.skipForm.reason) {
        this.$message && this.$message.error('请填写跳过原因');
        return;
      }
      this.actionSubmitting = true;
      try {
        await skipWorkoutSession({ session_id: this.actionSession.id, reason: this.skipForm.reason });
        this.$message && this.$message.success('已记录跳过情况');
        this.closeAction();
        this.refreshAll();
      } catch (error) {
        console.error('跳过训练失败', error);
        this.$message && this.$message.error('提交失败，请稍后再试');
      } finally {
        this.actionSubmitting = false;
      }
    }
  }
};
</script>

<style lang="less" scoped>
/* 原有样式保留，上面新增模块的样式如下 */
.panel { padding: 15px; box-sizing: border-box; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.panel-title { font-size: 18px; font-weight: bold; }
.text-btn { border: none; background: transparent; color: #39affd; cursor: pointer; }
.plan-body { display: flex; flex-direction: column; gap: 12px; }
.plan-progress { display: flex; align-items: center; gap: 15px; }
.progress-bar { flex: 1; height: 12px; border-radius: 12px; background: rgba(57, 175, 253, 0.2); }
.progress-value { height: 100%; border-radius: 12px; background: linear-gradient(90deg, #39affd, #0efcff); }
.phase-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
.phase-card { padding: 10px; border-radius: 12px; background: rgba(16, 45, 80, 0.6); font-size: 13px; }
.phase-card.ghost { color: #6ea1ff; opacity: 0.7; }
.phase-name { font-weight: bold; margin-bottom: 4px; }
.phase-meta { font-size: 12px; color: #6ea1ff; margin-top: 6px; }
.session-list { display: flex; flex-direction: column; gap: 8px; }
.session-item { padding: 10px; border-radius: 12px; background: rgba(16, 45, 80, 0.55); }
.session-item.ghost { color: #6ea1ff; opacity: 0.7; }
.session-title { font-weight: bold; margin-bottom: 4px; }
.session-meta { display: flex; flex-wrap: wrap; gap: 12px; font-size: 12px; color: #6ea1ff; }

.session-section { margin-top: 16px; padding-top: 12px; border-top: 1px solid rgba(57, 175, 253, 0.15); display: flex; flex-direction: column; gap: 12px; }
.session-section-header { display: flex; justify-content: space-between; align-items: center; }
.filter-tabs { display: flex; gap: 8px; }
.tab-btn { padding: 6px 12px; border-radius: 999px; border: 1px solid rgba(57, 175, 253, 0.4); background: transparent; color: #cfe7ff; cursor: pointer; }
.tab-btn.active { background: rgba(57, 175, 253, 0.2); color: #39affd; }

.session-table { display: flex; flex-direction: column; gap: 8px; }
.session-row { display: grid; grid-template-columns: 1.4fr 1.1fr 0.9fr 1.6fr 0.6fr; gap: 10px; padding: 12px; border-radius: 12px; background: rgba(16, 45, 80, 0.55); font-size: 13px; }
.session-header { font-weight: bold; background: rgba(16, 45, 80, 0.3); }
.col { display: flex; flex-direction: column; gap: 4px; }
.col-activity .name { font-weight: bold; }
.col-status { font-weight: bold; }
.col-status.is-pending { color: #ffdf6b; }
.col-status.is-completed { color: #54f0a0; }
.col-status.is-skipped { color: #ff7e7e; }
.adherence { display: block; font-size: 12px; color: #6ea1ff; }
.col-metrics span { display: block; color: #cfe7ff; }
.feedback { font-size: 12px; color: #6ea1ff; }
.col-actions { display: flex; flex-direction: column; gap: 6px; align-items: flex-start; }
.primary-btn, .ghost-btn { border: none; border-radius: 8px; padding: 6px 12px; font-weight: bold; cursor: pointer; }
.primary-btn { background: linear-gradient(90deg, #2af7ff, #26b3ff); color: #142c4d; }
.ghost-btn { background: transparent; border: 1px solid rgba(57, 175, 253, 0.5); color: #39affd; }

.pagination { display: flex; justify-content: center; align-items: center; gap: 12px; font-size: 13px; color: #cfe7ff; }
.pagination button { padding: 6px 14px; border-radius: 8px; border: none; background: rgba(57, 175, 253, 0.25); color: #fff; cursor: pointer; }

.action-panel { margin-top: 16px; border-radius: 12px; padding: 16px; background: rgba(16, 45, 80, 0.6); display: flex; flex-direction: column; gap: 12px; }
.action-form { display: flex; flex-direction: column; gap: 12px; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
label { font-size: 12px; color: #cfe7ff; display: flex; flex-direction: column; gap: 6px; }
input, textarea { border-radius: 8px; border: 1px solid rgba(57, 175, 253, 0.4); padding: 8px; background: rgba(255, 255, 255, 0.08); color: #fff; }
textarea { resize: none; }
.form-actions { display: flex; gap: 12px; justify-content: flex-end; }
.panel-empty { padding: 24px 0; text-align: center; color: #6ea1ff; }
</style>

  
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
  .plan-body {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .plan-progress {
    display: flex;
    align-items: center;
    gap: 15px;
  }
  .progress-bar {
    flex: 1;
    height: 12px;
    border-radius: 12px;
    background: rgba(57, 175, 253, 0.2);
  }
  .progress-value {
    height: 100%;
    border-radius: 12px;
    background: linear-gradient(90deg, #39affd, #0efcff);
  }
  .phase-list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
  }
  .phase-card {
    padding: 10px;
    border-radius: 12px;
    background: rgba(16, 45, 80, 0.6);
    font-size: 13px;
  }
  .phase-name {
    font-weight: bold;
    margin-bottom: 4px;
  }
  .phase-meta {
    font-size: 12px;
    color: #6ea1ff;
    margin-top: 6px;
  }
  .session-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .session-item {
    padding: 10px;
    border-radius: 12px;
    background: rgba(16, 45, 80, 0.55);
  }
  .session-title {
    font-weight: bold;
    margin-bottom: 4px;
  }
  .session-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 12px;
    color: #6ea1ff;
  }
  </style>
  