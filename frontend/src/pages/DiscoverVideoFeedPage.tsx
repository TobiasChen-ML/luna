import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInfiniteQuery } from '@tanstack/react-query';
import { Heart, Loader2, LogIn, MessageCircle, Share2, UserPlus } from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';
import { cn } from '@/utils/cn';
import { startOfficialChat } from '@/utils/startOfficialChat';
import type { TopCategory } from '@/types';

interface DiscoverCharacter {
  id: string;
  name?: string;
  first_name?: string;
  age?: number | string;
  avatar_url?: string;
  profile_image_url?: string;
  mature_image_url?: string;
  mature_cover_url?: string;
  mature_video_url?: string;
  preview_video_url?: string | null;
  personality_summary?: string;
  tags?: string[];
  top_category?: TopCategory;
}

const PAGE_SIZE = 24;
const GUEST_BROWSE_LIMIT = 12;

function getName(char: DiscoverCharacter) {
  return char.first_name || char.name || 'Character';
}

function getDisplayMedia(char: DiscoverCharacter) {
  const poster = char.mature_cover_url || char.mature_image_url || char.avatar_url || char.profile_image_url;
  const video = char.mature_video_url || char.preview_video_url || '';
  return { poster, video };
}

function pseudoCount(seed: string, base: number, mod: number) {
  let value = 0;
  for (let i = 0; i < seed.length; i += 1) value = (value * 31 + seed.charCodeAt(i)) % 100000;
  return base + (value % mod);
}

