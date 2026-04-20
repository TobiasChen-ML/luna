export const mockChatCharacter = {
  id: 'test-chat-char-001',
  name: 'Emma Watson',
  first_name: 'Emma',
  slug: 'emma-test',
  top_category: 'girls',
  description: 'A friendly and intelligent AI companion who loves meaningful conversations.',
  backstory: 'Emma grew up in a small town with big dreams. She is caring, thoughtful, and always ready to listen.',
  greeting: 'Hi there! I\'m Emma, nice to meet you! What would you like to talk about?',
  personality_tags: ['friendly', 'intelligent', 'caring', 'thoughtful'],
  profile_image_url: 'https://example.com/avatars/emma.jpg',
  media_urls: {
    avatar: 'https://example.com/avatars/emma.jpg',
    gallery: [
      'https://example.com/gallery/emma-1.jpg',
      'https://example.com/gallery/emma-2.jpg',
    ],
  },
  is_public: true,
  lifecycle_status: 'active',
  view_count: 5678,
  chat_count: 1234,
  popularity_score: 95,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-04-01T00:00:00Z',
};

export const mockChatCharacterAnime = {
  id: 'test-chat-char-002',
  name: 'Sakura Miko',
  first_name: 'Sakura',
  slug: 'sakura-anime',
  top_category: 'anime',
  description: 'A cheerful anime-style AI companion from a world of cherry blossoms.',
  backstory: 'Sakura comes from a magical world filled with cherry blossoms and adventure.',
  greeting: 'Konichiwa! I\'m Sakura~ Ready to explore together?',
  personality_tags: ['cheerful', 'cute', 'energetic', 'kind'],
  profile_image_url: 'https://example.com/avatars/sakura.jpg',
  media_urls: {
    avatar: 'https://example.com/avatars/sakura.jpg',
    gallery: [],
  },
  is_public: true,
  lifecycle_status: 'active',
  view_count: 3456,
  chat_count: 789,
  popularity_score: 88,
  created_at: '2026-02-01T00:00:00Z',
  updated_at: '2026-04-01T00:00:00Z',
};

export const mockUser = {
  id: 'test-user-001',
  email: 'test@example.com',
  firebase_uid: 'firebase-test-001',
  display_name: 'Test User',
  is_adult: true,
  is_admin: false,
  subscription_tier: 'free',
  credits: 100,
  purchased_credits: 0,
  monthly_credits_remaining: 50,
  mature_preference: 'adult',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-04-01T00:00:00Z',
};

export const mockChatSession = {
  session_id: 'test-session-001',
  character_id: 'test-chat-char-001',
  user_id: 'test-user-001',
  created_at: '2026-04-01T10:00:00Z',
  updated_at: '2026-04-01T10:00:00Z',
  message_count: 0,
};

export const mockWelcomeMessage = {
  id: 'welcome-msg-001',
  role: 'assistant',
  content: 'Hi there! I\'m Emma, nice to meet you! What would you like to talk about?',
  timestamp: '2026-04-01T10:00:00Z',
  character_id: 'test-chat-char-001',
};

export const mockAIResponses = {
  greeting: 'Hello! It\'s great to meet you too! How are you doing today?',
  about_me: 'I\'m Emma, an AI companion who loves having meaningful conversations. I enjoy discussing all sorts of topics - from deep philosophical questions to fun everyday chats!',
  follow_up: 'That sounds interesting! Tell me more about it. I\'d love to hear your thoughts.',
};

export function createMockJWT(payload: { sub?: string; exp?: number; email?: string; is_admin?: boolean } = {}): string {
  const defaultPayload = {
    sub: payload.sub || 'test-user-001',
    email: payload.email || 'test@example.com',
    is_admin: payload.is_admin || false,
    exp: payload.exp || Math.floor(Date.now() / 1000) + 3600,
  };
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = btoa(JSON.stringify(defaultPayload));
  return `${header}.${body}.mock-signature`;
}

export function createSSEResponse(chunks: string[]): string {
  return chunks.map(chunk => `data: ${JSON.stringify({ content: chunk })}\n\n`).join('');
}

export function createSSEStreamChunk(content: string, done = false): string {
  const data = done 
    ? { content, done: true }
    : { content };
  return `data: ${JSON.stringify(data)}\n\n`;
}

export const mockCharacterListForChat = [
  mockChatCharacter,
  mockChatCharacterAnime,
];

export const mockChatHistoryEmpty = [];

export const mockChatHistory = [
  {
    id: 'msg-001',
    role: 'user',
    content: 'Hello Emma!',
    timestamp: '2026-04-01T10:01:00Z',
    character_id: 'test-chat-char-001',
  },
  {
    id: 'msg-002',
    role: 'assistant',
    content: 'Hello! It\'s great to meet you too! How are you doing today?',
    timestamp: '2026-04-01T10:01:05Z',
    character_id: 'test-chat-char-001',
  },
  {
    id: 'msg-003',
    role: 'user',
    content: 'I\'m doing well! Tell me about yourself.',
    timestamp: '2026-04-01T10:02:00Z',
    character_id: 'test-chat-char-001',
  },
  {
    id: 'msg-004',
    role: 'assistant',
    content: 'I\'m Emma, an AI companion who loves having meaningful conversations. I enjoy discussing all sorts of topics - from deep philosophical questions to fun everyday chats!',
    timestamp: '2026-04-01T10:02:10Z',
    character_id: 'test-chat-char-001',
  },
];

export const mockGuestCredits = {
  initial: 5,
  per_message_cost: 1,
};
