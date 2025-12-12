<template>
  <dv-border-box-12 class="panel nutrition-panel">
    <div class="panel-header">
      <div class="panel-title-wrap">
        <div class="panel-title">膳食营养方案</div>
        <small>每日能量 {{ plan.energy || 0 }} kcal</small>
      </div>
      <div class="panel-actions">
        <button type="button" class="ghost-btn" @click="openRecordModal">记录餐食</button>
        <button type="button" class="ghost-btn" @click="openPlanModal">调整目标</button>
        <button type="button" class="icon-btn" :disabled="loading" @click="refreshAll">
          {{ loading ? '更新中' : '刷新' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else class="nutrition-body">
      <div class="macro-chart" ref="macroChart">
        <div v-if="!hasMacroData" class="empty-macro">暂无宏量营养素数据</div>
      </div>

      <div class="meal-list">
        <div
          v-for="meal in displayMeals"
          :key="meal.name + meal.desc"
          class="meal-card"
        >
          <div class="meal-title">{{ meal.name }}</div>
          <div class="meal-desc">{{ meal.desc }}</div>
          <div class="meal-meta">{{ meal.kcal }} kcal · {{ meal.macros }}</div>
        </div>

        <div class="supplements" v-if="plan.micronutrients.length">
          重点微量营养素：{{ plan.micronutrients.join(' / ') }}
        </div>

        <div class="recommendation-panel" v-if="recommendations.length">
          <div class="recommendation-header">
            <span>个性化营养建议</span>
            <button
              type="button"
              class="link-btn"
              :disabled="recommendationLoading"
              @click="fetchRecommendations(true)"
            >
              {{ recommendationLoading ? '刷新中...' : '刷新' }}
            </button>
          </div>
          <div
            v-for="rec in recommendations"
            :key="rec.key"
            class="recommendation-card"
          >
            <div class="rec-cat">{{ rec.category }}</div>
            <div class="rec-title">{{ rec.title }}</div>
            <div class="rec-desc">{{ rec.desc }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 记录餐食 -->
    <transition name="fade">
      <div class="modal-mask" v-if="showRecordModal">
        <div class="modal-card">
          <div class="modal-header">
            <span>记录餐食</span>
            <button type="button" class="icon-btn close-btn" @click="closeRecordModal">×</button>
          </div>
          <form class="modal-body" @submit.prevent="submitMealRecord">
            <label class="form-label">
              餐食时间
              <input type="datetime-local" v-model="recordForm.meal_time">
            </label>
            <label class="form-label">
              总卡路里（kcal）
              <input type="number" min="0" v-model.number="recordForm.calories" placeholder="不填则自动计算">
            </label>

            <div class="foods-section">
              <div class="section-title">
                食物列表
                <button type="button" class="link-btn" @click="addFood">+ 添加食物</button>
              </div>
              <div v-for="(food, index) in recordForm.foods" :key="index" class="food-row">
                <input type="text" placeholder="食物名称" v-model="food.name">
                <input type="number" min="0" placeholder="卡路里" v-model.number="food.calories">
                <input type="number" min="0" placeholder="蛋白质(g)" v-model.number="food.protein">
                <input type="number" min="0" placeholder="碳水(g)" v-model.number="food.carbs">
                <input type="number" min="0" placeholder="脂肪(g)" v-model.number="food.fat">
                <button type="button" class="remove-btn" @click="removeFood(index)">×</button>
              </div>
            </div>

            <div class="form-grid">
              <label class="form-label">
                升糖负荷
                <input type="number" min="0" step="0.1" v-model.number="recordForm.glycemic_load">
              </label>
              <label class="form-label">
                饱腹感 (0-100)
                <input type="number" min="0" max="100" step="1" v-model.number="recordForm.satiety_score">
              </label>
            </div>

            <label class="form-label">
              备注 / 反馈
              <textarea rows="2" v-model="recordForm.feedback" placeholder="可记录口味、饱腹感等"></textarea>
            </label>

            <div class="modal-actions">
              <button type="button" class="ghost-btn" @click="closeRecordModal">取消</button>
              <button type="submit" class="ghost-btn primary" :disabled="savingMeal">
                {{ savingMeal ? '保存中...' : '保存' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </transition>

    <!-- 调整计划 -->
    <transition name="fade">
      <div class="modal-mask" v-if="showPlanModal">
        <div class="modal-card">
          <div class="modal-header">
            <span>调整营养目标</span>
            <button type="button" class="icon-btn close-btn" @click="closePlanModal">×</button>
          </div>
          <form class="modal-body" @submit.prevent="submitPlanUpdate">
            <label class="form-label">
              每日能量目标 (kcal)
              <input type="number" min="0" v-model.number="planForm.energy_target">
            </label>

            <div class="form-grid">
              <label class="form-label">
                碳水比例 (%)
                <input type="number" min="0" max="100" v-model.number="planForm.macro_split.carb">
              </label>
              <label class="form-label">
                蛋白质比例 (%)
                <input type="number" min="0" max="100" v-model.number="planForm.macro_split.protein">
              </label>
              <label class="form-label">
                脂肪比例 (%)
                <input type="number" min="0" max="100" v-model.number="planForm.macro_split.fat">
              </label>
            </div>

            <label class="form-label">
              饮食限制（用逗号、顿号或空格分隔）
              <input type="text" v-model="planForm.dietary_restrictions_text" placeholder="例：低盐、无糖">
            </label>

            <label class="form-label">
              备注 / 建议
              <textarea rows="3" v-model="planForm.recommendations"></textarea>
            </label>

            <div class="modal-actions">
              <button type="button" class="ghost-btn" @click="closePlanModal">取消</button>
              <button type="submit" class="ghost-btn primary" :disabled="savingPlan">
                {{ savingPlan ? '保存中...' : '保存' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </transition>
  </dv-border-box-12>
</template>

<script>
import {
  getNutritionPlan,
  recordMeal,
  updateNutritionPlan,
  getNutritionRecommendations
} from '@/api/nutrition';
import * as echarts from 'echarts';

const padZero = (num) => (num < 10 ? `0${num}` : `${num}`);
const formatDatetimeLocal = (date = new Date()) => {
  const year = date.getFullYear();
  const month = padZero(date.getMonth() + 1);
  const day = padZero(date.getDate());
  const hour = padZero(date.getHours());
  const minute = padZero(date.getMinutes());
  return `${year}-${month}-${day}T${hour}:${minute}`;
};
const createFoodRow = () => ({
  name: '',
  calories: '',
  protein: '',
  carbs: '',
  fat: ''
});
const createMealForm = () => ({
  meal_time: formatDatetimeLocal(),
  calories: '',
  glycemic_load: '',
  satiety_score: '',
  feedback: '',
  foods: [createFoodRow()]
});
const createPlanForm = () => ({
  energy_target: '',
  macro_split: { carb: 50, protein: 25, fat: 25 },
  dietary_restrictions_text: '',
  recommendations: ''
});
const createPlanState = () => ({
  energy: 0,
  macros: { carb: 0, protein: 0, fat: 0 },
  meals: [],
  micronutrients: [],
  dietary_restrictions: [],
  recommendations: ''
});

export default {
  name: 'NutritionPlan',
  data() {
    return {
      loading: false,
      error: '',
      plan: createPlanState(),
      recommendations: [],
      recommendationLoading: false,
      chart: null,
      showRecordModal: false,
      showPlanModal: false,
      savingMeal: false,
      savingPlan: false,
      recordForm: createMealForm(),
      planForm: createPlanForm()
    };
  },
  computed: {
    hasMacroData() {
      const macros = this.plan.macros || {};
      return (macros.carb || 0) + (macros.protein || 0) + (macros.fat || 0) > 0;
    },
    displayMeals() {
      return this.plan.meals && this.plan.meals.length
        ? this.plan.meals
        : this.buildSampleMeals();
    }
  },
  watch: {
    'plan.macros': {
      deep: true,
      handler() {
        this.$nextTick(() => this.initChart());
      }
    }
  },
  mounted() {
    this.refreshAll();
    window.addEventListener('resize', this.handleResize);
  },
  beforeDestroy() {
    this.disposeChart();
    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    async refreshAll() {
      await this.fetchNutritionPlan();
      this.fetchRecommendations();
    },
    async fetchNutritionPlan() {
      this.loading = true;
      this.error = '';
      try {
        const res = await getNutritionPlan();
        this.plan = this.normalizePlan(res);
        this.planForm = this.buildPlanFormFromPlan();
      } catch (err) {
        this.error = err?.message || '获取营养计划失败';
      } finally {
        this.loading = false;
        this.$nextTick(() => this.initChart());
      }
    },
    async fetchRecommendations(force = false) {
      if (this.recommendations.length && !force) return;
      this.recommendationLoading = true;
      try {
        const res = await getNutritionRecommendations();
        const list = res?.recommendations || [];
        this.recommendations = list.slice(0, 4).map((item, index) => ({
          key: `${item.title || item.category || 'rec'}-${index}`,
          category: item.category || '建议',
          title: item.title || '营养建议',
          desc: item.desc || ''
        }));
      } catch (err) {
        this.notify(err?.message || '获取营养建议失败', 'error');
      } finally {
        this.recommendationLoading = false;
      }
    },
    normalizePlan(raw = {}) {
      let macros = raw.macros || raw.macro_split || {};
      if (typeof macros === 'string') {
        try {
          macros = JSON.parse(macros);
        } catch (err) {
          macros = {};
        }
      }
      return {
        energy: raw.energy || raw.energy_target_kcal || 0,
        macros: {
          carb: Number(macros.carb) || 0,
          protein: Number(macros.protein) || 0,
          fat: Number(macros.fat) || 0
        },
        meals: Array.isArray(raw.meals) ? raw.meals : [],
        micronutrients: Array.isArray(raw.micronutrients) ? raw.micronutrients : [],
        dietary_restrictions: Array.isArray(raw.dietary_restrictions)
          ? raw.dietary_restrictions
          : [],
        recommendations: raw.recommendations || ''
      };
    },
    buildPlanFormFromPlan() {
      const form = createPlanForm();
      form.energy_target = this.plan.energy || '';
      form.macro_split = {
        carb: this.plan.macros.carb || 0,
        protein: this.plan.macros.protein || 0,
        fat: this.plan.macros.fat || 0
      };
      form.dietary_restrictions_text = (this.plan.dietary_restrictions || []).join('、');
      form.recommendations = this.plan.recommendations || '';
      return form;
    },
    openRecordModal() {
      this.recordForm = createMealForm();
      this.showRecordModal = true;
    },
    closeRecordModal() {
      this.showRecordModal = false;
      this.recordForm = createMealForm();
    },
    openPlanModal() {
      this.planForm = this.buildPlanFormFromPlan();
      this.showPlanModal = true;
       },
    closePlanModal() {
      this.showPlanModal = false;
      this.planForm = this.buildPlanFormFromPlan();
    },
    addFood() {
      this.recordForm.foods.push(createFoodRow());
    },
    removeFood(index) {
      if (this.recordForm.foods.length === 1) {
        this.recordForm.foods = [createFoodRow()];
      } else {
        this.recordForm.foods.splice(index, 1);
      }
    },
    sanitizeFoods() {
      return this.recordForm.foods
        .map((food) => ({
          name: (food.name || '').trim(),
          calories: food.calories !== '' ? Number(food.calories) : undefined,
          protein: food.protein !== '' ? Number(food.protein) : undefined,
          carbs: food.carbs !== '' ? Number(food.carbs) : undefined,
          fat: food.fat !== '' ? Number(food.fat) : undefined
        }))
        .filter(
          (food) =>
            food.name ||
            food.calories ||
            food.protein ||
            food.carbs ||
            food.fat
        );
    },
    aggregateMacros(foods) {
      const totals = { protein: 0, carbs: 0, fat: 0 };
      foods.forEach((food) => {
        totals.protein += Number(food.protein) || 0;
        totals.carbs += Number(food.carbs) || 0;
        totals.fat += Number(food.fat) || 0;
      });
      return totals;
    },
    calculateCalories(foods) {
      return foods.reduce((sum, food) => {
        if (food.calories) {
          return sum + Number(food.calories);
        }
        const macrosCalories =
          ((Number(food.protein) || 0) + (Number(food.carbs) || 0)) * 4 +
          (Number(food.fat) || 0) * 9;
        return sum + macrosCalories;
      }, 0);
    },
    normalizeMealTime(value) {
      if (!value) return this.formatDateTime(new Date());
      if (value.includes('T')) {
        return value.replace('T', ' ').slice(0, 16);
      }
      return value;
    },
    async submitMealRecord() {
      const foods = this.sanitizeFoods();
      if (!foods.length && !this.recordForm.calories) {
        this.notify('请至少填写一个食物或总卡路里', 'warning');
        return;
      }
      const macros = this.aggregateMacros(foods);
      const payload = {
        meal_time: this.normalizeMealTime(this.recordForm.meal_time),
        foods,
        calories:
          Number(this.recordForm.calories) ||
          this.calculateCalories(foods) ||
          0,
        macros:
          macros.protein || macros.carbs || macros.fat ? macros : undefined,
        glycemic_load: this.recordForm.glycemic_load || undefined,
        satiety_score: this.recordForm.satiety_score || undefined,
        feedback: this.recordForm.feedback || undefined
      };
      this.savingMeal = true;
      try {
        await recordMeal(payload);
        this.notify('餐食记录已保存');
        this.closeRecordModal();
        this.fetchNutritionPlan();
      } catch (err) {
        this.notify(err?.message || '记录餐食失败', 'error');
      } finally {
        this.savingMeal = false;
      }
    },
    async submitPlanUpdate() {
      const macros = this.planForm.macro_split;
      const macroPayload = {
        carb: Number(macros.carb) || 0,
        protein: Number(macros.protein) || 0,
        fat: Number(macros.fat) || 0
      };
      const sum = macroPayload.carb + macroPayload.protein + macroPayload.fat;
      if (sum && (sum < 95 || sum > 105)) {
        this.notify('宏量营养素比例之和建议接近 100%', 'warning');
        return;
      }
      const payload = {
        energy_target: Number(this.planForm.energy_target) || 0,
        macro_split: macroPayload,
        dietary_restrictions: this.planForm.dietary_restrictions_text
          ? this.planForm.dietary_restrictions_text
              .split(/[,，、\s]/)
              .map((item) => item.trim())
              .filter(Boolean)
          : [],
        recommendations: this.planForm.recommendations || undefined
      };
      this.savingPlan = true;
      try {
        await updateNutritionPlan(payload);
        this.notify('营养计划已更新');
        this.closePlanModal();
        this.fetchNutritionPlan();
      } catch (err) {
        this.notify(err?.message || '更新营养计划失败', 'error');
      } finally {
        this.savingPlan = false;
      }
    },
    buildSampleMeals() {
      return [
        { name: '早餐', desc: '全麦面包 + 鸡蛋 + 酸奶', kcal: 430, macros: 'C45/P25/F30' },
        { name: '午餐', desc: '糙米饭 + 蒸鱼 + 蔬菜', kcal: 520, macros: 'C50/P30/F20' },
        { name: '晚餐', desc: '鸡胸肉 + 西蓝花 + 薯类', kcal: 480, macros: 'C40/P35/F25' }
      ];
    },
    initChart() {
  if (!this.$refs.macroChart) return;  // 如果ref不存在，直接返回（防止错误）

  if (!this.chart) {
    this.chart = echarts.init(this.$refs.macroChart);
  }

  let macros = this.plan.macros || { carb: 0, protein: 0, fat: 0 };  // 确保macros存在

  // 如果数据全0，使用默认值绘制（可选，避免空图）
  if (!this.hasMacroData) {
    macros = { carb: 50, protein: 25, fat: 25 };  // 默认比例，防止空饼图
    // 或者不改macros，让它绘制空图，并依赖<template>中的提示文本
  }

  this.chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
    legend: {
      orient: 'vertical',
      right: 0,
      top: 'center',
      textStyle: { color: '#cfe7ff' }
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['40%', '50%'],
        data: [
          { value: macros.carb || 0, name: '碳水' },
          { value: macros.protein || 0, name: '蛋白质' },
          { value: macros.fat || 0, name: '脂肪' }
        ],
        label: { color: '#fff', formatter: '{b}\n{d}%' },
        itemStyle: { borderColor: '#020a2b', borderWidth: 2 }
      }
    ]
  });
},

    disposeChart() {
      if (this.chart) {
        this.chart.dispose();
        this.chart = null;
      }
    },
    handleResize() {
      if (this.chart) {
        this.chart.resize();
      }
    },
    formatDateTime(date = new Date()) {
      const year = date.getFullYear();
      const month = padZero(date.getMonth() + 1);
      const day = padZero(date.getDate());
      const hour = padZero(date.getHours());
      const minute = padZero(date.getMinutes());
      return `${year}-${month}-${day} ${hour}:${minute}`;
    },
    notify(message, type = 'success') {
      if (this.$message && typeof this.$message[type] === 'function') {
        this.$message[type](message);
      } else if (type === 'error') {
        console.error(message);
      } else {
        console.log(message);
      }
    }
  }
};
</script>

<style lang="less" scoped>
.panel {
  padding: 15px;
  box-sizing: border-box;
  min-height: 300px;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.panel-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.panel-title {
  font-size: 18px;
  font-weight: bold;
}
.panel-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.ghost-btn,
.icon-btn,
.link-btn,
.remove-btn {
  cursor: pointer;
  border: none;
  outline: none;
}
.ghost-btn {
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(110, 161, 255, 0.4);
  background: rgba(110, 161, 255, 0.12);
  color: #cfe7ff;
  transition: all 0.2s ease;
}
.ghost-btn.primary {
  background: linear-gradient(90deg, #3d8bff, #6ecbff);
  color: #041028;
  border-color: transparent;
}
.ghost-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.icon-btn {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(110, 161, 255, 0.25);
  background: rgba(15, 45, 84, 0.4);
  color: #cfe7ff;
}
.link-btn {
  background: transparent;
  color: #6ea1ff;
  font-size: 12px;
}
.loading,
.error {
  text-align: center;
  padding: 40px 0;
  color: #cfe7ff;
}
.error {
  color: #ff6b6b;
}
.nutrition-body {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}
.macro-chart {
  width: 240px;
  height: 240px;
  position: relative;
}
.empty-macro {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #5e7499;
  font-size: 13px;
}
.meal-list {
  flex: 1;
  min-width: 220px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.meal-card {
  padding: 10px;
  border-radius: 12px;
  background: rgba(16, 45, 80, 0.55);
}
.meal-title {
  font-weight: bold;
  margin-bottom: 4px;
}
.meal-desc {
  font-size: 13px;
  margin-bottom: 4px;
  color: #d7e5ff;
}
.meal-meta {
  font-size: 12px;
  color: #8fb5ff;
}
.supplements {
  font-size: 12px;
  color: #6ea1ff;
}
.recommendation-panel {
  margin-top: 4px;
  padding: 10px;
  border-radius: 12px;
  background: rgba(16, 45, 80, 0.35);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #cfe7ff;
}
.recommendation-card {
  padding: 8px;
  border-radius: 10px;
  background: rgba(8, 24, 50, 0.6);
}
.rec-cat {
  font-size: 11px;
  color: #6ecbff;
}
.rec-title {
  font-weight: bold;
  margin: 2px 0;
}
.rec-desc {
  font-size: 12px;
  line-height: 1.4;
  color: #bcd0f6;
}
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.modal-card {
  width: 420px;
  background: rgba(4, 16, 44, 0.95);
  border: 1px solid rgba(110, 161, 255, 0.3);
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
  padding: 18px;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  color: #cfe7ff;
  font-size: 16px;
}
.close-btn {
  font-size: 18px;
  padding: 2px 6px;
  background: transparent;
  border: none;
  color: #cfe7ff;
}
.modal-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.form-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #9fb6d6;
}
.form-label input,
.form-label textarea {
  border-radius: 8px;
  border: 1px solid rgba(110, 161, 255, 0.4);
  background: rgba(8, 22, 46, 0.9);
  color: #cfe7ff;
  padding: 6px 10px;
  font-size: 13px;
  outline: none;
}
.form-label textarea {
  resize: none;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
}
.foods-section {
  border-radius: 10px;
  border: 1px solid rgba(110, 161, 255, 0.25);
  padding: 8px;
  background: rgba(8, 23, 52, 0.6);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #cfe7ff;
}
.food-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(50px, 1fr)) 28px;
  gap: 6px;
}
.food-row input {
  width: 100%;
  border-radius: 6px;
  border: 1px solid rgba(110, 161, 255, 0.25);
  background: rgba(4, 16, 44, 0.85);
  color: #cfe7ff;
  padding: 4px 6px;
  font-size: 12px;
}
.remove-btn {
  border-radius: 6px;
  background: rgba(255, 107, 107, 0.2);
  color: #ff8f8f;
  font-size: 16px;
  line-height: 1;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}
</style>
