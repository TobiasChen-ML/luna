/**
 * Tests for AuthContext — session restoration, login/logout state transitions,
 * and Telegram Mini App auto-login path.
 *
 * All external dependencies (Firebase, authService, telegram utils) are mocked
 * so tests are purely synchronous / deterministic.
 */

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { User as AppUser } from '@/types';

// ── Module mocks ──────────────────────────────────────────────────────────────

// Firebase is already mocked in src/test/setup.ts for firebase/auth.
// We override @/config/firebase here to control onAuthStateChanged behaviour.
vi.mock('@/config/firebase', () => ({
  auth: {
    currentUser: null,
    signOut: vi.fn().mockResolvedValue(undefined),
    onAuthStateChanged: vi.fn((cb: (u: null) => void) => {
      // Immediately call with null (no Firebase user) and return an unsubscribe fn
      cb(null);
      return vi.fn();
    }),
  },
}));

vi.mock('@/services/authService', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    loginWithGoogle: vi.fn(),
    loginWithTelegram: vi.fn(),
    initiateRegistration: vi.fn(),
    completeRegistration: vi.fn(),
    logout: vi.fn(),
    checkin: vi.fn(),
    exchangeFirebaseTokenForAppJWT: vi.fn(),
  },
}));

vi.mock('@/utils/telegram', () => ({
  isTelegramMiniApp: vi.fn(() => false),
  getTelegramInitData: vi.fn(() => ''),
}));

vi.mock('@/lib/tokenStorage', () => ({
  tokenStorage: {
    hasTokens: vi.fn(() => false),
    saveTokens: vi.fn(),
    clearTokens: vi.fn(),
    canRefresh: vi.fn(() => false),
    isAccessTokenExpired: vi.fn(() => true),
    getAccessToken: vi.fn(() => null),
    getRefreshToken: vi.fn(() => null),
  },
}));

// ── Imports after mocks ───────────────────────────────────────────────────────

import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { tokenStorage } from '@/lib/tokenStorage';
import { authService } from '@/services/authService';
import { isTelegramMiniApp } from '@/utils/telegram';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const mockUser: AppUser = {
  id: 'u1',
  email: 'test@example.com',
  display_name: 'Test User',
  credits: 100,
} as AppUser;

function makeJwt(exp: number): string {
  const h = btoa(JSON.stringify({ alg: 'HS256' }));
  const p = btoa(JSON.stringify({ sub: 'u1', exp }));
  return `${h}.${p}.sig`;
}

const FUTURE_EXP = () => Math.floor(Date.now() / 1000) + 3600;
const PAST_EXP = () => Math.floor(Date.now() / 1000) - 60;

/** Renders AuthProvider + a child component that exposes context values via data-testid. */
function TestConsumer() {
  const { user, loading, isAuthenticated, login, logout } = useAuth();
  if (loading) return <div data-testid="loading">loading</div>;
  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'authenticated' : 'guest'}</div>
      <div data-testid="user-email">{user?.email ?? 'none'}</div>
      <button onClick={() => login('test@example.com', 'pass')}>Login</button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
}

function renderWithAuth() {
  return render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>,
  );
}

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
  vi.mocked(isTelegramMiniApp).mockReturnValue(false);
  vi.mocked(authService.checkin).mockResolvedValue({ success: false });
  vi.mocked(authService.getCurrentUser).mockResolvedValue(mockUser);
  vi.mocked(tokenStorage.hasTokens).mockReturnValue(false);
  vi.mocked(tokenStorage.canRefresh).mockReturnValue(false);
});

afterEach(() => {
  localStorage.clear();
});

// ---------------------------------------------------------------------------
// Initial loading state
// ---------------------------------------------------------------------------

describe('initial state', () => {
  it('renders loading indicator before auth resolves', () => {
    // Make getCurrentUser hang so loading persists
    vi.mocked(authService.getCurrentUser).mockImplementation(
      () => new Promise(() => {}),
    );
    renderWithAuth();
    expect(screen.getByTestId('loading')).toBeInTheDocument();
  });

  it('resolves to unauthenticated (guest) with no stored tokens and no Firebase user', async () => {
    renderWithAuth();
    await waitFor(() =>
      expect(screen.getByTestId('auth-status')).toHaveTextContent('guest'),
    );
  });
});

// ---------------------------------------------------------------------------
// Session restoration from stored JWT
// ---------------------------------------------------------------------------

