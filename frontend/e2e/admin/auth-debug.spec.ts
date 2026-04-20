import { test, expect } from '@playwright/test';

test.describe('Admin Auth Debug', () => {
  test('debug full auth flow', async ({ page }) => {
    const response = await page.request.post('http://localhost:8999/api/auth/test-login', {
      data: { is_admin: true, email: 'admin@test.com', user_id: 'admin-test-001' }
    });
    
    const data = await response.json();
    const accessToken = data.access_token;
    console.log('Got token:', accessToken.slice(0, 50));
    
    await page.addInitScript((token) => {
      localStorage.setItem('roxy_access_token', token);
      localStorage.setItem('roxy_refresh_token', token);
      localStorage.setItem('aigirl_age_verified', JSON.stringify({
        verified: true,
        timestamp: Date.now(),
        expiresAt: Date.now() + 24 * 60 * 60 * 1000
      }));
      console.log('[Init Script] Token set in localStorage');
    }, accessToken);
    
    page.on('console', msg => {
      if (msg.text().includes('[Init Script]') || msg.text().includes('Failed') || msg.text().includes('restore')) {
        console.log('BROWSER:', msg.text());
      }
    });
    
    page.on('request', request => {
      if (request.url().includes('/auth/me')) {
        console.log('REQUEST /auth/me, Auth header:', request.headers()['authorization']?.slice(0, 30));
      }
    });
    
    page.on('response', async response => {
      if (response.url().includes('/auth/me')) {
        console.log('RESPONSE /auth/me:', response.status());
        try {
          const body = await response.json();
          console.log('RESPONSE body:', JSON.stringify(body).slice(0, 100));
        } catch (e) {
          console.log('RESPONSE not JSON');
        }
      }
    });
    
    await page.goto('/zh/admin', { waitUntil: 'networkidle' });
    
    console.log('Final URL:', page.url());
    
    const ls = await page.evaluate(() => ({
      access: localStorage.getItem('roxy_access_token')?.slice(0, 30),
      refresh: localStorage.getItem('roxy_refresh_token')?.slice(0, 30),
    }));
    console.log('localStorage:', ls);
    
    await page.screenshot({ path: 'test-results/debug-auth-final.png' });
  });
});
