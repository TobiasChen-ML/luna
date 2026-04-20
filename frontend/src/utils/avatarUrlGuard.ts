const env = import.meta.env as Record<string, string | undefined>;
const configuredCdnDomains = (env.VITE_AVATAR_CDN_ALLOWLIST || env.VITE_CDN_ALLOWLIST || env.VITE_ALLOWED_CDN_DOMAINS || '')
  .split(',')
  .map((value) => value.trim().toLowerCase())
  .filter((value) => value.length > 0);

export function isAllowedAvatarUrl(url: string | null | undefined, cdnAllowlist: readonly string[] = configuredCdnDomains): boolean {
  if (!url) return false;

  const trimmed = url.trim();
  if (!trimmed) return false;

  try {
    const base = typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
    const parsed = new URL(trimmed, base);
    const protocol = parsed.protocol.toLowerCase();

    if (protocol !== 'http:' && protocol !== 'https:') {
      return false;
    }

    if (typeof window !== 'undefined' && parsed.origin === window.location.origin) {
      return true;
    }

    // If no allowlist is configured, allow any http(s) remote host.
    // This keeps avatar rendering functional in local/dev environments.
    if (cdnAllowlist.length === 0) {
      return true;
    }

    const host = parsed.hostname.toLowerCase();
    return cdnAllowlist.some((domain) => host === domain || host.endsWith(`.${domain}`));
  } catch {
    return false;
  }
}

export function getSafeAvatarUrl(url: string | null | undefined, fallbackUrl?: string): string | undefined {
  if (!url || !url.trim()) {
    return undefined;
  }

  const trimmed = url.trim();
  return isAllowedAvatarUrl(trimmed) ? trimmed : fallbackUrl;
}
