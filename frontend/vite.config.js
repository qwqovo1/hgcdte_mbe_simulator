import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // 允许局域网/穿透访问
    port: 5173,
    strictPort: true,
    allowedHosts: 'all', // 允许穿透软件的所有动态域名
    proxy: {
      // 关键：将前端以 /api 开头的请求转发到后端端口
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  }
})