import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Home, MessageSquare, Users, User } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useTelegram } from '@/contexts/TelegramContext';
import { cn } from '@/utils/cn';

interface NavItem {
  icon: React.ElementType;
  labelKey: string;
  path: string;
}

const navItems: NavItem[] = [
  { icon: Home, labelKey: 'home', path: '/' },
  { icon: MessageSquare, labelKey: 'chat', path: '/chat' },
  { icon: Users, labelKey: 'characters', path: '/characters' },
  { icon: User, labelKey: 'profile', path: '/profile' },
];

const HIDDEN_ON_PATHS = ['/chat'];

export function BottomNavBar() {
  const { t } = useTranslation('navigation');
  const location = useLocation();
  const { user } = useAuth();
  const { webApp } = useTelegram();

  const tmaBottomInset = webApp?.contentSafeAreaInset?.bottom ?? 0;
  const bottomPadding = tmaBottomInset > 0
    ? `${tmaBottomInset}px`
    : 'var(--app-safe-area-bottom)';

  if (!user) return null;

  const shouldHide = HIDDEN_ON_PATHS.some(path => location.pathname.startsWith(path));
  if (shouldHide) return null;

  return (
    <nav 
      className="fixed bottom-0 left-0 right-0 z-50 md:hidden glass-effect border-t border-white/10"
      style={{ paddingBottom: bottomPadding }}
    >
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path || 
            (item.path !== '/' && location.pathname.startsWith(item.path));
          const Icon = item.icon;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex flex-col items-center justify-center flex-1 h-full py-2 transition-all duration-200',
                isActive 
                  ? 'text-primary-500' 
                  : 'text-zinc-400 active:text-zinc-200'
              )}
            >
              <div className="relative">
                <Icon 
                  size={22} 
                  className={cn(
                    'transition-transform duration-200',
                    isActive && 'scale-110'
                  )} 
                />
                {isActive && (
                  <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-primary-500 rounded-full" />
                )}
              </div>
              <span className={cn(
                'text-[10px] mt-1 font-medium transition-opacity duration-200',
                isActive ? 'opacity-100' : 'opacity-70'
              )}>
                {t(item.labelKey)}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
