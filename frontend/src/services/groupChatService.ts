import { api } from './api';
import type { GroupChatSession, Message, GroupChatStreamRequest } from '@/types/chat';

export const groupChatService = {
  async createSession(participants: string[], title?: string): Promise<GroupChatSession> {
    const response = await api.post<GroupChatSession>('/chat/group/sessions', {
      participants,
      title,
    });
    return response.data;
  },

  async getSession(sessionId: string): Promise<GroupChatSession> {
    const response = await api.get<GroupChatSession>(`/chat/group/sessions/${sessionId}`);
    return response.data;
  },

  async getMessages(sessionId: string, limit = 50): Promise<{ session_id: string; messages: Message[] }> {
    const response = await api.get<{ session_id: string; messages: Message[] }>(
      `/chat/group/sessions/${sessionId}/messages`,
      { params: { limit } }
    );
    return response.data;
  },

  streamChat(request: GroupChatStreamRequest): EventSource {
    const eventSource = new EventSource(
      `${api.defaults.baseURL}/chat/group/stream?${new URLSearchParams(request as any).toString()}`
    );
    return eventSource;
  },

  async postStreamChat(request: GroupChatStreamRequest): Promise<Response> {
    const response = await fetch(`${api.defaults.baseURL}/chat/group/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
      },
      body: JSON.stringify(request),
    });
    return response;
  },
};
