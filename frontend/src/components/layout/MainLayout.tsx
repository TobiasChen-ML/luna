import { Header } from './Header';
import { Footer } from './Footer';
import { BottomNavBar } from './BottomNavBar';
import { useAuth } from '@/contexts/AuthContext';

interface MainLayoutProps {
  children: React.ReactNode;
  showHeader?: boolean;
  showFooter?: boolean;
  showBottomNav?: boolean;
}

export function MainLayout({
  children,
  showHeader = true,
  showFooter = true,
  showBottomNav = true
}: MainLayoutProps) {
  const { user } = useAuth();
  
  // When logged in users see bottom nav on mobile, add extra bottom padding
  const hasBottomNav = showBottomNav && user;

  return (
    <div className="min-h-screen flex flex-col">
      {showHeader && <Header />}
      <main
        className={`flex-1 ${showHeader ? '' : 'pt-0'}`}
        style={{
          paddingTop: showHeader ? 'calc(4rem + var(--app-safe-area-top))' : undefined,
          paddingBottom: hasBottomNav
            ? 'calc(4rem + var(--app-safe-area-bottom))'
            : undefined
        }}
      >
        {children}
      </main>
      {/* Show Footer on desktop, show BottomNavBar on mobile after login */}
      {showFooter && <div className="hidden md:block"><Footer /></div>}
      {showBottomNav && <BottomNavBar />}
    </div>
  );
}
