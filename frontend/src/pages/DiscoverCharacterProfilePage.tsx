import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Grid3X3, ImageIcon, Loader2, MessageCircle, Play, X, type LucideIcon } from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';
import { cn } from '@/utils/cn';
import { startOfficialChat } from '@/utils/startOfficialChat';

type ProfileMediaType = 'video' | 'image';
type ProfileMediaFilter = 'all' | ProfileMediaType;

interface CharacterProfileMedia {
  id?: string;
  type?: ProfileMediaType | string;
  media_type?: ProfileMediaType | string;
  url?: string;
  image_url?: string;
  video_url?: string;
  thumbnail_url?: string;
  poster_url?: string;
  cover_url?: string;
}

interface CharacterProfile {
  id: string;
  name?: string;
  first_name?: string;
  age?: number | string;
  top_category?: string;
  avatar_url?: string;
  profile_image_url?: string;
  mature_image_url?: string;
  mature_cover_url?: string;
  mature_video_url?: string;
  preview_video_url?: string | null;
  personality_summary?: string;
  description?: string;
  tags?: string[];
  personality_tags?: string[];
  media?: CharacterProfileMedia[];
  gallery?: string[];
  image_urls?: string[];
  video_urls?: string[];
}

interface ProfileMediaItem {
  id: string;
  type: ProfileMediaType;
  url: string;
  thumbnailUrl?: string;
  label: string;
}

const MEDIA_FILTERS: Array<{
  id: ProfileMediaFilter;
  label: string;
  Icon: LucideIcon;
}> = [
  { id: 'all', label: 'All', Icon: Grid3X3 },
  { id: 'video', label: 'Videos', Icon: Play },
  { id: 'image', label: 'Photos', Icon: ImageIcon },
];

function getName(char?: CharacterProfile | null) {
  if (!char) return 'Character';
  return char.first_name || char.name || 'Character';
}

