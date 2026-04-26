import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Heart } from 'lucide-react';
import { Container } from './Container';

export function Footer() {
  const { t } = useTranslation('navigation');
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-white/10 bg-neutral-900/50 mt-auto">
      <Container>
        <div className="py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-primary rounded-lg"></div>
                <span className="font-heading font-bold text-xl gradient-text">
                  RoxyClub
                </span>
              </div>
              <p className="text-sm text-zinc-400">
                {t('footer.description')}
              </p>
              <p className="text-xs leading-relaxed text-zinc-500">
                Telegram-first access. Web and PWA support usage; paid digital benefits are
                activated in Telegram with Stars.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-4">{t('footer.product')}</h3>
              <ul className="space-y-2 text-sm text-zinc-400">
                <li>
                  <Link to="/features" className="hover:text-white transition-colors">
                    {t('gameplay')}
                  </Link>
                </li>
                <li>
                  <Link to="/character" className="hover:text-white transition-colors">
                    {t('characters')}
                  </Link>
                </li>
                <li>
                  <Link to="/subscriptions" className="hover:text-white transition-colors">
                    {t('pricing')}
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold mb-4">{t('footer.company')}</h3>
              <ul className="space-y-2 text-sm text-zinc-400">
                <li>
                  <a
                    href="/blog/"
                    className="hover:text-white transition-colors"
                    onClick={(e) => {
                      e.preventDefault();
                      window.location.href = '/blog/';
                    }}
                  >
                    {t('blog')}
                  </a>
                </li>
                <li>
                  <Link to="/privacy" className="hover:text-white transition-colors">
                    {t('privacy')}
                  </Link>
                </li>
                <li>
                  <Link to="/terms" className="hover:text-white transition-colors">
                    {t('terms')}
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold mb-4">{t('footer.support')}</h3>
              <ul className="space-y-2 text-sm text-zinc-400">
                <li>
                  <Link to="/faq" className="hover:text-white transition-colors">
                    {t('faq')}
                  </Link>
                </li>
                <li>
                  <a
                    href="mailto:support@roxyclub.ai"
                    className="hover:text-white transition-colors"
                  >
                    {t('footer.contactSupport')}
                  </a>
                </li>
              </ul>
            </div>
          </div>

          <div className="mt-12 pt-8 border-t border-white/10 flex flex-col md:flex-row items-center justify-between text-sm text-zinc-400">
            <p className="flex items-center gap-1">
              (c) {currentYear} RoxyClub. {t('footer.madeWith')} <Heart size={14} className="text-primary-500" fill="currentColor" /> {t('footer.byTeam')}.
            </p>
            <div className="flex items-center space-x-6 mt-4 md:mt-0">
              <Link to="/privacy" className="hover:text-white transition-colors">
                {t('privacy')}
              </Link>
              <Link to="/terms" className="hover:text-white transition-colors">
                {t('terms')}
              </Link>
            </div>
          </div>
        </div>
      </Container>
    </footer>
  );
}
