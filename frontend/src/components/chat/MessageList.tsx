import { useEffect, useMemo, useRef } from 'react';
import type { Message } from '@/types/chat';
import { MessageBubble, InnerMonologueBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { useChatContext } from '@/contexts/ChatContext';
import { getSafeAvatarUrl } from '@/utils/avatarUrlGuard';

interface MessageListProps {
  messages: Message[];
  isTyping?: boolean;
  characterName?: string;
  characterAvatar?: string;
  sessionId?: string;
}

export function MessageList({ messages, isTyping, characterName, characterAvatar, sessionId }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const loadMoreTriggerRef = useRef<HTMLDivElement>(null);
  const prevScrollHeight = useRef<number>(0);
  const shouldAutoScroll = useRef<boolean>(true);

  const { loadMoreMessages, hasMoreMessages, isLoadingMore, totalMessageCount, thinkingContent, isThinking } = useChatContext();
  const safeCharacterAvatar = getSafeAvatarUrl(characterAvatar);

  const displayMessages = useMemo(() => {
    const expanded: Message[] = [];

    for (const msg of messages) {
      if (msg.role === 'assistant' && msg.isNDJSON && msg.segments && msg.segments.length > 0) {
        const lastIndex = msg.segments.length - 1;
        msg.segments.forEach((seg, idx) => {
          expanded.push({
            id: `${msg.id}::seg-${idx}`,
            role: 'assistant',
            content: msg.content,
            segments: [seg],
            isNDJSON: true,
            timestamp: msg.timestamp,
            character_id: msg.character_id,
            image_url: idx === lastIndex ? msg.image_url : undefined,
            video_url: idx === lastIndex ? msg.video_url : undefined,
            audio_url: idx === lastIndex ? msg.audio_url : undefined,
            metadata: {
              ...msg.metadata,
              virtual_ndjson_segment: true,
              virtual_ndjson_last_segment: idx === lastIndex,
              parent_message_id: msg.id,
              ndjson_segment_index: idx,
              ndjson_segment_type: seg.type,
            },
          });
        });
        continue;
      }

      expanded.push(msg);
    }

    return expanded;
  }, [messages]);

  // IntersectionObserver for loading more when scrolling to top
  useEffect(() => {
    if (!loadMoreTriggerRef.current || !hasMoreMessages) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !isLoadingMore) {
          loadMoreMessages();
        }
      },
      { threshold: 0.1, rootMargin: '100px' }
    );

    observer.observe(loadMoreTriggerRef.current);
    return () => observer.disconnect();
  }, [hasMoreMessages, isLoadingMore, loadMoreMessages]);

  // Preserve scroll position when prepending messages
  useEffect(() => {
    if (isLoadingMore && messagesContainerRef.current) {
      prevScrollHeight.current = messagesContainerRef.current.scrollHeight;
    }
  }, [isLoadingMore]);

  useEffect(() => {
    if (!isLoadingMore && prevScrollHeight.current > 0 && messagesContainerRef.current) {
      const newScrollHeight = messagesContainerRef.current.scrollHeight;
      const scrollDiff = newScrollHeight - prevScrollHeight.current;
      messagesContainerRef.current.scrollTop += scrollDiff;
      prevScrollHeight.current = 0;
    }
  }, [messages, isLoadingMore]);

  // Auto-scroll to bottom only when user is at bottom (not for history loads)
  const handleScroll = () => {
    if (!messagesContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
    shouldAutoScroll.current = isAtBottom;
  };

  useEffect(() => {
    if (shouldAutoScroll.current && !isLoadingMore) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [displayMessages.length, isTyping, isLoadingMore]);

  if (messages.length === 0 && !isTyping) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center space-y-4 max-w-md">
          <div className="w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center mx-auto">
            <span className="text-2xl">💬</span>
          </div>
          <h3 className="text-xl font-semibold text-white">Start a Conversation</h3>
          <p className="text-zinc-400">
            Send a message to begin chatting with {characterName || 'your AI companion'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={messagesContainerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto px-4 py-6 space-y-2 overscroll-contain"
      style={{ WebkitOverflowScrolling: 'touch' }}
    >
      {/* Load trigger at top */}
      {hasMoreMessages && (
        <div ref={loadMoreTriggerRef} className="py-2 text-center">
          {isLoadingMore ? (
            <LoadingSpinner text="Loading older messages..." />
          ) : (
            <button
              onClick={loadMoreMessages}
              className="text-sm text-zinc-400 hover:text-primary-400 transition-colors"
            >
              Load older messages ({totalMessageCount - messages.length} remaining)
            </button>
          )}
        </div>
      )}

      {!hasMoreMessages && messages.length > 0 && (
        <div className="py-2 text-center text-xs text-zinc-500">
          Start of conversation
        </div>
      )}

      {displayMessages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          characterName={characterName}
          characterAvatar={safeCharacterAvatar}
          sessionId={sessionId}
        />
      ))}

      {thinkingContent && (
        <InnerMonologueBubble
          content={thinkingContent}
          isStreaming={isThinking}
          characterAvatar={safeCharacterAvatar}
          characterName={characterName}
        />
      )}
      {isTyping && <TypingIndicator characterName={characterName} characterAvatar={safeCharacterAvatar} />}
      <div ref={messagesEndRef} />
    </div>
  );
}
