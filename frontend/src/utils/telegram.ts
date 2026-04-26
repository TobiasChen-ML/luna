/**
 * Telegram Mini App (TMA) detection and SDK utility.
 *
 * All TMA-aware components should import from this module rather than
 * accessing window.Telegram directly.
 */

// ─── Type definitions ───────────────────────────────────────────────────────

export interface TelegramWebAppUser {
  id: number;
  is_bot?: boolean;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  is_premium?: boolean;
  photo_url?: string;
}

export interface TelegramThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
  header_bg_color?: string;
  accent_text_color?: string;
  section_bg_color?: string;
  section_header_text_color?: string;
  subtitle_text_color?: string;
  destructive_text_color?: string;
}

export interface TelegramSafeAreaInset {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

export interface TelegramBackButton {
  isVisible: boolean;
  show(): void;
  hide(): void;
  onClick(cb: () => void): void;
  offClick(cb: () => void): void;
}

export interface TelegramMainButton {
  text: string;
  color: string;
  textColor: string;
  isVisible: boolean;
  isProgressVisible: boolean;
  isActive: boolean;
  show(): void;
  hide(): void;
  enable(): void;
  disable(): void;
  showProgress(leaveActive?: boolean): void;
  hideProgress(): void;
  setText(text: string): void;
  onClick(cb: () => void): void;
  offClick(cb: () => void): void;
  setParams(params: {
    text?: string;
    color?: string;
    text_color?: string;
    is_active?: boolean;
    is_visible?: boolean;
  }): void;
}

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe: {
    user?: TelegramWebAppUser;
    chat_type?: string;
    chat_instance?: string;
    start_param?: string;
    auth_date: number;
    hash: string;
  };
  version: string;
  platform: string;
  colorScheme: 'light' | 'dark';
  themeParams: TelegramThemeParams;
  isExpanded: boolean;
  viewportHeight: number;
  viewportStableHeight: number;
  safeAreaInset?: TelegramSafeAreaInset;
  contentSafeAreaInset?: TelegramSafeAreaInset;
  BackButton: TelegramBackButton;
  MainButton: TelegramMainButton;
  ready(): void;
  expand(): void;
  close(): void;
  enableClosingConfirmation(): void;
  disableClosingConfirmation(): void;
  openInvoice(url: string, callback?: (status: 'paid' | 'cancelled' | 'failed' | 'pending') => void): void;
  openLink(url: string, options?: { try_instant_view?: boolean }): void;
  openTelegramLink(url: string): void;
  showAlert(message: string, callback?: () => void): void;
  showConfirm(message: string, callback: (ok: boolean) => void): void;
  onEvent(eventType: string, callback: () => void): void;
  offEvent(eventType: string, callback: () => void): void;
  sendData(data: string): void;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp;
    };
  }
}

// ─── Detection ───────────────────────────────────────────────────────────────

/**
 * Returns true if running inside a Telegram Mini App WebView.
 * Safe to call during SSR / before DOM is ready.
 */
export function isTelegramMiniApp(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof window.Telegram !== 'undefined' &&
    typeof window.Telegram.WebApp !== 'undefined' &&
    !!window.Telegram.WebApp.initData
  );
}

// ─── Accessors ───────────────────────────────────────────────────────────────

/** Typed accessor for window.Telegram.WebApp. Returns null outside TMA. */
export function getTelegramWebApp(): TelegramWebApp | null {
  if (!isTelegramMiniApp()) return null;
  return window.Telegram!.WebApp;
}

/** Returns the authenticated Telegram user from initDataUnsafe. */
export function getTelegramUser(): TelegramWebAppUser | null {
  return getTelegramWebApp()?.initDataUnsafe?.user ?? null;
}

/**
 * Returns the raw initData string used for backend HMAC verification.
 * Empty string when not in TMA context.
 */
export function getTelegramInitData(): string {
  return window.Telegram?.WebApp?.initData ?? '';
}

/** Returns the Telegram color scheme. Falls back to 'dark'. */
export function getTelegramColorScheme(): 'light' | 'dark' {
  return getTelegramWebApp()?.colorScheme ?? 'dark';
}

/** Returns Telegram themeParams, or an empty object outside TMA. */
export function getTelegramThemeParams(): TelegramThemeParams {
  return getTelegramWebApp()?.themeParams ?? {};
}

const TELEGRAM_MINI_APP_URL = (import.meta.env.VITE_TELEGRAM_MINI_APP_URL || '').trim();
const TELEGRAM_BOT_USERNAME = (import.meta.env.VITE_TELEGRAM_BOT_USERNAME || '').trim();
const TELEGRAM_MINI_APP_SHORT_NAME = (import.meta.env.VITE_TELEGRAM_MINI_APP_SHORT_NAME || '').trim();

function normalizeStartParam(startParam: string): string {
  return startParam.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 512);
}

export function buildTelegramMiniAppUrl(startParam = 'purchase'): string {
  const safeStartParam = normalizeStartParam(startParam);

  if (TELEGRAM_MINI_APP_URL) {
    const url = new URL(TELEGRAM_MINI_APP_URL);
    url.searchParams.set('startapp', safeStartParam);
    return url.toString();
  }

  if (TELEGRAM_BOT_USERNAME) {
    const username = TELEGRAM_BOT_USERNAME.replace(/^@/, '');
    if (TELEGRAM_MINI_APP_SHORT_NAME) {
      return `https://t.me/${username}/${TELEGRAM_MINI_APP_SHORT_NAME}?startapp=${encodeURIComponent(safeStartParam)}`;
    }
    return `https://t.me/${username}?start=${encodeURIComponent(safeStartParam)}`;
  }

  return 'https://telegram.org/apps';
}

export function openTelegramMiniApp(startParam = 'purchase'): void {
  window.location.href = buildTelegramMiniAppUrl(startParam);
}
