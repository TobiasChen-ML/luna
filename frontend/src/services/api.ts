import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { auth } from '@/config/firebase';
import { isTelegramMiniApp } from '@/utils/telegram';
import { tokenStorage } from '@/lib/tokenStorage';

const DEVICE_FINGERPRINT_KEY = 'aigirl_device_fingerprint';
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

function getDeviceFingerprint(): string {
  const fromStorage = localStorage.getItem(DEVICE_FINGERPRINT_KEY);
  if (fromStorage) return fromStorage;
  const generated =
    globalThis.crypto?.randomUUID?.() ||
    `fp_${Date.now()}_${Math.random().toString(36).slice(2, 12)}`;
  localStorage.setItem(DEVICE_FINGERPRINT_KEY, generated);
  return generated;
}

let isRefreshing = false;
let failedQueue: Array<{
  resolve: () => void;
  reject: (error: Error) => void;
}> = [];

function processQueue(error: Error | null): void {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve();
    }
  });
  failedQueue = [];
}

export const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // send HttpOnly auth cookies on every request
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  async (config) => {
    config.headers['X-Device-Fingerprint'] = getDeviceFingerprint();

    // Auth tokens live in HttpOnly cookies — the browser sends them automatically.
    // We only attach a Firebase ID token when there is no active app session yet
    // (e.g. first login, or after a full session expiry) so the backend can
    // exchange it for new cookies.
    if (!tokenStorage.hasTokens()) {
      const firebaseUser = auth.currentUser;
      if (firebaseUser) {
        const firebaseToken = await firebaseUser.getIdToken();
        config.headers.Authorization = `Bearer ${firebaseToken}`;
      }
    }

    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise<void>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => {
            // Cookies refreshed — remove any stale Authorization header and retry.
            delete originalRequest.headers.Authorization;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Step 1: try silent refresh via HttpOnly refresh_token cookie.
        await axios.post(`${BASE_URL}/auth/refresh`, null, { withCredentials: true });

        processQueue(null);
        delete originalRequest.headers.Authorization;
        return api(originalRequest);
      } catch {
        // Step 2: refresh cookie expired — try re-exchanging the Firebase token.
        const firebaseUser = auth.currentUser;
        if (firebaseUser) {
          try {
            const firebaseToken = await firebaseUser.getIdToken(/* forceRefresh */ true);
            await axios.post(
              `${BASE_URL}/auth/verify-token`,
              { token: firebaseToken },
              { withCredentials: true },
            );

            processQueue(null);
            delete originalRequest.headers.Authorization;
            return api(originalRequest);
          } catch {
            // Firebase re-auth also failed — fall through to logout.
          }
        }

        processQueue(new Error('Session expired'));
        tokenStorage.clearTokens();

        if (!isTelegramMiniApp()) {
          await auth.signOut();
          window.location.href = '/login';
        }

        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    if (error.response?.status === 403) {
      console.error('Forbidden: Insufficient permissions');
      const url = error.config?.url || '';
      if (url.includes('/admin/') && !window.location.pathname.includes('/admin/login')) {
        window.location.href = '/admin/login';
      }
    } else if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('Network Error: No response received');
    }

    return Promise.reject(error);
  },
);

/** Called after the backend sets auth cookies (no-op on the client side). */
export async function setAuthTokens(_accessToken: string, _refreshToken: string): Promise<void> {
  // Tokens are stored as HttpOnly cookies by the backend — nothing to do here.
}

/** Clears the JS-readable session indicator; actual cookie deletion is server-side. */
export function clearAuthTokens(): void {
  tokenStorage.clearTokens();
}

export function hasValidTokens(): boolean {
  return tokenStorage.hasTokens();
}
