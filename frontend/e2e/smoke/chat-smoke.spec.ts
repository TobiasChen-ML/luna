import { test, expect, setupGuestUser } from '../fixtures/chat.fixture';

test.describe('Smoke: Guest Chat', () => {
  test('guest chat page renders core elements', async ({ page, mockChatApi }) => {
    await setupGuestUser(page);
    await page.goto('/ai-girlfriend/emma-test?mode=guest');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/Guest Mode/i)).toBeVisible();
    await expect(page.getByText('Emma')).toBeVisible();
    await expect(page.getByPlaceholder(/Message Emma/i)).toBeVisible();
  });
});
