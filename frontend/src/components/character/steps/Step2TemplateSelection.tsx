import { useEffect, useMemo, useState } from 'react';
import { WizardStep } from '../WizardStep';
import { SelectionCard } from '../SelectionCard';
import { useWizard } from '@/contexts/CharacterWizardContext';
import type { CharacterTemplateId, OutfitStyle, ScenePreset, VoiceProfile } from '@/types/character';
import { templateService, type FactoryTemplate } from '@/services/templateService';
import { Briefcase, Heart, Sparkles, Dumbbell, Home } from 'lucide-react';

interface TemplatePreset {
  id: CharacterTemplateId;
  name: string;
  description: string;
  icon: React.ReactNode;
  defaults?: {
    relation?: {
      character_role: string;
      user_role: string;
      relationship_tone: string;
    };
    personalityTags?: string[];
    relationshipType?: string;
    backgroundProfession?: string;
    sceneEnvironment?: ScenePreset;
    voiceProfile?: VoiceProfile;
    outfitStyle?: OutfitStyle;
  };
}

// Hardcoded fallback list shown when the API is unavailable
const FALLBACK_TEMPLATES: TemplatePreset[] = [
  {
    id: 'romance_barista',
    name: 'Romance Barista',
    description: 'A sweet barista who knows your usual order and your secrets.',
    icon: <Heart size={24} className="text-white" />,
    defaults: {
      relation: { character_role: 'barista', user_role: 'regular', relationship_tone: 'sweet' },
      personalityTags: ['gentle', 'romantic', 'flirty'],
      relationshipType: 'Girlfriend',
      backgroundProfession: 'Barista',
      sceneEnvironment: 'RainCafe',
      voiceProfile: 'Lovely_Girl',
      outfitStyle: 'Casual',
    },
  },
  {
    id: 'office_boss',
    name: 'Office Boss',
    description: 'A confident boss who keeps things sharp, focused, and intense.',
    icon: <Briefcase size={24} className="text-white" />,
    defaults: {
      relation: { character_role: 'boss', user_role: 'assistant', relationship_tone: 'dominant' },
      personalityTags: ['confident', 'serious', 'dominant'],
      relationshipType: 'Mentor',
      backgroundProfession: 'Executive',
      sceneEnvironment: 'Office',
      voiceProfile: 'Wise_Woman',
      outfitStyle: 'Business',
    },
  },
  {
    id: 'mystic_witch',
    name: 'Mystic Witch',
    description: 'A mysterious guide with arcane knowledge and quiet intensity.',
    icon: <Sparkles size={24} className="text-white" />,
    defaults: {
      relation: { character_role: 'witch', user_role: 'seeker', relationship_tone: 'mysterious' },
      personalityTags: ['mysterious', 'creative', 'intellectual'],
      relationshipType: 'Companion',
      backgroundProfession: 'Occultist',
      sceneEnvironment: 'Fantasy',
      voiceProfile: 'Abbess',
      outfitStyle: 'Elegant',
    },
  },
  {
    id: 'fitness_coach',
    name: 'Fitness Coach',
    description: 'Motivating, energetic, and always pushing you to be better.',
    icon: <Dumbbell size={24} className="text-white" />,
    defaults: {
      relation: { character_role: 'coach', user_role: 'trainee', relationship_tone: 'supportive' },
      personalityTags: ['confident', 'playful', 'adventurous'],
      relationshipType: 'Mentor',
      backgroundProfession: 'Fitness Coach',
      sceneEnvironment: 'Beach',
      voiceProfile: 'Lively_Girl',
      outfitStyle: 'Sporty',
    },
  },
  {
    id: 'girl_next_door',
    name: 'Girl Next Door',
    description: 'Warm, friendly, and familiar with a playful spark.',
    icon: <Home size={24} className="text-white" />,
    defaults: {
      relation: { character_role: 'neighbor', user_role: 'neighbor', relationship_tone: 'friendly' },
      personalityTags: ['caring', 'playful', 'funny'],
      relationshipType: 'Friend',
      backgroundProfession: 'Student',
      sceneEnvironment: 'CozyHome',
      voiceProfile: 'Sweet_Girl_2',
      outfitStyle: 'Casual',
    },
  },
];

const CUSTOM_TEMPLATE: TemplatePreset = {
  id: 'custom',
  name: 'Custom',
  description: 'Start from scratch and define every detail yourself.',
  icon: <Sparkles size={24} className="text-white" />,
};

