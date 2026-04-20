import { WizardStep } from '../WizardStep';
import { SelectionCard } from '../SelectionCard';
import { ColorPicker } from '../ColorPicker';
import { Input } from '@/components/common';
import { useWizard } from '@/contexts/CharacterWizardContext';
import type { BodyType, SkinTone, HairStyle, HairColor, EyeColor, OutfitStyle } from '@/types/character';
import { Shirt, Sparkles, Dumbbell, Briefcase, Heart, Flame } from 'lucide-react';
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

const eyeColors: { name: EyeColor; value: EyeColor; hex: string }[] = [
  { name: 'Blue', value: 'Blue', hex: '#4A90E2' },
  { name: 'Green', value: 'Green', hex: '#50C878' },
  { name: 'Brown', value: 'Brown', hex: '#8B4513' },
  { name: 'Hazel', value: 'Hazel', hex: '#8E7618' },
  { name: 'Gray', value: 'Gray', hex: '#808080' },
  { name: 'Amber', value: 'Amber', hex: '#FFBF00' },
  { name: 'Violet', value: 'Violet', hex: '#8F00FF' },
];

const lipColors = [
  { name: 'Rose', value: '#FF6B9D', hex: '#FF6B9D' },
  { name: 'Coral', value: '#FF7F50', hex: '#FF7F50' },
  { name: 'Berry', value: '#C0506B', hex: '#C0506B' },
  { name: 'Natural', value: '#E8B4B8', hex: '#E8B4B8' },
  { name: 'Red', value: '#DC143C', hex: '#DC143C' },
  { name: 'Nude', value: '#D4A5A5', hex: '#D4A5A5' },
];

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

export function Step4Appearance() {
  const { characterData, updateNestedField } = useWizard();

  return (
    <WizardStep
      title="Customize Appearance"
      description="Define the physical look of your character"
    >
      <div className="space-y-10">
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
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-black/80 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                  {tone.label}
                </div>
                {characterData.appearance.skinTone === tone.value && (
                  <div className="absolute inset-0 rounded-xl ring-4 ring-primary-500/50"></div>
                )}
              </button>
            ))}
          </div>
        </div>

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

        <div>
          <ColorPicker
            label="Hair Color"
            options={hairColors}
            selected={characterData.hair.color}
            onSelect={(color) => updateNestedField('hair.color', color)}
          />
        </div>

        <div>
          <ColorPicker
            label="Eye Color"
            options={eyeColors}
            selected={characterData.face.eyeColor}
            onSelect={(color) => updateNestedField('face.eyeColor', color)}
          />
        </div>

        <div>
          <ColorPicker
            label="Lip Color"
            options={lipColors}
            selected={characterData.face.lipColor}
            onSelect={(color) => updateNestedField('face.lipColor', color)}
          />
        </div>

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

        <div>
          <Input
            label="Additional Outfit Details (Optional)"
            placeholder="e.g., Floral dress with a sun hat"
            value={characterData.outfit.description || ''}
            onChange={(e) => updateNestedField('outfit.description', e.target.value)}
            helperText="Describe specific clothing items or accessories"
          />
        </div>
      </div>
    </WizardStep>
  );
}
