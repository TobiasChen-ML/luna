import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate, Navigate } from 'react-router-dom';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { Button, Input, Card } from '@/components/common';
import { Container } from '@/components/layout';
import { Sparkles, AlertTriangle } from 'lucide-react';
import { useRecaptcha } from '@/hooks/useRecaptcha';

const blockedEmailDomains = ['qq.com', '163.com', '126.com'];

const registerSchema = z
  .object({
    email: z
      .string()
      .email()
      .refine(
        (email) => !blockedEmailDomains.includes(email.split('@')[1]?.toLowerCase() || ''),
        'blockedDomain'
      ),
    phoneNumber: z
      .string()
      .optional()
      .refine((value) => !value || !value.trim().startsWith('+86'), 'blockedPhone'),
    ageConsentGiven: z.boolean().refine((v) => v, 'ageConsentRequired'),
    password: z.string().min(6),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'passwordMismatch',
    path: ['confirmPassword'],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const { t } = useTranslation('auth');
  const { t: tValidation } = useTranslation('validation');
  const navigate = useNavigate();
  const { register: registerUser, loginWithGoogle, isAuthenticated, loading: authLoading } = useAuth();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { executeRecaptcha, resetRecaptcha, recaptchaContainerRef, recaptchaVersion, isConfigured } = useRecaptcha();

  if (!authLoading && isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      ageConsentGiven: false,
      phoneNumber: '',
    },
  });

  const getErrorMessage = (err: any): string => {
    if (err.response?.status === 429) {
      return t('register.errors.tooManyAttempts');
    } else if (err.response?.data?.detail) {
      return typeof err.response.data.detail === 'string' ? err.response.data.detail : t('register.errors.sendFailed');
    } else if (err.code === 'auth/email-already-in-use') {
      return t('register.errors.emailInUse');
    } else if (err.code === 'auth/weak-password') {
      return t('register.errors.weakPassword');
    } else {
      return t('register.errors.sendFailed');
    }
  };

  const onSubmit = async (data: RegisterFormData) => {
    setError('');
    setLoading(true);

    try {
      const captchaToken = await executeRecaptcha('register');
      if (isConfigured && recaptchaVersion === 'v2' && !captchaToken) {
        setError(t('register.errors.captchaRequired'));
        setLoading(false);
        return;
      }

      await registerUser(
        data.email,
        data.password,
        data.ageConsentGiven,
        data.phoneNumber,
        captchaToken
      );
      navigate('/register/check-email', { state: { email: data.email } });
    } catch (err: any) {
      resetRecaptcha();
      console.error('Registration error:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignUp = async () => {
    setError('');
    setGoogleLoading(true);

    try {
      const result = await loginWithGoogle();
      if (result === 'success') {
        navigate('/chat');
      }
    } catch (err: any) {
      console.error('Google sign-up error:', err);
      if (err.code === 'auth/popup-closed-by-user') {
      } else if (err.code === 'auth/cancelled-popup-request') {
      } else if (err.code === 'auth/popup-blocked') {
        setError(t('register.errors.popupBlocked'));
      } else if (err.needsDOB) {
        navigate('/chat', { state: { needsDOB: true } });
      } else {
        setError(t('register.errors.googleFailed'));
      }
    } finally {
      setGoogleLoading(false);
    }
  };

  const getFieldError = (field: string, errorType?: string): string | undefined => {
    if (!errorType) return undefined;
    
    switch (errorType) {
      case 'blockedDomain':
        return t('register.errors.emailDomainBlocked');
      case 'blockedPhone':
        return t('register.errors.phoneBlocked');
      case 'ageConsentRequired':
        return tValidation('required');
      case 'passwordMismatch':
        return tValidation('password.mismatch');
      default:
        return undefined;
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
          <h1 className="text-4xl font-heading font-bold mb-2">{t('register.title')}</h1>
          <p className="text-zinc-400">{t('register.subtitle')}</p>
        </div>

        <Card glass>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-500 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <Input
              {...register('email')}
              type="email"
              label={t('register.email')}
              placeholder={t('register.emailPlaceholder')}
              error={getFieldError('email', errors.email?.type === 'refine' ? 'blockedDomain' : undefined) || (errors.email ? tValidation('email.invalid') : undefined)}
              disabled={loading}
              autoComplete="email"
            />

            <Input
              {...register('phoneNumber')}
              type="tel"
              label={t('register.phoneNumber')}
              placeholder={t('register.phonePlaceholder')}
              error={getFieldError('phone', errors.phoneNumber?.type === 'refine' ? 'blockedPhone' : undefined)}
              disabled={loading}
              autoComplete="tel"
            />

            <Input
              {...register('password')}
              type="password"
              label={t('register.password')}
              placeholder={t('register.passwordPlaceholder')}
              error={errors.password ? tValidation('password.minLength', { count: 6 }) : undefined}
              disabled={loading}
              autoComplete="new-password"
              helperText={t('register.passwordHelper')}
            />

            <Input
              {...register('confirmPassword')}
              type="password"
              label={t('register.confirmPassword')}
              placeholder={t('register.passwordPlaceholder')}
              error={getFieldError('confirmPassword', errors.confirmPassword?.message)}
              disabled={loading}
              autoComplete="new-password"
            />

            <div className="space-y-4 pt-2 border-t border-white/10">
              <div className="flex items-start gap-3 text-amber-500/90 bg-amber-500/10 p-3 rounded-lg text-xs leading-relaxed">
                <AlertTriangle className="shrink-0 w-4 h-4 mt-0.5" />
                <p>
                  <span className="font-medium">18+ Only:</span> {t('register.ageNotice')}
                </p>
              </div>

              <label className="flex items-start gap-2 text-sm text-zinc-300">
                <input
                  {...register('ageConsentGiven')}
                  type="checkbox"
                  className="mt-1"
                  disabled={loading}
                />
                <span>{t('register.ageConsent')}</span>
              </label>
              {errors.ageConsentGiven?.message && (
                <p className="text-sm text-red-500">{getFieldError('ageConsentGiven', errors.ageConsentGiven.message)}</p>
              )}
            </div>

            <div className="text-sm text-zinc-400">
              {t('register.termsAgree')}{' '}
              <Link to="/terms" className="text-primary-500 hover:text-primary-400">
                {t('register.termsOfService')}
              </Link>{' '}
              {t('register.and')}{' '}
              <Link to="/privacy" className="text-primary-500 hover:text-primary-400">
                {t('register.privacyPolicy')}
              </Link>
            </div>

            {isConfigured && recaptchaVersion === 'v2' && (
              <div className="flex justify-center">
                <div ref={recaptchaContainerRef} />
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              loading={loading}
              disabled={loading || googleLoading}
            >
              {t('register.createAccount')}
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
              onClick={handleGoogleSignUp}
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
              {t('register.continueWithGoogle')}
            </Button>

            <div className="text-center text-sm text-zinc-400">
              {t('register.hasAccount')}{' '}
              <Link
                to="/login"
                className="text-primary-500 hover:text-primary-400 transition-colors font-medium"
              >
                {t('register.signIn')}
              </Link>
            </div>
          </form>
        </Card>
      </Container>
    </div>
  );
}
