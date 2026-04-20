import { useEffect, useMemo, useState } from 'react';
import { Loader2, Mic, PhoneOff, Sparkles, WifiOff } from 'lucide-react';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useConnectionState,
  useLocalParticipant,
  useRemoteParticipants,
  useSpeakingParticipants,
  useRoomContext,
} from '@livekit/components-react';
import { ConnectionState } from 'livekit-client';
import { cn } from '@/utils/cn';
import { useAudioFocus } from '@/contexts/AudioFocusContext';
import {
  generateRealtimeVoiceSession,
  type RealtimeVoiceSession,
} from '@/services/realtimeVoiceService';

type CallStatus = 'listening' | 'thinking' | 'speaking' | 'reconnecting' | 'connecting';

interface RealtimeCallModalProps {
  isOpen: boolean;
  characterId: string;
  sessionId?: string | null;
  characterName: string;
  onClose: () => void;
}

function statusCopy(status: CallStatus): string {
  switch (status) {
    case 'speaking':
      return '说话中';
    case 'thinking':
      return '思考中';
    case 'reconnecting':
      return 'AI 助手开小差了，正在重新连接';
    case 'connecting':
      return '连接中';
    case 'listening':
    default:
      return '聆听中';
  }
}

function RealtimeCallSurface({
  roomConfig,
  characterName,
  onHangUp,
}: {
  roomConfig: RealtimeVoiceSession;
  characterName: string;
  onHangUp: () => void;
}) {
  const connectionState = useConnectionState();
  const remoteParticipants = useRemoteParticipants();
  const speakingParticipants = useSpeakingParticipants();
  const { localParticipant } = useLocalParticipant();
  const room = useRoomContext();
  const { setAudioSuppressed } = useAudioFocus();
  const [reconnectHint, setReconnectHint] = useState(false);
  const [hasSeenAgent, setHasSeenAgent] = useState(false);

  useEffect(() => {
    setAudioSuppressed(true);
    return () => setAudioSuppressed(false);
  }, [setAudioSuppressed]);

  useEffect(() => {
    if (connectionState !== ConnectionState.Connected) {
      return;
    }

    if (remoteParticipants.length > 0) {
      setHasSeenAgent(true);
      setReconnectHint(false);
      return;
    }

    const timer = window.setTimeout(() => {
      setReconnectHint(true);
    }, 10000);

    return () => window.clearTimeout(timer);
  }, [connectionState, remoteParticipants.length]);

  useEffect(() => {
    if (remoteParticipants.length > 0) {
      setHasSeenAgent(true);
      setReconnectHint(false);
      return;
    }

    if (hasSeenAgent && connectionState === ConnectionState.Connected) {
      setReconnectHint(true);
    }
  }, [connectionState, hasSeenAgent, remoteParticipants.length]);

  const activeSpeakerIdentity = speakingParticipants.find(
    (participant) => participant.identity !== localParticipant.identity
  )?.identity;

  const status = useMemo<CallStatus>(() => {
    if (connectionState !== ConnectionState.Connected) {
      return 'connecting';
    }

    if (reconnectHint) {
      return 'reconnecting';
    }

    if (activeSpeakerIdentity) {
      return 'speaking';
    }

    if (remoteParticipants.length === 0) {
      return hasSeenAgent ? 'reconnecting' : 'thinking';
    }

    return 'listening';
  }, [
    activeSpeakerIdentity,
    connectionState,
    hasSeenAgent,
    reconnectHint,
    remoteParticipants.length,
  ]);

  const statusDotClass = cn(
    'h-3 w-3 rounded-full',
    status === 'speaking' && 'bg-emerald-400 shadow-[0_0_24px_rgba(74,222,128,0.9)]',
    status === 'listening' && 'bg-cyan-400 shadow-[0_0_24px_rgba(34,211,238,0.8)]',
    status === 'thinking' && 'bg-amber-400 shadow-[0_0_24px_rgba(251,191,36,0.8)]',
    status === 'reconnecting' && 'bg-rose-400 shadow-[0_0_24px_rgba(251,113,133,0.8)]',
    status === 'connecting' && 'bg-white/70 shadow-[0_0_24px_rgba(255,255,255,0.35)]'
  );

  return (
    <div className="relative flex h-full min-h-0 flex-col overflow-hidden bg-[#05060a] text-white">
      <RoomAudioRenderer />

      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-0 h-[520px] w-[520px] -translate-x-1/2 rounded-full bg-cyan-500/20 blur-[140px]" />
        <div className="absolute right-0 top-32 h-[380px] w-[380px] rounded-full bg-fuchsia-500/15 blur-[140px]" />
        <div className="absolute bottom-0 left-0 h-[360px] w-[360px] rounded-full bg-amber-500/10 blur-[140px]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_45%),linear-gradient(180deg,rgba(7,8,12,0.72),rgba(3,4,8,0.96))]" />
      </div>

      <div className="relative z-10 flex min-h-0 flex-1 flex-col px-4 py-4 sm:px-6 sm:py-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl">
              <Sparkles className="h-5 w-5 text-cyan-300" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-white/45">LiveKit Call</p>
              <h2 className="text-lg font-semibold text-white sm:text-xl">{characterName}</h2>
            </div>
          </div>

          <button
            type="button"
            onClick={async () => {
              await room.disconnect();
              onHangUp();
            }}
            className="inline-flex items-center gap-2 rounded-full border border-rose-400/30 bg-rose-500/10 px-4 py-2 text-sm font-medium text-rose-200 transition-colors hover:bg-rose-500/20 hover:text-white"
          >
            <PhoneOff className="h-4 w-4" />
            挂断
          </button>
        </div>

        <div className="mt-6 grid flex-1 gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.6fr)]">
          <div className="relative flex min-h-0 flex-col overflow-hidden rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-[0_24px_120px_rgba(0,0,0,0.45)] backdrop-blur-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className={statusDotClass} />
                <div>
                  <p className="text-sm text-white/55">当前状态</p>
                  <p className="text-2xl font-semibold tracking-tight">{statusCopy(status)}</p>
                </div>
              </div>
              <div className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-white/70">
                {remoteParticipants.length > 0 ? `${remoteParticipants.length} 位在线` : '等待 AI 助手'}
              </div>
            </div>

            <div className="mt-8 flex flex-1 items-center justify-center">
              <div className="relative flex h-72 w-72 items-center justify-center">
                <div
                  className={cn(
                    'absolute inset-0 rounded-full border border-white/10',
                    status === 'speaking' && 'animate-pulse border-emerald-400/40',
                    status === 'listening' && 'animate-pulse border-cyan-400/35',
                    status === 'thinking' && 'animate-pulse border-amber-400/35',
                    status === 'reconnecting' && 'animate-pulse border-rose-400/40'
                  )}
                />
                <div
                  className={cn(
                    'absolute inset-6 rounded-full border border-white/10',
                    status === 'speaking' && 'bg-emerald-400/10',
                    status === 'listening' && 'bg-cyan-400/10',
                    status === 'thinking' && 'bg-amber-400/10',
                    status === 'reconnecting' && 'bg-rose-400/10'
                  )}
                />
                <div className="relative flex h-44 w-44 items-center justify-center rounded-full border border-white/10 bg-black/30 shadow-inner shadow-black/40">
                  {status === 'connecting' ? (
                    <Loader2 className="h-14 w-14 animate-spin text-white/85" />
                  ) : status === 'reconnecting' ? (
                    <WifiOff className="h-14 w-14 text-rose-300" />
                  ) : (
                    <Mic
                      className={cn(
                        'h-14 w-14',
                        status === 'speaking' && 'text-emerald-300',
                        status === 'listening' && 'text-cyan-300',
                        status === 'thinking' && 'text-amber-300'
                      )}
                    />
                  )}
                </div>
              </div>
            </div>

            <div className="mt-4 rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white/80">
              <span className="font-medium text-white">{characterName}</span>
              <span className="mx-2 text-white/35">·</span>
              <span>{statusCopy(status)}</span>
            </div>
          </div>

          <div className="flex min-h-0 flex-col gap-4 rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-2xl">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.25em] text-white/40">Connection</p>
              <div className="mt-2 space-y-2 text-sm text-white/80">
                <div className="flex items-center justify-between gap-3">
                  <span>Room</span>
                  <span className="truncate text-white">{roomConfig.roomName}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Server</span>
                  <span className="truncate text-white/80">{roomConfig.serverUrl}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Participants</span>
                  <span className="text-white">{remoteParticipants.length + 1}</span>
                </div>
              </div>
            </div>

            <div className="flex-1 rounded-2xl border border-dashed border-white/10 bg-white/[0.03] p-4">
              <p className="text-xs uppercase tracking-[0.25em] text-white/40">Agent hints</p>
              <div className="mt-3 space-y-3 text-sm leading-relaxed text-white/75">
                <p>聆听中：等待你的发言并持续收音。</p>
                <p>思考中：AI 正在处理上下文和回复。</p>
                <p>说话中：AI 助手正在播报回复。</p>
              </div>
              {reconnectHint && (
                <div className="mt-4 rounded-xl border border-rose-400/20 bg-rose-500/10 p-3 text-sm text-rose-100">
                  AI 助手开小差了，正在重新连接
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/8 to-transparent p-4 text-sm text-white/70">
              请保持此窗口打开，麦克风与远端语音会在这里处理。
            </div>
          </div>
        </div>
      </div>
    </div>
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [roomConfig, setRoomConfig] = useState<RealtimeVoiceSession | null>(null);
  const [requestKey, setRequestKey] = useState(0);

  useEffect(() => {
    if (!isOpen) {
      setAudioSuppressed(false);
      setLoading(false);
      setError('');
      setRoomConfig(null);
      return;
    }

    setAudioSuppressed(true);
    setLoading(true);
    setError('');
    setRoomConfig(null);

    let cancelled = false;
    void generateRealtimeVoiceSession({ character_id: characterId, session_id: sessionId })
      .then((session) => {
        if (cancelled) return;
        setRoomConfig(session);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        console.error('Failed to generate realtime voice session:', err);
        setError(err instanceof Error ? err.message : 'Failed to start realtime call.');
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [characterId, isOpen, requestKey, sessionId, setAudioSuppressed]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] bg-black">
      {loading && (
        <div className="flex h-full items-center justify-center">
          <div className="space-y-4 text-center">
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-cyan-300" />
            <p className="text-sm text-white/65">正在准备通话房间...</p>
          </div>
        </div>
      )}

      {error && !loading && (
        <div className="flex h-full items-center justify-center p-6">
          <div className="max-w-md rounded-3xl border border-white/10 bg-white/5 p-6 text-center text-white shadow-[0_24px_100px_rgba(0,0,0,0.45)] backdrop-blur-xl">
            <p className="text-lg font-semibold">通话启动失败</p>
            <p className="mt-2 text-sm text-white/65">{error}</p>
            <div className="mt-6 flex items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => setRequestKey((value) => value + 1)}
                className="rounded-full bg-white px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-white/90"
              >
                重试
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full border border-white/15 px-4 py-2 text-sm text-white transition-colors hover:bg-white/10"
              >
                返回
              </button>
            </div>
          </div>
        </div>
      )}

      {roomConfig && !loading && !error && (
        <LiveKitRoom
          serverUrl={roomConfig.serverUrl}
          token={roomConfig.token}
          connect
          audio
          video={false}
          onDisconnected={() => {
            setAudioSuppressed(false);
            onClose();
          }}
        >
          <RealtimeCallSurface
            roomConfig={roomConfig}
            characterName={characterName}
            onHangUp={onClose}
          />
        </LiveKitRoom>
      )}
    </div>
  );
}
