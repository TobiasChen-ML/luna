import { describe, it, expect, vi, beforeEach } from 'vitest';

import { claimShareReward } from '@/utils/share';
import { rewardsService } from '@/services/rewardsService';

vi.mock('@/services/rewardsService', () => ({
  rewardsService: {
    claimShareReward: vi.fn(),
  },
}));

describe('claimShareReward', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns claim result when api succeeds', async () => {
    vi.mocked(rewardsService.claimShareReward).mockResolvedValue({
      success: true,
      granted: true,
      reason: 'granted',
      reward_amount: 10,
      new_balance: 130,
    });

    const result = await claimShareReward('gallery:item_1', 'gallery_media', {
      media_type: 'image',
    });

    expect(rewardsService.claimShareReward).toHaveBeenCalledWith({
      share_key: 'gallery:item_1',
      channel: 'gallery_media',
      metadata: { media_type: 'image' },
    });
    expect(result?.granted).toBe(true);
    expect(result?.reward_amount).toBe(10);
  });

  it('returns null when api fails', async () => {
    vi.mocked(rewardsService.claimShareReward).mockRejectedValue(new Error('network'));

    const result = await claimShareReward('discover:char_1', 'discover_profile');
    expect(result).toBeNull();
  });
});
