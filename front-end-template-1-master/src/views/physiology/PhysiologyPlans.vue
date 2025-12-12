<template>
  <div class="plans-page">
    <transition name="fade" mode="out-in">
      <dv-loading v-if="loading">Loading...</dv-loading>
      <div v-else class="plans-content">
        <div class="plans-tabs">
          <div
            v-for="tab in planTabs"
            :key="tab.value"
            :class="['plans-tab', { active: activeTab === tab.value }]"
            @click="setTab(tab.value)"
          >
            {{ tab.label }}
          </div>
        </div>

        <WorkoutPlan v-show="activeTab === 'workout'" :plan="plans.workout" />
        <ChronobiologyPlan v-show="activeTab === 'chronobiology'" :plan="plans.chronobiology" />
        <NutritionPlan v-show="activeTab === 'nutrition'" :plan="plans.nutrition" />
        <!-- ✅ 添加事件监听 @ask-question -->
        <AiCoachPlan 
          v-show="activeTab === 'ai'" 
          :coach-list="plans.aiCoach"
          @ask-question="handleAiQuestion"
        />
      </div>
    </transition>
  </div>
</template>

<script>
import WorkoutPlan from './components/WorkoutPlan.vue';
import ChronobiologyPlan from './components/ChronobiologyPlan.vue';
import NutritionPlan from './components/NutritionPlan.vue';
import AiCoachPlan from './components/AiCoachPlan.vue';

const mockPlans = {
  workout: {
    goal: '12 周降压 + 心肺耐力综合提升',
    progress: 58,
    phases: [
      { name: '第 1-4 周 · 适应期', duration: '4 周', target: '最大心率 60-70%', desc: '低冲击有氧 + 核心稳定性训练' },
      { name: '第 5-8 周 · 发展期', duration: '4 周', target: '最大心率 70-80%', desc: '间歇跑 + 力量循环' },
      { name: '第 9-12 周 · 巩固期', duration: '4 周', target: '最大心率 65-75%', desc: '多样化混合训练 + 主动恢复' }
    ],
    sessions: [
      { id: 'w1', name: '低冲击有氧', date: '周一', status: '完成', heartZone: '60%', rpe: 5 },
      { id: 'w2', name: '力量循环', date: '周三', status: '完成', heartZone: '70%', rpe: 7 },
      { id: 'w3', name: 'HIIT 间歇', date: '周五', status: '计划', heartZone: '80%', rpe: 8 }
    ]
  },
  nutrition: {
    energy: 1800,
    macros: { carb: 45, protein: 30, fat: 25 },
    micronutrients: ['钾', '镁', '辅酶 Q10', '维生素 D'],
    meals: [
      { name: '早餐', desc: '牛油果全麦吐司 + 鸡蛋 + 低脂奶', kcal: 430, macros: 'C45/P25/F30' },
      { name: '午餐', desc: '清蒸鱼 + 藜麦彩蔬', kcal: 520, macros: 'C40/P35/F25' },
      { name: '晚餐', desc: '鸡胸肉 + 西蓝花 + 糙米', kcal: 480, macros: 'C35/P40/F25' }
    ]
  },
  chronobiology: {
    target: '23:00 - 07:00',
    tip: '21:30 关闭蓝光，睡前 30 分钟冥想 + 伸展。',
    schedule: [
      { day: '周一', sleep: '22:45', wake: '06:50', adherence: 92, note: '保持良好' },
      { day: '周二', sleep: '23:30', wake: '06:40', adherence: 70, note: '加班延迟' },
      { day: '周三', sleep: '23:05', wake: '06:55', adherence: 86, note: '建议提前' },
      { day: '周四', sleep: '22:40', wake: '06:35', adherence: 95, note: '接近理想' },
      { day: '周五', sleep: '00:10', wake: '07:30', adherence: 60, note: '周末拖延' }
    ],
    sleepTrend: {
      nights: ['周一', '周二', '周三', '周四', '周五'],
      quality: [82, 74, 79, 88, 91],
      efficiency: [88, 80, 83, 92, 93]
    }
  },
  aiCoach: [
    { id: 'c1', tag: '心率变异', title: '晚间 HRV 下滑 12%', desc: '建议今天训练强度保持在 Zone2，训练后补充富镁食物。', time: '今天 08:00' },
    { id: 'c2', tag: '能量补给', title: '早餐碳水偏低', desc: '建议增加 30g 复合碳水，搭配 20g 优质蛋白。', time: '今天 07:30' },
    { id: 'c3', tag: '睡眠修复', title: '深睡比例下降', desc: '尝试在 22:30 前进入睡前流程,配合 10 分钟冥想。', time: '昨天 22:00' }
  ]
};

