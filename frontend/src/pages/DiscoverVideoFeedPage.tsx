import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInfiniteQuery } from '@tanstack/react-query';
import { Heart, Loader2, LogIn, MessageCircle, Share2, UserPlus } from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';
import { cn } from '@/utils/cn';
import { startOfficialChat } from '@/utils/startOfficialChat';
import { claimShareReward, share } from '@/utils/share';
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
  description?: string;
  tags?: string[];
  top_category?: TopCategory;
  comment_count?: number;
}

interface DiscoverComment {
  id: string;
  author: string;
  text: string;
  likes: number;
  created_at: string;
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

function hasPlayableVideo(char: DiscoverCharacter) {
  return Boolean(char.mature_video_url || char.preview_video_url);
}

function pseudoCount(seed: string, base: number, mod: number) {
  let value = 0;
  for (let i = 0; i < seed.length; i += 1) value = (value * 31 + seed.charCodeAt(i)) % 100000;
  return base + (value % mod);
}

function formatCommentTime(createdAt: string) {
  const created = new Date(createdAt).getTime();
  if (Number.isNaN(created)) return '';

  const seconds = Math.max(0, Math.floor((Date.now() - created) / 1000));
  if (seconds < 60) return 'now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}

export function DiscoverVideoFeedPage() {
  const navigate = useNavigate();
  const { isAuthenticated, refreshUser } = useAuth();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [likedIds, setLikedIds] = useState<Record<string, boolean>>({});
  const [showComments, setShowComments] = useState(false);
  const [commentsByCharacter, setCommentsByCharacter] = useState<Record<string, DiscoverComment[]>>({});
  const [loadingCommentsFor, setLoadingCommentsFor] = useState<string | null>(null);
  const [commentInput, setCommentInput] = useState('');
  const [postingComment, setPostingComment] = useState(false);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const sectionRefs = useRef<(HTMLElement | null)[]>([]);

  const {
    data,
    hasNextPage,
    isFetching,
    isFetchingNextPage,
    fetchNextPage,
  } = useInfiniteQuery<DiscoverCharacter[]>({
    queryKey: ['discover-video-feed'],
    queryFn: async ({ pageParam }) => {
      const offset = typeof pageParam === 'number' ? pageParam : 0;
      const params = new URLSearchParams({
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
  const allVideoCharacters = useMemo(
    () => allCharacters.filter((char) => hasPlayableVideo(char)),
    [allCharacters]
  );
  const visibleCharacters = useMemo(
    () => (isAuthenticated ? allVideoCharacters : allVideoCharacters.slice(0, GUEST_BROWSE_LIMIT)),
    [allVideoCharacters, isAuthenticated]
  );
  const currentCharacter = visibleCharacters[currentIndex] ?? null;
  const currentComments = currentCharacter ? commentsByCharacter[currentCharacter.id] ?? [] : [];
  const currentCommentsLoaded = currentCharacter ? currentCharacter.id in commentsByCharacter : false;

  useEffect(() => {
    if (currentIndex < visibleCharacters.length) return;
    setCurrentIndex(Math.max(0, visibleCharacters.length - 1));
  }, [currentIndex, visibleCharacters.length]);

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

  useEffect(() => {
    if (!showComments || !currentCharacter) return;
    if (currentCharacter.id in commentsByCharacter) return;

    let cancelled = false;
    setLoadingCommentsFor(currentCharacter.id);
    api.get<DiscoverComment[]>(`/characters/${currentCharacter.id}/comments`)
      .then((response) => {
        if (cancelled) return;
        setCommentsByCharacter((prev) => ({
          ...prev,
          [currentCharacter.id]: Array.isArray(response.data) ? response.data : [],
        }));
      })
      .catch((error) => {
        console.error('Failed to load discover comments:', error);
        if (!cancelled) {
          setCommentsByCharacter((prev) => ({ ...prev, [currentCharacter.id]: [] }));
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingCommentsFor(null);
      });

    return () => {
      cancelled = true;
    };
  }, [commentsByCharacter, currentCharacter, showComments]);

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
    const didShare = await share({ title, url: shareUrl });
    if (!didShare || !isAuthenticated) return;

    const reward = await claimShareReward(`discover:${char.id}`, 'discover_profile', {
      character_id: char.id,
      top_category: char.top_category ?? null,
    });
    if (reward?.granted) {
      await refreshUser();
    }
  }, [isAuthenticated, refreshUser]);

  const getCommentCount = useCallback((char: DiscoverCharacter) => {
    return commentsByCharacter[char.id]?.length ?? char.comment_count ?? 0;
  }, [commentsByCharacter]);

  const handleSubmitComment = useCallback(async () => {
    if (!currentCharacter || postingComment) return;
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    const text = commentInput.trim();
    if (!text) return;

    setPostingComment(true);
    try {
      const response = await api.post<DiscoverComment>(`/characters/${currentCharacter.id}/comments`, { text });
      setCommentsByCharacter((prev) => ({
        ...prev,
        [currentCharacter.id]: [response.data, ...(prev[currentCharacter.id] ?? [])],
      }));
      setCommentInput('');
    } catch (error) {
      console.error('Failed to post discover comment:', error);
    } finally {
      setPostingComment(false);
    }
  }, [commentInput, currentCharacter, isAuthenticated, navigate, postingComment]);

  return (
    <div className="h-[100dvh] bg-black text-white">
      <div ref={containerRef} className="h-full overflow-y-auto snap-y snap-mandatory">
        {visibleCharacters.map((char, index) => {
          const { poster, video } = getDisplayMedia(char);
          const liked = Boolean(likedIds[char.id]);
          const likes = pseudoCount(char.id, 1200, 50000) + (liked ? 1 : 0);
          const comments = getCommentCount(char);
          const shares = pseudoCount(`${char.id}-share`, 40, 1500);
          const storyBackground = char.description?.trim();

          return (
            <section
              key={char.id}
              ref={(el) => { sectionRefs.current[index] = el; }}
              data-index={index}
              className="relative h-[100dvh] snap-start overflow-hidden"
            >
              {video ? (
                <video
                  src={video}
                  className="absolute top-0 left-1/2 h-full w-auto max-w-none -translate-x-1/2 object-cover"
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

              <div className="absolute left-4 right-20 bottom-[calc(var(--app-safe-area-bottom)+108px)] z-20">
                <button
                  type="button"
                  className="text-left"
                  onClick={() => navigate(`/discover/profile/${char.id}`)}
                >
                  <div className="text-xl font-heading font-bold leading-tight">{getName(char)}</div>
                  {storyBackground && (
                    <p className="mt-2 text-sm text-zinc-200 line-clamp-3">{storyBackground}</p>
                  )}
                </button>
              </div>

              <div className="absolute left-4 right-4 bottom-[calc(var(--app-safe-area-bottom)+24px)] z-20 flex justify-center">
                <button
                  type="button"
                  className="h-12 w-full max-w-sm rounded-full bg-pink-500 hover:bg-pink-400 text-white font-semibold text-base transition-colors shadow-[0_10px_30px_rgba(236,72,153,0.35)]"
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
            className="w-full max-h-[72dvh] rounded-t-2xl border-t border-white/10 bg-zinc-950 p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Comments</h3>
                {currentCharacter && (
                  <p className="mt-0.5 text-xs text-zinc-400">{getName(currentCharacter)} preview discussion</p>
                )}
              </div>
              <button
                type="button"
                className="rounded-full bg-white/10 px-3 py-1.5 text-xs font-semibold hover:bg-white/15"
                onClick={() => setShowComments(false)}
              >
                Close
              </button>
            </div>
            {currentCharacter && (
              <div className="mt-4 max-h-[46dvh] space-y-4 overflow-y-auto pr-1">
                {loadingCommentsFor === currentCharacter.id && !currentCommentsLoaded && (
                  <div className="py-8 text-center text-sm text-zinc-500">Loading comments...</div>
                )}
                {currentCommentsLoaded && currentComments.length === 0 && (
                  <div className="py-8 text-center text-sm text-zinc-500">No comments yet.</div>
                )}
                {currentComments.map((comment) => (
                  <div key={comment.id} className="flex gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-pink-500 to-cyan-400 text-xs font-bold text-white">
                      {comment.author.slice(0, 1)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-white">{comment.author}</span>
                        <span className="text-xs text-zinc-500">{formatCommentTime(comment.created_at)}</span>
                      </div>
                      <p className="mt-1 text-sm leading-relaxed text-zinc-200">{comment.text}</p>
                      <div className="mt-2 flex items-center gap-3 text-xs text-zinc-500">
                        <span>{comment.likes} likes</span>
                        <span>Reply</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="mt-5 flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2">
              <input
                value={commentInput}
                onChange={(event) => setCommentInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault();
                    handleSubmitComment();
                  }
                }}
                disabled={postingComment}
                placeholder={isAuthenticated ? 'Add a comment...' : 'Log in to comment'}
                className="min-w-0 flex-1 bg-transparent text-sm text-white placeholder:text-zinc-500 outline-none"
              />
              <button
                type="button"
                className="text-sm font-semibold text-pink-300 disabled:text-zinc-600"
                disabled={postingComment || (isAuthenticated && !commentInput.trim())}
                onClick={handleSubmitComment}
              >
                {postingComment ? 'Posting' : 'Post'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