export function DiscoverVideoFeedPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [activeCategory, setActiveCategory] = useState<TopCategory>('girls');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [likedIds, setLikedIds] = useState<Record<string, boolean>>({});
  const [showComments, setShowComments] = useState(false);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const sectionRefs = useRef<(HTMLElement | null)[]>([]);

  const {
    data,
    hasNextPage,
    isFetching,
    isFetchingNextPage,
    fetchNextPage,
  } = useInfiniteQuery<DiscoverCharacter[]>({
    queryKey: ['discover-video-feed', activeCategory],
    queryFn: async ({ pageParam }) => {
      const offset = typeof pageParam === 'number' ? pageParam : 0;
      const params = new URLSearchParams({
        top_category: activeCategory,
        limit: String(PAGE_SIZE),
        offset: String(offset),
        personalized: 'true',
      });
      const response = await api.get<DiscoverCharacter[]>(`/characters/discover?${params.toString()}`);
      return Array.isArray(response.data) ? response.data : [];
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      if (!Array.isArray(lastPage) || lastPage.length < PAGE_SIZE) return undefined;
      return allPages.length * PAGE_SIZE;
    },
    staleTime: 60 * 1000,
  });

  const allCharacters = useMemo(() => (data?.pages ?? []).flat(), [data]);
  const visibleCharacters = useMemo(
    () => (isAuthenticated ? allCharacters : allCharacters.slice(0, GUEST_BROWSE_LIMIT)),
    [allCharacters, isAuthenticated]
  );
  const currentCharacter = visibleCharacters[currentIndex] ?? null;

  useEffect(() => {
    if (!isAuthenticated) return;
    if (!hasNextPage) return;
    if (currentIndex < Math.max(0, visibleCharacters.length - 3)) return;
    fetchNextPage().catch(() => {});
  }, [currentIndex, fetchNextPage, hasNextPage, isAuthenticated, visibleCharacters.length]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (!entry) return;
        const index = Number((entry.target as HTMLElement).dataset.index ?? 0);
        if (!Number.isNaN(index)) setCurrentIndex(index);
      },
      { root: container, threshold: [0.6] }
    );

    sectionRefs.current.forEach((el) => {
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [visibleCharacters.length]);

  const handlePlayWithMe = useCallback(async (char: DiscoverCharacter) => {
    try {
      await startOfficialChat(navigate, {
        isAuthenticated,
        characterId: char.id,
      });
    } catch (error) {
      console.error('Failed to start official chat from discover feed:', error);
    }
  }, [isAuthenticated, navigate]);

  const handleShare = useCallback(async (char: DiscoverCharacter) => {
    const shareUrl = `${window.location.origin}/discover/profile/${char.id}`;
    const title = `${getName(char)} on RoxyClub`;
    try {
      if (navigator.share) {
        await navigator.share({ title, url: shareUrl });
      } else if (navigator.clipboard) {
        await navigator.clipboard.writeText(shareUrl);
      }
    } catch {
      // user canceled or not permitted
    }
  }, []);

  return (
    <div className="h-[100dvh] bg-black text-white">
      <div className="fixed top-0 left-0 right-0 z-30 px-4 pt-[calc(var(--app-safe-area-top)+10px)] pb-3 bg-gradient-to-b from-black/85 to-transparent">
        <div className="mx-auto max-w-xl">
          <div className="inline-flex items-center rounded-full bg-white/10 border border-white/15 p-1">
            {(['girls', 'anime', 'guys'] as const).map((cat) => (
              <button
                key={cat}
                type="button"
                className={cn(
                  'px-4 py-1.5 rounded-full text-sm capitalize transition-colors',
                  activeCategory === cat ? 'bg-white text-black font-semibold' : 'text-zinc-200 hover:text-white'
                )}
                onClick={() => {
                  setActiveCategory(cat);
                  setCurrentIndex(0);
                  setLikedIds({});
                }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div ref={containerRef} className="h-full overflow-y-auto snap-y snap-mandatory">
        {visibleCharacters.map((char, index) => {
          const { poster, video } = getDisplayMedia(char);
          const liked = Boolean(likedIds[char.id]);
          const likes = pseudoCount(char.id, 1200, 50000) + (liked ? 1 : 0);
          const comments = pseudoCount(`${char.id}-comment`, 80, 3000);
          const shares = pseudoCount(`${char.id}-share`, 40, 1500);

          return (
            <section
              key={char.id}
              ref={(el) => { sectionRefs.current[index] = el; }}
              data-index={index}
              className="relative h-[100dvh] snap-start"
            >
              {video ? (
                <video
                  src={video}
                  className="absolute inset-0 h-full w-full object-cover"
                  autoPlay
                  loop
                  muted
                  playsInline
                />
              ) : poster ? (
                <img src={poster} alt={getName(char)} className="absolute inset-0 h-full w-full object-cover" />
              ) : (
                <div className="absolute inset-0 bg-gradient-to-br from-zinc-900 to-zinc-700" />
              )}

              <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/20 to-transparent" />

              <div className="absolute right-4 bottom-[calc(var(--app-safe-area-bottom)+90px)] z-20 flex flex-col items-center gap-5">
                <button
                  type="button"
                  className="flex flex-col items-center text-white"
                  onClick={() => navigate(`/discover/profile/${char.id}`)}
                >
                  <img
                    src={char.avatar_url || char.profile_image_url || poster || ''}
                    alt={getName(char)}
                    className="w-12 h-12 rounded-full border-2 border-white/70 object-cover"
                  />
                </button>
                <button
                  type="button"
                  className="flex flex-col items-center"
                  onClick={() => setLikedIds((prev) => ({ ...prev, [char.id]: !prev[char.id] }))}
                >
                  <Heart className={cn('w-7 h-7', liked ? 'fill-pink-500 text-pink-500' : 'text-white')} />
                  <span className="text-xs mt-1">{likes}</span>
                </button>
                <button type="button" className="flex flex-col items-center" onClick={() => setShowComments(true)}>
                  <MessageCircle className="w-7 h-7 text-white" />
                  <span className="text-xs mt-1">{comments}</span>
                </button>
                <button type="button" className="flex flex-col items-center" onClick={() => handleShare(char)}>
                  <Share2 className="w-7 h-7 text-white" />
                  <span className="text-xs mt-1">{shares}</span>
                </button>
              </div>

              <div className="absolute left-4 right-20 bottom-[calc(var(--app-safe-area-bottom)+24px)] z-20">
                <button
                  type="button"
                  className="text-left"
                  onClick={() => navigate(`/discover/profile/${char.id}`)}
                >
                  <div className="text-xl font-heading font-bold leading-tight">{getName(char)}</div>
                  {char.personality_summary && (
                    <p className="mt-1 text-sm text-zinc-200 line-clamp-2">{char.personality_summary}</p>
                  )}
                </button>
                <button
                  type="button"
                  className="mt-3 px-5 py-2 rounded-full bg-pink-500 hover:bg-pink-400 text-white font-semibold text-sm transition-colors"
                  onClick={() => handlePlayWithMe(char)}
                >
                  Play with me
                </button>
              </div>
            </section>
          );
        })}

        {!isAuthenticated && (
          <section className="relative h-[100dvh] snap-start flex items-center justify-center bg-zinc-950 px-6">
            <div className="w-full max-w-md rounded-2xl border border-white/10 bg-zinc-900/80 p-6 text-center">
              <h2 className="text-2xl font-heading font-bold">Continue Watching</h2>
              <p className="mt-2 text-zinc-300">
                Guest browsing limit reached. Login or create an account to keep swiping.
              </p>
              <div className="mt-6 grid grid-cols-1 gap-3">
                <button
                  type="button"
                  onClick={() => navigate('/register')}
                  className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-pink-500 px-4 py-3 font-semibold hover:bg-pink-400"
                >
                  <UserPlus className="w-4 h-4" />
                  Sign Up
                </button>
                <button
                  type="button"
                  onClick={() => navigate('/login')}
                  className="w-full inline-flex items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/5 px-4 py-3 font-semibold hover:bg-white/10"
                >
                  <LogIn className="w-4 h-4" />
                  Login
                </button>
              </div>
            </div>
          </section>
        )}

        {(isFetching || isFetchingNextPage) && (
          <div className="absolute top-20 right-4 z-40 rounded-full bg-black/40 px-3 py-1.5 text-xs inline-flex items-center gap-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Loading
          </div>
        )}
      </div>

      {showComments && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-end" onClick={() => setShowComments(false)}>
          <div
            className="w-full rounded-t-2xl border-t border-white/10 bg-zinc-950 p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold">Comments</h3>
            <p className="mt-2 text-zinc-400 text-sm">
              Comment interaction is now in UI preview mode. Backend posting can be connected next.
            </p>
            {currentCharacter && (
              <p className="mt-3 text-sm text-zinc-200">Now viewing: {getName(currentCharacter)}</p>
            )}
            <button
              type="button"
              className="mt-5 w-full rounded-xl bg-white/10 py-2.5 text-sm font-semibold hover:bg-white/15"
              onClick={() => setShowComments(false)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
