/**
 * Memory Management API Service
 * PRD v3 Section 8.3 - Memory Management UI
 */

import { api } from '@/services/api';

// ==================== Types ====================

export interface MemoryLayer {
  WORKING: 'working';
  EPISODIC: 'episodic';
  SEMANTIC: 'semantic';
}

export type MemoryLayerType = 'working' | 'episodic' | 'semantic';

export type GlobalMemoryCategory = 'preference' | 'fact' | 'dislike' | 'interest' | 'relationship';

export interface Memory {
  id: string;
  user_id: string;
  character_id: string;
  content: string;
  layer: MemoryLayerType;
  importance: number;
  decayed_importance: number;
  last_accessed?: string;
  created_at: string;
  updated_at: string;
  similarity?: number;
}

export interface GlobalMemory {
  id: string;
  user_id: string;
  content: string;
  category: GlobalMemoryCategory;
  source_character_id?: string;
  confidence: number;
  reference_count: number;
  is_confirmed: boolean;
  created_at: string;
  last_accessed: string;
}

export interface GlobalMemorySuggestion {
  content: string;
  category: GlobalMemoryCategory;
  source_character_id: string;
  occurrence_count: number;
  suggested_confidence: number;
}

export interface FactSummary {
  id?: string;
  content: string;
  category: string;
  confidence: number;
  created_at?: string;
  last_referenced?: string;
  reference_count: number;
}

export interface EpisodeSummary {
  summary: string;
  emotional_tone: string;
  importance: number;
  topics: string[];
  timestamp?: string;
}

export interface BondSummary {
  bond_type: string;
  strength: number;
  description: string;
}

export interface MemoryResponse {
  character_id: string;
  user_id: string;
  working_memory: Memory[];
  episodic_summary?: string;
  semantic_facts: string[];
  global_memories: GlobalMemory[];
  last_interaction?: string;
}

export interface OperationResponse {
  success: boolean;
  message: string;
}

export interface MemoryStats {
  total: number;
  by_layer: Record<MemoryLayerType, number>;
  global_memories: number;
}

// ==================== API Methods ====================

/**
 * Get all memories for a character
 */
export const getCharacterMemories = async (characterId: string): Promise<MemoryResponse> => {
  const response = await api.get(`/context/${characterId}/memory`);
  return response.data;
};

/**
 * Query memories with search
 */
export const queryMemories = async (
  characterId: string,
  query: string,
  layer?: MemoryLayerType,
  limit: number = 10
): Promise<{ memories: Memory[]; query: string }> => {
  const params = new URLSearchParams({ query, limit: String(limit) });
  if (layer) params.append('layer', layer);
  
  const response = await api.get(`/context/${characterId}/memory?${params}`);
  return response.data;
};

/**
 * Add a new memory
 */
export const addMemory = async (
  characterId: string,
  content: string,
  layer: MemoryLayerType = 'episodic',
  importance: number = 5
): Promise<{ memory_id: string; layer: string; importance: number }> => {
  const response = await api.post(`/context/${characterId}/memory`, {
    user_id: '',
    character_id: characterId,
    content,
    layer,
    importance,
  });
  return response.data;
};

/**
 * Forget a specific memory
 */
export const forgetMemory = async (
  characterId: string,
  memoryIds: string[]
): Promise<{ deleted_count: number }> => {
  const response = await api.post(`/context/${characterId}/memory/forget`, {
    memory_ids: memoryIds,
  });
  return response.data;
};

/**
 * Correct/update a memory
 */
export const correctMemory = async (
  characterId: string,
  memoryId: string,
  newContent: string
): Promise<{ memory_id: string; content: string }> => {
  const response = await api.post(`/context/${characterId}/memory/correct`, {
    memory_id: memoryId,
    new_content: newContent,
  });
  return response.data;
};

/**
 * Get memory statistics
 */
export const getMemoryStats = async (): Promise<MemoryStats> => {
  const response = await api.get('/context/stats');
  return response.data;
};

/**
 * Get full context summary (debug endpoint)
 */
export const getContextSummary = async (
  characterId: string
): Promise<MemoryResponse> => {
  const response = await api.get(`/context/${characterId}`);
  return response.data;
};

// ==================== Global Memory API ====================

/**
 * Get all global memories for the user
 */
export const getGlobalMemories = async (): Promise<{ memories: GlobalMemory[] }> => {
  const response = await api.get('/context/global');
  return response.data;
};

/**
 * Get suggestions for memories to promote to global
 */
export const getGlobalMemorySuggestions = async (): Promise<{ suggestions: GlobalMemorySuggestion[] }> => {
  const response = await api.get('/context/global/suggestions');
  return response.data;
};

/**
 * Create a new global memory
 */
export const createGlobalMemory = async (
  content: string,
  category: GlobalMemoryCategory = 'preference',
  sourceCharacterId?: string,
  confidence: number = 1.0
): Promise<{ global_memory_id: string; content: string; category: string }> => {
  const response = await api.post('/context/global', {
    content,
    category,
    source_character_id: sourceCharacterId,
    confidence,
  });
  return response.data;
};

/**
 * Promote an existing memory to global
 */
export const promoteToGlobalMemory = async (
  memoryId: string,
  category: GlobalMemoryCategory = 'preference'
): Promise<{ global_memory_id: string; status: string }> => {
  const response = await api.post('/context/global/promote', {
    memory_id: memoryId,
    category,
  });
  return response.data;
};

/**
 * Confirm a global memory
 */
export const confirmGlobalMemory = async (
  globalMemoryId: string
): Promise<{ global_memory_id: string; confirmed: boolean }> => {
  const response = await api.post(`/context/global/${globalMemoryId}/confirm`);
  return response.data;
};

/**
 * Delete a global memory
 */
export const deleteGlobalMemory = async (
  globalMemoryId: string
): Promise<{ deleted: boolean; global_memory_id: string }> => {
  const response = await api.delete(`/context/global/${globalMemoryId}`);
  return response.data;
};
