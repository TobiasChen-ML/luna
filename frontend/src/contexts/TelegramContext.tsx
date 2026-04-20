/**
 * TelegramProvider â€?manages Telegram Mini App lifecycle.
 *
 * Responsibilities:
 * - Call WebApp.ready() and WebApp.expand() on mount
 * - Expose isTma, webApp, user, colorScheme via useTelegram() hook
 * - Sync Telegram colorScheme â†?document class (dark/light)
 * - Apply Telegram themeParams as CSS custom properties
 */
import { createContext, useContext, useEffect, useMemo } from 'react';
import {
  isTelegramMiniApp,
  getTelegramWebApp,
  getTelegramUser,
  getTelegramColorScheme,
  getTelegramThemeParams,
} from '@/utils/telegram';
import type {
  TelegramWebApp,
  TelegramWebAppUser,
  TelegramThemeParams,
} from '@/utils/telegram';

interface TelegramContextType {
  isTma: boolean;
  webApp: TelegramWebApp | null;
  user: TelegramWebAppUser | null;
  colorScheme: 'light' | 'dark';
  themeParams: TelegramThemeParams;
}

const TelegramContext = createContext<TelegramContextType>({
  isTma: false,
  webApp: null,
  user: null,
  colorScheme: 'dark',
  themeParams: {},
});

export function TelegramProvider({ children }: { children: React.ReactNode }) {
  const isTma = isTelegramMiniApp();
  const webApp = getTelegramWebApp();

  // Initialize TMA lifecycle on mount
  useEffect(() => {
    if (!webApp) return;

    // Signal to Telegram that the app is ready to display
    webApp.ready();
    // Expand to full available height
    webApp.expand();
    // Prevent accidental close on back swipe
    webApp.enableClosingConfirmation();
  }, [webApp]);

  // Sync Telegram safe-area insets (Dynamic Island / device cutouts) to CSS vars.
  useEffect(() => {
    const root = document.documentElement;
    const resetSafeArea = () => {
      root.style.setProperty('--tg-safe-area-top', '0px');
      root.style.setProperty('--tg-safe-area-bottom', '0px');
    };

    if (!webApp) {
      resetSafeArea();
      return;
    }

    const applySafeAreaInsets = () => {
      const top = Math.max(
        webApp.safeAreaInset?.top ?? 0,
        webApp.contentSafeAreaInset?.top ?? 0,
        0
      );
      const bottom = Math.max(
        webApp.safeAreaInset?.bottom ?? 0,
        webApp.contentSafeAreaInset?.bottom ?? 0,
        0
      );
      root.style.setProperty('--tg-safe-area-top', `${top}px`);
      root.style.setProperty('--tg-safe-area-bottom', `${bottom}px`);
    };

    applySafeAreaInsets();
    webApp.onEvent('viewportChanged', applySafeAreaInsets);
    webApp.onEvent('safeAreaChanged', applySafeAreaInsets);

    return () => {
      webApp.offEvent('viewportChanged', applySafeAreaInsets);
      webApp.offEvent('safeAreaChanged', applySafeAreaInsets);
      resetSafeArea();
    };
  }, [webApp]);

  // Sync Telegram color scheme â†?Tailwind dark/light class
  useEffect(() => {
    if (!webApp) return;

    const applyTheme = () => {
      // Keep dark mode always on for now â€?full light mode is a follow-up task
      document.documentElement.classList.add('dark');

      // Map Telegram themeParams â†?CSS custom properties for accent colors
      const params = webApp.themeParams ?? {};
      const root = document.documentElement;
      if (params.button_color) root.style.setProperty('--tg-button-color', params.button_color);
      if (params.button_text_color) root.style.setProperty('--tg-button-text-color', params.button_text_color);
      if (params.link_color) root.style.setProperty('--tg-link-color', params.link_color);
      if (params.bg_color) root.style.setProperty('--tg-bg-color', params.bg_color);
      if (params.secondary_bg_color) root.style.setProperty('--tg-secondary-bg-color', params.secondary_bg_color);
    };

    applyTheme();
    webApp.onEvent('themeChanged', applyTheme);

    return () => {
      webApp.offEvent('themeChanged', applyTheme);
    };
  }, [webApp]);

  const value = useMemo<TelegramContextType>(
    () => ({
      isTma,
      webApp,
      user: getTelegramUser(),
      colorScheme: getTelegramColorScheme(),
      themeParams: getTelegramThemeParams(),
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [isTma]
  );

  return (
    <TelegramContext.Provider value={value}>
      {children}
    </TelegramContext.Provider>
  );
}

export function useTelegram(): TelegramContextType {
  return useContext(TelegramContext);
}


