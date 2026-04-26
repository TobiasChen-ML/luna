import { describe, expect, it } from 'vitest';

import { getInsufficientCreditsInfo } from '@/utils/apiError';

describe('getInsufficientCreditsInfo', () => {
  it('parses backend insufficient credit responses that use error_code', () => {
    const result = getInsufficientCreditsInfo({
      response: {
        status: 402,
        data: {
          detail: {
            error_code: 'insufficient_credits',
            required: 0.2,
            available: 0,
            message: 'Not enough credits for voice generation',
          },
        },
      },
    });

    expect(result).toEqual({
      required: 0.2,
      available: 0,
      message: 'Not enough credits for voice generation',
    });
  });

  it('keeps supporting legacy responses that use error', () => {
    const result = getInsufficientCreditsInfo({
      response: {
        status: 402,
        data: {
          error: 'insufficient_credits',
          required: 10,
          current: 3,
        },
      },
    });

    expect(result).toEqual({
      required: 10,
      available: 3,
      message: undefined,
    });
  });
});
