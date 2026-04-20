/**
 * Script Library API Service
 */
import { api } from './api';
import type {
  ScriptLibrary,
  ScriptLibraryListResponse,
  ScriptLibraryFilter,
  ScriptLibraryCreate,
  ScriptLibraryUpdate,
  ScriptTagsByCategory,
  ScriptTag,
} from '../types/scriptLibrary';

const BASE_URL = '/api/script-library';

export const scriptLibraryService = {
  async listScripts(filter: ScriptLibraryFilter = {}): Promise<ScriptLibraryListResponse> {
    const params = new URLSearchParams();
    
    if (filter.emotion_tones?.length) {
      params.append('emotion_tones', filter.emotion_tones.join(','));
    }
    if (filter.relation_types?.length) {
      params.append('relation_types', filter.relation_types.join(','));
    }
    if (filter.contrast_types?.length) {
      params.append('contrast_types', filter.contrast_types.join(','));
    }
    if (filter.era) params.append('era', filter.era);
    if (filter.gender_target) params.append('gender_target', filter.gender_target);
    if (filter.character_gender) params.append('character_gender', filter.character_gender);
    if (filter.profession) params.append('profession', filter.profession);
    if (filter.age_rating) params.append('age_rating', filter.age_rating);
    if (filter.length) params.append('length', filter.length);
    if (filter.search) params.append('search', filter.search);
    if (filter.status) params.append('status', filter.status);
    if (filter.page) params.append('page', filter.page.toString());
    if (filter.page_size) params.append('page_size', filter.page_size.toString());
    
    const response = await api.get(`${BASE_URL}?${params.toString()}`);
    return response.data;
  },

  async getRandomScripts(count: number = 5, status: string = 'published'): Promise<ScriptLibrary[]> {
    const response = await api.get(`${BASE_URL}/random?count=${count}&status=${status}`);
    return response.data;
  },

  async getScript(scriptId: string): Promise<ScriptLibrary> {
    const response = await api.get(`${BASE_URL}/${scriptId}`);
    return response.data;
  },

  async createScript(data: ScriptLibraryCreate): Promise<ScriptLibrary> {
    const response = await api.post(BASE_URL, data);
    return response.data;
  },

  async updateScript(scriptId: string, data: ScriptLibraryUpdate): Promise<ScriptLibrary> {
    const response = await api.put(`${BASE_URL}/${scriptId}`, data);
    return response.data;
  },

  async deleteScript(scriptId: string): Promise<{ success: boolean }> {
    const response = await api.delete(`${BASE_URL}/${scriptId}`);
    return response.data;
  },

  async getAllTags(): Promise<ScriptTagsByCategory> {
    const response = await api.get(`${BASE_URL}/tags`);
    return response.data;
  },

  async getTagsByCategory(category: string): Promise<ScriptTag[]> {
    const response = await api.get(`${BASE_URL}/tags/${category}`);
    return response.data;
  },

  async searchScripts(query: string, page: number = 1): Promise<ScriptLibraryListResponse> {
    return this.listScripts({ search: query, page });
  },

  async getScriptsByEmotionTone(tone: string, page: number = 1): Promise<ScriptLibraryListResponse> {
    return this.listScripts({ emotion_tones: [tone], page });
  },

  async getScriptsByRelationType(type: string, page: number = 1): Promise<ScriptLibraryListResponse> {
    return this.listScripts({ relation_types: [type], page });
  },

  async getScriptsByContrastType(type: string, page: number = 1): Promise<ScriptLibraryListResponse> {
    return this.listScripts({ contrast_types: [type], page });
  },

  async getScriptsByEra(era: string, page: number = 1): Promise<ScriptLibraryListResponse> {
    return this.listScripts({ era, page });
  },

  async getScriptsByGenderTarget(target: string, page: number = 1): Promise<ScriptLibraryListResponse> {
    return this.listScripts({ gender_target: target, page });
  },

  async getScriptsByAgeRating(rating: string, page: number = 1): Promise<ScriptLibraryListResponse> {
    return this.listScripts({ age_rating: rating, page });
  },
};

export default scriptLibraryService;
