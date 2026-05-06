import { auth } from '@/config/firebase';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export interface RealtimeVoiceSocketRequest {
  characterId: string;
  sessionId?: string | null;
}

export async function openRealtimeVoiceSocket(
  request: RealtimeVoiceSocketRequest
): Promise<WebSocket> {
  const token = await auth.currentUser?.getIdToken();
  if (!token) {
    throw new Error('请先登录后再发起实时通话');
  }

  const socket = new WebSocket(
    buildRealtimeVoiceWebSocketUrl({
      characterId: request.characterId,
      sessionId: request.sessionId,
      token,
    })
  );
  socket.binaryType = 'arraybuffer';
  return socket;
}

export function buildRealtimeVoiceWebSocketUrl({
  characterId,
  sessionId,
  token,
}: RealtimeVoiceSocketRequest & { token: string }): string {
  const url = new URL('/api/realtime-voice/ws', resolveWebSocketOrigin(BASE_URL));
  url.searchParams.set('character_id', characterId);
  if (sessionId) {
    url.searchParams.set('session_id', sessionId);
  }
  url.searchParams.set('token', token);
  return url.toString();
}

function resolveWebSocketOrigin(apiBaseUrl: string): string {
  const browserOrigin =
    typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
  const apiUrl = new URL(apiBaseUrl, browserOrigin);
  apiUrl.protocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
  return apiUrl.origin;
}
