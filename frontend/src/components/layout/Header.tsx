import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { LanguageSwitcher } from '@/i18n';
import { Container } from './Container';
import { Menu, X, Sparkles, MessageSquare, Users, User, BookOpen, LogOut } from 'lucide-react';

export function Header() {
  const { t } = useTranslation('navigation');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
    setIsMenuOpen(false);
  };

  const scrollToSection = (sectionId: string) => {
    if (location.pathname !== '/') {
      navigate('/');
      setTimeout(() => {
        const element = document.getElementById(sectionId);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    } else {
      const element = document.getElementById(sectionId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  const handleNavClick = (sectionId: string) => {
    setIsMenuOpen(false);
    scrollToSection(sectionId);
  };

  return (
    <header
      className="fixed left-0 right-0 z-50 glass-effect border-b border-white/10"
      style={{ top: 'var(--app-safe-area-top)' }}
    >
      <Container>
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2 group">
            <div className="relative">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <Sparkles size={16} className="text-white" />
              </div>
              <div className="absolute inset-0 bg-gradient-primary rounded-lg blur-lg opacity-50 group-hover:opacity-75 transition-opacity"></div>
            </div>
            <span className="font-heading font-bold text-xl gradient-text">
              RoxyClub
            </span>
          </Link>

          <nav className="hidden md:flex items-center space-x-6">
            {user ? (
              <>
                <Link
                  to="/chat"
                  className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
                >
                  <MessageSquare size={18} />
                  {t('chat')}
                </Link>
                <Link
                  to="/characters"
                  className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
                >
                  <Users size={18} />
                  {t('characters')}
                </Link>
                <Link
                  to="/profile"
                  className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
                >
                  <User size={18} />
                  {t('profile')}
                </Link>
                <a
                  href="/blog/"
                  className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
                  onClick={(e) => {
                    e.preventDefault();
                    window.location.href = '/blog/';
                  }}
                >
                  <BookOpen size={18} />
                  {t('blog')}
                </a>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 text-zinc-400 hover:text-red-400 transition-colors"
                >
                  <LogOut size={18} />
                  {t('logout')}
                </button>
              </>
            ) : (
              <>
                {location.pathname === '/' ? (
                  <>
                    <button
                      onClick={() => scrollToSection('gameplay')}
                      className="text-zinc-400 hover:text-white transition-colors"
                    >
                      {t('gameplay')}
                    </button>
                    <button
                      onClick={() => scrollToSection('characters')}
                      className="text-zinc-400 hover:text-white transition-colors"
                    >
                      {t('characters')}
                    </button>
                    <button
                      onClick={() => scrollToSection('pricing')}
                      className="text-zinc-400 hover:text-white transition-colors"
                    >
                      {t('subscriptions')}
                    </button>
                    <button
                      onClick={() => scrollToSection('faq')}
                      className="text-zinc-400 hover:text-white transition-colors"
                    >
                      {t('faq')}
                    </button>
                    <a
                      href="/blog/"
                      className="text-zinc-400 hover:text-white transition-colors"
                      onClick={(e) => {
                        e.preventDefault();
                        window.location.href = '/blog/';
                      }}
                    >
                      {t('blog')}
                    </a>
                  </>
                ) : (
                  <>
                    <Link
                      to="/features"
                      className="text-zinc-400 hover:text-white transition-colors"
                    >
                      {t('gameplay')}
                    </Link>
                    <Link
                      to="/character"
                      className="text-zinc-400 hover:text-white transition-colors"
                    >
                      {t('characters')}
                    </Link>
                    <Link
                      to="/subscriptions"
                      className="text-zinc-400 hover:text-white transition-colors"
                    >
                      {t('subscriptions')}
                    </Link>
                    <Link
                      to="/faq"
                      className="text-zinc-400 hover:text-white transition-colors"
                    >
                      {t('faq')}
                    </Link>
                    <a
                      href="/blog/"
                      className="text-zinc-400 hover:text-white transition-colors"
                      onClick={(e) => {
                        e.preventDefault();
                        window.location.href = '/blog/';
                      }}
                    >
                      {t('blog')}
                    </a>
                  </>
                )}
                <Link
                  to="/login"
                  className="text-zinc-400 hover:text-white transition-colors"
                >
                  {t('login')}
                </Link>
                <Link
                  to="/register"
                  className="btn-primary"
                >
                  {t('getStarted')}
                </Link>
              </>
            )}
          </nav>

          {!user && (
            <button
              className="md:hidden text-white p-2"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              aria-label="Toggle menu"
            >
              {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          )}

          <div className="flex items-center gap-3">
            <LanguageSwitcher />
          </div>
        </div>

        {isMenuOpen && (
          <nav className="md:hidden py-4 space-y-2 border-t border-white/10">
            {user ? (
              <>
                <Link
                  to="/chat"
                  className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors py-3 px-2"
                  onClick={() => setIsMenuOpen(false)}
                >
                  <MessageSquare size={18} />
                  {t('chat')}
                </Link>
                <Link
                  to="/characters"
                  className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors py-3 px-2"
                  onClick={() => setIsMenuOpen(false)}
                >
                  <Users size={18} />
                  {t('characters')}
                </Link>
                <Link
                  to="/profile"
                  className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors py-3 px-2"
                  onClick={() => setIsMenuOpen(false)}
                >
                  <User size={18} />
                  {t('profile')}
                </Link>
                <a
                  href="/blog/"
                  className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors py-3 px-2"
                  onClick={(e) => {
                    e.preventDefault();
                    setIsMenuOpen(false);
                    window.location.href = '/blog/';
                  }}
                >
                  <BookOpen size={18} />
                  {t('blog')}
                </a>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 text-zinc-400 hover:text-red-400 transition-colors py-3 px-2"
                >
                  <LogOut size={18} />
                  {t('logout')}
                </button>
              </>
            ) : (
              <>
                {location.pathname === '/' ? (
                  <>
                    <button
                      onClick={() => handleNavClick('gameplay')}
                      className="block w-full text-left text-zinc-400 hover:text-white transition-colors py-3 px-2"
                    >
                      {t('gameplay')}
                    </button>
                    <button
                      onClick={() => handleNavClick('characters')}
                      className="block w-full text-left text-zinc-400 hover:text-white transition-colors py-3 px-2"
                    >
                      {t('characters')}
                    </button>
                    <button
                      onClick={() => handleNavClick('pricing')}
                      className="block w-full text-left text-zinc-400 hover:text-white transition-colors py-3 px-2"
                    >
                      {t('subscriptions')}
                    </button>
                    <button
                      onClick={() => handleNavClick('faq')}
                      className="block w-full text-left text-zinc-400 hover:text-white transition-colors py-3 px-2"
                    >
                      {t('faq')}
                    </button>
                    <a
                      href="/blog/"
                      className="block w-full text-left text-zinc-400 hover:text-white transition-colors py-3 px-2"
                      onClick={(e) => {
                        e.preventDefault();
                        setIsMenuOpen(false);
                        window.location.href = '/blog/';
                      }}
                    >
                      {t('blog')}
                    </a>
                  </>
                ) : (
                  <>
                    <Link
                      to="/features"
                      className="block w-full text-left text-zinc-400 hover:text-white transition-colors py-3 px-2"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      {t('gameplay')}
                    </Link>
                    <Link
                      to="/character"
                      className="block w-full text-left text-zinc-400 hover:text-white transition-colors py-3 px-2"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      {t('characters')}
                    </Link>
                    <Link
                      to="/subscriptions"
                      className="block w-full text-left text-zinc-400 hover:text-white transition-colors py-3 px-2"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      {t('subscriptions')}
                    </Link>
                    <Link
                      to="/faq"
                      className="block w-full text-left text-zinc-400 hover:text-white transition-colors py-3 px-2"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      {t('faq')}
                    </Link>
                    <a
                      href="/blog/"
                      className="block w-full text-left text-zinc-400 hover:text-white transition-colors py-3 px-2"
                      onClick={(e) => {
                        e.preventDefault();
                        setIsMenuOpen(false);
                        window.location.href = '/blog/';
                      }}
                    >
                      {t('blog')}
                    </a>
                  </>
                )}
                <Link
                  to="/login"
                  className="block text-zinc-400 hover:text-white transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  {t('login')}
                </Link>
                <Link
                  to="/register"
                  className="block btn-primary text-center"
                  onClick={() => setIsMenuOpen(false)}
                >
                  {t('getStarted')}
                </Link>
              </>
            )}
          </nav>
        )}
      </Container>
    </header>
  );
}
