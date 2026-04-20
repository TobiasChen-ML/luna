// Character Wizard Step Types
export type CharacterStyle = 'Realistic' | 'Anime';
export type CharacterGender = 'Female' | 'Male';
export type CharacterTemplateId =
  | 'romance_barista'
  | 'office_boss'
  | 'mystic_witch'
  | 'fitness_coach'
  | 'girl_next_door'
  | 'custom'
  // Allow dynamic IDs from Character Factory while keeping autocomplete for known IDs
  | (string & {});

// Body Types
export type BodyType = 'Slim' | 'Athletic' | 'Curvy' | 'Plus Size';

// Hair
export type HairStyle = 'Long' | 'Short' | 'Medium' | 'Wavy' | 'Curly' | 'Straight';
export type HairColor = 'Blonde' | 'Brown' | 'Black' | 'Red' | 'Silver' | 'Pink' | 'Blue' | 'Purple';

// Eyes
export type EyeColor = 'Blue' | 'Green' | 'Brown' | 'Hazel' | 'Gray' | 'Amber' | 'Violet';

// Skin
export type SkinTone = 'Fair' | 'Light' | 'Medium' | 'Olive' | 'Tan' | 'Deep';

// Outfit
export type OutfitStyle = 'Casual' | 'Elegant' | 'Sporty' | 'Business' | 'Romantic' | 'Edgy';

// Personality
export type PersonalityTrait =
  | 'gentle' | 'caring' | 'playful' | 'mysterious' | 'confident'
  | 'shy' | 'adventurous' | 'intellectual' | 'romantic' | 'flirty'
  | 'dominant' | 'submissive' | 'funny' | 'serious' | 'creative';

// Relationship
export type RelationshipType = 'Friend' | 'Girlfriend' | 'Wife' | 'Companion' | 'Mentor';

// Race Types
export type RaceType = 'white race' | 'black race' | 'yellow race';

// Voice - Novita MiniMax Speech Female Voices + Additional Voices
export type VoiceProfile =
  | 'ASMR_Whisperer'
  | 'Sensual_Hypnotic'
  | 'Soft_Husky'
  | 'Mysterious_Warm'
  | 'Hollywood_Actress'
  | 'Inspirational_girl'
  | 'Cute_girl'
  | 'Lovely_Girl'
  | 'Sweet_Girl_2'
  | 'Lively_Girl'
  | 'Exuberant_Girl'
  | 'Calm_Woman'
  | 'Wise_Woman'
  | 'Decent_Boy'
  | 'Magnetic_boy'
  | 'Friendly_Person'
  | 'Abbess'
  | 'Seductive_Calm'
  | 'Meditative_ASMR';

export type ScenePreset =
  | 'Office'
  | 'Beach'
  | 'Fantasy'
  | 'NightCity'
  | 'CozyHome'
  | 'RainCafe';

// Character Wizard Data Structure
export interface CharacterWizardData {
  // Step 1: Style Selection
  gender: CharacterGender;
  style?: CharacterStyle;

  // Step 2: Template Selection
  template?: {
    id?: CharacterTemplateId;
    name?: string;
    description?: string;
  };

  // Step 4: Appearance
  appearance: {
    bodyType?: BodyType;
    skinTone?: SkinTone;
  };

  // Step 3: Relationship Identity (NEW - PRD v2026.02)
  relation?: {
    character_role: string;
    user_role: string;
    relationship_tone: string;
    relationship_type?: string;
  };

  // Step 4: Hair
  hair: {
    style?: HairStyle;
    color?: HairColor;
  };

  // Step 4: Face Features
  face: {
    eyeColor?: EyeColor;
    lipColor?: string;
  };

  // Step 4: Outfit
  outfit: {
    style?: OutfitStyle;
    description?: string;
  };

  // Step 5: Personality & Chat Style
  personality: {
    tags: PersonalityTrait[];
    relationship?: RelationshipType;
  };
  personalityExample?: string;

  // Step 7: Background & Boundaries
  background: {
    profession?: string;
    hobbies?: string[];
    backstory?: string;
  };

  preferences?: {
    likes?: string[];
    dislikes?: string[];
  };

  chatRules?: {
    mandatory?: {
      disallowed_topics?: string[];
      safety_level?: 'R13' | 'ADULT';
    };
    anchors?: {
      tone_voice?: string;
      keywords?: string[];
      quirks?: string[];
      catchphrases?: string[];
      secrets?: string[];
    };
    interaction?: {
      role_type?: 'guiding' | 'dependent' | 'passive';
      guidance_notes?: string;
    };
  };

  // Step 8: Scene & Opening Message
  scene?: {
    environment?: ScenePreset;
    openingMessage?: string;
  };

  // Step 9: Identity & Confirmation
  identity: {
    firstName?: string;
    age?: number;
    race?: RaceType;
  };

  avatarUrl?: string;
  voiceProfile?: VoiceProfile;

  // v3.1 Three-Part Character Schema
  personalitySummary?: string; // Max 300 chars

  // Force Character Routing (PRD v2026.02)
  consistency_config?: {
    force_prefix?: string;
  };
}

// Random selection helpers
const randomFrom = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

