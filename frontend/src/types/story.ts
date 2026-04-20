/**
 * Story system type definitions for Talkie Lab-style stories.
 */

// ==================== Enums ====================

export type AuthorType = 'admin' | 'user' | 'ai_generated';
export type StoryStatus = 'draft' | 'published' | 'archived';
export type NarrativePhase = 'opening' | 'rising' | 'climax' | 'resolution';
export type EndingType = 'good' | 'neutral' | 'bad' | 'secret';
export type ProgressStatus = 'not_started' | 'in_progress' | 'completed' | 'abandoned';

// ==================== Nested Types ====================

export interface EntryConditions {
  min_relationship_stage: string;
  min_trust: number;
  min_intimacy: number;
  required_story_ids: string[];
  unlocked_by_default: boolean;
}

export interface AITriggerConditions {
  sentiment?: string;
  depth?: string;
  relationship_stage_min?: string;
  event_types?: string[];
}

export interface ChoiceEffects {
  trust_delta: number;
  intimacy_delta: number;
  attraction_delta: number;
  unlock_choice_id?: string;
}

export interface ChoiceConditions {
  min_trust?: number;
  min_intimacy?: number;
  required_choice_id?: string;
}

export interface StoryChoice {
  id: string;
  text: string;
  next_node_id: string;
  effects?: ChoiceEffects;
  conditions?: ChoiceConditions;
  // Runtime fields (set by backend when filtering)
  locked?: boolean;
  lock_reason?: string;
}

export interface NodeCharacterContext {
  mood: string;
  goal?: string;
  behavior_mode?: string;
  talking_points: string[];
}

export interface AutoAdvanceConfig {
  enabled: boolean;
  after_turns: number;
  next_node_id?: string;
}

export interface CompletionRewards {
  trust_bonus: number;
  intimacy_bonus: number;
  unlock_story_ids: string[];
}

// ==================== Story Types ====================

export interface Story {
  id: string;
  character_id: string;
  title: string;
  description: string;
  cover_image_url?: string;
  author_type: AuthorType;
  author_id: string;
  status: StoryStatus;
  is_official: boolean;
  entry_conditions: EntryConditions;
  start_node_id?: string;
  total_nodes: number;
  ai_trigger_keywords: string[];
  completion_rewards: CompletionRewards;
  play_count: number;
  created_at: string;
  updated_at: string;
  // Optional: attached when fetching for a specific user
  user_progress?: StoryProgressSummary;
}

export interface StoryProgressSummary {
  status: ProgressStatus;
  current_node_id?: string;
  completion_percentage: number;
}

// ==================== Story Node Types ====================

export interface StoryNode {
  id: string;
  story_id: string;
  sequence: number;
  title: string;
  narrative_phase: NarrativePhase;
  location?: string;
  scene_description: string;
  character_context: NodeCharacterContext;
  response_instructions?: string;
  max_turns_in_node: number;
  choices: StoryChoice[];
  auto_advance: AutoAdvanceConfig;
  is_ending_node: boolean;
  ending_type?: EndingType;
  trigger_image: boolean;
  image_prompt_hint?: string;
  created_at: string;
  updated_at: string;
}

// ==================== Story Progress Types ====================

export interface ChoiceMade {
  node_id: string;
  choice_id: string;
  timestamp: string;
}

export interface StoryProgress {
  id: string;
  user_id: string;
  story_id: string;
  character_id: string;
  status: ProgressStatus;
  current_node_id?: string;
  turns_in_current_node: number;
  visited_nodes: string[];
  choices_made: ChoiceMade[];
  ending_reached?: EndingType;
  completion_time_minutes?: number;
  session_id?: string;
  started_at?: string;
  last_played_at?: string;
  completed_at?: string;
  rewards_claimed: boolean;
  completion_percentage?: number;
}

// ==================== Active Story (in chat session) ====================

export interface ActiveStory {
  story_id: string;
  progress_id: string;
  current_node_id: string;
  turns_in_node: number;
}

// ==================== SSE Event Types ====================

export interface StoryProgressEvent {
  story_id: string;
  story_title: string;
  current_node_id: string;
  narrative_phase: NarrativePhase;
  turns_remaining?: number;
  available_choices: StoryChoice[];
}

export interface StoryTransitionEvent {
  story_id: string;
  from_node_id: string;
  to_node_id: string;
  transition_type: 'choice' | 'auto_advance' | 'ending';
  new_node_title?: string;
  new_scene_description?: string;
  ending_type?: EndingType;
}

export interface StorySuggestionEvent {
  story_id: string;
  title: string;
  description: string;
  cover_image_url?: string;
}

export interface StoryCompletedEvent {
  story_id: string;
  story_title: string;
  ending_type: EndingType;
  rewards: CompletionRewards;
  completion_time_minutes: number;
}

// ==================== Storyboard Types ====================

export interface StoryboardPanel {
  panel_no: number;
  phase: string;
  scene_visual: string;
  caption: string;
  reference_image_url?: string | null;
}

export interface StoryboardResponse {
  image_url: string;
  story_summary: string;
  panels: StoryboardPanel[];
}

// ==================== API Request/Response Types ====================

export interface StartStoryRequest {
  session_id: string;
}

export interface MakeChoiceRequest {
  choice_id: string;
}

export interface StartStoryResponse {
  story: Story;
  current_node: StoryNode;
  progress: StoryProgress;
}

export interface MakeChoiceResponse {
  next_node: StoryNode | null;
  progress: StoryProgress;
  is_ending: boolean;
}
