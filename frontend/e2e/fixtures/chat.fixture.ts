import { test as base, Page } from '@playwright/test';
import {
  mockChatCharacter,
  mockChatCharacterAnime,
  mockUser,
  mockChatSession,
  mockAIResponses,
  createSSEResponse,
  createSSEStreamChunk,
  mockCharacterListForChat,
  mockChatHistory,
  mockGuestCredits,
} from './mocks/chat';

type ChatFixtures = {
  mockChatApi: void;
};

export const test = base.extend<ChatFixtures>({
  mockChatApi: async ({ page }, use) => {
    let requestCount = 0;
    let userCredits = mockUser.credits;
    let guestCredits = mockGuestCredits.initial;

    await page.route('**/api/geo/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ country: 'US', allowed: true }),
      });
    });

    await page.route('**/api/auth/me**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...mockUser,
          credits: userCredits,
        }),
      });
    });

    await page.route('**/api/auth/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      });
    });

    await page.route('**/api/characters/by-slug/**', async (route) => {
      const url = new URL(route.request().url());
      const slug = url.pathname.split('/').pop();
      
      const character = slug === 'sakura-anime' 
        ? mockChatCharacterAnime 
        : mockChatCharacter;
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: character.id }),
      });
    });

    await page.route('**/api/characters/official/**', async (route) => {
      const url = new URL(route.request().url());
      const id = url.pathname.split('/').pop();
      
      const character = id === mockChatCharacterAnime.id 
        ? mockChatCharacterAnime 
        : mockChatCharacter;

      const { slug: _slug, ...characterWithoutSlug } = character as typeof character & { slug?: string };
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(characterWithoutSlug),
      });
    });

    await page.route('**/api/characters/*', async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      const pathname = url.pathname;
      const method = request.method();

      if (method === 'GET') {
        const id = pathname.split('/').pop();
        const character = id === mockChatCharacterAnime.id 
          ? mockChatCharacterAnime 
          : mockChatCharacter;
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(character),
        });
        return;
      }

      await route.continue();
    });

    await page.route('**/api/chat/session*', async (route) => {
      const request = route.request();
      const method = request.method();

      if (method === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            session_id: mockChatSession.session_id,
            character_id: mockChatCharacter.id,
          }),
        });
        return;
      }

      if (method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            session: mockChatSession,
            messages: [],
          }),
        });
        return;
      }

      await route.continue();
    });

    await page.route('**/api/chat/history*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ messages: [] }),
      });
    });

    await page.route('**/api/chat/guest/credits', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          credits: guestCredits,
          is_exhausted: guestCredits <= 0,
        }),
      });
    });

    await page.route('**/api/chat/guest/send', async (route) => {
      const request = route.request();
      const requestBody = request.postDataJSON() as { message?: string } | null;
      const userMessage = requestBody?.message?.trim() || 'Hello';

      if (guestCredits <= 0) {
        await route.fulfill({
          status: 402,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: {
              error: 'Insufficient credits',
              required: mockGuestCredits.per_message_cost,
              available: 0,
            },
          }),
        });
        return;
      }

      guestCredits = Math.max(0, guestCredits - mockGuestCredits.per_message_cost);

      let responseContent = mockAIResponses.greeting;
      if (
        userMessage.toLowerCase().includes('about yourself') ||
        userMessage.toLowerCase().includes('who are you')
      ) {
        responseContent = mockAIResponses.about_me;
      } else if (requestCount > 2) {
        responseContent = mockAIResponses.follow_up;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          content: responseContent,
          credits_remaining: guestCredits,
          is_exhausted: guestCredits <= 0,
        }),
      });
    });

    await page.route('**/api/chat/stream', async (route) => {
      requestCount++;
      const request = route.request();
      let requestBody: { message?: string; character_id?: string } = {};
      
      try {
        requestBody = request.postDataJSON() || {};
      } catch {
        requestBody = {};
      }

      const userMessage = requestBody.message || 'Hello';
      
      let responseContent = mockAIResponses.greeting;
      if (userMessage.toLowerCase().includes('about yourself') || userMessage.toLowerCase().includes('who are you')) {
        responseContent = mockAIResponses.about_me;
      } else if (requestCount > 2) {
        responseContent = mockAIResponses.follow_up;
      }

      const chunks = responseContent.split(' ').map(word => word + ' ');
      const sseBody = createSSEResponse(chunks.slice(0, -1)) + createSSEStreamChunk(chunks[chunks.length - 1].trim(), true);

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        headers: {
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
        body: sseBody,
      });
    });

    await page.route('**/api/chat/guest/stream', async (route) => {
      if (guestCredits <= 0) {
        await route.fulfill({
          status: 402,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Insufficient credits',
            required: 1,
            available: 0,
          }),
        });
        return;
      }

      guestCredits--;
      
      const chunks = mockAIResponses.greeting.split(' ').map(word => word + ' ');
      const sseBody = createSSEResponse(chunks.slice(0, -1)) + createSSEStreamChunk(chunks[chunks.length - 1].trim(), true);

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        headers: {
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
        body: sseBody,
      });
    });

    await page.route('**/api/characters/*/lock-relationship', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          locked_at: new Date().toISOString(),
        }),
      });
    });

    await page.route('**/api/chat/complete-text', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          completed_text: 'This is a completed text from AI.',
        }),
      });
    });

    await page.route('**/api/images/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          task_id: 'mock-task-001',
          status: 'pending',
        }),
      });
    });

    await page.route('**/api/billing/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      });
    });

    await use(void 0);
  },
});

export function createAgeVerifiedStorage(): string {
  return JSON.stringify({
    verified: true,
    timestamp: Date.now(),
    expiresAt: Date.now() + 24 * 60 * 60 * 1000,
  });
}

export async function setupAuthenticatedUser(page: Page, options: { credits?: number } = {}) {
  await page.addInitScript((args) => {
    document.cookie = 'session_active=1; path=/';
    localStorage.setItem('aigirl_age_verified', args.ageVerified);
    if (args.credits !== undefined) {
      localStorage.setItem('test_user_credits', String(args.credits));
    }
  }, { 
    ageVerified: createAgeVerifiedStorage(),
    credits: options.credits,
  });
}

export async function setupGuestUser(page: Page, options: { credits?: number } = {}) {
  const credits = options.credits ?? mockGuestCredits.initial;
  await page.addInitScript((args) => {
    localStorage.setItem('aigirl_age_verified', args.ageVerified);
    localStorage.setItem('guest_credits', String(args.credits));
  }, { 
    ageVerified: createAgeVerifiedStorage(),
    credits,
  });
}

export { expect } from '@playwright/test';
export { mockChatCharacter, mockChatCharacterAnime, mockUser, mockAIResponses, mockGuestCredits };
