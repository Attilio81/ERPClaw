import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    proxy: {
      '/agents': 'http://localhost:8000',
      '/config': 'http://localhost:8000',
      '/chat':   'http://localhost:8000',
      '/shop':   'http://localhost:8000',
      '/admin':  'http://localhost:8000',
    },
  },
})
