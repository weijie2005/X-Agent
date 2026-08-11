<template>
  <div class="sessions-view">
    <div class="page-header">
      <h2>会话管理</h2>
      <button class="btn btn-primary" @click="createNewSession">新建会话</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    
    <div v-else-if="sessions.length === 0" class="empty-state">
      <p>暂无会话记录</p>
      <button class="btn btn-primary" @click="createNewSession">创建第一个会话</button>
    </div>

    <div v-else class="sessions-list">
      <div 
        v-for="session in sessions" 
        :key="session.id" 
        class="session-card"
      >
        <div class="session-info" @click="viewSession(session.id)">
          <h3>{{ session.title || '未命名会话' }}</h3>
          <p class="session-meta">
            <span class="session-time">{{ formatDate(session.created_at) }}</span>
            <span class="session-messages">{{ session.message_count || 0 }} 条消息</span>
          </p>
        </div>
        <div class="session-actions">
          <button class="btn-icon" title="继续对话" @click="continueSession(session.id)">💬</button>
          <button class="btn-icon" title="删除" @click="deleteSessionConfirm(session.id)">🗑️</button>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="closeDeleteConfirm">
      <div class="modal" @click.stop>
        <h3>确认删除</h3>
        <p>确定要删除这个会话吗？此操作不可恢复。</p>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeDeleteConfirm">取消</button>
          <button class="btn btn-danger" @click="confirmDelete">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const sessions = ref([])
const loading = ref(false)
const showDeleteConfirm = ref(false)
const sessionToDelete = ref(null)

const fetchSessions = async () => {
  loading.value = true
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
        limit: 50
      }
    })
    sessions.value = response.data
  } catch (error) {
    console.error('获取会话列表失败:', error)
    alert('获取会话列表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const createNewSession = () => {
  router.push('/')
  localStorage.removeItem('chat_session_id')
}

const viewSession = (sessionId) => {
  router.push(`/sessions/${sessionId}`)
}

const continueSession = (sessionId) => {
  localStorage.setItem('chat_session_id', sessionId)
  router.push('/')
}

const deleteSessionConfirm = (sessionId) => {
  sessionToDelete.value = sessionId
  showDeleteConfirm.value = true
}

const closeDeleteConfirm = () => {
  showDeleteConfirm.value = false
  sessionToDelete.value = null
}

const confirmDelete = async () => {
  if (!sessionToDelete.value) return
  
  try {
    await axios.delete(`/api/v1/sessions/${sessionToDelete.value}`)
    sessions.value = sessions.value.filter(s => s.id !== sessionToDelete.value)
    closeDeleteConfirm()
  } catch (error) {
    console.error('删除会话失败:', error)
    alert('删除会话失败: ' + (error.response?.data?.detail || error.message))
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchSessions()
})
</script>

<style scoped>
.sessions-view {
  padding: 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.page-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.btn-danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.btn-danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.loading {
  text-align: center;
  padding: 40px;
  color: #6b7280;
  font-size: 16px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-state p {
  font-size: 18px;
  color: #6b7280;
  margin-bottom: 24px;
}

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.session-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.session-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.session-info {
  flex: 1;
  cursor: pointer;
}

.session-info h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.session-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.session-time,
.session-messages {
  display: flex;
  align-items: center;
  gap: 4px;
}

.session-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  width: 40px;
  height: 40px;
  border: none;
  background: #f9fafb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 16px;
}

.btn-icon:hover {
  background: #f3f4f6;
  transform: scale(1.1);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 32px;
  max-width: 400px;
  width: 90%;
}

.modal h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
}

.modal p {
  font-size: 16px;
  color: #6b7280;
  margin: 0 0 24px 0;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .sessions-view {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .session-card {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .session-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>