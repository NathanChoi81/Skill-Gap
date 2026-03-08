import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/me': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/resumes': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/skills': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/roles': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/jobs': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/plan': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/courses': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/dev': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
