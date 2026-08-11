<template>
  <div class="chat-view">
    <div class="chat-container">
      <!-- 头部 -->
      <div class="chat-header">
        <h2>Agent session</h2>
        <div class="header-actions">
          <button class="btn btn-icon btn-primary" @click="createNewSession" title="新建对话">➕</button>
          <button class="btn btn-icon btn-secondary" @click="clearChat" title="清空对话">🗑️</button>
          <button class="btn btn-icon btn-success" @click="exportPDF" title="导出 PDF">📄</button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <ChatMessage
          v-for="(message, index) in messages"
          :key="index"
          :message="message"
        />
        
        <!-- 加载动画 -->
        <div v-if="isLoading" class="message assistant">
          <div class="message-avatar">🤖</div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-container">
        <!-- 知识库选择 -->
        <div class="knowledge-base-selector">
          <label class="checkbox-label">
            <input type="checkbox" v-model="useKnowledgeBase" @change="handleKnowledgeBaseToggle" />
            <span>使用知识库</span>
          </label>
          
          <!-- 树形选择器 -->
          <div v-if="useKnowledgeBase" class="tree-selector-container" ref="treeSelectorRef">
            <div class="tree-selector-header" @click="showTreeSelector = !showTreeSelector">
              <span>{{ selectedFilesText }}</span>
              <span class="dropdown-icon">{{ showTreeSelector ? '▲' : '▼' }}</span>
            </div>
            
            <div v-if="showTreeSelector" class="tree-selector-dropdown">
              <div class="tree-selector-actions">
                <button class="btn-tree" @click="selectAllFiles">全选</button>
                <button class="btn-tree" @click="deselectAllFiles">全不选</button>
              </div>
              
              <div class="tree-list">
                <div v-for="kb in knowledgeBases" :key="kb.id" class="tree-kb-item">
                  <div class="tree-kb-header" @click="toggleKbExpanded(kb.id)">
                    <input 
                      type="checkbox" 
                      :checked="isKbFullySelected(kb.id)"
                      :indeterminate.prop="isKbPartiallySelected(kb.id)"
                      @change="toggleKbSelection(kb.id)"
                      @click.stop
                    />
                    <span class="tree-icon">{{ expandedKbs.includes(kb.id) ? '▼' : '▶' }}</span>
                    <span class="tree-label">{{ kb.name }}</span>
                  </div>
                  
                  <div v-if="expandedKbs.includes(kb.id)" class="tree-documents">
                    <div 
                      v-for="doc in getKbDocuments(kb.id)" 
                      :key="doc.id" 
                      class="tree-doc-item"
                    >
                      <input 
                        type="checkbox" 
                        v-model="selectedFiles"
                        :value="doc.id"
                      />
                      <span class="tree-doc-label">{{ doc.filename }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 输入框和发送按钮 -->
        <div class="input-row">
          <textarea
            v-model="userInput"
            @keydown.enter.exact.prevent="sendMessage"
            placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
            rows="2"
            :disabled="isLoading"
          ></textarea>
          <button @click="sendMessage" :disabled="isLoading || !userInput.trim()">
            {{ isLoading ? '发送中...' : '发送' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import ChatMessage from '../components/ChatMessage.vue'

export default {
  name: 'ChatView',
  components: {
    ChatMessage
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const messages = ref([])
    const userInput = ref('')
    const isLoading = ref(false)
    const messagesContainer = ref(null)
    const knowledgeBases = ref([])
    const selectedKnowledgeBase = ref('')
    
    // 知识库选择相关状态
    const useKnowledgeBase = ref(false)
    const showTreeSelector = ref(false)
    const selectedFiles = ref([])
    const expandedKbs = ref([])
    const kbDocuments = ref({})
    const treeSelectorRef = ref(null)
    
    // 生成会话 ID（UUID格式）
    const generateSessionId = () => {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0
        const v = c === 'x' ? r : (r & 0x3 | 0x8)
        return v.toString(16)
      })
    }
    
    // 获取或创建会话 ID
    const getSessionId = () => {
      let sessionId = localStorage.getItem('chat_session_id')
      if (!sessionId) {
        sessionId = generateSessionId()
        localStorage.setItem('chat_session_id', sessionId)
      }
      return sessionId
    }
    
    // 滚动到底部
    const scrollToBottom = async () => {
      await nextTick()
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }
    
    // 发送消息
    const sendMessage = async () => {
      if (!userInput.value.trim() || isLoading.value) return
      
      const userMessage = userInput.value.trim()
      console.log('🚀 Sending message:', userMessage)
      
      // 添加用户消息
      messages.value.push({
        role: 'user',
        content: userMessage
      })
      
      userInput.value = ''
      isLoading.value = true
      
      await scrollToBottom()
      
      // 如果是第一条消息，更新会话标题
      if (messages.value.length === 1) {
        const sessionId = getSessionId()
        const title = userMessage.substring(0, 20) + (userMessage.length > 20 ? '...' : '')
        try {
          await axios.patch(`/api/v1/sessions/${sessionId}`, {
            title: title
          })
          console.log('✅ Updated session title:', title)
          
          // 通知Sidebar刷新会话列表
          window.dispatchEvent(new CustomEvent('session-updated'))
        } catch (error) {
          console.error('更新会话标题失败:', error)
        }
      }
      
      // 创建助手消息占位符
      const assistantMessageIndex = messages.value.length
      messages.value.push({
        role: 'assistant',
        content: '',
        thinking: '',
        isThinking: true,
        showThinking: true
      })
      
      try {
        const sessionId = getSessionId()
        console.log('📋 Session ID:', sessionId)
        
        // 获取当前用户ID
        const userStr = localStorage.getItem('user')
        let userId = null
        if (userStr) {
          try {
            const user = JSON.parse(userStr)
            userId = user.id
            console.log('👤 User ID:', userId)
          } catch (e) {
            console.error('Parse user error:', e)
          }
        }
        
        const response = await fetch('/api/v1/agent/chat/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            user_input: userMessage,
            session_id: sessionId,
            user_id: userId,
            knowledge_base_id: useKnowledgeBase.value && selectedFiles.value.length > 0 
              ? getPrimaryKnowledgeBaseId() 
              : null,
            document_ids: useKnowledgeBase.value && selectedFiles.value.length > 0 
              ? selectedFiles.value 
              : null
          })
        })
        
        console.log('📥 Response status:', response.status)
        console.log('📥 Response OK:', response.ok)
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let assistantContent = ''
        let thinkingContent = ''
        
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) {
            console.log('✅ Stream completed')
            break
          }
          
          const chunk = decoder.decode(value, { stream: true })
          console.log('📦 Received chunk:', chunk)
          buffer += chunk
          
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = line.slice(6)
                
                // 检查是否是完成标记
                if (data === '[DONE]') {
                  console.log('✅ Stream completed')
                  messages.value[assistantMessageIndex].isThinking = false
                  break
                }
                
                const parsed = JSON.parse(data)
                console.log('📝 Parsed data:', parsed)
                
                // 提取最终回复内容
                if (parsed.data?.reasoning?.current_output) {
                  assistantContent = parsed.data.reasoning.current_output
                  messages.value[assistantMessageIndex].content = assistantContent
                  await scrollToBottom()
                }
                
                // 提取推理步骤（思考过程）- 流式更新
                if (parsed.data?.reasoning_steps && Array.isArray(parsed.data.reasoning_steps)) {
                  // 将推理步骤格式化为可读的文本
                  thinkingContent = parsed.data.reasoning_steps.map(step => {
                    return `**步骤 ${step.step}：${step.action}**\n${step.content}`
                  }).join('\n\n')
                  messages.value[assistantMessageIndex].thinking = thinkingContent
                  await scrollToBottom()
                }
              } catch (e) {
                console.error('❌ Parse error:', e)
              }
            }
          }
        }
        
        console.log('🏁 Request completed')
      } catch (error) {
        console.error('❌ Error:', error)
        messages.value[assistantMessageIndex].content = `请求失败：${error.message}`
      } finally {
        isLoading.value = false
        await scrollToBottom()
      }
    }
    
    // 清空对话
    const clearChat = () => {
      messages.value = []
      localStorage.removeItem('chat_session_id')
    }
    
    // 创建新会话
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
        messages.value = []
        localStorage.setItem('chat_session_id', newSession.id)
        
        console.log('✅ Created new session:', newSession.id)
      } catch (error) {
        console.error('创建会话失败:', error)
        alert('创建会话失败')
      }
    }
    
    // 导出 PDF
    const exportPDF = async () => {
      const sessionId = localStorage.getItem('chat_session_id')
      if (!sessionId) {
        alert('没有可导出的会话')
        return
      }
      
      try {
        const response = await axios.get(`/api/v1/pdf/export/${sessionId}`, {
          responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `chat_${sessionId}.pdf`)
        document.body.appendChild(link)
        link.click()
        link.remove()
      } catch (error) {
        console.error('PDF 导出失败:', error)
        alert('PDF 导出失败')
      }
    }
    
    // 获取知识库列表
    const fetchKnowledgeBases = async () => {
      try {
        const response = await axios.get('/api/v1/knowledge-bases')
        knowledgeBases.value = response.data
        console.log('📚 Loaded knowledge bases:', knowledgeBases.value)
        
        // 加载每个知识库的文档列表
        for (const kb of knowledgeBases.value) {
          await fetchKbDocuments(kb.id)
        }
      } catch (error) {
        console.error('Failed to fetch knowledge bases:', error)
      }
    }
    
    // 获取知识库的文档列表
    const fetchKbDocuments = async (kbId) => {
      try {
        const response = await axios.get(`/api/v1/knowledge-bases/${kbId}/documents`, {
          params: { limit: 100 }
        })
        kbDocuments.value[kbId] = response.data
        console.log(`📄 Loaded ${response.data.length} documents for KB ${kbId}`)
      } catch (error) {
        console.error(`Failed to fetch documents for KB ${kbId}:`, error)
        kbDocuments.value[kbId] = []
      }
    }
    
    // 知识库选择相关方法
    const handleKnowledgeBaseToggle = () => {
      if (useKnowledgeBase.value) {
        // 默认全选所有文件
        selectAllFiles()
      } else {
        selectedFiles.value = []
      }
    }
    
    const toggleKbExpanded = (kbId) => {
      const index = expandedKbs.value.indexOf(kbId)
      if (index > -1) {
        expandedKbs.value.splice(index, 1)
      } else {
        expandedKbs.value.push(kbId)
      }
    }
    
    const getKbDocuments = (kbId) => {
      return kbDocuments.value[kbId] || []
    }
    
    const isKbFullySelected = (kbId) => {
      const docs = getKbDocuments(kbId)
      if (docs.length === 0) return false
      return docs.every(doc => selectedFiles.value.includes(doc.id))
    }
    
    const isKbPartiallySelected = (kbId) => {
      const docs = getKbDocuments(kbId)
      if (docs.length === 0) return false
      const selectedCount = docs.filter(doc => selectedFiles.value.includes(doc.id)).length
      return selectedCount > 0 && selectedCount < docs.length
    }
    
    const toggleKbSelection = (kbId) => {
      const docs = getKbDocuments(kbId)
      if (isKbFullySelected(kbId)) {
        // 取消选择该知识库的所有文件
        selectedFiles.value = selectedFiles.value.filter(
          fileId => !docs.find(doc => doc.id === fileId)
        )
      } else {
        // 选择该知识库的所有文件
        const docIds = docs.map(doc => doc.id)
        selectedFiles.value = [...new Set([...selectedFiles.value, ...docIds])]
      }
    }
    
    const selectAllFiles = () => {
      const allDocIds = []
      for (const kbId in kbDocuments.value) {
        const docs = kbDocuments.value[kbId]
        docs.forEach(doc => allDocIds.push(doc.id))
      }
      selectedFiles.value = allDocIds
    }
    
    const deselectAllFiles = () => {
      selectedFiles.value = []
    }
    
    const getPrimaryKnowledgeBaseId = () => {
      if (selectedFiles.value.length === 0) return null
      // 返回第一个选中文件所属的知识库ID
      for (const kb of knowledgeBases.value) {
        const docs = getKbDocuments(kb.id)
        if (docs.some(doc => selectedFiles.value.includes(doc.id))) {
          return kb.id
        }
      }
      return null
    }
    
    const selectedFilesText = computed(() => {
      if (!useKnowledgeBase.value) return ''
      if (selectedFiles.value.length === 0) return '请选择文件'
      if (selectedFiles.value.length === 1) return '已选择 1 个文件'
      return `已选择 ${selectedFiles.value.length} 个文件`
    })
    
    // 加载会话历史消息
    const loadSessionHistory = async () => {
      const sessionId = localStorage.getItem('chat_session_id')
      if (!sessionId) return
      
      try {
        console.log('📜 Loading session history for:', sessionId)
        const response = await axios.get(`/api/v1/sessions/${sessionId}/messages`, {
          params: {
            limit: 100
          }
        })
        
        const historyMessages = response.data
        console.log('📜 Loaded messages:', historyMessages.length)
        
        if (historyMessages && historyMessages.length > 0) {
          messages.value = historyMessages.map(msg => ({
            role: msg.role.toLowerCase(),
            content: msg.content
          }))
          
          await scrollToBottom()
        } else {
          messages.value = []
        }
      } catch (error) {
        console.error('Failed to load session history:', error)
        messages.value = []
      }
    }
    
    watch(() => route.path, async (newPath) => {
      if (newPath === '/') {
        console.log('🔄 Route changed to chat, reloading session history')
        messages.value = []
        await loadSessionHistory()
        await scrollToBottom()
      }
    })
    
    const handleSessionChange = async (event) => {
      console.log('🔄 Session changed event received:', event.detail)
      messages.value = []
      await loadSessionHistory()
      await scrollToBottom()
    }
    
    const handleClickOutside = (event) => {
      if (treeSelectorRef.value && !treeSelectorRef.value.contains(event.target)) {
        showTreeSelector.value = false
      }
    }
    
    onMounted(async () => {
      await loadSessionHistory()
      scrollToBottom()
      fetchKnowledgeBases()
      
      window.addEventListener('session-changed', handleSessionChange)
      document.addEventListener('click', handleClickOutside)
    })
    
    onUnmounted(() => {
      window.removeEventListener('session-changed', handleSessionChange)
      document.removeEventListener('click', handleClickOutside)
    })
    
    return {
      messages,
      userInput,
      isLoading,
      messagesContainer,
      knowledgeBases,
      selectedKnowledgeBase,
      useKnowledgeBase,
      showTreeSelector,
      selectedFiles,
      expandedKbs,
      kbDocuments,
      treeSelectorRef,
      selectedFilesText,
      sendMessage,
      clearChat,
      createNewSession,
      exportPDF,
      handleKnowledgeBaseToggle,
      toggleKbExpanded,
      getKbDocuments,
      isKbFullySelected,
      isKbPartiallySelected,
      toggleKbSelection,
      selectAllFiles,
      deselectAllFiles
    }
  }
}
</script>

