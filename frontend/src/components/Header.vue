<template>
  <header class="header">
    <div class="header-left">
      <h2 class="page-title">{{ pageTitle }}</h2>
    </div>
    
    <div class="header-right">
      <button class="header-btn" title="帮助">
        <span class="btn-icon">❓</span>
      </button>
      
      <button class="header-btn" title="通知">
        <span class="btn-icon">🔔</span>
      </button>
      
      <div class="user-dropdown" v-if="currentUser">
        <div class="user-info" @click="toggleUserMenu">
          <div class="user-avatar">{{ (currentUser.nickname || currentUser.username).charAt(0).toUpperCase() }}</div>
          <span class="user-name">{{ currentUser.nickname || currentUser.username }}</span>
          <span class="dropdown-arrow">▼</span>
        </div>
        
        <div v-if="showUserMenu" class="dropdown-menu" @click.stop>
          <div class="dropdown-item user-info-item">
            <div class="user-email">{{ currentUser.email || '未设置邮箱' }}</div>
          </div>
          <div class="dropdown-divider"></div>
          <button class="dropdown-item" @click.stop="goToUserManagement">
            <span class="menu-icon">👤</span>
            <span>用户管理</span>
          </button>
          <button class="dropdown-item" @click.stop="goToSettings">
            <span class="menu-icon">⚙️</span>
            <span>设置</span>
          </button>
          <div class="dropdown-divider"></div>
          <button class="dropdown-item logout-item" @click.stop="logout">
            <span class="menu-icon">🚪</span>
            <span>退出登录</span>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const currentUser = ref(null)
const showUserMenu = ref(false)

const pageTitle = computed(() => {
  const titles = {
    '/': '智能对话',
    '/sessions': '会话管理',
    '/settings': '系统设置'
  }
  return titles[route.path] || 'AI Agent'
})

const loadCurrentUser = () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      currentUser.value = JSON.parse(userStr)
    } catch (e) {
      console.error('Parse user error:', e)
    }
  }
}

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

const handleClickOutside = (event) => {
  if (showUserMenu.value) {
    const dropdown = document.querySelector('.user-dropdown')
    if (dropdown && !dropdown.contains(event.target)) {
      showUserMenu.value = false
    }
  }
}

const goToUserManagement = () => {
  showUserMenu.value = false
  router.push('/user-management')
}

const goToSettings = () => {
  showUserMenu.value = false
  router.push('/settings')
}

const logout = () => {
  showUserMenu.value = false
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}

onMounted(() => {
  loadCurrentUser()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.header {
  height: 64px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 50;
}

.header-left {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: #f9fafb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-btn:hover {
  background: #f3f4f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.btn-icon {
  font-size: 18px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #f9fafb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-info:hover {
  background: #f3f4f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.user-dropdown {
  position: relative;
}

.dropdown-arrow {
  font-size: 10px;
  color: #6b7280;
  margin-left: 4px;
  transition: transform 0.2s ease;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  overflow: hidden;
  z-index: 1000;
  animation: dropdownFade 0.2s ease;
}

@keyframes dropdownFade {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: none;
  text-align: left;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dropdown-item:hover {
  background: #f3f4f6;
}

.dropdown-item.user-info-item {
  cursor: default;
  padding: 16px;
}

.dropdown-item.user-info-item:hover {
  background: white;
}

.user-email {
  font-size: 12px;
  color: #6b7280;
}

.dropdown-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 4px 0;
}

.menu-icon {
  font-size: 16px;
}

.logout-item {
  color: #ef4444;
}

.logout-item:hover {
  background: #fee2e2;
}

@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }
  
  .user-name {
    display: none;
  }
}
</style>