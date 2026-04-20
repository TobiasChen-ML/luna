import { createContext, useContext, useEffect, useRef, useState } from 'react';
import type { User as FirebaseUser } from 'firebase/auth';
import { auth } from '@/config/firebase';
import { authService } from '@/services/authService';
import type { GoogleLoginResult } from '@/services/authService';
import type { User as AppUser } from '@/types';
import { isTelegramMiniApp, getTelegramInitData } from '@/utils/telegram';
import { tokenStorage } from '@/lib/tokenStorage';

interface AuthContextType {
  user: AppUser | null;
  firebaseUser: FirebaseUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<GoogleLoginResult>;
  loginWithTelegram: () => Promise<void>;
  register: (
    email: string,
    password: string,
    ageConsentGiven: boolean,
    phoneNumber?: string,
    captchaToken?: string | null
  ) => Promise<void>;
  completeRegistration: (dateOfBirth: { month: number; day: number; year: number }, ageConsent: boolean) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [user, setUser] = useState<AppUser | null>(null);
  const [loading, setLoading] = useState(true);
  const tmaLoginAttempted = useRef(false);
  const sessionRestored = useRef(false);

  const refreshUser = async () => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Error refreshing user data:', error);
    }
  };

  const performDailyCheckin = async () => {
    try {
      const checkinResult = await authService.checkin();
      if (checkinResult && checkinResult.success) {
        console.log('Daily check-in successful:', checkinResult.message);
        setUser(prev => prev ? { ...prev, credits: checkinResult.new_balance } : prev);
      }
    } catch (e) {
      console.error('Check-in failed (silent)', e);
    }
  };

  const restoreSessionFromAppJWT = async (): Promise<boolean> => {
    if (!tokenStorage.hasTokens()) return false;
    if (tokenStorage.isAccessTokenExpired() && !tokenStorage.canRefresh()) {
      tokenStorage.clearTokens();
      return false;
    }

    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
      await performDailyCheckin();
      return true;
    } catch (error) {
      console.error('Failed to restore session from App JWT:', error);
      tokenStorage.clearTokens();
      return false;
    }
  };

  const handleTelegramAutoLogin = async (): Promise<boolean> => {
    if (tmaLoginAttempted.current) return false;
    tmaLoginAttempted.current = true;

    try {
      const initData = getTelegramInitData();
      const userData = await authService.loginWithTelegram(initData);
      setUser(userData);
      await performDailyCheckin();
      return true;
    } catch (err) {
      console.error('Telegram auto-login failed:', err);
      return false;
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      if (sessionRestored.current) return;
      sessionRestored.current = true;

      if (isTelegramMiniApp()) {
        const success = await handleTelegramAutoLogin();
        if (success) {
          setLoading(false);
          return;
        }
      }

      const sessionRestoredFromJWT = await restoreSessionFromAppJWT();
      if (sessionRestoredFromJWT) {
        setLoading(false);
        return;
      }

      auth.onAuthStateChanged(async (fbUser) => {
        setFirebaseUser(fbUser);

        if (fbUser) {
          try {
            await authService.exchangeFirebaseTokenForAppJWT();
            const userData = await authService.getCurrentUser();
            setUser(userData);
            await performDailyCheckin();
          } catch (error) {
            console.error('Error during Firebase auth flow:', error);
            setUser(null);
          }
        } else {
          setUser(null);
        }

        setLoading(false);
      });
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      await authService.login(email, password);
      const userData = await authService.getCurrentUser();
      setUser(userData);
      await performDailyCheckin();
    } catch (error: unknown) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async () => {
    setLoading(true);
    try {
      return await authService.loginWithGoogle();
    } catch (error) {
      setLoading(false);
      throw error;
    }
  };

  const loginWithTelegram = async () => {
    setLoading(true);
    try {
      const initData = getTelegramInitData();
      const userData = await authService.loginWithTelegram(initData);
      setUser(userData);
      await performDailyCheckin();
    } finally {
      setLoading(false);
    }
  };

  const register = async (
    email: string,
    password: string,
    ageConsentGiven: boolean,
    phoneNumber?: string,
    captchaToken?: string | null
  ) => {
    setLoading(true);
    try {
      await authService.initiateRegistration(
        email,
        password,
        ageConsentGiven,
        phoneNumber,
        captchaToken
      );
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const completeRegistration = async (dateOfBirth: { month: number; day: number; year: number }, ageConsent: boolean) => {
    setLoading(true);
    try {
      const updatedUser = await authService.completeRegistration(dateOfBirth, ageConsent);
      setUser(updatedUser);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await authService.logout();
      setUser(null);
      setFirebaseUser(null);
    } finally {
      setLoading(false);
    }
  };

  const value = {
    user,
    firebaseUser,
    loading,
    isAuthenticated: !!user,
    login,
    loginWithGoogle,
    loginWithTelegram,
    register,
    completeRegistration,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
