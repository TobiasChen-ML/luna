/**
 * Script Service
 * 
 * v3.1 API
 */

import { api } from './api';

// Type definitions
export interface SceneConfig {
  scene_id: string;
  name: string;
  description: string;
  atmosphere: string;
  time_of_day: string;
  ambient_sounds: string[];
  available_npcs: string[];
}

export interface NPCConfig {
  npc_id: string;
  name: string;
  description: string;
  role: string;
  voice_type: string;
  personality_brief: string;
}

export interface ScriptTrigger {
  trigger_id: string;
  name: string;
  trigger_type: string;
  conditions: Record<string, unknown>;
  target_scene_id?: string;
  description?: string;
  one_time?: boolean;
}

export interface ScriptVariables {
  relationship_type: string;
  tension_level: string;
  custom_vars: Record<string, unknown>;
  unlocked_scenes: string[];
  triggered_events: string[];
  progress: number;
}

export interface Script {
  id: string;
  title: string;
  description: string;
  genre: string;
  character_id: string;
  author_id: string;
  author_type: string;
  status: string;
  world_setting: string;
  user_role: string;
  user_role_description: string;
  opening_line: string;
  scenes: SceneConfig[];
  npcs: NPCConfig[];
  triggers: ScriptTrigger[];
  start_scene_id?: string;
  cover_image?: string;
  tags: string[];
  play_count: number;
  likes: number;
  created_at: string;
  updated_at: string;
  nodes?: ScriptNode[];
}

export interface ScriptNodeChoice {
  id: string;
  text: string;
  next_node_id?: string;
}

export interface ScriptNode {
  id: string;
  script_id: string;
  node_type: 'scene' | 'choice' | 'ending';
  title?: string;
  description?: string;
  narrative?: string;
  choices?: ScriptNodeChoice[];
  position_x?: number;
  position_y?: number;
}

export interface ScriptNodeCreate {
  script_id: string;
  node_type: 'scene' | 'choice' | 'ending';
  title?: string;
  description?: string;
  narrative?: string;
  choices?: ScriptNodeChoice[];
  position_x?: number;
  position_y?: number;
}

export interface ScriptCreateData {
  title: string;
  description: string;
  genre: string;
  character_id: string;
  world_setting: string;
  user_role: string;
  user_role_description: string;
  opening_line: string;
  scenes: SceneConfig[];
  npcs: NPCConfig[];
  triggers: ScriptTrigger[];
  start_scene_id?: string;
  tags: string[];
}

