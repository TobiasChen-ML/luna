/**
 * Script Library Types
 */

export interface ScriptSeedCharacter {
  name: string;
  age: number;
  surface_identity: string;
  true_identity: string;
  profession: string;
}

export interface ScriptSeedContrast {
  surface: string;
  truth: string;
  hook: string;
}

export interface ScriptSeedProgression {
  start: string;
  build: string;
  climax: string;
  resolve: string;
}

export interface ScriptSeedKeyNode {
  name: string;
  description: string;
  trigger: string;
}

export interface ScriptSeedEndings {
  good: string;
  neutral: string;
  bad: string;
  secret: string;
}

export interface ScriptSeed {
  character: ScriptSeedCharacter;
  contrast: ScriptSeedContrast;
  progression: ScriptSeedProgression;
  key_nodes: ScriptSeedKeyNode[];
  endings: ScriptSeedEndings;
}

export interface ScriptLibrary {
  id: string;
  title: string;
  title_en?: string;
  summary?: string;
  emotion_tones: string[];
  relation_types: string[];
  contrast_types: string[];
  era?: string;
  gender_target?: string;
  character_gender?: string;
  profession?: string;
  length?: string;
  age_rating?: string;
  contrast_surface?: string;
  contrast_truth?: string;
  contrast_hook?: string;
  script_seed?: ScriptSeed;
  full_script?: Record<string, unknown>;
  popularity: number;
  status: 'draft' | 'published' | 'archived';
  created_at: string;
  updated_at: string;
}

export interface ScriptLibraryListResponse {
  items: ScriptLibrary[];
  total: number;
  page: number;
  page_size: number;
}

export interface ScriptTag {
  id: string;
  category: string;
  name: string;
  name_en?: string;
  description?: string;
  examples: string[];
  parent_id?: string;
}

export interface ScriptTagsByCategory {
  emotion_tones: ScriptTag[];
  relation_types: ScriptTag[];
  contrast_types: ScriptTag[];
  eras: ScriptTag[];
  professions: ScriptTag[];
  gender_targets: ScriptTag[];
  character_genders: ScriptTag[];
  lengths: ScriptTag[];
  age_ratings: ScriptTag[];
}

export interface ScriptLibraryFilter {
  emotion_tones?: string[];
  relation_types?: string[];
  contrast_types?: string[];
  era?: string;
  gender_target?: string;
  character_gender?: string;
  profession?: string;
  age_rating?: string;
  length?: string;
  search?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export interface ScriptLibraryCreate {
  title: string;
  title_en?: string;
  summary?: string;
  emotion_tones?: string[];
  relation_types?: string[];
  contrast_types?: string[];
  era?: string;
  gender_target?: string;
  character_gender?: string;
  profession?: string;
  length?: string;
  age_rating?: string;
  contrast_surface?: string;
  contrast_truth?: string;
  contrast_hook?: string;
  script_seed?: ScriptSeed;
  full_script?: Record<string, unknown>;
}

export interface ScriptLibraryUpdate {
  title?: string;
  title_en?: string;
  summary?: string;
  emotion_tones?: string[];
  relation_types?: string[];
  contrast_types?: string[];
  era?: string;
  gender_target?: string;
  character_gender?: string;
  profession?: string;
  length?: string;
  age_rating?: string;
  contrast_surface?: string;
  contrast_truth?: string;
  contrast_hook?: string;
  script_seed?: ScriptSeed;
  full_script?: Record<string, unknown>;
  status?: 'draft' | 'published' | 'archived';
}