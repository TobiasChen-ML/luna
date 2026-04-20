import { useMemo, useState } from 'react';
import { Container } from '@/components/layout/Container';
import { Button } from '@/components/common';
import { useAuth } from '@/contexts/AuthContext';
import {
  userPreferenceService,
  type MaturePreference,
} from '@/services/userPreferenceService';

export function MatureSettingsPage() {
  const { user, refreshUser } = useAuth();
  const initial = useMemo<MaturePreference>(() => {
    return user?.mature_preference === 'adult' ? 'adult' : 'teen';
  }, [user?.mature_preference]);

  const [value, setValue] = useState<MaturePreference>(initial);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const save = async () => {
    setSaving(true);
    setError('');
    setMessage('');
    try {
      await userPreferenceService.updateMaturePreference(value);
      await refreshUser();
      setMessage('Preference saved.');
    } catch (err: unknown) {
      const detail =
        typeof err === 'object' &&
        err !== null &&
        'response' in err &&
        typeof (err as { response?: unknown }).response === 'object'
          ? ((err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
            null)
          : null;
      setError(detail || 'Failed to save preference.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Container>
      <div className="py-8 max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">MATURE Preferences</h1>
          <p className="text-zinc-400">
            Choose your allowed content tier. This is combined with age and consent gates.
          </p>
        </div>

        <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
          <label className="block space-y-2">
            <span className="text-sm text-zinc-300">Content Tier</span>
            <select
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white"
              value={value}
              onChange={(e) => setValue(e.target.value as MaturePreference)}
              disabled={saving}
            >
              <option value="teen">R13</option>
              <option value="adult">ADULT</option>
            </select>
          </label>

          {message && <p className="text-sm text-emerald-400">{message}</p>}
          {error && <p className="text-sm text-rose-400">{error}</p>}

          <Button onClick={save} loading={saving}>
            Save Preference
          </Button>
        </section>
      </div>
    </Container>
  );
}

export default MatureSettingsPage;