<style>
html,
body {
  margin: 0;
  padding: 0;
  overflow: hidden;
  height: 100%;
  width: 100%;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}
</style>

<style scoped>
.chat-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
  box-sizing: border-box;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  min-height: 0;
}

.chat-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  flex-shrink: 0;
}

.chat-header h1 {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-icon {
  width: 36px;
  height: 36px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  border-radius: 50%;
}

.btn-primary {
  background: white;
  color: #667eea;
}

.btn-primary:hover {
  background: #f3f4f6;
  transform: translateY(-2px) scale(1.1);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px) scale(1.1);
}

.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover {
  background: #059669;
  transform: translateY(-2px) scale(1.1);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px;
  background: #f9fafb;
  min-height: 0;
}

.input-container {
  padding: 16px 20px;
  background: white;
  border-top: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex-shrink: 0;
}

.knowledge-base-selector {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.tree-selector-container {
  flex: 0 0 30%;
  max-width: 30%;
  position: relative;
}

.tree-selector-header {
  padding: 10px 14px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s ease;
}

.tree-selector-header:hover {
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.dropdown-icon {
  color: #6b7280;
  font-size: 12px;
}

.tree-selector-dropdown {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 0;
  right: 0;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
}

.tree-selector-actions {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.btn-tree {
  padding: 4px 10px;
  border: none;
  border-radius: 4px;
  background: #667eea;
  color: white;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-tree:hover {
  background: #5568d3;
  transform: translateY(-1px);
}

.tree-list {
  padding: 8px;
}

.tree-kb-item {
  margin-bottom: 4px;
}

.tree-kb-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.tree-kb-header:hover {
  background: #f3f4f6;
}

.tree-icon {
  font-size: 10px;
  color: #6b7280;
  width: 12px;
}

.tree-label {
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
}

.tree-documents {
  margin-left: 28px;
}

.tree-doc-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.tree-doc-item:hover {
  background: #f9fafb;
}

.tree-doc-label {
  font-size: 13px;
  color: #4b5563;
}

.input-container > textarea,
.input-container > button {
  /* 直接子元素样式 */
}

.input-container .input-row {
  display: flex;
  gap: 12px;
}

.input-container textarea {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  transition: all 0.2s ease;
  max-height: 120px;
}

.input-container textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.input-container button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 100px;
  flex-shrink: 0;
}

.input-container button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.input-container button:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}

.typing-indicator {
  display: flex;
  gap: 8px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #667eea;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: 0s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .chat-view {
    padding: 0;
  }
  
  .chat-header {
    padding: 12px 16px;
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
  }
  
  .btn {
    flex: 1;
  }
  
  .input-container {
    padding: 12px;
    flex-direction: column;
  }
  
  .input-container button {
    width: 100%;
  }
}
</style>