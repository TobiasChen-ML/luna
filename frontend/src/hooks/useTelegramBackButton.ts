/**
 * Integrates Telegram Mini App native BackButton.
 *
 * When called inside a TMA page:
 * - Shows BackButton on mount (if isVisible=true)
 * - Calls onBack when user taps the native back button
 * - Hides BackButton and removes handler on unmount
 *
 * Outside TMA this hook is a no-op.
 */
import { useEffect, useRef } from 'react';
import { useTelegram } from '@/contexts/TelegramContext';

export function useTelegramBackButton(
  onBack?: () => void,
  isVisible = true,
): void {
  const { isTma, webApp } = useTelegram();
  // Stable ref so the effect doesn't re-run when the callback identity changes
  const onBackRef = useRef(onBack);

  useEffect(() => {
    onBackRef.current = onBack;
  }, [onBack]);

  useEffect(() => {
    if (!isTma || !webApp) return;

    const backButton = webApp.BackButton;

    if (!isVisible) {
      backButton.hide();
      return;
    }

    backButton.show();

    const handler = () => onBackRef.current?.();
    backButton.onClick(handler);

    return () => {
      backButton.offClick(handler);
      backButton.hide();
    };
  }, [isTma, webApp, isVisible]);
}
