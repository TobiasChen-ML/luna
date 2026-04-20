import { api } from '@/services/api';

export type ConsentTier = 'sfw' | 'suggestive' | 'mature';

export interface ConsentResponse {
  success: boolean;
  consent_given: boolean;
  tier: ConsentTier;
  timestamp?: string | null;
  cooldown_until?: string | null;
  message: string;
}

export interface RelationshipSummary {
  character_id: string;
  stage: string;
  trust: number;
  intimacy: number;
  attraction: number;
  total_messages: number;
  total_sessions: number;
  visual_permissions: Record<string, unknown>;
}

export const relationshipService = {
  async setConsent(
    characterId: string,
    consent: boolean,
    tier: ConsentTier = 'mature'
  ): Promise<ConsentResponse> {
    const response = await api.post<ConsentResponse>(
      `/api/relationship/${characterId}/consent`,
      { consent, tier }
    );
    return response.data;
  },

  async getSummary(characterId: string): Promise<RelationshipSummary> {
    const response = await api.get<RelationshipSummary>(`/api/relationship/${characterId}`);
    return response.data;
  },
};

