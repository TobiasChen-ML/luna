import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet, useSearchParams, useLocation, useParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { GeoProvider, useGeoContext } from '@/contexts/GeoContext';
import { GuestProvider } from '@/contexts/GuestContext';
import { AgeGateProvider, useAgeGate } from '@/contexts/AgeGateContext';
import { TelegramProvider, useTelegram } from '@/contexts/TelegramContext';
import { MainLayout, RoxyShellLayout } from '@/components/layout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { CookieConsent, ErrorBoundary } from '@/components/common';
import { PWAInstallPrompt } from '@/components/common/PWAInstallPrompt';
import { AgeGatePage } from '@/pages/AgeGatePage';
import { AgeBlockedPage } from '@/pages/AgeBlockedPage';

import { SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, SupportedLanguage } from '@/i18n';

// Pages
import { LandingPage } from '@/pages/LandingPage';
import { RegionBlockedPage } from '@/pages/RegionBlockedPage';
import { GuestChatPage } from '@/pages/GuestChatPage';
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { ForgotPasswordPage } from '@/pages/ForgotPasswordPage';
import { CheckEmailPage } from '@/pages/CheckEmailPage';
import { VerifyEmailPage } from '@/pages/VerifyEmailPage';
import { ChatPage } from '@/pages/ChatPage';
import { GroupChatPage } from '@/pages/GroupChatPage';
import { CreateCharacterPage } from '@/pages/CreateCharacterPage';
import { MyCharactersPage } from '@/pages/MyCharactersPage';
import { ProfilePage } from '@/pages/ProfilePage';
import SettingsPage from '@/pages/SettingsPage';
import { FeaturesPage } from '@/pages/FeaturesPage';
import { SubscriptionsPage } from '@/pages/SubscriptionsPage';
import { CharactersPage } from '@/pages/CharactersPage';
import { CreatorPage } from '@/pages/CreatorPage';
import { FAQPage } from '@/pages/FAQPage';
import { PrivacyPolicyPage } from '@/pages/PrivacyPolicyPage';
import { TermsOfServicePage } from '@/pages/TermsOfServicePage';
import BlogList from '@/pages/blog/BlogList';
import BlogPost from '@/pages/blog/BlogPost';
import { GalleryPage } from '@/pages/GalleryPage';
import { GrowthPage } from '@/pages/GrowthPage';
import { RewardsPage } from '@/pages/RewardsPage';
import { MatureSettingsPage } from '@/pages/MatureSettingsPage';
import { GenerateImageCharactersPage } from '@/pages/GenerateImageCharactersPage';
import { GenerateImageComposerPage } from '@/pages/GenerateImageComposerPage';

import BillingPage from '@/pages/BillingPage';
import BillingSuccessPage from '@/pages/billing/SuccessPage';
import BillingCancelPage from '@/pages/billing/CancelPage';
import BillingSupportPage from '@/pages/billing/SupportPage';

import { CreatorCenterPage } from '@/pages/CreatorCenterPage';
import { CreateScriptPage } from '@/pages/CreateScriptPage';
import { EditScriptPage } from '@/pages/EditScriptPage';
import { ScriptLibraryList, ScriptLibraryDetail } from '@/pages/ScriptLibrary';
import { MemoryManagementPage } from '@/pages/MemoryManagementPage';
import { CommunityPage } from '@/pages/CommunityPage';
import { CreatorProfilePage } from '@/pages/CreatorProfilePage';
import AdminPage from '@/pages/admin/AdminPage';
import AdminLoginPage from '@/pages/admin/AdminLoginPage';
import CharacterCreatePage from '@/pages/admin/CharacterCreatePage';
import CharacterEditPage from '@/pages/admin/CharacterEditPage';
import StoryEditPage from '@/pages/admin/StoryEditPage';

