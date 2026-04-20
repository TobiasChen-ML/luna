/**
 * External Link Handler
 *
 * Platform-aware external link handling:
 * - PWA: Uses window.open
 * - TMA: Uses Telegram's openLink API
 */

import { isTelegramMiniApp, getTelegramWebApp } from '@/utils/telegram'

export interface OpenLinkOptions {
  tryInstantView?: boolean
}

export function openExternalUrl(url: string, options: OpenLinkOptions = {}): void {
  if (isTelegramMiniApp()) {
    const webApp = getTelegramWebApp()
    if (webApp) {
      webApp.openLink(url, { try_instant_view: options.tryInstantView })
      return
    }
  }

  window.open(url, '_blank', 'noopener,noreferrer')
}

export function openTelegramLink(url: string): void {
  if (isTelegramMiniApp()) {
    const webApp = getTelegramWebApp()
    if (webApp) {
      webApp.openTelegramLink(url)
      return
    }
  }

  window.open(url, '_blank', 'noopener,noreferrer')
}

export function openShareLink(text: string, url?: string): void {
  const shareUrl = url || window.location.href
  
  if (isTelegramMiniApp()) {
    const webApp = getTelegramWebApp()
    if (webApp) {
      const telegramShareUrl = `https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(text)}`
      webApp.openTelegramLink(telegramShareUrl)
      return
    }
  }

  if (navigator.share) {
    navigator.share({ title: text, url: shareUrl }).catch(() => {
      copyToClipboard(shareUrl)
    })
  } else {
    copyToClipboard(shareUrl)
  }
}

export function copyToClipboard(text: string): Promise<boolean> {
  return new Promise((resolve) => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => resolve(true)).catch(() => resolve(false))
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.select()
      try {
        document.execCommand('copy')
        resolve(true)
      } catch {
        resolve(false)
      } finally {
        document.body.removeChild(textarea)
      }
    }
  })
}
