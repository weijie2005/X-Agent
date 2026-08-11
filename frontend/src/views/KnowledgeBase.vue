<template>
  <div class="knowledge-base">
    <div class="page-header">
      <h1>知识库管理</h1>
      <button class="btn-primary" @click="showCreateDialog = true">
        创建知识库
      </button>
    </div>

    <div class="kb-list">
      <div v-if="loading" class="loading">加载中...</div>
      
      <div v-else-if="knowledgeBases.length === 0" class="empty-state">
        <p>暂无知识库，请创建一个知识库</p>
      </div>
      
      <div v-else class="kb-grid">
        <div v-for="kb in knowledgeBases" :key="kb.id" class="kb-card">
          <div class="kb-header">
            <h3>{{ kb.name }}</h3>
            <span class="kb-status" :class="{ active: kb.is_active }">
              {{ kb.is_active ? '活跃' : '停用' }}
            </span>
          </div>
          
          <p class="kb-description">{{ kb.description || '暂无描述' }}</p>
          
          <div class="kb-stats">
            <span>文档数量: {{ kb.document_count }}</span>
            <span>创建时间: {{ formatDate(kb.created_at) }}</span>
          </div>
          
          <div class="kb-actions">
            <button class="btn-secondary" @click="selectKnowledgeBase(kb)">
              查看文档
            </button>
            <button class="btn-danger" @click="deleteKnowledgeBase(kb.id)">
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedKB" class="document-section">
      <div class="section-header">
        <h2>{{ selectedKB.name }} - 文档列表</h2>
        <div class="upload-section">
          <input type="file" @change="handleFileSelect" accept=".pdf,.txt,.doc,.docx,.xls,.xlsx" />
          <button class="btn-primary" @click="uploadDocument" :disabled="!selectedFile">
            上传文档
          </button>
        </div>
      </div>

      <div class="document-list">
        <div v-if="documents.length === 0" class="empty-state">
          <p>暂无文档，请上传文档</p>
        </div>
        
        <div v-else class="document-grid">
          <div v-for="doc in documents" :key="doc.id" class="document-card">
            <div class="doc-info">
              <h4>{{ doc.filename }}</h4>
              <p>文件大小: {{ formatFileSize(doc.file_size) }}</p>
              <p>切片数量: {{ doc.chunk_count }}</p>
              <p>
                状态: 
                <span :class="{ indexed: doc.is_indexed, 'not-indexed': !doc.is_indexed }">
                  {{ doc.is_indexed ? '已索引' : '索引中...' }}
                </span>
              </p>
              <p v-if="doc.indexing_error" class="error">
                错误: {{ doc.indexing_error }}
              </p>
            </div>
            
            <div class="doc-actions">
              <button class="btn-danger" @click="deleteDocument(doc.id)">
                删除
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="search-section">
        <h3>检索测试</h3>
        <div class="search-input">
          <input 
            v-model="searchQuery" 
            placeholder="输入查询内容" 
            @keyup.enter="searchKnowledgeBase"
          />
          <button class="btn-primary" @click="searchKnowledgeBase">
            检索
          </button>
        </div>
        
        <div v-if="searchResults.length > 0" class="search-results">
          <h4>检索结果:</h4>
          <div v-for="(result, index) in searchResults" :key="index" class="result-item">
            <div class="result-score">相关度: {{ (result.score * 100).toFixed(1) }}%</div>
            <div class="result-content">{{ result.content }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showCreateDialog" class="dialog-overlay" @click="showCreateDialog = false">
      <div class="dialog" @click.stop>
        <h2>创建知识库</h2>
        <form @submit.prevent="createKnowledgeBase">
          <div class="form-group">
            <label>知识库名称:</label>
            <input v-model="newKB.name" required placeholder="请输入知识库名称" />
          </div>
          
          <div class="form-group">
            <label>描述:</label>
            <textarea v-model="newKB.description" placeholder="请输入知识库描述"></textarea>
          </div>
          
          <div class="form-actions">
            <button type="button" class="btn-secondary" @click="showCreateDialog = false">
              取消
            </button>
            <button type="submit" class="btn-primary">
              创建
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const knowledgeBases = ref([])
const documents = ref([])
const selectedKB = ref(null)
const selectedFile = ref(null)
const searchQuery = ref('')
const searchResults = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const newKB = ref({
  name: '',
  description: ''
})

const loadKnowledgeBases = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/v1/knowledge-bases')
    knowledgeBases.value = response.data
  } catch (error) {
    console.error('Failed to load knowledge bases:', error)
    alert('加载知识库列表失败')
  } finally {
    loading.value = false
  }
}

const createKnowledgeBase = async () => {
  try {
    await axios.post('/api/v1/knowledge-bases', newKB.value)
    showCreateDialog.value = false
    newKB.value = { name: '', description: '' }
    await loadKnowledgeBases()
    alert('知识库创建成功')
  } catch (error) {
    console.error('Failed to create knowledge base:', error)
    alert('创建知识库失败: ' + (error.response?.data?.error || error.message))
  }
}

