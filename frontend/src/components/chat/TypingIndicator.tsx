import { getSafeAvatarUrl } from '@/utils/avatarUrlGuard';

interface TypingIndicatorProps {
  characterName?: string;
  characterAvatar?: string;
}

export function TypingIndicator({ characterName, characterAvatar }: TypingIndicatorProps) {
  const safeCharacterAvatar = getSafeAvatarUrl(characterAvatar);

  return (
    <div className="flex gap-3 mb-4">
      {/* Avatar */}
      {safeCharacterAvatar ? (
        <div className="flex-shrink-0 w-10 h-10 rounded-full overflow-hidden border border-primary-500/30">
          <img src={safeCharacterAvatar} alt={characterName || 'AI'} className="w-full h-full object-cover" />
        </div>
      ) : (
        <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm bg-white/10 text-primary-400 border border-primary-500/30">
          {characterName?.charAt(0) || 'AI'}
        </div>
      )}

      {/* Typing Animation */}
      <div className="glass-effect px-4 py-3 rounded-2xl rounded-tl-sm">
        <div className="flex gap-1.5">
          <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
          <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
          <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce"></div>
        </div>
      </div>
    </div>
  );
}
