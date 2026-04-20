import { api } from './api';

interface StartVerificationResponse {
  session_id: string;
  verification_url: string;
  status: string;
}

interface VerificationStatusResponse {
  session_id: string;
  status: string;
  verified: boolean;
  failed: boolean;
}

export const ageVerificationService = {
  async start(): Promise<StartVerificationResponse> {
    const callbackUrl = `${window.location.origin}/chat`;
    const res = await api.post<StartVerificationResponse>('/auth/age-verification/start', {
      callback_url: callbackUrl,
    });
    return res.data;
  },

  async getStatus(sessionId: string): Promise<VerificationStatusResponse> {
    const res = await api.get<VerificationStatusResponse>('/auth/age-verification/status', {
      params: { session_id: sessionId },
    });
    return res.data;
  },
};

