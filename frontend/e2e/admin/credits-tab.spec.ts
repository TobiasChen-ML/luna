import { test, expect } from '../fixtures/admin.fixture';

test.describe('Admin CreditsTab Batch Adjustment', () => {
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

  test('should display batch adjustment mode toggle', async ({ page }) => {
    await page.goto('/zh/admin');
    await page.getByRole('button', { name: 'Credit管理' }).click();
    
    await expect(page.getByRole('button', { name: '用户调整' })).toBeVisible();
    await page.getByRole('button', { name: '用户调整' }).click();
    
    await expect(page.getByRole('button', { name: '单用户调整' })).toBeVisible();
    await expect(page.getByRole('button', { name: '批量调整' })).toBeVisible();
  });

  test('should switch to batch mode on click', async ({ page }) => {
    await page.goto('/zh/admin');
    await page.getByRole('button', { name: 'Credit管理' }).click();
    await page.getByRole('button', { name: '用户调整' }).click();
    
    const batchButton = page.getByRole('button', { name: '批量调整' });
    await batchButton.click();
    
    await expect(page.getByPlaceholder(/每行一个用户ID/)).toBeVisible();
    await expect(page.getByLabel('调整数量')).toBeVisible();
    await expect(page.getByLabel('原因')).toBeVisible();
  });

  test('should show user count when entering IDs', async ({ page }) => {
    await page.goto('/zh/admin');
    await page.getByRole('button', { name: 'Credit管理' }).click();
    await page.getByRole('button', { name: '用户调整' }).click();
    await page.getByRole('button', { name: '批量调整' }).click();
    
    const textarea = page.getByPlaceholder(/每行一个用户ID/);
    await textarea.fill('user-001\nuser-002\nuser-003');
    
    await expect(page.getByText('3 个用户')).toBeVisible();
  });

  test('should submit batch adjustment and show results', async ({ page }) => {
    await page.route('**/admin/credits/batch-adjust', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Batch adjustment completed: 2 success, 1 failures',
          success_count: 2,
          failure_count: 1,
          results: [
            { user_id: 'user-001', success: true, new_balance: 150 },
            { user_id: 'user-002', success: true, new_balance: 150 },
            { user_id: 'user-003', success: false, error: 'User not found' },
          ],
        }),
      });
    });

    await page.goto('/zh/admin');
    await page.getByRole('button', { name: 'Credit管理' }).click();
    await page.getByRole('button', { name: '用户调整' }).click();
    await page.getByRole('button', { name: '批量调整' }).click();
    
    const textarea = page.getByPlaceholder(/每行一个用户ID/);
    await textarea.fill('user-001\nuser-002\nuser-003');
    
    await page.getByLabel('调整数量').fill('50');
    await page.getByLabel('原因').fill('Batch bonus');
    
    await page.getByRole('button', { name: '批量调整' }).click();
    
    await expect(page.getByText('处理结果')).toBeVisible();
    await expect(page.getByText('user-001')).toBeVisible();
  });

  test('should show error for empty user IDs', async ({ page }) => {
    await page.goto('/zh/admin');
    await page.getByRole('button', { name: 'Credit管理' }).click();
    await page.getByRole('button', { name: '用户调整' }).click();
    await page.getByRole('button', { name: '批量调整' }).click();
    
    await page.getByLabel('调整数量').fill('50');
    await page.getByLabel('原因').fill('Test');
    
    await page.getByRole('button', { name: '批量调整' }).click();
    
    await expect(page.getByText(/请输入至少一个用户ID/)).toBeVisible();
  });

  test('should handle single user adjustment', async ({ page }) => {
    await page.route('**/admin/credits/adjust', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'Credits adjusted' }),
      });
    });

    await page.goto('/zh/admin');
    await page.getByRole('button', { name: 'Credit管理' }).click();
    await page.getByRole('button', { name: '用户调整' }).click();
    
    await page.getByPlaceholder('User ID (UUID)').fill('user-001');
    await page.getByPlaceholder('+100 or -50').fill('50');
    await page.getByPlaceholder('Adjustment reason').fill('Bonus');
    
    await page.getByRole('button', { name: '调整' }).first().click();
    
    await expect(page.getByText('Credits adjusted')).toBeVisible();
  });
});
