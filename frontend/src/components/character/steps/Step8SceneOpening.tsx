import { WizardStep } from '../WizardStep';
import { SelectionCard } from '../SelectionCard';
import { useWizard } from '@/contexts/CharacterWizardContext';
import type { ScenePreset } from '@/types/character';
import { Moon, Sun, Sparkles, Coffee, Building, CloudRain } from 'lucide-react';

const scenes: {
  value: ScenePreset;
  label: string;
  description: string;
  icon: React.ReactNode;
}[] = [
  {
    value: 'Office',
    label: 'Office',
    description: 'Professional setting with focused energy',
    icon: <Building size={20} className="text-white" />,
  },
  {
    value: 'Beach',
    label: 'Beach',
    description: 'Warm breeze and relaxed vibes',
    icon: <Sun size={20} className="text-white" />,
  },
  {
    value: 'Fantasy',
    label: 'Fantasy',
    description: 'Mystical and story-driven atmosphere',
    icon: <Sparkles size={20} className="text-white" />,
  },
  {
    value: 'NightCity',
    label: 'Night City',
    description: 'Neon lights and late-night energy',
    icon: <Moon size={20} className="text-white" />,
  },
  {
    value: 'CozyHome',
    label: 'Cozy Home',
    description: 'Comfortable and intimate setting',
    icon: <Coffee size={20} className="text-white" />,
  },
  {
    value: 'RainCafe',
    label: 'Rain Cafe',
    description: 'Soft rain and a warm cafe mood',
    icon: <CloudRain size={20} className="text-white" />,
  },
];

export function Step8SceneOpening() {
  const { characterData, updateNestedField } = useWizard();

  return (
    <WizardStep
      title="Scene and Opening"
      description="Set the initial atmosphere and greeting"
    >
      <div className="space-y-8">
        <div>
          <h3 className="text-lg font-semibold mb-4">Scene Preset</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {scenes.map((scene) => (
              <SelectionCard
                key={scene.value}
                title={scene.label}
                description={scene.description}
                selected={characterData.scene?.environment === scene.value}
                onClick={() => updateNestedField('scene.environment', scene.value)}
                icon={scene.icon}
              />
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-2">
            Opening Message (Optional)
          </label>
          <textarea
            value={characterData.scene?.openingMessage || ''}
            onChange={(e) => updateNestedField('scene.openingMessage', e.target.value)}
            placeholder="Write the first line your character will say"
            rows={4}
            className="input resize-none"
          />
          <p className="text-xs text-zinc-500 mt-1">
            You can use {'{{user}}'} and {'{{char}}'} placeholders.
          </p>
        </div>
      </div>
    </WizardStep>
  );
}
