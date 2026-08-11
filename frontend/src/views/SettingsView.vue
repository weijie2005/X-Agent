<template>
  <div class="settings-view">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>

    <div class="settings-section">
      <h3>基本设置</h3>
      <div class="setting-item">
        <label>主题</label>
        <select>
          <option>浅色</option>
          <option>深色</option>
          <option>自动</option>
        </select>
      </div>

      <div class="setting-item">
        <label>语言</label>
        <select>
          <option>中文</option>
          <option>英文</option>
        </select>
      </div>
    </div>

    <div class="settings-section">
      <h3>模型设置</h3>
      <div class="setting-item">
        <label>默认模型</label>
        <select>
          <option>DeepSeek</option>
          <option>GPT-4</option>
          <option>Claude</option>
        </select>
      </div>

      <div class="setting-item">
        <label>温度</label>
        <input type="range" min="0" max="1" step="0.1" value="0.7" />
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.settings-view {
  padding: 32px;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.settings-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.settings-section h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid #e5e7eb;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.setting-item label {
  font-size: 15px;
  font-weight: 500;
  color: #374151;
}

.setting-item select,
.setting-item input {
  padding: 8px 12px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s ease;
}

.setting-item select:focus,
.setting-item input:focus {
  outline: none;
  border-color: #667eea;
}

@media (max-width: 768px) {
  .settings-view {
    padding: 16px;
  }

  .setting-item {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }

  .setting-item select,
  .setting-item input {
    width: 100%;
  }
}
</style>