<template>
  <div :class="['message', message.role]">
    <div class="message-body">
      <!-- 思考过程（仅助手消息显示） -->
      <div v-if="message.role === 'assistant' && (message.thinking || message.isThinking)" class="thinking-section">
        <div class="thinking-header" @click="toggleThinking">
          <span class="thinking-icon">
            <span v-if="message.isThinking" class="spinner"></span>
            <span v-else>💭</span>
          </span>
          <span class="thinking-title">思考过程</span>
          <span class="thinking-toggle">{{ showThinking ? '▼' : '▶' }}</span>
        </div>
        
        <div v-show="showThinking" class="thinking-content">
          <div v-if="message.isThinking" class="thinking-loading">
            <div class="spinner-large"></div>
            <p>正在思考中...</p>
          </div>
          <div v-else-if="message.thinking" class="thinking-text" v-html="renderedThinking"></div>
          <div v-else class="thinking-empty">暂无思考过程</div>
        </div>
      </div>
      
      <!-- 消息内容 -->
      <div class="message-content" v-html="renderedContent"></div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { marked } from 'marked'
import mermaid from 'mermaid'
import * as echarts from 'echarts'
import hljs from 'highlight.js'
import DOMPurify from 'dompurify'

export default {
  name: 'ChatMessage',
  props: {
    message: {
      type: Object,
      required: true
    }
  },
  setup(props) {
    const showThinking = ref(false)
    
    // 初始化 Mermaid
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default'
    })

    // 切换思考过程显示
    const toggleThinking = () => {
      showThinking.value = !showThinking.value
    }

    // 渲染思考过程
    const renderedThinking = computed(() => {
      if (!props.message.thinking) return ''
      
      // 使用 marked 渲染 Markdown 格式的思考过程
      let html = marked(props.message.thinking)
      html = DOMPurify.sanitize(html)
      return html
    })

    // 渲染 Markdown 内容
    const renderedContent = computed(() => {
      if (!props.message.content) return ''

      // 配置 marked
      marked.setOptions({
        highlight: function(code, lang) {
          if (lang && hljs.getLanguage(lang)) {
            try {
              return hljs.highlight(code, { language: lang }).value
            } catch (e) {
              console.error('Highlight error:', e)
            }
          }
          return code
        },
        breaks: true,
        gfm: true
      })

      // 渲染 Markdown
      let html = marked(props.message.content)

      // 清理 HTML（防止 XSS）
      html = DOMPurify.sanitize(html, {
        ADD_TAGS: ['mermaid', 'echarts'],
        ADD_ATTR: ['class', 'id', 'style']
      })

      return html
    })

    // 渲染图表
    const renderCharts = async () => {
      await nextTick()

      // 渲染 Mermaid 图表
      const mermaidElements = document.querySelectorAll('.message-content pre code.language-mermaid')
      
      for (let i = 0; i < mermaidElements.length; i++) {
        const element = mermaidElements[i]
        
        // 跳过已经渲染的元素
        if (element.getAttribute('data-rendered')) continue
        
        const code = element.textContent

        try {
          const id = `mermaid-${Date.now()}-${i}`
          const { svg } = await mermaid.render(id, code)

          // 创建容器
          const container = document.createElement('div')
          container.className = 'mermaid-container'
          container.innerHTML = svg

          // 标记已渲染
          element.setAttribute('data-rendered', 'true')

          // 替换原始元素
          const pre = element.parentElement
          pre.parentElement.replaceChild(container, pre)
        } catch (error) {
          console.error('Mermaid render error:', error)
        }
      }

      // 渲染 ECharts 图表
      const echartsElements = document.querySelectorAll('.message-content pre code.language-echarts')
      
      for (let i = 0; i < echartsElements.length; i++) {
        const element = echartsElements[i]
        
        // 跳过已经渲染的元素
        if (element.getAttribute('data-rendered')) continue
        
        const code = element.textContent

        try {
          const config = JSON.parse(code)

          // 创建容器
          const container = document.createElement('div')
          container.className = 'chart-container'
          container.style.width = '100%'
          container.style.height = '400px'

          // 标记已渲染
          element.setAttribute('data-rendered', 'true')

          // 替换原始元素
          const pre = element.parentElement
          pre.parentElement.replaceChild(container, pre)

          // 渲染图表
          const chart = echarts.init(container)
          chart.setOption(config)
          
          // 响应式调整
          window.addEventListener('resize', () => {
            chart.resize()
          })
        } catch (error) {
          console.error('ECharts render error:', error)
        }
      }
    }

    // 监听消息内容变化，自动渲染图表
    const stopWatcher = watch(() => props.message.content, () => {
      renderCharts()
    })

    onMounted(() => {
      renderCharts()
    })
    
    // 清理监听器
    onUnmounted(() => {
      stopWatcher()
    })

    return {
      showThinking,
      toggleThinking,
      renderedThinking,
      renderedContent
    }
  }
}
</script>