function LanguageHandler() {
  const { i18n } = useTranslation();
  const { lang } = useParams<{ lang?: string }>();

  React.useEffect(() => {
    const langInPath = lang as SupportedLanguage | undefined;
    const isValidLang = langInPath && SUPPORTED_LANGUAGES.includes(langInPath);

    if (isValidLang && i18n.language !== langInPath) {
      i18n.changeLanguage(langInPath);
    } else if (!langInPath || !isValidLang) {
      const browserLang = navigator.language.split('-')[0];
      const detectedLang = SUPPORTED_LANGUAGES.includes(browserLang as SupportedLanguage)
        ? browserLang
        : DEFAULT_LANGUAGE;

      if (i18n.language !== detectedLang) {
        i18n.changeLanguage(detectedLang);
      }
    }
  }, [lang, i18n]);

  return <Outlet />;
}

function useLangPrefix() {
  const { lang } = useParams<{ lang?: string }>();
  const isValidLang = lang && SUPPORTED_LANGUAGES.includes(lang as SupportedLanguage);
  return isValidLang ? `/${lang}` : '';
}

function GeoBlockedWrapper({ children }: { children: React.ReactNode }) {
  const { isTma } = useTelegram();
  const { allowed, isLoading, countryCode, countryName } = useGeoContext();

  if (isTma) return <>{children}</>;

  if (isLoading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-zinc-950">
        <Loader2 className="w-12 h-12 text-pink-500 animate-spin" />
      </div>
    );
  }

  if (!allowed) {
    return <RegionBlockedPage countryCode={countryCode} countryName={countryName} />;
  }

  return <>{children}</>;
}

function AgeGateWrapper({ children }: { children: React.ReactNode }) {
  const { isTma } = useTelegram();
  const { isAuthenticated } = useAuth();
  const { isVerified, isUserBlocked, loading } = useAgeGate();
  const location = useLocation();

  if (isTma) return <>{children}</>;

  const exemptRoutes = ['/terms', '/privacy', '/region-blocked'];
  const pathWithoutLang = location.pathname.replace(/^\/[a-z]{2}(\/|$)/, '$1');
  const isExemptRoute = exemptRoutes.some(route => pathWithoutLang.startsWith(route));

  if (isExemptRoute) {
    return <>{children}</>;
  }

  if (loading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-zinc-950">
        <Loader2 className="w-12 h-12 text-pink-500 animate-spin" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <>{children}</>;
  }

  if (isUserBlocked) {
    return <AgeBlockedPage />;
  }

  if (!isVerified) {
    return <AgeGatePage />;
  }

  return <>{children}</>;
}

function ChatPageWrapper() {
  const { isAuthenticated, loading } = useAuth();
  const [searchParams] = useSearchParams();
  const mode = searchParams.get('mode');
  const langPrefix = useLangPrefix();

  if (loading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-zinc-950">
        <Loader2 className="w-12 h-12 text-pink-500 animate-spin" />
      </div>
    );
  }

  if (mode === 'guest' && !isAuthenticated) {
    return <GuestChatPage />;
  }

  if (!isAuthenticated) {
    return <Navigate to={langPrefix + '/login'} />;
  }

  return <ChatPage />;
}

