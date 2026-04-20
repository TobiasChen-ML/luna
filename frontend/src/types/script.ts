/**
 * Script System Types (PRD v2026.02)
 *
 * Types for the hidden quest system, script sessions, and multi-modal cues.
 */

// ==================== Core Script Types ====================

export interface ScriptRelation {
  character_role: string;  // e.g., "teacher", "boss", "neighbor"
  user_role: string;       // e.g., "student", "employee", "tenant"
  relationship_tone: string; // e.g., "sweet", "dominant", "cold"
}

export interface ScriptContext {
  time: string;           // e.g., "evening", "weekend", "after_work"
  location: string;       // e.g., "elevator", "office", "apartment_door"
  theme: string;          // Story hook description
  ambience_id?: string;   // e.g., "rain_sound", "siren_distant"
}

export interface HiddenQuest {
  objective: string;           // What user should guide character to do (hidden from user)
  progress_signals: string[];  // Keywords/actions that count as progress
  completion_threshold: number; // 0-100, when to consider complete
}

export interface StateDefinition {
  trigger_at_progress: number; // Quest progress % when this state activates
}

export type ScriptState = 'Start' | 'Build' | 'Climax' | 'Resolve';

export interface MediaCue {
  cue_id: string;
  trigger_stage: ScriptState;
  trigger_quest_progress: number;  // 0-100
  media_type: 'image' | 'video' | 'voice_note';
  prompt_template: string;
  min_intimacy: number;  // Required intimacy level (0-100)
}

export interface Script {
  id: string;
  name: string;
  description: string;
  relation: ScriptRelation;
  context: ScriptContext;
  hidden_quest: HiddenQuest;
  state_definitions: Record<ScriptState, StateDefinition>;
  cues: MediaCue[];
  hint_chips: string[];  // 2-4 action suggestions
  is_official: boolean;
  creator_id: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ScriptListResponse {
  scripts: Script[];
  total: number;
  page: number;
  page_size: number;
}

// ==================== Script Session Types ====================

export interface StateTransition {
  from_state: ScriptState;
  to_state: ScriptState;
  timestamp: string;
  reason: string;
}

export interface ScriptSession {
  id: string;
  user_id: string;
  character_id: string;
  script_id: string;
  chat_session_id: string;
  current_state: ScriptState;
  quest_progress: number;  // 0-100
  state_entered_at: string;
  triggered_cues: string[];  // Array of cue_ids already triggered
  state_transitions: StateTransition[];
  is_completed: boolean;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ScriptSessionCreate {
  user_id: string;
  character_id: string;
  script_id: string;
  chat_session_id: string;
}

export interface ScriptSessionUpdate {
  quest_progress?: number;
  current_state?: ScriptState;
  is_completed?: boolean;
}

// ==================== Character-Script Binding ====================

export interface CharacterScriptBinding {
  id: string;
  character_id: string;
  script_id: string;
  is_active: boolean;
  created_at: string;
}

// ==================== Script Evaluation ====================

export interface ScriptEvaluationResult {
  quest_progress: number;
  state: ScriptState;
  should_trigger_media: boolean;
  media_type?: 'image' | 'video' | 'voice_note';
  media_prompt?: string;
  hint_chips?: string[];
}

// ==================== Message Type Extensions ====================

export type MessageType = 'text' | 'image' | 'video' | 'voice_note';
export type MessageStatus = 'generating' | 'ready' | 'failed';

export interface MessageScriptContext {
  script_id: string;
  state: ScriptState;
  quest_progress: number;
  cue_id?: string;
}

export interface ExtendedMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  message_type: MessageType;
  status: MessageStatus;
  image_url?: string;
  video_url?: string;
  audio_url?: string;
  duration?: number;  // For voice_note (seconds)
  cost?: number;
  script_context?: MessageScriptContext;
  timestamp: string;
}

// ==================== SSE Event Types ====================

export interface ScriptStateUpdatedEvent {
  script_session_id: string;
  new_state: ScriptState;
  quest_progress: number;
  timestamp: string;
}

export interface QuestProgressUpdatedEvent {
  script_session_id: string;
  quest_progress: number;
  current_state: ScriptState;
  hint_chips?: string[];
}

export interface MediaCueTriggeredEvent {
  cue_id: string;
  media_type: 'image' | 'video' | 'voice_note';
  placeholder_message_id: string;
  estimated_time_seconds: number;
}

export interface VoiceNoteReadyEvent {
  message_id: string;
  audio_url: string;
  duration: number;
  cost?: number;
}

export interface VideoReadyEvent {
  message_id: string;
  video_url: string;
  source_image_url?: string;
}

export interface IntimacyUpdatedEvent {
  character_id: string;
  intimacy: number;
  change: number;
  reason?: string;
}

// ==================== Memory Types ====================

export type MemoryType = 'episodic' | 'semantic' | 'emotional';

export interface Memory {
  id: string;
  character_id: string;
  user_id: string;
  content: string;
  memory_type: MemoryType;
  importance_score: number;  // 1-10
  context?: Record<string, any>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface MemoryQueryRequest {
  character_id: string;
  user_id: string;
  query: string;
  top_k?: number;  // Default 5
  memory_types?: MemoryType[];
  min_importance?: number;
}

export interface MemoryQueryResult {
  memory: Memory;
  relevance_score: number;  // 0.0-1.0
}

export interface MemoryQueryResponse {
  results: MemoryQueryResult[];
  query: string;
  total_found: number;
}

// ==================== Character Card v1.1 Extensions ====================

export interface GenerationParams {
  trigger_words: string[];
  negative_prompt?: string;
  lora_weights: Record<string, number>;
  seed_preference?: number;
}

export interface WorldInfo {
  keys: string[];
  content: string;
}

export interface RelationshipInfo {
  type: string;  // "rival", "friend", "mentor"
  summary: string;
}

export interface KnowledgeData {
  world_info: WorldInfo[];
  relationships_map: Record<string, RelationshipInfo>;
}

export interface ConsistencyConfig {
  force_prefix: string;
  ooc_threshold: number;  // 0.0-1.0
  depth_of_intimacy: 'cold' | 'warm' | 'intimate';
}

export interface CharacterPolicy {
  safety_level: 'safe' | 'moderate' | 'mature';
  hard_refusals: string[];
  consent_requirements: string[];
}

export interface CharacterCardExtensions {
  character_card_version?: string;
  knowledge?: KnowledgeData;
  consistency_config?: ConsistencyConfig;
  policy?: CharacterPolicy;
  generation_params?: GenerationParams;
}

// ==================== API Request/Response Types ====================

export interface StartScriptRequest {
  character_id: string;
  script_id: string;
  chat_session_id: string;
}

export interface CompleteScriptResponse {
  session: ScriptSession;
  continuation_script_id?: string;
  message: string;
}

export interface ActiveScriptResponse {
  active: boolean;
  session?: ScriptSession;
}

// ==================== UI State Types ====================

export interface ScriptUIState {
  activeScript?: Script;
  session?: ScriptSession;
  showHints: boolean;
  currentHints: string[];
  progressPercentage: number;
  stateDescription: string;
}

export interface IntimacyState {
  value: number;  // 0-100
  stage: string;  // "stranger", "friend", "companion", etc.
  lastUpdated: string;
}
