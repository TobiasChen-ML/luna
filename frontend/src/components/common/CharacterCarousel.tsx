import { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle, Loader2 } from 'lucide-react';
import { Button } from './Button';
import { CharacterImage } from './CharacterImage';
import { useAuth } from '../../contexts/AuthContext';
import { toChatUrl } from '@/utils/chatUrl';
import { startOfficialChat } from '@/utils/startOfficialChat';

export interface Character {
  id?: string;
  name: string;
  age: number;
  trait: string;
  image: string;
  desc?: string;
  storyTitle?: string;
  storyDescription?: string;
  version?: string;
}

interface CharacterCarouselProps {
  characters: Character[];
}

const CARD_WIDTH = 260; // Base width
const GAP = 32; // Increased gap to accommodate scaling
const TRANSITION_DURATION = 500; // ms

export function CharacterCarousel({ characters }: CharacterCarouselProps) {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const totalItems = characters.length;
  // Create 3 sets for infinite scrolling
  const extendedCharacters = [...characters, ...characters, ...characters];
  // Start at the beginning of the middle set
  const initialIndex = totalItems;

  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [isTransitioning, setIsTransitioning] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleNext = useCallback(() => {
    setCurrentIndex(prev => prev + 1);
    setIsTransitioning(true);
  }, []);

  // Auto scroll
  useEffect(() => {
    if (isPaused) return;

    const interval = setInterval(() => {
      handleNext();
    }, 3000);

    return () => clearInterval(interval);
  }, [isPaused, handleNext]);

  // Handle seamless loop reset
  useEffect(() => {
    if (currentIndex >= totalItems * 2) {
      // Reset to middle set corresponding index
      timeoutRef.current = setTimeout(() => {
        setIsTransitioning(false);
        setCurrentIndex(totalItems);
      }, TRANSITION_DURATION);
    } else if (currentIndex < totalItems) {
      // Reset to middle set corresponding index (from left side)
      timeoutRef.current = setTimeout(() => {
        setIsTransitioning(false);
        setCurrentIndex(totalItems * 2 - 1);
      }, TRANSITION_DURATION);
    }

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [currentIndex, totalItems]);

  // Re-enable transition after reset
  useEffect(() => {
    if (!isTransitioning) {
      // Force reflow/repaint before enabling transition again
      const timer = setTimeout(() => {
        setIsTransitioning(true);
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isTransitioning]);

  const handleCardClick = (index: number) => {
    if (index !== currentIndex) {
      setCurrentIndex(index);
      setIsTransitioning(true);
    }
  };

  const handleChatNow = async (e: React.MouseEvent, char: Character) => {
    e.stopPropagation();

    if (!char.id) {
      // If authenticated, go to chat, otherwise go to register
      navigate(isAuthenticated ? '/chat' : '/register');
      return;
    }

    // Guest mode: Navigate directly to guest chat
    if (!isAuthenticated) {
      if (!char.id) return;
      navigate(`${toChatUrl({ ...char, id: char.id })}?mode=guest`);
      return;
    }

    // Authenticated: Copy official character and navigate
    try {
      setLoadingId(char.id);
      await startOfficialChat(navigate, {
        isAuthenticated,
        characterId: char.id,
      });
    } catch (error) {
      console.error('Failed to start chat:', error);
      // Show error to user instead of silently failing
      // Don't navigate to chat with official character ID - it will cause permission errors
      alert('Failed to start chat. Please try again.');
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div 
      className="relative w-full py-12 overflow-hidden"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      {/* Gradient Overlays for fade effect */}
      <div className="absolute left-0 top-0 bottom-0 w-12 md:w-32 z-10 bg-gradient-to-r from-black via-black/50 to-transparent pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-12 md:w-32 z-10 bg-gradient-to-l from-black via-black/50 to-transparent pointer-events-none" />

      <div 
        className="flex items-center"
        style={{
          // Calculate position to center the current item
          // 50vw - (half card) - (currentIndex * (card + gap))
          transform: `translateX(calc(50% - ${CARD_WIDTH / 2}px - ${currentIndex * (CARD_WIDTH + GAP)}px))`,
          transition: isTransitioning ? `transform ${TRANSITION_DURATION}ms cubic-bezier(0.4, 0, 0.2, 1)` : 'none',
          gap: `${GAP}px`
        }}
      >
        {extendedCharacters.map((char, idx) => {
          const isActive = idx === currentIndex;
          const distance = Math.abs(idx - currentIndex);
          // Only render if within reasonable range to improve performance? 
          // For 45 items (15*3), it's fine to render all.
          
          return (
            <div
              key={`${char.name}-${idx}`}
              onClick={() => handleCardClick(idx)}
              className={`
                group relative flex-shrink-0 rounded-xl overflow-hidden cursor-pointer transition-all duration-500 ease-out
                ${isActive ? 'z-20 border-2 border-primary-500/50 shadow-[0_0_30px_-5px_rgba(236,72,153,0.5)]' : 'z-10 brightness-50 hover:brightness-75'}
              `}
              style={{
                width: `${CARD_WIDTH}px`,
                transform: isActive ? 'scale(1.2)' : 'scale(0.8)',
                opacity: distance > 3 ? 0 : 1, // Hide distant items for better performance/clean look
                pointerEvents: distance > 2 ? 'none' : 'auto'
              }}
            >
              <div className="aspect-[3/4] w-full relative">
                <CharacterImage
                  characterName={char.name}
                  imageSrc={char.image}
                  className="w-full h-full object-cover"
                />
                
                <div className={`absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent transition-opacity duration-300 p-4
                  ${isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}
                `}>
                  <div className="absolute top-4 left-4 right-4">
                    <h3 className="text-lg font-heading font-bold text-white">
                      {char.name}
                    </h3>
                    <p className="mt-1 text-xs text-zinc-100/90 line-clamp-3 leading-relaxed transition-opacity duration-200 group-hover:opacity-0">
                      {char.desc || 'Mysterious background waiting to be discovered.'}
                    </p>
                    <div className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
                      {char.storyTitle && (
                        <p className="text-[11px] uppercase tracking-wide text-primary-300/90">
                          {char.storyTitle}
                        </p>
                      )}
                      <p className="mt-1 text-xs text-zinc-100 line-clamp-4 leading-relaxed">
                        {char.storyDescription || 'No opening script available yet.'}
                      </p>
                    </div>
                  </div>

                  <div className="absolute bottom-4 left-4 right-4 flex items-center justify-end text-xs text-zinc-400">
                    <Button
                      variant="secondary"
                      className="h-8 px-3 flex items-center gap-2 bg-white/10 hover:bg-white/20 border-white/20 backdrop-blur-sm text-xs"
                      onClick={(e) => handleChatNow(e, char)}
                      disabled={loadingId === char.id}
                    >
                      {loadingId === char.id ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <MessageCircle size={14} />
                      )}
                      Chat Now
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
