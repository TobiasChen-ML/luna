import type { Character } from '@/types';

const CATEGORY_PREFIX: Record<string, string> = {
  anime: 'ai-anime',
  guys: 'ai-boyfriend',
  girls: 'ai-girlfriend',
};

/**
 * Returns the SEO-friendly chat URL for a character.
 * Falls back to /chat?character=<id> if no slug is available.
 */
export function toChatUrl(character: Pick<Character, 'id' | 'slug' | 'top_category'>): string {
  if (character.slug) {
    const prefix = CATEGORY_PREFIX[character.top_category ?? 'girls'] ?? 'ai-girlfriend';
    return `/${prefix}/${character.slug}`;
  }
  return `/chat?character=${character.id}`;
}
