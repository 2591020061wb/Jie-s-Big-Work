<!-- src/views/mental/MentalLayout.vue -->
<template>
    <div class="mental-layout">
      <!-- 心理健康子导航 -->
      <div class="sub-nav">
        <router-link 
          :to="item.path" 
          v-for="item in subNavItems" 
          :key="item.path"
          :class="['sub-nav-item', { active: isActive(item.path) }]"
        >
          {{ item.name }}
        </router-link>
      </div>
      
      <!-- 内容区域 -->
      <div class="content-container">
        <router-view />
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'MentalLayout',
    data() {
      return {
        subNavItems: [
          { path: '/mental', name: '心理健康总览' },
          { path: '/mental/emotion', name: '情绪记录' },
          { path: '/mental/assessment', name: '心理测评' },
          { path: '/mental/ai', name: 'AI陪伴' },
          { path: '/mental/growth', name: '成长计划' }
        ]
      }
    },
    methods: {
      isActive(path) {
        if (path === '/mental') {
          return this.$route.path === '/mental'
        }
        return this.$route.path.startsWith(path)
      }
    }
  }
  </script>
  
  <style lang="less" scoped>
  .mental-layout {
    min-height: calc(100vh - 100px);
    padding: 20px;
    background: transparent;
  }
  
  .sub-nav {
    display: flex;
    justify-content: center;
    gap: 15px;
    margin-bottom: 30px;
    padding: 10px 0;
    border-bottom: 1px solid rgba(82, 162, 228, 0.3);
  }
  
  .sub-nav-item {
    padding: 10px 25px;
    border-radius: 30px;
    color: #52a2e4;
    text-decoration: none;
    font-size: 15px;
    transition: all 0.3s ease;
    border: 1px solid transparent;
    
    &:hover {
      border-color: rgba(82, 162, 228, 0.5);
      background: rgba(27, 45, 74, 0.3);
    }
    
    &.active {
      background: #1b2d4a;
      border-color: #52a2e4;
      color: #fff;
    }
  }
  
  .content-container {
    min-height: 500px;
  }
  </style>