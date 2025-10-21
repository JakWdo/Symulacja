import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // Public directory - assets kopiowane do dist/
  publicDir: 'public',
  build: {
    // Output directory
    outDir: 'dist',
    // Copy public assets to root of dist/
    copyPublicDir: true,
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target:
          process.env.VITE_API_URL && process.env.VITE_API_URL.trim().length > 0
            ? process.env.VITE_API_URL
            : 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
