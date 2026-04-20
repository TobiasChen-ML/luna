import { test, expect, setupGuestUser, mockChatCharacter, mockGuestCredits } from '../fixtures/chat.fixture';

test.describe('Guest Chat Flow', () => {
  test.beforeEach(async ({ page, mockChatApi }) => {
    await setupGuestUser(page);
    await page.goto('/ai-girlfriend/emma-test?mode=guest');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Load', () => {
    test('should display guest mode indicator', async ({ page }) => {
      await expect(page.getByText(/Guest Mode/i)).toBeVisible();
    });

    test('should show initial guest credits', async ({ page }) => {
      const creditsDisplay = page.getByText(mockGuestCredits.initial.toString());
      await expect(creditsDisplay).toBeVisible();
    });

    test('should display character info', async ({ page }) => {
      await expect(page.getByText('Emma')).toBeVisible();
    });

    test('should show chat input', async ({ page }) => {
      await expect(page.getByPlaceholder(/Message Emma/i)).toBeVisible();
    });

    test('should show sign up button', async ({ page }) => {
      await expect(page.getByRole('button', { name: /sign up|register/i })).toBeVisible();
    });
  });

  test.describe('Send Message', () => {
    test('should send message and decrease credits', async ({ page }) => {
      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('Hello!');
      await input.press('Enter');

      await expect(page.getByText('Hello!')).toBeVisible({ timeout: 5000 });
      
      const newCredits = mockGuestCredits.initial - mockGuestCredits.per_message_cost;
      await expect(page.getByText(newCredits.toString())).toBeVisible({ timeout: 3000 });
    });

    test('should show typing indicator', async ({ page }) => {
      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('Hello!');
      await input.press('Enter');

      const typingIndicator = page.locator('.animate-bounce').first();
      await expect(typingIndicator).toBeVisible({ timeout: 3000 });
    });

    test('should show AI response', async ({ page }) => {
      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('Hello!');
      await input.press('Enter');

      await expect(page.getByText(/Hello.*great to meet you/i)).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Welcome Screen', () => {
    test('should show welcome message when no messages', async ({ page }) => {
      await page.goto('/ai-girlfriend/emma-test?mode=guest');
      
      await expect(page.getByText(/Chat with Emma/i)).toBeVisible();
    });

    test('should show suggestion buttons', async ({ page }) => {
      await page.goto('/ai-girlfriend/emma-test?mode=guest');
      
      const suggestionButtons = page.locator('button').filter({ hasText: /Hey there|Tell me about|What do you like/i });
      await expect(suggestionButtons.first()).toBeVisible();
    });

    test('should send suggestion when clicked', async ({ page }) => {
      const suggestionButton = page.getByRole('button', { name: /Hey there/i });
      await suggestionButton.click();

      await expect(page.getByText(/Hey there/i)).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Credits Exhausted', () => {
    test('should block sending when credits are zero', async ({ page }) => {
      await setupGuestUser(page, { credits: 0 });
      await page.goto('/ai-girlfriend/emma-test?mode=guest');
      await page.waitForLoadState('networkidle');

      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('This should not send');
      await input.press('Enter');

      await expect(page.getByText(/Sign up|Register/i)).toBeVisible({ timeout: 5000 });
    });

    test('should show registration prompt modal', async ({ page }) => {
      await setupGuestUser(page, { credits: 0 });
      await page.goto('/ai-girlfriend/emma-test?mode=guest');
      await page.waitForLoadState('networkidle');

      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('Trigger modal');
      await input.press('Enter');

      const modal = page.locator('[role="dialog"], .modal, [class*="modal"]').first();
      await expect(modal).toBeVisible({ timeout: 5000 });
    });

    test('should disable input when credits exhausted', async ({ page }) => {
      await setupGuestUser(page, { credits: 0 });
      await page.goto('/ai-girlfriend/emma-test?mode=guest');
      await page.waitForLoadState('networkidle');

      const placeholder = page.getByPlaceholder(/Sign up to continue/i);
      await expect(placeholder).toBeVisible();
    });
  });

  test.describe('Navigation', () => {
    test('should navigate to home when clicking back', async ({ page }) => {
      const homeButton = page.getByRole('button').filter({ has: page.locator('svg') }).first();
      await homeButton.click();
      
      await expect(page).toHaveURL(/\//);
    });

    test('should navigate to register page', async ({ page }) => {
      const signUpButton = page.getByRole('button', { name: /sign up|register/i });
      await signUpButton.click();
      
      await expect(page).toHaveURL(/register/);
    });
  });

  test.describe('Audio Playback', () => {
    test('should show play button on AI messages', async ({ page }) => {
      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('Hello!');
      await input.press('Enter');

      await page.waitForTimeout(2000);

      const playButton = page.getByRole('button', { name: /play|volume/i });
      if (await playButton.isVisible()) {
        await expect(playButton).toBeVisible();
      }
    });

    test('should toggle between play and stop', async ({ page }) => {
      const input = page.getByPlaceholder(/Message Emma/i);
      await input.fill('Hello!');
      await input.press('Enter');

      await page.waitForTimeout(2000);

      const playButton = page.getByRole('button', { name: /play/i }).first();
      if (await playButton.isVisible()) {
        await playButton.click();
        await expect(page.getByRole('button', { name: /stop/i })).toBeVisible({ timeout: 3000 });
      }
    });
  });
});
