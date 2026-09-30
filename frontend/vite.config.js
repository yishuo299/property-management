import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // Django 的 STATIC_URL 为 /static/，构建产物由 Django 托管，必须用绝对前缀
  base: '/static/',
  build: {
    outDir: '../backend/static',
    emptyOutDir: true
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8004', changeOrigin: true },
      '/media': { target: 'http://localhost:8004', changeOrigin: true }
    }
  }
})
