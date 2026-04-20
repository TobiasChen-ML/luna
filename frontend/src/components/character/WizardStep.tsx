import { Card } from '@/components/common';
import { cn } from '@/utils/cn';

interface WizardStepProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export function WizardStep({ title, description, children, className }: WizardStepProps) {
  return (
    <div className={cn('w-full max-w-4xl mx-auto', className)}>
      <div className="text-center mb-8">
        <h2 className="text-3xl md:text-4xl font-heading font-bold mb-2">
          {title}
        </h2>
        {description && (
          <p className="text-lg text-zinc-400">
            {description}
          </p>
        )}
      </div>

      <Card glass className="p-8">
        {children}
      </Card>
    </div>
  );
}
