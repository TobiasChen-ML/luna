import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { Loader2, Plus, Search } from 'lucide-react';

import { api } from '@/services/api';
import { toChatUrl } from '@/utils/chatUrl';
import { cn } from '@/utils/cn';
import { PremiumOfferModal } from '@/components/billing/PremiumOfferModal';
import { CommingSoonModal } from '@/components/common';
import { useAuth } from '@/contexts/AuthContext';
import type { CategoriesResponse, FilterTagMeta, SubscriptionTier, TopCategory } from '@/types';

interface DiscoverCharacter {
  id: string;
  slug?: string;
  first_name?: string;
  name?: string;
  age?: number | string;
  avatar_url?: string;
  profile_image_url?: string;
  avatar_thumb_url?: string;
  avatar_card_url?: string;
  preview_video_url?: string | null;
  personality_summary?: string;
  tags?: string[];
  personality_tags?: string[];
  top_category?: import('@/types').TopCategory;
}

const PAGE_SIZE = 24;

interface UiConfigResponse {
  home?: {
    premium_offer?: {
      enabled?: boolean;
      banner_enabled?: boolean;
      default_hours?: number;
      end_at_ms?: number | null;
    };
    paywall?: {
      enabled?: boolean;
      trigger?: string;
      show_once?: boolean;
    };
  };
}

