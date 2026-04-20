/**
 * StoryCompletionModal
 *
 * Shown when a story reaches its ending. Displays the ending type,
 * completion time, rewards, and a button to generate the storyboard.
 */
import { useState } from 'react';
import { X, Trophy, Clock, Star, Clapperboard } from 'lucide-react';
import type { StoryCompletedEvent } from '@/types/story';
import type { StoryboardResponse } from '@/types/story';
import { storyService } from '@/services/storyService';
import { StoryboardModal } from './StoryboardModal';

interface StoryCompletionModalProps {
  data: StoryCompletedEvent;
  sessionId: string;
  onClose: () => void;
}

const ENDING_LABELS: Record<string, { label: string; color: string; bg: string }> = {
  good: { label: 'Good Ending', color: 'text-emerald-400', bg: 'bg-emerald-900/30 border-emerald-500/40' },
  neutral: { label: 'Neutral Ending', color: 'text-amber-400', bg: 'bg-amber-900/30 border-amber-500/40' },
  bad: { label: 'Bad Ending', color: 'text-rose-400', bg: 'bg-rose-900/30 border-rose-500/40' },
  secret: { label: 'Secret Ending', color: 'text-purple-400', bg: 'bg-purple-900/30 border-purple-500/40' },
};

export function StoryCompletionModal({ data, sessionId, onClose }: StoryCompletionModalProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [storyboard, setStoryboard] = useState<StoryboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ending = ENDING_LABELS[data.ending_type] ?? ENDING_LABELS.neutral;

  async function handleGenerateStoryboard() {
    setIsGenerating(true);
    setError(null);
    try {
      const result = await storyService.generateStoryboard(data.story_id, sessionId);
      setStoryboard(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Generation failed. Please try again.';
      setError(msg);
    } finally {
      setIsGenerating(false);
    }
  }

  if (storyboard) {
    return (
      <StoryboardModal
        storyboard={storyboard}
        storyTitle={data.story_title}
        endingType={data.ending_type}
        onClose={onClose}
      />
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-md rounded-2xl bg-gray-900 border border-gray-700 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className={`px-6 pt-6 pb-4 border-b ${ending.bg} border-gray-700`}>
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
          <div className="flex items-center gap-2 mb-1">
            <Trophy size={18} className={ending.color} />
            <span className={`text-xs font-semibold uppercase tracking-widest ${ending.color}`}>
              Script Completed
            </span>
          </div>
          <h2 className="text-xl font-bold text-white leading-tight">{data.story_title}</h2>
          <p className={`mt-1 text-sm font-medium ${ending.color}`}>{ending.label}</p>
        </div>

        {/* Stats */}
        <div className="px-6 py-4 flex gap-6">
          {data.completion_time_minutes > 0 && (
            <div className="flex items-center gap-2 text-gray-400 text-sm">
              <Clock size={14} />
              <span>{data.completion_time_minutes} min</span>
            </div>
          )}
          {(data.rewards.trust_bonus > 0 || data.rewards.intimacy_bonus > 0) && (
            <div className="flex items-center gap-2 text-gray-400 text-sm">
              <Star size={14} />
              <span>
                {data.rewards.trust_bonus > 0 && `Trust +${data.rewards.trust_bonus}`}
                {data.rewards.trust_bonus > 0 && data.rewards.intimacy_bonus > 0 && '  '}
                {data.rewards.intimacy_bonus > 0 && `Intimacy +${data.rewards.intimacy_bonus}`}
              </span>
            </div>
          )}
        </div>

        {/* Action */}
        <div className="px-6 pb-6 space-y-3">
          {error && (
            <p className="text-sm text-rose-400 text-center">{error}</p>
          )}

          <button
            onClick={handleGenerateStoryboard}
            disabled={isGenerating}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl
              bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500
              text-white font-semibold transition-all disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <Clapperboard size={18} />
            {isGenerating ? 'Generating storyboard memory... (~15-30s)' : '🎬 Generate Storyboard Memory'}
          </button>

          <button
            onClick={onClose}
            className="w-full py-2.5 px-4 rounded-xl border border-gray-600 text-gray-400
              hover:text-white hover:border-gray-500 transition-colors text-sm"
          >
            View Later
          </button>
        </div>
      </div>
    </div>
  );
}


