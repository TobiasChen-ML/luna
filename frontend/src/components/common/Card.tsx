import { cn } from '@/utils/cn';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  glass?: boolean;
}

export function Card({ children, className, glass = false }: CardProps) {
  return (
    <div
      className={cn(
        glass ? 'card-glass' : 'card',
        className
      )}
    >
      {children}
    </div>
  );
}
