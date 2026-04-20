import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Copy,
  Loader2,
  Play,
  Sparkles,
  Video,
  Wand2,
  X,
} from 'lucide-react';

import { api } from '@/services/api';
import { notificationService } from '@/services/notificationService';
import { InsufficientCreditsModal } from '@/components/chat/InsufficientCreditsModal';
import { VideoLoraSelector } from '@/components/video/VideoLoraSelector';
import { ImageLoraSelector } from '@/components/image/ImageLoraSelector';
import { HUNYUAN_VIDEO_LORAS, type HunyuanVideoLoRA } from '@/config/hunyuanVideoLoras';
import { type ImageGenerationLoRA } from '@/config/imageGenerationLoras';
import { getErrorMessage, getInsufficientCreditsInfo } from '@/utils/apiError';
import { RoxyShellLayout } from '@/components/layout';
import type { Character } from '@/types';

interface CharacterLike {
  id: string;
  name?: string;
  first_name?: string;
  age?: number | string;
  images?: string[];
  profile_image_url?: string;
  avatar_url?: string;
  media_urls?: {
    avatar?: string;
  };
}

interface SuggestionCategory {
  id: string;
  label: string;
  prompts: string[];
}

const SUGGESTION_CATEGORIES: SuggestionCategory[] = [
  {
    id: 'outfit',
    label: 'Outfit',
    prompts: [
      'wearing a red bikini',
      'wearing a satin robe',
      'wearing a leather mini-dress',
      'wearing a cropped top and skirt',
      'wearing elegant evening dress',
      'wearing a sheer white blouse',
      'wearing a tight bodycon dress',
      'wearing a school uniform',
      'wearing a maid outfit',
      'wearing a lace lingerie set',
    ],
  },
  {
    id: 'action',
    label: 'Action',
    prompts: [
      'leaning against a sports car',
      'walking under city neon lights',
      'holding a coffee cup and smiling',
      'taking a mirror selfie',
      'turning around with playful eye contact',
      'lying on a bed with a smile',
      'dancing gracefully',
      'stretching with arms above head',
      'applying lipstick in a mirror',
      'looking seductively at camera',
    ],
  },
  {
    id: 'pose',
    label: 'Pose',
    prompts: [
      'full body portrait',
      'close-up portrait',
      'looking over shoulder',
      'sitting with crossed legs',
      'hands on waist confident pose',
      'arching back gently',
      'kneeling gracefully',
      'lying down side view',
      'leaning forward with arms on knees',
      'standing back to camera glancing back',
    ],
  },
  {
    id: 'scene',
    label: 'Scene',
    prompts: [
      'at sunset beach',
      'inside modern apartment',
      'in luxury hotel lobby',
      'on rooftop at night',
      'in a cozy cafe',
      'in a bubble bath',
      'in a dimly lit bedroom',
      'poolside in sunlight',
      'in a flower field',
      'in a neon-lit nightclub',
    ],
  },
  {
    id: 'style',
    label: 'Style',
    prompts: [
      'photorealistic, 8K detail',
      'soft cinematic lighting',
      'golden hour warm glow',
      'dramatic studio lighting',
      'moody dark aesthetic',
      'dreamy soft focus',
      'high contrast vivid colors',
      'vintage film grain',
      'anime illustration style',
      'oil painting style',
    ],
  },
];

function getCharacterName(character: CharacterLike): string {
  return character.first_name || character.name || 'Character';
}

function getCharacterImage(character: CharacterLike): string {
  return (
    character.images?.[0] ||
    character.media_urls?.avatar ||
    character.avatar_url ||
    character.profile_image_url ||
    ''
  );
}

function buildPrompt(name: string, picks: string[]): string {
  const suffix = picks.join(', ');
  return `${name}, ${suffix}, photorealistic, high detail, cinematic lighting`;
}

function getRandomItem<T>(items: T[]): T {
  return items[Math.floor(Math.random() * items.length)];
}

interface AnimateState {
  showPrompt: boolean;
  prompt: string;
  isAnimating: boolean;
  taskId: string | null;
  videoUrl: string | null;
  error: string | null;
}

interface PersistedAnimateTask {
  taskId: string;
  imageUrl: string;
  animPrompt: string;
  characterId: string | undefined;
}

const DEFAULT_ANIMATE_PROMPT = 'smiling gently, hair flowing in breeze, smooth natural motion';

interface PosePreset {
  id: string;
  label: string;
  thumbnailUrl: string;
}

