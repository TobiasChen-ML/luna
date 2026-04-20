import { useMemo } from 'react';
import { X, Smartphone, Share2, Plus, Monitor, Download } from 'lucide-react';
import { detectPlatform, Platform, isPWA } from '@/utils/pwa';
import { isTelegramMiniApp } from '@/utils/telegram';

interface PWAInstallModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PWAInstallModal({ isOpen, onClose }: PWAInstallModalProps) {
  const platform = useMemo(() => detectPlatform(), []);

  if (!isOpen) return null;
  if (isTelegramMiniApp()) return null;
  if (isPWA()) return null;

  const handleClose = () => {
    localStorage.setItem('pwa-modal-dismissed', Date.now().toString());
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={handleClose}
      />
      
      <div className="relative bg-gradient-to-b from-zinc-900 to-zinc-950 rounded-2xl shadow-2xl max-w-md w-full max-h-[85vh] overflow-hidden animate-modal-in">
        <div className="sticky top-0 bg-gradient-to-b from-zinc-900 to-zinc-900/95 backdrop-blur-sm z-10 px-6 py-4 border-b border-zinc-800">
          <h2 className="text-xl font-bold text-white text-center">
            Install RoxyClub
          </h2>
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 text-zinc-400 hover:text-white transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto">
          <PlatformInstructions platform={platform} />
        </div>

        <div className="sticky bottom-0 bg-gradient-to-t from-zinc-950 to-transparent p-4">
          <button
            onClick={handleClose}
            className="w-full py-3 rounded-xl bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition-colors text-sm"
          >
            Maybe Later
          </button>
        </div>
      </div>
    </div>
  );
}

function PlatformInstructions({ platform }: { platform: Platform }) {
  switch (platform) {
    case 'ios':
      return <IOSInstructions />;
    case 'android':
      return <AndroidInstructions />;
    case 'desktop-chrome':
    case 'desktop-edge':
      return <DesktopInstructions platform={platform} />;
    default:
      return <GenericInstructions />;
  }
}

function IOSInstructions() {
  return (
    <div className="space-y-6">
      <div className="text-center mb-4">
        <div className="w-16 h-16 mx-auto bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mb-3">
          <Smartphone className="w-8 h-8 text-white" />
        </div>
        <p className="text-zinc-400 text-sm">
          Add RoxyClub to your iPhone home screen
        </p>
      </div>

      <div className="space-y-4">
        <StepCard
          number={1}
          title="Tap the Share button"
          description="Look for the share icon at the bottom of your screen"
          icon={<Share2 className="w-5 h-5 text-blue-400" />}
          highlight="Bottom of screen"
        />
        
        <StepCard
          number={2}
          title="Scroll down"
          description="Find 'Add to Home Screen' in the options list"
          icon={<Plus className="w-5 h-5 text-green-400" />}
          highlight="In share menu"
        />
        
        <StepCard
          number={3}
          title="Tap 'Add to Home Screen'"
          description="RoxyClub will appear on your home screen like a native app"
          icon={<Smartphone className="w-5 h-5 text-purple-400" />}
          highlight="Confirm to add"
        />
      </div>

      <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-4 mt-4">
        <p className="text-purple-300 text-sm text-center">
          Once installed, you can access RoxyClub anytime from your home screen!
        </p>
      </div>
    </div>
  );
}

function AndroidInstructions() {
  return (
    <div className="space-y-6">
      <div className="text-center mb-4">
        <div className="w-16 h-16 mx-auto bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mb-3">
          <Smartphone className="w-8 h-8 text-white" />
        </div>
        <p className="text-zinc-400 text-sm">
          Install RoxyClub on your Android device
        </p>
      </div>

      <div className="space-y-4">
        <StepCard
          number={1}
          title="Tap the menu button"
          description="Tap the three dots menu in the top right corner"
          icon={<Monitor className="w-5 h-5 text-zinc-400" />}
          highlight="Top right corner"
        />
        
        <StepCard
          number={2}
          title="Select 'Install app'"
          description="Or 'Add to Home screen' from the menu"
          icon={<Download className="w-5 h-5 text-green-400" />}
          highlight="In menu options"
        />
        
        <StepCard
          number={3}
          title="Confirm installation"
          description="Tap 'Install' to add RoxyClub to your home screen"
          icon={<Smartphone className="w-5 h-5 text-purple-400" />}
          highlight="Tap to confirm"
        />
      </div>

      <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4 mt-4">
        <p className="text-green-300 text-sm text-center">
          Your browser may also show an automatic install banner at the bottom of the screen.
        </p>
      </div>
    </div>
  );
}

