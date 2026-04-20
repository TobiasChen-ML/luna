import { wizardSteps } from '@/types/character';
import { useWizard } from '@/contexts/CharacterWizardContext';
import { Check } from 'lucide-react';
import { cn } from '@/utils/cn';

export function WizardProgress() {
  const { currentStep, goToStep, characterData } = useWizard();

  return (
    <div className="w-full py-8">
      {/* Mobile: Current step indicator */}
      <div className="md:hidden text-center mb-4">
        <p className="text-sm text-zinc-400">
          Step {currentStep} of {wizardSteps.length}
        </p>
        <h2 className="text-xl font-heading font-bold mt-1">
          {wizardSteps[currentStep - 1].title}
        </h2>
        {wizardSteps[currentStep - 1].optional && (
          <p className="text-xs text-zinc-500 mt-1">Optional</p>
        )}
      </div>

      {/* Desktop: Full stepper */}
      <div className="hidden md:block">
        <div className="flex items-center justify-between">
          {wizardSteps.map((step, index) => {
            const stepNumber = index + 1;
            const isActive = stepNumber === currentStep;
            const isCompleted = wizardSteps[index].validate(characterData);
            const isPast = stepNumber < currentStep;

            return (
              <div key={stepNumber} className="flex-1 flex items-center">
                {/* Step Circle */}
                <button
                  onClick={() => goToStep(stepNumber)}
                  className={cn(
                    'relative flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all',
                    isActive && 'border-primary-500 bg-primary-500/10',
                    isPast && isCompleted && 'border-primary-500 bg-primary-500',
                    !isActive && !isPast && 'border-white/20 bg-white/5',
                    'hover:scale-105'
                  )}
                >
                  {isPast && isCompleted ? (
                    <Check size={20} className="text-white" />
                  ) : (
                    <span
                      className={cn(
                        'text-sm font-semibold',
                        isActive && 'text-primary-500',
                        isPast && 'text-white',
                        !isActive && !isPast && 'text-zinc-500'
                      )}
                    >
                      {stepNumber}
                    </span>
                  )}

                  {/* Step label */}
                  <div className="absolute top-full mt-2 w-32 text-center">
                    <p
                      className={cn(
                        'text-xs font-medium',
                        isActive && 'text-white',
                        !isActive && 'text-zinc-500'
                      )}
                    >
                      {step.title}
                    </p>
                    {step.optional && (
                      <p className="text-[10px] text-zinc-500 mt-1">Optional</p>
                    )}
                  </div>
                </button>

                {/* Connector Line */}
                {stepNumber < wizardSteps.length && (
                  <div className="flex-1 h-0.5 mx-2">
                    <div
                      className={cn(
                        'h-full transition-all',
                        isPast ? 'bg-primary-500' : 'bg-white/20'
                      )}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Mobile: Progress bar */}
      <div className="md:hidden mt-4">
        <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-primary transition-all duration-300"
            style={{ width: `${(currentStep / wizardSteps.length) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