function LegacyChatRedirect() {
  const [searchParams] = useSearchParams();
  const characterId = searchParams.get('character');
  const mode = searchParams.get('mode');
  const langPrefix = useLangPrefix();
  const [redirectTo, setRedirectTo] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    if (!characterId) {
      setRedirectTo(null);
      setLoading(false);
      return;
    }
    fetch(`/api/characters/official/${characterId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.slug) {
          const prefix =
            data.top_category === 'anime'
              ? 'ai-anime'
              : data.top_category === 'guys'
              ? 'ai-boyfriend'
              : 'ai-girlfriend';
          setRedirectTo(`${langPrefix}/${prefix}/${data.slug}${mode ? `?mode=${mode}` : ''}`);
        } else {
          setRedirectTo(null);
        }
      })
      .catch(() => setRedirectTo(null))
      .finally(() => setLoading(false));
  }, [characterId, mode, langPrefix]);

  if (loading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-zinc-950">
        <Loader2 className="w-12 h-12 text-pink-500 animate-spin" />
      </div>
    );
  }

  if (redirectTo) {
    return <Navigate to={redirectTo} replace />;
  }

  return <ChatPageWrapper />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LanguageHandler />}>
        <Route
          path="/"
          element={
            <MainLayout showHeader={false} showFooter={false} showBottomNav={false}>
              <LandingPage />
            </MainLayout>
          }
        />
        <Route
          path="/features"
          element={
            <MainLayout>
              <FeaturesPage />
            </MainLayout>
          }
        />
        <Route
          path="/subscriptions"
          element={
            <RoxyShellLayout>
              <SubscriptionsPage />
            </RoxyShellLayout>
          }
        />
        <Route path="/pricing" element={<Navigate to="/subscriptions" replace />} />
        <Route
          path="/character"
          element={
            <RoxyShellLayout>
              <CharactersPage />
            </RoxyShellLayout>
          }
        />
        <Route
          path="/discover"
          element={
            <RoxyShellLayout>
              <CharactersPage />
            </RoxyShellLayout>
          }
        />
        <Route
          path="/ai-girlfriend"
          element={
            <RoxyShellLayout>
              <CharactersPage initialCategory="girls" />
            </RoxyShellLayout>
          }
        />
        <Route path="/ai-girlfriend/:slug" element={<ChatPageWrapper />} />
        <Route
          path="/ai-anime"
          element={
            <RoxyShellLayout>
              <CharactersPage initialCategory="anime" />
            </RoxyShellLayout>
          }
        />
        <Route path="/ai-anime/:slug" element={<ChatPageWrapper />} />
        <Route
          path="/ai-boyfriend"
          element={
            <RoxyShellLayout>
              <CharactersPage initialCategory="guys" />
            </RoxyShellLayout>
          }
        />
        <Route path="/ai-boyfriend/:slug" element={<ChatPageWrapper />} />
        <Route
          path="/chat/group"
          element={
            <ProtectedRoute>
              <GroupChatPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat/group/:sessionId"
          element={
            <ProtectedRoute>
              <GroupChatPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/creator"
          element={
            <MainLayout>
              <CreatorPage />
            </MainLayout>
          }
        />
        <Route
          path="/creators/:userId"
          element={
            <MainLayout>
              <CreatorProfilePage />
            </MainLayout>
          }
        />
        <Route
          path="/faq"
          element={
            <RoxyShellLayout>
              <FAQPage />
            </RoxyShellLayout>
          }
        />
        <Route
          path="/privacy"
          element={
            <MainLayout>
              <PrivacyPolicyPage />
            </MainLayout>
          }
        />
        <Route
          path="/terms"
          element={
            <MainLayout>
              <TermsOfServicePage />
            </MainLayout>
          }
        />
        <Route
          path="/login"
          element={
            <MainLayout showHeader={false} showFooter={false}>
              <LoginPage />
            </MainLayout>
          }
        />
        <Route
          path="/register"
          element={
            <MainLayout showHeader={false} showFooter={false}>
              <RegisterPage />
            </MainLayout>
          }
        />
        <Route
          path="/forgot-password"
          element={
            <MainLayout showHeader={false} showFooter={false}>
              <ForgotPasswordPage />
            </MainLayout>
          }
        />
        <Route
          path="/register/check-email"
          element={
            <MainLayout showHeader={false} showFooter={false}>
              <CheckEmailPage />
            </MainLayout>
          }
        />
        <Route
          path="/verify-email"
          element={
            <MainLayout showHeader={false} showFooter={false}>
              <VerifyEmailPage />
            </MainLayout>
          }
        />
        <Route path="/chat" element={<LegacyChatRedirect />} />
        <Route
          path="/create-character"
          element={
            <ProtectedRoute>
              <MainLayout showHeader={false} showFooter={false} showBottomNav={false}>
                <CreateCharacterPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/characters"
          element={
            <ProtectedRoute>
              <MainLayout showHeader={false} showFooter={false} showBottomNav={false}>
                <MyCharactersPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <RoxyShellLayout>
                <ProfilePage />
              </RoxyShellLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <MainLayout>
                <SettingsPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/gallery"
          element={
            <ProtectedRoute>
              <MainLayout>
                <GalleryPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/collection"
          element={
            <ProtectedRoute>
              <RoxyShellLayout>
                <GalleryPage />
              </RoxyShellLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/generate-image"
          element={
            <ProtectedRoute>
              <MainLayout showHeader={false} showFooter={false} showBottomNav={false}>
                <GenerateImageCharactersPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/generate-image/:characterId"
          element={
            <ProtectedRoute>
              <MainLayout showHeader={false} showFooter={false} showBottomNav={false}>
                <GenerateImageComposerPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/growth"
          element={
            <ProtectedRoute>
              <MainLayout>
                <GrowthPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/rewards"
          element={
            <ProtectedRoute>
              <MainLayout>
                <RewardsPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/mature-settings"
          element={
            <ProtectedRoute>
              <MainLayout>
                <MatureSettingsPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/creator-center"
          element={
            <ProtectedRoute>
              <CreatorCenterPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/community"
          element={
            <ProtectedRoute>
              <CommunityPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/script-library"
          element={
            <MainLayout>
              <ScriptLibraryList />
            </MainLayout>
          }
        />
        <Route
          path="/script-library/:scriptId"
          element={
            <MainLayout>
              <ScriptLibraryDetail />
            </MainLayout>
          }
        />
        <Route
          path="/create-script"
          element={
            <ProtectedRoute>
              <CreateScriptPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/edit-script/:scriptId"
          element={
            <ProtectedRoute>
              <EditScriptPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/memories/:characterId"
          element={
            <ProtectedRoute>
              <MainLayout>
                <MemoryManagementPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/login"
          element={<AdminLoginPage />}
        />
        <Route
          path="/admin/characters/create"
          element={<CharacterCreatePage />}
        />
        <Route
          path="/admin/characters/:characterId/edit"
          element={<CharacterEditPage />}
        />
        <Route
          path="/admin/stories/create"
          element={<StoryEditPage />}
        />
        <Route
          path="/admin/stories/:storyId/edit"
          element={<StoryEditPage />}
        />
        <Route
          path="/admin/*"
          element={<AdminPage />}
        />
        <Route
          path="/billing"
          element={
            <ProtectedRoute>
              <MainLayout>
                <BillingPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/billing/success"
          element={
            <ProtectedRoute>
              <MainLayout showHeader={false} showFooter={false}>
                <BillingSuccessPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/billing/cancel"
          element={
            <MainLayout showHeader={false} showFooter={false}>
              <BillingCancelPage />
            </MainLayout>
          }
        />
        <Route
          path="/billing/support"
          element={
            <ProtectedRoute>
              <BillingSupportPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/blog"
          element={
            <MainLayout>
              <BlogList />
            </MainLayout>
          }
        />
        <Route
          path="/blog/:slug"
          element={
            <MainLayout>
              <BlogPost />
            </MainLayout>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
    <TelegramProvider>
    <Router>
      <Suspense fallback={
        <div className="fixed inset-0 flex items-center justify-center bg-zinc-950">
          <Loader2 className="w-12 h-12 text-pink-500 animate-spin" />
        </div>
      }>
        <AuthProvider>
          <GeoProvider>
            <AgeGateProvider>
              <GuestProvider>
                <ErrorBoundary>
                  <GeoBlockedWrapper>
                    <AgeGateWrapper>
                      <CookieConsent />
                      <PWAInstallPrompt />
                      <AppRoutes />
                    </AgeGateWrapper>
                  </GeoBlockedWrapper>
                </ErrorBoundary>
              </GuestProvider>
            </AgeGateProvider>
          </GeoProvider>
        </AuthProvider>
      </Suspense>
    </Router>
    </TelegramProvider>
    </QueryClientProvider>
  );
}

export default App;
