import type { Message } from '@/types/chat';
import { cn } from '@/utils/cn';
import { format } from 'date-fns';
import { getSafeAvatarUrl } from '@/utils/avatarUrlGuard';

interface GroupMessageBubbleProps {
  message: Message;
  characterAvatars: Record<string, string>;
  characterNames: Record<string, string>;
}

export function GroupMessageBubble({
  message,
  characterAvatars,
  characterNames,
}: GroupMessageBubbleProps) {
  const isUser = message.role === 'user';
  const speakerId = message.speaker_id || message.character_id;
  const speakerName = message.speaker_name || characterNames[speakerId || ''] || 'AI';
  const speakerAvatar = characterAvatars[speakerId || ''];
  const safeAvatar = getSafeAvatarUrl(speakerAvatar);

  const speakerColors: Record<string, string> = {
    default: 'bg-purple-500',
  };

  const speakerColor = speakerColors[speakerId || ''] || speakerColors.default;

  return (
    <div
      className={cn(
        'flex gap-3 mb-4 animate-in slide-in-from-bottom-2',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {!isUser && (
        <div className="flex-shrink-0">
          {safeAvatar ? (
            <div className={cn('w-10 h-10 rounded-full overflow-hidden border-2', speakerColor)}>
              <img src={safeAvatar} alt={speakerName} className="w-full h-full object-cover" />
            </div>
          ) : (
            <div
              className={cn(
                'w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm text-white',
                speakerColor
              )}
            >
              {speakerName.charAt(0)}
            </div>
          )}
        </div>
      )}

      <div className={cn('flex-1 max-w-[80%]', isUser && 'flex flex-col items-end')}>
        {!isUser && speakerId && (
          <span className={cn('text-xs font-medium mb-1 px-1', 'text-purple-400')}>
            {speakerName}
          </span>
        )}

        <div
          className={cn(
            'px-4 py-3 rounded-2xl',
            isUser
              ? 'bg-gradient-primary text-white rounded-tr-sm'
              : 'glass-effect text-white rounded-tl-sm'
          )}
        >
          <div className="prose prose-invert prose-sm max-w-none break-words [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
            {message.content}
          </div>
        </div>

        <span className="text-xs text-zinc-500 mt-1 px-1">
          {(() => {
            try {
              const dateStr = message.timestamp || (message as any).created_at;
              if (!dateStr) return '';
              return format(new Date(dateStr), 'HH:mm');
            } catch {
              return '';
            }
          })()}
        </span>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-primary flex items-center justify-center font-semibold text-sm text-white">
          You
        </div>
      )}
    </div>
  );
}
