/**
 * Story Service - API calls for Talkie Lab-style story system.
 */
import { api } from './api';
import type {
  Story,
  StoryNode,
  StoryProgress,
  StartStoryResponse,
  MakeChoiceResponse,
  StoryboardResponse,
} from '@/types/story';

export const storyService = {
  /**
   * Get stories available for a character based on user's relationship.
   */
  async getAvailableStories(characterId: string): Promise<Story[]> {
    const response = await api.get<Story[]>(`/stories/available/${characterId}`);
    return response.data;
  },

  /**
   * Get all stories for a character.
   */
  async getCharacterStories(characterId: string, includeDrafts = false): Promise<Story[]> {
    const response = await api.get<Story[]>(`/stories/character/${characterId}`, {
      params: { include_drafts: includeDrafts },
    });
    return response.data;
  },

  /**
   * Get a specific story by ID.
   */
  async getStory(storyId: string): Promise<Story> {
    const response = await api.get<Story>(`/stories/${storyId}`);
    return response.data;
  },

  /**
   * Get all nodes for a story.
   */
  async getStoryNodes(storyId: string): Promise<StoryNode[]> {
    const response = await api.get<StoryNode[]>(`/stories/${storyId}/nodes`);
    return response.data;
  },

  /**
   * Start a story in the current chat session.
   */
  async startStory(storyId: string, sessionId: string): Promise<StartStoryResponse> {
    const response = await api.post<StartStoryResponse>(`/stories/${storyId}/start`, {
      session_id: sessionId,
    });
    return response.data;
  },

  /**
   * Resume an in-progress story.
   */
  async resumeStory(storyId: string, sessionId: string): Promise<StartStoryResponse> {
    const response = await api.post<StartStoryResponse>(`/stories/${storyId}/resume`, {
      session_id: sessionId,
    });
    return response.data;
  },

  /**
   * Make a choice in the current story.
   */
  async makeChoice(storyId: string, choiceId: string, sessionId?: string): Promise<MakeChoiceResponse> {
    const response = await api.post<MakeChoiceResponse>(
      `/stories/${storyId}/choice`,
      { choice_id: choiceId },
      { params: sessionId ? { session_id: sessionId } : undefined }
    );
    return response.data;
  },

  /**
   * Get user's progress for all stories with a character.
   */
  async getProgress(characterId: string): Promise<StoryProgress[]> {
    const response = await api.get<StoryProgress[]>(`/stories/progress/${characterId}`);
    return response.data;
  },

  /**
   * Create a new story for user's own character.
   */
  async createStory(storyData: Partial<Story>): Promise<Story> {
    const response = await api.post<Story>('/stories', storyData);
    return response.data;
  },

  /**
   * Update a story.
   */
  async updateStory(storyId: string, updates: Partial<Story>): Promise<Story> {
    const response = await api.put<Story>(`/stories/${storyId}`, updates);
    return response.data;
  },

  /**
   * Delete a story.
   */
  async deleteStory(storyId: string): Promise<void> {
    await api.delete(`/stories/${storyId}`);
  },

  /**
   * Create a new story node.
   */
  async createNode(nodeData: Partial<StoryNode>): Promise<StoryNode> {
    const response = await api.post<StoryNode>('/stories/nodes', nodeData);
    return response.data;
  },

  /**
   * Update a story node.
   */
  async updateNode(nodeId: string, updates: Partial<StoryNode>): Promise<StoryNode> {
    const response = await api.put<StoryNode>(`/stories/nodes/${nodeId}`, updates);
    return response.data;
  },

  /**
   * Delete a story node.
   */
  async deleteNode(nodeId: string): Promise<void> {
    await api.delete(`/stories/nodes/${nodeId}`);
  },

  /**
   * Generate a 3x3 cinematic storyboard image for a completed story.
   * Idempotent: returns cached result on subsequent calls.
   */
  async generateStoryboard(storyId: string, sessionId: string): Promise<StoryboardResponse> {
    const response = await api.post<StoryboardResponse>(
      `/stories/${storyId}/storyboard/generate`,
      { session_id: sessionId }
    );
    return response.data;
  },

  /**
   * Replay a completed story - creates new progress while preserving history.
   */
  async replayStory(storyId: string, sessionId: string): Promise<{
    progress_id: string;
    play_index: number;
    start_node_id: string | null;
    opening_message: string;
  }> {
    const response = await api.post(`/stories/${storyId}/replay`, { session_id: sessionId });
    return response.data;
  },

  /**
   * Get all play history for a story.
   */
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

  /**
   * Get detail of a specific play session.
   */
  async getPlayDetail(storyId: string, progressId: string): Promise<{
    id: string;
    user_id: string;
    story_id: string;
    status: string;
    current_node_id: string | null;
    visited_nodes: string[];
    choices_made: Array<{
      node_id: string;
      choice_id: string;
      timestamp: string;
    }>;
    ending_type: string | null;
    completion_time_minutes: number | null;
    started_at: string;
    completed_at: string | null;
    play_index: number;
  }> {
    const response = await api.get(`/stories/${storyId}/history/${progressId}`);
    return response.data;
  },

  /**
   * Archive current progress (before starting a new play).
   */
  async archiveProgress(storyId: string): Promise<{ success: boolean }> {
    const response = await api.post(`/stories/${storyId}/archive-progress`);
    return response.data;
  },
};

export default storyService;
