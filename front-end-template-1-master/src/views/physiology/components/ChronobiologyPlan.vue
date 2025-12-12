<template>
  <dv-border-box-11 class="panel chrono-panel">
    <div class="panel-header">
      <div>
        <div class="panel-title">生物钟调节计划</div>
        <small>目标睡眠：{{ planData.target }}</small>
      </div>
      <button class="text-btn" :disabled="loadingPlan" @click="refreshPlan">
        {{ loadingPlan ? '刷新中…' : '刷新' }}
      </button>
    </div>

    <div v-if="loadingPlan" class="panel-empty">正在加载生物钟计划...</div>
    <template v-else>
      <div class="chrono-tip">{{ planData.tip }}</div>

      <div class="schedule-list">
        <div v-for="item in planData.schedule" :key="item.day" class="schedule-item">
          <div class="day">{{ item.day }}</div>
          <div class="slot">{{ item.sleep }} - {{ item.wake }}</div>
          <div class="adherence">遵循度 {{ item.adherence }}%</div>
          <div class="note">{{ item.note }}</div>
        </div>
        <div v-if="!planData.schedule.length" class="panel-empty small">暂无行动记录</div>
      </div>

      <div v-if="planData.sleepTrend.nights.length" class="sleep-chart" ref="sleepChart"></div>
      <div v-else class="sleep-chart empty">暂无可显示的睡眠记录</div>

      <div class="form-section">
        <div class="form-header">
          <div class="panel-title small">每日作息记录</div>
          <small>POST /api/chronobiology/update</small>
        </div>
        <div class="form-grid">
          <label>
            记录日期
            <input type="date" v-model="updateForm.date" />
          </label>
          <label>
            入睡时间
            <input type="time" v-model="updateForm.sleep_time" placeholder="23:00" />
          </label>
          <label>
            起床时间
            <input type="time" v-model="updateForm.wake_time" placeholder="07:00" />
          </label>
          <label>
            咖啡因时间
            <input type="time" v-model="updateForm.caffeine_time" />
          </label>
          <label>
            咖啡因摄入
            <select v-model="updateForm.caffeine_amount">
              <option value="low">少量</option>
              <option value="moderate">适中</option>
              <option value="high">较多</option>
            </select>
          </label>
        </div>
        <div class="toggle-row">
          <label><input type="checkbox" v-model="updateForm.light_morning" />早晨光照</label>
          <label><input type="checkbox" v-model="updateForm.light_evening" />晚间光照</label>
        </div>
        <div class="submit-row">
          <button class="primary-btn" :disabled="submittingAction" @click="submitUpdate">
            {{ submittingAction ? '提交中…' : '保存记录' }}
          </button>
        </div>
      </div>

      <div class="form-section">
        <div class="form-header">
          <div class="panel-title small">睡眠会话记录</div>
          <small>POST /api/chronobiology/record_sleep</small>
        </div>
        <div class="form-grid">
          <label>
            睡眠开始日期
            <input type="date" v-model="sleepForm.start_date" />
          </label>
          <label>
            睡眠开始时间
            <input type="time" v-model="sleepForm.start_time" placeholder="23:10" />
          </label>
          <label>
            醒来日期
            <input type="date" v-model="sleepForm.end_date" />
          </label>
          <label>
            醒来时间
            <input type="time" v-model="sleepForm.end_time" placeholder="07:05" />
          </label>
          <label>
            夜间苏醒次数
            <input type="number" min="0" v-model.number="sleepForm.wake_episodes" />
          </label>
          <label>
            数据来源
            <select v-model="sleepForm.device">
              <option value="manual">手动录入</option>
              <option value="wearable">穿戴设备</option>
              <option value="app">第三方应用</option>
            </select>
          </label>
          <label>
            深睡 (%)
            <input type="number" min="0" max="100" v-model.number="sleepForm.deep" />
          </label>
          <label>
            浅睡 (%)
            <input type="number" min="0" max="100" v-model.number="sleepForm.light" />
          </label>
          <label>
            REM (%)
            <input type="number" min="0" max="100" v-model.number="sleepForm.rem" />
          </label>
        </div>
        <div class="submit-row">
          <button class="primary-btn" :disabled="submittingSleep" @click="submitSleep">
            {{ submittingSleep ? '提交中…' : '保存睡眠' }}
          </button>
        </div>
      </div>
    </template>
  </dv-border-box-11>
