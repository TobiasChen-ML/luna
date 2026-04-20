import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate, useParams } from 'react-router-dom';
import { useGuestContext } from '@/contexts/GuestContext';
import type { GuestMessage } from '@/contexts/GuestContext';
import { useAuth } from '@/contexts/AuthContext';
import { ChatInput } from '@/components/chat';
import { Button, RegistrationPromptModal } from '@/components/common';
import { Home, Coins, Sparkles, AlertCircle, Loader2, Volume2, VolumeX } from 'lucide-react';
import { cn } from '@/utils/cn';
import { getSafeAvatarUrl } from '@/utils/avatarUrlGuard';
import { openExternalUrl } from '@/utils/externalLink';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

interface OfficialCharacter {
  id: string;
  name: string;
  first_name?: string;
  profile_image_url?: string;
  images?: string[];
  personality_tags?: string[];
}

function GuestMessageBubble({ message, characterName, characterAvatar, characterId }: { message: GuestMessage; characterName: string; characterAvatar?: string; characterId: string }) {
  const isUser = message.role === 'user';
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [cachedAudioUrl, setCachedAudioUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const safeCharacterAvatar = getSafeAvatarUrl(characterAvatar);

  const handleAudioToggle = async () => {
    // If currently playing, stop it
    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      return;
    }

    // Stop any currently playing audio
    document.querySelectorAll('audio').forEach(audio => {
      audio.pause();
      audio.currentTime = 0;
    });

    // If we already have audio cached, play it
    if (cachedAudioUrl) {
      const audio = new Audio(cachedAudioUrl);
      audioRef.current = audio;
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => setIsPlaying(false);
      audio.play();
      setIsPlaying(true);
      return;
    }

    // Generate audio on-demand
    setIsLoadingAudio(true);
    try {
      const response = await axios.post(`${API_BASE}/chat/guest/audio/generate`, {
        text: message.content,
        character_id: characterId,
      });

      if (response.data.audio_url) {
        setCachedAudioUrl(response.data.audio_url);
        const audio = new Audio(response.data.audio_url);
        audioRef.current = audio;
        audio.onended = () => setIsPlaying(false);
        audio.onerror = () => setIsPlaying(false);
        audio.play();
        setIsPlaying(true);
      }
    } catch (error) {
      console.error('Failed to generate audio:', error);
    } finally {
      setIsLoadingAudio(false);
    }
  };

  return (
    <div
      className={cn(
        'flex gap-3 mb-4 animate-in slide-in-from-bottom-2',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      {!isUser && safeCharacterAvatar ? (
        <div className="flex-shrink-0 w-10 h-10 rounded-full overflow-hidden border border-pink-500/30">
          <img src={safeCharacterAvatar} alt={characterName || 'AI'} className="w-full h-full object-cover" />
        </div>
      ) : (
        <div
          className={cn(
            'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm',
            isUser
              ? 'bg-gradient-to-br from-pink-500 to-purple-600 text-white'
              : 'bg-white/10 text-pink-400 border border-pink-500/30'
          )}
        >
          {isUser ? 'You' : characterName?.charAt(0) || 'AI'}
        </div>
      )}

      {/* Message Content */}
      <div className={cn('flex-1 max-w-[85%]', isUser && 'flex flex-col items-end')}>
        <div
          className={cn(
            'px-4 py-3 rounded-2xl',
            isUser
              ? 'bg-gradient-to-br from-pink-500 to-purple-600 text-white rounded-tr-sm'
              : 'bg-white/5 border border-white/10 text-white rounded-tl-sm'
          )}
        >
          <div className="prose prose-invert prose-sm max-w-none break-words [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Image if present */}
          {message.image_url && (
            <div className="mt-3">
              <img
                src={message.image_url}
                alt="Character photo"
                className="rounded-lg max-w-full max-h-64 object-contain cursor-pointer hover:opacity-90 transition-opacity"
                onClick={() => openExternalUrl(message.image_url!)}
              />
            </div>
          )}

          {/* Video if present */}
          {message.video_url && (
            <div className="mt-3">
              <video
                src={message.video_url}
                controls
                className="rounded-lg max-w-full max-h-64"
                preload="metadata"
              />
            </div>
          )}
        </div>

        {/* Audio play button for assistant messages - generates on first click */}
        {!isUser && (
          <button
            onClick={handleAudioToggle}
            disabled={isLoadingAudio}
            className={cn(
              'mt-2 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs transition-all',
              isPlaying
                ? 'bg-pink-500/20 text-pink-400 border border-pink-500/30'
                : isLoadingAudio
                  ? 'bg-white/5 text-zinc-500 border border-white/10 cursor-wait'
                  : 'bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 border border-white/10'
            )}
          >
            {isLoadingAudio ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                <span>Loading...</span>
              </>
            ) : isPlaying ? (
              <>
                <VolumeX size={14} />
                <span>Stop</span>
              </>
            ) : (
              <>
                <Volume2 size={14} />
                <span>Play</span>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

function TypingIndicator({ characterName, characterAvatar }: { characterName: string; characterAvatar?: string }) {
  const safeCharacterAvatar = getSafeAvatarUrl(characterAvatar);

  return (
    <div className="flex gap-3 mb-4">
      {safeCharacterAvatar ? (
        <div className="flex-shrink-0 w-10 h-10 rounded-full overflow-hidden border border-pink-500/30">
          <img src={safeCharacterAvatar} alt={characterName || 'AI'} className="w-full h-full object-cover" />
        </div>
      ) : (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-white/10 text-pink-400 border border-pink-500/30 flex items-center justify-center font-semibold text-sm">
          {characterName?.charAt(0) || 'AI'}
        </div>
      )}
      <div className="bg-white/5 border border-white/10 rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex gap-1">
          <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}

export function GuestChatPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAuthenticated } = useAuth();
  const {
    guestCredits,
    isCreditsExhausted,
    guestMessages,
    sendGuestMessage,
    isSending,
    setIsGuestMode,
  } = useGuestContext();

  const isTyping = isSending; // Alias for typing indicator

  const [character, setCharacter] = useState<OfficialCharacter | null>(null);
  const [loadingCharacter, setLoadingCharacter] = useState(true);
  const [error, setError] = useState('');
  const [showRegistrationModal, setShowRegistrationModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { slug } = useParams<{ slug?: string }>();
  const [slugResolvedId, setSlugResolvedId] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    axios
      .get(`${API_BASE}/characters/by-slug/${slug}`)
      .then((r) => setSlugResolvedId(r.data.id))
      .catch(() => setSlugResolvedId(null));
  }, [slug]);

  const characterId = slug ? slugResolvedId : searchParams.get('character');

  // Redirect authenticated users to regular chat
  useEffect(() => {
    if (!isAuthenticated) return;
    if (slug) {
      // Already on slug route — re-render as authenticated ChatPage
      navigate(window.location.pathname, { replace: true });
    } else if (characterId) {
      navigate(`/chat?character=${characterId}`, { replace: true });
    }
  }, [isAuthenticated, slug, characterId, navigate]);

  // Enable guest mode
  useEffect(() => {
    setIsGuestMode(true);
    return () => setIsGuestMode(false);
  }, [setIsGuestMode]);

  // Load official character
  useEffect(() => {
    const loadCharacter = async () => {
      if (!characterId) {
        setError('No character specified');
        setLoadingCharacter(false);
        return;
      }

      try {
        const response = await axios.get(`${API_BASE}/characters/official/${characterId}`);
        setCharacter(response.data);
      } catch (err) {
        console.error('Failed to load character:', err);
        setError('Failed to load character');
      } finally {
        setLoadingCharacter(false);
      }
    };

    loadCharacter();
  }, [characterId]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [guestMessages]);

  // Show registration modal when credits exhausted
  useEffect(() => {
    if (isCreditsExhausted) {
      setShowRegistrationModal(true);
    }
  }, [isCreditsExhausted]);

  const handleSendMessage = async (content: string) => {
    if (!characterId || !content.trim()) return;

    if (isCreditsExhausted) {
      setShowRegistrationModal(true);
      return;
    }

    await sendGuestMessage(characterId, content.trim());
  };

  const characterName = character?.first_name || character?.name || 'AI';
  const characterImage = getSafeAvatarUrl(character?.images?.[0] || character?.profile_image_url);
  const chatBackdrop = characterImage;

  if (loadingCharacter) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-zinc-950">
        <div className="text-center space-y-4">
          <Loader2 className="w-16 h-16 text-pink-500 animate-spin mx-auto" />
          <p className="text-zinc-400">Loading character...</p>
        </div>
      </div>
    );
  }

  if (error || !character) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-zinc-950">
        <div className="text-center space-y-4">
          <AlertCircle size={48} className="text-red-500 mx-auto" />
          <p className="text-red-400">{error || 'Character not found'}</p>
          <Button onClick={() => navigate('/')}>Go Home</Button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="relative flex h-full min-h-[100dvh] w-full flex-col overflow-hidden bg-zinc-950"
    >
      {chatBackdrop && (
        <>
          <div
            className="absolute inset-0 lg:hidden bg-cover bg-center bg-no-repeat opacity-50 pointer-events-none"
            style={{ backgroundImage: `url(${chatBackdrop})` }}
          />
          <div
            className="absolute inset-0 hidden lg:block bg-cover bg-center bg-no-repeat"
            style={{ backgroundImage: `url(${chatBackdrop})` }}
          />
          <div className="absolute inset-0 hidden lg:block bg-black/70 backdrop-blur-[1px]" />
        </>
      )}
      <div className="relative z-10 flex flex-col flex-1 min-h-0">
        {/* Top Bar */}
        <div className="bg-zinc-900/70 border-b border-white/10 px-4 py-3 flex items-center gap-4 flex-shrink-0 backdrop-blur-sm">
        <button
          onClick={() => navigate('/')}
          className="text-zinc-400 hover:text-white transition-colors"
          title="Back to Home"
        >
          <Home size={24} />
        </button>

        {/* Character Info */}
        <div className="flex items-center gap-3 flex-1">
          <div className="w-10 h-10 rounded-full overflow-hidden bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center text-white font-semibold">
            {characterImage ? (
              <img src={characterImage} alt={characterName} className="w-full h-full object-cover" />
            ) : (
              characterName.charAt(0)
            )}
          </div>
          <div>
            <h2 className="font-semibold text-white">{characterName}</h2>
            <p className="text-xs text-zinc-400">Guest Mode</p>
          </div>
        </div>

        {/* Guest Credits Display */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-yellow-500">
          <Coins size={16} />
          <span className="font-medium text-sm">{guestCredits}</span>
          <span className="text-xs text-yellow-400/70 hidden sm:inline">credits</span>
        </div>

        {/* Sign Up Button */}
        <Button
          variant="primary"
          size="sm"
          onClick={() => navigate('/register')}
          className="flex items-center gap-2"
        >
          <Sparkles size={16} />
          <span className="hidden sm:inline">Sign Up Free</span>
        </Button>
        </div>

        {/* Chat Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 min-h-0">
        {/* Welcome Message */}
        {guestMessages.length === 0 && (
          <div className="text-center py-8 space-y-4">
            <div className="w-24 h-24 mx-auto rounded-full overflow-hidden bg-gradient-to-br from-pink-500 to-purple-600">
              {characterImage ? (
                <img
                  src={characterImage}
                  alt={characterName}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-3xl font-bold text-white">
                  {characterName.charAt(0)}
                </div>
              )}
            </div>
            <h3 className="text-xl font-semibold text-white">
              Chat with {characterName}
            </h3>
            <p className="text-zinc-400 text-sm max-w-md mx-auto">
              You have <span className="text-yellow-400 font-medium">{guestCredits} free messages</span>.
              Sign up to save your chat history and unlock all features!
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {['Hey there!', 'Tell me about yourself', 'What do you like to do?'].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => handleSendMessage(suggestion)}
                  className="px-4 py-2 rounded-full bg-white/5 border border-white/10 text-zinc-300 text-sm hover:bg-white/10 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        {guestMessages.map((msg) => (
          <GuestMessageBubble
            key={msg.id}
            message={msg}
            characterName={characterName}
            characterAvatar={characterImage}
            characterId={characterId || ''}
          />
        ))}

        {/* Typing Indicator */}
        {isTyping && <TypingIndicator characterName={characterName} characterAvatar={characterImage} />}

        <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <ChatInput
          onSend={handleSendMessage}
          placeholder={isCreditsExhausted ? 'Sign up to continue chatting...' : `Message ${characterName}...`}
          disabled={isCreditsExhausted || isSending}
        />

        {/* Registration Modal */}
        <RegistrationPromptModal
          isOpen={showRegistrationModal}
          variant="credits_exhausted"
        />
      </div>
    </div>
  );
}
