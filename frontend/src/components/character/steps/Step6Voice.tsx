import { useCallback, useEffect, useRef, useState } from 'react';
import { useWizard } from '@/contexts/CharacterWizardContext';
import { WizardStep } from '../WizardStep';
import { SelectionCard } from '../SelectionCard';
import type { VoiceProfile } from '@/types/character';
import { Mic, Volume2, Loader2, Play } from 'lucide-react';
import { api } from '@/services/api';

const voiceProfiles: {
  value: VoiceProfile;
  label: string;
  description: string;
}[] = [
  {
    value: 'ASMR_Whisperer',
    label: 'Almme',
    description: 'A female ASMR voice that is a soft, tranquil whisper, perfect for meditations, bedtime stories, relaxation apps, and affirmations. Its calming tone soothes the mind and creates a serene, comforting experience for listeners.',
  },
  {
    value: 'Sensual_Hypnotic',
    label: 'Natasha',
    description: 'A sexy, sultry yet gentle whisper ASMR voice that feels soothing and intimate.',
  },
  {
    value: 'Soft_Husky',
    label: 'Carla',
    description: 'A seductive yet gentle ASMR voice, whispered calmly and intimately.',
  },
  {
    value: 'Mysterious_Warm',
    label: 'Chloe',
    description: 'Playful and sassy teen whisper with charm; great for sidekicks or rebellious roles.',
  },
  {
    value: 'Hollywood_Actress',
    label: 'Madison Ray',
    description: 'A middle-aged American female voice with a pleasant tone for news-style delivery.',
  },
  {
    value: 'Lively_Girl',
    label: 'Velvety Calm',
    description: 'Warm, velvety, and smooth with deep resonant tones for comfort and confidence.',
  },
  {
    value: 'Seductive_Calm',
    label: 'Allison',
    description: 'A fun millennial female voice for news, commercials, audiobooks, and relatable characters.',
  },
  {
    value: 'Meditative_ASMR',
    label: 'Fernandez',
    description: 'A serious, mysterious, professional voice for podcasts, audiobooks, and narration.',
  },
];

const PREVIEW_TASK_STORAGE_KEY = 'aigirl_voice_preview_task';
const PREVIEW_POLL_INTERVAL_MS = 2000;

type StoredPreviewTask = {
  taskId: string;
  voiceId: VoiceProfile;
};

