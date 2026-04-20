import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { authService } from '@/services/authService';
import { Button, Input, Card } from '@/components/common';
import { Container } from '@/components/layout';
import { KeyRound, ArrowLeft, Mail } from 'lucide-react';

const forgotPasswordSchema = z.object({
  email: z.string().email(),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export function ForgotPasswordPage() {
  const { t } = useTranslation('auth');
  const { t: tValidation } = useTranslation('validation');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [sentEmail, setSentEmail] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setError('');
    setLoading(true);

    try {
      await authService.resetPassword(data.email);
      setSentEmail(data.email);
      setEmailSent(true);
    } catch (err: any) {
      console.error('Password reset error:', err);
      if (err.code === 'auth/user-not-found') {
        setError(t('login.errors.userNotFound'));
      } else if (err.code === 'auth/invalid-email') {
        setError(tValidation('email.invalid'));
      } else if (err.code === 'auth/too-many-requests') {
        setError(t('register.errors.tooManyAttempts'));
      } else {
        setError(t('forgotPassword.sendFailed') || 'Failed to send reset email. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (emailSent) {
    return (
      <div className="min-h-screen flex items-center justify-center py-12 px-4">
        <Container size="sm">
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <div className="relative">
                <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center">
                  <Mail size={32} className="text-white" />
                </div>
                <div className="absolute inset-0 bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl blur-xl opacity-50"></div>
              </div>
            </div>
            <h1 className="text-4xl font-heading font-bold mb-2">
              {t('forgotPassword.success')}
            </h1>
            <p className="text-zinc-400">
              {t('forgotPassword.successMessage')}
            </p>
            <p className="text-white font-medium mt-1">
              {sentEmail}
            </p>
          </div>

          <Card glass>
            <div className="space-y-6 text-center">
              <p className="text-zinc-400 text-sm">
                {t('forgotPassword.resend')}{' '}
                <Link to="#" className="text-primary-500 hover:text-primary-400">
                  {t('forgotPassword.resendLink')}
                </Link>
              </p>

              <div className="pt-4 border-t border-white/10">
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 text-primary-500 hover:text-primary-400 transition-colors font-medium"
                >
                  <ArrowLeft size={16} />
                  {t('forgotPassword.backToLogin')}
                </Link>
              </div>
            </div>
          </Card>
        </Container>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4">
      <Container size="sm">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center">
                <KeyRound size={32} className="text-white" />
              </div>
              <div className="absolute inset-0 bg-gradient-primary rounded-2xl blur-xl opacity-50"></div>
            </div>
          </div>
          <h1 className="text-4xl font-heading font-bold mb-2">
            {t('forgotPassword.title')}
          </h1>
          <p className="text-zinc-400">
            {t('forgotPassword.subtitle')}
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
                label={t('forgotPassword.email')}
                placeholder={t('forgotPassword.emailPlaceholder')}
                error={errors.email ? tValidation('email.invalid') : undefined}
                disabled={loading}
                autoComplete="email"
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              loading={loading}
              disabled={loading}
            >
              {t('forgotPassword.sendLink')}
            </Button>

            <div className="text-center">
              <Link
                to="/login"
                className="inline-flex items-center gap-2 text-zinc-400 hover:text-white transition-colors text-sm"
              >
                <ArrowLeft size={16} />
                {t('forgotPassword.backToLogin')}
              </Link>
            </div>
          </form>
        </Card>
      </Container>
    </div>
  );
}
