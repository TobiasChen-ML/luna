import { useWizard } from '@/contexts/CharacterWizardContext';
import { WizardStep } from '../WizardStep';
import { ColorPicker } from '../ColorPicker';
import { SelectionCard } from '../SelectionCard';
import type { HairStyle, HairColor } from '@/types/character';
import { OPTION_IMAGES } from '@/constants/optionImages';

const hairStyles: { value: HairStyle; label: string; description: string }[] = [
  { value: 'Long', label: 'Long', description: 'Flowing long hair' },
  { value: 'Short', label: 'Short', description: 'Stylish short cut' },
  { value: 'Medium', label: 'Medium', description: 'Shoulder-length' },
  { value: 'Wavy', label: 'Wavy', description: 'Natural waves' },
  { value: 'Curly', label: 'Curly', description: 'Bouncy curls' },
  { value: 'Straight', label: 'Straight', description: 'Sleek and straight' },
];

const hairColors: { name: HairColor; value: HairColor; hex: string }[] = [
  { name: 'Blonde', value: 'Blonde', hex: '#F5E6D3' },
  { name: 'Brown', value: 'Brown', hex: '#8B5A3C' },
  { name: 'Black', value: 'Black', hex: '#1A1A1A' },
  { name: 'Red', value: 'Red', hex: '#C84630' },
  { name: 'Silver', value: 'Silver', hex: '#C0C0C0' },
  { name: 'Pink', value: 'Pink', hex: '#FF69B4' },
  { name: 'Blue', value: 'Blue', hex: '#4169E1' },
  { name: 'Purple', value: 'Purple', hex: '#9370DB' },
];

export function Step3Hair() {
  const { characterData, updateNestedField } = useWizard();

  return (
    <WizardStep
      title="Style the Hair"
      description="Choose a hairstyle and color that captures your character's essence"
    >
      <div className="space-y-8">
        {/* Hair Style */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Hair Style</h3>
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
            {hairStyles.map((style) => (
              <SelectionCard
                key={style.value}
                title={style.label}
                description={style.description}
                selected={characterData.hair.style === style.value}
                onClick={() => updateNestedField('hair.style', style.value)}
                image={OPTION_IMAGES.hairStyle[style.value as keyof typeof OPTION_IMAGES.hairStyle]}
                variant="visual"
              />
            ))}
          </div>
        </div>

        {/* Hair Color */}
        <div>
          <ColorPicker
            label="Hair Color"
            options={hairColors}
            selected={characterData.hair.color}
            onSelect={(color) => updateNestedField('hair.color', color)}
          />
        </div>
      </div>
    </WizardStep>
  );
}
