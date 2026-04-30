// Subscription tier type
export type SubscriptionTier = 'free' | 'premium';

// Discovery / categorisation types
export type TopCategory = 'girls' | 'anime' | 'guys';

export interface FilterTagMeta {
  slug: string;
  display_name: string;
  count: number;
}

export interface CategorySummary {
  slug: TopCategory;
  display_name: string;
  url: string;
  count: number;
  filter_tags: FilterTagMeta[];
}

export interface CategoriesResponse {
  categories: CategorySummary[];
  total_characters: number;
}

// Re-export story types
export * from './story';

// Re-export script types (PRD v2026.02)
export * from './script';

// User Types
export interface User {
  id: string;
  email: string;
  firebase_uid: string;
  display_name?: string;
  gender?: string;
  is_adult: boolean;
  date_of_birth?: string;  // Stored as "YYYY-MM-DD" format
  subscription_tier: SubscriptionTier;
  credits: number;
  telegram_id?: string | null;
  telegram_username?: string | null;
  telegram_bound_at?: string | null;
  // Two-bucket credit system
  purchased_credits?: number;  // Credits from purchases (never expire)
  monthly_credits_remaining?: number;  // Monthly credits (reset each cycle)
  subscription_period_end?: string;  // When monthly credits reset
  subscription_start_date?: string;  // When subscription started
  mature_preference?: 'teen' | 'adult';
  preferences?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export type ReviewStatus = 'pending' | 'approved' | 'rejected';

// Character Types
export interface Character {
  id: string;
  user_id: string;
  slug?: string;
  first_name: string;
  age: number;
  style: 'Realistic' | 'Anime';
  gender: string;
  appearance: AppearanceData;
  outfit: OutfitData;
  personality_tags: string[];
  background: BackgroundData;
  media_urls: MediaUrls;
  profile_image_url?: string;
  video_url?: {
    IDLE_VIDEO_URL: string;
    TALKING_VIDEO_URL: string;
  };
  voice_profile?: string;
  is_deleted: boolean;
  system_prompt?: string;
  life_history?: string;
  created_at: string;
  updated_at: string;
  // Relationship locking fields (PRD v2026.02)
  relationship_role?: string;
  user_role?: string;
  relationship_locked?: boolean;
  relationship_locked_at?: string;
  // Force Character Routing (PRD v2026.02)
  consistency_config?: ConsistencyConfig;
  // Script / story context
  scene_preset?: string;
  story_synopsis?: string;
  greeting?: string;
  // UGC Creator System
  visibility?: 'public' | 'private';
  is_ugc_seeded?: boolean;
  creator_profile?: {
    user_id: string;
    display_name: string;
    avatar_url: string;
    bio?: string;
  };
  // UGC Review System
  review_status?: ReviewStatus;
  rejection_reason?: string;
  // Discovery / categorisation
  top_category?: TopCategory;
  filter_tags?: string[];
  preview_video_url?: string | null;
}

export interface ConsistencyConfig {
  force_prefix?: string;
  ooc_threshold?: number;
  depth_of_intimacy?: 'cold' | 'warm' | 'intimate';
}

export interface ForceRoutingTemplate {
  id: string;
  name: string;
  description: string;
  instruction: string;
}

export interface AppearanceData {
  body_type?: string;
  hair_style?: string;
  hair_color?: string;
  eye_color?: string;
  lip_color?: string;
  skin_tone?: string;
}

export interface OutfitData {
  style?: string;
  description?: string;
}

export interface BackgroundData {
  profession?: string;
  hobbies?: string[];
  relationship?: string;
  backstory?: string;
}

export interface MediaUrls {
  avatar?: string;
  gallery?: string[];
}

// Chat Types
export interface ChatMessage {
  id: string;
  character_id: string;
  role: 'user' | 'ai';
  content: string;
  created_at: string;
}

// API Response Types
export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

// Subscription & Billing Types
export type BillingPeriod = 'month' | 'year';
export type SubscriptionStatus = 'active' | 'past_due' | 'canceled' | 'incomplete';
export type PaymentType = 'subscription' | 'credit_pack' | 'refund';
export type PaymentStatus = 'succeeded' | 'pending' | 'failed' | 'refunded';

export interface SubscriptionPricePoint {
  month: number;
  year: number;
  currency: string;
}

export interface TierBenefitConfig {
  monthly_credits: number;
  daily_checkin_credits: number;
  character_limit: number;
}

export interface CreditCostConfig {
  message: number;
  image: number;
  video: number;
  voice_call_per_minute: number;
}

export interface BillingPricingConfig {
  subscription_prices: Record<SubscriptionTier, SubscriptionPricePoint>;
  credit_costs: CreditCostConfig;
  tier_benefits: Record<SubscriptionTier, TierBenefitConfig>;
}

export interface Subscription {
  id: string;
  user_id: string;
  tier: SubscriptionTier;
  billing_period: BillingPeriod;
  status: SubscriptionStatus;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  canceled_at: string | null;
  created_at: string;
}

export interface CreditPack {
  id: string;
  name: string;
  credits: number;
  price_cents: number;
  currency: string;
  description: string;
  is_popular: boolean;
}

export interface CreditBalance {
  total: number;
  monthly_remaining: number;
  purchased: number;
  next_reset: string | null;
  subscription_tier: SubscriptionTier;
}

export interface PaymentHistoryItem {
  id: string;
  type: PaymentType;
  amount_cents: number;
  currency: string;
  status: PaymentStatus;
  credits_granted: number | null;
  description: string;
  created_at: string;
}
