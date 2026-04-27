/**
 * Notification Service
 *
 * Provides a global SSE connection for receiving async notifications
 * such as video generation completion, credit updates, etc.
 *
 * This service should be initialized once on app startup and maintained
 * throughout the user's session.
 *
 * Usage:
 *   // In App.tsx or a top-level provider
 *   useEffect(() => {
 *     if (isAuthenticated) {
 *       notificationService.connect();
 *       notificationService.on('video_completed', handleVideoComplete);
 *     }
 *     return () => notificationService.disconnect();
 *   }, [isAuthenticated]);
 */

import { auth } from '@/config/firebase';

// ==================== Notification Event Types ====================

export type NotificationEventType =
  | 'video_completed'
  | 'video_failed'
  | 'image_done'
  | 'image_failed'
  | 'credit_update'
  | 'audio_uploaded'
  | 'task_status'
  | 'heartbeat'
  | 'error';

export interface VideoCompletedNotification {
  task_id: string;
  session_id: string;
  message_id: string;
  video_url: string;
}

export interface VideoFailedNotification {
  task_id: string;
  session_id: string;
  error: string;
  error_code?: string;
}

export interface ImageDoneNotification {
  message_id: string; // used as task_id for correlation
  image_url: string;
  task_id?: string;
  session_id?: string;
  holding_message_id?: string;
}

export interface ImageFailedNotification {
  task_id: string;
  session_id: string;
  error: string;
  error_code?: string;
  holding_message_id?: string;
}

export interface CreditUpdateNotification {
  balance: number;
  deducted: number;
  operation?: string;
}

export interface AudioUploadedNotification {
  session_id: string;
  message_id: string;
  audio_url: string;
}

export interface TaskStatusNotification {
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

export interface HeartbeatNotification {
  timestamp: string;
}

export interface ErrorNotification {
  message: string;
  error_code?: string;
}

export type NotificationPayload = {
  video_completed: VideoCompletedNotification;
  video_failed: VideoFailedNotification;
  image_done: ImageDoneNotification;
  image_failed: ImageFailedNotification;
  credit_update: CreditUpdateNotification;
  audio_uploaded: AudioUploadedNotification;
  task_status: TaskStatusNotification;
  heartbeat: HeartbeatNotification;
  error: ErrorNotification;
};

type NotificationHandler<T extends NotificationEventType> = (
  data: NotificationPayload[T]
) => void;

// ==================== Connection States ====================

export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting';

// ==================== Notification Service ====================

class NotificationService {
  private baseUrl: string;
  private abortController: AbortController | null = null;
  private handlers: Map<NotificationEventType, Set<NotificationHandler<any>>> = new Map();
  private connectionState: ConnectionState = 'disconnected';
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000; // Start with 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private stateChangeHandlers: Set<(state: ConnectionState) => void> = new Set();

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
  }

  /**
   * Get the current connection state.
   */
  getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  /**
   * Subscribe to connection state changes.
   */
  onStateChange(handler: (state: ConnectionState) => void): () => void {
    this.stateChangeHandlers.add(handler);
    return () => this.stateChangeHandlers.delete(handler);
  }

  private setConnectionState(state: ConnectionState): void {
    if (this.connectionState !== state) {
      this.connectionState = state;
      this.stateChangeHandlers.forEach((handler) => handler(state));
    }
  }

  /**
   * Get the current Firebase auth token.
   */
  private async getAuthToken(): Promise<string | null> {
    const user = auth.currentUser;
    if (!user) {
      return null;
    }
    return user.getIdToken();
  }

  /**
   * Parse SSE events from text.
   */
  private *parseSSE(text: string): Generator<{ type: NotificationEventType; data: any }> {
    const lines = text.split('\n');
    let currentEventType: string | null = null;
    let currentData: string | null = null;

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEventType = line.slice(7).trim();
      } else if (line.startsWith('data: ')) {
        currentData = line.slice(6);
      } else if (line === '' && currentEventType && currentData) {
        try {
          const parsed = JSON.parse(currentData);
          yield {
            type: currentEventType as NotificationEventType,
            data: parsed,
          };
        } catch {
          console.warn('Failed to parse notification data:', currentData);
        }
        currentEventType = null;
        currentData = null;
      }
    }
  }

  /**
   * Emit an event to all registered handlers.
   */
  private emit<T extends NotificationEventType>(type: T, data: NotificationPayload[T]): void {
    const handlers = this.handlers.get(type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(data);
        } catch (_e) {
          console.error(`Error in notification handler for ${type}:`, _e);
        }
      });
    }
  }

  /**
   * Register a handler for a notification type.
   * Returns an unsubscribe function.
   */
  on<T extends NotificationEventType>(
    type: T,
    handler: NotificationHandler<T>
  ): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    return () => {
      const handlers = this.handlers.get(type);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }

  /**
   * Remove all handlers for a notification type.
   */
  off(type: NotificationEventType): void {
    this.handlers.delete(type);
  }

  /**
   * Start the notification connection.
   */
  async connect(): Promise<void> {
    if (this.connectionState === 'connected' || this.connectionState === 'connecting') {
      return;
    }

    this.setConnectionState('connecting');

    try {
      await this.startStream();
    } catch (error) {
      if (error instanceof Error && error.message === 'User not authenticated') {
        this.setConnectionState('disconnected');
        return;
      }
      console.error('Failed to connect notification service:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Start the SSE stream.
   */
  private async startStream(): Promise<void> {
    // Clean up any existing connection
    this.abort();

    this.abortController = new AbortController();
    const { signal } = this.abortController;

    try {
      const token = await this.getAuthToken();
      if (!token) {
        throw new Error('User not authenticated');
      }

      const response = await fetch(`${this.baseUrl}/notifications/stream`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
        signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      this.setConnectionState('connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          console.log('Notification stream ended');
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        // Process complete events
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          if (part.trim()) {
            for (const event of this.parseSSE(part + '\n\n')) {
              this.emit(event.type, event.data);
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Notification stream aborted');
        return;
      }
      throw error;
    } finally {
      this.abortController = null;

      // If we were connected and the stream ended, try to reconnect
      if (this.connectionState === 'connected') {
        this.setConnectionState('disconnected');
        this.scheduleReconnect();
      }
    }
  }

  /**
   * Schedule a reconnection attempt with exponential backoff.
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.setConnectionState('disconnected');
      this.emit('error', {
        message: 'Failed to connect to notification service after multiple attempts',
        error_code: 'max_reconnect_attempts',
      });
      return;
    }

    this.setConnectionState('reconnecting');
    this.reconnectAttempts++;

    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    console.log(
      `Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`
    );

    this.reconnectTimer = setTimeout(async () => {
      try {
        await this.startStream();
      } catch (error) {
        console.error('Reconnection failed:', error);
        this.scheduleReconnect();
      }
    }, delay);
  }

  /**
   * Abort the current connection.
   */
  private abort(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  /**
   * Disconnect from the notification service.
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.abort();
    this.reconnectAttempts = 0;
    this.setConnectionState('disconnected');
  }

  /**
   * Check if the service is connected.
   */
  isConnected(): boolean {
    return this.connectionState === 'connected';
  }
}

// Export singleton instance
export const notificationService = new NotificationService();
