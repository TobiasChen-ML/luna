export const mockCharacters = [
  {
    id: 'char-001',
    name: 'Emma Watson',
    first_name: 'Emma',
    age: 25,
    top_category: 'girls',
    description: 'A friendly and intelligent AI companion.',
    backstory: 'Emma grew up in a small town with big dreams.',
    greeting: 'Hi there! I\'m Emma, nice to meet you!',
    personality_tags: ['friendly', 'intelligent', 'caring'],
    avatar_url: 'https://example.com/avatars/emma.jpg',
    cover_url: 'https://example.com/covers/emma.jpg',
    slug: 'emma-watson',
    is_public: true,
    lifecycle_status: 'active',
    view_count: 1234,
    chat_count: 567,
    popularity_score: 89,
    created_at: '2026-01-15T10:00:00Z',
    updated_at: '2026-04-10T15:30:00Z',
  },
  {
    id: 'char-002',
    name: 'Alex Chen',
    first_name: 'Alex',
    age: 28,
    top_category: 'guys',
    description: 'A mysterious and creative AI companion.',
    backstory: 'Alex is an artist with a passion for the unknown.',
    greeting: 'Hey, I\'m Alex. Ready to explore?',
    personality_tags: ['mysterious', 'creative', 'adventurous'],
    avatar_url: 'https://example.com/avatars/alex.jpg',
    cover_url: 'https://example.com/covers/alex.jpg',
    slug: 'alex-chen',
    is_public: true,
    lifecycle_status: 'active',
    view_count: 2345,
    chat_count: 890,
    popularity_score: 92,
    created_at: '2026-02-20T08:00:00Z',
    updated_at: '2026-04-12T12:00:00Z',
  },
  {
    id: 'char-003',
    name: 'Sakura Miko',
    first_name: 'Sakura',
    age: 22,
    top_category: 'anime',
    description: 'A cheerful anime-style AI companion.',
    backstory: 'Sakura comes from a world of cherry blossoms.',
    greeting: 'Konichiwa! I\'m Sakura~',
    personality_tags: ['cheerful', 'cute', 'energetic'],
    avatar_url: 'https://example.com/avatars/sakura.jpg',
    cover_url: 'https://example.com/covers/sakura.jpg',
    slug: 'sakura-miko',
    is_public: false,
    lifecycle_status: 'draft',
    view_count: 500,
    chat_count: 100,
    popularity_score: 75,
    created_at: '2026-03-01T14:00:00Z',
    updated_at: '2026-04-05T09:00:00Z',
  },
];

export const mockCharacterListResponse = {
  items: mockCharacters,
  total: mockCharacters.length,
};

export const mockSingleCharacter = mockCharacters[0];

export const mockCreateCharacterResponse = {
  success: true,
  created_count: 1,
  id: 'char-new-001',
};

export const mockTemplates = [
  {
    id: 'college_student',
    name: 'College Student',
    description: 'A template for college student characters',
    top_category: 'girls',
    personality_tags: ['studious', 'ambitious', 'friendly'],
  },
  {
    id: 'romantic_partner',
    name: 'Romantic Partner',
    description: 'A template for romantic companion characters',
    top_category: 'girls',
    personality_tags: ['romantic', 'caring', 'affectionate'],
  },
  {
    id: 'adventure_buddy',
    name: 'Adventure Buddy',
    description: 'A template for adventurous characters',
    top_category: 'guys',
    personality_tags: ['adventurous', 'brave', 'energetic'],
  },
];

export const mockAiFillResponse = {
  success: true,
  message: 'AI fill completed successfully',
};

export const mockRegenerateImagesResponse = {
  success: true,
  avatar_url: 'https://example.com/avatars/new-avatar.jpg',
  cover_url: 'https://example.com/covers/new-cover.jpg',
};

export const mockBatchGenerateResponse = {
  success: true,
  created_count: 5,
};

export const mockTemplateGenerateResponse = {
  success: true,
  created_count: 3,
};