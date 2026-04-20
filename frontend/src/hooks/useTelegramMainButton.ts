/**
 * Integrates Telegram Mini App native MainButton (bottom CTA button).
 *
 * When called inside a TMA page:
 * - Configures and shows MainButton with the given text/color
 * - Calls onClick when user taps it
 * - Hides MainButton and removes handler on unmount
 *
 * Outside TMA this hook is a no-op.
 */
import { useEffect, useRef } from 'react';
import { useTelegram } from '@/contexts/TelegramContext';

interface MainButtonConfig {
  text: string;
  onClick: () => void;
  isVisible?: boolean;
  isLoading?: boolean;
  color?: string;
  textColor?: string;
}

export function useTelegramMainButton({
  text,
  onClick,
  isVisible = true,
  isLoading = false,
  color,
  textColor,
}: MainButtonConfig): void {
  const { isTma, webApp } = useTelegram();
  // Stable ref to avoid re-registering onClick on every render
  const onClickRef = useRef(onClick);

  useEffect(() => {
    onClickRef.current = onClick;
  }, [onClick]);

  useEffect(() => {
    if (!isTma || !webApp) return;

    const btn = webApp.MainButton;

    btn.setParams({
      text,
      ...(color ? { color } : {}),
      ...(textColor ? { text_color: textColor } : {}),
      is_active: !isLoading,
      is_visible: isVisible,
    });

    if (isLoading) {
      btn.showProgress(true);
    } else {
      btn.hideProgress();
    }

    const handler = () => onClickRef.current();
    btn.onClick(handler);

    return () => {
      btn.offClick(handler);
      btn.hide();
    };
  }, [isTma, webApp, text, isVisible, isLoading, color, textColor]);
}
