/**
 * PWA Utilities
 * Service worker registration and install prompt management
 */

import { isTelegramMiniApp } from './telegram'
import { getCacheConfig } from './twaCache'

export interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

let deferredPrompt: BeforeInstallPromptEvent | null = null

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) {
    console.log('Service Worker not supported')
    return null
  }

  const isTma = isTelegramMiniApp()
  const cacheConfig = getCacheConfig()

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
    })

    console.log('Service Worker registered:', registration.scope, isTma ? '(TMA mode)' : '(PWA mode)')

    setInterval(() => {
      registration.update()
    }, cacheConfig.updateCheckIntervalMs)

    if (!isTma && cacheConfig.enableOfflineFallback) {
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing

        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              console.log('New service worker available')

              if (window.confirm('A new version is available. Reload to update?')) {
                newWorker.postMessage({ type: 'SKIP_WAITING' })
                window.location.reload()
              }
            }
          })
        }
      })
    }

    return registration
  } catch (error) {
    console.error('Service Worker registration failed:', error)
    return null
  }
}

export async function unregisterServiceWorker(): Promise<boolean> {
  if (!('serviceWorker' in navigator)) {
    return false
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration()
    if (registration) {
      await registration.unregister()
      console.log('Service Worker unregistered')
      return true
    }
    return false
  } catch (error) {
    console.error('Service Worker unregister failed:', error)
    return false
  }
}

export function isPWA(): boolean {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as any).standalone === true ||
    document.referrer.includes('android-app://')
  )
}

export type Platform = 'ios' | 'android' | 'desktop-chrome' | 'desktop-edge' | 'desktop-other' | 'unknown'

export function detectPlatform(): Platform {
  const ua = navigator.userAgent

  const isIOS = /iPad|iPhone|iPod/.test(ua) && !(window as any).MSStream
  if (isIOS) return 'ios'

  const isAndroid = /Android/.test(ua)
  if (isAndroid) return 'android'

  const isChrome = /Chrome/.test(ua) && !/Edge|Edg/.test(ua)
  const isEdge = /Edge|Edg/.test(ua)

  if (isChrome) return 'desktop-chrome'
  if (isEdge) return 'desktop-edge'
  return 'desktop-other'
}

export function canShowInstallPrompt(): boolean {
  if (isPWA()) return false
  if (isTelegramMiniApp()) return false
  if (wasDismissedRecently()) return false
  const platform = detectPlatform()
  if (platform === 'ios') return true
  return canInstall()
}

function wasDismissedRecently(): boolean {
  const dismissed = localStorage.getItem('pwa-modal-dismissed')
  if (!dismissed) return false
  const daysSince = (Date.now() - parseInt(dismissed, 10)) / (1000 * 60 * 60 * 24)
  return daysSince < 7
}

export function canInstall(): boolean {
  return deferredPrompt !== null
}

export function isIOSNotInstalled(): boolean {
  const ua = navigator.userAgent
  const isIOS = /iPad|iPhone|iPod/.test(ua) && !(window as any).MSStream
  return isIOS && !isPWA()
}

export function initInstallPrompt(): void {
  if (isTelegramMiniApp()) {
    return
  }

  window.addEventListener('beforeinstallprompt', (e: Event) => {
    e.preventDefault()
    deferredPrompt = e as BeforeInstallPromptEvent
    console.log('PWA install prompt available')
    window.dispatchEvent(new CustomEvent('pwa-install-available'))
  })

  window.addEventListener('appinstalled', () => {
    console.log('PWA installed successfully')
    deferredPrompt = null

    if (typeof gtag !== 'undefined') {
      gtag('event', 'pwa_install', {
        event_category: 'engagement',
        event_label: 'PWA Installed',
      })
    }
  })
}

export async function showInstallPrompt(): Promise<'accepted' | 'dismissed' | 'unavailable'> {
  if (!deferredPrompt) {
    console.log('Install prompt not available')
    return 'unavailable'
  }

  try {
    await deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    console.log('Install prompt outcome:', outcome)
    deferredPrompt = null
    return outcome
  } catch (error) {
    console.error('Install prompt error:', error)
    return 'unavailable'
  }
}

export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    console.log('Notifications not supported')
    return 'denied'
  }

  if (Notification.permission === 'granted') {
    return 'granted'
  }

  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission()
    return permission
  }

  return Notification.permission
}

export async function subscribeToPushNotifications(
  registration: ServiceWorkerRegistration
): Promise<PushSubscription | null> {
  try {
    const permission = await requestNotificationPermission()

    if (permission !== 'granted') {
      console.log('Notification permission denied')
      return null
    }

    const vapidPublicKey = import.meta.env.VITE_VAPID_PUBLIC_KEY
    if (!vapidPublicKey) {
      console.error('VAPID public key not configured')
      return null
    }

    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublicKey) as BufferSource,
    })

    console.log('Push subscription:', subscription)
    await sendSubscriptionToBackend(subscription)

    return subscription
  } catch (error) {
    console.error('Push subscription error:', error)
    return null
  }
}

async function sendSubscriptionToBackend(subscription: PushSubscription): Promise<void> {
  try {
    const response = await fetch('/api/notifications/subscribe-push', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(subscription.toJSON()),
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error(`Failed to send subscription: ${response.statusText}`)
    }

    console.log('Push subscription sent to backend successfully')
  } catch (error) {
    console.error('Failed to send push subscription to backend:', error)
    throw error
  }
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/')

  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }

  return outputArray
}

export function isOnline(): boolean {
  return navigator.onLine
}

export function onNetworkChange(callback: (isOnline: boolean) => void): () => void {
  const handleOnline = () => callback(true)
  const handleOffline = () => callback(false)

  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)

  return () => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  }
}

export async function getBatteryStatus(): Promise<{
  level: number
  charging: boolean
} | null> {
  if (!('getBattery' in navigator)) {
    return null
  }

  try {
    const battery = await (navigator as any).getBattery()
    return {
      level: battery.level,
      charging: battery.charging,
    }
  } catch (error) {
    console.error('Battery API error:', error)
    return null
  }
}

export async function shouldReduceActivity(): Promise<boolean> {
  const battery = await getBatteryStatus()

  if (!battery) {
    return false
  }

  return battery.level < 0.2 && !battery.charging
}

declare global {
  function gtag(...args: any[]): void
}
