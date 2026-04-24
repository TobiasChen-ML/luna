import { test, expect } from '@playwright/test';

test.describe('Smoke: Admin Login', () => {
  test('admin login page renders required fields', async ({ page }) => {
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

    await page.goto('/admin/login');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });
});
