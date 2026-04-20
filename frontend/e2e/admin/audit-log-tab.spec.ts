import { test, expect } from '../fixtures/admin.fixture';

test.describe('Admin AuditLogTab', () => {
  test.beforeEach(async ({ page, mockApi }) => {
    const mockPayload = { exp: Math.floor(Date.now() / 1000) + 3600, sub: 'admin-001' };
    const mockToken = `header.${btoa(JSON.stringify(mockPayload))}.signature`;
    
    await page.goto('/');
    await page.evaluate((token) => {
      localStorage.setItem('roxy_access_token', token);
      localStorage.setItem('roxy_refresh_token', token);
      localStorage.setItem('admin_token', 'mock-admin-jwt-token');
      localStorage.setItem('aigirl_age_verified', JSON.stringify({
        verified: true,
        timestamp: Date.now(),
        expiresAt: Date.now() + 24 * 60 * 60 * 1000
      }));
    }, mockToken);
  });

  test('should display audit log tab in sidebar', async ({ page }) => {
    await page.goto('/zh/admin');
    await page.waitForLoadState('networkidle');
    
    await expect(page.getByRole('button', { name: '操作日志' })).toBeVisible();
  });

  test('should load audit logs on tab click', async ({ page }) => {
    await page.route('**/admin/audit/logs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          logs: [
            {
              id: 1,
              admin_id: 'admin-001',
              admin_email: 'admin@test.com',
              action: 'credit_adjust',
              resource_type: 'user',
              resource_id: 'user-001',
              old_value: '{"balance": 100}',
              new_value: '{"balance": 150}',
              ip_address: '127.0.0.1',
              created_at: '2026-01-01T12:00:00Z',
            }
          ],
          total: 1,
          limit: 20,
          offset: 0,
        }),
      });
    });

    await page.goto('/zh/admin');
    await page.getByRole('button', { name: '操作日志' }).click();
    
    await expect(page.locator('table')).toBeVisible();
    await expect(page.getByText('admin@test.com')).toBeVisible();
  });

  test('should show filter panel when filter button clicked', async ({ page }) => {
    await page.route('**/admin/audit/**', async (route) => {
      if (route.request().url().includes('/actions')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(['credit_adjust', 'character_create']),
        });
      } else if (route.request().url().includes('/resource-types')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(['user', 'character']),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto('/zh/admin');
    await page.getByRole('button', { name: '操作日志' }).click();
    
    const filterButton = page.getByRole('button', { name: '筛选' });
    await filterButton.click();
    
    await expect(page.getByLabel('操作类型')).toBeVisible();
    await expect(page.getByLabel('资源类型')).toBeVisible();
  });

  test('should show log detail modal when clicking view button', async ({ page }) => {
    await page.route('**/admin/audit/logs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          logs: [
            {
              id: 1,
              admin_id: 'admin-001',
              admin_email: 'admin@test.com',
              action: 'credit_adjust',
              resource_type: 'user',
              resource_id: 'user-001',
              old_value: '{"balance": 100}',
              new_value: '{"balance": 150, "adjustment": 50}',
              ip_address: '127.0.0.1',
              user_agent: 'Mozilla/5.0',
              created_at: '2026-01-01T12:00:00Z',
            }
          ],
          total: 1,
        }),
      });
    });

    await page.goto('/zh/admin');
    await page.getByRole('button', { name: '操作日志' }).click();
    
    const viewButton = page.getByTitle('查看详情');
    await viewButton.click();
    
    await expect(page.getByText('操作详情')).toBeVisible();
  });
});
