<template>
    <div id="header">
      <div class="header-wrapper">
        <div id="header-left">
          <h1>健康系统</h1>
        </div>
        
        <!-- 已登录时显示：导航链接 + 用户名 + 退出按钮 -->
        <div class="nav-user-container" v-if="isLogin">
          <div id="header-nav">
            <div 
              :class="['header-nav-item', activePath === item.path ? 'active' : '', 'cool-border']" 
              @click="routerChange(item.path)" 
              v-for="item in validRouterLinks"
              :key="item.path"
            >
              <router-link class="nav content" :to="item.path">
                {{ item.meta.name }}
              </router-link>
              <div :class="[activePath === item.path ? 'top-left' : '', 'corner']"></div>
              <div :class="[activePath === item.path ? 'top-right' : '', 'corner']"></div>
              <div :class="[activePath === item.path ? 'bottom-left' : '', 'corner']"></div>
              <div :class="[activePath === item.path ? 'bottom-right' : '', 'corner']"></div>
            </div>
          </div>
          
          <!-- 用户名 + 退出登录按钮 -->
          <div class="user-operation">
            <span class="username">{{ username }}</span>
            <button class="logout-btn" @click="handleLogout">退出登录</button>
          </div>
        </div>
        
        <div id="header-time">
          {{ currentDateTime }}
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { isAuthenticated, getUser, logout, getToken } from '@/utils/auth';
  
  export default {
    name: 'Header',
    data() {
      return {
        activePath: '/index',
        routerLink: [],
        currentDateTime: this.getCurrentDateTime(),
        isLogin: false,
        username: ''
      };
    },
    created() {
      this.routerLink = this.$router.options.routes;
      this.activePath = this.$route.path;
      this.updateLoginStatus();
  
      this.interval = setInterval(() => {
        this.currentDateTime = this.getCurrentDateTime();
      }, 1000);
  
      this.$router.afterEach((to) => {
        this.activePath = to.path;
        this.updateLoginStatus(); // 路由变化时重新校验登录状态
      });
    },
    beforeDestroy() {
      clearInterval(this.interval);
    },
    computed: {
      validRouterLinks() {
        return this.routerLink.filter(item => {
          return item.meta?.requiresAuth && item.meta?.name;
        });
      }
    },
    methods: {
      getCurrentDateTime() {
        const now = new Date();
        const year = now.getFullYear();
        const month = (now.getMonth() + 1).toString().padStart(2, '0');
        const day = now.getDate().toString().padStart(2, '0');
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const seconds = now.getSeconds().toString().padStart(2, '0');
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
      },
      routerChange(path) {
        this.activePath = path;
        this.$router.push(path);
      },
      updateLoginStatus() {
        // 强制重新获取登录状态（避免缓存）
        const token = getToken();
        this.isLogin = !!token;
        if (this.isLogin) {
          const user = getUser();
          this.username = user?.username || '用户';
        } else {
          this.username = '';
          this.activePath = '/auth/login';
        }
        console.log('登录状态更新：', this.isLogin, 'Token：', token); // 调试用
      },
      // 修复后的退出登录逻辑（关键）
      handleLogout() {
        if (confirm('确定要退出登录吗？')) {
          try {
            // 1. 清除本地存储（Token + 用户信息）
            logout();
            console.log('退出登录：已清除本地存储');
  
            // 2. 强制更新登录状态（立即隐藏导航栏）
            this.updateLoginStatus();
  
            // 3. 跳转到登录页，并且清除路由历史（防止回退）
            this.$router.replace({
              path: '/auth/login',
              query: { logout: 'true' } // 标记是退出登录跳转
            });
  
            // 4. 提示成功
            this.$message.success('退出登录成功！');
  
          } catch (error) {
            console.error('退出登录失败：', error);
            this.$message.error('退出登录失败，请重试');
          }
        }
      }
    },
    watch: {
      // 监听 isLogin 变化，确保状态同步
      isLogin(newVal) {
        console.log('登录状态变化：', newVal);
        if (!newVal) {
          // 未登录时，确保导航栏隐藏
          this.activePath = '/auth/login';
        }
      },
      $route() {
        this.updateLoginStatus();
      }
    }
  };
  </script>
  
  <style lang="less" scoped>
  #header {
    width: 100%;
    background: rgba(2, 10, 43, 0.8);
    backdrop-filter: blur(5px);
    border-bottom: 1px solid rgba(48, 119, 177, 0.5);
  
    .header-wrapper {
      display: flex;
      padding: 10px 50px 15px;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 15px;
    }
  
    #header-left {
      h1 {
        color: #fff;
        font-size: 23px;
        margin: 0;
        font-weight: 600;
      }
    }
  
    .nav-user-container {
      display: flex;
      align-items: center;
      gap: 25px;
    }
  
    #header-nav {
      display: flex;
      margin: 5px 0;
  
      .header-nav-item {
        margin-right: 15px;
        padding: 10px 25px;
        border: 1px solid transparent;
        border-radius: 80px;
        cursor: pointer;
        transition: all 0.3s ease;
  
        &:last-child {
          margin-right: 0;
        }
  
        &:hover {
          border-color: rgba(82, 162, 228, 0.5);
          background: rgba(27, 45, 74, 0.5);
        }
  
        &.active {
          background: #1b2d4a;
          border-color: #52a2e4;
        }
      }
  
      .nav {
        text-decoration: none;
        color: #52a2e4;
        font-size: 15px;
        transition: color 0.3s ease;
  
        .header-nav-item.active & {
          color: #fff;
        }
      }
    }
  
    .user-operation {
      display: flex;
      align-items: center;
      gap: 15px;
  
      .username {
        color: #2af7ff;
        font-size: 16px;
        font-weight: 500;
      }
  
      .logout-btn {
        padding: 6px 20px;
        border: none;
        border-radius: 20px;
        background: linear-gradient(90deg, #ff6b6b, #ff8e8e);
        color: #fff;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.3s ease;
  
        &:hover {
          opacity: 0.9;
          transform: scale(1.05);
        }
  
        &:active {
          transform: scale(0.98);
        }
      }
    }
  
    #header-time {
      color: #52a2e4;
      font-size: 17px;
      font-family: 'Microsoft YaHei', sans-serif;
    }
  
    @media (max-width: 992px) {
      .header-wrapper {
        padding: 10px 20px 15px;
      }
  
      #header-left h1 {
        font-size: 20px;
      }
  
      .nav-user-container {
        flex-direction: column;
        gap: 10px;
        width: 100%;
      }
  
      #header-nav {
        justify-content: center;
        width: 100%;
  
        .header-nav-item {
          padding: 8px 20px;
          margin-right: 10px;
        }
      }
  
      .user-operation {
        gap: 20px;
      }
  
      #header-time {
        width: 100%;
        text-align: center;
        margin-top: 5px;
      }
    }
  
    @media (max-width: 576px) {
      #header-nav {
        flex-wrap: wrap;
        gap: 8px;
  
        .header-nav-item {
          margin-right: 0;
          padding: 6px 15px;
          font-size: 14px;
        }
      }
  
      .user-operation {
        flex-direction: column;
        gap: 8px;
      }
    }
  }
  
  .cool-border {
    position: relative;
  }
  
  .corner {
    position: absolute;
    width: 0;
    height: 0;
    border: 5px solid transparent;
    transition: all 0.3s ease;
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
  
  .content {
    display: flex;
    justify-content: center;
    align-items: center;
  }
  </style>