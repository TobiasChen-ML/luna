import type { NDJSONSegment } from '@/utils/ndjsonParser';

export type { NDJSONSegment, NDJSONSegmentType } from '@/utils/ndjsonParser';

export type MessageType = 'text' | 'image' | 'video' | 'voice_note';
export type MessageStatus = 'generating' | 'ready' | 'failed';
export type VoiceMode = 'on' | 'off' | 'auto';

export interface MessageScriptContext {
  script_id: string;
  state: string;
  quest_progress: number;
  cue_id?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  image_url?: string;
  video_url?: string;
  audio_url?: string;
  timestamp: string;
  character_id?: string;
  speaker_id?: string;
  speaker_name?: string;
  segments?: NDJSONSegment[];
  isNDJSON?: boolean;
  message_type?: MessageType;
  status?: MessageStatus;
  duration?: number;
  cost?: number;
  transcript?: string;
  error?: string;
  script_context?: MessageScriptContext;
  metadata?: {
    source?: 'voice_call' | 'text_chat' | 'group_chat';
    assistant_id?: string;
    timestamp?: string;
    [key: string]: any;
  };
}

export interface GroupChatSession {
  id: string;
  user_id: string;
  participants: string[];
  created_at: string;
  updated_at: string;
  message_count: number;
  messages?: Message[];
}

export interface GroupChatStreamRequest {
  participants: string[];
  message: string;
  session_id?: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  character_id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  messages?: Message[]; // Optional - use MessageListResponse for paginated messages
}

export interface MessageListResponse {
  messages: Message[];
  has_more: boolean;
  oldest_message_id: string | null;
  total_count: number;
}

export interface SendMessageRequest {
  character_id: string;
  message: string;
  session_id?: string;
}

export interface SendMessageResponse {
  message: Message;
  session_id: string;
  ai_response: Message;
}

// ==================== Video Task Tracking ====================

export interface PendingVideoTask {
  taskId: string;
  sessionId: string;
  holdingMessageId?: string;
  holdingMessage?: string;
  estimatedTimeSeconds: number;
  submittedAt: Date;
  status: 'pending' | 'completed' | 'failed';
}

// ==================== SSE Chat Request ====================

export interface ChatStreamRequest {
  character_id: string;
  message: string;
  session_id?: string;
  voice_mode?: VoiceMode;
}