const deleteKnowledgeBase = async (kbId) => {
  if (!confirm('确定要删除这个知识库吗？')) {
    return
  }
  
  try {
    await axios.delete(`/api/v1/knowledge-bases/${kbId}`)
    await loadKnowledgeBases()
    if (selectedKB.value?.id === kbId) {
      selectedKB.value = null
      documents.value = []
    }
    alert('知识库删除成功')
  } catch (error) {
    console.error('Failed to delete knowledge base:', error)
    alert('删除知识库失败')
  }
}

const selectKnowledgeBase = async (kb) => {
  selectedKB.value = kb
  await loadDocuments(kb.id)
}

const loadDocuments = async (kbId) => {
  try {
    const response = await axios.get(`/api/v1/knowledge-bases/${kbId}/documents`)
    documents.value = response.data
  } catch (error) {
    console.error('Failed to load documents:', error)
    alert('加载文档列表失败')
  }
}

const handleFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
}

const uploadDocument = async () => {
  if (!selectedFile.value || !selectedKB.value) {
    return
  }
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  
  try {
    await axios.post(
      `/api/v1/knowledge-bases/${selectedKB.value.id}/documents`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    
    selectedFile.value = null
    await loadDocuments(selectedKB.value.id)
    alert('文档上传成功')
  } catch (error) {
    console.error('Failed to upload document:', error)
    alert('文档上传失败: ' + (error.response?.data?.error || error.message))
  }
}

const deleteDocument = async (docId) => {
  if (!confirm('确定要删除这个文档吗？')) {
    return
  }
  
  try {
    await axios.delete(`/api/v1/knowledge-bases/${selectedKB.value.id}/documents/${docId}`)
    await loadDocuments(selectedKB.value.id)
    alert('文档删除成功')
  } catch (error) {
    console.error('Failed to delete document:', error)
    alert('删除文档失败')
  }
}

const searchKnowledgeBase = async () => {
  if (!searchQuery.value || !selectedKB.value) {
    return
  }
  
  try {
    const response = await axios.post(
      `/api/v1/knowledge-bases/${selectedKB.value.id}/search`,
      {
        query: searchQuery.value,
        limit: 5
      }
    )
    
    searchResults.value = response.data
  } catch (error) {
    console.error('Failed to search knowledge base:', error)
    alert('检索失败: ' + (error.response?.data?.error || error.message))
  }
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

onMounted(() => {
  loadKnowledgeBases()
})
</script>

<style scoped>
.knowledge-base {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0;
  color: #333;
}

.btn-primary {
  background: #667eea;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary:hover {
  background: #5a67d8;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background: #718096;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}

.btn-secondary:hover {
  background: #4a5568;
}

.btn-danger {
  background: #e53e3e;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}

.btn-danger:hover {
  background: #c53030;
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.kb-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.kb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.kb-header h3 {
  margin: 0;
  color: #333;
}

.kb-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: #e2e8f0;
  color: #718096;
}

.kb-status.active {
  background: #c6f6d5;
  color: #22543d;
}

.kb-description {
  color: #718096;
  margin-bottom: 15px;
  line-height: 1.5;
}

.kb-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
  font-size: 14px;
  color: #4a5568;
}

.kb-actions {
  display: flex;
  gap: 10px;
}

.document-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  margin: 0;
  color: #333;
}

.upload-section {
  display: flex;
  gap: 10px;
  align-items: center;
}

.upload-section input[type="file"] {
  padding: 5px;
}

.document-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.document-card {
  background: #f7fafc;
  border-radius: 6px;
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.doc-info h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.doc-info p {
  margin: 5px 0;
  font-size: 14px;
  color: #4a5568;
}

.indexed {
  color: #22543d;
  font-weight: 500;
}

.not-indexed {
  color: #d69e2e;
}

.error {
  color: #e53e3e;
  font-size: 12px;
}

.search-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.search-section h3 {
  margin: 0 0 15px 0;
  color: #333;
}

.search-input {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-input input {
  flex: 1;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 5px;
  font-size: 14px;
}

.search-results h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.result-item {
  background: #f7fafc;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 10px;
}

.result-score {
  font-size: 12px;
  color: #667eea;
  margin-bottom: 8px;
  font-weight: 500;
}

.result-content {
  color: #4a5568;
  line-height: 1.6;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 8px;
  padding: 30px;
  width: 500px;
  max-width: 90%;
}

.dialog h2 {
  margin: 0 0 20px 0;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #4a5568;
  font-weight: 500;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 5px;
  font-size: 14px;
}

.form-group textarea {
  min-height: 100px;
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.loading,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #718096;
}
</style>