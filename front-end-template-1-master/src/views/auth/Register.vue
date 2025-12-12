<template>
    <div class="auth-page">
      <dv-border-box-12 class="auth-card">
        <h2>创建帐号</h2>
        <form class="auth-form" @submit.prevent="handleRegister">
          <label>
            用户名
            <input v-model.trim="form.username" required />
          </label>
          <label>
            邮箱
            <input v-model.trim="form.email" type="email" required />
          </label>
          <label>
            密码
            <input v-model.trim="form.password" type="password" required />
          </label>
          <label>
            确认密码
            <input v-model.trim="form.confirmPassword" type="password" required />
          </label>
          <button type="submit" :disabled="loading">
            {{ loading ? '注册中...' : '注册' }}
          </button>
        </form>
        <p class="switch">
          已有帐号？
          <router-link to="/auth/login">直接登录</router-link>
        </p>
      </dv-border-box-12>
    </div>
  </template>
  
  <script>
  export default {
    name: 'Register',
    data() {
      return {
        loading: false,
        form: { username: '', email: '', password: '', confirmPassword: '' }
      };
    },
    methods: {
      async handleRegister() {
        if (this.form.password !== this.form.confirmPassword) {
          alert('两次输入的密码不一致');
          return;
        }
        this.loading = true;
        try {
          console.log('📝 开始注册...');
          
          const response = await this.$http.post('/api/auth/register', {
            username: this.form.username,
            email: this.form.email,
            password: this.form.password
          });
          
          console.log('✅ 注册成功:', response);
          alert('注册成功！请登录');
          
          this.$router.push({ 
            path: '/auth/login', 
            query: { username: this.form.username } 
          });
        } catch (error) {
          console.error('❌ 注册失败:', error);
          
          let errorMsg = '注册失败';
          if (error.response && error.response.data) {
            errorMsg = error.response.data.message || JSON.stringify(error.response.data);
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
    width: 420px;
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