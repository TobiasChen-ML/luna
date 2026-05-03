import { useCallback, useEffect, useRef, useState } from 'react';
import { Loader2, Mic, MicOff, PhoneOff, Sparkles } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAudioFocus } from '@/contexts/AudioFocusContext';
import { postVoiceTurn, type VoiceTurnResult } from '@/services/voiceTurnService';

type TurnStatus = 'idle' | 'recording' | 'processing' | 'playing' | 'error';

interface Turn {
  userText: string;
  assistantText: string;
  emotion: string;
}

interface PushToTalkModalProps {
  isOpen: boolean;
  characterId: string;
  sessionId: string;
  characterName: string;
  onClose: () => void;
}

const EMOTION_LABEL: Record<string, string> = {
  撒娇: '撒娇', 开心: '开心', 兴奋: '兴奋', 生气: '生气',
  委屈: '委屈', 害羞: '害羞', 悲伤: '悲伤', 温柔: '温柔',
  平静: '平静', 惊讶: '惊讶', 担心: '担心', 调皮: '调皮',
  default: '', playful: '调皮', happy: '开心', sad: '悲伤',
  angry: '生气', excited: '兴奋', gentle: '温柔', shy: '害羞',
};

function statusLabel(s: TurnStatus): string {
  switch (s) {
    case 'recording':   return '正在录音…';
    case 'processing':  return 'AI 思考中…';
    case 'playing':     return '播放中';
    case 'error':       return '出错了';
    default:            return '按住说话';
  }
}

