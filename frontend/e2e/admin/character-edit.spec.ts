import { test, expect } from '../fixtures/admin.fixture';
import { mockSingleCharacter } from '../fixtures/mocks/characters';

test.describe('Admin CharacterEditPage', () => {
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
    
    await page.goto(`/zh/admin/characters/${mockSingleCharacter.id}/edit`);
  });

  test.describe('Page Load', () => {
    test('should load character data into form', async ({ page }) => {
      await expect(page.getByText('编辑角色')).toBeVisible({ timeout: 10000 });
      await expect(page.getByLabel('角色名称')).toBeVisible();
    });

    test('should display all form sections', async ({ page }) => {
      await expect(page.getByText('基本信息')).toBeVisible();
      await expect(page.getByText('角色描述')).toBeVisible();
      await expect(page.getByText('SEO设置')).toBeVisible();
      await expect(page.getByText('状态设置')).toBeVisible();
    });

    test('should display action buttons', async ({ page }) => {
      await expect(page.getByRole('button', { name: '保存' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'AI填充' })).toBeVisible();
      await expect(page.getByRole('button', { name: '重新生成图片' })).toBeVisible();
    });
  });

  test.describe('Edit Basic Info', () => {
    test('should edit character name', async ({ page }) => {
      const nameInput = page.locator('input').filter({ hasText: mockSingleCharacter.name }).first();
      await page.getByLabel('角色名称').clear();
      await page.getByLabel('角色名称').fill('Updated Name');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });

    test('should edit display name', async ({ page }) => {
      await page.getByLabel('名字（显示用）').clear();
      await page.getByLabel('名字（显示用）').fill('New Display Name');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });

    test('should edit age', async ({ page }) => {
      const ageInput = page.getByLabel('年龄');
      await ageInput.clear();
      await ageInput.fill('30');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });

    test('should edit category', async ({ page }) => {
      const categorySelect = page.locator('select').first();
      await categorySelect.selectOption('anime');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });

    test('should edit slug', async ({ page }) => {
      const slugInput = page.getByLabel('Slug (URL)');
      await slugInput.clear();
      await slugInput.fill('new-character-slug');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Edit Description', () => {
    test('should edit description', async ({ page }) => {
      const descriptionTextarea = page.getByLabel('简介');
      await descriptionTextarea.clear();
      await descriptionTextarea.fill('Updated character description');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });

    test('should edit backstory', async ({ page }) => {
      const backstoryTextarea = page.getByLabel('背景故事');
      await backstoryTextarea.clear();
      await backstoryTextarea.fill('Updated backstory content');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });

    test('should edit greeting', async ({ page }) => {
      const greetingTextarea = page.getByLabel('开场白');
      await greetingTextarea.clear();
      await greetingTextarea.fill('Hello! Updated greeting here.');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });

    test('should edit system prompt', async ({ page }) => {
      const systemPromptTextarea = page.getByLabel('系统提示词');
      await systemPromptTextarea.clear();
      await systemPromptTextarea.fill('Updated system prompt for AI behavior');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });

    test('should toggle personality tags', async ({ page }) => {
      await page.getByRole('button', { name: 'gentle' }).click();
      await page.getByRole('button', { name: 'creative' }).click();
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Edit SEO Settings', () => {
    test('should edit SEO title', async ({ page }) => {
      const seoTitleInput = page.getByPlaceholder('SEO标题');
      await seoTitleInput.clear();
      await seoTitleInput.fill('Updated SEO Title for Character');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });

    test('should edit SEO description', async ({ page }) => {
      const seoDescTextarea = page.getByPlaceholder('SEO描述');
      await seoDescTextarea.clear();
      await seoDescTextarea.fill('Updated SEO description for better search visibility');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Edit Status', () => {
    test('should change lifecycle status', async ({ page }) => {
      const statusSelects = page.locator('select');
      await statusSelects.nth(1).selectOption('draft');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });

    test('should toggle public visibility', async ({ page }) => {
      const publicCheckbox = page.locator('input[type="checkbox"]').first();
      await publicCheckbox.click();
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Edit Voice Settings', () => {
    test('should edit ElevenLabs Voice ID', async ({ page }) => {
      const voiceIdInput = page.getByPlaceholder(/e.g., 21m00Tcm4TlvDq8ikWAM/);
      await voiceIdInput.clear();
      await voiceIdInput.fill('new-voice-id-12345');
      
      await page.getByRole('button', { name: '保存' }).click();
      
      await expect(page.getByText('保存成功')).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('AI Fill', () => {
    test('should trigger AI fill successfully', async ({ page }) => {
      await page.getByRole('button', { name: 'AI填充' }).click();
      
      await expect(page.getByText('AI填充成功')).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Regenerate Images', () => {
    test('should trigger image regeneration', async ({ page }) => {
      await page.getByRole('button', { name: '重新生成图片' }).click();
      
      await expect(page.getByText('图片重新生成成功')).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Navigation', () => {
    test('should navigate back to admin', async ({ page }) => {
      await page.locator('button').filter({ has: page.locator('svg') }).first().click();
      
      await expect(page).toHaveURL(/\/admin$/);
    });
  });

  test.describe('Statistics Display', () => {
    test('should display character statistics', async ({ page }) => {
      await expect(page.getByText('人气分数')).toBeVisible();
      await expect(page.getByText('对话次数')).toBeVisible();
      await expect(page.getByText('浏览次数')).toBeVisible();
      await expect(page.getByText('创建时间')).toBeVisible();
    });
  });
});
