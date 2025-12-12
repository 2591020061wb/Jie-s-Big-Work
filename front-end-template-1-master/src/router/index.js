import Vue from 'vue'
import VueRouter from 'vue-router'
import { isAuthenticated } from '@/utils/auth'

Vue.use(VueRouter)

const routes = [
  // 🔥 关键修改：根路径重定向到登录页
  {
    path: '/',
    redirect: '/auth/login'  // 直接重定向到登录页
  },
  {
    path: '/index',
    name: 'Index',
    component: () => import('@/views/Index.vue'),
    meta: { name: '病情概况', requiresAuth: true }
  },
  {
    path: '/pred',
    name: 'Pred',
    component: () => import('@/views/Pred.vue'),
    meta: { name: '在线预测', requiresAuth: true }
  },
  {
    path: '/tableData',
    name: 'TableData',
    component: () => import('@/views/TableData.vue'),
    meta: { name: '数据分析', requiresAuth: true }
  },
  {
    path: '/physiology',
    component: () => import('@/views/physiology/PhysiologyLayout.vue'),
    meta: { name: '生理健康', requiresAuth: true },
    redirect: '/physiology/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'PhysiologyDashboard',
        component: () => import('@/views/physiology/PhysiologyDashboard.vue'),
        meta: { name: '健康总览' }
      },
      {
        path: 'metrics',
        name: 'PhysiologyMetrics',
        component: () => import('@/views/physiology/PhysiologyMetrics.vue'),
        meta: { name: '监测记录' }
      },
      {
        path: 'plans',
        name: 'PhysiologyPlans',
        component: () => import('@/views/physiology/PhysiologyPlans.vue'),
        meta: { name: '干预计划' }
      }
    ]
  },
  {
    path: '/mental',
    component: () => import('@/views/mental/MentalLayout.vue'), // 心理健康的布局组件
    meta: { name: '心理健康', requiresAuth: true },
    redirect: '/mental',
    children: [
      {
        path: '',
        name: 'MentalHealth',
        component: () => import('@/views/mental/MentalHealth.vue'),
        meta: { name: '心理健康总览' }
      },
      {
        path: 'emotion',
        name: 'EmotionRecord',
        component: () => import('@/views/mental/EmotionRecord.vue'),
        meta: { name: '情绪记录' }
      },
      {
        path: 'assessment',
        name: 'PsychologicalTest',
        component: () => import('@/views/mental/PsychologicalTest.vue'),
        meta: { name: '心理测评' }
      },
      {
        path: 'ai',
        name: 'AICompanion',
        component: () => import('@/views/mental/AICompanion.vue'),
        meta: { name: 'AI陪伴' }
      },
      {
        path: 'growth',
        name: 'GrowthPlan',
        component: () => import('@/views/mental/GrowthPlan.vue'),
        meta: { name: '成长计划' }
      }
    ]
  },
  // 👇 核心修改：给可视化路由补全meta配置
  {
    path: '/articles',
    name: 'ArticleHub',
    component: () => import('@/views/ArticleHub.vue'),
    meta: { name: '健康文章', requiresAuth: true }
  },

  // 登录注册路由
  {
    path: '/auth',
    component: { render: (h) => h('router-view') },
    children: [
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/auth/Login.vue'),
        meta: { isAuthPage: true }  // 标记为认证页面
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('@/views/auth/Register.vue'),
        meta: { isAuthPage: true }  // 标记为认证页面
      }
    ]
  },
  {
    path: '*',
    redirect: '/auth/login'  // 404也重定向到登录页
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/profile/ProfilePage.vue'),
    meta: { name: '个人中心', requiresAuth: true }
  },
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

// 全局前置守卫（无需修改）
router.beforeEach((to, from, next) => {
  console.log('🔍 路由守卫 - 前往:', to.path, '| 已登录:', isAuthenticated())
  
  // 1. 如果是认证页面（登录/注册）
  if (to.matched.some(record => record.meta.isAuthPage)) {
    // 已登录的用户，不允许再访问登录/注册页，直接跳转到首页
    if (isAuthenticated()) {
      console.log('✅ 已登录，跳转到首页')
      next('/index'); // 已登录则强制跳首页
      return;
    }
    // 未登录，允许访问登录/注册页
    next();
    return;
  }
  
  // 2. 检查需要认证的路由
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (isAuthenticated()) {
      console.log('✅ 用户已认证，允许访问')
      next();
    } else {
      console.log('❌ 用户未认证，跳转到登录页')
      next({
        path: '/auth/login',
        query: { redirect: to.fullPath } // 记录目标页面，登录后跳转
      });
    }
  } else {
    // 3. 其他页面（如根路径）
    next();
  }
});

export default router