// Icon lookup for API-loaded templates (matched by known IDs)
const ICON_MAP: Record<string, React.ReactNode> = {
  romance_barista: <Heart size={24} className="text-white" />,
  office_boss: <Briefcase size={24} className="text-white" />,
  mystic_witch: <Sparkles size={24} className="text-white" />,
  fitness_coach: <Dumbbell size={24} className="text-white" />,
  girl_next_door: <Home size={24} className="text-white" />,
};

function mapFactoryDataToDefaults(
  data: Record<string, unknown>,
): TemplatePreset['defaults'] {
  const rel = data.relation as Record<string, string> | undefined;
  const bg = data.background as Record<string, string> | undefined;
  const outfit = data.outfit as Record<string, string> | undefined;

  return {
    relation: rel
      ? {
          character_role: rel.relationship_role ?? '',
          user_role: rel.user_role ?? '',
          relationship_tone: rel.dynamic ?? '',
        }
      : undefined,
    personalityTags: (data.personality_tags as string[] | undefined) ?? [],
    relationshipType: (data.relationship_type as string | undefined) ?? undefined,
    backgroundProfession: bg?.occupation ?? undefined,
    sceneEnvironment: (data.scene_preset as ScenePreset | undefined) ?? undefined,
    voiceProfile: (data.voice_id as VoiceProfile | undefined) ?? undefined,
    outfitStyle: (outfit?.style as OutfitStyle | undefined) ?? undefined,
  };
}

function factoryTemplateToPreset(tmpl: FactoryTemplate): TemplatePreset {
  return {
    id: tmpl.id,
    name: tmpl.name,
    description: tmpl.description ?? '',
    icon: ICON_MAP[tmpl.id] ?? <Sparkles size={24} className="text-white" />,
    defaults: mapFactoryDataToDefaults(tmpl.data),
  };
}

export function Step2TemplateSelection() {
  const { characterData, updateField, updateNestedField } = useWizard();
  const [templates, setTemplates] = useState<TemplatePreset[]>(FALLBACK_TEMPLATES);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    templateService
      .listTemplates({ is_official: true })
      .then((items) => {
        if (cancelled) return;
        if (items.length > 0) setTemplates(items.map(factoryTemplateToPreset));
        // else: keep FALLBACK_TEMPLATES already in state
      })
      .catch(() => {
        // Keep fallback list already in state
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const applyTemplate = (template: TemplatePreset) => {
    updateField('template', {
      id: template.id,
      name: template.name,
      description: template.description,
    });

    const defaults = template.defaults;
    if (!defaults) {
      return;
    }

    if (defaults.relation) {
      updateField('relation', defaults.relation);
    }
    if (defaults.personalityTags) {
      updateNestedField('personality.tags', defaults.personalityTags);
    }
    if (defaults.relationshipType) {
      updateNestedField('personality.relationship', defaults.relationshipType);
    }
    if (defaults.backgroundProfession) {
      updateNestedField('background.profession', defaults.backgroundProfession);
    }
    if (defaults.sceneEnvironment) {
      updateNestedField('scene.environment', defaults.sceneEnvironment);
    }
    if (defaults.voiceProfile) {
      updateNestedField('voiceProfile', defaults.voiceProfile);
    }
    if (defaults.outfitStyle) {
      updateNestedField('outfit.style', defaults.outfitStyle);
    }
  };

  const allTemplates = useMemo(() => [...templates, CUSTOM_TEMPLATE], [templates]);

  return (
    <WizardStep
      title="Choose a Template"
      description="Pick a preset to get started faster, or build from scratch"
    >
      <div className="space-y-6">
        <div
          className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4"
          aria-busy={isLoading}
          aria-label={isLoading ? 'Loading templates' : undefined}
        >
          {isLoading
            ? Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={`skeleton-${i}`}
                  className="h-32 rounded-xl bg-white/5 border border-white/10 animate-pulse"
                />
              ))
            : allTemplates.map((template) => (
                <SelectionCard
                  key={template.id}
                  title={template.name}
                  description={template.description}
                  selected={characterData.template?.id === template.id}
                  onClick={() => applyTemplate(template)}
                  icon={template.icon}
                />
              ))}
        </div>

        <div className="p-4 rounded-lg bg-white/5 border border-white/10">
          <p className="text-sm text-zinc-400">
            Templates apply recommended defaults. You can customize everything later.
          </p>
        </div>
      </div>
    </WizardStep>
  );
}
