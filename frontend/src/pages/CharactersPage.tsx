import { useRef, useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { Loader2, Search } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useTelegram } from '@/contexts/TelegramContext';
import { useTelegramMainButton } from '@/hooks/useTelegramMainButton';
import { api } from '@/services/api';
import { cn } from '@/utils/cn';
import { toChatUrl } from '@/utils/chatUrl';
import { FavoriteButton } from '@/components/character/FavoriteButton';
import type { TopCategory, CategoriesResponse } from '@/types';

interface DiscoverCharacter {
  id: string;
  slug?: string;
  name?: string;
  first_name?: string;
  age?: number | string;
  avatar_url?: string;
  profile_image_url?: string;
  mature_image_url?: string;
  mature_cover_url?: string;
  mature_video_url?: string;
  personality_tags?: string[];
  personality_summary?: string;
  tags?: string[];
  top_category?: TopCategory;
  filter_tags?: string[];
  preview_video_url?: string | null;
}

const PAGE_SIZE = 24;

interface CharactersPageProps {
  initialCategory?: TopCategory;
}

function getName(char: DiscoverCharacter) {
  return char.first_name || char.name || 'Character';
}

function getDisplayMedia(char: DiscoverCharacter, isAuthenticated: boolean) {
  const avatar = isAuthenticated
    ? (char.mature_image_url || char.avatar_url || char.profile_image_url)
    : (char.avatar_url || char.profile_image_url);
  const video = isAuthenticated
    ? (char.mature_video_url || char.preview_video_url)
    : char.preview_video_url;
  return { avatar, video };
}

function CharacterCard({
  char,
  onClick,
  isSelected = false,
  showFavorite = false,
  onRecordView,
  isAuthenticated = false,
}: {
  char: DiscoverCharacter;
  onClick: () => void;
  isSelected?: boolean;
  showFavorite?: boolean;
  onRecordView?: (charId: string) => void;
  isAuthenticated?: boolean;
}) {
  const [isHovering, setIsHovering] = useState(false);
  const [viewRecorded, setViewRecorded] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hoverTimeoutRef = useRef<number | null>(null);

  const name = getName(char);
  const ageText = char.age !== undefined && char.age !== null ? String(char.age) : null;
  const { avatar, video } = getDisplayMedia(char, isAuthenticated);
  const tags = char.personality_tags || char.tags || [];
  const summary = char.personality_summary || tags[0] || null;

  const onEnter = () => {
    setIsHovering(true);
    if (videoRef.current) videoRef.current.play().catch(() => {});
    
    if (!viewRecorded && onRecordView) {
      hoverTimeoutRef.current = window.setTimeout(() => {
        onRecordView(char.id);
        setViewRecorded(true);
      }, 2000);
    }
  };

  const onLeave = () => {
    setIsHovering(false);
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
      hoverTimeoutRef.current = null;
    }
  };

  return (
    <div
      className={cn(
        'group relative aspect-[3/4] rounded-2xl overflow-hidden cursor-pointer border transition-colors',
        isSelected
          ? 'border-pink-500 ring-2 ring-pink-500/50'
          : 'border-zinc-800/60 hover:border-white/20'
      )}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      onClick={onClick}
    >
      {avatar ? (
        <img
          src={avatar}
          alt={name}
          className={cn(
            'absolute inset-0 w-full h-full object-cover transition-opacity duration-300',
            isHovering && video ? 'opacity-0' : 'opacity-100'
          )}
          loading="lazy"
        />
      ) : (
        <div className="absolute inset-0 bg-gradient-to-br from-pink-500/10 to-purple-500/10" />
      )}

      {video && (
        <video
          ref={(el) => { videoRef.current = el; }}
          src={video}
          className={cn(
            'absolute inset-0 w-full h-full object-cover transition-opacity duration-300',
            isHovering ? 'opacity-100' : 'opacity-0'
          )}
          muted
          loop
          playsInline
          preload="none"
        />
      )}

      <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/15 to-transparent" />
      
      {showFavorite && (
        <div className="absolute top-3 right-3 z-10">
          <FavoriteButton characterId={char.id} size="md" />
        </div>
      )}
      
      <div className="absolute bottom-0 left-0 right-0 p-4">
        <div className="flex items-baseline gap-2">
          <h3 className="text-lg font-heading font-bold text-white leading-tight truncate">{name}</h3>
          {ageText && <span className="text-sm text-zinc-300">{ageText}</span>}
        </div>
        {summary && (
          <p className="mt-1 text-xs text-zinc-300/90 line-clamp-1 leading-relaxed">{summary}</p>
        )}
        <div className="mt-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <div className="inline-flex items-center justify-center px-3 py-1.5 rounded-full bg-white/10 border border-white/15 text-white text-xs font-semibold">
            Chat Now
          </div>
        </div>
      </div>
    </div>
  );
}

