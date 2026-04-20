import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate, Navigate } from 'react-router-dom';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { Button, Input, Card } from '@/components/common';
import { Container } from '@/components/layout';
import { Sparkles, ShieldCheck } from 'lucide-react';

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { t } = useTranslation('auth');
  const navigate = useNavigate();
  const { login, loginWithGoogle, isAuthenticated, loading: authLoading } = useAuth();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  if (!authLoading && isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  const onSubmit = async (data: LoginFormData) => {
    setError('');
    setLoading(true);

    try {
      await login(data.email, data.password);
      navigate('/chat');
    } catch (err: any) {
      console.error('Login error:', err);
      if (err.code === 'auth/user-not-found') {
        setError(t('login.errors.userNotFound'));
      } else if (err.code === 'auth/wrong-password') {
        setError(t('login.errors.wrongPassword'));
      } else if (err.code === 'auth/invalid-credential') {
        setError(t('login.errors.invalidCredential'));
      } else {
        setError(t('login.errors.loginFailed'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError('');
    setGoogleLoading(true);

    try {
      const result = await loginWithGoogle();
      if (result === 'success') {
        navigate('/chat');
      }
    } catch (err: any) {
      console.error('Google login error:', err);
      if (err.code === 'auth/popup-closed-by-user') {
      } else if (err.code === 'auth/cancelled-popup-request') {
      } else if (err.code === 'auth/popup-blocked') {
        setError(t('login.errors.popupBlocked'));
      } else {
        setError(t('login.errors.googleFailed'));
      }
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4">
      <Container size="sm">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center">
                <Sparkles size={32} className="text-white" />
              </div>
              <div className="absolute inset-0 bg-gradient-primary rounded-2xl blur-xl opacity-50"></div>
            </div>
          </div>
          <h1 className="text-4xl font-heading font-bold mb-2">
            {t('login.title')}
          </h1>
          <p className="text-zinc-400">
            {t('login.subtitle')}
          </p>
        </div>

        <Card glass>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-500 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div>
              <Input
                {...register('email')}
                type="email"
                label={t('login.email')}
                placeholder={t('login.emailPlaceholder')}
                error={errors.email?.message}
                disabled={loading}
                autoComplete="email"
              />
            </div>

            <div>
              <Input
                {...register('password')}
                type="password"
                label={t('login.password')}
                placeholder={t('login.passwordPlaceholder')}
                error={errors.password?.message}
                disabled={loading}
                autoComplete="current-password"
              />
            </div>

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-white/20 bg-white/5 text-primary-500 focus:ring-primary-500 focus:ring-offset-0"
                />
                <span className="text-zinc-400">{t('login.rememberMe')}</span>
              </label>
              <Link
                to="/forgot-password"
                className="text-primary-500 hover:text-primary-400 transition-colors"
              >
                {t('login.forgotPassword')}
              </Link>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              loading={loading}
              disabled={loading || googleLoading}
            >
              {t('login.signIn')}
            </Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/10"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-zinc-900 text-zinc-400">{t('common:or')}</span>
              </div>
            </div>

            <Button
              type="button"
              variant="secondary"
              className="w-full flex items-center justify-center gap-3"
              onClick={handleGoogleLogin}
              loading={googleLoading}
              disabled={loading || googleLoading}
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              {t('login.continueWithGoogle')}
            </Button>

            <div className="space-y-3 pt-2">
              <div className="flex items-start gap-2 text-amber-500/90 bg-amber-500/10 p-3 rounded-lg text-xs leading-relaxed">
                <ShieldCheck className="shrink-0 w-4 h-4 mt-0.5" />
                <p>
                  {t('login.ageNotice')}
                </p>
              </div>
            </div>

            <div className="text-center text-sm text-zinc-400">
              {t('login.noAccount')}{' '}
              <Link
                to="/register"
                className="text-primary-500 hover:text-primary-400 transition-colors font-medium"
              >
                {t('login.createOne')}
              </Link>
            </div>
          </form>
        </Card>
      </Container>
    </div>
  );
}
