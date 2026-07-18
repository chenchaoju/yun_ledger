import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    base: '/mobile/',
    plugins: [vue()],
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            vue: ['vue', 'vue-router', 'pinia'],
            element: ['element-plus', '@element-plus/icons-vue'],
            charts: ['echarts']
          }
        }
      }
    },
    server: {
      host: '0.0.0.0',
      port: 8023,
      proxy: {
        '/mobile-api': {
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8024',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/mobile-api/, '')
        },
        '/api': {
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8024',
          changeOrigin: true
        }
      }
    }
  }
})
