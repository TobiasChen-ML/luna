import type { Page } from '@playwright/test';
import { test, expect, setupGuestUser, mockAIResponses } from '../fixtures/chat.fixture';

const GUEST_CHAT_URL = '/chat?character=test-chat-char-001&mode=guest';

async function dismissCookieBannerIfPresent(page: Page) {
  const acceptAllButton = page.getByRole('button', { name: /Accept All/i });
  if (await acceptAllButton.isVisible()) {
    await acceptAllButton.click();
  }
}

test.describe('Guest Chat Full Flow', () => {
  test.beforeEach(async ({ page, mockChatApi }) => {
    await setupGuestUser(page);
    await page.goto(GUEST_CHAT_URL);
    await page.waitForLoadState('networkidle');
    await dismissCookieBannerIfPresent(page);
  });

  test('should send message, receive role reply, and deduct credits', async ({ page }) => {
    const creditValue = page.locator('div:has(svg.lucide-coins) span').first();
    await expect(creditValue).toHaveText('5');

    const input = page.getByPlaceholder(/Message Emma/i);
    await input.fill('Hello Emma!');
    await input.press('Enter');

    await expect(page.getByText('Hello Emma!')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(mockAIResponses.greeting)).toBeVisible({ timeout: 5000 });
    await expect(creditValue).toHaveText('4');
  });

  test('should block further sends when credits are exhausted', async ({ page }) => {
    const input = page.getByPlaceholder(/Message Emma/i);
    for (let i = 0; i < 5; i += 1) {
      await input.fill(`message-${i}`);
      await input.press('Enter');
      await expect(page.getByText(`message-${i}`)).toBeVisible({ timeout: 5000 });
    }

    await expect(page.getByText('Free Credits Exhausted')).toBeVisible({ timeout: 5000 });
    await expect(page.getByPlaceholder(/Sign up to continue chatting/i)).toBeVisible();
  });
});
