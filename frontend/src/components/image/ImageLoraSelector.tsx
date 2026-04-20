import { useState } from 'react';
import { cn } from '@/utils/cn';
import {
  IMAGE_GENERATION_LORAS,
  IMAGE_LORA_CATEGORIES,
  type ImageGenerationLoRA,
  type ImageLoRACategory,
} from '@/config/imageGenerationLoras';

interface ImageLoraSelectorProps {
  selectedId: string | null;
  onSelect: (lora: ImageGenerationLoRA | null) => void;
  /** compact = horizontal scroll chips for chat modal; full = tabbed grid for generate page */
  variant?: 'compact' | 'full';
}

export function ImageLoraSelector({
  selectedId,
  onSelect,
  variant = 'compact',
}: ImageLoraSelectorProps) {
  const [activeCategory, setActiveCategory] = useState<ImageLoRACategory>('scene');

  if (variant === 'compact') {
    return (
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-white/10">
        {IMAGE_GENERATION_LORAS.map((lora) => {
          const isSelected = selectedId === lora.id;
          return (
            <button
              key={lora.id}
              type="button"
              onClick={() => onSelect(isSelected ? null : lora)}
              title={lora.description}
              className={cn(
                'flex-shrink-0 rounded-lg border px-2.5 py-1.5 transition-colors text-left',
                isSelected
                  ? 'border-pink-400/70 bg-pink-500/20 text-pink-100'
                  : 'border-white/10 bg-white/5 text-zinc-300 hover:border-white/25 hover:bg-white/10 hover:text-white'
              )}
            >
              <p className="text-[11px] font-semibold whitespace-nowrap">{lora.name}</p>
            </button>
          );
        })}
      </div>
    );
  }

  // Full variant — category tabs + grid
  const categories = Object.keys(IMAGE_LORA_CATEGORIES) as ImageLoRACategory[];
  const filtered = IMAGE_GENERATION_LORAS.filter((l) => l.category === activeCategory);

  return (
    <div className="space-y-2">
      {/* Category tabs */}
      <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-white/10">
        {categories.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setActiveCategory(cat)}
            className={cn(
              'flex-shrink-0 rounded-md border px-2.5 py-1 text-[11px] font-semibold transition-colors',
              activeCategory === cat
                ? 'border-pink-400/70 bg-pink-500/20 text-pink-100'
                : 'border-white/10 bg-white/5 text-zinc-400 hover:border-white/25 hover:text-white'
            )}
          >
            {IMAGE_LORA_CATEGORIES[cat]}
          </button>
        ))}
      </div>

      {/* LoRA cards */}
      <div className="flex flex-wrap gap-2">
        {filtered.map((lora) => {
          const isSelected = selectedId === lora.id;
          return (
            <button
              key={lora.id}
              type="button"
              onClick={() => onSelect(isSelected ? null : lora)}
              title={lora.description}
              className={cn(
                'rounded-lg border px-3 py-2 text-left transition-colors',
                isSelected
                  ? 'border-pink-400/70 bg-pink-500/20 text-pink-100'
                  : 'border-white/10 bg-white/5 text-zinc-300 hover:border-white/25 hover:bg-white/10 hover:text-white'
              )}
            >
              <p className="text-xs font-semibold">{lora.name}</p>
              <p className="text-[10px] text-zinc-500 mt-0.5">{lora.description}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
