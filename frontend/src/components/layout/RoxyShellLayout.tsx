import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  BookHeart,
  ChevronDown,
  CircleDollarSign,
  Compass,
  Contact,
  Globe2,
  HelpCircle,
  Home,
  ImagePlus,
  Menu,
  MessageCircle,
  Trophy,
  UserCircle2,
  WandSparkles,
  X,
} from 'lucide-react';

import { CommingSoonModal, LanguageModal } from '@/components/common';
import { cn } from '@/utils/cn';

interface RoxyShellLayoutProps {
  children: React.ReactNode;
  contentClassName?: string;
}

export function RoxyShellLayout({ children, contentClassName }: RoxyShellLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isLanguageModalOpen, setIsLanguageModalOpen] = useState(false);
  const [isCommingSoonModalOpen, setIsCommingSoonModalOpen] = useState(false);

  const sidebarItems = useMemo(
    () => [
      { label: 'Home', icon: Home, to: '/' },
      { label: 'Discover', icon: Compass, to: '/discover' },
      { label: 'Chat', icon: MessageCircle, to: '/chat' },
      { label: 'Collection', icon: BookHeart, to: '/collection' },
      { label: 'Generate Image', icon: ImagePlus, to: '/generate-image' },
      { label: 'Create Character', icon: WandSparkles, to: '/create-character' },
      { label: 'My AI', icon: UserCircle2, to: '/characters' },
      { label: 'Premium', icon: CircleDollarSign, to: '/subscriptions', badge: '-70%' },
    ],
    []
  );

  const settingItems = useMemo(
    () => [
      { label: 'English', icon: Globe2, to: '#' },
      { label: 'Discord', icon: MessageCircle, to: '#', comingSoon: true },
      { label: 'Help Center', icon: HelpCircle, to: '/faq' },
      { label: 'Contact Us', icon: Contact, to: 'mailto:support@roxyclub.ai' },
      { label: 'Affiliate', icon: Trophy, to: '#', comingSoon: true },
    ],
    []
  );

  const categoryKey =
    location.pathname.startsWith('/ai-anime')
      ? 'anime'
      : location.pathname.startsWith('/ai-boyfriend')
        ? 'guys'
        : 'girls';

  const closeMobileMenu = () => setIsMobileMenuOpen(false);
  const isMobileViewport = () => window.matchMedia('(max-width: 767px)').matches;

  const handleNavToggle = () => {
    if (isMobileViewport()) {
      setIsMobileMenuOpen((prev) => !prev);
      return;
    }

    setIsSidebarCollapsed((prev) => !prev);
  };

  useEffect(() => {
    const onResize = () => {
      if (!isMobileViewport()) {
        setIsMobileMenuOpen(false);
      }
    };

    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return (
    <div className="min-h-screen bg-[#0b0c10] text-white">
      <header
        className="fixed right-0 left-0 z-40 border-b border-white/10 bg-[#0a0b0f]"
        style={{ top: 'var(--app-safe-area-top)' }}
      >
        <div className="h-14 px-5 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <button
              type="button"
              onClick={handleNavToggle}
              className="text-zinc-300 hover:text-white"
              aria-label="Toggle navigation"
              aria-expanded={isMobileMenuOpen}
            >
              <Menu size={22} />
            </button>
            <Link to="/" className="text-2xl font-bold leading-none">
              <span className="text-white">RoxyClub</span>
              <span className="text-pink-500">.ai</span>
            </Link>
            <nav className="hidden md:flex items-center gap-8 text-sm font-semibold">
              <Link
                to="/"
                className={cn(
                  'h-14 flex items-center border-b-2',
                  categoryKey === 'girls'
                    ? 'text-pink-400 border-pink-500'
                    : 'text-zinc-300 border-transparent hover:text-white'
                )}
              >
                Girls
              </Link>
              <button
                type="button"
                onClick={() => setIsCommingSoonModalOpen(true)}
                className={cn(
                  'h-14 flex items-center border-b-2',
                  categoryKey === 'anime'
                    ? 'text-pink-400 border-pink-500'
                    : 'text-zinc-300 border-transparent hover:text-white'
                )}
              >
                Anime
              </button>
              <button
                type="button"
                onClick={() => setIsCommingSoonModalOpen(true)}
                className={cn(
                  'h-14 flex items-center border-b-2',
                  categoryKey === 'guys'
                    ? 'text-pink-400 border-pink-500'
                    : 'text-zinc-300 border-transparent hover:text-white'
                )}
              >
                Guys
              </button>
            </nav>
          </div>
          <div className="flex items-center gap-5">
            <Link
              to="/subscriptions"
              className="hidden sm:inline-flex items-center rounded-full border border-pink-500/50 bg-purple-500/10 px-4 py-1.5 text-sm font-semibold text-pink-200"
            >
              Premium 70% OFF
            </Link>
            <button
              onClick={() => navigate('/profile')}
              className="flex items-center gap-2 text-zinc-100 font-semibold"
            >
              <span className="w-7 h-7 rounded-full bg-pink-400/90 inline-block" />
              <span className="hidden sm:inline">My Profile</span>
              <ChevronDown size={16} />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile drawer overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 z-50 md:hidden"
          onClick={closeMobileMenu}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

          {/* Drawer panel */}
          <div
            className="absolute top-0 left-0 bottom-0 w-[260px] bg-[#0a0b0f] border-r border-white/10 flex flex-col"
            style={{ paddingTop: 'var(--app-safe-area-top)' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Drawer header */}
            <div className="flex items-center justify-between h-14 px-4 border-b border-white/10">
              <Link
                to="/"
                onClick={closeMobileMenu}
                className="text-xl font-bold leading-none"
              >
                <span className="text-white">RoxyClub</span>
                <span className="text-pink-500">.ai</span>
              </Link>
              <button
                onClick={closeMobileMenu}
                className="text-zinc-400 hover:text-white p-1"
                aria-label="Close menu"
              >
                <X size={20} />
              </button>
            </div>

            {/* Nav items */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {sidebarItems.map((item) => {
                const Icon = item.icon;
                const active =
                  item.to === '/'
                    ? location.pathname === '/'
                    : location.pathname.startsWith(item.to);
                const sharedClass = cn(
                  'w-full flex items-center justify-between rounded-xl border px-3 py-2.5 text-sm transition-colors',
                  active
                    ? 'bg-zinc-700/40 border-zinc-500/70 text-white'
                    : 'border-white/10 text-zinc-300 hover:bg-white/5 hover:text-white'
                );
                return (
                  <Link
                    key={item.label}
                    to={item.to}
                    onClick={closeMobileMenu}
                    className={sharedClass}
                  >
                    <span className="flex items-center gap-2.5">
                      <Icon size={16} />
                      {item.label}
                    </span>
                    {item.badge && (
                      <span className="rounded-full bg-red-500 px-1.5 py-0.5 text-[10px] font-semibold text-white">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>

            {/* Settings */}
            <div className="p-4 space-y-2 border-t border-white/10">
              {settingItems.map((item) => {
                const Icon = item.icon;
                if (item.label === 'English') {
                  return (
                    <button
                      key={item.label}
                      onClick={() => {
                        closeMobileMenu();
                        setIsLanguageModalOpen(true);
                      }}
                      className="w-full flex items-center gap-2.5 rounded-xl border border-white/10 px-3 py-2.5 text-sm text-zinc-300 hover:bg-white/5 hover:text-white"
                    >
                      <Icon size={16} />
                      {item.label}
                    </button>
                  );
                }
                if (item.comingSoon) {
                  return (
                    <button
                      key={item.label}
                      onClick={() => {
                        closeMobileMenu();
                        setIsCommingSoonModalOpen(true);
                      }}
                      className="w-full flex items-center gap-2.5 rounded-xl border border-white/10 px-3 py-2.5 text-sm text-zinc-300 hover:bg-white/5 hover:text-white"
                    >
                      <Icon size={16} />
                      {item.label}
                    </button>
                  );
                }
                return (
                  <a
                    key={item.label}
                    href={item.to}
                    onClick={closeMobileMenu}
                    className="flex items-center gap-2.5 rounded-xl border border-white/10 px-3 py-2.5 text-sm text-zinc-300 hover:bg-white/5 hover:text-white"
                  >
                    <Icon size={16} />
                    {item.label}
                  </a>
                );
              })}
              <div className="pt-2 text-[10px] text-zinc-500">Privacy Notice | Terms of Service</div>
            </div>
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside
        className={`hidden md:flex fixed left-0 bottom-0 border-r border-white/10 bg-[#0a0b0f] flex-col transition-all duration-300 ${
          isSidebarCollapsed ? 'w-[82px]' : 'w-[234px]'
        }`}
        style={{ top: 'calc(3.5rem + var(--app-safe-area-top))' }}
      >
        <div className="p-4 space-y-2">
          {sidebarItems.map((item) => {
            const Icon = item.icon;
            const active = item.to === '/' ? location.pathname === '/' : location.pathname.startsWith(item.to);
            const sharedClass = `flex items-center rounded-xl border px-3 py-2 text-sm transition-colors ${
              isSidebarCollapsed ? 'justify-center' : 'justify-between'
            } ${
              active
                ? 'bg-zinc-700/40 border-zinc-500/70 text-white'
                : 'border-white/10 text-zinc-300 hover:bg-white/5 hover:text-white'
            }`;
            const inner = (
              <>
                <span className="flex items-center gap-2">
                  <Icon size={15} />
                  {!isSidebarCollapsed && item.label}
                </span>
                {!isSidebarCollapsed && item.badge && (
                  <span className="rounded-full bg-red-500 px-1.5 py-0.5 text-[10px] font-semibold text-white">
                    {item.badge}
                  </span>
                )}
              </>
            );
            return (
              <Link
                key={item.label}
                to={item.to}
                className={sharedClass}
                title={isSidebarCollapsed ? item.label : undefined}
              >
                {inner}
              </Link>
            );
          })}
        </div>

        <div className="mt-auto p-4 space-y-2 border-t border-white/10">
          {settingItems.map((item) => {
            const Icon = item.icon;
            if (item.label === 'English') {
              return (
                <button
                  key={item.label}
                  onClick={() => setIsLanguageModalOpen(true)}
                  className={`w-full flex items-center rounded-xl border border-white/10 px-3 py-2 text-sm text-zinc-300 hover:bg-white/5 hover:text-white ${
                    isSidebarCollapsed ? 'justify-center' : 'gap-2'
                  }`}
                  title={isSidebarCollapsed ? item.label : undefined}
                >
                  <Icon size={15} />
                  {!isSidebarCollapsed && item.label}
                </button>
              );
            }
            if (item.comingSoon) {
              return (
                <button
                  key={item.label}
                  onClick={() => setIsCommingSoonModalOpen(true)}
                  className={`w-full flex items-center rounded-xl border border-white/10 px-3 py-2 text-sm text-zinc-300 hover:bg-white/5 hover:text-white ${
                    isSidebarCollapsed ? 'justify-center' : 'gap-2'
                  }`}
                  title={isSidebarCollapsed ? item.label : undefined}
                >
                  <Icon size={15} />
                  {!isSidebarCollapsed && item.label}
                </button>
              );
            }
            return (
              <a
                key={item.label}
                href={item.to}
                className={`flex items-center rounded-xl border border-white/10 px-3 py-2 text-sm text-zinc-300 hover:bg-white/5 hover:text-white ${
                  isSidebarCollapsed ? 'justify-center' : 'gap-2'
                }`}
                title={isSidebarCollapsed ? item.label : undefined}
              >
                <Icon size={15} />
                {!isSidebarCollapsed && item.label}
              </a>
            );
          })}
          {!isSidebarCollapsed && (
            <div className="pt-2 text-[10px] text-zinc-500">Privacy Notice | Terms of Service</div>
          )}
        </div>
      </aside>

      <main
        className={`transition-all duration-300 ${
          isSidebarCollapsed ? 'md:pl-[82px]' : 'md:pl-[234px]'
        }`}
        style={{ paddingTop: 'calc(4rem + var(--app-safe-area-top))' }}
      >
        <div className={cn('mx-auto max-w-[1240px] p-4 md:p-7', contentClassName)}>{children}</div>
      </main>

      <LanguageModal
        isOpen={isLanguageModalOpen}
        onClose={() => setIsLanguageModalOpen(false)}
      />
      <CommingSoonModal
        isOpen={isCommingSoonModalOpen}
        onClose={() => setIsCommingSoonModalOpen(false)}
      />
    </div>
  );
}