export function Step6Voice() {
  const { characterData, updateNestedField } = useWizard();
  const [playingVoice, setPlayingVoice] = useState<VoiceProfile | null>(null);
  const [loadingVoice, setLoadingVoice] = useState<VoiceProfile | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const pollPreviewTaskRef = useRef<((taskId: string, voiceId: VoiceProfile) => Promise<void>) | null>(null);

  const clearPollTimer = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const savePendingTask = useCallback((taskId: string, voiceId: VoiceProfile) => {
    const payload: StoredPreviewTask = { taskId, voiceId };
    localStorage.setItem(PREVIEW_TASK_STORAGE_KEY, JSON.stringify(payload));
  }, []);

  const clearPendingTask = useCallback(() => {
    localStorage.removeItem(PREVIEW_TASK_STORAGE_KEY);
  }, []);

  const playAudio = useCallback(async (audioUrl: string, voiceId: VoiceProfile) => {
    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    audio.onloadeddata = () => {
      setLoadingVoice(null);
      setPlayingVoice(voiceId);
    };

    audio.onended = () => {
      setPlayingVoice(null);
      audioRef.current = null;
    };

    audio.onerror = () => {
      setLoadingVoice(null);
      setPlayingVoice(null);
      console.error('Failed to play audio');
    };

    await audio.play();
  }, []);

  const pollPreviewTask = useCallback(async (taskId: string, voiceId: VoiceProfile) => {
    try {
      const response = await api.get(`/characters/voice/preview/${taskId}`);
      const status = response.data?.status as string | undefined;
      const audioUrl = response.data?.audio_url as string | undefined;

      if (status === 'completed' && audioUrl) {
        clearPendingTask();
        clearPollTimer();
        await playAudio(audioUrl, voiceId);
        return;
      }

      if (status === 'failed') {
        clearPendingTask();
        clearPollTimer();
        setLoadingVoice(null);
        setPlayingVoice(null);
        console.error('Voice preview task failed:', response.data?.error || 'unknown error');
        return;
      }

      setLoadingVoice(voiceId);
      pollTimerRef.current = window.setTimeout(() => {
        if (pollPreviewTaskRef.current) {
          void pollPreviewTaskRef.current(taskId, voiceId);
        }
      }, PREVIEW_POLL_INTERVAL_MS);
    } catch (error: unknown) {
      const maybeStatus = (error as { response?: { status?: number } })?.response?.status;
      if (maybeStatus === 404) {
        clearPendingTask();
        clearPollTimer();
        setLoadingVoice(null);
        setPlayingVoice(null);
        return;
      }

      pollTimerRef.current = window.setTimeout(() => {
        if (pollPreviewTaskRef.current) {
          void pollPreviewTaskRef.current(taskId, voiceId);
        }
      }, PREVIEW_POLL_INTERVAL_MS);
    }
  }, [clearPendingTask, clearPollTimer, playAudio]);

  useEffect(() => {
    pollPreviewTaskRef.current = pollPreviewTask;
  }, [pollPreviewTask]);

  const handleVoicePreview = useCallback(async (voiceId: VoiceProfile) => {
    try {
      clearPollTimer();
      clearPendingTask();
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      setPlayingVoice(null);
      setLoadingVoice(voiceId);

      const response = await api.post(`/characters/voice/preview?voice_id=${voiceId}`);

      if (response.data.success && response.data.status === 'completed' && response.data.audio_url) {
        await playAudio(response.data.audio_url as string, voiceId);
        return;
      }

      const taskId = response.data?.task_id as string | undefined;
      if (response.data.success && taskId) {
        savePendingTask(taskId, voiceId);
        await pollPreviewTask(taskId, voiceId);
        return;
      }

      setLoadingVoice(null);
    } catch (error) {
      console.error('Failed to preview voice:', error);
      setLoadingVoice(null);
      setPlayingVoice(null);
    }
  }, [clearPendingTask, clearPollTimer, playAudio, pollPreviewTask, savePendingTask]);

  useEffect(() => {
    const restorePendingTask = () => {
      const raw = localStorage.getItem(PREVIEW_TASK_STORAGE_KEY);
      if (!raw) return;

      try {
        const parsed = JSON.parse(raw) as StoredPreviewTask;
        if (!parsed?.taskId || !parsed?.voiceId) {
          clearPendingTask();
          return;
        }
        setLoadingVoice(parsed.voiceId);
        void pollPreviewTask(parsed.taskId, parsed.voiceId);
      } catch {
        clearPendingTask();
      }
    };

    restorePendingTask();

    return () => {
      clearPollTimer();
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [clearPendingTask, clearPollTimer, pollPreviewTask]);

  return (
    <WizardStep
      title="Choose a Voice"
      description="Select a voice profile for your character (optional)"
    >
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Mic size={20} className="text-primary-500" />
          <h3 className="text-lg font-semibold">Voice Profile</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {voiceProfiles.map((voice) => {
            const isLoading = loadingVoice === voice.value;
            const isPlaying = playingVoice === voice.value;

            return (
              <SelectionCard
                key={voice.value}
                title={voice.label}
                description={voice.description}
                selected={characterData.voiceProfile === voice.value}
                onClick={() => updateNestedField('voiceProfile', voice.value)}
                icon={<Volume2 size={20} className="text-white" />}
                variant="visual"
                compact
                badge={
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleVoicePreview(voice.value);
                    }}
                    className="w-8 h-8 rounded-full bg-primary-500 hover:bg-primary-600 flex items-center justify-center shadow-lg transition-all hover:scale-110"
                    title="Preview voice"
                  >
                    {isLoading ? (
                      <Loader2 size={16} className="text-white animate-spin" />
                    ) : isPlaying ? (
                      <Volume2 size={16} className="text-white animate-pulse" />
                    ) : (
                      <Play size={14} className="text-white ml-0.5" />
                    )}
                  </button>
                }
              />
            );
          })}
        </div>
        <p className="text-xs text-zinc-500">
          You can skip this step and add a voice later.
        </p>
      </div>
    </WizardStep>
  );
}
