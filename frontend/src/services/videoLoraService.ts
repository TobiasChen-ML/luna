import { api } from '@/services/api';

export interface VideoLoraAction {
  id: string;
  lora_preset_id: string;
  lora_name: string;
  action_label: string;
  trigger_word: string;
  default_prompt: string;
  description: string;
}

interface VideoLoraActionsResponse {
  actions: VideoLoraAction[];
}

let cache: VideoLoraAction[] | null = null;
let inflight: Promise<VideoLoraAction[]> | null = null;

export async function fetchVideoLoraActions(force = false): Promise<VideoLoraAction[]> {
  if (!force && cache) return cache;
  if (!force && inflight) return inflight;

  inflight = api
    .get<VideoLoraActionsResponse>('/images/video-lora-actions')
    .then((res) => {
      const actions = Array.isArray(res.data?.actions) ? res.data.actions : [];
      cache = actions;
      return actions;
    })
    .finally(() => {
      inflight = null;
    });

  return inflight;
}