<style scoped>
.message {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  padding: 20px;
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInUp 0.4s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  background: #f3f4f6;
  color: #1f2937;
  margin-left: 60px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.message.user:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.message.assistant {
  background: white;
  color: #1f2937;
  margin-right: 60px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.message.assistant:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.message-body {
  flex: 1;
  min-width: 0;
}

/* 思考过程样式 */
.thinking-section {
  margin-bottom: 20px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  background: #fafafa;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
  border-bottom: 1px solid transparent;
}

.thinking-header:hover {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  border-bottom-color: #e5e7eb;
}

.thinking-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
}

.thinking-title {
  flex: 1;
  font-weight: 600;
  color: #374151;
  font-size: 15px;
}

.thinking-toggle {
  color: #6b7280;
  font-size: 14px;
  transition: transform 0.3s ease;
}

.thinking-content {
  padding: 20px;
  border-top: 1px solid #e5e7eb;
  max-height: 400px;
  overflow-y: auto;
  background: white;
}

.thinking-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #6b7280;
}

.thinking-text {
  line-height: 1.8;
  color: #6b7280;
  font-size: 14px;
}

.thinking-text p {
  margin: 10px 0;
}

.thinking-text strong {
  color: #4b5563;
  font-weight: 600;
}

.thinking-text code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #6b7280;
}

.thinking-empty {
  color: #9ca3af;
  text-align: center;
  padding: 20px;
  font-size: 14px;
}

/* 转圈动画 */
.spinner {
  display: inline-block;
  width: 18px;
  height: 18px;
  border: 2px solid #d1d5db;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-large {
  display: inline-block;
  width: 56px;
  height: 56px;
  border: 4px solid #e5e7eb;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 消息内容样式 */
.message-content {
  line-height: 1.8;
  word-wrap: break-word;
  overflow-wrap: break-word;
  font-size: 15px;
  color: #1f2937;
}

.message-content pre {
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
  border: 1px solid #e5e7eb;
}

.message-content code {
  background: #f3f4f6;
  padding: 3px 8px;
  border-radius: 4px;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
  font-size: 14px;
  color: #6366f1;
}

.message-content pre code {
  background: none;
  padding: 0;
  color: #1f2937;
}

.message-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.message-content th,
.message-content td {
  border: 1px solid #e5e7eb;
  padding: 12px 16px;
  text-align: left;
}

.message-content th {
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  font-weight: 600;
  color: #374151;
}

.message-content tr:hover {
  background: #f9fafb;
}

.message-content ul,
.message-content ol {
  margin: 12px 0;
  padding-left: 28px;
}

.message-content li {
  margin: 6px 0;
  line-height: 1.8;
}

.message-content h1,
.message-content h2,
.message-content h3,
.message-content h4,
.message-content h5,
.message-content h6 {
  margin: 20px 0 12px 0;
  font-weight: 600;
  color: #111827;
}

.message-content h1 {
  font-size: 26px;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 10px;
}

.message-content h2 {
  font-size: 22px;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}

.message-content h3 {
  font-size: 18px;
}

.message-content h4 {
  font-size: 16px;
}

.message-content blockquote {
  border-left: 4px solid #6366f1;
  padding-left: 20px;
  margin: 12px 0;
  color: #6b7280;
  background: #f9fafb;
  border-radius: 0 8px 8px 0;
  padding: 12px 20px;
}

.message-content img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 12px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-content a {
  color: #6366f1;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.message-content a:hover {
  color: #4f46e5;
  text-decoration: underline;
}

/* Mermaid 和 ECharts 容器 */
.mermaid-container,
.chart-container {
  margin: 20px 0;
  text-align: center;
  padding: 20px;
  background: #f9fafb;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.mermaid-container svg,
.chart-container canvas {
  max-width: 100%;
  height: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .message.user {
    margin-left: 0;
  }
  
  .message.assistant {
    margin-right: 0;
  }
  
  .message-avatar {
    width: 40px;
    height: 40px;
    font-size: 28px;
  }
  
  .thinking-content {
    max-height: 300px;
  }
  
  .message {
    padding: 16px;
    gap: 12px;
  }
}
</style>