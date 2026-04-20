/**
 * Tests for services/api.ts — request interceptor, 401 auto-retry with token
 * refresh, concurrent-refresh queue, and Telegram Mini App special handling.
 *
 * Uses MSW (msw/node) to intercept HTTP at the Node level so Axios requests
 * are intercepted without a real server.
 */

import {
  afterAll,
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

// ── Module mocks (must be at top level, before imports that need them) ───────

const mockAuthState = {
  currentUser: null as { getIdToken: () => Promise<string> } | null,
};

vi.mock('@/config/firebase', () => ({
  get auth() {
    return {
      get currentUser() {
        return mockAuthState.currentUser;
      },
      signOut: vi.fn().mockResolvedValue(undefined),
    };
  },
}));

vi.mock('@/utils/telegram', () => ({
  isTelegramMiniApp: vi.fn(() => false),
}));

vi.mock('@/lib/tokenStorage', () => ({
  tokenStorage: {
    hasTokens: vi.fn(() => false),
    getAccessToken: vi.fn(() => null),
    getRefreshToken: vi.fn(() => null),
    saveTokens: vi.fn(),
    clearTokens: vi.fn(),
    canRefresh: vi.fn(() => false),
    isAccessTokenExpired: vi.fn(() => true),
  },
}));

// ── Now import the subjects under test ───────────────────────────────────────

import { api } from '@/services/api';
import { tokenStorage } from '@/lib/tokenStorage';
import { auth } from '@/config/firebase';
import { isTelegramMiniApp } from '@/utils/telegram';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeJwt(exp: number): string {
  const h = btoa(JSON.stringify({ alg: 'HS256' }));
  const p = btoa(JSON.stringify({ sub: 'u1', exp }));
  return `${h}.${p}.sig`;
}

const FUTURE_EXP = () => Math.floor(Date.now() / 1000) + 3600;
const PAST_EXP = () => Math.floor(Date.now() / 1000) - 60;

const NEW_ACCESS = () => makeJwt(FUTURE_EXP() + 100);
const NEW_REFRESH = () => makeJwt(FUTURE_EXP() + 86400);

// ---------------------------------------------------------------------------
// MSW server setup
// ---------------------------------------------------------------------------

let refreshCallCount = 0;
let latestNewAccess = '';
let latestNewRefresh = '';

const server = setupServer();

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterAll(() => server.close());

beforeEach(() => {
  localStorage.clear();
  refreshCallCount = 0;
  latestNewAccess = NEW_ACCESS();
  latestNewRefresh = NEW_REFRESH();
  vi.clearAllMocks();
  vi.mocked(isTelegramMiniApp).mockReturnValue(false);
  vi.mocked(tokenStorage.hasTokens).mockReturnValue(false);
  vi.mocked(tokenStorage.canRefresh).mockReturnValue(false);
  vi.mocked(tokenStorage.isAccessTokenExpired).mockReturnValue(true);
});

afterEach(() => server.resetHandlers());

// ---------------------------------------------------------------------------
// Request interceptor — token attachment
// ---------------------------------------------------------------------------

describe('request interceptor', () => {
  it('attaches Firebase ID token as Bearer header when no session cookies and Firebase user exists', async () => {
    let capturedAuth = '';
    server.use(
      http.get('/api/ping', ({ request }) => {
        capturedAuth = request.headers.get('authorization') ?? '';
        return HttpResponse.json({ ok: true });
      }),
    );

    const firebaseToken = makeJwt(FUTURE_EXP());
    mockAuthState.currentUser = {
      getIdToken: vi.fn().mockResolvedValue(firebaseToken),
    };
    vi.mocked(tokenStorage.hasTokens).mockReturnValue(false);

    await api.get('/ping');
    expect(capturedAuth).toBe(`Bearer ${firebaseToken}`);
    
    mockAuthState.currentUser = null;
  });

  it('does not set Authorization when session cookies exist', async () => {
    let capturedAuth: string | null = 'NOT_SET';
    server.use(
      http.get('/api/ping', ({ request }) => {
        capturedAuth = request.headers.get('authorization');
        return HttpResponse.json({ ok: true });
      }),
    );

    vi.mocked(tokenStorage.hasTokens).mockReturnValue(true);

    await api.get('/ping');
    expect(capturedAuth).toBeNull();
  });

  it('does not set Authorization when no tokens are stored and no Firebase user', async () => {
    let capturedAuth: string | null = 'NOT_SET';
    server.use(
      http.get('/api/ping', ({ request }) => {
        capturedAuth = request.headers.get('authorization');
        return HttpResponse.json({ ok: true });
      }),
    );

    vi.mocked(tokenStorage.hasTokens).mockReturnValue(false);

    await api.get('/ping');
    expect(capturedAuth).toBeNull();
  });

  it('attaches X-Device-Fingerprint on every request', async () => {
    let fingerprint = '';
    server.use(
      http.get('/api/ping', ({ request }) => {
        fingerprint = request.headers.get('x-device-fingerprint') ?? '';
        return HttpResponse.json({ ok: true });
      }),
    );

    await api.get('/ping');
    expect(fingerprint).toBeTruthy();
    expect(fingerprint.length).toBeGreaterThan(0);
  });

  it('reuses the same fingerprint across requests', async () => {
    const fingerprints: string[] = [];
    server.use(
      http.get('/api/ping', ({ request }) => {
        fingerprints.push(request.headers.get('x-device-fingerprint') ?? '');
        return HttpResponse.json({ ok: true });
      }),
    );

    await api.get('/ping');
    await api.get('/ping');
    expect(fingerprints[0]).toBe(fingerprints[1]);
  });
});

// ---------------------------------------------------------------------------
// 401 auto-retry with token refresh
// ---------------------------------------------------------------------------

describe('401 auto-retry', () => {
  it('calls /auth/refresh and retries original request on 401', async () => {
    let requestCount = 0;
    server.use(
      http.get('/api/protected', () => {
        requestCount++;
        if (requestCount === 1) return HttpResponse.json({ error: 'unauthorized' }, { status: 401 });
        return HttpResponse.json({ data: 'secret' });
      }),
      http.post('/api/auth/refresh', () => {
        refreshCallCount++;
        return HttpResponse.json({ success: true });
      }),
    );

    vi.mocked(tokenStorage.hasTokens).mockReturnValue(true);

    const response = await api.get('/protected');
    expect(response.status).toBe(200);
    expect(refreshCallCount).toBe(1);
    expect(requestCount).toBe(2);
  });

  it('does not retry when _retry flag is already set (prevents infinite loops)', async () => {
    let requestCount = 0;
    server.use(
      http.get('/api/always-401', () => {
        requestCount++;
        return HttpResponse.json({ error: 'unauthorized' }, { status: 401 });
      }),
      http.post('/api/auth/refresh', () => {
        refreshCallCount++;
        return HttpResponse.json({ success: true });
      }),
    );

vi.mocked(tokenStorage.hasTokens).mockReturnValue(true);

    await expect(api.get('/always-401')).rejects.toMatchObject({
      response: { status: 401 },
    });
    expect(requestCount).toBe(2);
    expect(refreshCallCount).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// Concurrent 401 — queue mechanism
// ---------------------------------------------------------------------------

describe('concurrent 401 requests queue behind a single refresh', () => {
  it('issues exactly one refresh call when multiple requests get 401 simultaneously', async () => {
    let protectedCallCount = 0;
    server.use(
      http.get('/api/protected', () => {
        protectedCallCount++;
        if (protectedCallCount <= 3) return HttpResponse.json({ error: 'unauthorized' }, { status: 401 });
        return HttpResponse.json({ data: 'ok' });
      }),
      http.post('/api/auth/refresh', async () => {
        refreshCallCount++;
        await new Promise((r) => setTimeout(r, 20));
        protectedCallCount = 100;
        return HttpResponse.json({ success: true });
      }),
    );

    vi.mocked(tokenStorage.hasTokens).mockReturnValue(true);

    const [r1, r2, r3] = await Promise.all([
      api.get('/protected'),
      api.get('/protected'),
      api.get('/protected'),
    ]);

    expect([r1.status, r2.status, r3.status]).toEqual([200, 200, 200]);
    expect(refreshCallCount).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// Refresh failure — non-Telegram context
// ---------------------------------------------------------------------------

describe('refresh failure in non-Telegram context', () => {
  it('handles refresh failure appropriately', async () => {
    vi.mocked(isTelegramMiniApp).mockReturnValue(false);
    vi.stubGlobal('location', { href: '' });

    server.use(
      http.get('/api/protected', () =>
        HttpResponse.json({ error: 'unauthorized' }, { status: 401 }),
      ),
      http.post('/api/auth/refresh', () =>
        HttpResponse.json({ error: 'token expired' }, { status: 401 }),
      ),
    );

    vi.mocked(tokenStorage.hasTokens).mockReturnValue(true);

    await expect(api.get('/protected')).rejects.toBeDefined();
  });
});

// ---------------------------------------------------------------------------
// Telegram Mini App — 401 must NOT redirect or sign out
// ---------------------------------------------------------------------------

describe('Telegram Mini App — 401 handling', () => {
  it('rejects without redirecting when no refresh token exists', async () => {
    vi.mocked(isTelegramMiniApp).mockReturnValue(true);
    vi.stubGlobal('location', { href: '' });

    server.use(
      http.get('/api/protected', () =>
        HttpResponse.json({ error: 'unauthorized' }, { status: 401 }),
      ),
      http.post('/api/auth/refresh', () =>
        HttpResponse.json({ error: 'no token' }, { status: 401 }),
      ),
    );

    vi.mocked(tokenStorage.hasTokens).mockReturnValue(false);

    await expect(api.get('/protected')).rejects.toBeDefined();

    expect(window.location.href).toBe('');
    expect(auth.signOut).not.toHaveBeenCalled();
  });

  it('rejects without signing out when refresh fails in TMA context', async () => {
    vi.mocked(isTelegramMiniApp).mockReturnValue(true);
    vi.stubGlobal('location', { href: '' });

    server.use(
      http.get('/api/protected', () =>
        HttpResponse.json({ error: 'unauthorized' }, { status: 401 }),
      ),
      http.post('/api/auth/refresh', () =>
        HttpResponse.json({ error: 'invalid' }, { status: 401 }),
      ),
    );

    vi.mocked(tokenStorage.hasTokens).mockReturnValue(true);

    await expect(api.get('/protected')).rejects.toBeDefined();

    expect(auth.signOut).not.toHaveBeenCalled();
    expect(window.location.href).toBe('');
  });

  it('handles refresh failure in TMA context', async () => {
    vi.mocked(isTelegramMiniApp).mockReturnValue(true);

    server.use(
      http.get('/api/protected', () =>
        HttpResponse.json({ error: 'unauthorized' }, { status: 401 }),
      ),
      http.post('/api/auth/refresh', () =>
        HttpResponse.json({ error: 'invalid' }, { status: 401 }),
      ),
    );

    vi.mocked(tokenStorage.hasTokens).mockReturnValue(true);

    await expect(api.get('/protected')).rejects.toBeDefined();
  });
});
