import axios from 'axios'
import { getToken, clearAuth } from './auth'
import router from '@/router'

const $http = axios.create({
  baseURL: process.env.VUE_APP_API_BASE || 'http://localhost:3000',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
$http.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
$http.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status } = error.response
      
      if (status === 401) {
        clearAuth()
        if (router.currentRoute.path !== '/auth/login') {
          router.replace({ 
            path: '/auth/login', 
            query: { redirect: router.currentRoute.fullPath } 
          })
        }
        // 简单的错误提示
        alert('登录已过期，请重新登录')
      }
    }
    
    return Promise.reject(error)
  }
)

export default $http