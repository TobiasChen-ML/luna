import { useWizard } from '@/contexts/CharacterWizardContext';
import { Button } from '@/components/common';
import { ArrowLeft, ArrowRight, Sparkles, Shuffle } from 'lucide-react';
import { wizardSteps } from '@/types/character';

interface WizardNavigationProps {
  onComplete?: () => void;
}

export function WizardNavigation({ onComplete }: WizardNavigationProps) {
  const {
    currentStep,
    canProceed,
    nextStep,
    previousStep,
    isComplete,
    randomizeStep,
    skipStep,
  } = useWizard();

  const currentConfig = wizardSteps[currentStep - 1];
  const canSkip = !!currentConfig?.optional && !canProceed;

  const handleNext = () => {
    if (isComplete && onComplete) {
      onComplete();
    } else {
      nextStep();
    }
  };

  const handleSkip = () => {
    const warning = currentConfig?.skipWarning || 'Skip this step? You can edit later.';
    if (window.confirm(warning)) {
      skipStep();
    }
  };

  return (
    <div className="flex items-center justify-between gap-4 py-6 border-t border-white/10">
      {/* Back Button */}
      <Button
        variant="ghost"
        onClick={previousStep}
        disabled={currentStep === 1}
        className="min-w-[120px]"
      >
        <ArrowLeft size={16} className="mr-2" />
        Back
      </Button>

      {/* Randomize Button */}
      <Button
        variant="outline"
        onClick={randomizeStep}
        className="hidden md:flex"
      >
        <Shuffle size={16} className="mr-2" />
        Randomize
      </Button>

      {/* Skip Button */}
      {canSkip && (
        <Button
          variant="ghost"
          onClick={handleSkip}
          className="min-w-[100px]"
        >
          Skip
        </Button>
      )}

      {/* Next/Complete Button */}
      <Button
        variant="primary"
        onClick={handleNext}
        disabled={!canProceed}
        className="min-w-[120px]"
      >
        {isComplete ? (
          <>
            <Sparkles size={16} className="mr-2" />
            Create Character
          </>
        ) : (
          <>
            Next
            <ArrowRight size={16} className="ml-2" />
          </>
        )}
      </Button>
    </div>
  );
}
