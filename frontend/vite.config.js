import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    // 允许所有外部域名访问，这是远程访问成功的关键
    allowedHosts: 'all'
  }
})