import { useState } from 'react';
import { Gamepad2 } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useTelegram } from '@/contexts/TelegramContext';

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
  sceneInfo,
}: SceneChoicesProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const { webApp } = useTelegram();

  if (choices.length === 0) return null;

  const handleSelect = (choice: string, index: number) => {
    if (disabled || selectedIndex !== null) return;
    setSelectedIndex(index);
    webApp?.HapticFeedback?.impactOccurred('medium');
    onSelect(choice);
  };

  return (
    <div className="px-3 py-3 sm:px-4 sm:py-4 border-t border-primary-500/30 bg-gradient-to-t from-primary-950/50 to-transparent flex-shrink-0">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-2 mb-3">
          <Gamepad2 size={16} className="text-primary-400" />
          <span className="text-sm font-medium text-primary-300">Choose your response</span>
          {sceneInfo?.narrative_phase && (
            <span className="ml-auto text-xs text-zinc-500 capitalize">
              {sceneInfo.narrative_phase} · Turn {sceneInfo.turn || 1}
            </span>
          )}
        </div>

        {sceneInfo?.description && (
          <p className="text-xs text-zinc-400 mb-3 italic">{sceneInfo.description}</p>
        )}

        <div className="flex flex-col gap-2">
          {choices.map((choice, index) => (
            <button
              key={index}
              onClick={() => handleSelect(choice, index)}
              disabled={disabled || selectedIndex !== null}
              className={cn(
                'w-full px-4 py-3.5 rounded-xl border text-sm text-left transition-all duration-200',
                'min-h-[48px] active:scale-[0.98]',
                selectedIndex === null
                  ? 'bg-white/5 hover:bg-primary-500/20 border-primary-500/30 hover:border-primary-400 text-zinc-200 hover:text-white'
                  : selectedIndex === index
                    ? 'bg-primary-500/30 border-primary-400 text-white scale-[0.98]'
                    : 'bg-white/3 border-white/10 text-zinc-500 opacity-40',
                (disabled || selectedIndex !== null) && selectedIndex !== index && 'cursor-not-allowed',
              )}
            >
              <span className="inline-flex items-center gap-2.5">
                <span
                  className={cn(
                    'w-6 h-6 rounded-full text-xs flex items-center justify-center font-semibold shrink-0',
                    selectedIndex === index
                      ? 'bg-primary-500 text-white'
                      : 'bg-primary-500/20 text-primary-400',
                  )}
                >
                  {index + 1}
                </span>
                {choice}
              </span>
            </button>
          ))}
        </div>

        {selectedIndex === null && (
          <p className="mt-2 text-xs text-zinc-500 text-center">
            Tap a choice or type your own response
          </p>
        )}
      </div>
    </div>
  );
}