function formatCountdown(msRemaining: number) {
  const totalSeconds = Math.max(0, Math.floor(msRemaining / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${String(hours).padStart(2, '0')}Hrs${String(minutes).padStart(2, '0')}Min${String(seconds).padStart(2, '0')}Sec`;
}

function useLocalOfferCountdown(
  storageKey = 'premium_offer_ends_at',
  defaultHours = 8,
  forcedEndsAtMs?: number | null
) {
  const [endsAt, setEndsAt] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    if (typeof forcedEndsAtMs === 'number' && Number.isFinite(forcedEndsAtMs) && forcedEndsAtMs > Date.now() + 30_000) {
      window.localStorage.setItem(storageKey, String(forcedEndsAtMs));
      setEndsAt(forcedEndsAtMs);
      return;
    }

    const raw = window.localStorage.getItem(storageKey);
    const parsed = raw ? Number(raw) : NaN;
    const existingValid = Number.isFinite(parsed) && parsed > Date.now() + 30_000;

    const nextEndsAt = existingValid ? parsed : Date.now() + defaultHours * 3600 * 1000;
    window.localStorage.setItem(storageKey, String(nextEndsAt));
    setEndsAt(nextEndsAt);
  }, [storageKey, defaultHours, forcedEndsAtMs]);

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const msRemaining = endsAt ? endsAt - now : null;
  const countdownText = msRemaining !== null ? formatCountdown(msRemaining) : null;
  const isExpired = msRemaining !== null ? msRemaining <= 0 : false;

  return { endsAt, msRemaining, countdownText, isExpired };
}

function CandyLikeNavBar({ onOpenCommingSoon }: { onOpenCommingSoon: () => void }) {
  return (
    <div
      className="fixed left-0 right-0 z-50 bg-zinc-950/80 backdrop-blur border-b border-white/10"
      style={{ top: 'var(--app-safe-area-top)' }}
    >
      <div className="h-16 w-full max-w-[1600px] mx-auto px-4 md:px-8 flex items-center justify-between">
        <div className="flex items-center gap-5">
          <Link to="/home" className="font-heading font-bold text-lg text-white">
            RoxyClub
          </Link>
          <div className="hidden md:flex items-center gap-4 text-sm">
            <Link to="/home" className="text-zinc-200 hover:text-white transition-colors">
              Home
            </Link>
            <Link to="/community" className="text-zinc-400 hover:text-white transition-colors">
              Discover
            </Link>
            <Link to="/ai-girlfriend" className="text-white font-semibold">
              Girls
            </Link>
            <button
              type="button"
              onClick={onOpenCommingSoon}
              className="text-zinc-400 hover:text-white transition-colors"
            >
              Anime
            </button>
            <button
              type="button"
              onClick={onOpenCommingSoon}
              className="text-zinc-400 hover:text-white transition-colors"
            >
              Guys
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/subscriptions"
            className="px-3 py-2 rounded-full bg-pink-500/15 text-pink-300 border border-pink-500/30 hover:bg-pink-500/20 transition-colors text-sm font-semibold"
          >
            Premium
          </Link>
          <Link
            to="/create-character"
            className="hidden sm:inline-flex items-center gap-2 px-3 py-2 rounded-full bg-white/5 text-zinc-200 border border-white/10 hover:bg-white/10 transition-colors text-sm"
          >
            <Plus className="w-4 h-4" />
            Create
          </Link>
        </div>
      </div>

      {/* Mobile nav: simple category row */}
      <div className="md:hidden border-t border-white/10">
        <div className="w-full max-w-[1600px] mx-auto px-4 py-2 flex items-center gap-3 overflow-x-auto text-sm">
          <Link to="/home" className="shrink-0 px-3 py-1.5 rounded-full bg-white/10 text-white border border-white/10">
            Girls
          </Link>
          <button
            type="button"
            onClick={onOpenCommingSoon}
            className="shrink-0 px-3 py-1.5 rounded-full bg-transparent text-zinc-300 border border-white/10"
          >
            Anime
          </button>
          <button
            type="button"
            onClick={onOpenCommingSoon}
            className="shrink-0 px-3 py-1.5 rounded-full bg-transparent text-zinc-300 border border-white/10"
          >
            Guys
          </button>
          <Link to="/community" className="shrink-0 px-3 py-1.5 rounded-full bg-transparent text-zinc-300 border border-white/10">
            Discover
          </Link>
          <Link to="/subscriptions" className="shrink-0 px-3 py-1.5 rounded-full bg-pink-500/20 text-pink-200 border border-pink-500/30">
            Premium
          </Link>
        </div>
      </div>
    </div>
  );
}

function getName(char: DiscoverCharacter) {
  return char.first_name || char.name || 'Character';
}

function getAvatar(char: DiscoverCharacter) {
  return char.avatar_card_url || char.avatar_url || char.profile_image_url;
}

function getTags(char: DiscoverCharacter) {
  return char.personality_tags || char.tags || [];
}

function CharacterCard({ char, onClick }: { char: DiscoverCharacter; onClick: () => void }) {
  const [isHovering, setIsHovering] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const name = getName(char);
  const ageText = char.age !== undefined && char.age !== null ? String(char.age) : null;
  const avatar = getAvatar(char);
  const tags = getTags(char);
  const summary = char.personality_summary || tags[0] || null;

  const onEnter = () => {
    setIsHovering(true);
    if (videoRef.current) {
      videoRef.current.play().catch(() => {});
    }
  };

  const onLeave = () => {
    setIsHovering(false);
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
  };

  return (
    <div
      className="group relative aspect-[3/4] rounded-2xl overflow-hidden cursor-pointer border border-zinc-800/60 hover:border-white/20 transition-colors"
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      onClick={onClick}
    >
      {/* Poster / image */}
      {avatar ? (
        <img
          src={avatar}
          alt={name}
          className={cn(
            'absolute inset-0 w-full h-full object-cover transition-opacity duration-300',
            isHovering && char.preview_video_url ? 'opacity-0' : 'opacity-100'
          )}
          loading="lazy"
        />
      ) : (
        <div className="absolute inset-0 bg-gradient-to-br from-pink-500/10 to-purple-500/10" />
      )}

      {/* Hover video */}
      {char.preview_video_url && (
        <video
          ref={(el) => {
            videoRef.current = el;
          }}
          src={char.preview_video_url}
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

      {/* Bottom info (always visible) */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/15 to-transparent" />
      <div className="absolute bottom-0 left-0 right-0 p-4">
        <div className="flex items-baseline gap-2">
          <h3 className="text-lg font-heading font-bold text-white leading-tight truncate">
            {name}
          </h3>
          {ageText && (
            <span className="text-sm text-zinc-300">{ageText}</span>
          )}
        </div>
        {summary && (
          <p className="mt-1 text-xs text-zinc-300/90 line-clamp-1 leading-relaxed">
            {summary}
          </p>
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

function CandyLikeFooter() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-white/10 bg-black/40 mt-10">
      <div className="w-full max-w-[1600px] mx-auto px-4 md:px-8 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-8 text-sm">
          <div className="space-y-3">
            <div className="font-heading font-bold text-white text-lg">RoxyClub</div>
            <p className="text-zinc-400 leading-relaxed">
              Browse characters, preview moments, and start a story-driven chat.
            </p>
          </div>

          <div>
            <div className="text-white font-semibold mb-3">Explore</div>
            <ul className="space-y-2 text-zinc-400">
              <li><Link className="hover:text-white transition-colors" to="/home">Girls</Link></li>
              <li><Link className="hover:text-white transition-colors" to="/ai-anime">Anime</Link></li>
              <li><Link className="hover:text-white transition-colors" to="/ai-boyfriend">Guys</Link></li>
              <li><Link className="hover:text-white transition-colors" to="/community">Discover</Link></li>
            </ul>
          </div>

          <div>
            <div className="text-white font-semibold mb-3">Product</div>
            <ul className="space-y-2 text-zinc-400">
              <li><Link className="hover:text-white transition-colors" to="/subscriptions">Subscriptions</Link></li>
              <li><Link className="hover:text-white transition-colors" to="/create-character">Create</Link></li>
              <li><Link className="hover:text-white transition-colors" to="/characters">My AI</Link></li>
              <li><Link className="hover:text-white transition-colors" to="/gallery">Gallery</Link></li>
            </ul>
          </div>

          <div>
            <div className="text-white font-semibold mb-3">Legal</div>
            <ul className="space-y-2 text-zinc-400">
              <li><Link className="hover:text-white transition-colors" to="/privacy">Privacy</Link></li>
              <li><Link className="hover:text-white transition-colors" to="/terms">Terms</Link></li>
            </ul>
          </div>

          <div>
            <div className="text-white font-semibold mb-3">Support</div>
            <ul className="space-y-2 text-zinc-400">
              <li><Link className="hover:text-white transition-colors" to="/faq">Help Center</Link></li>
              <li><a className="hover:text-white transition-colors" href="mailto:support@roxyclub.ai">Contact</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-zinc-500">
          <div>(c) {year} RoxyClub. All rights reserved.</div>
          <div className="flex items-center gap-5">
            <Link className="hover:text-zinc-200 transition-colors" to="/privacy">Privacy</Link>
            <Link className="hover:text-zinc-200 transition-colors" to="/terms">Terms</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

export function LoggedInGirlsHomePage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const subscriptionTier: SubscriptionTier = user?.subscription_tier || 'free';

  const [activeCategory, setActiveCategory] = useState<TopCategory>('girls');
  const [activeFilterTag, setActiveFilterTag] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [paywallOpen, setPaywallOpen] = useState(false);
  const [isCommingSoonModalOpen, setIsCommingSoonModalOpen] = useState(false);
  const [pendingChatChar, setPendingChatChar] = useState<DiscoverCharacter | null>(null);
  const [hidePremiumBanner, setHidePremiumBanner] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchInput), 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const { data: uiConfig } = useQuery<UiConfigResponse>({
    queryKey: ['ui-config'],
    queryFn: () => api.get<UiConfigResponse>('/auth/ui_config').then((r) => r.data),
    staleTime: 10 * 60 * 1000,
    retry: false,
  });

  const offerConfig = uiConfig?.home?.premium_offer;
  const paywallConfig = uiConfig?.home?.paywall;

  const offerEnabled = offerConfig?.enabled !== false;
  const bannerEnabled = offerConfig?.banner_enabled !== false;
  const defaultOfferHours = offerConfig?.default_hours ?? 8;
  const forcedEndsAtMs = offerConfig?.end_at_ms ?? null;

  const { countdownText } = useLocalOfferCountdown(
    'home_premium_offer_ends_at',
    defaultOfferHours,
    forcedEndsAtMs
  );

  useEffect(() => {
    setHidePremiumBanner(window.localStorage.getItem('home_hide_premium_banner') === '1');
  }, []);

  const { data: categoriesData } = useQuery<CategoriesResponse>({
    queryKey: ['characters-categories'],
    queryFn: () => api.get<CategoriesResponse>('/characters/categories').then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });

  const activeCategorySummary = useMemo(
    () => categoriesData?.categories?.find((c) => c.slug === activeCategory),
    [categoriesData, activeCategory]
  );
  const filterTags: FilterTagMeta[] = activeCategorySummary?.filter_tags ?? [];

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetching,
    isFetchingNextPage,
  } = useInfiniteQuery<DiscoverCharacter[]>({
    queryKey: ['home-discover', activeCategory, activeFilterTag, debouncedSearch],
    queryFn: async ({ pageParam }) => {
      const offset = typeof pageParam === 'number' ? pageParam : 0;
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(offset),
        top_category: activeCategory,
      });
      if (activeFilterTag) params.set('filter_tag', activeFilterTag);
      if (debouncedSearch.trim()) params.set('name', debouncedSearch.trim());
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

  const characters = useMemo(() => (data?.pages ?? []).flat(), [data]);

  const sentinelRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    if (!hasNextPage) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const first = entries[0];
        if (!first?.isIntersecting) return;
        if (isFetchingNextPage) return;
        fetchNextPage().catch(() => {});
      },
      { rootMargin: '600px 0px' }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  const onSelectFilter = (slug: string | null) => {
    setActiveFilterTag(slug);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const onSelectCategory = (cat: TopCategory) => {
    setActiveCategory(cat);
    setActiveFilterTag(null);
    setSearchInput('');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const shouldShowPaywall = subscriptionTier === 'free' && paywallConfig?.enabled !== false;
  const paywallTrigger = (paywallConfig?.trigger || 'first_chat_click').toLowerCase();
  const paywallShowOnce = paywallConfig?.show_once !== false;
  const paywallSeenKey = 'home_paywall_seen_v2';

  const [hasScrolledDeep, setHasScrolledDeep] = useState(false);
  useEffect(() => {
    const onScroll = () => {
      if (window.scrollY > window.innerHeight * 2) {
        setHasScrolledDeep(true);
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const openChat = (char: DiscoverCharacter) => {
    if (shouldShowPaywall) {
      const seen = window.localStorage.getItem(paywallSeenKey) === '1';

      const gateByScroll = paywallTrigger === 'after_scroll' && hasScrolledDeep;
      const gateByFirstClick = paywallTrigger === 'first_chat_click';
      const gateAlways = paywallTrigger === 'always';

      const shouldGate = gateAlways || gateByFirstClick || gateByScroll;
      const shouldGateNow = shouldGate && (!paywallShowOnce || !seen);

      if (shouldGateNow) {
        window.localStorage.setItem(paywallSeenKey, '1');
        setPendingChatChar(char);
        setPaywallOpen(true);
        return;
      }
    }
    navigate(toChatUrl(char));
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      <CandyLikeNavBar onOpenCommingSoon={() => setIsCommingSoonModalOpen(true)} />

      {/* Sticky premium banner (Candy-like urgency, original copy) */}
      {subscriptionTier === 'free' && offerEnabled && bannerEnabled && countdownText && !hidePremiumBanner && (
        <div className="fixed top-[calc(7rem+var(--app-safe-area-top))] md:top-[calc(4rem+var(--app-safe-area-top))] left-0 right-0 z-40">
          <div className="w-full max-w-[1600px] mx-auto px-4 md:px-8 py-2">
            <div className="flex items-center justify-between gap-3 px-4 py-2 rounded-xl bg-gradient-to-r from-pink-500/15 to-purple-500/15 border border-pink-500/20 backdrop-blur">
              <div className="text-sm text-zinc-200">
                <span className="font-semibold text-pink-200">Limited-time Premium offer</span>{' '}
                <span className="text-zinc-300">ends in</span>{' '}
                <span className="font-mono text-zinc-100">{countdownText}</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPaywallOpen(true)}
                  className="px-3 py-1.5 rounded-full bg-pink-500 text-white text-sm font-semibold hover:bg-pink-400 transition-colors"
                >
                  Upgrade
                </button>
                <button
                  onClick={() => {
                    window.localStorage.setItem('home_hide_premium_banner', '1');
                    setHidePremiumBanner(true);
                  }}
                  className="px-3 py-1.5 rounded-full bg-white/5 text-zinc-200 text-sm hover:bg-white/10 transition-colors"
                >
                  Later
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="w-full max-w-[1600px] mx-auto px-4 md:px-8 pt-6 pb-10">
        {/* Hero row */}
        <div className="pt-28 md:pt-10">
          <div className="flex items-end justify-between gap-4 mb-4">
            <div className="hidden md:flex items-center gap-3">
              <Link
                to="/characters"
                className="text-sm text-zinc-300 hover:text-white transition-colors"
              >
                My AI
              </Link>
              <button
                onClick={() => setPaywallOpen(true)}
                className="text-sm font-semibold px-3 py-2 rounded-full bg-pink-500 text-white hover:bg-pink-400 transition-colors"
              >
                Go Premium
              </button>
            </div>
          </div>
        </div>

        {/* Category tabs + search row */}
        <div className="flex items-center gap-3 mb-4">
          {/* Category tabs */}
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

          {/* Search input */}
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

        {/* Filter pills 鈥?single-row horizontal scroll */}
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
              <CharacterCard key={char.id} char={char} onClick={() => openChat(char)} />
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
            {debouncedSearch ? `No results for "${debouncedSearch}"` : 'No characters found.'}
          </div>
        )}

        {!hasNextPage && characters.length > 0 && (
          <div className="py-10 text-center text-sm text-zinc-500">
            You've reached the end.
          </div>
        )}
      </div>

      <PremiumOfferModal
        isOpen={paywallOpen}
        onClose={() => {
          setPaywallOpen(false);
          setPendingChatChar(null);
        }}
        countdownText={countdownText}
        onContinueFree={
          pendingChatChar
            ? () => {
                const char = pendingChatChar;
                setPaywallOpen(false);
                setPendingChatChar(null);
                navigate(toChatUrl(char));
              }
            : undefined
        }
      />
      <CommingSoonModal
        isOpen={isCommingSoonModalOpen}
        onClose={() => setIsCommingSoonModalOpen(false)}
      />

      <CandyLikeFooter />
    </div>
  );
}



