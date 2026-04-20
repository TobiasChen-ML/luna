/**
 * UGC Service - User Generated Content
 *
 * v3.1 API
 */

import { api } from './api';

// Type definitions
export interface Quota {
  current: number;
  limit: number;
  can_create: boolean;
}

export interface UserCharacter {
  id: string;
  owner_id: string;
  first_name: string;
  age: number;
  gender: string;
  personality_tags: string[];
  background: Record<string, unknown>;
  system_prompt: string;
  appearance: Record<string, unknown>;
  avatar_url?: string;
  voice_config: Record<string, unknown>;
  is_official: boolean;
  is_public: boolean;
  likes: number;
  downloads: number;
  created_at: string;
  updated_at: string;
}

export interface CommunityCharacter extends UserCharacter {
  published_at: string;
  creator_nickname: string;
  original_creator_id?: string;
  forked_from?: string;
}

export interface CharacterCreateData {
  first_name: string;
  age?: number;
  gender?: string;
  personality_tags?: string[];
  background?: Record<string, unknown>;
  system_prompt?: string;
  appearance?: Record<string, unknown>;
  avatar_url?: string;
  voice_config?: Record<string, unknown>;
}

export interface ScriptTemplate {
  id: string;
  name: string;
  genre: string;
  description: string;
  world_setting: string;
  preview_image?: string;
}

export interface CreatorOverview {
  creator_id: string;
  characters_total: number;
  characters_published: number;
  scripts_total: number;
  scripts_active: number;
  updated_at: string;
}

// API methods
export const ugcService = {
  // ==================== Character related ====================

  // Check character quota
  async checkCharacterQuota(): Promise<Quota> {
    const response = await api.get('/ugc/characters/quota');
    return response.data;
  },

  // Create character
  async createCharacter(data: CharacterCreateData): Promise<UserCharacter> {
    const response = await api.post('/ugc/characters', data);
    return response.data;
  },

  // Get my character list
  async getMyCharacters(page = 1, pageSize = 20): Promise<{
    characters: UserCharacter[];
    total: number;
    page: number;
    page_size: number;
  }> {
    const response = await api.get(`/ugc/characters?page=${page}&page_size=${pageSize}`);
    return response.data;
  },

  // Update character
  async updateCharacter(charId: string, data: Partial<CharacterCreateData>): Promise<UserCharacter> {
    const response = await api.put(`/ugc/characters/${charId}`, data);
    return response.data;
  },

  // Delete character
  async deleteCharacter(charId: string): Promise<void> {
    await api.delete(`/ugc/characters/${charId}`);
  },

  // Publish character
  async publishCharacter(charId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/ugc/characters/${charId}/publish`);
    return response.data;
  },

  // ==================== Script related ====================

  // Check script quota
  async checkScriptQuota(): Promise<Quota> {
    const response = await api.get('/ugc/scripts/quota');
    return response.data;
  },

  // Get script templates
  async getTemplates(genre?: string): Promise<{ templates: ScriptTemplate[] }> {
    const url = genre ? `/ugc/scripts/templates?genre=${genre}` : '/ugc/scripts/templates';
    const response = await api.get(url);
    return response.data;
  },

  // Create script from template
  async createScriptFromTemplate(
    templateId: string,
    characterId: string,
    customizations: Record<string, unknown>
  ): Promise<unknown> {
    const response = await api.post('/ugc/scripts/from-template', null, {
      params: {
        template_id: templateId,
        character_id: characterId,
      },
      data: customizations,
    });
    return response.data;
  },

  // Create custom script
  async createCustomScript(data: unknown): Promise<unknown> {
    const response = await api.post('/ugc/scripts/custom', data);
    return response.data;
  },

  // Update script
  async updateScript(scriptId: string, data: unknown): Promise<unknown> {
    const response = await api.put(`/ugc/scripts/${scriptId}`, data);
    return response.data;
  },

  // Delete script
  async deleteScript(scriptId: string): Promise<void> {
    await api.delete(`/ugc/scripts/${scriptId}`);
  },

  // Publish script
  async publishScript(scriptId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/ugc/scripts/${scriptId}/publish`);
    return response.data;
  },

  // ==================== Community browsing ====================

  // Browse community characters
  async browseCommunityCharacters(options?: {
    search?: string;
    sort_by?: 'published_at' | 'downloads';
    page?: number;
    pageSize?: number;
  }): Promise<{
    characters: CommunityCharacter[];
    total: number;
    page: number;
    page_size: number;
  }> {
    const params = new URLSearchParams();
    if (options?.search) params.append('search', options.search);
    if (options?.sort_by) params.append('sort_by', options.sort_by);
    if (options?.page) params.append('page', options.page.toString());
    if (options?.pageSize) params.append('page_size', options.pageSize.toString());

    const response = await api.get(`/ugc/community/characters?${params}`);
    return response.data;
  },

  // Fork Community Characters
  async forkCharacter(charId: string): Promise<{
    success: boolean;
    character: UserCharacter;
    message: string;
  }> {
    const response = await api.post(`/ugc/characters/${charId}/fork`);
    return response.data;
  },

  // Browse community scripts
  async browseCommunityScripts(options?: {
    genre?: string;
    search?: string;
    page?: number;
    pageSize?: number;
  }): Promise<{
    scripts: unknown[];
    total: number;
    page: number;
  }> {
    const params = new URLSearchParams();
    if (options?.genre) params.append('genre', options.genre);
    if (options?.search) params.append('search', options.search);
    if (options?.page) params.append('page', options.page.toString());
    if (options?.pageSize) params.append('page_size', options.pageSize.toString());

    const response = await api.get(`/ugc/community/scripts?${params}`);
    return response.data;
  },

  // ==================== Creator Center ====================
  async getCreatorOverview(): Promise<CreatorOverview> {
    const response = await api.get('/ugc/creator/overview');
    return response.data;
  },
};

export default ugcService;




