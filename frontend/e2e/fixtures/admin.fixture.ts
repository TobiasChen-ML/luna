import { test as base, Page } from '@playwright/test';
import {
  mockCharacterListResponse,
  mockSingleCharacter,
  mockCreateCharacterResponse,
  mockTemplates,
  mockAiFillResponse,
  mockRegenerateImagesResponse,
  mockBatchGenerateResponse,
  mockTemplateGenerateResponse,
} from './mocks/characters';

type AdminFixtures = {
  mockApi: void;
};

export const test = base.extend<AdminFixtures>({
  mockApi: async ({ page }, use) => {
    await page.route('**/api/geo/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ country: 'US', allowed: true }),
      });
    });

    await page.route('**/auth/me**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          id: 'admin-001', 
          email: 'admin@test.com', 
          firebase_uid: 'firebase-admin-001',
          display_name: 'Admin User',
          is_adult: true,
          is_admin: true,
          subscription_tier: 'premium',
          credits: 1000,
          purchased_credits: 500,
          monthly_credits_remaining: 500,
          mature_preference: 'adult',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-04-01T00:00:00Z',
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

    await page.route('**/api/characters/**', async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.includes('/discover')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ characters: [], categories: ['girls', 'anime', 'guys'] }),
        });
        return;
      }
      if (url.pathname.includes('/categories')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(['girls', 'anime', 'guys']),
        });
        return;
      }
      await route.continue();
    });

    await page.route('**/admin/api/characters**', async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      const method = request.method();
      const path = url.pathname;

      if (method === 'GET' && path.endsWith('/characters')) {
        const search = url.searchParams.get('search');
        let filteredList = mockCharacterListResponse;
        if (search) {
          filteredList = {
            ...mockCharacterListResponse,
            items: mockCharacterListResponse.items.filter(
              (c) => c.name.toLowerCase().includes(search.toLowerCase())
            ),
            total: mockCharacterListResponse.items.filter(
              (c) => c.name.toLowerCase().includes(search.toLowerCase())
            ).length,
          };
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(filteredList),
        });
        return;
      }

      if (method === 'GET' && /\/admin\/api\/characters\/[^/]+$/.test(path)) {
        const id = path.split('/').pop();
        const char = mockCharacterListResponse.items.find((c) => c.id === id) || mockSingleCharacter;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(char),
        });
        return;
      }

      if (method === 'DELETE' && /\/admin\/api\/characters\/[^/]+$/.test(path)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
        return;
      }

      if (method === 'POST' && path.endsWith('/batch-delete')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
        return;
      }

      if (method === 'POST' && path.endsWith('/characters')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockCreateCharacterResponse),
        });
        return;
      }

      if (method === 'POST' && path.endsWith('/batch-generate')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockBatchGenerateResponse),
        });
        return;
      }

      if (method === 'POST' && path.endsWith('/from-template')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockTemplateGenerateResponse),
        });
        return;
      }

      if (method === 'PUT' && /\/admin\/api\/characters\/[^/]+$/.test(path)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
        return;
      }

      if (method === 'POST' && /\/admin\/api\/characters\/[^/]+\/regenerate-images/.test(path)) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockRegenerateImagesResponse),
        });
        return;
      }

      await route.continue();
    });

    await page.route('**/admin/characters/**', async (route) => {
      const request = route.request();
      const method = request.method();
      const path = new URL(request.url()).pathname;

      if (method === 'GET' && /\/admin\/characters\/[^/]+$/.test(path)) {
        const match = path.match(/\/admin\/characters\/([^/]+)/);
        const id = match ? match[1] : null;
        const char = mockCharacterListResponse.items.find((c) => c.id === id) || mockSingleCharacter;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(char),
        });
        return;
      }

      if (method === 'POST' && path.includes('/ai-fill')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockAiFillResponse),
        });
        return;
      }

      await route.continue();
    });

    await page.route('**/admin/api/character-templates**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTemplates),
      });
    });

    await use(void 0);
  },
});

export { expect } from '@playwright/test';
