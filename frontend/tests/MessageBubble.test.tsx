import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { MessageBubble } from '@/components/chat/MessageBubble';
import type { Message } from '@/types/chat';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    refreshUser: vi.fn(),
    user: null,
    isAuthenticated: false,
  }),
}));

vi.mock('@/contexts/ChatContext', () => ({
  useChatContext: () => ({
    registerAnimateTask: vi.fn(),
    pendingVideoTasks: [],
    showInsufficientCreditsModal: vi.fn(),
  }),
}));

vi.mock('@/services/api', () => ({
  api: {
    post: vi.fn(),
  },
}));

const baseUserMessage: Message = {
  id: 'msg-001',
  role: 'user',
  content: 'Hello there!',
  timestamp: '2026-03-12T10:00:00Z',
};

const baseAssistantMessage: Message = {
  id: 'msg-002',
  role: 'assistant',
  content: 'Hi! How can I help you today?',
  timestamp: '2026-03-12T10:00:05Z',
};

function renderMessageBubble(message: Message, props: Partial<{ characterName: string; sessionId: string }> = {}) {
  return render(
    <MemoryRouter>
      <MessageBubble message={message} {...props} />
    </MemoryRouter>
  );
}

describe('MessageBubble', () => {
  it('renders without crashing for a user message', () => {
    renderMessageBubble(baseUserMessage);
    expect(document.body).toBeTruthy();
  });

  it('renders without crashing for an assistant message', () => {
    renderMessageBubble(baseAssistantMessage, { characterName: 'Roxy' });
    expect(document.body).toBeTruthy();
  });

  it('displays user message content', () => {
    renderMessageBubble(baseUserMessage);
    expect(screen.getByText('Hello there!')).toBeInTheDocument();
  });

  it('displays assistant message content', () => {
    renderMessageBubble(baseAssistantMessage, { characterName: 'Roxy' });
    expect(screen.getByText('Hi! How can I help you today?')).toBeInTheDocument();
  });

  it('shows "You" avatar for user messages', () => {
    renderMessageBubble(baseUserMessage);
    expect(screen.getByText('You')).toBeInTheDocument();
  });

  it('shows character initial in avatar for assistant messages', () => {
    renderMessageBubble(baseAssistantMessage, { characterName: 'Roxy' });
    expect(screen.getByText('R')).toBeInTheDocument();
  });

  it('shows "AI" avatar when no character name is provided', () => {
    renderMessageBubble(baseAssistantMessage);
    expect(screen.getByText('AI')).toBeInTheDocument();
  });

  it('renders generating skeleton when status is generating', () => {
    const generatingMessage: Message = {
      ...baseAssistantMessage,
      status: 'generating',
    };
    renderMessageBubble(generatingMessage, { characterName: 'Roxy' });
    expect(screen.getByText(/Generating/i)).toBeInTheDocument();
  });

  it('shows voice play button for assistant text messages with sessionId', () => {
    renderMessageBubble(baseAssistantMessage, { characterName: 'Roxy', sessionId: 'session-123' });
    const voiceButton = screen.getByTitle(/Play voice/i);
    expect(voiceButton).toBeInTheDocument();
  });
});