</template>

<script>
import {
  getPlan as getChronoPlan,
  updateAction as updateChronoAction,
  recordSleep as recordSleepSession
} from '@/api/chronobiology';

const formatDate = (date) => {
  if (!date) return '';
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const defaultPlanState = () => ({
  target: '未设置',
  tip: '保持记录以获得更多建议',
  schedule: [],
  sleepTrend: { nights: [], quality: [], efficiency: [] }
});

export default {
  name: 'ChronobiologyPlan',
  props: {
    plan: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    const today = formatDate(new Date());
    return {
      loadingPlan: false,
      planData: defaultPlanState(),
      chart: null,
      submittingAction: false,
      submittingSleep: false,
      updateForm: {
        date: today,
        sleep_time: '',
        wake_time: '',
        light_morning: true,
        light_evening: false,
        caffeine_time: '10:00',
        caffeine_amount: 'moderate'
      },
      sleepForm: {
        start_date: today,
        start_time: '',
        end_date: today,
        end_time: '',
        wake_episodes: 0,
        device: 'manual',
        deep: 25,
        light: 55,
        rem: 20
      }
    };
  },
  watch: {
    plan: {
      deep: true,
      immediate: true,
      handler(val) {
        if (val && Object.keys(val).length) {
          this.planData = this.normalizePlan(val);
        }
      }
    },
    'planData.sleepTrend': {
      deep: true,
      handler() {
        this.$nextTick(() => this.initChart());
      }
    }
  },
  created() {
    this.refreshPlan();
  },
  mounted() {
    window.addEventListener('resize', this.handleResize);
  },
  beforeDestroy() {
    this.disposeChart();
    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    normalizePlan(raw = {}) {
      const schedule = Array.isArray(raw.schedule) ? raw.schedule : [];
      const scores = raw.sleepScores || raw.sleepTrend || {};
      return {
        target: raw.target || '未设置',
        tip: raw.tip || '保持记录以获得更多建议',
        schedule,
        sleepTrend: {
          nights: scores.nights || [],
          quality: scores.quality || scores['质量'] || [],
          efficiency: scores.efficiency || scores['效率'] || []
        }
      };
    },
    async refreshPlan() {
      await this.loadPlan();
    },
    async loadPlan() {
      this.loadingPlan = true;
      try {
        const response = await getChronoPlan();
        const payload = response?.data ?? response;
        this.planData = this.normalizePlan(payload);
      } catch (error) {
        console.error('获取生物钟计划失败', error);
        this.$message && this.$message.error('无法加载生物钟计划，请稍后重试');
      } finally {
        this.loadingPlan = false;
      }
    },
    initChart() {
      const trend = this.planData.sleepTrend || {};
      if (!this.$refs.sleepChart || !trend.nights || !trend.nights.length) {
        this.disposeChart();
        return;
      }
      const option = {
        tooltip: { trigger: 'axis' },
        legend: { data: ['睡眠质量', '睡眠效率'], textStyle: { color: '#cfe7ff' } },
        grid: { left: '6%', right: '4%', top: '18%', bottom: '12%' },
        xAxis: {
          type: 'category',
          data: trend.nights,
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
            data: trend.quality,
            itemStyle: { color: '#14c5ff' },
            areaStyle: { color: 'rgba(20,197,255,0.25)' }
          },
          {
            name: '睡眠效率',
            type: 'line',
            smooth: true,
            data: trend.efficiency,
            itemStyle: { color: '#f6c94a' }
          }
        ]
      };
      if (this.chart) {
        this.chart.dispose();
      }
      this.chart = this.$echarts.init(this.$refs.sleepChart);
      this.chart.setOption(option);
    },
    handleResize() {
      this.chart && this.chart.resize();
    },
    disposeChart() {
      if (this.chart) {
        this.chart.dispose();
        this.chart = null;
      }
    },
    buildUpdatePayload() {
      return {
        date: this.updateForm.date,
        sleep_time: this.updateForm.sleep_time || undefined,
        wake_time: this.updateForm.wake_time || undefined,
        light_exposure: {
          morning: this.updateForm.light_morning,
          evening: this.updateForm.light_evening
        },
        caffeine_intake: {
          time: this.updateForm.caffeine_time,
          amount: this.updateForm.caffeine_amount
        }
      };
   
    },
    async submitUpdate() {
      if (!this.updateForm.sleep_time && !this.updateForm.wake_time) {
        this.$message && this.$message.error('至少填写一个睡眠/起床时间');
        return;
      }
      this.submittingAction = true;
      try {
        await updateChronoAction(this.buildUpdatePayload());
        this.$message && this.$message.success('已保存作息记录');
        this.refreshPlan();
      } catch (error) {
        console.error('更新生物钟记录失败', error);
        this.$message && this.$message.error('提交失败，请稍后重试');
      } finally {
        this.submittingAction = false;
      }
    },
    buildSleepPayload() {
      return {
        start_time: `${this.sleepForm.start_date} ${this.sleepForm.start_time}`,
        end_time: `${this.sleepForm.end_date} ${this.sleepForm.end_time}`,
        wake_episodes: Number(this.sleepForm.wake_episodes) || 0,
        device: this.sleepForm.device,
        sleep_stages: {
          deep: Number(this.sleepForm.deep) || 0,
          light: Number(this.sleepForm.light) || 0,
          rem: Number(this.sleepForm.rem) || 0
        }
      };
    },
    async submitSleep() {
      if (!this.sleepForm.start_date || !this.sleepForm.start_time || !this.sleepForm.end_date || !this.sleepForm.end_time) {
        this.$message && this.$message.error('请填写完整的开始/结束时间');
        return;
      }
      this.submittingSleep = true;
      try {
        await recordSleepSession(this.buildSleepPayload());
        this.$message && this.$message.success('睡眠记录已保存');
        this.resetSleepForm();
        this.refreshPlan();
      } catch (error) {
        console.error('记录睡眠失败', error);
        this.$message && this.$message.error('提交失败，请稍后重试');
      } finally {
        this.submittingSleep = false;
      }
    },
    resetSleepForm() {
      const today = formatDate(new Date());
      this.sleepForm.start_date = today;
      this.sleepForm.end_date = today;
      this.sleepForm.start_time = '';
      this.sleepForm.end_time = '';
      this.sleepForm.wake_episodes = 0;
    }
  }
};
</script>

