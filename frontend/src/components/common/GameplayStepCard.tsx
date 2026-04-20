import { cn } from '@/utils/cn';

interface GameplayStepCardProps {
  step: string;
  title: string;
  description: string;
  icon?: React.ReactNode;
  className?: string;
}

export function GameplayStepCard({
  step,
  title,
  description,
  icon,
  className,
}: GameplayStepCardProps) {
  return (
    <div className={cn('card-glass space-y-4', className)}>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-gradient-primary rounded-xl flex items-center justify-center">
          {icon}
        </div>
        <span className="text-xs font-semibold tracking-[0.3em] text-primary-300">
          {step}
        </span>
      </div>
      <h3 className="text-2xl font-heading font-bold">{title}</h3>
      <p className="text-zinc-400">{description}</p>
    </div>
  );
}
