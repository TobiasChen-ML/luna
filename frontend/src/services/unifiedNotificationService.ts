/**
 * Unified Notification Service
 *
 * Provides a platform-aware notification interface that works for both:
 * - PWA: Web Push notifications via Service Worker
 * - TMA: Telegram Bot notifications
 */

import { isTelegramMiniApp } from '@/utils/telegram'
import { registerServiceWorker, subscribeToPushNotifications, requestNotificationPermission } from '@/utils/pwa'
import { telegramNotificationService } from './telegramNotificationService'
import type { NotificationChannel } from './notificationChannel'

class UnifiedNotificationService {
  private registration: ServiceWorkerRegistration | null = null

  async initialize(): Promise<void> {
    if (isTelegramMiniApp()) {
      console.log('[Notifications] TMA mode - using Telegram notifications')
      return
    }

    console.log('[Notifications] PWA mode - using Web Push')
    const reg = await registerServiceWorker()
    if (reg) {
      this.registration = reg
    }
  }

  async enable(): Promise<boolean> {
    if (isTelegramMiniApp()) {
      return telegramNotificationService.subscribe()
    }

    if (!this.registration) {
      await this.initialize()
    }

    if (this.registration) {
      const permission = await requestNotificationPermission()
      if (permission !== 'granted') {
        console.warn('[Notifications] Permission not granted')
        return false
      }
      const subscription = await subscribeToPushNotifications(this.registration)
      return !!subscription
    }

    return false
  }

  async disable(): Promise<boolean> {
    if (isTelegramMiniApp()) {
      return telegramNotificationService.unsubscribe()
    }

    return false
  }

  async isEnabled(): Promise<boolean> {
    if (isTelegramMiniApp()) {
      return telegramNotificationService.isSubscribed()
    }

    if (!this.registration) {
      return false
    }

    const subscription = await this.registration.pushManager.getSubscription()
    return !!subscription
  }

  getChannel(): NotificationChannel | null {
    if (isTelegramMiniApp()) {
      return telegramNotificationService
    }
    return null
  }
}

export const unifiedNotificationService = new UnifiedNotificationService()
