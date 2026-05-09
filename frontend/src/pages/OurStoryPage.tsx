import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { BookOpen, ChevronLeft, Heart, Loader2, Sparkles, Star, Zap } from 'lucide-react';
import { api } from '@/services/api';
import { getSafeAvatarUrl } from '@/utils/avatarUrlGuard';

interface OurStoryData {
  character: { id: string; name: string; avatar_url?: string };
  first_met: string | null;
  days_together: number;
  relationship_stage: string;
  key_memories: { id: string; content: string; layer: string; created_at: string }[];
  milestones: { id: string; milestone_type: string; description: string; occurred_at: string }[];
  generated_stories: { id: string; title: string; cover_image_url?: string; created_at: string }[];
}

const STAGE_LABELS: Record<string, string> = {
  stranger: 'Strangers',
  acquaintance: 'Acquaintances',
  friend: 'Friends',
  close: 'Close Friends',
  intimate: 'Intimate',
  soulmate: 'Soulmates',
};

const STAGE_ORDER = ['stranger', 'acquaintance', 'friend', 'close', 'intimate', 'soulmate'];

const MILESTONE_ICONS: Record<string, { icon: React.ReactNode; color: string }> = {
  first_message: { icon: <Heart size={14} />, color: 'text-pink-400' },
  stage_up: { icon: <Star size={14} />, color: 'text-amber-400' },
  story_created: { icon: <BookOpen size={14} />, color: 'text-primary-400' },
  streak_7day: { icon: <Zap size={14} />, color: 'text-emerald-400' },
  streak_30day: { icon: <Zap size={14} />, color: 'text-emerald-400' },
  streak_100day: { icon: <Sparkles size={14} />, color: 'text-amber-400' },
};

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return iso;
  }
}

export function OurStoryPage() {
  const { characterId } = useParams<{ characterId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<OurStoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!characterId) return;
    const load = async () => {
      try {
        const resp = await api.get<OurStoryData>(`/context/${characterId}/our-story`);
        setData(resp.data);
      } catch {
        setError('Could not load your story. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [characterId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <Loader2 size={32} className="text-primary-400 animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center gap-4 text-zinc-400 p-8 text-center">
        <p>{error || 'Something went wrong.'}</p>
        <button onClick={() => navigate(-1)} className="text-primary-400 text-sm underline">Go back</button>
      </div>
    );
  }

  const stageIndex = STAGE_ORDER.indexOf(data.relationship_stage);
  const stageProgress = stageIndex >= 0 ? ((stageIndex + 1) / STAGE_ORDER.length) * 100 : 0;
  const safeAvatar = getSafeAvatarUrl(data.character.avatar_url);

  return (
    <div className="min-h-screen bg-zinc-950 pb-16">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-zinc-950/90 backdrop-blur border-b border-white/10 px-4 py-3 flex items-center gap-3 pt-safe">
        <button onClick={() => navigate(-1)} className="text-zinc-400 hover:text-white transition-colors">
          <ChevronLeft size={22} />
        </button>
        <h1 className="font-heading font-bold text-white text-base">Our Story</h1>
      </div>

      <div className="max-w-lg mx-auto px-4 pt-6 space-y-6">
        {/* Character card */}
        <div className="rounded-2xl border border-white/10 bg-zinc-900 p-5 flex gap-4 items-center">
          <div className="w-16 h-16 rounded-full overflow-hidden border-2 border-primary-500/40 shrink-0">
            {safeAvatar ? (
              <img src={safeAvatar} alt={data.character.name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full bg-primary-500/20 flex items-center justify-center text-primary-400 font-bold text-xl">
                {data.character.name.charAt(0)}
              </div>
            )}
          </div>
          <div className="min-w-0">
            <p className="font-bold text-white text-lg">{data.character.name}</p>
            {data.days_together > 0 && (
              <p className="text-sm text-zinc-400">Together {data.days_together} day{data.days_together !== 1 ? 's' : ''}</p>
            )}
            {data.first_met && (
              <p className="text-xs text-zinc-500">Since {formatDate(data.first_met)}</p>
            )}
          </div>
        </div>

        {/* Relationship stage */}
        <div className="rounded-2xl border border-white/10 bg-zinc-900 p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-zinc-300">Relationship</span>
            <span className="text-sm font-bold text-primary-300">
              {STAGE_LABELS[data.relationship_stage] ?? data.relationship_stage}
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-zinc-800 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-primary-500 to-primary-400 transition-all duration-700"
              style={{ width: `${stageProgress}%` }}
            />
          </div>
          <div className="mt-2 flex justify-between text-[10px] text-zinc-600">
            <span>Stranger</span>
            <span>Soulmate</span>
          </div>
        </div>

        {/* Timeline */}
        {data.milestones.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">Timeline</h2>
            <div className="relative">
              {/* Vertical line */}
              <div className="absolute left-[19px] top-0 bottom-0 w-px bg-white/10" />

              <div className="space-y-4">
                {data.milestones.map((m) => {
                  const meta = MILESTONE_ICONS[m.milestone_type];
                  return (
                    <div key={m.id} className="flex gap-4 items-start">
                      <div className={`w-10 h-10 rounded-full bg-zinc-900 border border-white/15 flex items-center justify-center shrink-0 ${meta?.color ?? 'text-zinc-400'}`}>
                        {meta?.icon ?? <Star size={14} />}
                      </div>
                      <div className="flex-1 pb-2 min-w-0">
                        <p className="text-sm text-white font-medium leading-tight">{m.description || m.milestone_type}</p>
                        <p className="text-xs text-zinc-500 mt-0.5">{formatDate(m.occurred_at)}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Generated stories */}
        {data.generated_stories.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">Your Stories</h2>
            <div className="space-y-3">
              {data.generated_stories.map((story) => (
                <div
                  key={story.id}
                  className="flex gap-3 items-center rounded-xl border border-white/10 bg-zinc-900 p-3"
                >
                  <div className="w-14 h-14 rounded-lg overflow-hidden shrink-0 bg-zinc-800">
                    {story.cover_image_url ? (
                      <img src={story.cover_image_url} alt={story.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-zinc-600">
                        <BookOpen size={20} />
                      </div>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-white truncate">{story.title}</p>
                    <p className="text-xs text-zinc-500">{formatDate(story.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Key memories */}
        {data.key_memories.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">Key Memories</h2>
            <div className="space-y-2">
              {data.key_memories.map((mem) => (
                <div key={mem.id} className="rounded-xl border border-white/10 bg-zinc-900 px-4 py-3">
                  <p className="text-sm text-zinc-200 leading-relaxed line-clamp-3">{mem.content}</p>
                  <p className="text-[10px] text-zinc-600 mt-1">{formatDate(mem.created_at)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {data.milestones.length === 0 && data.key_memories.length === 0 && (
          <div className="text-center text-zinc-500 text-sm py-8">
            <Heart size={32} className="mx-auto mb-3 text-zinc-700" />
            <p>Your story is just beginning.</p>
            <p className="text-xs mt-1">Chat more to build memories and milestones.</p>
          </div>
        )}
      </div>
    </div>
  );
}
