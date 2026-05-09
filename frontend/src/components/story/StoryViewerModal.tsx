import { useEffect, useState } from 'react';
import { BookOpen, ChevronRight, Loader2, Play, X } from 'lucide-react';
import { api, startStory } from '@/services/api';
import { notificationService } from '@/services/notificationService';
import { cn } from '@/utils/cn';

interface StoryNode {
  id: string;
  node_type: 'scene' | 'ending';
  title?: string;
  narrative?: string;
  choices?: { id: string; text: string }[];
}

interface StoryViewerModalProps {
  characterName: string;
  characterAvatar?: string;
  sessionId: string;
  characterId: string;
  scriptId?: string;
  onClose: () => void;
  onStoryModeStarted?: () => void;
}

export function StoryViewerModal({
  characterName,
  characterAvatar,
  sessionId,
  scriptId: initialScriptId,
  onClose,
  onStoryModeStarted,
}: StoryViewerModalProps) {
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [isStartingMode, setIsStartingMode] = useState(false);
  const [scriptId, setScriptId] = useState<string | null>(initialScriptId ?? null);
  const [coverUrl, setCoverUrl] = useState<string | null>(null);
  const [storyTitle, setStoryTitle] = useState('');
  const [nodes, setNodes] = useState<StoryNode[]>([]);
  const [currentNodeIndex, setCurrentNodeIndex] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let pollInterval: ReturnType<typeof setInterval> | undefined;

    const loadScript = async (sid: string) => {
      if (cancelled) return false;
      try {
        const scriptResp = await api.get<{ title?: string; cover_image_url?: string }>(`/scripts/${sid}`);
        setScriptId(sid);
        setStoryTitle(scriptResp.data?.title || 'Your Story');
        if (scriptResp.data?.cover_image_url) setCoverUrl(scriptResp.data.cover_image_url);

        const nodesResp = await api.get<{ nodes: StoryNode[] }>(`/scripts/${sid}/nodes`);
        const rawNodes = nodesResp.data?.nodes || [];
        if (rawNodes.length === 0) return false;
        setNodes(rawNodes);
        setStatus('ready');
        return true;
      } catch {
        return false;
      }
    };

    const check = async () => {
      if (initialScriptId && await loadScript(initialScriptId)) return true;

      const resp = await api.get<{ items: { id: string }[] }>(
        `/scripts?source_session_id=${encodeURIComponent(sessionId)}&limit=1`,
      );
      const item = resp.data?.items?.[0];
      return Boolean(item?.id && await loadScript(item.id));
    };

    const cutoff = Date.now() + 120_000;
    const poll = async () => {
      if (cancelled) return;
      if (Date.now() > cutoff) {
        setStatus('error');
        if (pollInterval) clearInterval(pollInterval);
        return;
      }
      try {
        if (await check()) {
          if (pollInterval) clearInterval(pollInterval);
        }
      } catch {
        // Keep polling until the generation task finishes or times out.
      }
    };

    const unsubscribe = notificationService.on('story_generated', (event) => {
      if (event.session_id !== sessionId) return;
      if (event.status === 'failed') {
        setStatus('error');
        return;
      }
      void loadScript(event.script_id);
    });

    void poll();
    pollInterval = setInterval(poll, 4000);

    return () => {
      cancelled = true;
      if (pollInterval) clearInterval(pollInterval);
      unsubscribe();
    };
  }, [initialScriptId, sessionId]);

  const currentNode = nodes[currentNodeIndex];
  const isEnding = currentNode?.node_type === 'ending';
  const progress = nodes.length > 0 ? ((currentNodeIndex + 1) / nodes.length) * 100 : 0;

  const handleChoice = () => {
    const nextIndex = currentNodeIndex + 1;
    if (nextIndex < nodes.length) {
      setCurrentNodeIndex(nextIndex);
    }
  };

  const handleNext = () => {
    const nextIndex = currentNodeIndex + 1;
    if (nextIndex < nodes.length) setCurrentNodeIndex(nextIndex);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />

      <div className="relative flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden rounded-t-2xl border border-white/10 bg-zinc-950 shadow-2xl sm:rounded-2xl">
        <div className="relative h-48 flex-shrink-0 overflow-hidden bg-zinc-900 sm:h-56">
          {coverUrl ? (
            <img src={coverUrl} alt="Story cover" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center">
              {characterAvatar ? (
                <img
                  src={characterAvatar}
                  alt={characterName}
                  className="h-full w-full object-cover opacity-40"
                />
              ) : (
                <BookOpen size={48} className="text-zinc-700" />
              )}
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/40 to-transparent" />

          <button
            onClick={onClose}
            className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-black/50 text-zinc-300 backdrop-blur hover:text-white"
            aria-label="Close story"
          >
            <X size={16} />
          </button>

          <div className="absolute bottom-3 left-4 right-4">
            <p className="mb-1 text-xs text-primary-400">{characterName} & You</p>
            <h2 className="line-clamp-2 text-lg font-bold leading-tight text-white">
              {storyTitle || 'Crafting your story...'}
            </h2>
            {scriptId && <p className="mt-1 text-[10px] text-zinc-500">{scriptId}</p>}
          </div>
        </div>

        {status === 'ready' && (
          <div className="h-0.5 flex-shrink-0 bg-zinc-800">
            <div
              className="h-full bg-primary-500 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          {status === 'loading' && (
            <div className="flex flex-col items-center justify-center gap-4 py-12">
              <Loader2 size={32} className="animate-spin text-primary-400" />
              <p className="text-center text-sm text-zinc-400">
                AI is writing your story...
                <br />
                <span className="text-xs text-zinc-500">This usually takes about 30 seconds</span>
              </p>
            </div>
          )}

          {status === 'error' && (
            <div className="flex flex-col items-center justify-center gap-3 py-12">
              <p className="text-center text-sm text-zinc-400">
                Story generation timed out. Please try again.
              </p>
              <button onClick={onClose} className="text-sm text-primary-400 underline">
                Close
              </button>
            </div>
          )}

          {status === 'ready' && currentNode && (
            <div>
              {currentNode.title && (
                <h3 className="mb-3 text-base font-semibold text-white">{currentNode.title}</h3>
              )}
              <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-300 sm:text-base">
                {currentNode.narrative}
              </p>
            </div>
          )}
        </div>

        {status === 'ready' && currentNode && (
          <div className="flex-shrink-0 space-y-2 border-t border-white/10 p-4">
            {/* Begin in Chat — bind story to session for character-led mode */}
            {onStoryModeStarted && currentNodeIndex === 0 && !isEnding && scriptId && (
              <button
                onClick={async () => {
                  setIsStartingMode(true);
                  try {
                    await startStory(sessionId, scriptId);
                    onStoryModeStarted();
                    onClose();
                  } catch {
                    setIsStartingMode(false);
                  }
                }}
                disabled={isStartingMode}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-purple-600 py-3 text-sm font-semibold text-white transition-all hover:bg-purple-500 disabled:opacity-60"
              >
                {isStartingMode ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                {isStartingMode ? 'Starting…' : 'Begin in Chat'}
              </button>
            )}

            {!isEnding && currentNode.choices && currentNode.choices.length > 0 ? (
              currentNode.choices.map((choice, i) => (
                <button
                  key={choice.id}
                  onClick={handleChoice}
                  className="min-h-[48px] w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-left text-sm text-zinc-200 transition-all hover:border-primary-400/60 hover:bg-primary-500/20 hover:text-white"
                >
                  <span className="inline-flex items-center gap-2.5">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary-500/20 text-xs font-semibold text-primary-400">
                      {i + 1}
                    </span>
                    {choice.text}
                  </span>
                </button>
              ))
            ) : isEnding ? (
              <div className="space-y-3 text-center">
                <p className="text-sm font-medium text-primary-400">The End</p>
                <button
                  onClick={onClose}
                  className="w-full rounded-xl bg-primary-500 py-3 text-sm font-semibold text-white transition-all hover:bg-primary-600"
                >
                  Close Story
                </button>
              </div>
            ) : (
              <button
                onClick={handleNext}
                className={cn(
                  'flex w-full items-center justify-center gap-2 rounded-xl border border-white/10 py-3 text-sm text-zinc-300 transition-all',
                  'hover:bg-white/5 hover:text-white',
                )}
              >
                Continue <ChevronRight size={16} />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
