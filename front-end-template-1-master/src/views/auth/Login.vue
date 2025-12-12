<template>
    <div class="auth-page">
      <dv-border-box-12 class="auth-card">
        <h2>用户登录</h2>
        <form class="auth-form" @submit.prevent="handleLogin">
          <label>
            用户名
            <input v-model.trim="form.username" autocomplete="username" required />
          </label>
          <label>
            密码
            <input v-model.trim="form.password" type="password" autocomplete="current-password" required />
          </label>
          <button type="submit" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>
        <p class="switch">
          没有帐号？
          <router-link to="/auth/register">去注册</router-link>
        </p>
      </dv-border-box-12>
    </div>
  </template>
  
  <script>
  import { setToken, setUser } from '@/utils/auth';
  
  export default {
    name: 'Login',
    data() {
      return {
        loading: false,
        form: { username: '', password: '' }
      };
    },
    methods: {
      // Login.vue - 修改登录方法
async handleLogin() {
  if (!this.form.username || !this.form.password) {
    alert('请输入用户名和密码');
    return;
  }
  this.loading = true;
  try {
    console.log('🔑 开始登录...');
    
    // 关键修改：用 this.$http（根据你之前的代码，你使用的是axios实例）
    const response = await this.$http.post('/api/auth/login', this.form);
    console.log('✅ 登录响应:', response); // response已经经过拦截器处理，直接是response.data
    
    // 保存token和用户信息到Vuex store
    this.$store.commit('SET_TOKEN', response.token);
    this.$store.commit('SET_USER', response.user);
    
    // 或者使用action
    // await this.$store.dispatch('login', {
    //   token: response.token,
    //   user: response.user
    // });
    
    alert('登录成功！即将跳转到首页');
    
    // 跳转到目标页面
    const redirect = this.$route.query.redirect || '/index';
    console.log('🚀 跳转目标:', redirect);
    this.$router.replace(redirect);
  } catch (error) {
    console.error('❌ 登录错误:', error);
    
    let errorMsg = '登录失败';
    if (error.response) {
      errorMsg = error.response.message || JSON.stringify(error.response);
    } else if (error.message.includes('Network')) {
      errorMsg = '网络连接失败，请检查后端服务是否启动（端口3000）';
    }
    
    alert('错误: ' + errorMsg);
  } finally {
    this.loading = false;
  }
}
    }
  };
  </script>
  
  <style scoped>
  .auth-page {
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #020a2b;
  }
  .auth-card {
    width: 360px;
    padding: 30px;
    box-sizing: border-box;
    text-align: center;
  }
  .auth-form {
    display: flex;
    flex-direction: column;
    gap: 15px;
    margin-top: 20px;
  }
  .auth-form label {
    display: flex;
    flex-direction: column;
    text-align: left;
    color: #cfe7ff;
  }
  .auth-form input {
    margin-top: 6px;
    border: none;
    border-radius: 8px;
    padding: 8px 10px;
  }
  button {
    border: none;
    border-radius: 20px;
    padding: 10px 0;
    cursor: pointer;
    color: #020a2b;
    background: linear-gradient(90deg, #2af7ff, #26b3ff);
  }
  .switch {
    margin-top: 15px;
    color: #6ea1ff;
  }
  </style>