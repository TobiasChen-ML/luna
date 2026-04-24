import { useEffect, useMemo, useState } from 'react';
import { cn } from '@/utils/cn';
import { fetchVideoLoraActions, type VideoLoraAction } from '@/services/videoLoraService';

interface VideoLoraSelectorProps {
  selectedId: string | null;
  onSelect: (lora: VideoLoraAction | null) => void;
  /** compact = small cards for the chat modal; full = larger cards for the generate page */
  variant?: 'compact' | 'full';
}

function toTwoKeywords(name: string): string {
  const parts = name
    .split(/[\s_\-./|()[\]{}:;,]+/)
    .map((part) => part.trim())
    .filter(Boolean);
  if (parts.length <= 2) return parts.join(' ');
  return `${parts[0]} ${parts[1]}`;
}

export function VideoLoraSelector({ selectedId, onSelect, variant = 'compact' }: VideoLoraSelectorProps) {
  const [actions, setActions] = useState<VideoLoraAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isCompact = variant === 'compact';
  const visibleActions = useMemo(
    () => (isCompact ? actions.slice(0, 24) : actions),
    [actions, isCompact]
  );

  useEffect(() => {
    let active = true;
    fetchVideoLoraActions()
      .then((list) => {
        if (!active) return;
        setActions(list);
      })
      .catch((err) => {
        if (!active) return;
        console.error('Failed to load video lora actions:', err);
        setError('Failed to load actions');
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return <p className="text-[11px] text-zinc-500">Loading actions...</p>;
  }

  if (error) {
    return <p className="text-[11px] text-rose-300/80">{error}</p>;
  }

  if (visibleActions.length === 0) {
    return <p className="text-[11px] text-zinc-500">No actions configured in Admin LoRA settings.</p>;
  }

  return (
    <div
      className={cn(
        'flex gap-2 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-white/10',
        !isCompact && 'flex-wrap overflow-x-visible'
      )}
    >
      {visibleActions.map((lora) => {
        const isSelected = selectedId === lora.id;
        return (
          <button
            key={lora.id}
            type="button"
            onClick={() => onSelect(isSelected ? null : lora)}
            title={lora.description || lora.lora_name}
            className={cn(
              'flex-shrink-0 rounded-lg border px-2.5 transition-colors text-left',
              isCompact ? 'py-1.5' : 'py-2 flex-shrink',
              isSelected
                ? 'border-violet-400/70 bg-violet-500/20 text-violet-100'
                : 'border-white/10 bg-white/5 text-zinc-300 hover:border-white/25 hover:bg-white/10 hover:text-white'
            )}
          >
            <p className={cn('font-semibold whitespace-nowrap', isCompact ? 'text-[11px]' : 'text-xs')}>
              {lora.action_label}
            </p>
            {!isCompact && (
              <p className="text-[10px] text-zinc-500 mt-0.5">{toTwoKeywords(lora.lora_name)}</p>
            )}
          </button>
        );
      })}
    </div>
  );
}
