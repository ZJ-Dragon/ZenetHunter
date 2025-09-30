import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

// Bootstrap React 18 app into #root (see index.html)
const container = document.getElementById('root') as HTMLElement
if (!container) {
  throw new Error('Root container #root not found. Ensure index.html contains <div id="root"></div>.')
}

createRoot(container).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
