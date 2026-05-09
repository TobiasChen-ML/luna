import { useState } from 'react';
import { BookOpen, Sparkles, X } from 'lucide-react';
import { generateStoryFromChat } from '@/services/api';

interface Props {
  sessionId: string;
  characterId: string;
  message: string;
  onAccepted: (scriptId: string) => void;
  onDismiss: () => void;
}

export function StoryProposalCard({ sessionId, characterId, message, onAccepted, onDismiss }: Props) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAccept = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const { script_id } = await generateStoryFromChat(characterId, sessionId);
      onAccepted(script_id);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: { message?: string } } } };
      setError(e?.response?.data?.detail?.message ?? 'Failed to generate story. Please try again.');
      setIsGenerating(false);
    }
  };

  return (
    <div className="mx-4 mb-3 rounded-2xl border border-purple-500/30 bg-gradient-to-br from-purple-950/60 to-indigo-950/60 p-4 backdrop-blur-sm">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-purple-500/20">
          <Sparkles className="h-4 w-4 text-purple-300" />
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-purple-200 mb-1">Story Awaits</p>
          <p className="text-sm text-white/80 leading-snug">{message}</p>

          {error && (
            <p className="mt-2 text-xs text-red-400">{error}</p>
          )}

          <div className="mt-3 flex gap-2">
            <button
              onClick={handleAccept}
              disabled={isGenerating}
              className="flex items-center gap-1.5 rounded-full bg-purple-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-purple-500 disabled:opacity-60 transition-colors"
            >
              <BookOpen className="h-3.5 w-3.5" />
              {isGenerating ? 'Creating…' : 'Start Story'}
            </button>
            <button
              onClick={onDismiss}
              disabled={isGenerating}
              className="rounded-full px-3 py-1.5 text-sm text-white/50 hover:text-white/80 transition-colors"
            >
              Maybe later
            </button>
          </div>
        </div>

        <button onClick={onDismiss} className="shrink-0 text-white/30 hover:text-white/60 transition-colors">
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
