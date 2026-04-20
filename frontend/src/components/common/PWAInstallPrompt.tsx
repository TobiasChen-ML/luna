import { useState, useEffect, useCallback } from 'react';
import { X, Download, Smartphone } from 'lucide-react';
import { showInstallPrompt, canInstall, isPWA, isIOSNotInstalled, detectPlatform } from '@/utils/pwa';
import { isTelegramMiniApp } from '@/utils/telegram';
import { PWAInstallModal } from './PWAInstallModal';

const DISMISS_KEY = 'pwa-install-dismissed';
const DISMISS_DAYS = 7;
const INITIAL_DELAY_MS = 30000;

function isDismissedRecently(): boolean {
  const dismissed = localStorage.getItem(DISMISS_KEY);
  if (!dismissed) return false;
  const daysSince = (Date.now() - parseInt(dismissed, 10)) / (1000 * 60 * 60 * 24);
  return daysSince < DISMISS_DAYS;
}

export function PWAInstallPrompt() {
  const [showBanner, setShowBanner] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);

  const shouldShow = useCallback(() => {
    if (isPWA()) return false;
    if (isTelegramMiniApp()) return false;
    if (isDismissedRecently()) return false;
    const platform = detectPlatform();
    if (platform === 'ios') return isIOSNotInstalled();
    return canInstall();
  }, []);

  useEffect(() => {
    if (!shouldShow()) return;

    const scheduleShow = () => {
      if (shouldShow()) {
        setTimeout(() => setShowBanner(true), INITIAL_DELAY_MS);
      }
    };

    window.addEventListener('pwa-install-available', scheduleShow);
    scheduleShow();

    return () => {
      window.removeEventListener('pwa-install-available', scheduleShow);
    };
  }, [shouldShow]);

  useEffect(() => {
    const handleTrigger = () => {
      if (!shouldShow()) return;
      if (isDismissedRecently()) return;
      setShowBanner(true);
    };

    window.addEventListener('pwa-prompt-trigger', handleTrigger);
    return () => window.removeEventListener('pwa-prompt-trigger', handleTrigger);
  }, [shouldShow]);

  const handleBannerClick = () => {
    setShowBanner(false);
    const platform = detectPlatform();
    if (platform !== 'ios' && canInstall()) {
      handleNativeInstall();
    } else {
      setShowModal(true);
    }
  };

  const handleNativeInstall = async () => {
    setIsInstalling(true);
    try {
      const outcome = await showInstallPrompt();
      if (outcome === 'accepted') {
        setShowBanner(false);
      } else if (outcome === 'unavailable') {
        setShowModal(true);
      }
    } catch (error) {
      console.error('Install error:', error);
      setShowModal(true);
    } finally {
      setIsInstalling(false);
    }
  };

  const handleDismiss = () => {
    setShowBanner(false);
    localStorage.setItem(DISMISS_KEY, Date.now().toString());
  };

  if (!showBanner) {
    return (
      <PWAInstallModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
      />
    );
  }

  const platform = detectPlatform();
  const isIOS = platform === 'ios';
  const bannerText = isIOS
    ? 'Add to Home Screen for the best experience'
    : 'Install RoxyClub for quick access & offline support';

  return (
    <>
      <div className="fixed bottom-0 left-0 right-0 z-50 p-4 animate-slide-up">
        <div className="max-w-md mx-auto bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl shadow-2xl overflow-hidden">
          <div className="relative p-5">
            <button
              onClick={handleDismiss}
              className="absolute top-3 right-3 text-white/80 hover:text-white transition-colors"
              aria-label="Dismiss"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-4">
              <div className="flex-shrink-0 w-11 h-11 bg-white/20 rounded-xl flex items-center justify-center">
                {isIOS ? (
                  <Smartphone className="w-5 h-5 text-white" />
                ) : (
                  <Download className="w-5 h-5 text-white" />
                )}
              </div>

              <div className="flex-1 min-w-0 pr-6">
                <h3 className="text-base font-semibold text-white mb-0.5">
                  Install RoxyClub
                </h3>
                <p className="text-sm text-white/80 line-clamp-2">
                  {bannerText}
                </p>
              </div>

              <button
                onClick={handleBannerClick}
                disabled={isInstalling}
                className="flex-shrink-0 bg-white text-purple-600 font-semibold py-2.5 px-5 rounded-xl hover:bg-gray-100 active:scale-95 transition-all disabled:opacity-50 text-sm"
              >
                {isInstalling ? (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
                  </span>
                ) : isIOS ? (
                  'How to Install'
                ) : (
                  'Install'
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      <PWAInstallModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
      />
    </>
  );
}

const styles = `
@keyframes slide-up {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.animate-slide-up {
  animation: slide-up 0.3s ease-out;
}
`;

if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = styles;
  document.head.appendChild(styleSheet);
}
