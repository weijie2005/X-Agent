<template>
  <div :class="['sidebar', { collapsed: isCollapsed }]">
    <div class="sidebar-header">
      <div v-show="!isCollapsed" class="logo">
        <span class="logo-icon">🤖</span>
        <span class="logo-text">X-Agent</span>
      </div>
      <button class="toggle-btn" @click="toggleSidebar">
        <span v-if="isCollapsed">»</span>
        <span v-else>«</span>
      </button>
    </div>
    
    <nav class="sidebar-nav">
      <!-- 对话菜单项（带新建会话按钮） -->
      <div class="nav-item-wrapper">
        <router-link 
          to="/"
          class="nav-item"
          title="对话"
        >
          <span class="nav-icon">💬</span>
          <span v-show="!isCollapsed" class="nav-text">对话</span>
        </router-link>
        <button 
          v-show="!isCollapsed" 
          class="new-session-btn" 
          @click="createNewSession"
          title="新建会话"
        >
          +
        </button>
      </div>
      
      <router-link 
        v-for="item in otherMenuItems" 
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :title="item.title"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span v-show="!isCollapsed" class="nav-text">{{ item.text }}</span>
      </router-link>
      
      <!-- 最近会话列表 -->
      <div v-show="!isCollapsed" class="recent-sessions">
        <div class="recent-sessions-header">
          <span class="nav-icon">📋</span>
          <span class="nav-text">最近会话</span>
        </div>
        <div class="recent-sessions-list">
          <div 
            v-for="session in recentSessions" 
            :key="session.id"
            class="recent-session-item"
            @click="openSession(session.id)"
            :title="session.title || '未命名会话'"
          >
            <span class="session-dot">●</span>
            <span class="session-title">{{ session.title || '未命名会话' }}</span>
          </div>
          <div v-if="recentSessions.length === 0" class="no-sessions">
            暂无会话
          </div>
        </div>
      </div>
    </nav>
    
    <div class="sidebar-footer">
      <button class="nav-item" title="退出登录" @click="logout">
        <span class="nav-icon">🚪</span>
        <span v-show="!isCollapsed" class="nav-text">退出登录</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const isCollapsed = ref(false)
const recentSessions = ref([])

const otherMenuItems = [
  {
    path: '/sessions',
    icon: '📋',
    text: '会话管理',
    title: '会话管理'
  },
  {
    path: '/knowledge-base',
    icon: '📚',
    text: '知识库管理',
    title: '知识库管理'
  },
  {
    path: '/settings',
    icon: '⚙️',
    text: '系统设置',
    title: '系统设置'
  }
]

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const createNewSession = async () => {
  try {
    const userStr = localStorage.getItem('user')
    let userId = null
    if (userStr) {
      try {
        const user = JSON.parse(userStr)
        userId = user.id
      } catch (e) {
        console.error('Parse user error:', e)
      }
    }
    
    const response = await axios.post('/api/v1/sessions', {
      user_id: userId,
      title: '新会话'
    })
    
    const newSession = response.data
    localStorage.setItem('chat_session_id', newSession.id)
    
    if (router.currentRoute.value.path === '/') {
      window.dispatchEvent(new CustomEvent('session-changed', { 
        detail: { sessionId: newSession.id } 
      }))
    } else {
      await router.push('/')
    }
    
    await fetchRecentSessions()
  } catch (error) {
    console.error('创建会话失败:', error)
    alert('创建会话失败')
  }
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}

const fetchRecentSessions = async () => {
  try {
    const userStr = localStorage.getItem('user')
    let userId = null
    if (userStr) {
      try {
        const user = JSON.parse(userStr)
        userId = user.id
      } catch (e) {
        console.error('Parse user error:', e)
      }
    }
    
    const response = await axios.get('/api/v1/sessions', {
      params: {
        user_id: userId,
        limit: 10
      }
    })
    recentSessions.value = response.data
  } catch (error) {
    console.error('获取最近会话失败:', error)
  }
}

const openSession = async (sessionId) => {
  localStorage.setItem('chat_session_id', sessionId)
  
  if (router.currentRoute.value.path === '/') {
    window.dispatchEvent(new CustomEvent('session-changed', { 
      detail: { sessionId } 
    }))
  } else {
    await router.push('/')
  }
}

const handleSessionUpdate = () => {
  fetchRecentSessions()
}

onMounted(() => {
  fetchRecentSessions()
  window.addEventListener('session-updated', handleSessionUpdate)
})

onUnmounted(() => {
  window.removeEventListener('session-updated', handleSessionUpdate)
})
</script>

<style scoped>
.sidebar {
  width: 240px;
  height: 100vh;
  background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
  color: #f9fafb;
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 100;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  min-height: 72px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.toggle-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: #f9fafb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
}

.nav-item-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-item-wrapper .nav-item {
  flex: 1;
}

.new-session-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  flex-shrink: 0;
}

.new-session-btn:hover {
  background: #667eea;
  color: white;
  transform: scale(1.1);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  color: #d1d5db;
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
  border: none;
  background: transparent;
  width: 100%;
  text-align: left;
  font-size: 15px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #f9fafb;
  transform: translateX(4px);
}

.nav-item.router-link-active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 12px;
}

.nav-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.nav-text {
  font-weight: 500;
}

.recent-sessions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.recent-sessions-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  color: #9ca3af;
  font-size: 14px;
  font-weight: 600;
}

.recent-sessions-list {
  margin-top: 8px;
}

.recent-session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  color: #d1d5db;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 8px;
  margin: 2px 4px;
}

.recent-session-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #f9fafb;
}

.session-dot {
  font-size: 8px;
  color: #667eea;
}

.session-title {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.no-sessions {
  padding: 12px 16px;
  color: #6b7280;
  font-size: 14px;
  text-align: center;
}

.sidebar-footer {
  padding: 16px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    transform: translateX(-100%);
  }
  
  .sidebar:not(.collapsed) {
    transform: translateX(0);
  }
}
</style>