import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3030,
    proxy: {
      '/api': {
        target: 'http://localhost:7396',
        changeOrigin: true,
      },
      '/images': {
        target: 'http://localhost:7396',
        changeOrigin: true,
      },
    },
  },
})
