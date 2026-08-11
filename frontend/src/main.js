import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// 配置 axios 拦截器，自动添加 token 到请求头
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 配置 axios 响应拦截器，处理 401 错误
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // Token 过期或无效，清除本地存储并跳转到登录页
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

createApp(App).use(router).mount('#app')