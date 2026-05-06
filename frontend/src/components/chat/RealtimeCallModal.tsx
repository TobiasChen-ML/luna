import { useCallback, useEffect, useRef, useState } from 'react';
import { Loader2, Mic, MicOff, PhoneOff, Sparkles, WifiOff, Waves } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAudioFocus } from '@/contexts/AudioFocusContext';
import { openRealtimeVoiceSocket } from '@/services/realtimeVoiceService';

type CallStatus = 'connecting' | 'listening' | 'thinking' | 'speaking' | 'muted' | 'ended' | 'error';

interface RealtimeCallModalProps {
  isOpen: boolean;
  characterId: string;
  sessionId?: string | null;
  characterName: string;
  onClose: () => void;
}

interface RealtimeEventPayload {
  type?: string;
  session_id?: string;
  voice_id?: string;
  message?: string;
  text?: string;
  conversation_initiation_metadata_event?: {
    conversation_id?: string;
  };
  user_transcription_event?: {
    user_transcript?: string;
  };
  agent_response_event?: {
    agent_response?: string;
  };
  agent_response_correction_event?: {
    corrected_agent_response?: string;
  };
}

const INPUT_SAMPLE_RATE = 16000;
const OUTPUT_SAMPLE_RATE = 16000;
const INPUT_BUFFER_SIZE = 4096;

function statusCopy(status: CallStatus): string {
  switch (status) {
    case 'speaking':
      return 'AI 说话中';
    case 'thinking':
      return 'AI 思考中';
    case 'muted':
      return '麦克风已静音';
    case 'ended':
      return '通话已结束';
    case 'error':
      return '通话异常';
    case 'connecting':
      return '正在连接 ElevenLabs';
    case 'listening':
    default:
      return '实时聆听中';
  }
}

function getAudioContextConstructor(): typeof AudioContext {
  const maybeWindow = window as typeof window & {
    webkitAudioContext?: typeof AudioContext;
  };
  const AudioContextConstructor = window.AudioContext || maybeWindow.webkitAudioContext;
  if (!AudioContextConstructor) {
    throw new Error('当前浏览器不支持实时音频通话');
  }
  return AudioContextConstructor;
}

function resampleAudio(
  input: Float32Array,
  sourceSampleRate: number,
  targetSampleRate: number
): Float32Array {
  if (sourceSampleRate === targetSampleRate) {
    return input;
  }

  const ratio = sourceSampleRate / targetSampleRate;
  const outputLength = Math.max(1, Math.floor(input.length / ratio));
  const output = new Float32Array(outputLength);

  for (let i = 0; i < outputLength; i += 1) {
    const sourceIndex = i * ratio;
    const left = Math.floor(sourceIndex);
    const right = Math.min(left + 1, input.length - 1);
    const weight = sourceIndex - left;
    output[i] = input[left] * (1 - weight) + input[right] * weight;
  }

  return output;
}

function float32ToPcm16(input: Float32Array): Int16Array {
  const output = new Int16Array(input.length);
  for (let i = 0; i < input.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, input[i]));
    output[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return output;
}

function pcm16ToFloat32(input: Int16Array): Float32Array<ArrayBuffer> {
  const output = new Float32Array(input.length) as Float32Array<ArrayBuffer>;
  for (let i = 0; i < input.length; i += 1) {
    output[i] = input[i] / (input[i] < 0 ? 0x8000 : 0x7fff);
  }
  return output;
}

function cloneArrayBufferView(view: ArrayBufferView): ArrayBuffer {
  const copy = new Uint8Array(view.byteLength);
  copy.set(new Uint8Array(view.buffer, view.byteOffset, view.byteLength));
  return copy.buffer;
}

function extractUserTranscript(payload: RealtimeEventPayload): string {
  return payload.user_transcription_event?.user_transcript || '';
}

function extractAgentText(payload: RealtimeEventPayload): string {
  return (
    payload.agent_response_event?.agent_response ||
    payload.agent_response_correction_event?.corrected_agent_response ||
    ''
  );
}

