import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { X } from 'lucide-react';
import { Button } from './Button';
import { cn } from '@/utils/cn';
import { isTelegramMiniApp } from '@/utils/telegram';

const COOKIE_CONSENT_KEY = 'cookie_consent';

export function CookieConsent() {
  // Cookie consent is not applicable inside Telegram's WebView
  if (isTelegramMiniApp()) return null;

  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if user has already made a choice
    const consent = localStorage.getItem(COOKIE_CONSENT_KEY);
    if (!consent) {
      // Small delay for better UX - don't show immediately on page load
      const timer = setTimeout(() => {
        setIsVisible(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem(COOKIE_CONSENT_KEY, 'accepted');
    setIsVisible(false);
  };

  const handleDecline = () => {
    localStorage.setItem(COOKIE_CONSENT_KEY, 'declined');
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div
      className={cn(
        'fixed bottom-0 left-0 right-0 z-50',
        'bg-zinc-900/95 backdrop-blur-sm border-t border-zinc-700',
        'p-4 md:p-6',
        'animate-in slide-in-from-bottom duration-300'
      )}
    >
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
          {/* Close button for mobile */}
          <button
            onClick={handleDecline}
            className="absolute top-3 right-3 md:hidden text-zinc-400 hover:text-white"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Cookie icon and text */}
          <div className="flex-1 pr-8 md:pr-0">
            <div className="flex items-start gap-3">
              <span className="text-2xl">🍪</span>
              <div>
                <h3 className="text-white font-semibold mb-1">We use cookies</h3>
                <p className="text-zinc-400 text-sm">
                  We use cookies to enhance your browsing experience, serve personalized content,
                  and analyze our traffic. By clicking "Accept All", you consent to our use of cookies.{' '}
                  <Link to="/privacy" className="text-primary-400 hover:text-primary-300 underline">
                    Privacy Policy
                  </Link>
                </p>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 w-full md:w-auto">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDecline}
              className="flex-1 md:flex-none"
            >
              Decline
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleAccept}
              className="flex-1 md:flex-none"
            >
              Accept All
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
