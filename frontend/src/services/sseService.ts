/**
 * SSE Chat Service
 *
 * Handles Server-Sent Events (SSE) for chat streaming.
 * Replaces WebSocket for text and image chat interactions.
 *
 * Usage:
 *   const stream = await sseService.streamChat({
 *     characterId: 'abc123',
 *     message: 'Hello!',
 *     sessionId: 'optional-session-id'
 *   });
 *
 *   for await (const event of stream) {
 *     switch (event.type) {
 *       case 'text_delta':
 *         // Append text chunk
 *         break;
 *       case 'image_done':
 *         // Display image
 *         break;
 *     }
 *   }
 */

import { auth } from '@/config/firebase';
import type {
  StoryProgressEvent,
  StoryTransitionEvent,
  StorySuggestionEvent,
  StoryCompletedEvent,
} from '@/types/story';

// ==================== SSE Event Types ====================

export type SSEEventType =
  | 'session_created'
  | 'user_message'
  | 'text_delta'
  | 'text_done'
  | 'image_generating'
  | 'image_done'
  | 'opening_message'
  | 'video_submitted'
  | 'video_completed'
  | 'video_failed'
  | 'video_intent_declined'
  | 'credit_update'
  | 'suggestions'
  | 'error'
  | 'heartbeat'
  | 'age_verification_required'
  | 'stream_end'
  // PRD v3: Gameplay events
  | 'scene_choices'
  | 'story_progress'
  | 'story_transition'
  | 'story_suggestion'
  | 'story_completed'
  | 'scene_node_action_started'
  | 'scene_node_action_done'
  | 'scene_node_action_failed'
  | 'scene_node_action_downgraded'
  // PRD v3: Debug events
  | 'context_update'
  // PRD v2026.02: Script System events
  | 'script_state_updated'
  | 'quest_progress_updated'
  | 'intimacy_updated'
  | 'media_cue_triggered'
  | 'voice_note_pending'
  | 'voice_note_ready'
  | 'voice_note_failed'
  | 'video_ready'
  | 'audio_uploaded'
  | 'tool_call'
  | 'task_status'
  | 'thinking_delta'
  | 'thinking_done';

// ==================== Event Payloads ====================

export interface SessionCreatedEvent {
  session_id: string;
  character_id: string;
  is_new: boolean;
}

export interface UserMessageEvent {
  message_id: string;
  content: string;
  timestamp: string;
}

export interface TextDeltaEvent {
  delta: string;
}

export interface TextDoneEvent {
  message_id: string;
  full_content: string;
  audio_available?: boolean;
}

export interface ImageGeneratingEvent {
  status: string;
  estimated_time_seconds: number;
}

export interface ImageDoneEvent {
  message_id: string;
  image_url: string;
}

export interface OpeningMessageEvent {
  message_id: string;
  content: string;
  is_opening: boolean;
}

export interface VideoSubmittedEvent {
  task_id: string;
  session_id: string;
  estimated_time_seconds: number;
  holding_message?: string;
  holding_message_id?: string;
}

export interface VideoCompletedEvent {
  task_id: string;
  session_id: string;
  message_id: string;
  video_url: string;
}

export interface VideoFailedEvent {
  task_id: string;
  session_id: string;
  error: string;
  error_code?: string;
}

export interface VideoIntentDeclinedEvent {
  message: string;
  show_photo_button: boolean;
  character_id?: string;
}

export interface CreditUpdateEvent {
  balance: number;
  deducted: number;
  operation?: string;
}

export interface SuggestionsEvent {
  suggestions: string[];
}

export interface ErrorEvent {
  message: string;
  error_code?: string;
  details?: Record<string, unknown>;
}

export interface HeartbeatEvent {
  timestamp: string;
}

export interface StreamEndEvent {
  session_id: string;
  message_count: number;
  summary?: Record<string, unknown>;
}

export interface AgeVerificationRequiredEvent {
  message: string;
  reason: string;
}

// PRD v3: Gameplay Event Payloads
export interface SceneChoicesEvent {
  choices: string[];
  scene_state?: {
    description: string;
    active: boolean;
    turn: number;
    location?: string;
    narrative_phase?: string;
  };
}

export interface SceneNodeActionStartedEvent {
  node_id: string;
  action_type: 'send_image' | 'send_voice' | 'send_video' | 'none';
  action_id?: string;
  payload?: Record<string, unknown>;
}

