/**
 * Chat Context
 *
 * Provides chat functionality using Server-Sent Events (SSE) for streaming.
 * Replaces the previous WebSocket implementation for improved stability.
 *
 * Architecture:
 * - POST /api/chat/stream: SSE for text and image chat
 * - GET /api/notifications/stream: Global SSE for async events (video completion)
 */

import { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import type { Character } from '@/types';
import type { Message, MessageListResponse, PendingVideoTask, NDJSONSegment, VoiceMode } from '@/types/chat';
import type { StoryCompletedEvent } from '@/types/story';
import { api } from '@/services/api';
import { sseService, type SSEEventData } from '@/services/sseService';
import { notificationService } from '@/services/notificationService';
import { InsufficientCreditsModal } from '@/components/chat/InsufficientCreditsModal';
import { getInsufficientCreditsInfo } from '@/utils/apiError';
import { useAuth } from './AuthContext';
import {
  createNDJSONParserState,
  parseNDJSONDelta,
  isLikelyNDJSON,
  parseNDJSONContent,
  type NDJSONParserState
} from '@/utils/ndjsonParser';

// PRD v3: Scene choices
interface SceneChoices {
  choices: string[];
  sceneState?: {
    description: string;
    active: boolean;
    turn: number;
    location?: string;
    narrative_phase?: string;
  };
}

interface ChatContextValue {
  currentCharacter: Character | null;
  setCurrentCharacter: (character: Character | null) => void;
  messages: Message[];
  sessionId: string | null;
  isLoading: boolean;
  isTyping: boolean;
  isBuffering: boolean;
  suggestedReplies: string[];
  pendingVideoTasks: PendingVideoTask[];
  sendMessage: (content: string, options?: { immediate?: boolean; voiceMode?: VoiceMode; isAdultMode?: boolean }) => Promise<void>;
  requestVoiceNote: (text: string) => Promise<void>;
  clearChat: () => void;
  loadChatHistory: (characterId: string) => Promise<void>;
  // Pagination
  hasMoreMessages: boolean;
  isLoadingMore: boolean;
  totalMessageCount: number;
  loadMoreMessages: () => Promise<void>;
  // PRD v3: Gameplay events
  sceneChoices: SceneChoices | null;
  clearSceneChoices: () => void;
  // Intimacy tracking
  intimacy: number;
  relationshipStage: string;
  relationshipDashboard: {
    trust: number;
    desire: number;
    dependency: number;
    gmNode: string;
  };
  // Story completion
  storyCompletedData: StoryCompletedEvent | null;
  clearStoryCompletedData: () => void;
  // Scene banner (script scene / recap)
  sceneBanner: { scene: string | null; synopsis: string | null } | null;
  ageVerificationRequired: boolean;
  ageVerificationMessage: string | null;
  clearAgeVerificationRequired: () => void;
  // Pre-warm session init before character details are loaded
  preloadSession: (characterId: string) => void;
  // Inject a local-only message into the chat (e.g. fal.ai direct generation)
  addLocalMessage: (msg: Message) => void;
  updateLocalMessage: (id: string, patch: Partial<Message>) => void;
  registerAnimateTask: (taskId: string, sessionId: string) => void;
  showInsufficientCreditsModal: (required?: number, available?: number) => void;
  // Inner monologue (ephemeral — cleared on text_done)
  thinkingContent: string;
  isThinking: boolean;
}

const ChatContext = createContext<ChatContextValue | undefined>(undefined);

export function useChatContext() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within ChatProvider');
  }
  return context;
}

// Message batching configuration
const BATCH_DELAY_MS = 300;
const DELTA_RENDER_THROTTLE_MS = 75;
const VIDEO_TASK_POLL_INTERVAL_MS = 5000;
const VIDEO_TASK_POLL_MAX_ATTEMPTS = 72; // ~6 minutes
const CHAT_PENDING_VIDEO_TASKS_KEY = 'roxy_chat_pending_video_tasks';
const SESSION_INIT_CACHE_TTL_MS = 30 * 60 * 1000;

interface PersistedChatVideoTask {
  taskId: string;
  sessionId: string;
  createdAt: string;
}

interface SessionInitData {
  session_id: string;
  is_new: boolean;
  scene: string | null;
  synopsis: string | null;
  opening_message: string | null;
  message_id: string | null;
}

interface SessionInitCacheEntry {
  promise: Promise<SessionInitData>;
  resolvedAt?: number;
}

interface InsufficientCreditsState {
  isOpen: boolean;
  required?: number;
  available?: number;
}

