import { api } from '@/services/api';

export type MaturePreference = 'teen' | 'adult';

export const userPreferenceService = {
  async updateMaturePreference(maturePreference: MaturePreference): Promise<void> {
    await api.put('/auth/me/mature-preference', {
      mature_preference: maturePreference,
    });
  },
};

