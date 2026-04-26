import {
  createUserWithEmailAndPassword,
  signOut,
  sendPasswordResetEmail,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithRedirect,
  updatePassword,
  EmailAuthProvider,
  reauthenticateWithCredential,
} from 'firebase/auth';
import type { User } from 'firebase/auth';
import type { AxiosError } from 'axios';
import { auth } from '@/config/firebase';
import { api, setAuthTokens, clearAuthTokens } from './api';
import { tokenStorage } from '@/lib/tokenStorage';
import type { User as AppUser } from '@/types';

type CompleteRegistrationResponse = { message: string; user: AppUser };
export type GoogleLoginResult = 'success' | 'redirect';

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user?: AppUser;
  is_admin?: boolean;
}

async function exchangeFirebaseToken(): Promise<TokenResponse | null> {
  const firebaseUser = auth.currentUser;
  if (!firebaseUser) return null;
  
  const idToken = await firebaseUser.getIdToken();
  const response = await api.post<TokenResponse>('/auth/verify-token', { token: idToken });
  
  const { access_token, refresh_token } = response.data;
  setAuthTokens(access_token, refresh_token);
  
  return response.data;
}

export const authService = {
  async register(email: string, password: string, isAdult: boolean): Promise<User> {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);

    try {
      const uid = userCredential.user.uid;
      await api.post('/auth/register', { email, firebase_uid: uid, is_adult: isAdult });
    } catch (error) {
      console.error('Error creating user in backend:', error);
    }

    return userCredential.user;
  },

  async initiateRegistration(
    email: string,
    password: string,
    ageConsentGiven: boolean,
    phoneNumber?: string,
    captchaToken?: string | null
  ): Promise<{ email: string }> {
    const response = await api.post('/auth/register/initiate', {
      email,
      password,
      phone_number: phoneNumber || null,
      age_consent_given: ageConsentGiven,
      captcha_token: captchaToken,
    });
    return response.data;
  },

  async verifyEmail(token: string): Promise<{ customToken: string; user: AppUser }> {
    const response = await api.post('/auth/verify-email', { token });
    return response.data;
  },

  async resendVerification(email: string): Promise<void> {
    await api.post('/auth/resend-verification', { email });
  },

  async login(email: string, password: string): Promise<User> {
    const response = await api.post<TokenResponse>('/auth/login', { email, password });
    const { access_token, refresh_token } = response.data;
    await setAuthTokens(access_token, refresh_token);

    return {
      uid: response.data.user?.id ?? '',
      email,
      displayName: response.data.user?.display_name ?? null,
    } as User;
  },

  async loginWithGoogle(): Promise<GoogleLoginResult> {
    const provider = new GoogleAuthProvider();
    let userCredential: Awaited<ReturnType<typeof signInWithPopup>> | null = null;
    try {
      userCredential = await signInWithPopup(auth, provider);
    } catch (error: unknown) {
      const code = (error as { code?: string }).code;
      if (code === 'auth/popup-blocked') {
        await signInWithRedirect(auth, provider);
        return 'redirect';
      }
      throw error;
    }

    try {
      await api.post('/auth/register', {
        email: userCredential.user.email,
        firebase_uid: userCredential.user.uid,
        is_adult: true,
      });
    } catch (error: unknown) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      const detail = axiosError.response?.data?.detail;
      const isExistingUser =
        axiosError.response?.status === 400 &&
        typeof detail === 'string' &&
        detail.includes('already');
      if (!isExistingUser) {
        console.error('Error syncing Google user to backend:', error);
      }
    }

    try {
      await exchangeFirebaseToken();
    } catch (error: unknown) {
      console.error('Failed to exchange Firebase token for App JWT:', error);
    }

    return 'success';
  },

  async logout(): Promise<void> {
    try {
      // Ask the backend to expire the HttpOnly auth cookies.
      await api.post('/auth/logout');
    } catch {
      // Best-effort — still proceed with Firebase sign-out.
    }
    clearAuthTokens();
    await signOut(auth);
  },

  async getCurrentUser(): Promise<AppUser> {
    const response = await api.get<AppUser>('/auth/me');
    return response.data;
  },

  async completeRegistration(
    dateOfBirth: { month: number; day: number; year: number },
    ageConsent: boolean
  ): Promise<AppUser> {
    const response = await api.post<CompleteRegistrationResponse>('/auth/complete-registration', {
      date_of_birth: dateOfBirth,
      age_consent_given: ageConsent,
    });
    return response.data.user;
  },

  async loginWithTelegram(initData: string): Promise<AppUser> {
    const response = await api.post<{
      access_token: string;
      refresh_token: string;
      user: AppUser;
      is_new_user: boolean;
    }>('/auth/telegram', { init_data: initData });
    
    const { access_token, refresh_token, user } = response.data;
    setAuthTokens(access_token, refresh_token);
    
    return user;
  },

  async checkin(): Promise<{ success: boolean; credits_granted: number; new_balance: number; message: string } | null> {
    try {
      const response = await api.post('/auth/checkin');
      return response.data;
    } catch (error: unknown) {
      const axiosError = error as AxiosError;
      if (axiosError.response?.status === 429) {
        return null;
      }
      throw error;
    }
  },

  async getIdToken(): Promise<string | null> {
    const user = auth.currentUser;
    if (!user) return null;
    return await user.getIdToken();
  },

  async resetPassword(email: string): Promise<void> {
    await sendPasswordResetEmail(auth, email);
  },

  async updateProfile(fields: { display_name?: string; gender?: string }): Promise<AppUser> {
    const response = await api.put<{ success: boolean; user: AppUser }>('/auth/me/profile', fields);
    return response.data.user;
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    const firebaseUser = auth.currentUser;
    if (!firebaseUser || !firebaseUser.email) {
      throw new Error('No authenticated user');
    }
    const credential = EmailAuthProvider.credential(firebaseUser.email, currentPassword);
    await reauthenticateWithCredential(firebaseUser, credential);
    await updatePassword(firebaseUser, newPassword);
  },

  async refreshToken(): Promise<TokenResponse | null> {
    // No body needed — the backend reads the refresh token from the HttpOnly cookie.
    const response = await api.post<TokenResponse>('/auth/refresh');
    return response.data;
  },

  hasValidTokens(): boolean {
    return tokenStorage.hasTokens();
  },

  async exchangeFirebaseTokenForAppJWT(): Promise<TokenResponse | null> {
    return exchangeFirebaseToken();
  },
};
