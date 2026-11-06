import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  publicDir: 'public',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          echarts: ['echarts/core', 'echarts/charts', 'echarts/components', 'echarts/renderers'],
        },
      },
    },
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY ?? 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