export function PushToTalkModal({
  isOpen,
  characterId,
  sessionId,
  characterName,
  onClose,
}: PushToTalkModalProps) {
  const { setAudioSuppressed } = useAudioFocus();
  const [status, setStatus] = useState<TurnStatus>('idle');
  const [error, setError] = useState('');
  const [turns, setTurns] = useState<Turn[]>([]);

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recorderRef    = useRef<MediaRecorder | null>(null);
  const chunksRef      = useRef<Blob[]>([]);
  const startTimeRef   = useRef<number>(0);
  const audioRef       = useRef<HTMLAudioElement | null>(null);
  const transcriptRef  = useRef<HTMLDivElement | null>(null);
  const mountedRef     = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  // Suppress background audio while modal is open
  useEffect(() => {
    if (isOpen) {
      setAudioSuppressed(true);
    } else {
      setAudioSuppressed(false);
      // Stop any ongoing recording when modal closes
      const recorder = recorderRef.current;
      if (recorder && recorder.state !== 'inactive') recorder.stop();
      mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
      audioRef.current?.pause();
    }
    return () => setAudioSuppressed(false);
  }, [isOpen, setAudioSuppressed]);

  // Auto-scroll transcript
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [turns]);

  const startRecording = useCallback(async () => {
    if (status !== 'idle') return;
    setError('');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/mp4')
          ? 'audio/mp4'
          : '';
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      recorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.start(100);
      startTimeRef.current = Date.now();
      setStatus('recording');
    } catch {
      setError('无法访问麦克风，请检查浏览器权限');
      setStatus('error');
    }
  }, [status]);

  const stopRecording = useCallback(() => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state === 'inactive') return;

    recorder.onstop = async () => {
      const inputDuration = (Date.now() - startTimeRef.current) / 1000;
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' });

      mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
      recorderRef.current = null;

      if (blob.size < 1000) {
        // Too short — ignore
        setStatus('idle');
        return;
      }

      setStatus('processing');
      try {
        const result = await postVoiceTurn({
          audioBlob: blob,
          sessionId,
          characterId,
          inputDurationSeconds: inputDuration,
        });
        await playResult(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : '通话出错');
        setStatus('error');
      }
    };

    recorder.stop();
  }, [characterId, sessionId]);

  const playResult = useCallback(async (result: VoiceTurnResult) => {
    if (!mountedRef.current) return;

    setTurns((prev) => [
      ...prev,
      {
        userText: result.transcriptIn,
        assistantText: result.transcriptOut,
        emotion: result.emotion,
      },
    ]);

    const url = URL.createObjectURL(result.audioBlob);
    const audio = new Audio(url);
    audioRef.current = audio;
    if (mountedRef.current) setStatus('playing');

    await new Promise<void>((resolve) => {
      audio.onended = () => { URL.revokeObjectURL(url); resolve(); };
      audio.onerror = () => { URL.revokeObjectURL(url); resolve(); };
      audio.play().catch(resolve);
    });

    audioRef.current = null;
    if (mountedRef.current) setStatus('idle');
  }, []);

  // Pointer events — support both mouse and touch
  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    startRecording();
  }, [startRecording]);

  const handlePointerUp = useCallback(() => {
    stopRecording();
  }, [stopRecording]);

  if (!isOpen) return null;

  const isHolding = status === 'recording';
  const isBusy    = status === 'processing' || status === 'playing';

  return (
    <div className="fixed inset-0 z-[100] flex flex-col bg-[#05060a] text-white">
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-0 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-cyan-500/20 blur-[130px]" />
        <div className="absolute bottom-0 right-0 h-[340px] w-[340px] rounded-full bg-fuchsia-500/15 blur-[130px]" />
      </div>

      {/* Header */}
      <div className="relative z-10 flex items-center justify-between px-5 pt-5">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl">
            <Sparkles className="h-4 w-4 text-cyan-300" />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-widest text-white/40">语音通话</p>
            <p className="text-base font-semibold">{characterName}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center gap-2 rounded-full border border-rose-400/30 bg-rose-500/10 px-4 py-2 text-sm font-medium text-rose-200 transition-colors hover:bg-rose-500/20"
          >
            <PhoneOff className="h-4 w-4" />
            挂断
          </button>
        </div>
      </div>

      {/* Transcript */}
      <div
        ref={transcriptRef}
        className="relative z-10 mx-5 mt-4 flex-1 overflow-y-auto rounded-3xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-xl"
      >
        {turns.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-white/30">
            对话记录将在这里显示
          </div>
        ) : (
          <div className="space-y-4">
            {turns.map((turn, i) => (
              <div key={i} className="space-y-2">
                {/* User bubble */}
                <div className="flex justify-end">
                  <div className="max-w-[75%] rounded-2xl rounded-br-md bg-cyan-500/20 px-4 py-2 text-sm text-white/90">
                    {turn.userText}
                  </div>
                </div>
                {/* AI bubble */}
                <div className="flex items-end gap-2">
                  <div className="max-w-[75%] rounded-2xl rounded-bl-md bg-white/10 px-4 py-2 text-sm text-white/90">
                    {turn.assistantText}
                  </div>
                  {EMOTION_LABEL[turn.emotion] && (
                    <span className="mb-1 shrink-0 rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-white/50">
                      {EMOTION_LABEL[turn.emotion]}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="relative z-10 mx-5 mt-3 rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-2 text-sm text-rose-200">
          {error}
        </div>
      )}

      {/* Hold-to-talk button */}
      <div className="relative z-10 flex flex-col items-center gap-3 pb-10 pt-6">
        <p className="text-xs text-white/40">{statusLabel(status)}</p>

        <button
          type="button"
          onPointerDown={handlePointerDown}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
          disabled={isBusy}
          className={cn(
            'relative flex h-24 w-24 select-none items-center justify-center rounded-full border-2 transition-all duration-150',
            isHolding && 'scale-110 border-cyan-400 bg-cyan-500/25 shadow-[0_0_40px_rgba(34,211,238,0.5)]',
            isBusy   && 'cursor-not-allowed border-white/20 bg-white/5 opacity-60',
            !isHolding && !isBusy && 'border-white/20 bg-white/8 hover:border-white/35 hover:bg-white/12 active:scale-95',
          )}
        >
          {status === 'processing' ? (
            <Loader2 className="h-10 w-10 animate-spin text-amber-300" />
          ) : status === 'playing' ? (
            <Mic className="h-10 w-10 text-emerald-300" />
          ) : status === 'error' ? (
            <MicOff className="h-10 w-10 text-rose-300" />
          ) : (
            <Mic className={cn('h-10 w-10', isHolding ? 'text-cyan-300' : 'text-white/70')} />
          )}

          {/* Pulse ring while recording */}
          {isHolding && (
            <span className="absolute inset-0 animate-ping rounded-full border-2 border-cyan-400/40" />
          )}
        </button>

        <p className="text-[11px] text-white/25">
          {isBusy ? '' : '按住说话，松开发送'}
        </p>
      </div>
    </div>
  );
}
