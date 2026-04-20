import { test, expect } from '../fixtures/admin.fixture';

test.describe('Admin CharacterCreatePage', () => {
  test.beforeEach(async ({ page, mockApi }) => {
    const mockPayload = { exp: Math.floor(Date.now() / 1000) + 3600, sub: 'admin-001' };
    const mockToken = `header.${btoa(JSON.stringify(mockPayload))}.signature`;
    
    await page.addInitScript((token) => {
      localStorage.setItem('roxy_access_token', token);
      localStorage.setItem('roxy_refresh_token', token);
      localStorage.setItem('admin_token', 'mock-admin-jwt-token');
      localStorage.setItem('aigirl_age_verified', JSON.stringify({
        verified: true,
        timestamp: Date.now(),
        expiresAt: Date.now() + 24 * 60 * 60 * 1000
      }));
    }, mockToken);
    
    await page.goto('/zh/admin/characters/create');
  });

  test.describe('Manual Creation Mode', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('button', { name: '手动创建' }).click();
    });

    test('should display manual creation form', async ({ page }) => {
      await expect(page.getByPlaceholder('输入角色名称')).toBeVisible();
      await expect(page.getByPlaceholder('Emma')).toBeVisible();
      await expect(page.getByRole('button', { name: '创建角色' })).toBeVisible();
    });

    test('should create character with required fields', async ({ page }) => {
      await page.getByPlaceholder('输入角色名称').fill('Test Character');
      await page.getByPlaceholder('Emma').fill('Test');
      
      await page.getByRole('button', { name: '创建角色' }).click();
      
      await expect(page.getByText('角色创建成功')).toBeVisible({ timeout: 10000 });
    });

    test('should validate required name field', async ({ page }) => {
      await page.getByRole('button', { name: '创建角色' }).click();
      
      await expect(page.getByText('请输入角色名称')).toBeVisible();
    });

    test('should fill all character fields', async ({ page }) => {
      await page.getByPlaceholder('输入角色名称').fill('Full Character');
      await page.getByPlaceholder('Emma').fill('Full');
      
      const selects = page.locator('select');
      await selects.first().selectOption('anime');
      
      await page.getByPlaceholder('角色简介...').fill('A complete test character');
      await page.getByPlaceholder('角色背景故事...').fill('Test backstory');
      await page.getByPlaceholder('角色的开场白...').fill('Hello, I am a test!');
      
      await page.getByRole('button', { name: '创建角色' }).click();
      
      await expect(page.getByText('角色创建成功')).toBeVisible({ timeout: 10000 });
    });

    test('should select personality tags', async ({ page }) => {
      await page.getByPlaceholder('输入角色名称').fill('Tagged Character');
      
      await page.getByRole('button', { name: 'gentle' }).click();
      await page.getByRole('button', { name: 'caring' }).click();
      
      await page.getByRole('button', { name: '创建角色' }).click();
      
      await expect(page.getByText('角色创建成功')).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Batch Generation Mode', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('button', { name: '批量AI生成' }).click();
    });

    test('should display batch generation form', async ({ page }) => {
      await expect(page.getByText('生成数量')).toBeVisible();
      await expect(page.getByText('分类')).toBeVisible();
      await expect(page.getByText('最小年龄')).toBeVisible();
      await expect(page.getByText('最大年龄')).toBeVisible();
      await expect(page.getByRole('button', { name: '开始批量生成' })).toBeVisible();
    });

    test('should configure batch generation parameters', async ({ page }) => {
      const numberInputs = page.locator('input[type="number"]');
      await numberInputs.first().fill('5');
      
      const selects = page.locator('select');
      await selects.first().selectOption('girls');
      
      await page.getByRole('button', { name: '开始批量生成' }).click();
      
      await expect(page.getByText(/成功创建/)).toBeVisible({ timeout: 10000 });
    });

    test('should toggle checkboxes', async ({ page }) => {
      const checkboxes = page.locator('input[type="checkbox"]');
      await checkboxes.first().click();
      
      await expect(checkboxes.first()).toBeChecked();
    });
  });

  test.describe('Template Generation Mode', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('button', { name: '模板变体' }).click();
    });

    test('should display template generation form', async ({ page }) => {
      await expect(page.getByText('选择模板')).toBeVisible();
      await expect(page.getByText('变体数量')).toBeVisible();
      await expect(page.getByRole('button', { name: '从模板创建' })).toBeVisible();
    });

    test('should select template and generate variants', async ({ page }) => {
      const selects = page.locator('select');
      await selects.first().selectOption({ index: 0 });
      
      await page.getByRole('button', { name: '从模板创建' }).click();
      
      await expect(page.getByText(/成功创建/)).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Navigation', () => {
    test('should navigate back to admin', async ({ page }) => {
      await page.locator('button').filter({ has: page.locator('svg') }).first().click();
      
      await expect(page).toHaveURL(/\/admin$/);
    });

    test('should switch between creation modes', async ({ page }) => {
      await page.getByRole('button', { name: '批量AI生成' }).click();
      await expect(page.getByText('生成数量')).toBeVisible();
      
      await page.getByRole('button', { name: '模板变体' }).click();
      await expect(page.getByText('选择模板')).toBeVisible();
      
      await page.getByRole('button', { name: '手动创建' }).click();
      await expect(page.getByPlaceholder('输入角色名称')).toBeVisible();
    });
  });
});
