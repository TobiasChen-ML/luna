import { auth } from '@/config/firebase';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export interface VoiceTurnResult {
  audioBlob: Blob;
  transcriptIn: string;
  transcriptOut: string;
  emotion: string;
  creditsUsed: number;
  sessionTotalSeconds: number;
}

export async function postVoiceTurn(params: {
  audioBlob: Blob;
  sessionId: string;
  characterId: string;
  inputDurationSeconds: number;
  language?: string;
}): Promise<VoiceTurnResult> {
  const token = await auth.currentUser?.getIdToken();

  const formData = new FormData();
  formData.append('audio', params.audioBlob, 'audio.webm');
  formData.append('session_id', params.sessionId);
  formData.append('character_id', params.characterId);
  formData.append('input_duration', String(params.inputDurationSeconds));
  formData.append('language', params.language ?? 'zh');

  const res = await fetch(`${BASE_URL}/voice/turn`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
    credentials: 'include',
  });

  if (!res.ok) {
    if (res.status === 402) throw new Error('积分不足，无法继续通话');
    if (res.status === 422) throw new Error('无法识别语音，请再试一次');
    throw new Error(`通话出错 (${res.status})`);
  }

  const audioBlob = await res.blob();

  const decode = (h: string | null) => {
    if (!h) return '';
    try {
      return decodeURIComponent(h);
    } catch {
      return h;
    }
  };

  return {
    audioBlob,
    transcriptIn: decode(res.headers.get('X-Transcript-In')),
    transcriptOut: decode(res.headers.get('X-Transcript-Out')),
    emotion: res.headers.get('X-Emotion') ?? 'default',
    creditsUsed: parseFloat(res.headers.get('X-Credits-Used') ?? '0'),
    sessionTotalSeconds: parseFloat(res.headers.get('X-Session-Total-Seconds') ?? '0'),
  };
}

