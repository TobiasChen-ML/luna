import { test, expect } from '@playwright/test';

test.describe('Admin Debug', () => {
  test('debug auth flow', async ({ page }) => {
    const response = await page.request.post('http://localhost:8999/api/auth/test-login', {
      data: { is_admin: true, email: 'admin@test.com', user_id: 'admin-test-001' }
    });
    
    const data = await response.json();
    console.log('Token received:', data.access_token?.slice(0, 50));
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    await page.evaluate((token) => {
      localStorage.setItem('roxy_access_token', token);
      localStorage.setItem('roxy_refresh_token', token);
      localStorage.setItem('aigirl_age_verified', JSON.stringify({
        verified: true,
        timestamp: Date.now(),
        expiresAt: Date.now() + 24 * 60 * 60 * 1000
      }));
      console.log('Token set in localStorage:', localStorage.getItem('roxy_access_token')?.slice(0, 50));
    }, data.access_token);
    
    const cookieAccept = page.getByRole('button', { name: 'Accept All' });
    if (await cookieAccept.count() > 0) {
      await cookieAccept.first().click();
      await page.waitForTimeout(500);
    }
    
    await page.goto('/zh/admin');
    await page.waitForTimeout(3000);
    
    const url = page.url();
    console.log('Current URL:', url);
    
    const localStorageData = await page.evaluate(() => ({
      access_token: localStorage.getItem('roxy_access_token')?.slice(0, 50),
      refresh_token: localStorage.getItem('roxy_refresh_token')?.slice(0, 50),
      age_verified: localStorage.getItem('aigirl_age_verified'),
    }));
    console.log('localStorage after navigation:', localStorageData);
    
    const pageContent = await page.content();
    const hasAdmin = pageContent.includes('角色管理') || pageContent.includes('仪表盘');
    console.log('Has admin content:', hasAdmin);
    
    await page.screenshot({ path: 'test-results/debug-admin-page.png' });
    
    await expect(page).toHaveURL(/admin/);
  });
});
