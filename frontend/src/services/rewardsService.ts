import { api } from './api';

export interface ShareRewardClaimResponse {
  success: boolean;
  granted: boolean;
  reason: 'granted' | 'duplicate' | 'daily_limit' | string;
  reward_amount: number;
  new_balance: number;
  daily_limit?: number;
}

export const rewardsService = {
  async claimShareReward(params: {
    share_key: string;
    channel?: string;
    metadata?: Record<string, unknown>;
  }): Promise<ShareRewardClaimResponse> {
    const response = await api.post<ShareRewardClaimResponse>('/rewards/share/claim', params);
    return response.data;
  },
};
