import { cn } from '@/utils/cn';
import { X } from 'lucide-react';

interface TagSelectorProps {
  label: string;
  options: string[];
  selected: string[];
  onSelect: (tags: string[]) => void;
  maxSelection?: number;
  helperText?: string;
}

export function TagSelector({
  label,
  options,
  selected,
  onSelect,
  maxSelection = 5,
  helperText,
}: TagSelectorProps) {
  const toggleTag = (tag: string) => {
    if (selected.includes(tag)) {
      onSelect(selected.filter((t) => t !== tag));
    } else if (selected.length < maxSelection) {
      onSelect([...selected, tag]);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-zinc-300">
          {label}
        </label>
        <span className="text-xs text-zinc-500">
          {selected.length} / {maxSelection} selected
        </span>
      </div>

      {helperText && (
        <p className="text-sm text-zinc-400">{helperText}</p>
      )}

      {/* Selected Tags */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 p-4 rounded-lg bg-white/5 border border-white/10">
          {selected.map((tag) => (
            <button
              key={tag}
              onClick={() => toggleTag(tag)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-500 text-white rounded-full text-sm font-medium hover:bg-primary-600 transition-colors"
            >
              {tag}
              <X size={14} />
            </button>
          ))}
        </div>
      )}

      {/* Available Tags */}
      <div className="flex flex-wrap gap-2">
        {options.map((tag) => {
          const isSelected = selected.includes(tag);
          const isDisabled = !isSelected && selected.length >= maxSelection;

          return (
            <button
              key={tag}
              onClick={() => toggleTag(tag)}
              disabled={isDisabled}
              className={cn(
                'px-4 py-2 rounded-full text-sm font-medium transition-all',
                'hover:scale-105 active:scale-95',
                isSelected
                  ? 'bg-primary-500/20 text-primary-400 border-2 border-primary-500'
                  : 'bg-white/5 text-zinc-400 border-2 border-white/10 hover:border-white/30 hover:text-white',
                isDisabled && 'opacity-30 cursor-not-allowed hover:scale-100'
              )}
            >
              {tag}
            </button>
          );
        })}
      </div>
    </div>
  );
}
