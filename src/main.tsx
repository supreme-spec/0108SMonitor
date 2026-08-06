import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

if (typeof window !== 'undefined') {
  window.onerror = (message, source, lineno, colno, error) => {
    console.error('[GLOBAL ERROR]', message, 'at', source + ':' + lineno + ':' + colno, error)
    const el = document.createElement('pre')
    el.style.cssText = 'position:fixed;inset:0;z-index:99999;background:#000;color:#f44;padding:20px;font-size:14px;white-space:pre-wrap;overflow:auto;'
    el.textContent = '[GLOBAL ERROR]\n' + message + '\n' + (error && error.stack ? error.stack : '')
    document.body.appendChild(el)
  }
  window.addEventListener('unhandledrejection', (event) => {
    console.error('[UNHANDLED REJECTION]', event.reason)
    const el = document.createElement('pre')
    el.style.cssText = 'position:fixed;inset:0;z-index:99999;background:#000;color:#f44;padding:20px;font-size:14px;white-space:pre-wrap;overflow:auto;'
    el.textContent = '[UNHANDLED REJECTION]\n' + (event.reason instanceof Error ? event.reason.message + '\n' + event.reason.stack : String(event.reason))
    document.body.appendChild(el)
  })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
