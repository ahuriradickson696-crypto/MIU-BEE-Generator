$vite = @"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:5000',
      '/download': 'http://localhost:5000'
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
"@
[System.IO.File]::WriteAllText("$PWD\vite.config.js", $vite, [System.Text.UTF8Encoding]::new($false))
Get-Content vite.config.js