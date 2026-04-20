import { cn } from '@/utils/cn';
import { HUNYUAN_VIDEO_LORAS, type HunyuanVideoLoRA } from '@/config/hunyuanVideoLoras';

interface VideoLoraSelectorProps {
  selectedId: string | null;
  onSelect: (lora: HunyuanVideoLoRA | null) => void;
  /** compact = small cards for the chat modal; full = larger cards for the generate page */
  variant?: 'compact' | 'full';
}

export function VideoLoraSelector({ selectedId, onSelect, variant = 'compact' }: VideoLoraSelectorProps) {
  const isCompact = variant === 'compact';

  return (
    <div
      className={cn(
        'flex gap-2 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-white/10',
        !isCompact && 'flex-wrap overflow-x-visible'
      )}
    >
      {HUNYUAN_VIDEO_LORAS.map((lora) => {
        const isSelected = selectedId === lora.id;
        return (
          <button
            key={lora.id}
            type="button"
            onClick={() => onSelect(isSelected ? null : lora)}
            title={lora.description}
            className={cn(
              'flex-shrink-0 rounded-lg border px-2.5 transition-colors text-left',
              isCompact ? 'py-1.5' : 'py-2 flex-shrink',
              isSelected
                ? 'border-violet-400/70 bg-violet-500/20 text-violet-100'
                : 'border-white/10 bg-white/5 text-zinc-300 hover:border-white/25 hover:bg-white/10 hover:text-white'
            )}
          >
            <p className={cn('font-semibold whitespace-nowrap', isCompact ? 'text-[11px]' : 'text-xs')}>
              {lora.name}
            </p>
            {!isCompact && (
              <p className="text-[10px] text-zinc-500 mt-0.5">{lora.description}</p>
            )}
          </button>
        );
      })}
    </div>
  );
}