export interface SceneNodeActionDoneEvent {
  node_id: string;
  action_type: 'send_image' | 'send_voice' | 'send_video' | 'none';
  action_id?: string;
  result?: Record<string, unknown>;
}

export interface SceneNodeActionFailedEvent {
  node_id: string;
  action_type: 'send_image' | 'send_voice' | 'send_video' | 'none';
  action_id?: string;
  reason: string;
  error_code?: string;
}

export interface SceneNodeActionDowngradedEvent {
  node_id: string;
  from_action: 'send_image' | 'send_voice' | 'send_video' | 'none';
  to_action: 'send_image' | 'send_voice' | 'send_video' | 'none' | 'fallback_text';
  reason?: string;
}

// PRD v3: Debug Event Payload
export interface ContextUpdateEvent {
  character_id: string;
  state?: {
    mood?: string;
    energy?: number;
  };
  relationship?: {
    stage?: string;
    trust?: number;
    intimacy?: number;
  };
  memory?: {
    facts_count?: number;
    episodes_count?: number;
  };
  orchestrator?: {
    intent?: string;
    sentiment?: string;
    depth?: string;
    event_type?: string;
  };
  prompt_mode?: string;
}

// PRD v2026.02: Script System Event Payloads
export interface ScriptStateUpdatedEvent {
  session_id: string;
  script_id: string;
  previous_state: string;
  current_state: 'Start' | 'Build' | 'Climax' | 'Resolve';
  quest_progress: number;
  timestamp: string;
}

export interface QuestProgressUpdatedEvent {
  session_id: string;
  script_id: string;
  quest_progress: number; // 0-100
  current_state: 'Start' | 'Build' | 'Climax' | 'Resolve';
  hint_chips?: string[];
}

export interface IntimacyUpdatedEvent {
  character_id: string;
  user_id?: string;
  previous_value?: number;
  current_value?: number;
  change_amount?: number;
  reason?: string;
  timestamp?: string;
  intimacy?: number;
  change?: number;
  relationship_stage?: string;
  trust?: number;
  desire?: number;
  dependency?: number;
  gm_current_node?: string;
  dashboard?: {
    stage?: string;
    intimacy?: number;
    trust?: number;
    desire?: number;
    dependency?: number;
    delta?: Record<string, number>;
  };
}

export interface MediaCueTriggeredEvent {
  cue_id: string;
  media_type: 'image' | 'video' | 'voice_note';
  placeholder_message_id: string;
  estimated_time_seconds?: number;
  script_context?: {
    script_id: string;
    state: string;
    quest_progress: number;
  };
}

export interface VoiceNotePendingEvent {
  message_id: string;
}

export interface VoiceNoteReadyEvent {
  message_id: string;
  audio_url: string;
  duration: number; // seconds
  cost?: number;
  script_context?: {
    script_id: string;
    cue_id?: string;
  };
}

export interface VideoReadyEvent {
  message_id: string;
  video_url: string;
  duration?: number; // seconds
  cost?: number;
  source: 'img2video' | 'script_cue';
  script_context?: {
    script_id: string;
    cue_id?: string;
  };
}

export interface VoiceNoteFailedEvent {
  message_id: string;
  reason?: string;
}

export interface AudioUploadedEvent {
  session_id: string;
  message_id: string;
  audio_url: string;
}

export interface TaskStatusEvent {
  event_id: string;
  message_id: string;
  task_id: string;
  skill_name: string;
  status: 'pending' | 'progress' | 'ready' | 'failed';
  created_at: string;
  updated_at: string;
  payload: Record<string, unknown>;
  error_code?: string;
}

export interface ThinkingDeltaEvent {
  delta: string;
}

export interface ThinkingDoneEvent {
  full_content: string;
}

export interface ToolCallEvent {
  tool_name: string;
  phase: 'requested' | 'submitted' | 'completed' | 'failed' | string;
  args?: Record<string, unknown>;
  task_id?: string;
  status?: 'pending' | 'progress' | 'ready' | 'failed' | string;
  message?: string;
}

// ==================== Union Type ====================