export default {
  name: 'PhysiologyPlans',
  components: {
    WorkoutPlan,
    ChronobiologyPlan,
    NutritionPlan,
    AiCoachPlan
  },
  data() {
    return {
      loading: true,
      planTabs: [
        { label: '运动干预计划', value: 'workout' },
        { label: '生物钟调节计划', value: 'chronobiology' },
        { label: '膳食营养', value: 'nutrition' },
        { label: 'AI 问答助手', value: 'ai' }
      ],
      activeTab: 'workout',
      plans: {
        workout: { goal: '', progress: 0, phases: [], sessions: [] },
        nutrition: { energy: 0, macros: {}, meals: [], micronutrients: [] },
        chronobiology: { target: '', tip: '', schedule: [], sleepTrend: { nights: [], quality: [], efficiency: [] } },
        aiCoach: []
      }
    };
  },
  created() {
    this.fetchPlans();
  },
  methods: {
    setTab(value) {
      if (this.activeTab !== value) {
        this.activeTab = value;
      }
    },
    async fetchPlans() {
      try {
        const { data } = await this.$http.get('/physiology/plans');
        this.consumePayload(data);
      } catch (error) {
        console.warn('[PhysiologyPlans] 使用 mock 数据', error);
        this.consumePayload(mockPlans);
      } finally {
        this.loading = false;
      }
    },
    consumePayload(payload) {
      this.plans.workout = payload.workout || this.plans.workout;
      this.plans.nutrition = payload.nutrition || this.plans.nutrition;
      this.plans.chronobiology = payload.chronobiology || this.plans.chronobiology;
      this.plans.aiCoach = payload.aiCoach || [];
    },
    
    // ✅ 处理AI问答的回复
 // ✅ 处理AI问答的回复
handleAiQuestion(data) {
  console.log('📩 收到AI回复:', data);
  
  const now = new Date();
  const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
  
  if (data.loading) {
    // ✅ 用户提问时：添加临时消息
    this.plans.aiCoach.unshift({
      id: `temp-${Date.now()}`,
      tag: '医学助手',
      title: data.question,
      desc: data.answer,
      time: timeStr,
      isTemp: true
    });
  } else {
    // ✅ AI回复时：找到临时消息的索引
    const tempIndex = this.plans.aiCoach.findIndex(msg => msg.isTemp);
    
    if (tempIndex !== -1) {
      // ✅ 使用 $set 替换整个对象（关键修复！）
      this.$set(this.plans.aiCoach, tempIndex, {
        id: `ai-${Date.now()}`,
        tag: data.error ? '❌ 错误' : '✅ 医学助手',
        title: data.question,
        desc: data.answer,
        time: timeStr,
        isTemp: false
      });
    } else {
      // 没找到临时消息，直接添加
      this.plans.aiCoach.unshift({
        id: `ai-${Date.now()}`,
        tag: data.error ? '❌ 错误' : '✅ 医学助手',
        title: data.question,
        desc: data.answer,
        time: timeStr
      });
    }
  }
  
  // 限制消息数量
  if (this.plans.aiCoach.length > 20) {
    this.plans.aiCoach = this.plans.aiCoach.slice(0, 20);
  }
  
  // ✅ 强制刷新视图（双重保险）
  this.$forceUpdate();
}

  }
};
</script>

<style lang="less" scoped>
.plans-page {
  width: 100%;
  min-height: calc(100vh - 120px);
  color: #cfe7ff;
}
.plans-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.plans-tabs {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 15px;
  padding: 5px 0 10px;
}
.plans-tab {
  padding: 10px 32px;
  border-radius: 40px;
  background: rgba(10, 27, 58, 0.7);
  cursor: pointer;
  transition: all 0.3s;
  color: #82c5ff;
  font-weight: 600;
}
.plans-tab.active {
  background: #1b2d4a;
  color: #0efcff;
  box-shadow: 0 0 15px rgba(14, 252, 255, 0.35);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}
</style>
