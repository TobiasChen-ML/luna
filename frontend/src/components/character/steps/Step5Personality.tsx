import { useWizard } from '@/contexts/CharacterWizardContext';
import { WizardStep } from '../WizardStep';
import { TagSelector } from '../TagSelector';
import { SelectionCard } from '../SelectionCard';
import { ForceRoutingSelector } from '../ForceRoutingSelector';
import type { PersonalityTrait, RelationshipType } from '@/types/character';
import { Heart, Users, User, Crown, Lightbulb } from 'lucide-react';
import { OPTION_IMAGES } from '@/constants/optionImages';

const personalityTraits: PersonalityTrait[] = [
  'gentle',
  'caring',
  'playful',
  'mysterious',
  'confident',
  'shy',
  'adventurous',
  'intellectual',
  'romantic',
  'flirty',
  'dominant',
  'submissive',
  'funny',
  'serious',
  'creative',
];

const relationshipTypes: {
  value: RelationshipType;
  label: string;
  description: string;
  icon: React.ReactNode;
}[] = [
  {
    value: 'Friend',
    label: 'Friend',
    description: 'Close companion and confidant',
    icon: <Users size={20} className="text-white" />,
  },
  {
    value: 'Girlfriend',
    label: 'Girlfriend',
    description: 'Romantic partner',
    icon: <Heart size={20} className="text-white" />,
  },
  {
    value: 'Wife',
    label: 'Wife',
    description: 'Life partner and spouse',
    icon: <Crown size={20} className="text-white" />,
  },
  {
    value: 'Companion',
    label: 'Companion',
    description: 'Loyal and devoted partner',
    icon: <User size={20} className="text-white" />,
  },
  {
    value: 'Mentor',
    label: 'Mentor',
    description: 'Wise guide and advisor',
    icon: <Lightbulb size={20} className="text-white" />,
  },
];

export function Step5Personality() {
  const { characterData, updateNestedField, updateField } = useWizard();

  return (
    <WizardStep
      title="Define Personality"
      description="Create a unique personality and tone"
    >
      <div className="space-y-8">
        <div>
          <TagSelector
            label="Personality Traits"
            options={personalityTraits}
            selected={characterData.personality.tags}
            onSelect={(tags) => updateNestedField('personality.tags', tags)}
            maxSelection={5}
            helperText="Select up to 5 traits that define your character"
          />
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-4">Relationship Type</h3>
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
            {relationshipTypes.map((type) => (
              <SelectionCard
                key={type.value}
                title={type.label}
                description={type.description}
                selected={characterData.personality.relationship === type.value}
                onClick={() => updateNestedField('personality.relationship', type.value)}
                image={OPTION_IMAGES.relationship[type.value as keyof typeof OPTION_IMAGES.relationship]}
                icon={type.icon}
                variant="visual"
              />
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-2">
            Personality Summary (Optional)
          </label>
          <textarea
            value={characterData.personalitySummary || ''}
            onChange={(e) => updateField('personalitySummary', e.target.value.slice(0, 300))}
            maxLength={300}
            rows={4}
            placeholder="Describe your character in a few sentences (max 300 characters)"
            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
          />
          <div className="flex justify-between items-center mt-1">
            <p className="text-xs text-zinc-500">
              This summary helps keep your character consistent.
            </p>
            <p className="text-xs text-zinc-500">
              {characterData.personalitySummary?.length || 0}/300
            </p>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-2">
            Personality Example (Optional)
          </label>
          <textarea
            value={characterData.personalityExample || ''}
            onChange={(e) => updateField('personalityExample', e.target.value.slice(0, 800))}
            maxLength={800}
            rows={5}
            placeholder="Write a short example of how the character speaks or reacts."
            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
          />
          <p className="text-xs text-zinc-500 mt-1">
            You can include dialogue or action to anchor tone and voice.
          </p>
        </div>

        <div className="p-6 rounded-lg bg-white/5 border border-white/10">
          <ForceRoutingSelector
            currentInstruction={characterData.consistency_config?.force_prefix || ''}
            onSelect={(instruction) => {
              updateNestedField('consistency_config.force_prefix', instruction);
            }}
            showCustomInput={true}
          />
        </div>
      </div>
    </WizardStep>
  );
}