export function RealtimeCallModal({
  isOpen,
  characterId,
  sessionId,
  characterName,
  onClose,
}: RealtimeCallModalProps) {
  const { setAudioSuppressed } = useAudioFocus();
  const [status, setStatus] = useState<CallStatus>('connecting');
  const [error, setError] = useState('');
  const [requestKey, setRequestKey] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [remoteSessionId, setRemoteSessionId] = useState('');
  const [voiceId, setVoiceId] = useState('');
  const [conversationId, setConversationId] = useState('');
  const [lastUserText, setLastUserText] = useState('');
  const [lastAgentText, setLastAgentText] = useState('');

  const socketRef = useRef<WebSocket | null>(null);
  const inputContextRef = useRef<AudioContext | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const inputSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const inputProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const inputGainRef = useRef<GainNode | null>(null);
  const playbackSourcesRef = useRef<Set<AudioBufferSourceNode>>(new Set());
  const nextPlayTimeRef = useRef(0);
  const speakingTimerRef = useRef<number | null>(null);
  const statusRef = useRef<CallStatus>('connecting');
  const mutedRef = useRef(false);
  const mountedRef = useRef(false);
  const closeRequestedRef = useRef(false);

  const clearSpeakingTimer = useCallback(() => {
    if (speakingTimerRef.current !== null) {
      window.clearTimeout(speakingTimerRef.current);
      speakingTimerRef.current = null;
    }
  }, []);

  const stopInputCapture = useCallback(() => {
    const processor = inputProcessorRef.current;
    if (processor) {
      processor.onaudioprocess = null;
      processor.disconnect();
      inputProcessorRef.current = null;
    }

    inputSourceRef.current?.disconnect();
    inputSourceRef.current = null;
    inputGainRef.current?.disconnect();
    inputGainRef.current = null;

    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;

    const inputContext = inputContextRef.current;
    inputContextRef.current = null;
    if (inputContext && inputContext.state !== 'closed') {
      void inputContext.close();
    }
  }, []);

  const stopPlayback = useCallback(() => {
    clearSpeakingTimer();
    playbackSourcesRef.current.forEach((source) => {
      try {
        source.stop();
      } catch {
        // Source may already be stopped.
      }
      source.disconnect();
    });
    playbackSourcesRef.current.clear();
    nextPlayTimeRef.current = 0;

    const playbackContext = playbackContextRef.current;
    playbackContextRef.current = null;
    if (playbackContext && playbackContext.state !== 'closed') {
      void playbackContext.close();
    }
  }, [clearSpeakingTimer]);

  const cleanupRealtimeResources = useCallback(
    (notifyServer: boolean) => {
      stopInputCapture();
      stopPlayback();

      const socket = socketRef.current;
      socketRef.current = null;
      if (!socket) {
        return;
      }

      socket.onopen = null;
      socket.onmessage = null;
      socket.onerror = null;
      socket.onclose = null;

      if (notifyServer && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'stop' }));
      }

      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
        socket.close();
      }
    },
    [stopInputCapture, stopPlayback]
  );

  const markAgentSpeaking = useCallback(
    (durationMs: number) => {
      clearSpeakingTimer();
      setStatus('speaking');
      speakingTimerRef.current = window.setTimeout(() => {
        if (
          !mountedRef.current ||
          statusRef.current === 'error' ||
          statusRef.current === 'ended'
        ) {
          return;
        }
        setStatus(mutedRef.current ? 'muted' : 'listening');
      }, Math.max(450, durationMs + 180));
    },
    [clearSpeakingTimer]
  );

  const playPcmAudio = useCallback(
    async (audioData: ArrayBuffer) => {
      if (!mountedRef.current || audioData.byteLength === 0) {
        return;
      }

      const AudioContextConstructor = getAudioContextConstructor();
      let playbackContext = playbackContextRef.current;
      if (!playbackContext || playbackContext.state === 'closed') {
        playbackContext = new AudioContextConstructor({ sampleRate: OUTPUT_SAMPLE_RATE });
        playbackContextRef.current = playbackContext;
        nextPlayTimeRef.current = playbackContext.currentTime;
      }

      if (playbackContext.state === 'suspended') {
        await playbackContext.resume();
      }

      const pcm = new Int16Array(audioData);
      const samples = pcm16ToFloat32(pcm);
      const buffer = playbackContext.createBuffer(1, samples.length, OUTPUT_SAMPLE_RATE);
      buffer.copyToChannel(samples, 0);

      const source = playbackContext.createBufferSource();
      source.buffer = buffer;
      source.connect(playbackContext.destination);
      playbackSourcesRef.current.add(source);
      source.onended = () => {
        playbackSourcesRef.current.delete(source);
        source.disconnect();
      };

      const startAt = Math.max(playbackContext.currentTime + 0.02, nextPlayTimeRef.current);
      source.start(startAt);
      nextPlayTimeRef.current = startAt + buffer.duration;
      markAgentSpeaking(Math.max(0, nextPlayTimeRef.current - playbackContext.currentTime) * 1000);
    },
    [markAgentSpeaking]
  );

  const startMicrophone = useCallback(async () => {
    if (inputContextRef.current) {
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
        },
      });

      if (!mountedRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }

      const AudioContextConstructor = getAudioContextConstructor();
      const inputContext = new AudioContextConstructor();
      if (inputContext.state === 'suspended') {
        await inputContext.resume();
      }

      const source = inputContext.createMediaStreamSource(stream);
      const processor = inputContext.createScriptProcessor(INPUT_BUFFER_SIZE, 1, 1);
      const silentGain = inputContext.createGain();
      silentGain.gain.value = 0;

      processor.onaudioprocess = (event) => {
        const socket = socketRef.current;
        if (!socket || socket.readyState !== WebSocket.OPEN || mutedRef.current) {
          return;
        }

        const input = event.inputBuffer.getChannelData(0);
        const resampled = resampleAudio(input, inputContext.sampleRate, INPUT_SAMPLE_RATE);
        const pcm = float32ToPcm16(resampled);
        const frame = pcm.buffer.slice(pcm.byteOffset, pcm.byteOffset + pcm.byteLength);
        socket.send(frame);
      };

      source.connect(processor);
      processor.connect(silentGain);
      silentGain.connect(inputContext.destination);

      mediaStreamRef.current = stream;
      inputContextRef.current = inputContext;
      inputSourceRef.current = source;
      inputProcessorRef.current = processor;
      inputGainRef.current = silentGain;
      stream.getAudioTracks().forEach((track) => {
        track.enabled = !mutedRef.current;
      });
      setStatus(mutedRef.current ? 'muted' : 'listening');
    } catch {
      setError('无法访问麦克风，请检查浏览器权限');
      setStatus('error');
      closeRequestedRef.current = true;
      cleanupRealtimeResources(true);
    }
  }, [cleanupRealtimeResources]);

  const handleRealtimeEvent = useCallback(
    (payload: RealtimeEventPayload) => {
      const eventType = payload.type || '';

      if (eventType === 'realtime_session_started') {
        setRemoteSessionId(payload.session_id || '');
        setVoiceId(payload.voice_id || '');
        void startMicrophone();
        return;
      }

      if (eventType === 'conversation_initiation_metadata') {
        setConversationId(
          payload.conversation_initiation_metadata_event?.conversation_id || ''
        );
        return;
      }

      if (eventType === 'user_transcript') {
        const transcript = extractUserTranscript(payload);
        if (transcript) {
          setLastUserText(transcript);
          setStatus('thinking');
        }
        return;
      }

      if (eventType === 'agent_response' || eventType === 'agent_response_correction') {
        const agentText = extractAgentText(payload);
        if (agentText) {
          setLastAgentText(agentText);
        }
        return;
      }

      if (eventType === 'agent_response_complete') {
        setStatus(mutedRef.current ? 'muted' : 'listening');
        return;
      }

      if (eventType === 'interruption') {
        stopPlayback();
        setStatus(mutedRef.current ? 'muted' : 'listening');
        return;
      }

      if (eventType === 'conversation_ended' || eventType === 'conversation_end') {
        closeRequestedRef.current = true;
        cleanupRealtimeResources(false);
        setStatus('ended');
        return;
      }

      if (eventType === 'error') {
        setError(payload.message || '实时通话出错');
        setStatus('error');
      }
    },
    [cleanupRealtimeResources, startMicrophone, stopPlayback]
  );

  const handleSocketMessage = useCallback(
    async (event: MessageEvent) => {
      if (!mountedRef.current) {
        return;
      }

      if (typeof event.data === 'string') {
        try {
          handleRealtimeEvent(JSON.parse(event.data) as RealtimeEventPayload);
        } catch {
          handleRealtimeEvent({ type: 'error', message: '实时通话消息解析失败' });
        }
        return;
      }

      const audioData =
        event.data instanceof Blob
            ? await event.data.arrayBuffer()
          : event.data instanceof ArrayBuffer
            ? event.data
            : ArrayBuffer.isView(event.data)
              ? cloneArrayBufferView(event.data)
              : null;

      if (audioData) {
        await playPcmAudio(audioData);
      }
    },
    [handleRealtimeEvent, playPcmAudio]
  );

  useEffect(() => {
    mutedRef.current = isMuted;
  }, [isMuted]);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    if (!isOpen) {
      closeRequestedRef.current = true;
      cleanupRealtimeResources(false);
      mountedRef.current = false;
      setAudioSuppressed(false);
      return;
    }

    let cancelled = false;
    mountedRef.current = true;
    closeRequestedRef.current = false;
    mutedRef.current = false;
    setIsMuted(false);
    setAudioSuppressed(true);
    setStatus('connecting');
    setError('');
    setRemoteSessionId('');
    setVoiceId('');
    setConversationId('');
    setLastUserText('');
    setLastAgentText('');

    void openRealtimeVoiceSocket({ characterId, sessionId })
      .then((socket) => {
        if (cancelled) {
          socket.close();
          return;
        }

        socketRef.current = socket;
        socket.onopen = () => {
          if (!cancelled) {
            setStatus('connecting');
          }
        };
        socket.onmessage = (event) => {
          void handleSocketMessage(event);
        };
        socket.onerror = () => {
          if (!cancelled) {
            setError('实时通话连接失败');
            setStatus('error');
          }
        };
        socket.onclose = (event) => {
          if (cancelled || closeRequestedRef.current) {
            return;
          }
          stopInputCapture();
          stopPlayback();
          setStatus(event.wasClean ? 'ended' : 'error');
          if (!event.wasClean) {
            setError(event.reason || '实时通话连接已断开');
          }
        };
      })
      .catch((err: unknown) => {
        if (cancelled) {
          return;
        }
        setError(err instanceof Error ? err.message : '实时通话启动失败');
        setStatus('error');
      });

    return () => {
      cancelled = true;
      closeRequestedRef.current = true;
      cleanupRealtimeResources(true);
      mountedRef.current = false;
      setAudioSuppressed(false);
    };
  }, [
    characterId,
    cleanupRealtimeResources,
    handleSocketMessage,
    isOpen,
    requestKey,
    sessionId,
    setAudioSuppressed,
    stopInputCapture,
    stopPlayback,
  ]);

  const handleHangUp = useCallback(() => {
    closeRequestedRef.current = true;
    cleanupRealtimeResources(true);
    setAudioSuppressed(false);
    onClose();
  }, [cleanupRealtimeResources, onClose, setAudioSuppressed]);

  const handleRetry = useCallback(() => {
    closeRequestedRef.current = true;
    cleanupRealtimeResources(true);
    setRequestKey((value) => value + 1);
  }, [cleanupRealtimeResources]);

  const toggleMute = useCallback(() => {
    setIsMuted((previous) => {
      const next = !previous;
      mutedRef.current = next;
      mediaStreamRef.current?.getAudioTracks().forEach((track) => {
        track.enabled = !next;
      });
      if (status !== 'connecting' && status !== 'speaking' && status !== 'error') {
        setStatus(next ? 'muted' : 'listening');
      }
      return next;
    });
  }, [status]);

  if (!isOpen) return null;

  const statusDotClass = cn(
    'h-3 w-3 rounded-full',
    status === 'speaking' && 'bg-emerald-400 shadow-[0_0_24px_rgba(74,222,128,0.9)]',
    status === 'listening' && 'bg-cyan-400 shadow-[0_0_24px_rgba(34,211,238,0.8)]',
    status === 'thinking' && 'bg-amber-400 shadow-[0_0_24px_rgba(251,191,36,0.8)]',
    status === 'muted' && 'bg-zinc-400 shadow-[0_0_24px_rgba(161,161,170,0.6)]',
    status === 'ended' && 'bg-white/50 shadow-[0_0_24px_rgba(255,255,255,0.3)]',
    status === 'error' && 'bg-rose-400 shadow-[0_0_24px_rgba(251,113,133,0.8)]',
    status === 'connecting' && 'bg-white/70 shadow-[0_0_24px_rgba(255,255,255,0.35)]'
  );

  return (
    <div className="fixed inset-0 z-[100] flex min-h-0 flex-col overflow-hidden bg-[#05060a] text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.18),transparent_42%),linear-gradient(180deg,rgba(5,6,10,0.94),rgba(3,4,8,1))]" />

      <div className="relative z-10 flex items-center justify-between gap-4 border-b border-white/10 px-4 py-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl">
            <Sparkles className="h-5 w-5 text-cyan-300" />
          </div>
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-[0.28em] text-white/45">ElevenLabs Realtime</p>
            <h2 className="truncate text-lg font-semibold text-white sm:text-xl">{characterName}</h2>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={toggleMute}
            disabled={status === 'connecting' || status === 'error' || status === 'ended'}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/15 bg-white/5 text-white/80 transition-colors hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-45"
            title={isMuted ? '取消静音' : '静音'}
          >
            {isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </button>
          <button
            type="button"
            onClick={handleHangUp}
            className="inline-flex items-center gap-2 rounded-full border border-rose-400/30 bg-rose-500/10 px-4 py-2 text-sm font-medium text-rose-200 transition-colors hover:bg-rose-500/20 hover:text-white"
          >
            <PhoneOff className="h-4 w-4" />
            挂断
          </button>
        </div>
      </div>

      <div className="relative z-10 grid min-h-0 flex-1 gap-4 p-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(300px,0.65fr)] lg:p-6">
        <div className="flex min-h-0 flex-col rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-[0_24px_120px_rgba(0,0,0,0.45)] backdrop-blur-2xl sm:p-6">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className={statusDotClass} />
              <div>
                <p className="text-sm text-white/55">当前状态</p>
                <p className="text-2xl font-semibold tracking-tight">{statusCopy(status)}</p>
              </div>
            </div>
            <div className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-white/70">
              {remoteSessionId ? '已接通' : '连接中'}
            </div>
          </div>

          <div className="flex flex-1 items-center justify-center py-8">
            <div className="relative flex h-72 w-72 items-center justify-center">
              <div
                className={cn(
                  'absolute inset-0 rounded-full border border-white/10',
                  status === 'speaking' && 'animate-pulse border-emerald-400/40 bg-emerald-400/5',
                  status === 'listening' && 'animate-pulse border-cyan-400/35 bg-cyan-400/5',
                  status === 'thinking' && 'animate-pulse border-amber-400/35 bg-amber-400/5',
                  status === 'muted' && 'border-zinc-400/30 bg-zinc-400/5',
                  status === 'error' && 'border-rose-400/40 bg-rose-400/5'
                )}
              />
              <div className="absolute inset-8 rounded-full border border-white/10 bg-black/20" />
              <div className="relative flex h-44 w-44 items-center justify-center rounded-full border border-white/10 bg-black/35 shadow-inner shadow-black/40">
                {status === 'connecting' ? (
                  <Loader2 className="h-14 w-14 animate-spin text-white/85" />
                ) : status === 'error' ? (
                  <WifiOff className="h-14 w-14 text-rose-300" />
                ) : status === 'speaking' ? (
                  <Waves className="h-14 w-14 text-emerald-300" />
                ) : isMuted ? (
                  <MicOff className="h-14 w-14 text-zinc-300" />
                ) : (
                  <Mic
                    className={cn(
                      'h-14 w-14',
                      status === 'thinking' ? 'text-amber-300' : 'text-cyan-300'
                    )}
                  />
                )}
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white/80">
            <span className="font-medium text-white">{characterName}</span>
            <span className="mx-2 text-white/35">·</span>
            <span>{statusCopy(status)}</span>
          </div>
        </div>

        <div className="flex min-h-0 flex-col gap-4 rounded-3xl border border-white/10 bg-black/25 p-5 backdrop-blur-2xl">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.25em] text-white/40">Connection</p>
            <div className="mt-3 space-y-2 text-sm text-white/80">
              <div className="flex items-center justify-between gap-3">
                <span>Session</span>
                <span className="truncate text-white">{remoteSessionId || sessionId || '准备中'}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>Voice</span>
                <span className="truncate text-white/80">{voiceId || '等待 ElevenLabs'}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>Conversation</span>
                <span className="truncate text-white/80">{conversationId || '未返回'}</span>
              </div>
            </div>
          </div>

          <div className="min-h-0 flex-1 rounded-2xl border border-dashed border-white/10 bg-white/[0.03] p-4">
            <p className="text-xs uppercase tracking-[0.25em] text-white/40">Live transcript</p>
            <div className="mt-4 space-y-3 text-sm leading-relaxed text-white/75">
              <div>
                <p className="mb-1 text-xs text-white/35">You</p>
                <p className="rounded-2xl bg-cyan-500/10 px-3 py-2 text-white/85">
                  {lastUserText || '实时转写将在这里显示'}
                </p>
              </div>
              <div>
                <p className="mb-1 text-xs text-white/35">{characterName}</p>
                <p className="rounded-2xl bg-white/10 px-3 py-2 text-white/85">
                  {lastAgentText || 'AI 回复文本将在这里显示'}
                </p>
              </div>
            </div>
          </div>

          {error ? (
            <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 p-4 text-sm text-rose-100">
              <p className="font-medium text-white">通话启动失败</p>
              <p className="mt-1 text-rose-100/80">{error}</p>
              <div className="mt-4 flex gap-3">
                <button
                  type="button"
                  onClick={handleRetry}
                  className="rounded-full bg-white px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-white/90"
                >
                  重试
                </button>
                <button
                  type="button"
                  onClick={handleHangUp}
                  className="rounded-full border border-white/15 px-4 py-2 text-sm text-white transition-colors hover:bg-white/10"
                >
                  返回
                </button>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4 text-sm text-white/70">
              通话会持续采集麦克风音频并实时播放 ElevenLabs 回复。
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
