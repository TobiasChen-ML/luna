import { useState } from 'react';
import { Button } from '@/components/common';
import { relationshipService, type ConsentTier } from '@/services/relationshipService';

interface ConsentModalProps {
  isOpen: boolean;
  characterId: string;
  characterName: string;
  onClose: () => void;
}

const tierOptions: ConsentTier[] = ['sfw', 'suggestive', 'mature'];

export function ConsentModal({
  isOpen,
  characterId,
  characterName,
  onClose,
}: ConsentModalProps) {
  const [tier, setTier] = useState<ConsentTier>('mature');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const apply = async (consent: boolean) => {
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const result = await relationshipService.setConsent(characterId, consent, tier);
      setMessage(result.message || (consent ? 'Consent granted.' : 'Consent revoked.'));
    } catch (err: unknown) {
      const detail =
        typeof err === 'object' &&
        err !== null &&
        'response' in err &&
        typeof (err as { response?: unknown }).response === 'object'
          ? ((err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
            null)
          : null;
      setError(detail || 'Failed to update consent.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-md rounded-xl border border-white/15 bg-zinc-900 p-5 space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Explicit Consent</h3>
          <p className="text-sm text-zinc-400 mt-1">
            Manage mature-content consent for {characterName}.
          </p>
        </div>

        <label className="block space-y-2">
          <span className="text-sm text-zinc-300">Tier</span>
          <select
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white"
            value={tier}
            onChange={(e) => setTier(e.target.value as ConsentTier)}
            disabled={busy}
          >
            {tierOptions.map((item) => (
              <option key={item} value={item}>
                {item.toUpperCase()}
              </option>
            ))}
          </select>
        </label>

        {message && <p className="text-sm text-emerald-400">{message}</p>}
        {error && <p className="text-sm text-rose-400">{error}</p>}

        <div className="flex gap-2">
          <Button variant="secondary" className="flex-1" onClick={onClose} disabled={busy}>
            Close
          </Button>
          <Button className="flex-1" onClick={() => apply(true)} loading={busy}>
            Grant
          </Button>
          <Button
            variant="outline"
            className="flex-1"
            onClick={() => apply(false)}
            disabled={busy}
          >
            Revoke
          </Button>
        </div>
      </div>
    </div>
  );
}
