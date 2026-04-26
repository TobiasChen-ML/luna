import { Link } from 'react-router-dom';
import { Crown, Sparkles, X } from 'lucide-react';

import { Modal } from '@/components/common/Modal';
import { Button } from '@/components/common/Button';

interface PremiumOfferModalProps {
  isOpen: boolean;
  onClose: () => void;
  onContinueFree?: () => void;
  countdownText?: string | null;
}

export function PremiumOfferModal({
  isOpen,
  onClose,
  onContinueFree,
  countdownText,
}: PremiumOfferModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-lg p-0 overflow-hidden">
      <div className="relative p-6 border-b border-white/10">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 p-2 rounded-lg hover:bg-white/5 transition-colors"
          aria-label="Close"
        >
          <X className="w-5 h-5 text-zinc-300" />
        </button>

        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500/30 to-purple-500/30 border border-pink-500/20 flex items-center justify-center">
            <Crown className="w-5 h-5 text-pink-200" />
          </div>
          <div>
            <h2 className="text-xl font-heading font-bold text-white">Unlock Premium</h2>
            <p className="text-sm text-zinc-400">
              Faster progression, higher limits, and more media features.
            </p>
          </div>
        </div>

        {countdownText && (
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-pink-500/10 border border-pink-500/20 text-pink-200 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            Limited-time offer ends in {countdownText}
          </div>
        )}
      </div>

      <div className="p-6 space-y-5">
        <ul className="space-y-3 text-sm">
          {[
            'More monthly credits + higher daily check-in',
            'More active characters',
            'Image + video generation (tier dependent)',
            'Voice calling (tier dependent)',
          ].map((text) => (
            <li key={text} className="flex items-start gap-3 text-zinc-200">
              <span className="mt-1 w-1.5 h-1.5 rounded-full bg-pink-400" />
              <span>{text}</span>
            </li>
          ))}
        </ul>

        <div className="flex flex-col gap-3">
          <Link to="/subscriptions" className="block" onClick={onClose}>
            <Button variant="primary" className="w-full">
              See Plans & Upgrade
            </Button>
          </Link>

          {onContinueFree && (
            <Button variant="secondary" className="w-full" onClick={onContinueFree}>
              Continue Free
            </Button>
          )}
        </div>

        <p className="text-xs text-zinc-500">
          Purchases are completed in Telegram with Stars. Active benefits work across supported access points.
        </p>
      </div>
    </Modal>
  );
}