export type SSEEventData =
  | { type: 'session_created'; data: SessionCreatedEvent }
  | { type: 'user_message'; data: UserMessageEvent }
  | { type: 'text_delta'; data: TextDeltaEvent }
  | { type: 'text_done'; data: TextDoneEvent }
  | { type: 'image_generating'; data: ImageGeneratingEvent }
  | { type: 'image_done'; data: ImageDoneEvent }
  | { type: 'opening_message'; data: OpeningMessageEvent }
  | { type: 'video_submitted'; data: VideoSubmittedEvent }
  | { type: 'video_completed'; data: VideoCompletedEvent }
  | { type: 'video_failed'; data: VideoFailedEvent }
  | { type: 'video_intent_declined'; data: VideoIntentDeclinedEvent }
  | { type: 'credit_update'; data: CreditUpdateEvent }
  | { type: 'suggestions'; data: SuggestionsEvent }
  | { type: 'error'; data: ErrorEvent }
  | { type: 'heartbeat'; data: HeartbeatEvent }
  | { type: 'age_verification_required'; data: AgeVerificationRequiredEvent }
  | { type: 'stream_end'; data: StreamEndEvent }
  // PRD v3: Gameplay events
  | { type: 'scene_choices'; data: SceneChoicesEvent }
  | { type: 'story_progress'; data: StoryProgressEvent }
  | { type: 'story_transition'; data: StoryTransitionEvent }
  | { type: 'story_suggestion'; data: StorySuggestionEvent }
  | { type: 'story_completed'; data: StoryCompletedEvent }
  | { type: 'scene_node_action_started'; data: SceneNodeActionStartedEvent }
  | { type: 'scene_node_action_done'; data: SceneNodeActionDoneEvent }
  | { type: 'scene_node_action_failed'; data: SceneNodeActionFailedEvent }
  | { type: 'scene_node_action_downgraded'; data: SceneNodeActionDowngradedEvent }
  // PRD v3: Debug events
  | { type: 'context_update'; data: ContextUpdateEvent }
  // PRD v2026.02: Script System events
  | { type: 'script_state_updated'; data: ScriptStateUpdatedEvent }
  | { type: 'quest_progress_updated'; data: QuestProgressUpdatedEvent }
  | { type: 'intimacy_updated'; data: IntimacyUpdatedEvent }
  | { type: 'media_cue_triggered'; data: MediaCueTriggeredEvent }
  | { type: 'voice_note_pending'; data: VoiceNotePendingEvent }
  | { type: 'voice_note_ready'; data: VoiceNoteReadyEvent }
  | { type: 'voice_note_failed'; data: VoiceNoteFailedEvent }
  | { type: 'video_ready'; data: VideoReadyEvent }
  | { type: 'audio_uploaded'; data: AudioUploadedEvent }
  | { type: 'tool_call'; data: ToolCallEvent }
  | { type: 'task_status'; data: TaskStatusEvent }
  | { type: 'thinking_delta'; data: ThinkingDeltaEvent }
  | { type: 'thinking_done'; data: ThinkingDoneEvent };

export type SSEStreamEvent = SSEEventData & { id?: string };

// ==================== Request Types ====================

export interface ChatStreamRequest {
  characterId: string;
  message: string;
  sessionId?: string;
  voiceMode?: 'on' | 'off' | 'auto';
  resumeToken?: string;
  idempotencyKey?: string;
  lastEventId?: string;
  isAdultOverride?: boolean;
}

// ==================== SSE Parser ====================

/**
 * Parse SSE text into events.
 * SSE format:
 *   event: event_type
 *   data: {"key": "value"}
 *
 *   (blank line separates events)
 */
function* parseSSE(text: string): Generator<SSEStreamEvent> {
  const lines = text.split('\n');
  let currentEventType: string | null = null;
  let currentData: string | null = null;
  let currentEventId: string | null = null;

  for (const line of lines) {
    if (line.startsWith('id: ')) {
      currentEventId = line.slice(4).trim();
    } else if (line.startsWith('event: ')) {
      currentEventType = line.slice(7).trim();
    } else if (line.startsWith('data: ')) {
      currentData = line.slice(6);
    } else if (line === '' && currentEventType && currentData) {
      // End of event
      try {
        const parsed = JSON.parse(currentData);
        yield {
          id: currentEventId || undefined,
          type: currentEventType as SSEEventType,
          data: parsed,
        } as SSEStreamEvent;
      } catch {
        console.warn('Failed to parse SSE data:', currentData);
      }
      currentEventId = null;
      currentEventType = null;
      currentData = null;
    }
  }
}

