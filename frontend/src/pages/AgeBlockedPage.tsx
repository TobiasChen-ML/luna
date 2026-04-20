import { ShieldX } from 'lucide-react';
import { useAgeGate } from '@/contexts/AgeGateContext';

export function AgeBlockedPage() {
  const { blockTimeRemaining } = useAgeGate();

  // Format remaining time
  const formatTime = (ms: number): string => {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 bg-zinc-950 flex items-center justify-center z-50 p-4">
      <div className="max-w-md w-full bg-zinc-900 rounded-2xl p-8 text-center border border-zinc-800 shadow-xl">
        <div className="mb-6">
          <ShieldX className="w-16 h-16 text-red-500 mx-auto" />
        </div>

        <h1 className="text-2xl font-bold text-white mb-4">
          Access Denied
        </h1>

        <p className="text-zinc-400 mb-6 leading-relaxed">
          This website is intended for users who are{' '}
          <span className="text-white font-semibold">18 years or older</span>.
        </p>

        <p className="text-zinc-500 mb-8">
          Based on your response, you are not eligible to access this content.
        </p>

        {blockTimeRemaining > 0 && (
          <div className="bg-zinc-800 rounded-lg p-4 mb-6">
            <p className="text-sm text-zinc-400">
              You may try again in:
            </p>
            <p className="text-2xl font-mono text-white mt-1">
              {formatTime(blockTimeRemaining)}
            </p>
          </div>
        )}

        <p className="text-xs text-zinc-500">
          If you believe this is an error, please close this window and return later.
        </p>
      </div>
    </div>
  );
}
