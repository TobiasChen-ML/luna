import { test, expect } from '@playwright/test';

test.describe('Smoke: Billing Cancel', () => {
  test('billing cancel page renders expected content', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem(
        'aigirl_age_verified',
        JSON.stringify({
          verified: true,
          timestamp: Date.now(),
          expiresAt: Date.now() + 24 * 60 * 60 * 1000,
        }),
      );
    });

    await page.route('**/api/geo/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ country: 'US', allowed: true }),
      });
    });

    await page.goto('/billing/cancel');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: /Checkout Canceled/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Back to Billing/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /View Plans/i })).toBeVisible();
  });
});