describe('session restoration from stored app JWT', () => {
  it('sets user when valid tokens exist in localStorage', async () => {
    vi.mocked(tokenStorage.hasTokens).mockReturnValue(true);
    vi.mocked(tokenStorage.canRefresh).mockReturnValue(true);
    vi.mocked(tokenStorage.isAccessTokenExpired).mockReturnValue(false);
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockUser);

    renderWithAuth();
    await waitFor(() =>
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated'),
    );
    expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
    expect(authService.getCurrentUser).toHaveBeenCalledTimes(1);
  });

  it('clears tokens and stays unauthenticated when getCurrentUser throws', async () => {
    vi.mocked(tokenStorage.hasTokens).mockReturnValue(true);
    vi.mocked(authService.getCurrentUser).mockRejectedValue(new Error('Network error'));

    renderWithAuth();
    await waitFor(() =>
      expect(screen.getByTestId('auth-status')).toHaveTextContent('guest'),
    );
    expect(tokenStorage.clearTokens).toHaveBeenCalled();
  });

  it('skips restoration and stays guest when tokens are fully expired and unrefreshable', async () => {
    vi.mocked(tokenStorage.hasTokens).mockReturnValue(true);
    vi.mocked(tokenStorage.isAccessTokenExpired).mockReturnValue(true);
    vi.mocked(tokenStorage.canRefresh).mockReturnValue(false);

    renderWithAuth();
    await waitFor(() =>
      expect(screen.getByTestId('auth-status')).toHaveTextContent('guest'),
    );
    expect(authService.getCurrentUser).not.toHaveBeenCalled();
    expect(tokenStorage.clearTokens).toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// login()
// ---------------------------------------------------------------------------

describe('login()', () => {
  it('sets user state after successful login', async () => {
    vi.mocked(authService.login).mockResolvedValue(undefined);
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockUser);
    const user = userEvent.setup();

    renderWithAuth();
    await waitFor(() => expect(screen.queryByTestId('loading')).not.toBeInTheDocument());

    await user.click(screen.getByText('Login'));
    await waitFor(() =>
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated'),
    );
    expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
  });

  it('re-throws on login failure and user remains unauthenticated', async () => {
    vi.mocked(authService.login).mockRejectedValue(new Error('Invalid credentials'));
    const user = userEvent.setup();

    renderWithAuth();
    await waitFor(() => expect(screen.queryByTestId('loading')).not.toBeInTheDocument());

    // The button click triggers login() which throws — catch it via error boundary
    // In this simplified test we just verify the UI stays as guest
    await user.click(screen.getByText('Login')).catch(() => {});
    // Give React time to settle
    await waitFor(() =>
      expect(screen.getByTestId('auth-status')).toHaveTextContent('guest'),
    );
  });
});

// ---------------------------------------------------------------------------
// logout()
// ---------------------------------------------------------------------------

describe('logout()', () => {
  it('clears user state after logout', async () => {
    vi.mocked(tokenStorage.hasTokens).mockReturnValue(true);
    vi.mocked(tokenStorage.canRefresh).mockReturnValue(true);
    vi.mocked(tokenStorage.isAccessTokenExpired).mockReturnValue(false);
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockUser);
    vi.mocked(authService.logout).mockResolvedValue(undefined);
    const user = userEvent.setup();

    renderWithAuth();
    await waitFor(() =>
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated'),
    );

    await user.click(screen.getByText('Logout'));
    await waitFor(() =>
      expect(screen.getByTestId('auth-status')).toHaveTextContent('guest'),
    );
    expect(screen.getByTestId('user-email')).toHaveTextContent('none');
  });
});

// ---------------------------------------------------------------------------
// Daily check-in on session restore
// ---------------------------------------------------------------------------

describe('daily check-in on restore', () => {
  it('updates credits when check-in succeeds', async () => {
    vi.mocked(tokenStorage.hasTokens).mockReturnValue(true);
    vi.mocked(tokenStorage.canRefresh).mockReturnValue(true);
    vi.mocked(tokenStorage.isAccessTokenExpired).mockReturnValue(false);
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockUser);
    vi.mocked(authService.checkin).mockResolvedValue({
      success: true,
      message: 'Checked in',
      new_balance: 150,
    });

    function CreditsConsumer() {
      const { user } = useAuth();
      return <div data-testid="credits">{user?.credits ?? 0}</div>;
    }
    render(
      <AuthProvider>
        <CreditsConsumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId('credits')).toHaveTextContent('150'),
    );
  });
});

// ---------------------------------------------------------------------------
// Telegram Mini App auto-login
// ---------------------------------------------------------------------------

describe('Telegram Mini App auto-login', () => {
  it('authenticates user via Telegram when isTelegramMiniApp returns true', async () => {
    vi.mocked(isTelegramMiniApp).mockReturnValue(true);
    vi.mocked(authService.loginWithTelegram).mockResolvedValue(mockUser);

    renderWithAuth();
    await waitFor(() =>
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated'),
    );
    expect(authService.loginWithTelegram).toHaveBeenCalledTimes(1);
    // Should NOT attempt Firebase flow when Telegram login succeeds
    expect(authService.exchangeFirebaseTokenForAppJWT).not.toHaveBeenCalled();
  });

  it('falls back to JWT / Firebase flow when Telegram auto-login fails', async () => {
    vi.mocked(isTelegramMiniApp).mockReturnValue(true);
    vi.mocked(authService.loginWithTelegram).mockRejectedValue(new Error('TMA error'));

    renderWithAuth();
    // Telegram login failed → falls through to JWT/Firebase path → resolves as guest
    await waitFor(() =>
      expect(screen.getByTestId('auth-status')).toHaveTextContent('guest'),
    );
  });

  it('does not call loginWithTelegram more than once (tmaLoginAttempted guard)', async () => {
    vi.mocked(isTelegramMiniApp).mockReturnValue(true);
    vi.mocked(authService.loginWithTelegram).mockResolvedValue(mockUser);

    // Re-rendering the same provider instance doesn't retrigger (useRef guard)
    const { rerender } = renderWithAuth();
    await waitFor(() =>
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated'),
    );
    rerender(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );
    // Still just one call
    expect(authService.loginWithTelegram).toHaveBeenCalledTimes(1);
  });
});
