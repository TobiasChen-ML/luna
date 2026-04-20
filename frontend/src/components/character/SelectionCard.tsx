import { cn } from '@/utils/cn';
import { Check } from 'lucide-react';

interface SelectionCardProps {
  title: string;
  description?: string;
  selected: boolean;
  onClick: () => void;
  icon?: React.ReactNode;
  image?: string;
  disabled?: boolean;
  variant?: 'default' | 'visual';
  compact?: boolean;
  badge?: React.ReactNode;
  onBadgeClick?: (e: React.MouseEvent) => void;
}

export function SelectionCard({
  title,
  description,
  selected,
  onClick,
  icon,
  image,
  disabled = false,
  variant = 'default',
  compact = false,
  badge,
  onBadgeClick,
}: SelectionCardProps) {
  if (variant === 'visual') {
    return (
      <button
        onClick={onClick}
        disabled={disabled}
        className={cn(
          'group relative w-full text-left p-3 rounded-xl border-2 transition-all overflow-hidden',
          'hover:scale-[1.02] active:scale-[0.98]',
          selected
            ? 'border-primary-500 bg-primary-500/10'
            : 'border-white/10 bg-white/5 hover:border-white/20',
          disabled && 'opacity-50 cursor-not-allowed hover:scale-100'
        )}
      >
        {/* Image Section */}
        <div
          className={cn(
            'relative w-full rounded-lg overflow-hidden mb-3 bg-black/20',
            compact ? 'h-28' : 'aspect-[3/4]'
          )}
        >
            {image ? (
                <img 
                    src={image} 
                    alt={title} 
                    className={cn(
                        "w-full h-full object-cover transition-transform duration-500",
                        selected ? "scale-110" : "group-hover:scale-110"
                    )} 
                />
            ) : (
                <div className="w-full h-full flex items-center justify-center bg-white/5">
                    {icon}
                </div>
            )}
            
            {/* Selected Overlay */}
            {selected && (
                <div className="absolute inset-0 bg-primary-500/20 flex items-center justify-center">
                    <div className="w-10 h-10 bg-primary-500 rounded-full flex items-center justify-center shadow-lg transform scale-100 transition-transform">
                        <Check size={20} className="text-white" />
                    </div>
                </div>
            )}
            
            {/* Hover Overlay */}
            {!selected && !disabled && (
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
            )}

            {/* Badge (e.g., play button, loading spinner) */}
            {badge && (
                <div
                    className="absolute top-2 right-2 z-10"
                    onClick={onBadgeClick}
                >
                    {badge}
                </div>
            )}
        </div>

        {/* Content Section */}
        <div className="px-1">
            <div className="flex items-center justify-between gap-2 mb-1">
                <h3 className={cn(
                    'font-semibold text-lg',
                    selected ? 'text-primary-400' : 'text-zinc-200'
                )}>
                    {title}
                </h3>
            </div>
            {description && (
                <p className="text-xs text-zinc-400 line-clamp-2 leading-relaxed">
                    {description}
                </p>
            )}
        </div>
      </button>
    );
  }

  // Default List Variant
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'relative w-full text-left p-6 rounded-xl border-2 transition-all',
        'hover:scale-[1.02] active:scale-[0.98]',
        selected
          ? 'border-primary-500 bg-primary-500/10'
          : 'border-white/10 bg-white/5 hover:border-white/20',
        disabled && 'opacity-50 cursor-not-allowed hover:scale-100'
      )}
    >
      {/* Image Background */}
      {image && (
        <div className="absolute inset-0 rounded-xl overflow-hidden opacity-20">
          <img src={image} alt={title} className="w-full h-full object-cover" />
        </div>
      )}

      <div className="relative flex items-start gap-4">
        {/* Icon */}
        {icon && (
          <div
            className={cn(
              'flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center',
              selected ? 'bg-primary-500' : 'bg-white/10'
            )}
          >
            {icon}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3
            className={cn(
              'font-semibold text-lg mb-1',
              selected ? 'text-white' : 'text-zinc-200'
            )}
          >
            {title}
          </h3>
          {description && (
            <p className="text-sm text-zinc-400">{description}</p>
          )}
        </div>

        {/* Check Icon */}
        {selected && (
          <div className="flex-shrink-0 w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center">
            <Check size={14} className="text-white" />
          </div>
        )}
      </div>
    </button>
  );
}
