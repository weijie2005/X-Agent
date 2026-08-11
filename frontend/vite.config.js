import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  // 加载 .env 文件
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [vue()],
    server: {
      host: env.FRONTEND_HOST || '0.0.0.0',
      port: parseInt(env.FRONTEND_PORT || '3000'),
      proxy: {
        '/api': {
          target: `http://localhost:${env.BACKEND_PORT || '8080'}`,
          changeOrigin: true
        }
      }
    }
  }
})