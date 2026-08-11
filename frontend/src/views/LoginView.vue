<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>🤖X-Agent</h1>
        <p>{{ isLogin ? '欢迎回来' : '创建新账号' }}</p>
      </div>

      <div class="login-tabs">
        <button 
          :class="['tab', { active: isLogin }]" 
          @click="isLogin = true"
        >
          登录
        </button>
        <button 
          :class="['tab', { active: !isLogin }]" 
          @click="isLogin = false"
        >
          注册
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            placeholder="请输入用户名"
            required
            :disabled="isLoading"
          />
        </div>

        <div v-if="!isLogin" class="form-group">
          <label for="email">邮箱（可选）</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            placeholder="请输入邮箱"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            required
            :disabled="isLoading"
          />
        </div>

        <div v-if="!isLogin" class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            required
            :disabled="isLoading"
          />
        </div>

        <div v-if="!isLogin" class="form-group">
          <label for="nickname">昵称（可选）</label>
          <input
            id="nickname"
            v-model="form.nickname"
            type="text"
            placeholder="请输入昵称"
            :disabled="isLoading"
          />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button type="submit" class="submit-btn" :disabled="isLoading">
          {{ isLoading ? '处理中...' : (isLogin ? '登录' : '注册') }}
        </button>
      </form>

      <div class="login-footer">
        <p>
          {{ isLogin ? '还没有账号？' : '已有账号？' }}
          <a href="#" @click.prevent="isLogin = !isLogin">
            {{ isLogin ? '立即注册' : '立即登录' }}
          </a>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'LoginView',
  setup() {
    const router = useRouter()
    const isLogin = ref(true)
    const isLoading = ref(false)
    const errorMessage = ref('')
    
    const form = ref({
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      nickname: ''
    })

    const handleSubmit = async () => {
      errorMessage.value = ''
      
      // 注册时验证密码确认
      if (!isLogin.value) {
        if (form.value.password !== form.value.confirmPassword) {
          errorMessage.value = '两次输入的密码不一致'
          return
        }
        if (form.value.password.length < 6) {
          errorMessage.value = '密码长度至少为6位'
          return
        }
      }
      
      isLoading.value = true

      try {
        const endpoint = isLogin.value ? '/api/v1/auth/login' : '/api/v1/auth/register'
        
        const payload = isLogin.value 
          ? {
              username: form.value.username,
              password: form.value.password
            }
          : {
              username: form.value.username,
              password: form.value.password,
              email: form.value.email || undefined,
              nickname: form.value.nickname || undefined
            }

        const response = await axios.post(endpoint, payload)
        
        if (response.data.success) {
          // 保存用户信息和 token
          localStorage.setItem('user', JSON.stringify(response.data.user))
          localStorage.setItem('token', response.data.token)
          
          // 跳转到聊天页面
          router.push('/')
        }
      } catch (error) {
        console.error('Auth error:', error)
        errorMessage.value = error.response?.data?.error || error.response?.data?.detail || '操作失败，请重试'
      } finally {
        isLoading.value = false
      }
    }

    return {
      isLogin,
      isLoading,
      errorMessage,
      form,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-box {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 420px;
  overflow: hidden;
}

.login-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px 30px;
  text-align: center;
}

.login-header h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
}

.login-header p {
  margin: 10px 0 0;
  font-size: 16px;
  opacity: 0.9;
}

.login-tabs {
  display: flex;
  border-bottom: 2px solid #e5e7eb;
}

.tab {
  flex: 1;
  padding: 16px;
  border: none;
  background: none;
  font-size: 16px;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab.active {
  color: #667eea;
  background: #f3f4f6;
}

.tab:hover:not(.active) {
  background: #f9fafb;
}

.login-form {
  padding: 30px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.form-group input:disabled {
  background: #f9fafb;
  cursor: not-allowed;
}

.error-message {
  padding: 12px;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  margin-bottom: 20px;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-footer {
  padding: 20px 30px;
  background: #f9fafb;
  text-align: center;
  border-top: 1px solid #e5e7eb;
}

.login-footer p {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.login-footer a {
  color: #667eea;
  font-weight: 600;
  text-decoration: none;
}

.login-footer a:hover {
  text-decoration: underline;
}
</style>