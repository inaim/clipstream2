import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  // Ensure Vite always resolves to the single React/react-dom instance
  // installed in this project. This avoids runtime errors caused by
  // multiple React copies (Invalid hook call / useState of null).
  resolve: {
    alias: {
      react: resolve(__dirname, 'node_modules/react'),
      'react-dom': resolve(__dirname, 'node_modules/react-dom')
    }
  },
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:8080',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  define: {
    __API_BASE_URL__: JSON.stringify(
      process.env.VITE_API_BASE_URL || 'http://localhost:8080'
    ),
  },
});