function loadPersistedChatVideoTasks(): PersistedChatVideoTask[] {
  try {
    const raw = localStorage.getItem(CHAT_PENDING_VIDEO_TASKS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function savePersistedChatVideoTask(task: PersistedChatVideoTask): void {
  const tasks = loadPersistedChatVideoTasks().filter((t) => t.taskId !== task.taskId);
  localStorage.setItem(CHAT_PENDING_VIDEO_TASKS_KEY, JSON.stringify([...tasks, task]));
}

function removePersistedChatVideoTask(taskId: string): void {
  const tasks = loadPersistedChatVideoTasks().filter((t) => t.taskId !== taskId);
  localStorage.setItem(CHAT_PENDING_VIDEO_TASKS_KEY, JSON.stringify(tasks));
}

function mergeStreamingText(
  current: string,
  incoming: string
): { merged: string; appended: string } {
  if (!incoming) return { merged: current, appended: '' };
  if (!current) return { merged: incoming, appended: incoming };

  if (incoming.startsWith(current)) {
    return { merged: incoming, appended: incoming.slice(current.length) };
  }

  if (current.endsWith(incoming)) {
    return { merged: current, appended: '' };
  }

  const maxOverlap = Math.min(current.length, incoming.length);
  for (let overlap = maxOverlap; overlap > 0; overlap -= 1) {
    if (current.slice(current.length - overlap) === incoming.slice(0, overlap)) {
      return { merged: current + incoming.slice(overlap), appended: incoming.slice(overlap) };
    }
  }

  return { merged: current + incoming, appended: incoming };
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const { refreshUser, isAuthenticated } = useAuth();
  const [currentCharacter, setCurrentCharacter] = useState<Character | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isBuffering, setIsBuffering] = useState(false);
  const [thinkingContent, setThinkingContent] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [suggestedReplies, setSuggestedReplies] = useState<string[]>([]);
  const [pendingVideoTasks, setPendingVideoTasks] = useState<PendingVideoTask[]>([]);

  // PRD v3: Gameplay state
  const [sceneChoices, setSceneChoices] = useState<SceneChoices | null>(null);

  // Intimacy tracking
  const [intimacy, setIntimacy] = useState(0);
  const [relationshipStage, setRelationshipStage] = useState('Stranger');
  const [relationshipDashboard, setRelationshipDashboard] = useState({
    trust: 0,
    desire: 0,
    dependency: 0,
    gmNode: 'node_intro',
  });

  // Story completion
  const [storyCompletedData, setStoryCompletedData] = useState<StoryCompletedEvent | null>(null);

  // Scene banner (script scene / recap)
  const [sceneBanner, setSceneBanner] = useState<{ scene: string | null; synopsis: string | null } | null>(null);
  const [ageVerificationRequired, setAgeVerificationRequired] = useState(false);
  const [ageVerificationMessage, setAgeVerificationMessage] = useState<string | null>(null);
  const [insufficientCreditsState, setInsufficientCreditsState] = useState<InsufficientCreditsState>({
    isOpen: false,
  });

  // Pagination state
  const [hasMoreMessages, setHasMoreMessages] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [oldestMessageId, setOldestMessageId] = useState<string | null>(null);
  const [totalMessageCount, setTotalMessageCount] = useState(0);

  // Streaming state ref
  const streamingMessageIdRef = useRef<string | null>(null);
  const streamingContentRef = useRef<string>('');

  // NDJSON parsing state refs
  const ndjsonParserRef = useRef<NDJSONParserState | null>(null);
  const isNDJSONModeRef = useRef<boolean>(false);
  const streamingSegmentsRef = useRef<NDJSONSegment[]>([]);

  // Message batching refs
  const messageBufferRef = useRef<{ content: string; tempId: string; voiceMode: VoiceMode; isAdultMode?: boolean }[]>([]);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isFlushingRef = useRef(false);
  const streamRenderTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastStreamRenderAtRef = useRef(0);
  const videoPollTimersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const videoPollAttemptsRef = useRef<Record<string, number>>({});

  // ==================== Notification Service Setup ====================

  // Use refs so handlers always see latest values without re-registering
  const sessionIdRef = useRef<string | null>(null);
  const currentCharacterRef = useRef<typeof currentCharacter>(null);
  sessionIdRef.current = sessionId;
  currentCharacterRef.current = currentCharacter;

  useEffect(() => {
    if (!isAuthenticated) return;

    notificationService.connect();

    const unsubVideoComplete = notificationService.on('video_completed', (data) => {
      console.log('Video completed:', data);
      if (videoPollTimersRef.current[data.task_id]) {
        clearInterval(videoPollTimersRef.current[data.task_id]);
        delete videoPollTimersRef.current[data.task_id];
      }
      delete videoPollAttemptsRef.current[data.task_id];
      removePersistedChatVideoTask(data.task_id);

      const videoMessage: Message = {
        id: data.message_id,
        role: 'assistant',
        content: '',
        video_url: data.video_url,
        timestamp: new Date().toISOString(),
        character_id: currentCharacterRef.current?.id || '',
      };

      if (data.session_id === sessionIdRef.current) {
        setMessages((prev) => {
          const existing = prev.find((msg) => msg.id === data.message_id);
          if (existing) {
            return prev.map((msg) =>
              msg.id === data.message_id
                ? {
                    ...msg,
                    video_url: data.video_url,
                    message_type: 'video',
                    status: 'ready',
                  }
                : msg
            );
          }

          // SSE may retry/replay the same completion event; avoid duplicated bubbles.
          if (data.video_url && prev.some((msg) => msg.video_url === data.video_url)) {
            return prev;
          }

          return [...prev, videoMessage];
        });
      }

      setPendingVideoTasks((prev) =>
        prev.map((task) =>
          task.taskId === data.task_id ? { ...task, status: 'completed' } : task
        )
      );

      refreshUser();
    });

    const unsubVideoFailed = notificationService.on('video_failed', (data) => {
      console.error('Video generation failed:', data);
      if (videoPollTimersRef.current[data.task_id]) {
        clearInterval(videoPollTimersRef.current[data.task_id]);
        delete videoPollTimersRef.current[data.task_id];
      }
      delete videoPollAttemptsRef.current[data.task_id];
      removePersistedChatVideoTask(data.task_id);

      setPendingVideoTasks((prev) =>
        prev.map((task) =>
          task.taskId === data.task_id ? { ...task, status: 'failed' } : task
        )
      );
    });

    const unsubCreditUpdate = notificationService.on('credit_update', () => {
      refreshUser();
    });

    const unsubAudioUploaded = notificationService.on('audio_uploaded', (data) => {
      if (data.session_id !== sessionIdRef.current) return;
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === data.message_id
            ? {
                ...msg,
                audio_url: data.audio_url,
                status: 'ready',
                message_type: msg.message_type || 'voice_note',
              }
            : msg
        )
      );
    });

    const unsubImageDone = notificationService.on('image_done', (data) => {
      if (data.session_id && data.session_id !== sessionIdRef.current) return;
      setMessages((prev) => {
        if (data.holding_message_id) {
          const holdingIdx = prev.findIndex((msg) => msg.id === data.holding_message_id);
          if (holdingIdx >= 0) {
            return prev.map((msg) =>
              msg.id === data.holding_message_id
                ? {
                    ...msg,
                    id: data.message_id || msg.id,
                    image_url: data.image_url,
                    content: '',
                    message_type: 'image',
                    status: 'ready',
                  }
                : msg
            );
          }
        }
        const existing = prev.find((msg) => msg.id === data.message_id);
        if (existing) {
          return prev.map((msg) =>
            msg.id === data.message_id
              ? { ...msg, image_url: data.image_url, message_type: 'image', status: 'ready' }
              : msg
          );
        }
        return [
          ...prev,
          {
            id: data.message_id,
            role: 'assistant',
            content: '',
            image_url: data.image_url,
            message_type: 'image',
            status: 'ready',
            timestamp: new Date().toISOString(),
            character_id: currentCharacterRef.current?.id || '',
          },
        ];
      });
    });

    const unsubImageFailed = notificationService.on('image_failed', (data) => {
      if (data.session_id && data.session_id !== sessionIdRef.current) return;
      if (!data.holding_message_id) return;
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === data.holding_message_id ? { ...msg, status: 'failed' } : msg
        )
      );
    });

    const unsubTaskStatus = notificationService.on('task_status', (data) => {
      if (sessionIdRef.current == null) return;
      setMessages((prev) => {
        const idx = prev.findIndex((msg) => msg.id === data.message_id);
        if (idx === -1) return prev;
        return prev.map((msg) =>
          msg.id === data.message_id
            ? {
                ...msg,
                status:
                  msg.status === 'ready' && (data.status === 'pending' || data.status === 'progress')
                    ? 'ready'
                    : data.status === 'ready'
                    ? 'ready'
                    : data.status === 'failed'
                      ? 'failed'
                      : 'generating',
                metadata: {
                  ...(msg.metadata || {}),
                  task_id: data.task_id,
                  task_status: data.status,
                  task_skill: data.skill_name,
                },
              }
            : msg
        );
      });
    });

    return () => {
      unsubVideoComplete();
      unsubVideoFailed();
      unsubImageDone();
      unsubImageFailed();
      unsubCreditUpdate();
      unsubAudioUploaded();
      unsubTaskStatus();
      notificationService.disconnect();
    };
  // Only reconnect when auth state changes 鈥?not on every character/session switch
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, refreshUser]);

  const parseMessageForDisplay = useCallback((msg: Message): Message => {
    if (msg.role !== 'assistant' || !msg.content) return msg;
    if (!isLikelyNDJSON(msg.content)) return msg;

    const { segments, parseErrors } = parseNDJSONContent(msg.content);
    if (segments.length === 0) return msg;

    return {
      ...msg,
      segments,
      isNDJSON: parseErrors <= 3,
    };
  }, []);

  const refreshSessionMessages = useCallback(async (targetSessionId: string) => {
    const response = await api.get<MessageListResponse>(
      `/chat/sessions/${targetSessionId}/messages?limit=20`
    );

    setMessages(response.data.messages.map(parseMessageForDisplay));
    setHasMoreMessages(response.data.has_more);
    setOldestMessageId(response.data.oldest_message_id);
    setTotalMessageCount(response.data.total_count);
  }, [parseMessageForDisplay]);

  const stopVideoTaskPolling = useCallback((taskId: string) => {
    if (videoPollTimersRef.current[taskId]) {
      clearTimeout(videoPollTimersRef.current[taskId]);
      delete videoPollTimersRef.current[taskId];
    }
    delete videoPollAttemptsRef.current[taskId];
  }, []);

  const startVideoTaskPolling = useCallback(
    (task: PersistedChatVideoTask) => {
      if (videoPollTimersRef.current[task.taskId]) return;

      videoPollAttemptsRef.current[task.taskId] = 0;
      const pollOnce = async () => {
        if (!videoPollAttemptsRef.current[task.taskId] && videoPollAttemptsRef.current[task.taskId] !== 0) {
          return;
        }

        videoPollAttemptsRef.current[task.taskId] =
          (videoPollAttemptsRef.current[task.taskId] || 0) + 1;

        if (videoPollAttemptsRef.current[task.taskId] > VIDEO_TASK_POLL_MAX_ATTEMPTS) {
          stopVideoTaskPolling(task.taskId);
          removePersistedChatVideoTask(task.taskId);
          setPendingVideoTasks((prev) =>
            prev.map((item) =>
              item.taskId === task.taskId ? { ...item, status: 'failed' } : item
              )
            );
          return;
        }

        let shouldContinuePolling = true;
        try {
          const response = await api.get(`/images/tasks/${task.taskId}`);
          const status = (response.data as { status?: string }).status;

          if (status === 'succeeded') {
            stopVideoTaskPolling(task.taskId);
            removePersistedChatVideoTask(task.taskId);
            setPendingVideoTasks((prev) =>
              prev.map((item) =>
                item.taskId === task.taskId ? { ...item, status: 'completed' } : item
              )
            );
            await refreshUser();

            if (sessionIdRef.current === task.sessionId) {
              await refreshSessionMessages(task.sessionId);
            }
            shouldContinuePolling = false;
            return;
          }

          if (status === 'failed') {
            stopVideoTaskPolling(task.taskId);
            removePersistedChatVideoTask(task.taskId);
            setPendingVideoTasks((prev) =>
              prev.map((item) =>
                item.taskId === task.taskId ? { ...item, status: 'failed' } : item
              )
            );
            shouldContinuePolling = false;
          }
        } catch (error) {
          console.error(`Polling video task failed (${task.taskId}):`, error);
          const statusCode = (error as { response?: { status?: number } })?.response?.status;
          if (statusCode === 403 || statusCode === 404) {
            stopVideoTaskPolling(task.taskId);
            removePersistedChatVideoTask(task.taskId);
            setPendingVideoTasks((prev) =>
              prev.map((item) =>
                item.taskId === task.taskId ? { ...item, status: 'failed' } : item
              )
            );
            shouldContinuePolling = false;
          }
        }

        if (shouldContinuePolling && videoPollAttemptsRef.current[task.taskId] !== undefined) {
          videoPollTimersRef.current[task.taskId] = setTimeout(pollOnce, VIDEO_TASK_POLL_INTERVAL_MS);
        }
      };

      // First poll immediately, then continue by setTimeout.
      void pollOnce();
    },
    [refreshSessionMessages, refreshUser, stopVideoTaskPolling]
  );

  const registerAnimateTask = useCallback(
    (taskId: string, taskSessionId: string) => {
      const persistedTask: PersistedChatVideoTask = {
        taskId,
        sessionId: taskSessionId,
        createdAt: new Date().toISOString(),
      };

      savePersistedChatVideoTask(persistedTask);

      setPendingVideoTasks((prev) => {
        if (prev.some((item) => item.taskId === taskId)) return prev;
        return [
          ...prev,
          {
            taskId,
            sessionId: taskSessionId,
            estimatedTimeSeconds: 30,
            submittedAt: new Date(),
            status: 'pending',
          },
        ];
      });

      startVideoTaskPolling(persistedTask);
    },
    [startVideoTaskPolling]
  );

  useEffect(() => {
    if (!isAuthenticated) {
      Object.keys(videoPollTimersRef.current).forEach(stopVideoTaskPolling);
      return;
    }

    const persistedTasks = loadPersistedChatVideoTasks();
    persistedTasks.forEach((task) => {
      setPendingVideoTasks((prev) => {
        if (prev.some((item) => item.taskId === task.taskId)) return prev;
        return [
          ...prev,
          {
            taskId: task.taskId,
            sessionId: task.sessionId,
            estimatedTimeSeconds: 30,
            submittedAt: new Date(task.createdAt),
            status: 'pending',
          },
        ];
      });
      startVideoTaskPolling(task);
    });
  }, [isAuthenticated, startVideoTaskPolling, stopVideoTaskPolling]);

  // Self-heal: if any pending task loses its timer unexpectedly, resume polling.
  useEffect(() => {
    if (!isAuthenticated) return;
    pendingVideoTasks
      .filter((task) => task.status === 'pending')
      .forEach((task) => {
        if (!videoPollTimersRef.current[task.taskId]) {
          startVideoTaskPolling({
            taskId: task.taskId,
            sessionId: task.sessionId,
            createdAt: task.submittedAt.toISOString(),
          });
        }
      });
  }, [isAuthenticated, pendingVideoTasks, startVideoTaskPolling]);

  // ==================== Load More Messages ====================

  const loadMoreMessages = useCallback(async () => {
    if (!sessionId || !hasMoreMessages || isLoadingMore) return;

    setIsLoadingMore(true);
    try {
      const params = new URLSearchParams({
        limit: '20',
        ...(oldestMessageId && { before_id: oldestMessageId }),
      });

      const response = await api.get<MessageListResponse>(
        `/chat/sessions/${sessionId}/messages?${params}`
      );

      const parsedMessages = response.data.messages.map(parseMessageForDisplay);

      setMessages((prev) => [...parsedMessages, ...prev]);
      setHasMoreMessages(response.data.has_more);
      setOldestMessageId(response.data.oldest_message_id);
      setTotalMessageCount(response.data.total_count);
    } catch (error) {
      console.error('Failed to load more messages:', error);
    } finally {
      setIsLoadingMore(false);
    }
  }, [sessionId, hasMoreMessages, isLoadingMore, oldestMessageId, parseMessageForDisplay]);

  // ==================== Load Chat History ====================

  // Cache: character_id -> in-flight/resolved init payload with 30m TTL.
  const sessionInitCacheRef = useRef<Map<string, SessionInitCacheEntry>>(new Map());

  const getSessionInit = useCallback((characterId: string): Promise<SessionInitData> => {
    const now = Date.now();
    const existing = sessionInitCacheRef.current.get(characterId);
    if (existing) {
      if (!existing.resolvedAt || now - existing.resolvedAt < SESSION_INIT_CACHE_TTL_MS) {
        return existing.promise;
      }
      sessionInitCacheRef.current.delete(characterId);
    }

    const promise = api
      .post<SessionInitData>('/chat/sessions/initialize', { character_id: characterId })
      .then((r) => r.data);
    sessionInitCacheRef.current.set(characterId, { promise });

    promise
      .then(() => {
        const current = sessionInitCacheRef.current.get(characterId);
        if (current?.promise === promise) {
          sessionInitCacheRef.current.set(characterId, {
            promise,
            resolvedAt: Date.now(),
          });
        }
      })
      .catch(() => {
        const current = sessionInitCacheRef.current.get(characterId);
        if (current?.promise === promise) {
          sessionInitCacheRef.current.delete(characterId);
        }
      });

    return promise;
  }, []);

  const preloadSession = useCallback((characterId: string) => {
    void getSessionInit(characterId);
  }, [getSessionInit]);

  const loadingCharacterIdRef = useRef<string | null>(null);

  const loadChatHistory = useCallback(async (characterId: string) => {
    // Prevent duplicate concurrent loads for the same character
    if (loadingCharacterIdRef.current === characterId) return;
    loadingCharacterIdRef.current = characterId;

    setIsLoading(true);

    // Abort any ongoing stream
    sseService.abort();

    // Reset pagination state
    setHasMoreMessages(true);
    setOldestMessageId(null);
    setTotalMessageCount(0);
    setSceneBanner(null);

    try {
      // Reuse pre-warmed session init if available (fired in parallel with character fetch)
      const initData = await getSessionInit(characterId);

      const { session_id, scene, synopsis, opening_message, message_id } = initData;
      setSessionId(session_id);

      // Store scene banner data
      if (scene || synopsis) {
        setSceneBanner({ scene: scene ?? null, synopsis: synopsis ?? null });
      }

      // Fetch existing messages (includes the opening message if just created)
      const msgResponse = await api.get<MessageListResponse>(
        `/chat/sessions/${session_id}/messages?limit=20`
      );

      const parsedMessages = msgResponse.data.messages.map(parseMessageForDisplay);

      // If opening message was just generated but not yet in DB fetch, prepend it
      if (opening_message && message_id && parsedMessages.length === 0) {
        parsedMessages.push({
          id: message_id,
          role: 'assistant',
          content: opening_message,
          timestamp: new Date().toISOString(),
          character_id: characterId,
        });
      }

      setMessages(parsedMessages);
      setHasMoreMessages(msgResponse.data.has_more);
      setOldestMessageId(msgResponse.data.oldest_message_id);
      setTotalMessageCount(msgResponse.data.total_count);
    } catch (error) {
      console.error('Failed to load chat history:', error);
      setMessages([]);
      setSessionId(null);
    } finally {
      setIsLoading(false);
      loadingCharacterIdRef.current = null;
    }
  }, [getSessionInit, parseMessageForDisplay]);

  const flushStreamingRender = useCallback(() => {
    const streamId = streamingMessageIdRef.current;
    if (!streamId) return;

    const content = streamingContentRef.current;
    const segments = isNDJSONModeRef.current ? [...streamingSegmentsRef.current] : undefined;
    const isNDJSON = isNDJSONModeRef.current;
    const characterId = currentCharacter?.id || '';

    setMessages((prev) => {
      const existingIndex = prev.findIndex((msg) => msg.id === streamId);
      if (existingIndex !== -1) {
        return prev.map((msg, idx) =>
          idx === existingIndex
            ? {
                ...msg,
                content: content || msg.content,
                segments,
                isNDJSON,
              }
            : msg
        );
      }

      if (!content) return prev;

      const newMsg: Message = {
        id: streamId,
        role: 'assistant',
        content,
        segments,
        isNDJSON,
        timestamp: new Date().toISOString(),
        character_id: characterId,
      };
      return [...prev, newMsg];
    });
  }, [currentCharacter]);

  const scheduleStreamingRender = useCallback(
    (force = false) => {
      const now = Date.now();
      const elapsed = now - lastStreamRenderAtRef.current;

      const run = () => {
        lastStreamRenderAtRef.current = Date.now();
        streamRenderTimerRef.current = null;
        flushStreamingRender();
      };

      if (force || elapsed >= DELTA_RENDER_THROTTLE_MS) {
        if (streamRenderTimerRef.current) {
          clearTimeout(streamRenderTimerRef.current);
          streamRenderTimerRef.current = null;
        }
        run();
        return;
      }

      if (!streamRenderTimerRef.current) {
        streamRenderTimerRef.current = setTimeout(
          run,
          DELTA_RENDER_THROTTLE_MS - elapsed
        );
      }
    },
    [flushStreamingRender]
  );

  const showInsufficientCreditsModal = useCallback((required?: number, available?: number) => {
    setInsufficientCreditsState({
      isOpen: true,
      required,
      available,
    });
  }, []);

  // ==================== SSE Event Handler ====================

  const handleSSEEvent = useCallback(
    (event: SSEEventData) => {
      switch (event.type) {
        case 'session_created':
          if (event.data.is_new || !sessionId) {
            setSessionId(event.data.session_id);
          }
          setThinkingContent('');
          setIsThinking(false);
          break;

        case 'user_message':
          // User message confirmed - update temp ID if needed
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id.startsWith('temp-') && msg.role === 'user'
                ? { ...msg, id: event.data.message_id }
                : msg
            )
          );
          break;

        case 'text_delta':
          setIsTyping(false);
          if (streamingMessageIdRef.current) {
            const { merged, appended } = mergeStreamingText(
              streamingContentRef.current,
              event.data.delta
            );
            streamingContentRef.current = merged;

            if (
              !isNDJSONModeRef.current &&
              isLikelyNDJSON(streamingContentRef.current)
            ) {
              const fresh = createNDJSONParserState();
              const { updatedState } = parseNDJSONDelta(
                fresh,
                streamingContentRef.current
              );
              if (
                updatedState.segments.length > 0 &&
                updatedState.parseErrors <= 3
              ) {
                isNDJSONModeRef.current = true;
                ndjsonParserRef.current = updatedState;
                streamingSegmentsRef.current = updatedState.segments;
              }
            }

            if (appended && isNDJSONModeRef.current && ndjsonParserRef.current) {
              const { updatedState } = parseNDJSONDelta(
                ndjsonParserRef.current,
                appended
              );
              ndjsonParserRef.current = updatedState;
              streamingSegmentsRef.current = updatedState.segments;

              if (updatedState.parseErrors > 3) {
                isNDJSONModeRef.current = false;
              }
            }
          } else {
            // Start new streaming message
            const newId = `stream-${Date.now()}`;
            streamingMessageIdRef.current = newId;
            streamingContentRef.current = event.data.delta;

            ndjsonParserRef.current = createNDJSONParserState();
            isNDJSONModeRef.current = isLikelyNDJSON(event.data.delta);
            streamingSegmentsRef.current = [];

            if (isNDJSONModeRef.current) {
              const { updatedState } = parseNDJSONDelta(
                ndjsonParserRef.current,
                event.data.delta
              );
              ndjsonParserRef.current = updatedState;
              streamingSegmentsRef.current = updatedState.segments;
            }
          }

          scheduleStreamingRender();
          break;

        case 'text_done':
          if (streamRenderTimerRef.current) {
            clearTimeout(streamRenderTimerRef.current);
            streamRenderTimerRef.current = null;
          }

          {
            const streamId = streamingMessageIdRef.current;
            const finalContent =
              event.data.full_content || streamingContentRef.current || '';
            const segments = isNDJSONModeRef.current
              ? [...streamingSegmentsRef.current]
              : undefined;
            const isNDJSON = isNDJSONModeRef.current;
            const characterId = currentCharacter?.id || '';

            setMessages((prev) => {
              let updated = false;
              let next = prev.map((msg) => {
                if (streamId && msg.id === streamId) {
                  updated = true;
                  return {
                    ...msg,
                    id: event.data.message_id,
                    content: finalContent || msg.content,
                    segments,
                    isNDJSON,
                  };
                }
                if (msg.id === event.data.message_id) {
                  updated = true;
                  return {
                    ...msg,
                    content: finalContent || msg.content,
                    segments,
                    isNDJSON,
                  };
                }
                return msg;
              });

              if (!updated && finalContent) {
                const fallbackMsg: Message = {
                  id: event.data.message_id,
                  role: 'assistant',
                  content: finalContent,
                  segments,
                  isNDJSON,
                  timestamp: new Date().toISOString(),
                  character_id: characterId,
                };
                next = [...next, fallbackMsg];
              }
              return next;
            });
          }

          // Reset NDJSON state
          ndjsonParserRef.current = null;
          isNDJSONModeRef.current = false;
          streamingSegmentsRef.current = [];

          streamingMessageIdRef.current = null;
          streamingContentRef.current = '';
          lastStreamRenderAtRef.current = 0;
          setThinkingContent('');
          setIsThinking(false);
          break;

        case 'thinking_delta':
          setThinkingContent((prev) => prev + event.data.delta);
          setIsThinking(true);
          break;

        case 'thinking_done':
          setIsThinking(false);
          // Keep thinkingContent visible until text_done clears it
          break;

        case 'stream_end':
          if (streamRenderTimerRef.current) {
            clearTimeout(streamRenderTimerRef.current);
            streamRenderTimerRef.current = null;
          }
          if (event.data?.summary?.credit_update || event.data?.summary?.settlement === 'queued') {
            refreshUser();
          }
          setIsTyping(false);
          break;

        case 'error':
          if (streamRenderTimerRef.current) {
            clearTimeout(streamRenderTimerRef.current);
            streamRenderTimerRef.current = null;
          }
          console.error('SSE Error:', event.data);
          if (event.data.error_code === 'age_verification_required') {
            setAgeVerificationRequired(true);
            setAgeVerificationMessage(event.data.message || 'Age verification is required to continue.');
          }
          if (event.data.error_code === 'insufficient_credits') {
            showInsufficientCreditsModal(
              event.data.required,
              event.data.available
            );
          }
          setIsTyping(false);
          setThinkingContent('');
          setIsThinking(false);
          break;

        case 'image_generating':
          // Could show a loading indicator
          console.log('Image generating:', event.data.status);
          break;

        case 'image_done': {
          setIsTyping(false);
          const imageMsg: Message = {
            id: event.data.message_id,
            role: 'assistant',
            content: '',
            image_url: event.data.image_url,
            timestamp: new Date().toISOString(),
            character_id: currentCharacter?.id || '',
          };
          setMessages((prev) => [...prev, imageMsg]);
          break;
        }

        case 'video_submitted': {
          // Track pending video task
          const pendingTask: PendingVideoTask = {
            taskId: event.data.task_id,
            sessionId: event.data.session_id,
            holdingMessageId: event.data.holding_message_id,
            holdingMessage: event.data.holding_message,
            estimatedTimeSeconds: event.data.estimated_time_seconds,
            submittedAt: new Date(),
            status: 'pending',
          };
          setPendingVideoTasks((prev) => [...prev, pendingTask]);
          const persistedTask: PersistedChatVideoTask = {
            taskId: event.data.task_id,
            sessionId: event.data.session_id,
            createdAt: new Date().toISOString(),
          };
          savePersistedChatVideoTask(persistedTask);
          startVideoTaskPolling(persistedTask);
          break;
        }

        case 'credit_update':
          refreshUser();
          break;

        case 'suggestions':
          setSuggestedReplies(event.data.suggestions);
          break;

        // PRD v3: Scene choices event
        case 'scene_choices':
          setSceneChoices({
            choices: event.data.choices || [],
            sceneState: event.data.scene_state,
          });
          console.log('Scene choices received:', event.data.choices);
          break;

        case 'scene_node_action_started':
          console.log(
            'Scene node action started:',
            event.data.node_id,
            event.data.action_type
          );
          break;

        case 'scene_node_action_done':
          console.log(
            'Scene node action done:',
            event.data.node_id,
            event.data.action_type
          );
          break;

        case 'scene_node_action_failed':
          console.warn(
            'Scene node action failed:',
            event.data.node_id,
            event.data.action_type,
            event.data.reason
          );
          break;

        case 'scene_node_action_downgraded':
          console.log(
            'Scene node action downgraded:',
            event.data.node_id,
            event.data.from_action,
            '->',
            event.data.to_action
          );
          break;

        // PRD v2026.02: Script System events
        case 'script_state_updated':
          console.log('Script state updated:', event.data.current_state, '(Progress:', event.data.quest_progress + '%)');
          // Update script progress in UI (handled by ScriptProgress component via props)
          break;

        case 'quest_progress_updated':
          console.log('Quest progress:', event.data.quest_progress + '%', '- State:', event.data.current_state);
          if (event.data.hint_chips && event.data.hint_chips.length > 0) {
            setSuggestedReplies(event.data.hint_chips);
          }
          break;

        case 'intimacy_updated':
          const intimacyDelta = event.data.change_amount ?? event.data.change ?? 0;
          console.log(
            'Intimacy updated:',
            event.data.previous_value,
            '->',
            event.data.current_value,
            `(${intimacyDelta > 0 ? '+' : ''}${intimacyDelta})`
          );
          // Update intimacy state
          setIntimacy(event.data.current_value || event.data.intimacy || 0);
          if (event.data.relationship_stage) {
            setRelationshipStage(event.data.relationship_stage);
          }
          setRelationshipDashboard((prev) => ({
            trust: event.data.dashboard?.trust ?? event.data.trust ?? prev.trust,
            desire: event.data.dashboard?.desire ?? event.data.desire ?? prev.desire,
            dependency:
              event.data.dashboard?.dependency ??
              event.data.dependency ??
              prev.dependency,
            gmNode: event.data.gm_current_node ?? prev.gmNode,
          }));
          break;

        case 'media_cue_triggered':
          console.log('Media cue triggered:', event.data.media_type, '- Estimated time:', event.data.estimated_time_seconds + 's');
          // Placeholder message already created by backend, no action needed
          break;

        case 'voice_note_pending':
          // For text-first voice upgrade, mark existing message as voice-pending.
          // Fallback to placeholder only when message is not present (manual voice-note path).
          setMessages((prev) => {
            const existingIndex = prev.findIndex((msg) => msg.id === event.data.message_id);
            if (existingIndex !== -1) {
              return prev.map((msg) =>
                msg.id === event.data.message_id
                  ? {
                      ...msg,
                      metadata: {
                        ...(msg.metadata || {}),
                        voice_pending: true,
                      },
                    }
                  : msg
              );
            }
            return [
              ...prev,
              {
                id: event.data.message_id,
                role: 'assistant' as const,
                content: '',
                message_type: 'voice_note',
                status: 'generating',
                timestamp: new Date().toISOString(),
                character_id: currentCharacter?.id || '',
              },
            ];
          });
          break;

        case 'tool_call':
          console.log(
            'Tool call:',
            event.data.tool_name,
            event.data.phase,
            event.data.status,
            event.data.task_id || ''
          );
          break;

        case 'task_status':
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === event.data.message_id
                ? {
                    ...msg,
                    status:
                      ((event.data.skill_name === 'tts' && !!msg.content) && (event.data.status === 'pending' || event.data.status === 'progress'))
                        ? 'ready'
                        : msg.status === 'ready' && (event.data.status === 'pending' || event.data.status === 'progress')
                        ? 'ready'
                        : event.data.status === 'ready'
                        ? 'ready'
                        : event.data.status === 'failed'
                          ? 'failed'
                          : 'generating',
                    metadata: {
                      ...(msg.metadata || {}),
                      task_id: event.data.task_id,
                      task_status: event.data.status,
                      task_skill: event.data.skill_name,
                      voice_pending:
                        event.data.skill_name === 'tts'
                          ? event.data.status === 'pending' || event.data.status === 'progress'
                          : (msg.metadata as any)?.voice_pending,
                    },
                    error:
                      event.data.status === 'failed'
                        ? String(
                            (event.data.payload as { reason?: string } | undefined)?.reason ||
                              event.data.error_code ||
                              'Task failed'
                          )
                        : msg.error,
                  }
                : msg
            )
          );
          break;

        case 'voice_note_ready':
          setIsTyping(false);
          // Update placeholder message with ready voice note
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === event.data.message_id
                ? {
                    ...msg,
                    message_type: 'voice_note',
                    status: 'ready',
                    audio_url: event.data.audio_url,
                    duration: event.data.duration,
                    cost: event.data.cost,
                    metadata: {
                      ...(msg.metadata || {}),
                      voice_pending: false,
                    },
                  }
                : msg
            )
          );
          console.log('Voice note ready:', event.data.message_id);
          break;

        case 'voice_note_failed':
          setIsTyping(false);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === event.data.message_id
                ? {
                    ...msg,
                    status: 'failed',
                    error: event.data.reason || 'Voice generation failed',
                    metadata: {
                      ...(msg.metadata || {}),
                      voice_pending: false,
                    },
                  }
                : msg
            )
          );
          break;

        case 'audio_uploaded':
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === event.data.message_id
                ? {
                    ...msg,
                    audio_url: event.data.audio_url,
                    status: 'ready',
                    message_type: msg.message_type || 'voice_note',
                  }
                : msg
            )
          );
          break;

        case 'video_ready':
          setIsTyping(false);
          // Update placeholder message or add new video message
          setMessages((prev) => {
            const existingIndex = prev.findIndex(msg => msg.id === event.data.message_id);
            if (existingIndex !== -1) {
              // Update existing placeholder
              return prev.map((msg) =>
                msg.id === event.data.message_id
                  ? {
                      ...msg,
                      status: 'ready',
                      video_url: event.data.video_url,
                      duration: event.data.duration,
                      cost: event.data.cost,
                    }
                  : msg
              );
            } else {
              // Add new video message
              const videoMsg: Message = {
                id: event.data.message_id,
                role: 'assistant',
                content: '',
                video_url: event.data.video_url,
                timestamp: new Date().toISOString(),
                character_id: currentCharacter?.id || '',
                message_type: 'video',
                status: 'ready',
                duration: event.data.duration,
                cost: event.data.cost,
              };
              return [...prev, videoMsg];
            }
          });
          console.log('Video ready:', event.data.message_id, '- Source:', event.data.source);
          break;

        case 'story_completed':
          setStoryCompletedData({
            story_id: event.data.story_id,
            story_title: event.data.story_title,
            ending_type: event.data.ending_type,
            rewards: event.data.rewards,
            completion_time_minutes: event.data.completion_time_minutes,
          });
          console.log('Story completed:', event.data.story_title, '- Ending:', event.data.ending_type);
          break;

        case 'age_verification_required':
          setAgeVerificationRequired(true);
          setAgeVerificationMessage(event.data.message || 'Age verification is required to continue.');
          setIsTyping(false);
          break;

        case 'video_intent_declined': {
          setIsTyping(false);
          const declineMsg: Message = {
            id: `decline-${Date.now()}`,
            role: 'assistant',
            content: event.data.message,
            timestamp: new Date().toISOString(),
            character_id: currentCharacter?.id || '',
            metadata: {
              show_photo_button: event.data.show_photo_button,
            },
          };
          setMessages((prev) => [...prev, declineMsg]);
          break;
        }

        default:
          break;
      }
    },
    [currentCharacter, refreshUser, scheduleStreamingRender, sessionId, startVideoTaskPolling, showInsufficientCreditsModal]
  );

  // ==================== Send Message via SSE ====================

  const flushMessageBuffer = useCallback(async () => {
    if (!currentCharacter || messageBufferRef.current.length === 0) return;
    if (isFlushingRef.current) return;

    isFlushingRef.current = true;

    try {
      while (messageBufferRef.current.length > 0) {
        const first = messageBufferRef.current[0];
        if (!first) break;
        const voiceMode = first.voiceMode || 'auto';
        const bufferedMessages: { content: string; tempId: string; voiceMode: VoiceMode; isAdultMode?: boolean }[] = [];
        while (messageBufferRef.current.length > 0) {
          const candidate = messageBufferRef.current[0];
          if ((candidate.voiceMode || 'auto') !== voiceMode) break;
          bufferedMessages.push(messageBufferRef.current.shift()!);
        }
        setIsBuffering(false);
        setIsTyping(true);

        // Combine all buffered messages
        const combinedContent = bufferedMessages.map((m) => m.content).join('\n');

        try {
          // Stream the chat request
          const isAdultMode = bufferedMessages[0]?.isAdultMode;
          const stream = sseService.streamChat({
            characterId: currentCharacter.id,
            message: combinedContent,
            sessionId: sessionId || undefined,
            voiceMode,
            ...(isAdultMode !== undefined && { isAdultOverride: isAdultMode }),
          });

          // Process events
          for await (const event of stream) {
            handleSSEEvent(event);
          }
        } catch (error: any) {
          console.error('Failed to send message:', error);

          const insufficientCredits = getInsufficientCreditsInfo(error);
          if (insufficientCredits) {
            showInsufficientCreditsModal(insufficientCredits.required, insufficientCredits.available);
          }

          // Remove optimistic messages on error
          const tempIds = bufferedMessages.map((m) => m.tempId);
          setMessages((prev) => prev.filter((m) => !tempIds.includes(m.id)));
          setIsTyping(false);
        }
      }
    } finally {
      isFlushingRef.current = false;
      if (messageBufferRef.current.length > 0) {
        setTimeout(() => {
          void flushMessageBuffer();
        }, 0);
      }
    }
  }, [currentCharacter, sessionId, handleSSEEvent, showInsufficientCreditsModal]);

  const sendMessage = useCallback(
    async (content: string, options?: { immediate?: boolean; voiceMode?: VoiceMode; isAdultMode?: boolean }) => {
      if (!currentCharacter || !content.trim()) return;
      const immediate = Boolean(options?.immediate);
      const voiceMode = options?.voiceMode || 'auto';
      const isAdultMode = options?.isAdultMode;

      // Clear suggestions
      setSuggestedReplies([]);

      const tempId = `temp-${Date.now()}-${Math.random()}`;
      const userMessage: Message = {
        id: tempId,
        role: 'user',
        content: content.trim(),
        timestamp: new Date().toISOString(),
        character_id: currentCharacter.id,
      };

      // Optimistically add user message
      setMessages((prev) => [...prev, userMessage]);

      // Add to buffer
      messageBufferRef.current.push({ content: content.trim(), tempId, voiceMode, isAdultMode });
      setIsBuffering(true);

      // Clear existing timer
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
        debounceTimerRef.current = null;
      }

      if (immediate) {
        void flushMessageBuffer();
        return;
      }

      // Set debounce timer
      debounceTimerRef.current = setTimeout(() => {
        debounceTimerRef.current = null;
        void flushMessageBuffer();
      }, BATCH_DELAY_MS);
    },
    [currentCharacter, flushMessageBuffer]
  );

  // ==================== Clear Chat ====================

  const clearChat = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setPendingVideoTasks([]);
    setSuggestedReplies([]);
    // PRD v3
    setSceneChoices(null);
    setStoryCompletedData(null);

    // Clear message buffer
    messageBufferRef.current = [];
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
    setIsBuffering(false);
    isFlushingRef.current = false;
    if (streamRenderTimerRef.current) {
      clearTimeout(streamRenderTimerRef.current);
      streamRenderTimerRef.current = null;
    }
    lastStreamRenderAtRef.current = 0;

    // Abort any ongoing stream
    sseService.abort();
  }, []);

  const closeInsufficientCreditsModal = useCallback(() => {
    setInsufficientCreditsState((prev) => ({ ...prev, isOpen: false }));
  }, []);

  // ==================== Request Voice Note ====================

  const requestVoiceNote = useCallback(
    async (text: string) => {
      if (!currentCharacter || !sessionId || !text.trim()) {
        console.error('Cannot request voice note: missing character or session');
        return;
      }

      try {
        setIsLoading(true);

        // Call backend endpoint to request voice note
        const response = await api.post('/chat/request-voice-note', null, {
          params: {
            character_id: currentCharacter.id,
            session_id: sessionId,
            text: text.trim(),
          },
        });

        if (response.data.success) {
          const { placeholder_message_id } = response.data;

          // Add placeholder message to messages list
          const placeholderMessage: Message = {
            id: placeholder_message_id,
            role: 'assistant',
            content: text.trim(),
            message_type: 'voice_note',
            status: 'generating',
            timestamp: new Date().toISOString(),
            character_id: currentCharacter.id,
          };

          setMessages((prev) => [...prev, placeholderMessage]);

          // Credits were deducted, refresh user
          if (refreshUser) {
            await refreshUser();
          }

          console.log(`Voice note generation started for message ${placeholder_message_id}`);
        } else {
          throw new Error('Failed to request voice note');
        }
      } catch (error: any) {
        console.error('Failed to request voice note:', error);

        const insufficientCredits = getInsufficientCreditsInfo(error);
        if (insufficientCredits) {
          showInsufficientCreditsModal(insufficientCredits.required, insufficientCredits.available);
        } else {
          alert('Failed to request voice note. Please try again.');
        }
      } finally {
        setIsLoading(false);
      }
    },
    [currentCharacter, sessionId, refreshUser, showInsufficientCreditsModal]
  );

  // PRD v3: Clear functions for gameplay state
  const clearSceneChoices = useCallback(() => {
    setSceneChoices(null);
  }, []);

  const clearStoryCompletedData = useCallback(() => {
    setStoryCompletedData(null);
  }, []);

  const clearAgeVerificationRequired = useCallback(() => {
    setAgeVerificationRequired(false);
    setAgeVerificationMessage(null);
  }, []);

  // ==================== Character Change Effect ====================

  useEffect(() => {
    // Clear buffer when switching characters
    messageBufferRef.current = [];
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
    setIsBuffering(false);
    if (streamRenderTimerRef.current) {
      clearTimeout(streamRenderTimerRef.current);
      streamRenderTimerRef.current = null;
    }
    lastStreamRenderAtRef.current = 0;
    setPendingVideoTasks([]);

    if (currentCharacter) {
      loadChatHistory(currentCharacter.id);
      setSuggestedReplies([]);
    } else {
      setMessages([]);
      setSessionId(null);
      setSuggestedReplies([]);
      sseService.abort();
    }
  }, [currentCharacter, loadChatHistory]);

  useEffect(() => {
    const videoPollTimers = videoPollTimersRef.current;
    return () => {
      if (streamRenderTimerRef.current) {
        clearTimeout(streamRenderTimerRef.current);
      }
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      Object.values(videoPollTimers).forEach(clearInterval);
    };
  }, []);

  // ==================== Context Value ====================

  const value: ChatContextValue = {
    currentCharacter,
    setCurrentCharacter,
    messages,
    sessionId,
    isLoading,
    isTyping,
    isBuffering,
    suggestedReplies,
    pendingVideoTasks,
    sendMessage,
    requestVoiceNote,
    clearChat,
    loadChatHistory,
    hasMoreMessages,
    isLoadingMore,
    totalMessageCount,
    loadMoreMessages,
    // PRD v3: Gameplay events
    sceneChoices,
    clearSceneChoices,
    // Intimacy tracking
    intimacy,
    relationshipStage,
    relationshipDashboard,
    // Story completion
    storyCompletedData,
    clearStoryCompletedData,
    // Scene banner
    sceneBanner,
    ageVerificationRequired,
    ageVerificationMessage,
    clearAgeVerificationRequired,
    preloadSession,
    addLocalMessage: (msg: Message) => setMessages((prev) => [...prev, msg]),
    updateLocalMessage: (id: string, patch: Partial<Message>) =>
      setMessages((prev) =>
        prev.map((m) => (m.id === id ? { ...m, ...patch } : m))
      ),
    registerAnimateTask,
    showInsufficientCreditsModal,
    thinkingContent,
    isThinking,
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
      <InsufficientCreditsModal
        isOpen={insufficientCreditsState.isOpen}
        required={insufficientCreditsState.required}
        available={insufficientCreditsState.available}
        onClose={closeInsufficientCreditsModal}
      />
    </ChatContext.Provider>
  );
}



