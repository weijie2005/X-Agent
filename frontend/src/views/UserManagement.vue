<template>
  <div class="user-management">
    <div class="management-header">
      <h1>👤 用户管理</h1>
      <button class="btn btn-primary" @click="goBack">返回聊天</button>
    </div>

    <div class="management-content">
      <!-- 当前用户信息 -->
      <div class="current-user-section">
        <h2>当前用户信息</h2>
        <div class="user-card">
          <div class="user-avatar-large">
            {{ (currentUser?.nickname || currentUser?.username || 'U').charAt(0).toUpperCase() }}
          </div>
          <div class="user-details">
            <div class="user-detail-item">
              <label>用户名：</label>
              <span>{{ currentUser?.username }}</span>
            </div>
            <div class="user-detail-item">
              <label>昵称：</label>
              <span>{{ currentUser?.nickname || '未设置' }}</span>
            </div>
            <div class="user-detail-item">
              <label>邮箱：</label>
              <span>{{ currentUser?.email || '未设置' }}</span>
            </div>
            <div class="user-detail-item">
              <label>手机号：</label>
              <span>{{ currentUser?.phone || '未设置' }}</span>
            </div>
            <div class="user-detail-item">
              <label>所在部门：</label>
              <span>{{ currentUser?.department || '未设置' }}</span>
            </div>
            <div class="user-detail-item">
              <label>注册时间：</label>
              <span>{{ formatDate(currentUser?.created_at) }}</span>
            </div>
            <div class="user-detail-item">
              <label>最后登录：</label>
              <span>{{ currentUser?.last_login_at ? formatDate(currentUser?.last_login_at) : '从未登录' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 修改信息 -->
      <div class="edit-section">
        <h2>修改个人信息</h2>
        <form @submit.prevent="updateProfile" class="edit-form">
          <div class="form-group">
            <label for="nickname">昵称</label>
            <input
              id="nickname"
              v-model="editForm.nickname"
              type="text"
              placeholder="请输入昵称"
            />
          </div>

          <div class="form-group">
            <label for="email">邮箱</label>
            <input
              id="email"
              v-model="editForm.email"
              type="email"
              placeholder="请输入邮箱"
            />
          </div>

          <div class="form-group">
            <label for="phone">手机号</label>
            <input
              id="phone"
              v-model="editForm.phone"
              type="tel"
              placeholder="请输入手机号"
            />
          </div>

          <div class="form-group">
            <label for="department">所在部门</label>
            <input
              id="department"
              v-model="editForm.department"
              type="text"
              placeholder="请输入所在部门"
            />
          </div>

          <div v-if="successMessage" class="success-message">
            {{ successMessage }}
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>

          <button type="submit" class="btn btn-success" :disabled="isUpdating">
            {{ isUpdating ? '保存中...' : '保存修改' }}
          </button>
        </form>
      </div>

      <!-- 修改密码 -->
      <div class="password-section">
        <h2>修改密码</h2>
        <form @submit.prevent="changePassword" class="edit-form">
          <div class="form-group">
            <label for="oldPassword">当前密码</label>
            <input
              id="oldPassword"
              v-model="passwordForm.oldPassword"
              type="password"
              placeholder="请输入当前密码"
              required
            />
          </div>

          <div class="form-group">
            <label for="newPassword">新密码</label>
            <input
              id="newPassword"
              v-model="passwordForm.newPassword"
              type="password"
              placeholder="请输入新密码"
              required
            />
          </div>

          <div class="form-group">
            <label for="confirmPassword">确认新密码</label>
            <input
              id="confirmPassword"
              v-model="passwordForm.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
              required
            />
          </div>

          <div v-if="passwordSuccessMessage" class="success-message">
            {{ passwordSuccessMessage }}
          </div>

          <div v-if="passwordErrorMessage" class="error-message">
            {{ passwordErrorMessage }}
          </div>

          <button type="submit" class="btn btn-warning" :disabled="isChangingPassword">
            {{ isChangingPassword ? '修改中...' : '修改密码' }}
          </button>
        </form>
      </div>

      <!-- 退出登录 -->
      <div class="logout-section">
        <h2>退出登录</h2>
        <p class="logout-hint">退出当前账号，需要重新登录才能使用系统。</p>
        <button class="btn btn-danger" @click="logout">
          <span class="menu-icon">🚪</span>
          <span>退出登录</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'UserManagement',
  setup() {
    const router = useRouter()
    const currentUser = ref(null)
    const isUpdating = ref(false)
    const isChangingPassword = ref(false)
    const successMessage = ref('')
    const errorMessage = ref('')
    const passwordSuccessMessage = ref('')
    const passwordErrorMessage = ref('')
    
    const editForm = ref({
      nickname: '',
      email: '',
      phone: '',
      department: ''
    })
    
    const passwordForm = ref({
      oldPassword: '',
      newPassword: '',
      confirmPassword: ''
    })

    // 加载当前用户信息
    const loadCurrentUser = () => {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        try {
          currentUser.value = JSON.parse(userStr)
          editForm.value.nickname = currentUser.value.nickname || ''
          editForm.value.email = currentUser.value.email || ''
          editForm.value.phone = currentUser.value.phone || ''
          editForm.value.department = currentUser.value.department || ''
        } catch (e) {
          console.error('Parse user error:', e)
        }
      }
    }

    // 格式化日期
    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    }

    // 更新个人信息
    const updateProfile = async () => {
      successMessage.value = ''
      errorMessage.value = ''
      isUpdating.value = true

      try {
        const response = await axios.put('/api/v1/auth/profile', {
          nickname: editForm.value.nickname,
          email: editForm.value.email,
          phone: editForm.value.phone,
          department: editForm.value.department
        })
        
        // 更新本地存储的用户信息
        currentUser.value = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
        
        successMessage.value = '个人信息更新成功！'
        
        setTimeout(() => {
          successMessage.value = ''
        }, 3000)
      } catch (error) {
        console.error('Update profile error:', error)
        errorMessage.value = error.response?.data?.detail || '更新失败，请重试'
      } finally {
        isUpdating.value = false
      }
    }

    // 修改密码
    const changePassword = async () => {
      passwordSuccessMessage.value = ''
      passwordErrorMessage.value = ''

      // 验证密码
      if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
        passwordErrorMessage.value = '两次输入的密码不一致'
        return
      }

      if (passwordForm.value.newPassword.length < 6) {
        passwordErrorMessage.value = '密码长度至少为6位'
        return
      }

      isChangingPassword.value = true

      try {
        const response = await axios.put('/api/v1/auth/password', {
          old_password: passwordForm.value.oldPassword,
          new_password: passwordForm.value.newPassword
        })
        
        passwordSuccessMessage.value = response.data.message || '密码修改成功！'
        
        // 清空表单
        passwordForm.value = {
          oldPassword: '',
          newPassword: '',
          confirmPassword: ''
        }
        
        setTimeout(() => {
          passwordSuccessMessage.value = ''
        }, 3000)
      } catch (error) {
        console.error('Change password error:', error)
        passwordErrorMessage.value = error.response?.data?.detail || '密码修改失败，请重试'
      } finally {
        isChangingPassword.value = false
      }
    }

    // 返回聊天页面
    const goBack = () => {
      router.push('/')
    }

    // 退出登录
    const logout = () => {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      router.push('/login')
    }

    onMounted(() => {
      loadCurrentUser()
    })

    return {
      currentUser,
      editForm,
      passwordForm,
      isUpdating,
      isChangingPassword,
      successMessage,
      errorMessage,
      passwordSuccessMessage,
      passwordErrorMessage,
      formatDate,
      updateProfile,
      changePassword,
      goBack,
      logout
    }
  }
}
</script>

