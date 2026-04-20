import { test, expect } from '@playwright/test';

test.describe('Admin CharactersTab', () => {
  test.beforeEach(async ({ page }) => {
    const response = await page.request.post('http://localhost:8999/api/auth/test-login', {
      data: { is_admin: true, email: 'admin@test.com', user_id: 'admin-test-001' }
    });
    
    const data = await response.json();
    const accessToken = data.access_token;
    
    await page.addInitScript((token) => {
      localStorage.setItem('roxy_access_token', token);
      localStorage.setItem('roxy_refresh_token', token);
      localStorage.setItem('aigirl_age_verified', JSON.stringify({
        verified: true,
        timestamp: Date.now(),
        expiresAt: Date.now() + 24 * 60 * 60 * 1000
      }));
    }, accessToken);
    
    await page.goto('/zh/admin');
    await page.waitForLoadState('networkidle');
    
    const cookieAccept = page.getByRole('button', { name: 'Accept All' });
    if (await cookieAccept.count() > 0) {
      await cookieAccept.first().click();
      await page.waitForTimeout(500);
    }
  });

  test('should load admin page', async ({ page }) => {
    await expect(page).toHaveURL(/admin/);
  });

  test('should load and display character list', async ({ page }) => {
    await page.getByRole('button', { name: '角色管理' }).click();
    await expect(page.locator('table')).toBeVisible({ timeout: 15000 });
  });

  test('should navigate to character create page', async ({ page }) => {
    await page.getByRole('button', { name: '角色管理' }).click();
    await page.getByRole('button', { name: '创建角色' }).click();
    await expect(page).toHaveURL(/\/admin\/characters\/create/);
  });
});
