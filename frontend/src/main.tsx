import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './i18n'
import App from './App.tsx'
import { registerServiceWorker, initInstallPrompt } from './utils/pwa'
import { isTelegramMiniApp } from './utils/telegram'

const isDev = import.meta.env.DEV

if (!isDev && 'serviceWorker' in navigator) {
  registerServiceWorker().then((registration) => {
    if (registration) {
      console.log('✅ Service Worker registered successfully')
    }
  }).catch((error) => {
    console.error('❌ Service Worker registration failed:', error)
  })

  if (!isTelegramMiniApp()) {
    initInstallPrompt()
  }
}

createRoot(document.getElementById('root')!).render(
  isDev ? (
    <StrictMode>
      <App />
    </StrictMode>
  ) : (
    <App />
  ),
)
