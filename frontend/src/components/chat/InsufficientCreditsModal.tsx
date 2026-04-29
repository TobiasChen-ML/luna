import { Link } from 'react-router-dom';
import { Coins, X } from 'lucide-react';

import { Modal } from '@/components/common/Modal';
import { Button } from '@/components/common/Button';

interface InsufficientCreditsModalProps {
  isOpen: boolean;
  onClose: () => void;
  required?: number;
  available?: number;
}

export function InsufficientCreditsModal({
  isOpen,
  onClose,
  required,
  available,
}: InsufficientCreditsModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-md p-0 overflow-hidden">
      <div className="relative p-5 border-b border-white/10">
        <button
          onClick={onClose}
          className="absolute right-3 top-3 p-2 rounded-lg hover:bg-white/5 transition-colors"
          aria-label="Close"
        >
          <X className="w-4 h-4 text-zinc-300" />
        </button>

        <div className="flex items-center gap-3 pr-8">
          <div className="w-9 h-9 rounded-xl bg-amber-500/15 border border-amber-400/20 flex items-center justify-center">
            <Coins className="w-5 h-5 text-amber-300" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Credits exhausted</h2>
            <p className="text-sm text-zinc-400">Buy an extra package to continue.</p>
          </div>
        </div>
      </div>

      <div className="p-5 space-y-4">
        {(typeof required === 'number' || typeof available === 'number') && (
          <p className="text-sm text-zinc-300">
            Required: <span className="text-white font-medium">{required ?? '-'}</span>
            {' | '}
            Available: <span className="text-white font-medium">{available ?? '-'}</span>
          </p>
        )}

        <Link to="/billing?buyCredits=1" className="block" onClick={onClose}>
          <Button className="w-full">Go to payment page and buy extra package</Button>
        </Link>

        <Button variant="secondary" onClick={onClose} className="w-full">
          Maybe later
        </Button>
      </div>
    </Modal>
  );
}