<style scoped>
.user-management {
  min-height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.management-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px 30px;
  border-radius: 16px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.management-header h1 {
  margin: 0;
  font-size: 24px;
  color: #1f2937;
}

.management-content {
  max-width: 800px;
  margin: 0 auto;
}

.current-user-section,
.edit-section,
.password-section,
.logout-section {
  background: white;
  padding: 30px;
  border-radius: 16px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.current-user-section h2,
.edit-section h2,
.password-section h2,
.logout-section h2 {
  margin: 0 0 20px;
  font-size: 18px;
  color: #1f2937;
}

.user-card {
  display: flex;
  gap: 30px;
  align-items: flex-start;
}

.user-avatar-large {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 700;
  flex-shrink: 0;
}

.user-details {
  flex: 1;
}

.user-detail-item {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.user-detail-item label {
  font-weight: 600;
  color: #6b7280;
  min-width: 80px;
}

.user-detail-item span {
  color: #1f2937;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.form-group input {
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

.success-message {
  padding: 12px;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  border-radius: 8px;
  color: #065f46;
  font-size: 14px;
}

.error-message {
  padding: 12px;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
}

.logout-hint {
  color: #6b7280;
  margin-bottom: 16px;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5a67d8;
  transform: translateY(-2px);
}

.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover {
  background: #059669;
  transform: translateY(-2px);
}

.btn-warning {
  background: #f59e0b;
  color: white;
}

.btn-warning:hover {
  background: #d97706;
  transform: translateY(-2px);
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
  transform: translateY(-2px);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}
</style>