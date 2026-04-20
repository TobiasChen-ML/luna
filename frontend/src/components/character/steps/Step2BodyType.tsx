import { useWizard } from '@/contexts/CharacterWizardContext';
import { WizardStep } from '../WizardStep';
import { SelectionCard } from '../SelectionCard';
import type { BodyType, SkinTone } from '@/types/character';
import { OPTION_IMAGES } from '@/constants/optionImages';

const bodyTypes: { value: BodyType; label: string; description: string }[] = [
  { value: 'Slim', label: 'Slim', description: 'Slender and graceful figure' },
  { value: 'Athletic', label: 'Athletic', description: 'Toned and fit physique' },
  { value: 'Curvy', label: 'Curvy', description: 'Curved and feminine silhouette' },
  { value: 'Plus Size', label: 'Plus Size', description: 'Full-figured and confident' },
];

const skinTones: { value: SkinTone; label: string; hex: string }[] = [
  { value: 'Fair', label: 'Fair', hex: '#FFE0D1' },
  { value: 'Light', label: 'Light', hex: '#F1C9AB' },
  { value: 'Medium', label: 'Medium', hex: '#D4A373' },
  { value: 'Olive', label: 'Olive', hex: '#C19A6B' },
  { value: 'Tan', label: 'Tan', hex: '#A67B5B' },
  { value: 'Deep', label: 'Deep', hex: '#8B5A3C' },
];

export function Step2BodyType() {
  const { characterData, updateNestedField } = useWizard();

  return (
    <WizardStep
      title="Customize Body Type"
      description="Choose the physical appearance that resonates with you"
    >
      <div className="space-y-8">
        {/* Body Type Selection */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Body Type</h3>
          <div className="grid sm:grid-cols-2 gap-4">
            {bodyTypes.map((type) => (
              <SelectionCard
                key={type.value}
                title={type.label}
                description={type.description}
                selected={characterData.appearance.bodyType === type.value}
                onClick={() => updateNestedField('appearance.bodyType', type.value)}
                image={OPTION_IMAGES.bodyType[type.value as keyof typeof OPTION_IMAGES.bodyType]}
                variant="visual"
              />
            ))}
          </div>
        </div>

        {/* Skin Tone Selection */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Skin Tone</h3>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
            {skinTones.map((tone) => (
              <button
                key={tone.value}
                onClick={() => updateNestedField('appearance.skinTone', tone.value)}
                className="group relative aspect-square rounded-xl border-2 transition-all hover:scale-110"
                style={{
                  backgroundColor: tone.hex,
                  borderColor:
                    characterData.appearance.skinTone === tone.value
                      ? '#FF3B7A'
                      : 'rgba(255,255,255,0.2)',
                }}
              >
                {/* Tooltip */}
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-black/80 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                  {tone.label}
                </div>

                {/* Selection ring */}
                {characterData.appearance.skinTone === tone.value && (
                  <div className="absolute inset-0 rounded-xl ring-4 ring-primary-500/50"></div>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>
    </WizardStep>
  );
}
