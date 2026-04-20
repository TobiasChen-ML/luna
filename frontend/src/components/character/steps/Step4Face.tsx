import { useWizard } from '@/contexts/CharacterWizardContext';
import { WizardStep } from '../WizardStep';
import { ColorPicker } from '../ColorPicker';
import type { EyeColor } from '@/types/character';

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

export function Step4Face() {
  const { characterData, updateNestedField } = useWizard();

  return (
    <WizardStep
      title="Define Face Features"
      description="Choose the eye color and lip shade that bring your character to life"
    >
      <div className="space-y-8">
        {/* Eye Color */}
        <div>
          <ColorPicker
            label="Eye Color"
            options={eyeColors}
            selected={characterData.face.eyeColor}
            onSelect={(color) => updateNestedField('face.eyeColor', color)}
          />
        </div>

        {/* Lip Color */}
        <div>
          <ColorPicker
            label="Lip Color"
            options={lipColors}
            selected={characterData.face.lipColor}
            onSelect={(color) => updateNestedField('face.lipColor', color)}
          />
        </div>

        <div className="mt-8 p-4 rounded-lg bg-white/5 border border-white/10">
          <p className="text-sm text-zinc-400 text-center">
            These details will help generate a unique and personalized character image
          </p>
        </div>
      </div>
    </WizardStep>
  );
}
