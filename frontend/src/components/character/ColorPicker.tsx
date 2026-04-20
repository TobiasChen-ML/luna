import { cn } from '@/utils/cn';
import { Check } from 'lucide-react';

interface ColorOption {
  name: string;
  value: string;
  hex?: string;
}

interface ColorPickerProps {
  label: string;
  options: ColorOption[];
  selected?: string;
  onSelect: (value: string) => void;
}

export function ColorPicker({ label, options, selected, onSelect }: ColorPickerProps) {
  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-zinc-300">
        {label}
      </label>
      <div className="grid grid-cols-4 md:grid-cols-6 gap-3">
        {options.map((option) => (
          <button
            key={option.value}
            onClick={() => onSelect(option.value)}
            className={cn(
              'group relative aspect-square rounded-lg border-2 transition-all',
              'hover:scale-110 active:scale-95',
              selected === option.value
                ? 'border-primary-500 ring-2 ring-primary-500/50'
                : 'border-white/20 hover:border-white/40'
            )}
            style={{
              backgroundColor: option.hex || option.value,
            }}
          >
            {/* Name tooltip */}
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-black/80 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              {option.name}
            </div>

            {/* Check mark */}
            {selected === option.value && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-6 h-6 bg-white rounded-full flex items-center justify-center">
                  <Check size={14} className="text-black" />
                </div>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
