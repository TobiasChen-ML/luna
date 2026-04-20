/**
 * StorySuggestion Component
 *
 * Shows when AI suggests starting a story based on conversation context.
 * Appears as a floating notification/card that can be accepted or dismissed.
 */
import { BookOpen, X, PlayCircle } from 'lucide-react';
import type { StorySuggestionEvent } from '@/types/story';

interface StorySuggestionProps {
  suggestion: StorySuggestionEvent;
  onAccept: () => void;
  onDismiss: () => void;
}

export function StorySuggestion({
  suggestion,
  onAccept,
  onDismiss
}: StorySuggestionProps) {
  return (
    <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-40 w-full max-w-md px-4 animate-slide-up">
      <div className="bg-gradient-to-r from-purple-900/95 to-pink-900/95 rounded-xl border border-purple-500/30 shadow-2xl overflow-hidden backdrop-blur-sm">
        <div className="p-4">
          {/* Header */}
          <div className="flex items-start justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
                <BookOpen size={16} className="text-purple-400" />
              </div>
              <div>
                <p className="text-xs text-purple-300">Story Suggestion</p>
                <h3 className="font-semibold text-white">{suggestion.title}</h3>
              </div>
            </div>
            <button
              onClick={onDismiss}
              className="text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
            >
              <X size={16} />
            </button>
          </div>

          {/* Cover and Description */}
          <div className="flex gap-3 mb-4">
            {suggestion.cover_image_url ? (
              <img
                src={suggestion.cover_image_url}
                alt={suggestion.title}
                className="w-16 h-16 object-cover rounded-lg flex-shrink-0"
              />
            ) : (
              <div className="w-16 h-16 bg-gradient-to-br from-purple-600/30 to-pink-600/30 rounded-lg flex-shrink-0 flex items-center justify-center">
                <BookOpen className="text-purple-400" size={24} />
              </div>
            )}
            <p className="text-sm text-zinc-300 line-clamp-3">
              {suggestion.description || 'An exciting story awaits...'}
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={onDismiss}
              className="flex-1 px-4 py-2 text-sm text-zinc-300 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              Not now
            </button>
            <button
              onClick={onAccept}
              className="flex-1 px-4 py-2 text-sm bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors flex items-center justify-center gap-2"
            >
              <PlayCircle size={16} />
              Start Story
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
