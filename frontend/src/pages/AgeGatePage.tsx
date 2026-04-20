import { useTranslation } from 'react-i18next';
import { ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/common/Button';
import { useAgeGate } from '@/contexts/AgeGateContext';

export function AgeGatePage() {
  const { t } = useTranslation('auth');
  const { verify, block } = useAgeGate();

  const handleEnter = () => {
    verify();
  };

  const handleLeave = () => {
    block();
  };

  return (
    <div className="fixed inset-0 bg-zinc-950 flex items-center justify-center z-50 p-4">
      <div className="max-w-md w-full bg-zinc-900 rounded-2xl p-8 text-center border border-zinc-800 shadow-xl">
        <div className="mb-6">
          <ShieldCheck className="w-16 h-16 text-primary-500 mx-auto" />
        </div>

        <h1 className="text-2xl font-bold text-white mb-4">
          {t('ageGate.title')}
        </h1>

        <p className="text-zinc-400 mb-8 leading-relaxed">
          {t('ageGate.subtitle')}
        </p>

        <div className="flex flex-col gap-3 mb-6">
          <Button
            variant="primary"
            size="lg"
            onClick={handleEnter}
            className="w-full"
          >
            {t('ageGate.yes')}
          </Button>

          <Button
            variant="secondary"
            size="lg"
            onClick={handleLeave}
            className="w-full"
          >
            {t('ageGate.no')}
          </Button>
        </div>

        <p className="text-xs text-zinc-500 leading-relaxed">
          {t('ageGate.notice')}{' '}
          <Link to="/terms" className="text-primary-400 hover:text-primary-300 underline">
            {t('register.termsOfService')}
          </Link>{' '}
          {t('register.and')}{' '}
          <Link to="/privacy" className="text-primary-400 hover:text-primary-300 underline">
            {t('register.privacyPolicy')}
          </Link>.
        </p>
      </div>
    </div>
  );
}
