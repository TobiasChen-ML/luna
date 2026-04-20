import { useLocation, useNavigate, Link } from 'react-router-dom';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, RefreshCw } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { Container } from '@/components/layout/Container';
import { authService } from '@/services/authService';

export function CheckEmailPage() {
  const { t } = useTranslation('auth');
  const location = useLocation();
  const navigate = useNavigate();
  const email = location.state?.email;
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);
  const [error, setError] = useState('');

  if (!email) {
    navigate('/register');
    return null;
  }

  const handleResend = async () => {
    setResending(true);
    setError('');
    try {
      await authService.resendVerification(email);
      setResent(true);
      setTimeout(() => setResent(false), 5000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resend email');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 bg-gradient-to-br from-zinc-900 via-purple-900/20 to-zinc-900">
      <Container size="sm">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center">
              <Mail size={32} className="text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold mb-2 text-white">
            {t('checkEmail.title')}
          </h1>
          <p className="text-zinc-400">
            {t('checkEmail.subtitle')}
          </p>
          <p className="text-purple-400 font-medium mt-1">{email}</p>
        </div>

        <Card>
          <div className="space-y-6 p-6">
            <div className="text-center text-zinc-300">
              <p>{t('checkEmail.instruction')}</p>
              <p className="text-sm text-zinc-400 mt-2">
                {t('checkEmail.spamNote')}
              </p>
            </div>

            {resent && (
              <div className="bg-green-500/10 border border-green-500/50 text-green-400 px-4 py-3 rounded-lg text-sm text-center">
                {t('checkEmail.resent') || 'Verification email resent successfully!'}
              </div>
            )}

            {error && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm text-center">
                {error}
              </div>
            )}

            <div className="space-y-3">
              <Button
                variant="secondary"
                className="w-full"
                onClick={handleResend}
                disabled={resending || resent}
              >
                <RefreshCw size={16} className={resending ? 'animate-spin' : ''} />
                {resent ? (t('checkEmail.resent') || 'Email Sent!') : t('checkEmail.resend')}
              </Button>

              <div className="text-center text-sm text-zinc-400">
                {t('register.hasAccount')}{' '}
                <Link to="/login" className="text-purple-400 hover:text-purple-300 transition-colors font-medium">
                  {t('register.signIn')}
                </Link>
              </div>
            </div>
          </div>
        </Card>

        <div className="mt-6 text-center text-sm text-zinc-500">
          <p>{t('checkEmail.spamNote')}</p>
        </div>
      </Container>
    </div>
  );
}
