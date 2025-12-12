<template>
    <div class="physio-layout">
      <div class="sub-nav">
        <div
          v-for="tab in tabs"
          :key="tab.path"
          :class="['sub-nav-item', isActive(tab.path) ? 'active' : '', 'cool-border']"
          @click="go(tab.path)"
        >
          <span>{{ tab.label }}</span>
          <div :class="[isActive(tab.path) ? 'top-left' : '', 'corner']"></div>
          <div :class="[isActive(tab.path) ? 'top-right' : '', 'corner']"></div>
          <div :class="[isActive(tab.path) ? 'bottom-left' : '', 'corner']"></div>
          <div :class="[isActive(tab.path) ? 'bottom-right' : '', 'corner']"></div>
        </div>
      </div>
      <div class="sub-content">
        <transition name="fade" mode="out-in">
          <router-view />
        </transition>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'PhysiologyLayout',
    data() {
      return {
        tabs: [
          { label: '健康总览', path: '/physiology/dashboard' },
          { label: '监测记录', path: '/physiology/metrics' },
          { label: '干预计划', path: '/physiology/plans' }
        ]
      }
    },
    methods: {
      go(path) {
        if (this.$route.path !== path) {
          this.$router.push(path)
        }
      },
      isActive(path) {
        return this.$route.path === path
      }
    }
  }
  </script>
  
  <style lang="less" scoped>
  .physio-layout {
    width: 100%;
    min-height: calc(100vh - 120px);
    display: flex;
    flex-direction: column;
    color: #cfe7ff;
  }
  .sub-nav {
    padding: 10px 0 20px;
    display: flex;
    gap: 15px;
    justify-content: center;
  }
  .sub-nav-item {
    position: relative;
    padding: 10px 45px;
    border-radius: 40px;
    background: rgba(10, 27, 58, 0.7);
    cursor: pointer;
    transition: all 0.3s;
    color: #82c5ff;
    font-weight: 600;
  }
  .sub-nav-item.active {
    background: #1b2d4a;
    color: #0efcff;
  }
  .cool-border {
    position: relative;
  }
  .corner {
    position: absolute;
    width: 0;
    height: 0;
    border: 5px solid transparent;
  }
  .top-left {
    top: 0;
    left: 0;
    border-top-color: #fff;
    border-left-color: #fff;
  }
  .top-right {
    top: 0;
    right: 0;
    border-top-color: #fff;
    border-right-color: #fff;
  }
  .bottom-left {
    bottom: 0;
    left: 0;
    border-bottom-color: #fff;
    border-left-color: #fff;
  }
  .bottom-right {
    bottom: 0;
    right: 0;
    border-bottom-color: #fff;
    border-right-color: #fff;
  }
  .sub-content {
    flex: 1;
  }
  .fade-enter-active,
  .fade-leave-active {
    transition: opacity 0.4s;
  }
  .fade-enter,
  .fade-leave-to {
    opacity: 0;
  }
  </style>
  