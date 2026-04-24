import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Loader2 } from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';
import { startOfficialChat } from '@/utils/startOfficialChat';

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
}

function getName(char?: CharacterProfile | null) {
  if (!char) return 'Character';
  return char.first_name || char.name || 'Character';
}

export function DiscoverCharacterProfilePage() {
  const navigate = useNavigate();
  const { characterId } = useParams<{ characterId: string }>();
  const { isAuthenticated } = useAuth();

  const { data, isLoading, isError } = useQuery<CharacterProfile>({
    queryKey: ['discover-character-profile', characterId],
    queryFn: async () => {
      const response = await api.get<CharacterProfile>(`/characters/official/${characterId}`);
      return response.data;
    },
    enabled: Boolean(characterId),
    staleTime: 60 * 1000,
  });

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
      <div className="h-[100dvh] bg-zinc-950 text-white flex items-center justify-center">
        <Loader2 className="w-7 h-7 animate-spin" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="h-[100dvh] bg-zinc-950 text-white flex items-center justify-center px-6">
        <div className="text-center">
          <p className="text-lg font-semibold">Character not found</p>
          <button
            type="button"
            className="mt-4 rounded-lg bg-white/10 px-4 py-2 text-sm hover:bg-white/15"
            onClick={() => navigate('/discover')}
          >
            Back to Discover
          </button>
        </div>
      </div>
    );
  }

  const displayName = getName(data);
  const poster = data.mature_cover_url || data.mature_image_url || data.avatar_url || data.profile_image_url;
  const video = data.mature_video_url || data.preview_video_url;
  const tags = (data.personality_tags?.length ? data.personality_tags : data.tags) || [];

  return (
    <div className="min-h-[100dvh] bg-zinc-950 text-white">
      <div className="relative h-[64vh] min-h-[420px] bg-black">
        {video ? (
          <video
            src={video}
            className="absolute inset-0 w-full h-full object-cover"
            autoPlay
            muted
            loop
            playsInline
          />
        ) : poster ? (
          <img src={poster} alt={displayName} className="absolute inset-0 w-full h-full object-cover" />
        ) : null}
        <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-black/35 to-black/10" />

        <button
          type="button"
          className="absolute top-[calc(var(--app-safe-area-top)+12px)] left-4 inline-flex items-center gap-2 rounded-full bg-black/45 px-3 py-2 text-sm"
          onClick={() => navigate('/discover')}
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        <div className="absolute bottom-6 left-5 right-5">
          <h1 className="text-3xl font-heading font-bold">{displayName}</h1>
          {data.age != null && <p className="mt-1 text-zinc-200">Age {String(data.age)}</p>}
        </div>
      </div>

      <div className="px-5 py-6 max-w-3xl mx-auto">
        {data.personality_summary && (
          <p className="text-zinc-200 leading-relaxed">{data.personality_summary}</p>
        )}
        {data.description && (
          <p className="mt-3 text-zinc-300 leading-relaxed">{data.description}</p>
        )}
        {tags.length > 0 && (
          <div className="mt-5 flex flex-wrap gap-2">
            {tags.slice(0, 12).map((tag) => (
              <span key={tag} className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs text-zinc-200">
                {tag}
              </span>
            ))}
          </div>
        )}

        <button
          type="button"
          className="mt-8 w-full sm:w-auto rounded-xl bg-pink-500 px-8 py-3 text-sm font-semibold hover:bg-pink-400 transition-colors"
          onClick={handlePlayWithMe}
        >
          Play with me
        </button>
      </div>
    </div>
  );
}
