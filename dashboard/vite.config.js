import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

export default defineConfig({
  plugins: [
    react(),
    // Serve parent-directory output/ files during dev
    {
      name: 'serve-parent-output',
      configureServer(server) {
        server.middlewares.use('/output', (req, res, next) => {
          const filePath = path.resolve(import.meta.dirname, '..', 'output', req.url.replace(/^\//, ''))
          if (fs.existsSync(filePath)) {
            res.setHeader('Content-Type', 'application/json')
            res.end(fs.readFileSync(filePath))
          } else {
            res.statusCode = 404
            res.end('Not found')
          }
        })
      },
    },
  ],
})
