<template>
  <div class="physiology-page">
    <!-- 调试信息（临时显示） -->
    <div v-if="debugMode" class="debug-panel">
      <h3>调试信息</h3>
      <p>加载状态: {{ loading ? '加载中' : '完成' }}</p>
      <p>疾病风险数量: {{ diseaseRisks.length }}</p>
      <p>API响应: {{ apiResponse ? '有数据' : '无数据' }}</p>
      <button @click="toggleDebug">隐藏调试</button>
    </div>
    
    <transition name="fade" mode="out-in">
      <div v-if="loading" key="loading" class="loading-wrapper">
        <dv-loading>{{ loadingMessage || 'Loading...' }}</dv-loading>
        <p v-if="loadingMessage" class="loading-message">{{ loadingMessage }}</p>
      </div>
      <div v-else key="content" class="physiology-grid">
        <div class="column column-form">
          <dv-border-box-12 class="panel">
            <div class="panel-header">
              <div>
                <div class="panel-title">健康数据采集</div>
                <small>支持完整健康指标录入</small>
              </div>
              <dv-decoration-5 class="dec-line" :color="['#39affd', '#142c4d']" />
            </div>

            <div class="metric-form">
              <div class="form-row">
                <label>心率(bpm)
                  <input type="number" v-model.number="metricForm.heart_rate" placeholder="78" min="30" max="200" />
                </label>
                <label>收缩压(mmHg)
                  <input type="number" v-model.number="metricForm.blood_pressure_systolic" placeholder="120" min="60" max="250" />
                </label>
                <label>舒张压(mmHg)
                  <input type="number" v-model.number="metricForm.blood_pressure_diastolic" placeholder="78" min="40" max="150" />
                </label>
              </div>
              
              <div class="form-row">
                <label>血氧(%)
                  <input type="number" v-model.number="metricForm.blood_oxygen" placeholder="98" min="70" max="100" step="0.1" />
                </label>
                <label>呼吸频率(次/分)
                  <input type="number" v-model.number="metricForm.resp_rate" placeholder="16" min="8" max="40" />
                </label>
                <label>体温(℃)
                  <input type="number" v-model.number="metricForm.temperature" placeholder="36.5" step="0.1" min="35" max="42" />
                </label>
              </div>
              
              <div class="form-row">
                <label>血糖(mmol/L)
                  <input type="number" v-model.number="metricForm.glucose" placeholder="5.6" step="0.1" min="2" max="30" />
                </label>
                <label>睡眠时长(h)
                  <input type="number" v-model.number="metricForm.sleep_duration" step="0.1" placeholder="7.2" min="0" max="24" />
                </label>
                <label>压力指数(0-100)
                  <input type="number" v-model.number="metricForm.stress_level" placeholder="35" min="0" max="100" />
                </label>
              </div>
              
              <div class="form-row">
                <label>步数(今日)
                  <input type="number" v-model.number="metricForm.steps" placeholder="5200" min="0" max="50000" />
                </label>
                <label>体重(kg)
                  <input type="number" v-model.number="metricForm.weight_kg" placeholder="65.5" step="0.1" min="20" max="300" />
                </label>
                <label>来源
                  <select v-model="metricForm.source">
                    <option value="manual">手动录入</option>
                    <option value="wearable">可穿戴设备</option>
                    <option value="hospital">医院体检</option>
                    <option value="app">手机APP</option>
                  </select>
                </label>
              </div>
              
              <div class="form-row">
                <label>备注
                  <input type="text" v-model="metricForm.notes" placeholder="例如：餐后2小时测量，感觉良好" />
                </label>
              </div>
            </div>

            <div class="form-actions">
              <button :disabled="submitLoading" @click="submitMetricForm">
                {{ submitLoading ? '提交中...' : '提交健康数据' }}
              </button>
              <button type="button" class="ghost" @click="resetMetricForm">重置</button>
            </div>
          </dv-border-box-12>
        </div>

        <div class="column column-risk">
          <dv-border-box-13 class="panel">
            <div class="panel-header">
              <div class="panel-title">风险预警中心</div>
              <small>6 个月趋势 + 重点疾病</small>
            </div>
            <div class="risk-content">
              <div ref="trendChart" class="chart-block"></div>
              <div class="disease-risk-list">
                <div 
                  v-for="(item, index) in diseaseRisks" 
                  :key="getRiskKey(item, index)" 
                  class="risk-item"
                >
                  <div class="risk-name">{{ getDiseaseName(item) }}</div>
                  <div class="risk-score">{{ calculateRiskPercent(getRiskValue(item)) }}</div>
                  <div class="risk-desc">{{ getRiskDescription(item) }}</div>
                </div>
                
                <template v-if="diseaseRisks.length === 0">
                  <div class="risk-item empty">
                    <div class="risk-name">暂无数据</div>
                    <div class="risk-desc">提交健康数据后生成风险预警</div>
                  </div>
                </template>
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
      </div>
    </transition>
  </div>
