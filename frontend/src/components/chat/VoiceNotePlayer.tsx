/**
 * VoiceNotePlayer Component (PRD v2026.02)
 *
 * Audio player for voice note messages with waveform visualization.
 */
import { useState, useRef, useEffect, useMemo } from 'react';
import { Play, Pause, Loader2, MicOff } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAudioFocus } from '@/contexts/AudioFocusContext';

interface VoiceNotePlayerProps {
  messageId: string;
  audioUrl: string;
  duration: number; // Duration in seconds
  isGenerating?: boolean;
  cost?: number;
  onPlayStart?: () => void;
  onPlayEnd?: () => void;
}

let activeVoiceNoteController: { id: string; pause: () => void } | null = null;

function hashSeed(input: string): number {
  let hash = 0;
  for (let i = 0; i < input.length; i += 1) {
    hash = (hash << 5) - hash + input.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

function seededWaveHeights(seedInput: string, count = 36): number[] {
  const seed = hashSeed(seedInput) || 1;
  const heights: number[] = [];
  let state = seed;

  for (let i = 0; i < count; i += 1) {
    state = (state * 1664525 + 1013904223) % 0x100000000;
    const normalized = state / 0x100000000;
    heights.push(22 + Math.floor(normalized * 56));
  }

  return heights;
}

export function VoiceNotePlayer({
  messageId,
  audioUrl,
  duration,
  isGenerating = false,
  cost,
  onPlayStart,
  onPlayEnd,
}: VoiceNotePlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const waveformHeights = useMemo(() => seededWaveHeights(messageId), [messageId]);
  const { isAudioSuppressed } = useAudioFocus();

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const pauseSelf = () => {
    if (!audioRef.current) return;
    audioRef.current.pause();
    setIsPlaying(false);
  };

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => {
    if (isAudioSuppressed) {
      pauseSelf();
      setIsLoading(false);
      if (activeVoiceNoteController?.id === messageId) {
        activeVoiceNoteController = null;
      }
    }
  }, [isAudioSuppressed, messageId]);

  useEffect(() => {
    if (!audioUrl || isGenerating) return;

    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    const onLoadStart = () => setIsLoading(true);
    const onCanPlay = () => setIsLoading(false);
    const onTimeUpdate = () => setCurrentTime(audio.currentTime);
    const onPause = () => setIsPlaying(false);
    const onEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
      if (activeVoiceNoteController?.id === messageId) {
        activeVoiceNoteController = null;
      }
      onPlayEnd?.();
    };

    audio.addEventListener('loadstart', onLoadStart);
    audio.addEventListener('canplay', onCanPlay);
    audio.addEventListener('timeupdate', onTimeUpdate);
    audio.addEventListener('pause', onPause);
    audio.addEventListener('ended', onEnded);

    return () => {
      if (activeVoiceNoteController?.id === messageId) {
        activeVoiceNoteController = null;
      }
      audio.pause();
      audio.removeEventListener('loadstart', onLoadStart);
      audio.removeEventListener('canplay', onCanPlay);
      audio.removeEventListener('timeupdate', onTimeUpdate);
      audio.removeEventListener('pause', onPause);
      audio.removeEventListener('ended', onEnded);
      audio.src = '';
      audioRef.current = null;
    };
  }, [audioUrl, isGenerating, messageId, onPlayEnd]);

  const handlePlayPause = () => {
    if (!audioRef.current || isAudioSuppressed) return;

    if (isPlaying) {
      pauseSelf();
      if (activeVoiceNoteController?.id === messageId) {
        activeVoiceNoteController = null;
      }
      return;
    }

    if (activeVoiceNoteController && activeVoiceNoteController.id !== messageId) {
      activeVoiceNoteController.pause();
    }

    audioRef.current.play().then(() => {
      activeVoiceNoteController = { id: messageId, pause: pauseSelf };
      setIsPlaying(true);
      onPlayStart?.();
    }).catch((error) => {
      console.error('Audio playback error:', error);
      setIsPlaying(false);
    });
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current || !duration) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const newTime = percentage * duration;

    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  if (isGenerating) {
    return (
      <div className="flex items-center gap-3 p-3 bg-zinc-800/50 rounded-xl border border-zinc-700/50">
        <div className="flex items-center justify-center w-10 h-10 bg-primary-500/20 rounded-full">
          <Loader2 className="w-5 h-5 text-primary-400 animate-spin" />
        </div>
        <div className="flex-1 space-y-2">
          <div className="h-8 bg-zinc-700/50 rounded animate-pulse" />
          <div className="text-xs text-zinc-500">Generating voice...</div>
        </div>
      </div>
    );
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="flex items-center gap-3 p-3 bg-zinc-800/50 rounded-xl border border-zinc-700/50 hover:border-zinc-600/50 transition-colors">
      <button
        onClick={handlePlayPause}
        disabled={isLoading || isAudioSuppressed}
        className={cn(
          'flex items-center justify-center w-10 h-10 rounded-full transition-all',
          'bg-primary-500 hover:bg-primary-600 disabled:bg-zinc-700',
          'focus:outline-none focus:ring-2 focus:ring-primary-400/50'
        )}
        title={isAudioSuppressed ? '通话中音频已暂停' : 'Play voice note'}
      >
        {isAudioSuppressed ? (
          <MicOff className="w-5 h-5 text-white" />
        ) : isLoading ? (
          <Loader2 className="w-5 h-5 text-white animate-spin" />
        ) : isPlaying ? (
          <Pause className="w-5 h-5 text-white" fill="white" />
        ) : (
          <Play className="w-5 h-5 text-white ml-0.5" fill="white" />
        )}
      </button>

      <div className="flex-1 space-y-1">
        <div
          className="relative h-8 bg-zinc-700/50 rounded cursor-pointer group overflow-hidden"
          onClick={handleSeek}
        >
          <div
            className="absolute inset-y-0 left-0 bg-primary-500/30 rounded transition-all"
            style={{ width: `${progress}%` }}
          />

          <div className="absolute inset-0 flex items-center justify-around px-1">
            {waveformHeights.map((height, i) => {
              const isPassed = (i / waveformHeights.length) * 100 < progress;
              return (
                <div
                  key={i}
                  className={cn(
                    'w-0.5 rounded-full transition-colors',
                    isPassed ? 'bg-primary-300' : 'bg-zinc-600',
                    isPlaying && 'animate-pulse'
                  )}
                  style={{ height: `${height}%` }}
                />
              );
            })}
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-zinc-400">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      {cost !== undefined && cost > 0 && (
        <div className="text-xs text-zinc-500 ml-1">
          {cost.toFixed(2)} credits
        </div>
      )}

      {isAudioSuppressed && (
        <div className="ml-1 text-xs text-amber-300">
          通话中，音频已暂停
        </div>
      )}
    </div>
  );
}
