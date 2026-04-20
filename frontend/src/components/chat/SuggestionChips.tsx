import { Sparkles } from 'lucide-react';

interface SuggestionChipsProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
  disabled?: boolean;
}

export function SuggestionChips({ suggestions, onSelect, disabled }: SuggestionChipsProps) {
  if (suggestions.length === 0) return null;

  return (
    <div className="px-2 py-2 sm:px-4 sm:py-3 border-t border-white/10 flex-shrink-0">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles size={14} className="text-primary-400" />
          <span className="text-xs text-zinc-400">Suggestions</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => onSelect(suggestion)}
              disabled={disabled}
              className="px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 hover:border-primary-500/50 text-xs text-zinc-300 hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