</template>

<script>
import { submitMetrics } from '@/api/metrics';
import { getRiskAssessment } from '@/api/risk';

const defaultRiskTrend = () => ({ 
  months: [], 
  values: [] 
});

export default {
  name: 'PhysiologyDashboard',
  data() {
    return {
      loading: true,
      submitLoading: false,
      loadingMessage: '正在加载风险评估数据...',
      debugMode: false,  // 默认关闭调试模式
      apiResponse: null,
      metricForm: {
        // 原有字段
        heart_rate: null,
        blood_pressure_systolic: null,
        blood_pressure_diastolic: null,
        blood_oxygen: null,
        sleep_duration: null,
        stress_level: null,
        steps: null,
        weight_kg: null,
        source: 'manual',
        notes: '',
        
        // 新增的数据库字段
        resp_rate: null,      // 呼吸频率
        temperature: null,    // 体温
        glucose: null,        // 血糖
      },
      diseaseRisks: [],
      riskTrend: defaultRiskTrend(),
      riskFactors: [],
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
    formattedRiskFactors() {
      return this.riskFactors.map((item) => {
        const factor = item && item.factor ? item.factor : '-';
        const weight = item && item.weight ? item.weight : 0;
        return {
          factor,
          weight,
          percent: this.formatPercent(weight)
        };
      });
    }
  },
  created() {
    this.loadRiskData();
    window.addEventListener('resize', this.handleResize);
  },
  beforeDestroy() {
    this.disposeCharts();
    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    getRiskKey(item, index) {
      if (item && item.disease) {
        return `risk-${item.disease}-${index}`;
      }
      return `risk-${index}`;
    },
    
    getDiseaseName(item) {
      return item && item.disease ? item.disease : '未知';
    },
    
    getRiskValue(item) {
      return item && item.risk ? item.risk : 0;
    },
    
    getRiskDescription(item) {
      return item && item.desc ? item.desc : '等待最新评估';
    },
    
    calculateRiskPercent(riskValue) {
      const risk = riskValue || 0;
      return `${(risk * 100).toFixed(0)}%`;
    },
    
    formatPercent(value) {
      const num = value || 0;
      return `${(num ).toFixed(1)}%`;
    },
    
    async loadRiskData() {
      this.loading = true;
      this.loadingMessage = '正在请求风险评估API...';
      console.log('[PhysiologyDashboard] 开始加载风险数据...');
      
      try {
        this.loadingMessage = '正在获取风险评估...';
        const response = await getRiskAssessment();
        console.log('[PhysiologyDashboard] API响应:', response);
        
        if (response && typeof response === 'object') {
          const data = response;
          this.apiResponse = data;
          console.log('[PhysiologyDashboard] API数据:', data);
          
          // 处理疾病风险数据
          if (Array.isArray(data.diseaseRisks) && data.diseaseRisks.length > 0) {
            this.diseaseRisks = data.diseaseRisks.map(item => ({
              disease: item.disease || '未知疾病',
              risk: typeof item.risk === 'number' ? item.risk : 0,
              desc: item.desc || '等待评估'
            }));
            console.log(`[PhysiologyDashboard] 加载了 ${this.diseaseRisks.length} 条疾病风险`);
          } else {
            console.warn('[PhysiologyDashboard] 疾病风险数据为空');
            this.diseaseRisks = [];
          }
          
          // 处理趋势数据
          if (data.riskTrend) {
            this.riskTrend = {
              months: Array.isArray(data.riskTrend.months) ? data.riskTrend.months : [],
              values: Array.isArray(data.riskTrend.values) ? data.riskTrend.values : []
            };
            console.log(`[PhysiologyDashboard] 趋势数据: ${this.riskTrend.months.length}个月`);
          } else {
            this.riskTrend = defaultRiskTrend();
          }
          
          // 处理风险因素
          if (Array.isArray(data.riskFactors)) {
            this.riskFactors = data.riskFactors;
            console.log(`[PhysiologyDashboard] 风险因素: ${this.riskFactors.length}个`);
          } else {
            this.riskFactors = [];
          }
          
        } else {
          console.error('[PhysiologyDashboard] API响应数据为空或格式错误');
          this.diseaseRisks = [];
          this.riskTrend = defaultRiskTrend();
          this.riskFactors = [];
        }
        
      } catch (error) {
        console.error('[PhysiologyDashboard] 加载失败:', error);
        console.error('[PhysiologyDashboard] 错误详情:', error.response || error.message);
        
        // 使用模拟数据
        this.useMockData();
        
      } finally {
        this.loading = false;
        this.loadingMessage = '';
        this.refreshRiskBoard();
        
        this.$nextTick(() => {
          setTimeout(() => {
            this.initTrendChart();
            console.log('[PhysiologyDashboard] 图表初始化完成');
          }, 100);
        });
      }
    },

    useMockData() {
      console.log('[PhysiologyDashboard] 使用模拟数据');
      this.diseaseRisks = [
        { disease: '高血压', risk: 0.65, desc: '血压波动较大，需密切监控' },
        { disease: '糖尿病', risk: 0.45, desc: '血糖水平偏高，需控制饮食' },
        { disease: '代谢综合征', risk: 0.7, desc: '腰臀比偏高，久坐导致胰岛负荷' },
        { disease: '睡眠呼吸暂停', risk: 0.45, desc: '睡眠效率下降，夜间心率波动大' }
      ];
      
      this.riskTrend = {
        months: ['1月', '2月', '3月', '4月', '5月', '6月'],
        values: [0.65, 0.62, 0.58, 0.55, 0.52, 0.50]
      };
      
      this.riskFactors = [
        { factor: '血压偏高', weight: 0.4 },
        { factor: '血糖波动', weight: 0.25 },
        { factor: '体重超标', weight: 0.2 },
        { factor: '睡眠不足', weight: 0.1 },
        { factor: '缺乏运动', weight: 0.05 }
      ];
    },
    
    refreshRiskBoard() {
      const rows = this.formattedRiskFactors.map((item) => [
        item.factor,
        item.percent
      ]);
      
      if (rows.length === 0) {
        rows.push(['暂无风险因素', '0%']);
      }
      
      this.riskBoardConfig = { 
        ...this.riskBoardConfig, 
        data: rows 
      };
    },
    
    async submitMetricForm() {
      const requiredFields = ['heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic'];
      const missingFields = requiredFields.filter(field => {
        const value = this.metricForm[field];
        return value === null || value === undefined || value === '';
      });
      
      if (missingFields.length > 0) {
        if (this.$message && this.$message.error) {
          this.$message.error('请填写心率和血压数据');
        }
        return;
      }
      
      this.submitLoading = true;
      try {
        // 构建提交数据，过滤空值
        const payload = {};
        Object.keys(this.metricForm).forEach(key => {
          if (this.metricForm[key] !== null && this.metricForm[key] !== '') {
            payload[key] = this.metricForm[key];
          }
        });
        
        await submitMetrics(payload);
        if (this.$message && this.$message.success) {
          this.$message.success('健康数据已提交到监测中心');
        }
        
        // 刷新风险评估数据
        await this.loadRiskData();
        
        // 重置表单
        this.resetMetricForm();
        
      } catch (error) {
        console.error('[PhysiologyDashboard] 提交失败', error);
        if (this.$message && this.$message.error) {
          this.$message.error('提交失败，请稍后重试');
        }
      } finally {
        this.submitLoading = false;
      }
    },
    
    resetMetricForm() {
      this.metricForm = {
        heart_rate: null,
        blood_pressure_systolic: null,
        blood_pressure_diastolic: null,
        blood_oxygen: null,
        resp_rate: null,
        temperature: null,
        glucose: null,
        sleep_duration: null,
        stress_level: null,
        steps: null,
        weight_kg: null,
        source: 'manual',
        notes: ''
      };
    },
    
    initTrendChart() {
      const trend = this.riskTrend || defaultRiskTrend();
      const months = Array.isArray(trend.months) ? trend.months : [];
      const values = Array.isArray(trend.values) ? trend.values : [];
      
      if (!months.length || !this.$refs.trendChart) {
        this.disposeChart('trend');
        return;
      }
      
      const option = {
        tooltip: { 
          trigger: 'axis', 
          formatter: (params) => {
            const param = params[0];
            return `${param.name}<br/>风险: ${(param.value * 100).toFixed(1)}%`;
          }
        },
        grid: { 
          left: '6%', 
          right: '4%', 
          top: '12%', 
          bottom: '15%' 
        },
        xAxis: {
          type: 'category',
          data: months,
          boundaryGap: false,
          axisLine: { 
            lineStyle: { 
              color: '#39affd' 
            } 
          },
          axisLabel: { 
            color: '#cfe7ff' 
          }
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 1,
          axisLabel: { 
            color: '#cfe7ff', 
            formatter: (val) => `${Math.round(val * 100)}%` 
          },
          splitLine: { 
            lineStyle: { 
              color: 'rgba(57,175,253,0.2)' 
            } 
          }
        },
        series: [
          {
            name: '风险评分',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: { 
              color: '#0efcff' 
            },
            itemStyle: { 
              color: '#0efcff' 
            },
            areaStyle: { 
              color: 'rgba(14,252,255,0.25)' 
            },
            data: values
          }
        ]
      };
      
      this.setChart('trend', this.$refs.trendChart, option);
    },
    
    setChart(name, dom, option) {
      if (!dom || !this.$echarts) return;
      if (this.charts[name]) {
        this.charts[name].dispose();
      }
      const chart = this.$echarts.init(dom);
      chart.setOption(option);
      this.$set(this.charts, name, chart);
    },
    
    disposeChart(name) {
      const chart = this.charts[name];
      if (chart) {
        chart.dispose();
        this.$delete(this.charts, name);
      }
    },
    
    disposeCharts() {
      Object.keys(this.charts).forEach((name) => {
        this.disposeChart(name);
      });
    },
    
    handleResize() {
      Object.values(this.charts).forEach((chart) => {
        if (chart && chart.resize) {
          chart.resize();
        }
      });
    },
    
    toggleDebug() {
      this.debugMode = !this.debugMode;
    }
  }
};
</script>

<style lang="less" scoped>
.physiology-page { 
  width: 100%; 
  min-height: calc(100vh - 120px); 
  color: #cfe7ff; 
}

// 调试面板样式
.debug-panel {
  position: fixed;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 10px;
  border-radius: 5px;
  z-index: 1000;
  font-size: 12px;
  max-width: 300px;
  
  h3 {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #0efcff;
  }
  
  p {
    margin: 4px 0;
    line-height: 1.4;
  }
  
  button {
    margin-top: 8px;
    padding: 4px 8px;
    background: #39affd;
    color: white;
    border: none;
    border-radius: 3px;
    cursor: pointer;
    font-size: 12px;
    
    &:hover {
      background: #26b3ff;
    }
  }
}

.loading-wrapper { 
  display: flex; 
  flex-direction: column;
  align-items: center; 
  justify-content: center; 
  min-height: 400px; 
  
  .loading-message {
    margin-top: 16px;
    color: #9dcfff;
    font-size: 14px;
  }
}

.physiology-grid { 
  display: grid; 
  grid-template-columns: 1fr 1fr; 
  gap: 20px; 
}

.column { 
  display: flex; 
  flex-direction: column; 
  gap: 20px; 
}

.panel { 
  padding: 18px; 
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

.metric-form { 
  display: flex; 
  flex-direction: column; 
  gap: 14px; 
}

.form-row { 
  display: grid; 
  grid-template-columns: repeat(3, 1fr); 
  gap: 12px; 
}

.form-row label { 
  display: flex; 
  flex-direction: column; 
  font-size: 13px; 
  color: #70c8ff; 
}

.form-row input,
.form-row select { 
  margin-top: 6px; 
  border-radius: 12px; 
  border: 1px solid rgba(57, 175, 253, 0.3); 
  padding: 8px 12px; 
  background: rgba(255, 255, 255, 0.08); 
  color: #fff; 
  transition: border-color 0.3s;
  
  &:focus {
    outline: none;
    border-color: #39affd;
  }
}

.form-actions { 
  margin-top: 14px; 
  display: flex; 
  gap: 12px; 
}

.form-actions button { 
  flex: 1; 
  border: none; 
  border-radius: 20px; 
  padding: 10px 0; 
  cursor: pointer; 
  color: #020a2b; 
  background: linear-gradient(90deg, #2af7ff, #26b3ff);
  font-weight: bold;
  transition: opacity 0.3s;
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  &:hover:not(:disabled) {
    opacity: 0.9;
  }
}

.form-actions .ghost { 
  background: transparent; 
  color: #39affd; 
  border: 1px solid #39affd; 
  
  &:hover {
    background: rgba(57, 175, 253, 0.1);
  }
}

.risk-content { 
  display: flex; 
  gap: 14px; 
}

.chart-block { 
  flex: 1; 
  height: 260px; 
  min-width: 300px;
}

.disease-risk-list { 
  width: 240px; 
  display: flex; 
  flex-direction: column; 
  gap: 12px; 
}

.risk-item { 
  padding: 12px; 
  border-radius: 12px; 
  background: rgba(16, 45, 80, 0.6); 
  transition: transform 0.3s, background 0.3s;
  
  &:hover {
    transform: translateY(-2px);
    background: rgba(16, 45, 80, 0.8);
  }
  
  &.empty {
    align-items: center;
    text-align: center;
    color: #89bff4;
    background: rgba(16, 45, 80, 0.4);
  }
}

.risk-name { 
  font-weight: bold; 
  margin-bottom: 5px;
}

.risk-score { 
  font-size: 28px; 
  margin: 6px 0; 
  color: #0efcff; 
  font-weight: bold;
}

.risk-desc { 
  font-size: 13px; 
  color: #9dcfff; 
  line-height: 1.4;
}

@media (max-width: 1200px) {
  .physiology-grid { 
    grid-template-columns: 1fr; 
  }
  
  .risk-content { 
    flex-direction: column; 
  }
  
  .disease-risk-list { 
    width: 100%; 
    flex-direction: row; 
    flex-wrap: wrap; 
  }
  
  .disease-risk-list .risk-item { 
    flex: 1 1 calc(50% - 10px); 
  }
}

@media (max-width: 768px) {
  .form-row { 
    grid-template-columns: 1fr; 
  }
  
  .disease-risk-list .risk-item { 
    flex: 1 1 100%; 
  }
  
  .chart-block {
    min-width: auto;
  }
}
</style>