export function DiscoverCharacterProfilePage() {
  const navigate = useNavigate();
  const { characterId } = useParams<{ characterId: string }>();
  const { isAuthenticated } = useAuth();
  const [activeFilter, setActiveFilter] = useState<ProfileMediaFilter>('all');
  const [activeMedia, setActiveMedia] = useState<ProfileMediaItem | null>(null);

  const { data, isLoading, isError } = useQuery<CharacterProfile>({
    queryKey: ['discover-character-profile', characterId],
    queryFn: async () => {
      const response = await api.get<CharacterProfile>(`/characters/official/${characterId}`);
      return response.data;
    },
    enabled: Boolean(characterId),
    staleTime: 60 * 1000,
  });

  const mediaItems = useMemo<ProfileMediaItem[]>(() => {
    if (!data) return [];

    const items: ProfileMediaItem[] = [];
    const seen = new Set<string>();
    const fallbackPoster = data.mature_cover_url || data.mature_image_url || data.profile_image_url || data.avatar_url;

    const addMedia = (type: ProfileMediaType, url: string | null | undefined, thumbnailUrl: string | null | undefined, label: string) => {
      if (!url || seen.has(`${type}:${url}`)) return;
      seen.add(`${type}:${url}`);
      items.push({
        id: `${type}-${items.length}`,
        type,
        url,
        thumbnailUrl: thumbnailUrl || undefined,
        label,
      });
    };

    addMedia('video', data.mature_video_url || data.preview_video_url, fallbackPoster, 'Featured video');
    addMedia('image', data.profile_image_url, data.profile_image_url, 'Profile photo');
    addMedia('image', data.mature_cover_url, data.mature_cover_url, 'Cover photo');
    addMedia('image', data.mature_image_url, data.mature_image_url, 'Gallery photo');
    addMedia('image', data.avatar_url, data.avatar_url, 'Avatar');

    data.video_urls?.forEach((url, index) => {
      addMedia('video', url, fallbackPoster, `Video ${index + 1}`);
    });

    data.image_urls?.forEach((url, index) => {
      addMedia('image', url, url, `Photo ${index + 1}`);
    });

    data.gallery?.forEach((url, index) => {
      addMedia('image', url, url, `Gallery ${index + 1}`);
    });

    data.media?.forEach((media, index) => {
      const mediaUrl = media.url || media.video_url || media.image_url;
      const mediaType = media.type || media.media_type || (media.video_url ? 'video' : 'image');
      const normalizedType: ProfileMediaType = String(mediaType).toLowerCase() === 'video' ? 'video' : 'image';
      const thumbnailUrl = media.thumbnail_url || media.poster_url || media.cover_url || media.image_url || fallbackPoster;
      addMedia(normalizedType, mediaUrl, thumbnailUrl, `${normalizedType === 'video' ? 'Video' : 'Photo'} ${index + 1}`);
    });

    return items;
  }, [data]);

  const filteredMediaItems = useMemo(
    () => (activeFilter === 'all' ? mediaItems : mediaItems.filter((item) => item.type === activeFilter)),
    [activeFilter, mediaItems]
  );

  const videoCount = mediaItems.filter((item) => item.type === 'video').length;
  const imageCount = mediaItems.filter((item) => item.type === 'image').length;

  const handlePlayWithMe = async () => {
    if (!data?.id) return;
    try {
      await startOfficialChat(navigate, {
        isAuthenticated,
        characterId: data.id,
      });
    } catch (error) {
      console.error('Failed to start official chat from profile page:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="h-[100dvh] bg-black text-white flex items-center justify-center">
        <Loader2 className="w-7 h-7 animate-spin" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="h-[100dvh] bg-black text-white flex items-center justify-center px-6">
        <div className="text-center">
          <p className="text-lg font-semibold">Character not found</p>
          <button
            type="button"
            className="mt-4 rounded-md bg-white px-4 py-2 text-sm font-semibold text-black hover:bg-zinc-200"
            onClick={() => navigate('/discover')}
          >
            Back to Discover
          </button>
        </div>
      </div>
    );
  }

  const displayName = getName(data);
  const avatar = data.avatar_url || data.profile_image_url || data.mature_image_url || data.mature_cover_url;
  const heroMedia = mediaItems.find((item) => item.type === 'video') || mediaItems[0];
  const tags = (data.personality_tags?.length ? data.personality_tags : data.tags) || [];

  return (
    <div className="min-h-[100dvh] bg-black text-white">
      <header className="sticky top-0 z-40 border-b border-white/10 bg-black/90 px-3 pt-[calc(var(--app-safe-area-top)+8px)] backdrop-blur">
        <div className="mx-auto flex h-12 max-w-[520px] items-center justify-between">
          <button
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/10 hover:bg-white/15"
            onClick={() => navigate('/discover')}
            aria-label="Back to Discover"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="min-w-0 px-3 text-center">
            <p className="truncate text-sm font-semibold">@{displayName}</p>
          </div>
          <div className="h-9 w-9" />
        </div>
      </header>

      <main className="mx-auto max-w-[520px] pb-[calc(var(--app-safe-area-bottom)+28px)]">
        <section className="relative h-[42dvh] min-h-[340px] overflow-hidden bg-zinc-950">
          {heroMedia?.type === 'video' ? (
            <video
              src={heroMedia.url}
              poster={heroMedia.thumbnailUrl}
              className="absolute inset-0 h-full w-full object-cover"
              autoPlay
              muted
              loop
              playsInline
            />
          ) : heroMedia?.url ? (
            <img src={heroMedia.url} alt={displayName} className="absolute inset-0 h-full w-full object-cover" />
          ) : (
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,#27272a,#020617_70%)]" />
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black via-black/25 to-black/10" />

          <div className="absolute bottom-5 left-4 right-20">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-300">Discover profile</p>
            <h1 className="mt-2 text-4xl font-heading font-bold leading-none">{displayName}</h1>
            {data.age != null && <p className="mt-2 text-sm text-zinc-200">Age {String(data.age)}</p>}
          </div>

          <div className="absolute bottom-5 right-4 flex flex-col items-center gap-4">
            <button
              type="button"
              className="relative h-16 w-16 overflow-hidden rounded-full border-2 border-white bg-zinc-900"
              onClick={() => {
                if (heroMedia) setActiveMedia(heroMedia);
              }}
              aria-label="Open featured media"
            >
              {avatar ? (
                <img src={avatar} alt={displayName} className="h-full w-full object-cover" />
              ) : (
                <span className="flex h-full w-full items-center justify-center text-xl font-bold">
                  {displayName.slice(0, 1)}
                </span>
              )}
            </button>
            <button
              type="button"
              className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-white text-black hover:bg-zinc-200"
              onClick={handlePlayWithMe}
              aria-label="Start chat"
            >
              <MessageCircle className="h-5 w-5" />
            </button>
          </div>
        </section>

        <section className="px-4 py-5">
          <div className="flex items-start gap-4">
            <div className="h-20 w-20 shrink-0 overflow-hidden rounded-full border border-white/20 bg-zinc-900">
              {avatar ? (
                <img src={avatar} alt={displayName} className="h-full w-full object-cover" />
              ) : (
                <span className="flex h-full w-full items-center justify-center text-2xl font-bold">
                  {displayName.slice(0, 1)}
                </span>
              )}
            </div>

            <div className="min-w-0 flex-1">
              <div className="grid grid-cols-3 gap-3 text-center">
                <div>
                  <div className="text-lg font-bold">{mediaItems.length}</div>
                  <div className="mt-0.5 text-[11px] text-zinc-400">Media</div>
                </div>
                <div>
                  <div className="text-lg font-bold">{videoCount}</div>
                  <div className="mt-0.5 text-[11px] text-zinc-400">Videos</div>
                </div>
                <div>
                  <div className="text-lg font-bold">{imageCount}</div>
                  <div className="mt-0.5 text-[11px] text-zinc-400">Photos</div>
                </div>
              </div>
              <button
                type="button"
                className="mt-4 inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-white text-sm font-semibold text-black hover:bg-zinc-200"
                onClick={handlePlayWithMe}
              >
                <MessageCircle className="h-4 w-4" />
                Play with me
              </button>
            </div>
          </div>

          <div className="mt-5">
            <h2 className="text-xl font-heading font-bold">{displayName}</h2>
            {data.personality_summary && (
              <p className="mt-2 text-sm leading-relaxed text-zinc-200">{data.personality_summary}</p>
            )}
            {data.description && (
              <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-zinc-400">{data.description}</p>
            )}
            {tags.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {tags.slice(0, 10).map((tag) => (
                  <span key={tag} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-zinc-200">
                    #{tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </section>

        <nav className="sticky top-[calc(var(--app-safe-area-top)+56px)] z-30 grid grid-cols-3 border-y border-white/10 bg-black/95 backdrop-blur">
          {MEDIA_FILTERS.map(({ id, label, Icon }) => (
            <button
              key={id}
              type="button"
              className={cn(
                'flex h-12 items-center justify-center gap-2 text-xs font-semibold text-zinc-500 transition-colors',
                activeFilter === id && 'border-b-2 border-white text-white'
              )}
              onClick={() => setActiveFilter(id)}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>

        {filteredMediaItems.length > 0 ? (
          <section className="grid grid-cols-3 gap-px bg-black">
            {filteredMediaItems.map((item) => (
              <button
                key={item.id}
                type="button"
                className="group relative aspect-[9/14] overflow-hidden bg-zinc-900 text-left"
                onClick={() => setActiveMedia(item)}
                aria-label={`Open ${item.label}`}
              >
                {item.type === 'video' ? (
                  item.thumbnailUrl ? (
                    <img src={item.thumbnailUrl} alt={item.label} className="h-full w-full object-cover transition-transform group-hover:scale-105" />
                  ) : (
                    <video src={item.url} className="h-full w-full object-cover transition-transform group-hover:scale-105" muted playsInline />
                  )
                ) : (
                  <img src={item.url} alt={item.label} className="h-full w-full object-cover transition-transform group-hover:scale-105" />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-80" />
                <div className="absolute left-2 top-2 inline-flex h-7 w-7 items-center justify-center rounded-full bg-black/55">
                  {item.type === 'video' ? <Play className="h-3.5 w-3.5 fill-white" /> : <ImageIcon className="h-3.5 w-3.5" />}
                </div>
              </button>
            ))}
          </section>
        ) : (
          <section className="flex min-h-[260px] items-center justify-center px-8 text-center">
            <div>
              <Grid3X3 className="mx-auto h-10 w-10 text-zinc-600" />
              <p className="mt-4 text-sm font-semibold text-zinc-300">No media yet</p>
              <p className="mt-1 text-xs text-zinc-500">Photos and videos will appear here when available.</p>
            </div>
          </section>
        )}
      </main>

      {activeMedia && (
        <div className="fixed inset-0 z-50 bg-black text-white" onClick={() => setActiveMedia(null)}>
          <button
            type="button"
            className="absolute right-4 top-[calc(var(--app-safe-area-top)+12px)] z-20 inline-flex h-10 w-10 items-center justify-center rounded-full bg-white/10 hover:bg-white/15"
            onClick={() => setActiveMedia(null)}
            aria-label="Close media"
          >
            <X className="h-5 w-5" />
          </button>
          <div className="flex h-full items-center justify-center" onClick={(event) => event.stopPropagation()}>
            {activeMedia.type === 'video' ? (
              <video
                src={activeMedia.url}
                poster={activeMedia.thumbnailUrl}
                className="h-full max-h-full w-full object-contain"
                autoPlay
                loop
                playsInline
                controls
              />
            ) : (
              <img src={activeMedia.url} alt={activeMedia.label} className="max-h-full w-full object-contain" />
            )}
          </div>
          <div className="pointer-events-none absolute bottom-[calc(var(--app-safe-area-bottom)+20px)] left-4 right-20">
            <p className="text-sm font-semibold">{displayName}</p>
            <p className="mt-1 text-xs text-zinc-300">{activeMedia.label}</p>
          </div>
        </div>
      )}
    </div>
  );
}
