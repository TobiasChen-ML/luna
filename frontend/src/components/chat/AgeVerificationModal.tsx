import { useEffect, useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { Button } from '@/components/common';
import { ageVerificationService } from '@/services/ageVerificationService';

interface AgeVerificationModalProps {
  isOpen: boolean;
  message?: string | null;
  onVerified: () => void;
  onClose: () => void;
}

export function AgeVerificationModal({
  isOpen,
  message,
  onVerified,
  onClose,
}: AgeVerificationModalProps) {
  const [isStarting, setIsStarting] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [verificationUrl, setVerificationUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !sessionId) return;

    setIsPolling(true);
    const timer = setInterval(async () => {
      try {
        const status = await ageVerificationService.getStatus(sessionId);
        if (status.verified) {
          clearInterval(timer);
          setIsPolling(false);
          onVerified();
        } else if (status.failed) {
          clearInterval(timer);
          setIsPolling(false);
          setError('Age verification failed. Please retry.');
        }
      } catch {
        // keep polling silently
      }
    }, 3000);

    return () => {
      clearInterval(timer);
      setIsPolling(false);
    };
  }, [isOpen, sessionId, onVerified]);

  if (!isOpen) return null;

  const handleStart = async () => {
    setError(null);
    setIsStarting(true);
    try {
      const result = await ageVerificationService.start();
      setSessionId(result.session_id);
      setVerificationUrl(result.verification_url || null);
      if (result.verification_url) {
        window.open(result.verification_url, '_blank', 'noopener,noreferrer');
      }
    } catch {
      setError('Failed to start age verification. Please try again.');
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-md rounded-xl border border-white/15 bg-zinc-900 p-5 space-y-4">
        <div className="flex items-center gap-3">
          <ShieldCheck className="text-primary-400" size={24} />
          <h3 className="text-lg font-semibold text-white">Age Verification Required</h3>
        </div>
        <p className="text-sm text-zinc-300">
          {message || 'MATURE image/video access requires third-party age verification.'}
        </p>
        {verificationUrl && (
          <p className="text-xs text-zinc-400 break-all">
            Verification URL: {verificationUrl}
          </p>
        )}
        {error && <p className="text-sm text-rose-400">{error}</p>}
        <div className="flex gap-2">
          <Button variant="secondary" className="flex-1" onClick={onClose}>
            Close
          </Button>
          <Button className="flex-1" onClick={handleStart} loading={isStarting || isPolling}>
            {sessionId ? 'Waiting Result...' : 'Verify Now'}
          </Button>
        </div>
      </div>
    </div>
  );
}

