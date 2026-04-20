import { test, expect } from '../fixtures/admin.fixture';

test.describe('Admin Basic Tests', () => {
  test('should navigate to admin page', async ({ page, mockApi }) => {
    const mockPayload = { exp: Math.floor(Date.now() / 1000) + 3600, sub: 'admin-001' };
    const mockToken = `header.${Buffer.from(JSON.stringify(mockPayload)).toString('base64')}.signature`;
    
    await page.addInitScript((token) => {
      localStorage.setItem('roxy_access_token', token);
      localStorage.setItem('roxy_refresh_token', token);
      localStorage.setItem('aigirl_age_verified', JSON.stringify({
        verified: true,
        timestamp: Date.now(),
        expiresAt: Date.now() + 24 * 60 * 60 * 1000
      }));
    }, mockToken);
    
    await page.goto('/zh/admin');
    
    await page.waitForTimeout(2000);
    
    const url = page.url();
    console.log('Current URL:', url);
    
    if (url.includes('/admin')) {
      const buttons = await page.locator('button').allTextContents();
      console.log('Buttons found:', buttons);
    }
    
    await expect(page).toHaveURL(/admin/);
  });
});
