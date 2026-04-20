/**
 * Notification Channel Interface
 *
 * Abstracts notification delivery across different platforms:
 * - Web Push (PWA)
 * - Telegram Bot (TMA)
 */

export interface NotificationOptions {
  title: string
  body: string
  icon?: string
  badge?: string
  tag?: string
  data?: Record<string, unknown>
  requireInteraction?: boolean
}

export interface NotificationChannel {
  readonly name: 'webpush' | 'telegram'
  isSupported(): boolean
  requestPermission(): Promise<boolean>
  getPermissionStatus(): NotificationPermission | 'granted' | 'denied' | 'default'
  subscribe(): Promise<boolean>
  unsubscribe(): Promise<boolean>
  isSubscribed(): Promise<boolean>
}

export type NotificationChannelType = NotificationChannel['name']
