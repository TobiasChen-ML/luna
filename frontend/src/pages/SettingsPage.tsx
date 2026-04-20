import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Smartphone } from 'lucide-react';
import { Container } from '@/components/layout/Container';
import { VoicePresenceSettings } from '@/components/settings/VoicePresenceSettings';
import { PWAInstallModal } from '@/components/common/PWAInstallModal';
import { Link } from 'react-router-dom';
import { useTelegramBackButton } from '@/hooks/useTelegramBackButton';
import { isPWA, detectPlatform } from '@/utils/pwa';
import { isTelegramMiniApp } from '@/utils/telegram';

export default function SettingsPage() {
  const { t } = useTranslation('settings');
  const navigate = useNavigate();
  const [showPWAModal, setShowPWAModal] = useState(false);
  useTelegramBackButton(() => navigate(-1));

  const canShowInstall = !isPWA() && !isTelegramMiniApp();
  const platform = detectPlatform();
  const installLabel = platform === 'ios' ? 'Add to Home Screen' : 'Install App';

  const handleInstallClick = () => {
    setShowPWAModal(true);
  };

  return (
    <Container>
      <div className="py-8 max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">{t('title')}</h1>
          <p className="text-gray-600">{t('description') || 'Manage your preferences and account settings'}</p>
        </div>

        {canShowInstall && (
          <section className="rounded-xl border border-purple-500/30 bg-purple-500/10 p-4">
            <button
              onClick={handleInstallClick}
              className="flex items-center gap-3 w-full text-left"
            >
              <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                <Smartphone className="w-5 h-5 text-purple-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-white">{installLabel}</h3>
                <p className="text-sm text-purple-300/80">Quick access, offline support, native experience</p>
              </div>
              <span className="text-purple-400 text-sm">Learn how</span>
            </button>
          </section>
        )}

        <section>
          <VoicePresenceSettings />
        </section>

        <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-3">
          <h2 className="text-lg font-semibold text-white">{t('more') || 'More'}</h2>
          <div className="flex flex-wrap gap-2">
            <Link to="/growth" className="px-3 py-2 rounded-lg border border-zinc-700 text-sm text-zinc-200 hover:bg-zinc-800">
              {t('growth') || 'Growth'}
            </Link>
            <Link to="/rewards" className="px-3 py-2 rounded-lg border border-zinc-700 text-sm text-zinc-200 hover:bg-zinc-800">
              {t('rewards') || 'Rewards'}
            </Link>
            <Link to="/mature-settings" className="px-3 py-2 rounded-lg border border-zinc-700 text-sm text-zinc-200 hover:bg-zinc-800">
              {t('matureContent') || 'MATURE Preferences'}
            </Link>
          </div>
        </section>
      </div>

      <PWAInstallModal isOpen={showPWAModal} onClose={() => setShowPWAModal(false)} />
    </Container>
  );
}
