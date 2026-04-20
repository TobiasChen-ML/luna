import { useEffect, useState, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { signInWithCustomToken } from 'firebase/auth';
import { auth } from '@/config/firebase';
import { authService } from '@/services/authService';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { Card } from '@/components/common/Card';
import { Container } from '@/components/layout/Container';

export function VerifyEmailPage() {
  const { t } = useTranslation('auth');
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [errorMessage, setErrorMessage] = useState('');
  const verifiedRef = useRef(false);

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams.get('token');

      if (!token) {
        setStatus('error');
        setErrorMessage(t('verifyEmail.errorMessage'));
        return;
      }

      if (verifiedRef.current) return;
      verifiedRef.current = true;

      try {
        const { customToken } = await authService.verifyEmail(token);

        try {
          await signInWithCustomToken(auth, customToken);
        } catch (authError: any) {
          console.error('Firebase Auth Error:', authError);
          
          if (authError.code === 'auth/network-request-failed') {
             setErrorMessage(t('verifyEmail.networkError') || 'Verification successful, but failed to log in automatically. Please log in manually.');
          } else {
             console.warn("Ignoring Firebase login error after successful backend verification");
          }
        }

        setStatus('success');

        setTimeout(() => {
          navigate('/chat');
        }, 2000);

      } catch (error: any) {
        console.error('Verification error:', error);
        setStatus('error');

        if (error.response?.data?.detail) {
          setErrorMessage(error.response.data.detail);
        } else {
          setErrorMessage(t('verifyEmail.errorMessage'));
        }
      }
    };

    verifyEmail();
  }, [searchParams, navigate, t]);

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 bg-gradient-to-br from-zinc-900 via-purple-900/20 to-zinc-900">
      <Container size="sm">
        <Card>
          <div className="text-center space-y-6 p-8">
            {status === 'verifying' && (
              <>
                <Loader2 size={64} className="mx-auto text-purple-500 animate-spin" />
                <h2 className="text-2xl font-bold text-white">{t('verifyEmail.title')}</h2>
                <p className="text-zinc-400">{t('common:loading')}</p>
              </>
            )}

            {status === 'success' && (
              <>
                <CheckCircle size={64} className="mx-auto text-green-500" />
                <h2 className="text-2xl font-bold text-green-400">{t('verifyEmail.success')}</h2>
                <p className="text-zinc-400">
                  {t('verifyEmail.successMessage')}
                </p>
              </>
            )}

            {status === 'error' && (
              <>
                <XCircle size={64} className="mx-auto text-red-500" />
                <h2 className="text-2xl font-bold text-red-400">{t('verifyEmail.error')}</h2>
                <p className="text-zinc-400">{errorMessage}</p>
                <button
                  onClick={() => navigate('/register')}
                  className="text-purple-400 hover:text-purple-300 font-medium transition-colors"
                >
                  {t('register.createAccount')}
                </button>
              </>
            )}
          </div>
        </Card>
      </Container>
    </div>
  );
}
