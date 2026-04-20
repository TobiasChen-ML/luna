/**
 * reCAPTCHA hook for React
 * Supports v3 execute flow and v2 checkbox flow.
 */
import { useEffect, useCallback, useRef } from 'react';

// Get site key from environment
const RECAPTCHA_SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY || '';
const RECAPTCHA_VERSION = (import.meta.env.VITE_RECAPTCHA_VERSION || 'v3').toLowerCase();
const RECAPTCHA_SOURCES = [
  'https://www.google.com/recaptcha/api.js',
  'https://www.recaptcha.net/recaptcha/api.js',
];

// Extend window type for grecaptcha
declare global {
  interface Window {
    grecaptcha: {
      ready: (callback: () => void) => void;
      render: (
        container: string | HTMLElement,
        parameters: {
          sitekey: string;
          callback?: (token: string) => void;
          'expired-callback'?: () => void;
          'error-callback'?: () => void;
        }
      ) => number;
      reset: (widgetId?: number) => void;
      getResponse: (widgetId?: number) => string;
      execute: (siteKey: string, options: { action: string }) => Promise<string>;
    };
  }
}

/**
 * Hook to use reCAPTCHA
 * @returns executeRecaptcha + v2 container ref
 */
export function useRecaptcha() {
  const isLoadedRef = useRef(false);
  const isReadyRef = useRef(false);
  const v2WidgetIdRef = useRef<number | null>(null);
  const v2TokenRef = useRef<string | null>(null);
  const recaptchaContainerRef = useRef<HTMLDivElement | null>(null);

  const markReadyIfAvailable = useCallback(() => {
    if (window.grecaptcha) {
      window.grecaptcha.ready(() => {
        isReadyRef.current = true;
        if (
          RECAPTCHA_VERSION === 'v2' &&
          recaptchaContainerRef.current &&
          v2WidgetIdRef.current === null
        ) {
          v2WidgetIdRef.current = window.grecaptcha.render(recaptchaContainerRef.current, {
            sitekey: RECAPTCHA_SITE_KEY,
            callback: (token: string) => {
              v2TokenRef.current = token;
            },
            'expired-callback': () => {
              v2TokenRef.current = null;
            },
            'error-callback': () => {
              v2TokenRef.current = null;
            },
          });
        }
      });
    }
  }, []);

  const loadScript = useCallback((baseUrl: string) => {
    const script = document.createElement('script');
    script.src =
      RECAPTCHA_VERSION === 'v2'
        ? `${baseUrl}?render=explicit`
        : `${baseUrl}?render=${RECAPTCHA_SITE_KEY}`;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      markReadyIfAvailable();
    };
    document.head.appendChild(script);
    return script;
  }, [markReadyIfAvailable]);

  useEffect(() => {
    // Skip if no site key configured
    if (!RECAPTCHA_SITE_KEY) {
      console.warn('reCAPTCHA site key not configured');
      return;
    }

    // Skip if already loaded
    if (isLoadedRef.current) return;
    isLoadedRef.current = true;

    // Check if script already exists
    const existingScript = document.querySelector('script[src*="recaptcha"]');
    if (existingScript) {
      markReadyIfAvailable();
      return;
    }

    // Load from google.com first, then fallback to recaptcha.net
    const primaryScript = loadScript(RECAPTCHA_SOURCES[0]);
    primaryScript.onerror = () => {
      if (!document.querySelector('script[src*="recaptcha.net/recaptcha/api.js"]')) {
        loadScript(RECAPTCHA_SOURCES[1]);
      }
    };

    return () => {
      // Cleanup is tricky with grecaptcha, leave it loaded
    };
  }, [loadScript, markReadyIfAvailable]);

  /**
   * Execute reCAPTCHA and get token
   * @param action - Action name for analytics (v3 only)
   * @returns Promise<string | null> - Token or null if not available
   */
  const executeRecaptcha = useCallback(async (action: string): Promise<string | null> => {
    // If no site key, skip captcha
    if (!RECAPTCHA_SITE_KEY) {
      return null;
    }

    // Wait briefly for script/grecaptcha readiness
    if (!window.grecaptcha || !isReadyRef.current) {
      await new Promise((resolve) => setTimeout(resolve, 300));
    }

    if (!window.grecaptcha) {
      console.warn('reCAPTCHA not loaded');
      return null;
    }

    try {
      if (RECAPTCHA_VERSION === 'v2') {
        if (v2WidgetIdRef.current === null) {
          return null;
        }
        const response = window.grecaptcha.getResponse(v2WidgetIdRef.current);
        return response || v2TokenRef.current;
      }

      const token = await window.grecaptcha.execute(RECAPTCHA_SITE_KEY, { action });
      return token;
    } catch (error) {
      console.error('reCAPTCHA execution failed:', error);
      return null;
    }
  }, []);

  const resetRecaptcha = useCallback(() => {
    if (RECAPTCHA_VERSION !== 'v2' || !window.grecaptcha || v2WidgetIdRef.current === null) {
      return;
    }
    window.grecaptcha.reset(v2WidgetIdRef.current);
    v2TokenRef.current = null;
  }, []);

  return {
    executeRecaptcha,
    resetRecaptcha,
    recaptchaContainerRef,
    recaptchaVersion: RECAPTCHA_VERSION,
    isConfigured: Boolean(RECAPTCHA_SITE_KEY),
  };
}