// TODO: Replace thumbnailUrl values with your actual pose reference image URLs
const POSE_PRESETS: PosePreset[] = [
  { id: 'standing', label: 'Standing', thumbnailUrl: '' },
  { id: 'sitting', label: 'Sitting', thumbnailUrl: '' },
  { id: 'kneeling', label: 'Kneeling', thumbnailUrl: '' },
  { id: 'lying_side', label: 'Lying Side', thumbnailUrl: '' },
  { id: 'lean_back', label: 'Lean Back', thumbnailUrl: '' },
  { id: 'bend_forward', label: 'Bend Forward', thumbnailUrl: '' },
  { id: 'on_all_fours', label: 'On All Fours', thumbnailUrl: '' },
  { id: 'seated_spread', label: 'Seated Spread', thumbnailUrl: '' },
];
const POLL_INTERVAL_MS = 4000;
const POLL_MAX_ATTEMPTS = 120;
const STORAGE_KEY = 'roxy_pending_animate_tasks';
const HUNYUAN_STORAGE_KEY = 'roxy_pending_hunyuan_tasks';

interface HunyuanVideoState {
  isGenerating: boolean;
  taskId: string | null;
  videoUrl: string | null;
  error: string | null;
}

interface PersistedHunyuanTask {
  taskId: string;
  characterId: string | undefined;
  prompt: string;
  loraId: string | undefined;
}

function loadPersistedHunyuanTasks(): PersistedHunyuanTask[] {
  try {
    const raw = localStorage.getItem(HUNYUAN_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as PersistedHunyuanTask[]) : [];
  } catch {
    return [];
  }
}

function savePersistedHunyuanTask(task: PersistedHunyuanTask): void {
  const tasks = loadPersistedHunyuanTasks().filter((t) => t.taskId !== task.taskId);
  localStorage.setItem(HUNYUAN_STORAGE_KEY, JSON.stringify([...tasks, task]));
}

function removePersistedHunyuanTask(taskId: string): void {
  const tasks = loadPersistedHunyuanTasks().filter((t) => t.taskId !== taskId);
  localStorage.setItem(HUNYUAN_STORAGE_KEY, JSON.stringify(tasks));
}

function loadPersistedTasks(): PersistedAnimateTask[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as PersistedAnimateTask[];
  } catch {
    return [];
  }
}

function savePersistedTask(task: PersistedAnimateTask): void {
  const tasks = loadPersistedTasks().filter((t) => t.taskId !== task.taskId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...tasks, task]));
}

