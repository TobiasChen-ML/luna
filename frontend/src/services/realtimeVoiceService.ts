import { api } from '@/services/api';

export interface RealtimeVoiceSessionResponse {
  token: string;
  room?: string;
  room_name?: string;
  livekit_url?: string;
  server_url?: string;
  url?: string;
}

export interface RealtimeVoiceSessionRequest {
  character_id: string;
  session_id?: string | null;
}

export interface RealtimeVoiceSession {
  token: string;
  roomName: string;
  serverUrl: string;
}

export async function generateRealtimeVoiceSession(
  request: RealtimeVoiceSessionRequest
): Promise<RealtimeVoiceSession> {
  const response = await api.post<RealtimeVoiceSessionResponse>('/voice/generate_token', {
    character_id: request.character_id,
    session_id: request.session_id ?? undefined,
  });

  const serverUrl =
    response.data.livekit_url ||
    response.data.server_url ||
    response.data.url ||
    import.meta.env.VITE_LIVEKIT_URL ||
    import.meta.env.VITE_LIVEKIT_SERVER_URL ||
    '';

  const roomName = response.data.room_name || response.data.room || '';

  if (!response.data.token || !roomName || !serverUrl) {
    throw new Error('Invalid realtime voice session response');
  }

  return {
    token: response.data.token,
    roomName,
    serverUrl,
  };
}
