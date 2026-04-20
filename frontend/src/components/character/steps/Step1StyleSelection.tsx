import { useWizard } from '@/contexts/CharacterWizardContext';
import { WizardStep } from '../WizardStep';
import { SelectionCard } from '../SelectionCard';
import { OPTION_IMAGES } from '@/constants/optionImages';
import { useEffect } from 'react';

export function Step1StyleSelection() {
  const { characterData, updateField } = useWizard();

  useEffect(() => {
    if (characterData.gender !== 'Female') {
      updateField('gender', 'Female');
    }
  }, [characterData.gender, updateField]);

  return (
    <WizardStep
      title="Choose Your Character Style"
      description="Select art style"
    >
      <div className="space-y-8">
        <div>
          <h3 className="text-lg font-semibold mb-4">Style</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <SelectionCard
              title="Realistic"
              description="Photorealistic characters with lifelike details and natural appearance"
              selected={characterData.style === 'Realistic'}
              onClick={() => updateField('style', 'Realistic')}
              image={OPTION_IMAGES.style.Realistic}
              variant="visual"
            />

            <SelectionCard
              title="Anime"
              description="Stylized anime characters with expressive features and vibrant aesthetics"
              selected={characterData.style === 'Anime'}
              onClick={() => updateField('style', 'Anime')}
              image={OPTION_IMAGES.style.Anime}
              variant="visual"
            />
          </div>
        </div>

        <div className="mt-8 p-4 rounded-lg bg-primary-500/10 border border-primary-500/20">
          <p className="text-sm text-zinc-300 text-center">
            Tip: You can change these later.
          </p>
        </div>
      </div>
    </WizardStep>
  );
}