function removePersistedTask(taskId: string): void {
  const tasks = loadPersistedTasks().filter((t) => t.taskId !== taskId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
}

export function GenerateImageComposerPage() {
  const navigate = useNavigate();
  const { characterId } = useParams<{ characterId: string }>();
  const [character, setCharacter] = useState<CharacterLike | null>(null);
  const [isLoadingCharacter, setIsLoadingCharacter] = useState(true);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>(SUGGESTION_CATEGORIES[0].id);
  const [prompt, setPrompt] = useState('');
  const [numImages, setNumImages] = useState(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImages, setGeneratedImages] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [insufficientCreditsState, setInsufficientCreditsState] = useState<{
    isOpen: boolean;
    required?: number;
    available?: number;
  }>({ isOpen: false });
  const [selectedPoseId, setSelectedPoseId] = useState<string | null>(null);
  const [animateStates, setAnimateStates] = useState<Record<string, AnimateState>>({});
  const pollTimers = useRef<Record<string, ReturnType<typeof setInterval>>>({});

  // Image LoRA selection
  const [selectedImageLora, setSelectedImageLora] = useState<ImageGenerationLoRA | null>(null);

  // Hunyuan video state
  const [selectedLora, setSelectedLora] = useState<HunyuanVideoLoRA | null>(null);
  const [hunyuanPrompt, setHunyuanPrompt] = useState('');
  const [hunyuanState, setHunyuanState] = useState<HunyuanVideoState>({
    isGenerating: false,
    taskId: null,
    videoUrl: null,
    error: null,
  });
  const hunyuanPollTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const activeCategory = useMemo(
    () => SUGGESTION_CATEGORIES.find((category) => category.id === selectedCategoryId) || SUGGESTION_CATEGORIES[0],
    [selectedCategoryId]
  );

  const characterName = character ? getCharacterName(character) : 'Character';
  const characterImage = character ? getCharacterImage(character) : '';

  useEffect(() => {
    // This page relies on SSE image_done/image_failed notifications.
    // Ensure the notification stream is connected even when user enters
    // Generate Image directly (without visiting Chat first).
    if (!notificationService.isConnected()) {
      void notificationService.connect();
    }
  }, []);

  useEffect(() => {
    const fetchCharacter = async () => {
      if (!characterId) {
        setIsLoadingCharacter(false);
        return;
      }
      setIsLoadingCharacter(true);
      try {
        let matched: CharacterLike | null = null;
        try {
          const myResponse = await api.get<Character>(`/characters/${characterId}`);
          matched = myResponse.data;
        } catch (myErr: unknown) {
          const status = (myErr as { response?: { status?: number } })?.response?.status;
          if (status !== 404) {
            throw myErr;
          }
          const officialResponse = await api.get<CharacterLike>(`/characters/official/${characterId}`);
          matched = officialResponse.data;
        }

        setCharacter(matched);
        if (matched) {
          const defaults = [
            getRandomItem(SUGGESTION_CATEGORIES[0].prompts),
            getRandomItem(SUGGESTION_CATEGORIES[1].prompts),
            getRandomItem(SUGGESTION_CATEGORIES[2].prompts),
            getRandomItem(SUGGESTION_CATEGORIES[3].prompts),
          ];
          setPrompt(buildPrompt(getCharacterName(matched), defaults));
        }
      } catch (fetchError) {
        console.error('Failed to fetch character for image generator:', fetchError);
        setCharacter(null);
      } finally {
        setIsLoadingCharacter(false);
      }
    };

    fetchCharacter();
  }, [characterId]);

  // Clean up all polling timers on unmount
  useEffect(() => {
    const timers = pollTimers.current;
    const hunyuanTimer = hunyuanPollTimer;
    return () => {
      Object.values(timers).forEach(clearInterval);
      if (hunyuanTimer.current) clearInterval(hunyuanTimer.current);
    };
  }, []);

  const stopPolling = useCallback((imageUrl: string) => {
    if (pollTimers.current[imageUrl]) {
      clearInterval(pollTimers.current[imageUrl]);
      delete pollTimers.current[imageUrl];
    }
  }, []);

  const setAnimateState = useCallback((imageUrl: string, patch: Partial<AnimateState>) => {
    setAnimateStates((prev) => ({
      ...prev,
      [imageUrl]: {
        ...(prev[imageUrl] ?? {
          showPrompt: false,
          prompt: DEFAULT_ANIMATE_PROMPT,
          isAnimating: false,
          taskId: null,
          videoUrl: null,
          error: null,
        }),
        ...patch,
      },
    }));
  }, []);

  const startPolling = useCallback((imageUrl: string, taskId: string) => {
    let attempts = 0;
    pollTimers.current[imageUrl] = setInterval(async () => {
      attempts += 1;
      if (attempts > POLL_MAX_ATTEMPTS) {
        stopPolling(imageUrl);
        setAnimateState(imageUrl, { isAnimating: false, error: 'Video generation timed out.' });
        removePersistedTask(taskId);
        return;
      }
      try {
        const res = await api.get(`/images/tasks/${taskId}`);
        const data = res.data as { status?: string; result?: { data?: string; video_url?: string } };
        const status = data.status;
        if (status === 'succeeded') {
          stopPolling(imageUrl);
          const videoUrl = data.result?.data || data.result?.video_url || null;
          setAnimateState(imageUrl, { isAnimating: false, videoUrl });
          removePersistedTask(taskId);
        } else if (status === 'failed') {
          stopPolling(imageUrl);
          setAnimateState(imageUrl, { isAnimating: false, error: 'Video generation failed.' });
          removePersistedTask(taskId);
        }
      } catch (pollErr) {
        console.error('Polling error:', pollErr);
      }
    }, POLL_INTERVAL_MS);
  }, [setAnimateState, stopPolling]);

  // Resume polling for any tasks that were pending before a page refresh
  useEffect(() => {
    const persisted = loadPersistedTasks();
    if (persisted.length === 0) return;
    persisted.forEach((task) => {
      setAnimateState(task.imageUrl, {
        isAnimating: true,
        taskId: task.taskId,
        prompt: task.animPrompt,
        showPrompt: false,
        error: null,
        videoUrl: null,
      });
      startPolling(task.imageUrl, task.taskId);
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startHunyuanPolling = useCallback((taskId: string) => {
    let attempts = 0;
    hunyuanPollTimer.current = setInterval(async () => {
      attempts += 1;
      if (attempts > POLL_MAX_ATTEMPTS) {
        if (hunyuanPollTimer.current) clearInterval(hunyuanPollTimer.current);
        setHunyuanState((prev) => ({ ...prev, isGenerating: false, error: 'Video generation timed out.' }));
        removePersistedHunyuanTask(taskId);
        return;
      }
      try {
        const res = await api.get(`/images/tasks/${taskId}`);
        const data = res.data as { status?: string; result?: { data?: string; video_url?: string } };
        if (data.status === 'succeeded') {
          if (hunyuanPollTimer.current) clearInterval(hunyuanPollTimer.current);
          const url = data.result?.video_url || data.result?.data || null;
          setHunyuanState({ isGenerating: false, taskId, videoUrl: url, error: null });
          removePersistedHunyuanTask(taskId);
        } else if (data.status === 'failed') {
          if (hunyuanPollTimer.current) clearInterval(hunyuanPollTimer.current);
          setHunyuanState((prev) => ({ ...prev, isGenerating: false, error: 'Video generation failed.' }));
          removePersistedHunyuanTask(taskId);
        }
      } catch {
        // Network hiccup — keep polling
      }
    }, POLL_INTERVAL_MS);
  }, []);

  // Resume Hunyuan task after page refresh (断点轮询)
  useEffect(() => {
    const persisted = loadPersistedHunyuanTasks();
    if (persisted.length === 0) return;
    // Resume the most recent pending task for this character
    const mine = characterId
      ? persisted.filter((t) => t.characterId === characterId)
      : persisted;
    if (mine.length === 0) return;
    const task = mine[mine.length - 1];
    const lora = HUNYUAN_VIDEO_LORAS.find((l) => l.id === task.loraId) ?? null;
    setSelectedLora(lora);
    setHunyuanPrompt(task.prompt);
    setHunyuanState({ isGenerating: true, taskId: task.taskId, videoUrl: null, error: null });
    startHunyuanPolling(task.taskId);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const applySuggestion = (value: string) => {
    setPrompt((prev) => {
      if (!prev.trim()) return buildPrompt(characterName, [value]);
      if (prev.toLowerCase().includes(value.toLowerCase())) return prev;
      return `${prev.replace(/\s+$/, '')}, ${value}`;
    });
  };

  const suggestWithAi = () => {
    const picks = SUGGESTION_CATEGORIES.map((category) => getRandomItem(category.prompts));
    setPrompt(buildPrompt(characterName, picks));
  };

  const copyPrompt = async () => {
    if (!prompt.trim()) return;
    try {
      await navigator.clipboard.writeText(prompt);
    } catch (copyError) {
      console.error('Failed to copy prompt:', copyError);
    }
  };

  const generateImages = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt first.');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      if (!notificationService.isConnected()) {
        await notificationService.connect();
      }

      // Submit all tasks and collect task_ids immediately (no blocking wait).
      // Priority: pose preset → OpenPose+InstantID; otherwise → Novita img2img+LoRA.
      const selectedPose = POSE_PRESETS.find((p) => p.id === selectedPoseId);
      const taskResponses = await Promise.all(
        Array.from({ length: numImages }, () => {
          if (selectedPose?.thumbnailUrl) {
            return api.post<{ task_id: string; status: string }>('/images/generate-pose-mature', {
              prompt,
              character_id: characterId,
              pose_image_url: selectedPose.thumbnailUrl,
            });
          }
          return api.post<{ task_id: string; status: string }>('/images/generate-mature-lora', {
            prompt,
            character_id: characterId,
            lora_id: selectedImageLora?.id ?? null,
          });
        })
      );
      const taskIds = taskResponses.map((r) => r.data.task_id);

      // Primary: SSE notification. Backup: HTTP polling every 5 s. Timeout: 6 min.
      const TIMEOUT_MS = 360_000;
      const waitForImage = (taskId: string): Promise<string> =>
        new Promise((resolve, reject) => {
          let settled = false;

          const cleanup = () => {
            settled = true;
            unsubDone();
            unsubFailed();
            clearInterval(pollInterval);
            clearTimeout(timer);
          };

          const timer = setTimeout(() => {
            if (!settled) {
              cleanup();
              reject(new Error('Timed out waiting for image'));
            }
          }, TIMEOUT_MS);

          const unsubDone = notificationService.on('image_done', (data) => {
            if (data.message_id !== taskId || settled) return;
            cleanup();
            resolve(data.image_url);
          });

          const unsubFailed = notificationService.on('image_failed', (data) => {
            if (data.task_id !== taskId || settled) return;
            cleanup();
            reject(new Error(data.error || 'Image generation failed'));
          });

          const pollInterval = setInterval(async () => {
            if (settled) return;
            try {
              const res = await api.get<{ status: string; result?: { data?: string } }>(
                `/images/tasks/${taskId}`
              );
              const { status, result } = res.data;
              if (status === 'succeeded' && result?.data) {
                cleanup();
                resolve(result.data);
              } else if (status === 'failed') {
                cleanup();
                reject(new Error('Image generation failed'));
              }
            } catch {
              // Ignore poll errors
            }
          }, 5000);
        });

      const settled = await Promise.allSettled(taskIds.map(waitForImage));
      const urls = settled
        .filter((r): r is PromiseFulfilledResult<string> => r.status === 'fulfilled')
        .map((r) => r.value);

      if (urls.length === 0) {
        setError('No image returned. Try another prompt.');
        setGeneratedImages([]);
        return;
      }
      setGeneratedImages(urls);

      // Save generated images to collection (fire-and-forget)
      api.post('/images/save-media', {
        image_urls: urls,
        character_id: characterId || null,
        character_name: characterName,
        prompt,
      }).catch((err) => console.warn('save-media failed (non-blocking):', err));

    } catch (generateError) {
      console.error('Failed to generate images:', generateError);
      const insufficientCredits = getInsufficientCreditsInfo(generateError);
      if (insufficientCredits) {
        setInsufficientCreditsState({
          isOpen: true,
          required: insufficientCredits.required,
          available: insufficientCredits.available,
        });
      }
      setError(getErrorMessage(generateError, 'Generate failed. Please retry.'));
      setGeneratedImages([]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleImageLoraSelect = (lora: ImageGenerationLoRA | null) => {
    setSelectedImageLora(lora);
    if (!lora) return;
    setPrompt((prev) => {
      if (prev.includes(lora.triggerWord)) return prev;
      return prev.trim() ? `${lora.triggerWord}, ${prev}` : lora.triggerWord + ', ';
    });
  };

  const handleLoraSelect = (lora: HunyuanVideoLoRA | null) => {
    setSelectedLora(lora);
    if (!lora) return;
    setHunyuanPrompt(lora.defaultPrompt);
  };

  const handleGenerateHunyuanVideo = async () => {
    if (!hunyuanPrompt.trim()) return;

    setHunyuanState({ isGenerating: true, taskId: null, videoUrl: null, error: null });

    try {
      const loras = selectedLora
        ? [{ path: selectedLora.civitaiId, scale: selectedLora.defaultStrength }]
        : [];

      const res = await api.post<{ task_id: string }>('/images/generate-video-wan-character', {
        prompt: hunyuanPrompt.trim(),
        character_id: characterId || null,
        image_url: characterImage || null,
        loras,
      });

      const { task_id } = res.data;
      setHunyuanState((prev) => ({ ...prev, taskId: task_id }));
      savePersistedHunyuanTask({
        taskId: task_id,
        characterId,
        prompt: hunyuanPrompt.trim(),
        loraId: selectedLora?.id,
      });
      startHunyuanPolling(task_id);
    } catch (err: unknown) {
      const insufficientCredits = getInsufficientCreditsInfo(err);
      if (insufficientCredits) {
        setInsufficientCreditsState({
          isOpen: true,
          required: insufficientCredits.required,
          available: insufficientCredits.available,
        });
      }
      setHunyuanState({
        isGenerating: false,
        taskId: null,
        videoUrl: null,
        error: getErrorMessage(err, 'Video generation failed.'),
      });
    }
  };

  const handleAnimate = useCallback(async (imageUrl: string, animPrompt: string) => {
    setAnimateState(imageUrl, { showPrompt: false, isAnimating: true, error: null, videoUrl: null, taskId: null });
    try {
      const res = await api.post('/images/animate-standalone', {
        image_url: imageUrl,
        character_id: characterId || null,
        prompt: animPrompt,
      });
      const { task_id } = res.data as { task_id: string };
      setAnimateState(imageUrl, { taskId: task_id });
      savePersistedTask({ taskId: task_id, imageUrl, animPrompt, characterId });
      startPolling(imageUrl, task_id);
    } catch (err: unknown) {
      const insufficientCredits = getInsufficientCreditsInfo(err);
      if (insufficientCredits) {
        setInsufficientCreditsState({
          isOpen: true,
          required: insufficientCredits.required,
          available: insufficientCredits.available,
        });
      }
      const msg = insufficientCredits
        ? (insufficientCredits.message || 'Insufficient credits for video generation.')
        : 'Failed to start video generation.';
      setAnimateState(imageUrl, { isAnimating: false, error: msg });
    }
  }, [characterId, setAnimateState, startPolling]);

  if (isLoadingCharacter) {
    return (
      <RoxyShellLayout contentClassName="max-w-[900px]">
        <div className="rounded-2xl border border-white/10 bg-black/30 px-8 py-14 text-center text-zinc-400">
          <Loader2 className="mx-auto mb-3 h-8 w-8 animate-spin" />
          Loading...
        </div>
      </RoxyShellLayout>
    );
  }

  if (!character) {
    return (
      <RoxyShellLayout contentClassName="max-w-[900px]">
        <div className="mx-auto max-w-md rounded-2xl border border-white/10 bg-black/40 p-6 text-center">
          <h1 className="text-xl font-bold">Character not found</h1>
          <p className="mt-2 text-sm text-zinc-400">Please go back and choose another character.</p>
          <button
            onClick={() => navigate('/generate-image')}
            className="mt-4 rounded-xl border border-white/15 bg-white/5 px-4 py-2 text-sm hover:bg-white/10"
          >
            Back to character list
          </button>
        </div>
      </RoxyShellLayout>
    );
  }

  return (
    <RoxyShellLayout contentClassName="max-w-[900px] p-4 md:p-8">
      <div>
          <div className="mb-5 flex items-center gap-2 text-2xl font-bold">
            <Sparkles className="h-6 w-6 text-pink-300" />
            Generate Image
          </div>

          <div className="grid grid-cols-1 md:grid-cols-[210px_1fr] gap-4">
            <div className="relative h-[260px] overflow-hidden rounded-2xl border border-white/10">
              {characterImage ? (
                <img src={characterImage} alt={characterName} className="h-full w-full object-cover" />
              ) : (
                <div className="h-full w-full bg-zinc-900" />
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
              <div className="absolute bottom-3 left-3 right-3 text-lg font-bold">{characterName}</div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-4">
              <div className="mb-3 flex items-center justify-between">
                <button
                  onClick={suggestWithAi}
                  className="inline-flex items-center gap-2 rounded-lg border border-indigo-400/50 bg-indigo-500/15 px-3 py-1.5 text-sm font-semibold text-indigo-200 hover:bg-indigo-500/25"
                >
                  <Wand2 className="h-4 w-4" />
                  AI Suggest Prompt
                </button>
                <button
                  onClick={copyPrompt}
                  className="inline-flex items-center gap-1 rounded-lg border border-white/15 bg-white/5 px-2.5 py-1.5 text-xs text-zinc-300 hover:bg-white/10"
                >
                  <Copy className="h-3.5 w-3.5" />
                  Copy
                </button>
              </div>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe the scene you want..."
                className="h-[198px] w-full resize-none rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white outline-none focus:border-pink-400/50"
              />
            </div>
          </div>

          <div className="mt-6">
            <div className="mb-3 text-lg font-bold">Suggestions</div>
            <div className="mb-3 flex flex-wrap items-center gap-2">
              {SUGGESTION_CATEGORIES.map((category) => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategoryId(category.id)}
                  className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                    selectedCategoryId === category.id
                      ? 'border-indigo-400/60 bg-indigo-500/15 text-indigo-200'
                      : 'border-white/10 bg-white/5 text-zinc-300 hover:bg-white/10'
                  }`}
                >
                  {category.label}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              {activeCategory.prompts.map((item) => (
                <button
                  key={item}
                  onClick={() => applySuggestion(item)}
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-zinc-200 hover:border-white/25 hover:bg-white/10 hover:text-white transition-colors"
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6">
            <div className="mb-3 flex items-center justify-between">
              <div className="text-lg font-bold">Pose Reference</div>
              {selectedPoseId && (
                <button
                  onClick={() => setSelectedPoseId(null)}
                  className="text-xs text-zinc-400 hover:text-white transition-colors"
                >
                  Clear pose
                </button>
              )}
            </div>
            <p className="mb-3 text-xs text-zinc-500">
              Select a pose to generate with InstantID face lock (MATURE). Leave unselected for standard generation.
            </p>
            <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-white/10">
              {POSE_PRESETS.map((pose) => (
                <button
                  key={pose.id}
                  onClick={() => setSelectedPoseId((prev) => (prev === pose.id ? null : pose.id))}
                  className={`flex-shrink-0 flex flex-col items-center gap-1.5 rounded-xl border p-1.5 transition-colors ${
                    selectedPoseId === pose.id
                      ? 'border-pink-400/70 bg-pink-500/15'
                      : 'border-white/10 bg-white/5 hover:border-white/25 hover:bg-white/10'
                  }`}
                >
                  <div className="h-20 w-16 overflow-hidden rounded-lg bg-zinc-800">
                    {pose.thumbnailUrl ? (
                      <img
                        src={pose.thumbnailUrl}
                        alt={pose.label}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-[10px] text-zinc-600">
                        No image
                      </div>
                    )}
                  </div>
                  <span className="text-[11px] text-zinc-300">{pose.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* LoRA selector */}
          <div className="mt-6">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-lg font-bold">Style / Position LoRA</span>
              {selectedImageLora && (
                <button
                  type="button"
                  onClick={() => setSelectedImageLora(null)}
                  className="text-xs text-zinc-400 hover:text-white transition-colors"
                >
                  Clear
                </button>
              )}
            </div>
            <ImageLoraSelector
              selectedId={selectedImageLora?.id ?? null}
              onSelect={handleImageLoraSelect}
              variant="full"
            />
          </div>

          <div className="mt-6">
            <div className="mb-3 text-lg font-bold">Number of images</div>
            <div className="grid grid-cols-4 gap-3">
              {[1, 4, 8, 16].map((count) => (
                <button
                  key={count}
                  onClick={() => setNumImages(count)}
                  className={`rounded-lg border py-2 font-semibold transition-colors ${
                    numImages === count
                      ? 'border-indigo-400/60 bg-indigo-500/15 text-indigo-100'
                      : 'border-white/10 bg-white/5 text-zinc-300 hover:bg-white/10'
                  }`}
                >
                  {count}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={generateImages}
            disabled={isGenerating}
            className="mt-6 w-full rounded-xl bg-gradient-to-r from-indigo-500 to-pink-500 px-4 py-3 text-lg font-bold disabled:opacity-60"
          >
            {isGenerating ? 'Generating...' : 'Generate Image'}
          </button>

          {error && <div className="mt-3 text-sm text-red-300">{error}</div>}

          {/* ==================== Shoot Video (Hunyuan) ==================== */}
          <div className="mt-10 rounded-2xl border border-violet-500/20 bg-violet-500/5 p-5">
            <div className="mb-4 flex items-center gap-2">
              <Video className="h-5 w-5 text-violet-300" />
              <h2 className="text-lg font-bold text-violet-100">Shoot Video</h2>
              <span className="rounded-full bg-violet-500/20 px-2 py-0.5 text-[11px] text-violet-300 font-medium">
                Hunyuan v1.0 · IP-Adapter
              </span>
            </div>

            {/* LoRA selector */}
            <div className="mb-4">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-semibold text-zinc-300">Scene / Action</p>
                {selectedLora && (
                  <button
                    type="button"
                    onClick={() => { setSelectedLora(null); setHunyuanPrompt(''); }}
                    className="flex items-center gap-1 text-xs text-zinc-500 hover:text-white transition-colors"
                  >
                    <X size={12} />
                    Clear
                  </button>
                )}
              </div>
              <VideoLoraSelector
                selectedId={selectedLora?.id ?? null}
                onSelect={handleLoraSelect}
                variant="full"
              />
              {selectedLora && (
                <p className="mt-2 text-xs text-violet-300/80">
                  Scene prompt auto-filled: <span className="font-mono bg-violet-500/10 px-1.5 py-0.5 rounded">{selectedLora.name}</span>
                </p>
              )}
            </div>

            {/* Prompt */}
            <div className="mb-4">
              <p className="mb-2 text-sm font-semibold text-zinc-300">Prompt</p>
              <textarea
                value={hunyuanPrompt}
                onChange={(e) => setHunyuanPrompt(e.target.value)}
                placeholder="Select a scene above — trigger word will be added automatically. Then describe the character, setting, and mood..."
                rows={4}
                className="w-full resize-none rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white placeholder:text-zinc-500 outline-none focus:border-violet-400/50"
              />
            </div>

            <button
              onClick={() => void handleGenerateHunyuanVideo()}
              disabled={hunyuanState.isGenerating || !hunyuanPrompt.trim()}
              className="w-full rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-4 py-3 font-bold text-white hover:from-violet-500 hover:to-indigo-500 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {hunyuanState.isGenerating ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Generating... (may take 3–5 min)
                </>
              ) : (
                <>
                  <Video size={18} />
                  Generate Video
                </>
              )}
            </button>

            {hunyuanState.error && (
              <p className="mt-3 text-sm text-red-400">{hunyuanState.error}</p>
            )}

            {hunyuanState.isGenerating && hunyuanState.taskId && (
              <p className="mt-2 text-xs text-zinc-500 text-center">
                Task ID: <span className="font-mono">{hunyuanState.taskId}</span> · polling every 4s
              </p>
            )}

            {hunyuanState.videoUrl && (
              <div className="mt-4">
                <p className="mb-2 text-sm font-semibold text-violet-200">Generated Video</p>
                <video
                  src={hunyuanState.videoUrl}
                  controls
                  loop
                  autoPlay
                  muted
                  className="w-full rounded-xl border border-violet-400/20"
                />
                <div className="mt-2 flex gap-2">
                  <a
                    href={hunyuanState.videoUrl}
                    download
                    className="flex-1 rounded-lg border border-violet-400/30 bg-violet-500/10 px-3 py-2 text-center text-sm text-violet-200 hover:bg-violet-500/20 transition-colors"
                  >
                    Download
                  </a>
                  <button
                    onClick={() => setHunyuanState({ isGenerating: false, taskId: null, videoUrl: null, error: null })}
                    className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-300 hover:bg-white/10 transition-colors"
                  >
                    New Video
                  </button>
                </div>
              </div>
            )}
          </div>

          {generatedImages.length > 0 && (
            <section className="mt-8">
              <div className="mb-3 flex items-center justify-between">
                <div className="text-lg font-bold">Generated Results</div>
                <a
                  href="/collection"
                  className="text-sm text-indigo-300 hover:text-indigo-200 underline"
                >
                  View Collection →
                </a>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {generatedImages.map((url) => {
                  const anim = animateStates[url];
                  return (
                    <div key={url} className="flex flex-col gap-2">
                      {/* Image */}
                      <div className="relative group">
                        <img
                          src={url}
                          alt="Generated"
                          className="w-full rounded-xl border border-white/10 object-cover"
                        />
                        {/* Animate toggle button */}
                        {!anim?.isAnimating && !anim?.videoUrl && (
                          <button
                            onClick={() => setAnimateState(url, { showPrompt: !(anim?.showPrompt) })}
                            className="absolute bottom-2 right-2 flex items-center gap-1.5 rounded-lg bg-primary-500/90 px-3 py-1.5 text-sm font-medium text-white shadow-lg backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-all hover:bg-primary-600/90"
                          >
                            <Play size={14} fill="white" />
                            Animate
                          </button>
                        )}
                        {anim?.isAnimating && (
                          <div className="absolute bottom-2 right-2 flex items-center gap-1.5 rounded-lg bg-black/70 px-3 py-1.5 text-sm text-white">
                            <Loader2 size={14} className="animate-spin" />
                            Animating...
                          </div>
                        )}
                      </div>

                      {/* Animate prompt panel */}
                      {anim?.showPrompt && !anim.isAnimating && (
                        <div className="rounded-xl border border-white/10 bg-zinc-900/95 p-3 shadow-xl">
                          <p className="mb-2 text-xs text-zinc-400">Describe the action you want</p>
                          <input
                            type="text"
                            value={anim.prompt}
                            onChange={(e) => setAnimateState(url, { prompt: e.target.value })}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' && anim.prompt.trim()) handleAnimate(url, anim.prompt.trim());
                              if (e.key === 'Escape') setAnimateState(url, { showPrompt: false });
                            }}
                            className="w-full rounded-lg border border-white/10 bg-zinc-800 px-3 py-2 text-sm text-white placeholder:text-zinc-500 focus:border-primary-400 focus:outline-none"
                            placeholder="e.g. walking on beach, smiling at camera"
                            autoFocus
                          />
                          <div className="mt-2 flex gap-2">
                            <button
                              onClick={() => anim.prompt.trim() && handleAnimate(url, anim.prompt.trim())}
                              disabled={!anim.prompt.trim()}
                              className="flex-1 rounded-lg bg-primary-500 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-600 disabled:opacity-40"
                            >
                              Generate Video
                            </button>
                            <button
                              onClick={() => setAnimateState(url, { showPrompt: false })}
                              className="rounded-lg bg-zinc-700 px-3 py-1.5 text-sm text-zinc-300 transition-colors hover:bg-zinc-600"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Video result */}
                      {anim?.videoUrl && (
                        <video
                          src={anim.videoUrl}
                          controls
                          loop
                          autoPlay
                          muted
                          className="w-full rounded-xl border border-white/10"
                        />
                      )}

                      {/* Per-image error */}
                      {anim?.error && (
                        <p className="text-xs text-red-400">{anim.error}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>
          )}
      </div>
      <InsufficientCreditsModal
        isOpen={insufficientCreditsState.isOpen}
        required={insufficientCreditsState.required}
        available={insufficientCreditsState.available}
        onClose={() => setInsufficientCreditsState((prev) => ({ ...prev, isOpen: false }))}
      />
    </RoxyShellLayout>
  );
}
