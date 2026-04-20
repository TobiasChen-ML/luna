/**
 * SceneChoices Component
 *
 * Displays interactive scene choices during gameplay mode.
 * PRD v3 Section 2.6 (FR-6): Scene Gameplay MVP
 *
 * When clicked, sends the choice as the user's next message.
 */
import { Gamepad2 } from 'lucide-react';

interface SceneChoicesProps {
  choices: string[];
  onSelect: (choice: string) => void;
  disabled?: boolean;
  sceneInfo?: {
    description?: string;
    turn?: number;
    narrative_phase?: string;
  };
}

export function SceneChoices({
  choices,
  onSelect,
  disabled,
  sceneInfo
}: SceneChoicesProps) {
  if (choices.length === 0) return null;

  return (
    <div className="px-2 py-3 sm:px-4 sm:py-4 border-t border-primary-500/30 bg-gradient-to-t from-primary-950/50 to-transparent flex-shrink-0">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-2 mb-3">
          <Gamepad2 size={16} className="text-primary-400" />
          <span className="text-sm font-medium text-primary-300">Choose your response</span>
          {sceneInfo?.narrative_phase && (
            <span className="ml-auto text-xs text-zinc-500 capitalize">
              {sceneInfo.narrative_phase} - Turn {sceneInfo.turn || 1}
            </span>
          )}
        </div>

        {/* Scene description if available */}
        {sceneInfo?.description && (
          <p className="text-xs text-zinc-400 mb-3 italic">
            {sceneInfo.description}
          </p>
        )}

        {/* Choice buttons */}
        <div className="flex flex-col gap-2">
          {choices.map((choice, index) => (
            <button
              key={index}
              onClick={() => onSelect(choice)}
              disabled={disabled}
              className="w-full px-4 py-3 rounded-lg bg-white/5 hover:bg-primary-500/20 border border-primary-500/30 hover:border-primary-400 text-sm text-left text-zinc-200 hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <span className="inline-flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-primary-500/20 text-primary-400 text-xs flex items-center justify-center font-medium group-hover:bg-primary-500/40">
                  {index + 1}
                </span>
                {choice}
              </span>
            </button>
          ))}
        </div>

        {/* Hint */}
        <p className="mt-2 text-xs text-zinc-500 text-center">
          Click a choice or type your own response
        </p>
      </div>
    </div>
  );
}
