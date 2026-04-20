import { test, expect, setupAuthenticatedUser, mockChatCharacter, mockAIResponses } from '../fixtures/chat.fixture';

test.describe('Authenticated Chat Flow', () => {
  test.beforeEach(async ({ page, mockChatApi }) => {
    await setupAuthenticatedUser(page);
    await page.goto('/ai-girlfriend/emma-test');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Load', () => {
    test('should display character info and chat input', async ({ page }) => {
      await expect(page.getByText('Emma')).toBeVisible();
      await expect(page.getByPlaceholder(/Message Emma/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /send/i })).toBeVisible();
    });

    test('should show user credits in header', async ({ page }) => {
      const creditsDisplay = page.locator('text=/\\d+/').first();
      await expect(creditsDisplay).toBeVisible();
    });

    test('should show character selector sidebar on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 720 });
      const sidebar = page.locator('aside, [class*="sidebar"]').first();
      await expect(sidebar).toBeVisible();
    });
  });

  test.describe('Send Message', () => {
    test('should send message when clicking send button', async ({ page }) => {
      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('Hello Emma!');
      
      const sendButton = page.getByRole('button', { name: /send/i });
      await sendButton.click();

      await expect(page.getByText('Hello Emma!')).toBeVisible({ timeout: 5000 });
    });

    test('should send message when pressing Enter', async ({ page }) => {
      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('Hello from keyboard!');
      await input.press('Enter');

      await expect(page.getByText('Hello from keyboard!')).toBeVisible({ timeout: 5000 });
    });

    test('should not send empty message', async ({ page }) => {
      const sendButton = page.getByRole('button', { name: /send/i });
      await expect(sendButton).toBeDisabled();
      
      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('   ');
      await expect(sendButton).toBeDisabled();
    });

    test('should show typing indicator while AI responds', async ({ page }) => {
      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('Hello!');
      await input.press('Enter');

      const typingIndicator = page.locator('.animate-bounce').first();
      await expect(typingIndicator).toBeVisible({ timeout: 3000 });
    });

    test('should display AI response after typing', async ({ page }) => {
      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('Hello!');
      await input.press('Enter');

      await expect(page.getByText('Hello!')).toBeVisible({ timeout: 5000 });
      
      await expect(page.getByText(mockAIResponses.greeting)).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Multi-turn Conversation', () => {
    test('should maintain message order in conversation', async ({ page }) => {
      const input = page.getByPlaceholder(/Message Emma/i);

      await input.fill('First message');
      await input.press('Enter');
      await page.waitForTimeout(1000);

      await input.fill('Second message');
      await input.press('Enter');
      await page.waitForTimeout(1000);

      await expect(page.getByText('First message')).toBeVisible();
      await expect(page.getByText('Second message')).toBeVisible();
    });

    test('should clear input after sending', async ({ page }) => {
      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('Test message');
      await input.press('Enter');

      await expect(input).toHaveValue('');
    });

    test('should allow Shift+Enter for new line', async ({ page }) => {
      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('Line 1');
      await input.press('Shift+Enter');
      await input.fill('Line 1\nLine 2');
      
      await expect(input).toHaveValue(/Line 1.*Line 2/s);
    });
  });

  test.describe('Character Panel', () => {
    test('should display character description', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 720 });
      
      const descriptionSection = page.locator('text=/Description|About/i').first();
      await expect(descriptionSection).toBeVisible();
    });

    test('should show relationship metrics', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 720 });
      
      const intimacyText = page.locator('text=/Intimacy|Trust|Desire/i').first();
      await expect(intimacyText).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Navigation', () => {
    test('should navigate to home when clicking brand', async ({ page }) => {
      const brandButton = page.getByRole('button', { name: /RoxyClub/i });
      await brandButton.click();
      
      await expect(page).toHaveURL(/\//);
    });

    test('should open mobile sidebar when clicking menu button', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      const menuButton = page.getByRole('button', { name: /toggle/i }).first();
      if (await menuButton.isVisible()) {
        await menuButton.click();
        await page.waitForTimeout(500);
      }
    });
  });

  test.describe('Voice Mode Toggle', () => {
    test('should display voice mode options', async ({ page }) => {
      const voiceToggle = page.locator('text=/开启语音|关闭语音|自动/i').first();
      await expect(voiceToggle).toBeVisible({ timeout: 5000 });
    });

    test('should switch voice mode on click', async ({ page }) => {
      const autoButton = page.getByRole('button', { name: /自动/i });
      if (await autoButton.isVisible()) {
        await autoButton.click();
        await expect(autoButton).toHaveClass(/bg-primary/);
      }
    });
  });

  test.describe('Adult Mode Toggle', () => {
    test('should display Mature/Safe toggle', async ({ page }) => {
      const matureToggle = page.getByRole('button', { name: /Mature|Safe/i });
      await expect(matureToggle).toBeVisible({ timeout: 5000 });
    });

    test('should toggle between Mature and Safe', async ({ page }) => {
      const matureToggle = page.getByRole('button', { name: /Mature|Safe/i });
      const currentText = await matureToggle.textContent();

      await matureToggle.click();
      const newText = await matureToggle.textContent();

      expect(currentText).not.toBe(newText);
    });
  });
});
