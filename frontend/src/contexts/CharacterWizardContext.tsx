import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { CharacterWizardData, ScenePreset, VoiceProfile } from '@/types/character';
import { initialCharacterData, wizardSteps, generateRandomAppearance } from '@/types/character';

interface CharacterWizardContextType {
  // State
  currentStep: number;
  characterData: CharacterWizardData;
  isComplete: boolean;
  canProceed: boolean;

  // Navigation
  nextStep: () => void;
  previousStep: () => void;
  goToStep: (step: number) => void;
  skipStep: () => void;

  // Data Management
  updateField: <K extends keyof CharacterWizardData>(
    field: K,
    value: CharacterWizardData[K]
  ) => void;
  updateNestedField: (path: string, value: any) => void;
  resetWizard: () => void;

  // Actions
  randomizeAll: () => void;
  randomizeStep: () => void;
  saveProgress: () => void;
}

const CharacterWizardContext = createContext<CharacterWizardContextType | undefined>(
  undefined
);

const STORAGE_KEY = 'aigirl_wizard_state';

export function CharacterWizardProvider({ children }: { children: React.ReactNode }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [characterData, setCharacterData] = useState<CharacterWizardData>(initialCharacterData);

  // Load from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem(STORAGE_KEY);
    if (savedState) {
      try {
        const { step, data } = JSON.parse(savedState);
        const normalizedStep = Math.min(
          Math.max(Number(step) || 1, 1),
          wizardSteps.length
        );
        setCurrentStep(normalizedStep);
        setCharacterData(data);
      } catch (error) {
        console.error('Failed to load saved wizard state:', error);
      }
    }
  }, []);

  // Save to localStorage on change
  useEffect(() => {
    const state = {
      step: currentStep,
      data: characterData,
      timestamp: Date.now(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [currentStep, characterData]);

  const currentConfig = wizardSteps[currentStep - 1];
  const isStepValid = currentConfig?.validate(characterData) ?? false;

  // Validate current step
  const canProceed = isStepValid;

  // Check if wizard is complete
  const isComplete = currentStep === wizardSteps.length && canProceed;

  // Update a top-level field
  const updateField = useCallback(
    <K extends keyof CharacterWizardData>(
      field: K,
      value: CharacterWizardData[K]
    ) => {
      setCharacterData((prev) => ({
        ...prev,
        [field]: value,
      }));
    },
    []
  );

  // Update nested field using dot notation (e.g., "appearance.bodyType")
  const updateNestedField = useCallback((path: string, value: any) => {
    setCharacterData((prev) => {
      const keys = path.split('.');
      const newData = { ...prev } as any;
      let current: any = newData;

      for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i] as keyof typeof current;
        current[key] = { ...current[key] };
        current = current[key];
      }

      current[keys[keys.length - 1]] = value;
      return newData;
    });
  }, []);

  // Navigation
  const nextStep = useCallback(() => {
    if (currentStep < wizardSteps.length && canProceed) {
      setCurrentStep((prev) => prev + 1);
    }
  }, [currentStep, canProceed]);

  const skipStep = useCallback(() => {
    if (currentStep < wizardSteps.length) {
      setCurrentStep((prev) => prev + 1);
    }
  }, [currentStep]);

  const previousStep = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [currentStep]);

  const goToStep = useCallback((step: number) => {
    if (step >= 1 && step <= wizardSteps.length) {
      setCurrentStep(step);
    }
  }, []);

  // Reset wizard
  const resetWizard = useCallback(() => {
    setCurrentStep(1);
    setCharacterData(initialCharacterData);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  // Randomize all fields
  const randomizeAll = useCallback(() => {
    const outfitStyles = ['Casual', 'Elegant', 'Sporty', 'Business', 'Romantic', 'Edgy'];
    const personalityTraits = ['gentle', 'caring', 'playful', 'mysterious', 'confident', 'shy', 'adventurous', 'romantic'];
    const relationships = ['Friend', 'Girlfriend', 'Companion', 'Wife', 'Mentor'];
    const names = ['Emma', 'Sophia', 'Olivia', 'Ava', 'Isabella', 'Mia', 'Luna', 'Chloe'];
    const professions = ['Designer', 'Artist', 'Writer', 'Teacher', 'Nurse', 'Developer', 'Chef', 'Musician'];
    const hobbies = ['Art', 'Music', 'Reading', 'Cooking', 'Gaming', 'Travel', 'Photography', 'Dancing'];
    const relationPresets = [
      { character_role: 'girlfriend', user_role: 'boyfriend', relationship_tone: 'sweet' },
      { character_role: 'boss', user_role: 'employee', relationship_tone: 'dominant' },
      { character_role: 'neighbor', user_role: 'neighbor', relationship_tone: 'friendly' },
      { character_role: 'mentor', user_role: 'student', relationship_tone: 'supportive' },
    ];
    const voiceProfiles: VoiceProfile[] = [
      'Inspirational_girl',
      'Cute_girl',
      'Lovely_Girl',
      'Sweet_Girl_2',
      'Lively_Girl',
      'Exuberant_Girl',
      'Calm_Woman',
      'Wise_Woman',
      'Decent_Boy',
      'Magnetic_boy',
      'Friendly_Person',
      'Abbess',
    ];
    const scenePresets: ScenePreset[] = ['Office', 'Beach', 'Fantasy', 'NightCity', 'CozyHome', 'RainCafe'];

    const randomData: CharacterWizardData = {
      ...generateRandomAppearance(),
      template: {
        id: 'custom',
        name: 'Custom',
        description: 'Start from scratch',
      },
      relation: relationPresets[Math.floor(Math.random() * relationPresets.length)],
      outfit: {
        style: outfitStyles[Math.floor(Math.random() * outfitStyles.length)] as any,
      },
      personality: {
        tags: personalityTraits.slice(0, Math.floor(Math.random() * 3) + 1) as any,
        relationship: relationships[Math.floor(Math.random() * relationships.length)] as any,
      },
      personalitySummary: '',
      personalityExample: '',
      background: {
        profession: professions[Math.floor(Math.random() * professions.length)],
        hobbies: hobbies.sort(() => Math.random() - 0.5).slice(0, 2),
      },
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
        environment: scenePresets[Math.floor(Math.random() * scenePresets.length)],
        openingMessage: '',
      },
      identity: {
        firstName: names[Math.floor(Math.random() * names.length)],
        age: Math.floor(Math.random() * 15) + 20,
      },
      voiceProfile: voiceProfiles[Math.floor(Math.random() * voiceProfiles.length)],
    };
    setCharacterData(randomData);
  }, []);

  // Randomize current step only
  const randomizeStep = useCallback(() => {
    const outfitStyles = ['Casual', 'Elegant', 'Sporty', 'Business', 'Romantic', 'Edgy'];
    const personalityTraits = ['gentle', 'caring', 'playful', 'mysterious', 'confident', 'shy', 'adventurous', 'romantic'];
    const relationships = ['Friend', 'Girlfriend', 'Companion', 'Wife', 'Mentor'];
    const names = ['Emma', 'Sophia', 'Olivia', 'Ava', 'Isabella', 'Mia', 'Luna', 'Chloe'];
    const relationPresets = [
      { character_role: 'girlfriend', user_role: 'boyfriend', relationship_tone: 'sweet' },
      { character_role: 'boss', user_role: 'employee', relationship_tone: 'dominant' },
      { character_role: 'neighbor', user_role: 'neighbor', relationship_tone: 'friendly' },
      { character_role: 'mentor', user_role: 'student', relationship_tone: 'supportive' },
    ];
    const voiceProfiles: VoiceProfile[] = [
      'Inspirational_girl',
      'Cute_girl',
      'Lovely_Girl',
      'Sweet_Girl_2',
      'Lively_Girl',
      'Exuberant_Girl',
      'Calm_Woman',
      'Wise_Woman',
      'Decent_Boy',
      'Magnetic_boy',
      'Friendly_Person',
      'Abbess',
    ];
    const scenePresets: ScenePreset[] = ['Office', 'Beach', 'Fantasy', 'NightCity', 'CozyHome', 'RainCafe'];

    switch (currentStep) {
      case 1: {
        const appearance = generateRandomAppearance();
        updateField('gender', 'Female');
        updateField('style', appearance.style);
        break;
      }
      case 2: {
        const preset = relationPresets[Math.floor(Math.random() * relationPresets.length)];
        updateField('relation', preset);
        break;
      }
      case 3: {
        const appearance = generateRandomAppearance();
        updateField('appearance', appearance.appearance);
        updateField('hair', appearance.hair);
        updateField('face', appearance.face);
        updateNestedField('outfit.style', outfitStyles[Math.floor(Math.random() * outfitStyles.length)]);
        break;
      }
      case 4:
        updateNestedField('personality.tags', personalityTraits.slice(0, Math.floor(Math.random() * 3) + 1));
        updateNestedField('personality.relationship', relationships[Math.floor(Math.random() * relationships.length)]);
        break;
      case 5:
        updateNestedField('voiceProfile', voiceProfiles[Math.floor(Math.random() * voiceProfiles.length)]);
        break;
      case 6:
        updateNestedField('background.profession', 'Designer');
        updateNestedField('background.hobbies', ['Reading', 'Music']);
        break;
      case 7:
        updateNestedField('scene.environment', scenePresets[Math.floor(Math.random() * scenePresets.length)]);
        break;
      case 8:
        updateNestedField('identity.firstName', names[Math.floor(Math.random() * names.length)]);
        updateNestedField('identity.age', Math.floor(Math.random() * 15) + 20);
        break;
    }
  }, [currentStep, updateField, updateNestedField]);

  // Manual save (in case auto-save fails)
  const saveProgress = useCallback(() => {
    const state = {
      step: currentStep,
      data: characterData,
      timestamp: Date.now(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [currentStep, characterData]);

  const value = {
    currentStep,
    characterData,
    isComplete,
    canProceed,
    nextStep,
    previousStep,
    goToStep,
    skipStep,
    updateField,
    updateNestedField,
    resetWizard,
    randomizeAll,
    randomizeStep,
    saveProgress,
  };

  return (
    <CharacterWizardContext.Provider value={value}>
      {children}
    </CharacterWizardContext.Provider>
  );
}

export function useWizard() {
  const context = useContext(CharacterWizardContext);
  if (context === undefined) {
    throw new Error('useWizard must be used within a CharacterWizardProvider');
  }
  return context;
}