export interface ScriptListResponse {
  scripts: Script[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ScriptProgress {
  id: string;
  user_id: string;
  script_id: string;
  character_id: string;
  current_scene_id: string;
  variables: ScriptVariables;
  relationship_metrics: {
    affection: number;
    trust: number;
    intimacy: number;
  };
  session_count: number;
  total_turns: number;
  started_at: string;
  last_played_at: string;
}

export interface RelationshipStageInfo {
  script_id: string;
  metrics: {
    affection: number;
    trust: number;
    intimacy: number;
  };
  current_stage: string;
  next_stage: string | null;
  progress: number;
  requirements: {
    affection: number;
    trust: number;
    intimacy: number;
  };
}

// API methods
export const scriptService = {
  // Create script
  async createScript(data: ScriptCreateData): Promise<Script> {
    const response = await api.post('/scripts', data);
    return response.data;
  },
  
  // Get script details
  async getScript(scriptId: string): Promise<Script> {
    const response = await api.get(`/scripts/${scriptId}`);
    return response.data;
  },
  
  // Update script
  async updateScript(scriptId: string, data: Partial<ScriptCreateData>): Promise<Script> {
    const response = await api.put(`/scripts/${scriptId}`, data);
    return response.data;
  },
  
  // Delete script
  async deleteScript(scriptId: string): Promise<void> {
    await api.delete(`/scripts/${scriptId}`);
  },
  
  // Get character script list
  async getCharacterScripts(
    characterId: string,
    options?: { status?: string; page?: number; pageSize?: number }
  ): Promise<ScriptListResponse> {
    const params = new URLSearchParams();
    if (options?.status) params.append('status', options.status);
    if (options?.page) params.append('page', options.page.toString());
    if (options?.pageSize) params.append('page_size', options.pageSize.toString());
    
    const response = await api.get(`/scripts/character/${characterId}?${params}`);
    return response.data;
  },
  
  // Get my script list
  async getMyScripts(page = 1, pageSize = 20): Promise<ScriptListResponse> {
    const response = await api.get(`/scripts/user/my-scripts?page=${page}&page_size=${pageSize}`);
    return response.data;
  },
  
  // Start script session
  async startScript(
    scriptId: string,
    continueProgress = true
  ): Promise<{
    session_state: unknown;
    opening_message: string;
    progress_id: string;
  }> {
    const response = await api.post(`/scripts/${scriptId}/start`, {
      script_id: scriptId,
      continue_progress: continueProgress,
    });
    return response.data;
  },
  
  // Get script progress
  async getProgress(scriptId: string): Promise<ScriptProgress> {
    const response = await api.get(`/scripts/${scriptId}/progress`);
    return response.data;
  },
  
  // Get all user script progress
  async getAllProgress(): Promise<ScriptProgress[]> {
    const response = await api.get('/scripts/user/progress');
    return response.data;
  },
  
  // Get relationship stage info
  async getRelationshipStage(scriptId: string): Promise<RelationshipStageInfo> {
    const response = await api.get(`/scripts/${scriptId}/relationship-stage`);
    return response.data;
  },
  
  // Check emotion gates
  async checkEmotionGates(scriptId: string): Promise<{
    script_id: string;
    gates: Record<string, {
      passed: boolean;
      current: unknown;
      required: unknown;
    }>;
  }> {
    const response = await api.get(`/scripts/${scriptId}/gates`);
    return response.data;
  },
  
  // Load DAG
  async loadDAG(scriptId: string): Promise<{
    script_id: string;
    nodes: number;
    edges: number;
    start_node: string;
  }> {
    const response = await api.post(`/scripts/${scriptId}/load-dag`);
    return response.data;
  },
  
  // Validate DAG
  async validateDAG(scriptId: string): Promise<{
    script_id: string;
    valid: boolean;
    errors: string[];
  }> {
    const response = await api.get(`/scripts/${scriptId}/dag/validate`);
    return response.data;
  },
  
  // Get script endings
  async getEndings(scriptId: string): Promise<{
    script_id: string;
    endings: Array<{
      node_id: string;
      name: string;
      ending_type: string;
    }>;
  }> {
    const response = await api.get(`/scripts/${scriptId}/dag/endings`);
    return response.data;
  },

  // Review APIs
  async getPendingScripts(page = 1, pageSize = 20): Promise<ScriptListResponse> {
    const response = await api.get(`/admin/scripts/pending?page=${page}&page_size=${pageSize}`);
    return response.data;
  },

  async submitForReview(scriptId: string, comment?: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/admin/scripts/${scriptId}/submit-review`, { comment });
    return response.data;
  },

  async approveScript(scriptId: string, comment?: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/admin/scripts/${scriptId}/approve`, { comment });
    return response.data;
  },

  async rejectScript(scriptId: string, comment?: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/admin/scripts/${scriptId}/reject`, { comment });
    return response.data;
  },

  async getScriptReviews(scriptId: string): Promise<Array<{
    id: string;
    script_id: string;
    reviewer_id: string;
    action: string;
    previous_status: string | null;
    comment: string | null;
    created_at: string;
  }>> {
    const response = await api.get(`/admin/scripts/${scriptId}/reviews`);
    return response.data;
  },

  async createNode(data: ScriptNodeCreate): Promise<ScriptNode> {
    const response = await api.post(`/admin/scripts/${data.script_id}/nodes`, data);
    return response.data;
  },

  async updateNode(nodeId: string, data: Partial<ScriptNode> & { script_id?: string }): Promise<ScriptNode> {
    const scriptId = data.script_id;
    if (!scriptId) {
      throw new Error('script_id is required for node update');
    }
    const payload = { ...data };
    delete payload.script_id;
    const response = await api.put(`/admin/scripts/${scriptId}/nodes/${nodeId}`, payload);
    return response.data;
  },

  async deleteNode(nodeId: string, scriptId?: string): Promise<void> {
    if (!scriptId) {
      throw new Error('script_id is required for node deletion');
    }
    await api.delete(`/admin/scripts/${scriptId}/nodes/${nodeId}`);
  },

  // Replay APIs
  async replayStory(storyId: string, sessionId: string): Promise<{
    progress_id: string;
    play_index: number;
    start_node_id: string;
    opening_message: string;
  }> {
    const response = await api.post(`/stories/${storyId}/replay`, { session_id: sessionId });
    return response.data;
  },

  async getPlayHistory(storyId: string): Promise<Array<{
    play_id: string;
    play_index: number;
    status: string;
    ending_type: string | null;
    completion_time_minutes: number | null;
    started_at: string;
    completed_at: string | null;
    choices_count: number;
  }>> {
    const response = await api.get(`/stories/${storyId}/history`);
    return response.data;
  },
};

export default scriptService;


