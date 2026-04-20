/**
 * IntimacyMeter Component (PRD v2026.02)
 *
 * Displays relationship intimacy as a filling heart with smooth animations.
 */
import { useState, useEffect } from 'react';
import { Heart } from 'lucide-react';
import { cn } from '@/utils/cn';

interface IntimacyMeterProps {
  value: number;  // 0-100
  characterName: string;
  onChange?: (newValue: number) => void;  // For admin testing
  className?: string;
}

// Relationship stage thresholds
const STAGE_THRESHOLDS = {
  stranger: { min: 0, max: 10, label: 'Stranger', color: 'text-zinc-500' },
  acquaintance: { min: 10, max: 30, label: 'Acquaintance', color: 'text-blue-400' },
  friend: { min: 30, max: 50, label: 'Friend', color: 'text-green-400' },
  close_friend: { min: 50, max: 70, label: 'Close Friend', color: 'text-yellow-400' },
  companion: { min: 70, max: 90, label: 'Companion', color: 'text-orange-400' },
  intimate: { min: 90, max: 100, label: 'Intimate', color: 'text-pink-400' },
};

function getStage(value: number) {
  for (const [key, stage] of Object.entries(STAGE_THRESHOLDS)) {
    if (value >= stage.min && value < stage.max) {
      return { key, ...stage };
    }
  }
  return { key: 'intimate', ...STAGE_THRESHOLDS.intimate };
}

export function IntimacyMeter({
  value,
  characterName,
  onChange,
  className,
}: IntimacyMeterProps) {
  const [displayValue, setDisplayValue] = useState(value);
  const [showTooltip, setShowTooltip] = useState(false);
  const [previousValue, setPreviousValue] = useState(value);

  // Animate value changes
  useEffect(() => {
    if (value === displayValue) return;

    const diff = value - displayValue;
    const step = diff / 10;  // 10 animation steps
    const duration = 500;  // 500ms total animation
    const interval = duration / 10;

    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep++;
      if (currentStep >= 10) {
        setDisplayValue(value);
        clearInterval(timer);
      } else {
        setDisplayValue(prev => prev + step);
      }
    }, interval);

    setPreviousValue(displayValue);

    return () => clearInterval(timer);
  }, [value]);

  const stage = getStage(displayValue);
  const fillPercentage = Math.max(0, Math.min(100, displayValue));

  // Heart fill gradient based on intimacy level
  const getHeartColor = (percentage: number): string => {
    if (percentage < 10) return '#71717a'; // zinc-500
    if (percentage < 30) return '#60a5fa'; // blue-400
    if (percentage < 50) return '#4ade80'; // green-400
    if (percentage < 70) return '#facc15'; // yellow-400
    if (percentage < 90) return '#fb923c'; // orange-400
    return '#f472b6'; // pink-400
  };

  const heartColor = getHeartColor(fillPercentage);
  const hasChanged = value !== previousValue;
  const changeAmount = value - previousValue;

  return (
    <div className={cn('relative', className)}>
      {/* Heart Icon with Fill */}
      <div
        className="relative cursor-pointer"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => onChange?.(Math.min(100, value + 10))}  // Admin: click to increase
      >
        {/* Background Heart (outline) */}
        <Heart className={cn('w-8 h-8', stage.color)} strokeWidth={2} />

        {/* Filled Heart (animated) */}
        <div
          className="absolute inset-0 overflow-hidden transition-all duration-500"
          style={{
            clipPath: `inset(${100 - fillPercentage}% 0 0 0)`,
          }}
        >
          <Heart
            className="w-8 h-8"
            fill={heartColor}
            stroke={heartColor}
            strokeWidth={2}
          />
        </div>

        {/* Pulse animation on change */}
        {hasChanged && (
          <div
            className="absolute inset-0 rounded-full animate-ping opacity-75"
            style={{
              background: `radial-gradient(circle, ${heartColor}40 0%, transparent 70%)`,
            }}
          />
        )}

        {/* Change indicator */}
        {hasChanged && Math.abs(changeAmount) > 0 && (
          <div
            className={cn(
              'absolute -top-2 -right-2 text-xs font-bold px-1.5 py-0.5 rounded-full',
              'animate-fade-in-out',
              changeAmount > 0
                ? 'bg-green-500/20 text-green-400'
                : 'bg-red-500/20 text-red-400'
            )}
          >
            {changeAmount > 0 ? '+' : ''}{changeAmount}
          </div>
        )}
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 animate-fade-in">
          <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-3 shadow-xl min-w-[180px]">
            <div className="text-sm font-medium text-white mb-1">
              {characterName}'s Intimacy
            </div>

            {/* Progress Bar */}
            <div className="relative h-2 bg-zinc-800 rounded-full overflow-hidden mb-2">
              <div
                className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                style={{
                  width: `${fillPercentage}%`,
                  backgroundColor: heartColor,
                }}
              />
            </div>

            {/* Stage and Value */}
            <div className="flex items-center justify-between text-xs">
              <span className={cn('font-medium', stage.color)}>
                {stage.label}
              </span>
              <span className="text-zinc-400">
                {displayValue.toFixed(0)}/100
              </span>
            </div>

            {/* Stage Progress */}
            <div className="text-xs text-zinc-500 mt-1">
              {displayValue < 100 ? (
                <>
                  {Math.max(0, getStage(displayValue + 1).min - displayValue)} to{' '}
                  {getStage(displayValue + 1).label}
                </>
              ) : (
                'Maximum intimacy reached!'
              )}
            </div>
          </div>

          {/* Tooltip arrow */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px">
            <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-zinc-700" />
          </div>
        </div>
      )}

      {/* Custom CSS for animations */}
      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes fade-in-out {
          0% {
            opacity: 0;
            transform: scale(0.8);
          }
          20% {
            opacity: 1;
            transform: scale(1);
          }
          80% {
            opacity: 1;
            transform: scale(1);
          }
          100% {
            opacity: 0;
            transform: scale(0.8);
          }
        }

        .animate-fade-in {
          animation: fade-in 0.2s ease-out;
        }

        .animate-fade-in-out {
          animation: fade-in-out 2s ease-out forwards;
        }
      `}</style>
    </div>
  );
}

/**
 * Compact variant for space-constrained areas
 */
export function IntimacyMeterCompact({
  value,
  className,
}: {
  value: number;
  className?: string;
}) {
  const stage = getStage(value);
  const fillPercentage = Math.max(0, Math.min(100, value));

  const getHeartColor = (percentage: number): string => {
    if (percentage < 10) return '#71717a';
    if (percentage < 30) return '#60a5fa';
    if (percentage < 50) return '#4ade80';
    if (percentage < 70) return '#facc15';
    if (percentage < 90) return '#fb923c';
    return '#f472b6';
  };

  const heartColor = getHeartColor(fillPercentage);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="relative">
        <Heart className="w-5 h-5 text-zinc-600" strokeWidth={2} />
        <div
          className="absolute inset-0 overflow-hidden transition-all duration-500"
          style={{
            clipPath: `inset(${100 - fillPercentage}% 0 0 0)`,
          }}
        >
          <Heart
            className="w-5 h-5"
            fill={heartColor}
            stroke={heartColor}
            strokeWidth={2}
          />
        </div>
      </div>
      <span className={cn('text-sm font-medium', stage.color)}>
        {value.toFixed(0)}%
      </span>
    </div>
  );
}
