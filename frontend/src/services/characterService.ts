import { api } from './api';
import type { Character } from '@/types';

interface DiscoverCharactersParams {
  limit?: number;
  offset?: number;
  category?: string;
}

interface DiscoverCharactersResponse {
  characters: Character[];
  total: number;
}

export const characterService = {
  async getCharacterById(characterId: string): Promise<Character> {
    const response = await api.get<Character>(`/characters/${characterId}`);
    return response.data;
  },

  async getDiscoverCharacters(params: DiscoverCharactersParams = {}): Promise<DiscoverCharactersResponse> {
    const response = await api.get<DiscoverCharactersResponse>('/characters/discover', { params });
    return response.data;
  },

  async getCharacterBySlug(slug: string): Promise<Character> {
    const response = await api.get<Character>(`/characters/by-slug/${slug}`);
    return response.data;
  },
};