export function CharactersPage({ initialCategory }: CharactersPageProps = {}) {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const { isTma } = useTelegram();

  const [activeCategory, setActiveCategory] = useState<TopCategory>(initialCategory ?? 'girls');
  const [activeFilterTag, setActiveFilterTag] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState('');
  const [selectedChar, setSelectedChar] = useState<DiscoverCharacter | null>(null);

  const { data: categoriesData } = useQuery<CategoriesResponse>({
    queryKey: ['characters-categories'],
    queryFn: () => api.get<CategoriesResponse>('/characters/categories').then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });

  const activeCategorySummary = categoriesData?.categories?.find((c) => c.slug === activeCategory);
  const filterTags = activeCategorySummary?.filter_tags ?? [];

  const recordView = useCallback(async (characterId: string) => {
    if (!isAuthenticated || !user) return;
    try {
      await api.post(`/characters/${characterId}/view`, { view_duration_seconds: 2 });
    } catch (error) {
      console.error('Failed to record view:', error);
    }
  }, [isAuthenticated, user]);

  const {
    data,
    hasNextPage,
    isFetching,
    isFetchingNextPage,
  } = useInfiniteQuery<DiscoverCharacter[]>({
    queryKey: ['characters-discover', activeCategory, activeFilterTag, searchInput, isAuthenticated],
    queryFn: async ({ pageParam }) => {
      const offset = typeof pageParam === 'number' ? pageParam : 0;
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(offset),
        top_category: activeCategory,
        personalized: 'true',
      });
      if (activeFilterTag) params.set('filter_tag', activeFilterTag);
      if (searchInput.trim()) params.set('name', searchInput.trim());
      const resp = await api.get<DiscoverCharacter[]>(`/characters/discover?${params.toString()}`);
      return Array.isArray(resp.data) ? resp.data : [];
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      if (!Array.isArray(lastPage) || lastPage.length < PAGE_SIZE) return undefined;
      return allPages.length * PAGE_SIZE;
    },
    staleTime: 2 * 60 * 1000,
  });

  const characters = (data?.pages ?? []).flat();

  const sentinelRef = useRef<HTMLDivElement | null>(null);

  const onSelectCategory = (cat: TopCategory) => {
    setActiveCategory(cat);
    setActiveFilterTag(null);
    setSearchInput('');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const onSelectFilter = (slug: string | null) => {
    setActiveFilterTag(slug);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const navigateToChat = useCallback((char: DiscoverCharacter) => {
    navigate(isAuthenticated ? toChatUrl(char) : '/register');
  }, [isAuthenticated, navigate]);

  const openChat = (char: DiscoverCharacter) => {
    // In TMA: first tap selects; MainButton confirms navigation
    if (isTma) {
      setSelectedChar(char);
      return;
    }
    navigateToChat(char);
  };

  // TMA MainButton — shows when a character is selected
  useTelegramMainButton({
    text: selectedChar ? `Chat with ${getName(selectedChar)}` : 'Select a Character',
    onClick: useCallback(() => {
      if (selectedChar) navigateToChat(selectedChar);
    }, [selectedChar, navigateToChat]),
    isVisible: isTma && !!selectedChar,
  });

  return (
    <div>
      {/* Category tabs + search row */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex gap-1 shrink-0">
          {(['girls', 'anime', 'guys'] as const).map((cat) => (
            <button
              key={cat}
              onClick={() => onSelectCategory(cat)}
              className={cn(
                'px-5 py-2 rounded-full text-sm font-semibold border transition-colors capitalize',
                activeCategory === cat
                  ? 'bg-white/10 text-white border-white/20'
                  : 'bg-transparent text-zinc-400 border-white/10 hover:bg-white/5 hover:text-zinc-200'
              )}
            >
              {cat === 'girls' ? 'Girls' : cat === 'anime' ? 'Anime' : 'Guys'}
            </button>
          ))}
        </div>

        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 pointer-events-none" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search..."
            className="w-full pl-9 pr-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-white placeholder:text-zinc-500 focus:outline-none focus:border-white/25 transition-colors"
          />
        </div>
      </div>

      {/* Filter pills — horizontal scroll */}
      {filterTags.length > 0 && (
        <div className="flex gap-2 mb-6 overflow-x-auto pb-1 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          <button
            onClick={() => onSelectFilter(null)}
            className={cn(
              'shrink-0 px-4 py-2 rounded-full text-xs font-semibold border transition-colors',
              activeFilterTag === null
                ? 'bg-white/10 text-white border-white/15'
                : 'bg-transparent text-zinc-300 border-white/10 hover:bg-white/5'
            )}
          >
            All
          </button>
          {filterTags.map((ft) => (
            <button
              key={ft.slug}
              onClick={() => onSelectFilter(ft.slug)}
              className={cn(
                'shrink-0 px-4 py-2 rounded-full text-xs font-semibold border transition-colors',
                activeFilterTag === ft.slug
                  ? 'bg-pink-500/20 text-pink-200 border-pink-500/30'
                  : 'bg-transparent text-zinc-300 border-white/10 hover:bg-white/5'
              )}
            >
              {ft.display_name}
            </button>
          ))}
        </div>
      )}

      {/* Grid */}
      {isFetching && characters.length === 0 ? (
        <div className="py-20 flex items-center justify-center text-zinc-400">
          <Loader2 className="w-6 h-6 mr-2 animate-spin" />
          Loading...
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
          {characters.map((char) => (
            <CharacterCard
              key={char.id}
              char={char}
              onClick={() => openChat(char)}
              isSelected={isTma && selectedChar?.id === char.id}
              showFavorite={isAuthenticated}
              onRecordView={recordView}
              isAuthenticated={isAuthenticated}
            />
          ))}
        </div>
      )}

      {/* Infinite scroll sentinel */}
      <div ref={sentinelRef} className="h-10" />
      {(isFetchingNextPage || (hasNextPage && characters.length > 0)) && (
        <div className="py-10 flex items-center justify-center text-zinc-400">
          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
          Loading more...
        </div>
      )}

      {!isFetching && characters.length === 0 && (
        <div className="py-20 text-center text-sm text-zinc-400">
          {searchInput ? `No results for "${searchInput}"` : 'No characters found.'}
        </div>
      )}

      {!hasNextPage && characters.length > 0 && (
        <div className="py-10 text-center text-sm text-zinc-500">
          You've reached the end.
        </div>
      )}
    </div>
  );
}
