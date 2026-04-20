import { useWizard } from '@/contexts/CharacterWizardContext';
import { WizardStep } from '../WizardStep';
import { SelectionCard } from '../SelectionCard';
import { Input } from '@/components/common';
import type { OutfitStyle } from '@/types/character';
import { Shirt, Sparkles, Dumbbell, Briefcase, Heart, Flame } from 'lucide-react';
import { OPTION_IMAGES } from '@/constants/optionImages';

const outfitStyles: {
  value: OutfitStyle;
  label: string;
  description: string;
  icon: React.ReactNode;
}[] = [
  {
    value: 'Casual',
    label: 'Casual',
    description: 'Relaxed and comfortable everyday wear',
    icon: <Shirt size={24} className="text-white" />,
  },
  {
    value: 'Elegant',
    label: 'Elegant',
    description: 'Sophisticated and refined attire',
    icon: <Sparkles size={24} className="text-white" />,
  },
  {
    value: 'Sporty',
    label: 'Sporty',
    description: 'Athletic and active clothing',
    icon: <Dumbbell size={24} className="text-white" />,
  },
  {
    value: 'Business',
    label: 'Business',
    description: 'Professional and polished look',
    icon: <Briefcase size={24} className="text-white" />,
  },
  {
    value: 'Romantic',
    label: 'Romantic',
    description: 'Soft and feminine styling',
    icon: <Heart size={24} className="text-white" />,
  },
  {
    value: 'Edgy',
    label: 'Edgy',
    description: 'Bold and alternative fashion',
    icon: <Flame size={24} className="text-white" />,
  },
];

export function Step5Outfit() {
  const { characterData, updateNestedField } = useWizard();

  return (
    <WizardStep
      title="Select Outfit Style"
      description="Choose the fashion style that matches your character's personality"
    >
      <div className="space-y-8">
        {/* Outfit Style */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Outfit Style</h3>
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
            {outfitStyles.map((style) => (
              <SelectionCard
                key={style.value}
                title={style.label}
                description={style.description}
                selected={characterData.outfit.style === style.value}
                onClick={() => updateNestedField('outfit.style', style.value)}
                image={OPTION_IMAGES.outfit[style.value as keyof typeof OPTION_IMAGES.outfit]}
                icon={style.icon}
                variant="visual"
              />
            ))}
          </div>
        </div>

        {/* Optional Description */}
        <div>
          <Input
            label="Additional Details (Optional)"
            placeholder="e.g., Floral dress with a sun hat..."
            value={characterData.outfit.description || ''}
            onChange={(e) => updateNestedField('outfit.description', e.target.value)}
            helperText="Describe specific clothing items or accessories"
          />
        </div>
      </div>
    </WizardStep>
  );
}
