/**
 * StoryboardModal
 *
 * Full-screen display of the generated 3x3 storyboard image.
 * Shows the story summary below the image.
 */
import { X, Download } from 'lucide-react';
import type { StoryboardResponse } from '@/types/story';

interface StoryboardModalProps {
  storyboard: StoryboardResponse;
  storyTitle: string;
  endingType: string;
  onClose: () => void;
}

const ENDING_LABELS: Record<string, string> = {
  good: 'Good Ending',
  neutral: 'Neutral Ending',
  bad: 'Bad Ending',
  secret: 'Secret Ending',
};

export function StoryboardModal({ storyboard, storyTitle, endingType, onClose }: StoryboardModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/90 backdrop-blur-sm p-4">
      {/* Top bar */}
      <div className="w-full max-w-2xl flex items-center justify-between mb-4">
        <div>
          <h2 className="text-white font-bold text-lg leading-tight">{storyTitle}</h2>
          <p className="text-gray-400 text-sm">{ENDING_LABELS[endingType] ?? endingType}</p>
        </div>
        <div className="flex items-center gap-2">
          <a
            href={storyboard.image_url}
            download
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700/50 transition-colors"
            title="Save image"
          >
            <Download size={18} />
          </a>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700/50 transition-colors"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Storyboard image */}
      <div className="w-full max-w-2xl rounded-xl overflow-hidden border border-gray-700 shadow-2xl">
        <img
          src={storyboard.image_url}
          alt={`${storyTitle} Storyboard Memory`}
          className="w-full h-auto object-contain"
          onContextMenu={(e) => e.preventDefault()}
        />
      </div>

      {/* Summary */}
      {storyboard.story_summary && (
        <p className="mt-4 max-w-2xl text-center text-gray-300 text-sm leading-relaxed px-4">
          {storyboard.story_summary}
        </p>
      )}

      <p className="mt-3 text-gray-600 text-xs">Long-press or right-click to save image</p>
    </div>
  );
}