const skinTones: SkinTone[] = ['Fair', 'Light', 'Medium', 'Olive', 'Tan', 'Deep'];
const hairStyles: HairStyle[] = ['Long', 'Short', 'Medium', 'Wavy', 'Curly', 'Straight'];
const hairColors: HairColor[] = ['Blonde', 'Brown', 'Black', 'Red', 'Silver', 'Pink', 'Blue', 'Purple'];
const eyeColors: EyeColor[] = ['Blue', 'Green', 'Brown', 'Hazel', 'Gray', 'Amber', 'Violet'];
const lipColors = ['#FF6B9D', '#E85A71', '#D4426D', '#C43A5E', '#FF8FA3', '#FFB3C1'];

// Generate random values for hidden steps
export const generateRandomAppearance = () => ({
  gender: 'Female' as CharacterGender,
  style: randomFrom(['Realistic', 'Anime'] as CharacterStyle[]),
  appearance: {
    bodyType: 'Slim' as BodyType,
    skinTone: randomFrom(skinTones),
  },
  hair: {
    style: randomFrom(hairStyles),
    color: randomFrom(hairColors),
  },
  face: {
    eyeColor: randomFrom(eyeColors),
    lipColor: randomFrom(lipColors),
  },
});

// Initial state with defaults for hidden steps (1-4)
export const initialCharacterData: CharacterWizardData = {
  ...generateRandomAppearance(),
  template: {
    id: 'custom',
    name: 'Custom',
    description: 'Start from scratch',
  },
  relation: {
    character_role: '',
    user_role: '',
    relationship_tone: 'sweet',
  },
  outfit: {},
  personality: {
    tags: [],
  },
  background: {},
  preferences: {
    likes: [],
    dislikes: [],
  },
  chatRules: {
    mandatory: {
      disallowed_topics: [],
      safety_level: 'ADULT',
    },
    anchors: {
      tone_voice: 'warm_friendly',
      keywords: [],
      quirks: [],
      catchphrases: [],
      secrets: [],
    },
    interaction: {
      role_type: 'guiding',
    },
  },
  scene: {
    environment: 'CozyHome',
    openingMessage: '',
  },
  identity: {},
  avatarUrl: undefined,
};

// Wizard Step Configuration
export interface WizardStep {
  step: number;
  title: string;
  description: string;
  validate: (data: CharacterWizardData) => boolean;
  optional?: boolean;
  skipWarning?: string;
}

export const wizardSteps: WizardStep[] = [
  {
    step: 1,
    title: 'Style',
    description: 'Pick a style',
    validate: (data) => !!data.style,
  },
  {
    step: 2,
    title: 'Relationship',
    description: 'Define your relationship dynamic',
    validate: (data) =>
      !!data.relation?.character_role &&
      !!data.relation?.user_role &&
      !!data.relation?.relationship_tone,
  },
  {
    step: 3,
    title: 'Appearance',
    description: 'Body, hair, face, and outfit',
    validate: (data) =>
      !!data.appearance.bodyType &&
      !!data.appearance.skinTone &&
      !!data.hair.style &&
      !!data.hair.color &&
      !!data.face.eyeColor &&
      !!data.face.lipColor &&
      !!data.outfit.style,
  },
  {
    step: 4,
    title: 'Personality',
    description: 'Traits, relationship, and style',
    validate: (data) =>
      data.personality.tags.length > 0 &&
      !!data.personality.relationship,
  },
  {
    step: 5,
    title: 'Voice',
    description: 'Pick a voice (optional)',
    validate: (data) => !!data.voiceProfile,
    optional: true,
    skipWarning: 'Skip voice selection? You can add a voice later.',
  },
  {
    step: 6,
    title: 'Background',
    description: 'Backstory and boundaries (optional)',
    validate: (data) => {
      const hasBackground =
        !!data.background.profession ||
        (data.background.hobbies || []).length > 0 ||
        !!data.background.backstory;
      const hasPreferences =
        (data.preferences?.likes || []).length > 0 ||
        (data.preferences?.dislikes || []).length > 0;
      const hasChatRules =
        (data.chatRules?.mandatory?.disallowed_topics || []).length > 0 ||
        data.chatRules?.mandatory?.safety_level === 'ADULT' ||
        (data.chatRules?.anchors?.tone_voice &&
          data.chatRules.anchors.tone_voice !== 'warm_friendly') ||
        (data.chatRules?.anchors?.keywords || []).length > 0 ||
        (data.chatRules?.anchors?.quirks || []).length > 0 ||
        (data.chatRules?.anchors?.catchphrases || []).length > 0 ||
        (data.chatRules?.anchors?.secrets || []).length > 0 ||
        (data.chatRules?.interaction?.role_type &&
          data.chatRules.interaction.role_type !== 'guiding') ||
        !!data.chatRules?.interaction?.guidance_notes;
      return hasBackground || hasPreferences || hasChatRules;
    },
    optional: true,
    skipWarning: 'Skip background and boundaries? You can edit later.',
  },
  {
    step: 7,
    title: 'Scene',
    description: 'Scene and opening message',
    validate: (data) => !!data.scene?.environment,
  },
  {
    step: 8,
    title: 'Confirm',
    description: 'Name and final details',
    validate: (data) =>
      !!data.identity.firstName &&
      !!data.identity.age &&
      data.identity.age >= 18 &&
      data.identity.age <= 99,
  },
];
