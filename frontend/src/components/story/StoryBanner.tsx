/**
 * StoryBanner Component
 *
 * Shows a banner when a story is active in the chat.
 * Displays story title, progress, and option to exit.
 */
import { BookOpen, X } from 'lucide-react';
import type { Story, NarrativePhase } from '@/types/story';

interface StoryBannerProps {
  story: Story;
  narrativePhase: NarrativePhase | null;
  onExit?: () => void;
}

const phaseLabels: Record<NarrativePhase, string> = {
  opening: 'Opening',
  rising: 'Rising',
  climax: 'Climax',
  resolution: 'Resolution',
};

export function StoryBanner({
  story,
  narrativePhase,
  onExit
}: StoryBannerProps) {
  return (
    <div className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 border-b border-purple-500/30 px-4 py-2">
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <BookOpen size={16} className="text-purple-400 flex-shrink-0" />
          <span className="text-sm font-medium text-white truncate">
            {story.title}
          </span>
          {narrativePhase && (
            <span className="text-xs text-purple-300 flex-shrink-0">
              - {phaseLabels[narrativePhase]}
            </span>
          )}
        </div>

        {onExit && (
          <button
            onClick={onExit}
            className="text-zinc-400 hover:text-white p-1 rounded hover:bg-white/10 transition-colors flex-shrink-0"
            title="Exit story"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  );
}