function DesktopInstructions({ platform }: { platform: Platform }) {
  const browserName = platform === 'desktop-chrome' ? 'Chrome' : 'Edge';
  
  return (
    <div className="space-y-6">
      <div className="text-center mb-4">
        <div className="w-16 h-16 mx-auto bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mb-3">
          <Monitor className="w-8 h-8 text-white" />
        </div>
        <p className="text-zinc-400 text-sm">
          Install RoxyClub on {browserName}
        </p>
      </div>

      <div className="space-y-4">
        <StepCard
          number={1}
          title="Look for the install icon"
          description={`Click the install icon in the address bar (right side)`}
          icon={<Download className="w-5 h-5 text-blue-400" />}
          highlight="Address bar"
        />
        
        <StepCard
          number={2}
          title="Or use the menu"
          description={`Click ${platform === 'desktop-chrome' ? '⋮' : '⋯'} menu → 'Save as app' or 'Install'`}
          icon={<Monitor className="w-5 h-5 text-zinc-400" />}
          highlight="Top right menu"
        />
        
        <StepCard
          number={3}
          title="Confirm installation"
          description="RoxyClub will be added as a standalone app"
          icon={<Smartphone className="w-5 h-5 text-purple-400" />}
          highlight="Click 'Install'"
        />
      </div>

      <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 mt-4">
        <p className="text-blue-300 text-sm text-center">
          The app will open in its own window with a native desktop experience.
        </p>
      </div>
    </div>
  );
}

function GenericInstructions() {
  return (
    <div className="space-y-6">
      <div className="text-center mb-4">
        <div className="w-16 h-16 mx-auto bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mb-3">
          <Download className="w-8 h-8 text-white" />
        </div>
        <p className="text-zinc-400 text-sm">
          Install RoxyClub for the best experience
        </p>
      </div>

      <div className="space-y-4">
        <StepCard
          number={1}
          title="Check your browser menu"
          description="Look for 'Install' or 'Add to Home Screen' option"
          icon={<Monitor className="w-5 h-5 text-zinc-400" />}
        />
        
        <StepCard
          number={2}
          title="Enable installation"
          description="Allow the browser to install the app"
          icon={<Download className="w-5 h-5 text-green-400" />}
        />
        
        <StepCard
          number={3}
          title="Enjoy the app"
          description="Access RoxyClub from your home screen or apps menu"
          icon={<Smartphone className="w-5 h-5 text-purple-400" />}
        />
      </div>

      <div className="bg-zinc-800/50 border border-zinc-700 rounded-xl p-4 mt-4">
        <p className="text-zinc-400 text-sm text-center">
          For the best experience, use Chrome, Edge, or Safari on your device.
        </p>
      </div>
    </div>
  );
}

function StepCard({ 
  number, 
  title, 
  description, 
  icon,
  highlight 
}: { 
  number: number;
  title: string;
  description: string;
  icon: React.ReactNode;
  highlight?: string;
}) {
  return (
    <div className="flex gap-4 items-start p-4 bg-zinc-800/50 rounded-xl border border-zinc-700/50">
      <div className="flex-shrink-0 w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-400 font-bold text-sm">
        {number}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          {icon}
          <h3 className="font-medium text-white">{title}</h3>
        </div>
        <p className="text-sm text-zinc-400 mb-2">{description}</p>
        {highlight && (
          <span className="inline-block px-2 py-0.5 bg-zinc-700/50 rounded text-xs text-zinc-500">
            {highlight}
          </span>
        )}
      </div>
    </div>
  );
}

const styles = `
@keyframes modal-in {
  from {
    transform: scale(0.95) translateY(20px);
    opacity: 0;
  }
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

.animate-modal-in {
  animation: modal-in 0.3s ease-out;
}
`;

if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = styles;
  document.head.appendChild(styleSheet);
}
