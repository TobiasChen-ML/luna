/**
 * Telegram Notification Service
 *
 * Uses Telegram Bot API to send notifications to users
 * inside Telegram Mini App environment.
 *
 * Backend requirements:
 * - POST /api/notifications/telegram/register - Register user's chat_id
 * - POST /api/notifications/telegram/unregister - Unregister user
 */

import { api } from './api'
import { isTelegramMiniApp, getTelegramUser, getTelegramInitData } from '@/utils/telegram'
import type { NotificationChannel } from './notificationChannel'

class TelegramNotificationService implements NotificationChannel {
  readonly name = 'telegram' as const
  private subscribed = false

  isSupported(): boolean {
    return isTelegramMiniApp()
  }

  getPermissionStatus(): 'granted' | 'denied' | 'default' {
    if (!isTelegramMiniApp()) return 'denied'
    return this.subscribed ? 'granted' : 'default'
  }

  async requestPermission(): Promise<boolean> {
    if (!isTelegramMiniApp()) return false
    return true
  }

  async subscribe(): Promise<boolean> {
    if (!isTelegramMiniApp()) return false

    try {
      const initData = getTelegramInitData()
      const telegramUser = getTelegramUser()

      if (!telegramUser) {
        console.warn('Telegram user not available')
        return false
      }

      await api.post('/api/notifications/telegram/register', {
        telegram_user_id: telegramUser.id,
        username: telegramUser.username,
        first_name: telegramUser.first_name,
        last_name: telegramUser.last_name,
        init_data: initData,
      })

      this.subscribed = true
      console.log('Telegram notifications registered')
      return true
    } catch (error) {
      console.error('Failed to register Telegram notifications:', error)
      return false
    }
  }

  async unsubscribe(): Promise<boolean> {
    if (!isTelegramMiniApp()) return false

    try {
      await api.post('/api/notifications/telegram/unregister')
      this.subscribed = false
      console.log('Telegram notifications unregistered')
      return true
    } catch (error) {
      console.error('Failed to unregister Telegram notifications:', error)
      return false
    }
  }

  async isSubscribed(): Promise<boolean> {
    if (!isTelegramMiniApp()) return false

    try {
      const response = await api.get('/api/notifications/telegram/status')
      this.subscribed = response.data.subscribed === true
      return this.subscribed
    } catch {
      return this.subscribed
    }
  }
}

export const telegramNotificationService = new TelegramNotificationService()
