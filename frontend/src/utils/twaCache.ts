/**
 * TMA (Telegram Mini App) Cache Configuration
 *
 * Telegram WebView has different caching requirements:
 * - Shorter API cache TTL to avoid auth token issues
 * - No offline fallback (TMA has its own lifecycle)
 * - No background sync (managed by Telegram)
 */

import { isTelegramMiniApp } from './telegram'

export interface CacheConfig {
  apiMaxAgeSeconds: number
  imageMaxAgeSeconds: number
  staticMaxAgeSeconds: number
  enableOfflineFallback: boolean
  enableBackgroundSync: boolean
  updateCheckIntervalMs: number
}

export const PWA_CACHE_CONFIG: CacheConfig = {
  apiMaxAgeSeconds: 60 * 60 * 24,
  imageMaxAgeSeconds: 60 * 60 * 24 * 30,
  staticMaxAgeSeconds: 60 * 60 * 24 * 365,
  enableOfflineFallback: true,
  enableBackgroundSync: true,
  updateCheckIntervalMs: 60 * 60 * 1000,
}

export const TMA_CACHE_CONFIG: CacheConfig = {
  apiMaxAgeSeconds: 60,
  imageMaxAgeSeconds: 60 * 60 * 24 * 30,
  staticMaxAgeSeconds: 60 * 60 * 24 * 365,
  enableOfflineFallback: false,
  enableBackgroundSync: false,
  updateCheckIntervalMs: 5 * 60 * 1000,
}

export function getCacheConfig(): CacheConfig {
  return isTelegramMiniApp() ? TMA_CACHE_CONFIG : PWA_CACHE_CONFIG
}