// ==================== SSE Service ====================

class SSEService {
  private baseUrl: string;
  private abortController: AbortController | null = null;
  private lastResumeToken: string | null = null;
  private lastEventId: string | null = null;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
  }

  private getDeviceFingerprint(): string {
    const key = 'aigirl_device_fingerprint';
    const fromStorage = localStorage.getItem(key);
    if (fromStorage) return fromStorage;
    const generated =
      (globalThis.crypto?.randomUUID?.() ||
        `fp_${Date.now()}_${Math.random().toString(36).slice(2, 12)}`);
    localStorage.setItem(key, generated);
    return generated;
  }

  /**
   * Get the current Firebase auth token.
   */
  private async getAuthToken(): Promise<string> {
    const user = auth.currentUser;
    if (!user) {
      throw new Error('User not authenticated');
    }
    return user.getIdToken();
  }

  /**
   * Abort any ongoing stream.
   */
  abort(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  /**
   * Stream chat messages using SSE.
   *
   * @param request Chat stream request
   * @returns Async generator yielding SSE events
   */
  async *streamChat(request: ChatStreamRequest): AsyncGenerator<SSEStreamEvent> {
    // Abort any existing stream
    this.abort();

    this.abortController = new AbortController();
    const { signal } = this.abortController;

    try {
      const token = await this.getAuthToken();
      const idempotencyKey =
        request.idempotencyKey ||
        `chat-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
      const seenEventIds = new Set<string>();

      const updateStreamMeta = (event: SSEStreamEvent): boolean => {
        const payload = event.data as unknown as Record<string, unknown>;
        const eventId =
          event.id || (typeof payload.event_id === 'string' ? payload.event_id : null);
        const resumeToken =
          typeof payload.resume_token === 'string' ? payload.resume_token : null;
        if (resumeToken) this.lastResumeToken = resumeToken;
        if (!eventId) return true;
        if (seenEventIds.has(eventId)) return false;
        seenEventIds.add(eventId);
        this.lastEventId = eventId;
        return true;
      };

      const response = await fetch(`${this.baseUrl}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          Accept: 'text/event-stream',
          'X-Device-Fingerprint': this.getDeviceFingerprint(),
          ...(request.lastEventId || this.lastEventId
            ? { 'Last-Event-ID': request.lastEventId || this.lastEventId || '' }
            : {}),
        },
        body: JSON.stringify({
          character_id: request.characterId,
          message: request.message,
          session_id: request.sessionId,
          voice_mode: request.voiceMode || 'auto',
          resume_token: request.resumeToken || this.lastResumeToken,
          idempotency_key: idempotencyKey,
          last_event_id: request.lastEventId || this.lastEventId,
          ...(request.isAdultOverride !== undefined && { is_adult_override: request.isAdultOverride }),
        }),
        signal,
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorData: ErrorEvent;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = {
            message: errorText || `HTTP ${response.status}`,
            error_code: `http_${response.status}`,
          };
        }
        yield { type: 'error', data: errorData };
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        yield {
          type: 'error',
          data: { message: 'No response body', error_code: 'no_body' },
        };
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          // Process any remaining buffer
          if (buffer.trim()) {
            for (const event of parseSSE(buffer + '\n\n')) {
              if (!updateStreamMeta(event)) continue;
              yield event;
            }
          }
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        // Process complete events (separated by double newlines)
        const parts = buffer.split('\n\n');

        // Keep the last potentially incomplete part in the buffer
        buffer = parts.pop() || '';

        // Process complete events
        for (const part of parts) {
          if (part.trim()) {
            for (const event of parseSSE(part + '\n\n')) {
              if (!updateStreamMeta(event)) continue;
              yield event;
            }
          }
        }
      }
    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('SSE stream aborted');
        return;
      }
      const message = error instanceof Error ? error.message : 'Stream error';
      yield {
        type: 'error',
        data: {
          message,
          error_code: 'stream_error',
        },
      };
    } finally {
      this.abortController = null;
    }
  }

  /**
   * Check if a stream is currently active.
   */
  isStreaming(): boolean {
    return this.abortController !== null;
  }
}

// Export singleton instance
export const sseService = new SSEService();