<style lang="less" scoped>
.panel { padding: 15px; box-sizing: border-box; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.panel-title { font-size: 18px; font-weight: bold; }
.panel-title.small { font-size: 15px; }
.text-btn { border: none; background: transparent; color: #39affd; cursor: pointer; }
.chrono-tip { margin-bottom: 10px; padding: 10px; border-radius: 10px; background: rgba(16, 45, 80, 0.55); }
.schedule-list { display: flex; flex-direction: column; gap: 8px; }
.schedule-item { display: grid; grid-template-columns: 80px 1fr 110px 1fr; gap: 10px; padding: 8px 10px; border-radius: 10px; background: rgba(16, 45, 80, 0.45); font-size: 13px; }
.sleep-chart { width: 100%; height: 220px; margin-top: 10px; }
.sleep-chart.empty { display: flex; align-items: center; justify-content: center; border-radius: 10px; background: rgba(16, 45, 80, 0.45); color: #6ea1ff; font-size: 13px; }
.panel-empty { padding: 20px 0; text-align: center; color: #6ea1ff; }
.panel-empty.small { padding: 10px 0; font-size: 12px; }
.form-section { margin-top: 14px; padding: 12px; border-radius: 10px; background: rgba(16, 45, 80, 0.45); display: flex; flex-direction: column; gap: 10px; }
.form-header { display: flex; justify-content: space-between; align-items: center; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.form-grid label { font-size: 12px; color: #cfe7ff; display: flex; flex-direction: column; gap: 4px; }
input, select { border-radius: 8px; border: 1px solid rgba(57, 175, 253, 0.4); padding: 8px; background: rgba(255, 255, 255, 0.05); color: #fff; }
.toggle-row { display: flex; gap: 20px; font-size: 12px; color: #cfe7ff; }
.submit-row { display: flex; justify-content: flex-end; }
.primary-btn { border: none; border-radius: 8px; padding: 6px 16px; font-weight: bold; background: linear-gradient(90deg, #2af7ff, #26b3ff); color: #142c4d; cursor: pointer; }
.textarea { resize: none; }
@media (max-width: 600px) { .schedule-item { grid-template-columns: 1fr 1fr; } }
</style>
