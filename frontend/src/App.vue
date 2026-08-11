<template>
  <div class="app-layout">
    <Sidebar />
    <div class="main-container">
      <Header />
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
import Header from './components/Header.vue'
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  background: #f3f4f6;
  min-height: 100vh;
  color: #1f2937;
}

#app {
  min-height: 100vh;
}

.app-layout {
  display: flex;
  min-height: 100vh;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  background: #f9fafb;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f3f4f6;
}

::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-content {
    padding: 0;
  }
}
</style>