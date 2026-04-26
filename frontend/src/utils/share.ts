/**
 * Share Utility
 *
 * Platform-aware sharing:
 * - PWA: Uses Web Share API with clipboard fallback
 * - TMA: Uses Telegram's share mechanism
 */

import { isTelegramMiniApp, getTelegramWebApp } from '@/utils/telegram'
import { copyToClipboard } from './externalLink'
import { rewardsService } from '@/services/rewardsService'

export interface ShareOptions {
  title?: string
  text?: string
  url?: string
}

export interface ShareRewardClaimResult {
  success: boolean
  granted: boolean
  reason: string
  reward_amount: number
  new_balance: number
}

export async function share(options: ShareOptions): Promise<boolean> {
  const shareUrl = options.url || window.location.href
  const shareText = options.text || options.title || ''

  if (isTelegramMiniApp()) {
    const webApp = getTelegramWebApp()
    if (webApp) {
      const telegramShareUrl = `https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(shareText)}`
      webApp.openTelegramLink(telegramShareUrl)
      return true
    }
  }

  if (navigator.share) {
    try {
      await navigator.share({
        title: options.title,
        text: options.text,
        url: shareUrl,
      })
      return true
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        return false
      }
      return copyToClipboard(shareUrl)
    }
  }

  return copyToClipboard(shareUrl)
}

export function shareCharacter(characterName: string, characterSlug: string, category: string = 'ai-girlfriend'): Promise<boolean> {
  const url = `${window.location.origin}/${category}/${characterSlug}`
  return share({
    title: `Chat with ${characterName} on RoxyClub`,
    text: `Come chat with ${characterName} - ${window.location.hostname}`,
    url,
  })
}

export function shareChat(characterName: string, sessionId: string): Promise<boolean> {
  return share({
    title: `Chat with ${characterName}`,
    text: `Join my conversation with ${characterName} on RoxyClub`,
  })
}

export async function claimShareReward(
  shareKey: string,
  channel: string,
  metadata?: Record<string, unknown>
): Promise<ShareRewardClaimResult | null> {
  try {
    return await rewardsService.claimShareReward({
      share_key: shareKey,
      channel,
      metadata,
    })
  } catch (error) {
    console.error('Failed to claim share reward:', error)
    return null
  }
}
