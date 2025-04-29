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
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: '',
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        format: 'umd',
        entryFileNames: '[name].[hash].js',
        chunkFileNames: '[name].[hash].js',
        assetFileNames: '[name].[hash].[ext]'
      }
    }
  }
})
