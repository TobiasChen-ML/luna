export interface ImageGenerationLoRA {
  id: string;
  name: string;
  /** Trigger word(s) prepended to the prompt when selected */
  triggerWord: string;
  description: string;
  category: ImageLoRACategory;
  defaultStrength: number;
}

export type ImageLoRACategory = 'scene';

export const IMAGE_LORA_CATEGORIES: Record<ImageLoRACategory, string> = {
  scene: 'Scene',
};

export const IMAGE_GENERATION_LORAS: ImageGenerationLoRA[] = [
  {
    id: 'blowjob',
    name: 'Blowjob',
    triggerWord:
      'blowjob, oral sex, penis in mouth, pov, beautiful woman on knees, looking up at viewer, completely nude, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Oral sex – blowjob POV',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'butterfly_sex',
    name: 'Butterfly Sex',
    triggerWord:
      'butterfly sex, missionary position, penis, sex, legs raised, beautiful woman, looking at viewer, completely nude, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Butterfly / missionary sex position',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'cumshot',
    name: 'Cumshot',
    triggerWord:
      'projectile cum, cumshot, penis, pov, facial, covered in cum, beautiful woman kneeling, completely nude, looking at viewer, awaiting cum, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Cumshot / facial finish',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'doggy_style',
    name: 'Doggy Style',
    triggerWord:
      'doggy style, doggy style position, penis, sex, beautiful woman, from behind, looking back, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Doggy style sex position',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'fivesome',
    name: 'Fivesome',
    triggerWord:
      'fivesome, group sex, multiple men, beautiful woman, completely nude, gangbang, all holes filled, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Fivesome group sex',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'foodtease',
    name: 'Food Tease',
    triggerWord:
      'foodtease, food play, licking food sensually, beautiful woman, completely nude, seductive expression, looking at viewer, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Sensual food teasing',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'foursome',
    name: 'Foursome',
    triggerWord:
      'foursome, group sex, multiple partners, beautiful woman, completely nude, double penetration, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Foursome group sex',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'handjob',
    name: 'Handjob',
    triggerWord:
      'handjob, stroking penis, pov, beautiful woman, hand wrapped around penis, looking at viewer, completely nude, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'POV handjob',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'licking_cock',
    name: 'Licking Cock',
    triggerWord:
      'licking cock, tongue on penis, oral teasing, pov, beautiful woman, looking up at viewer, completely nude, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Cock licking / oral teasing',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'orgasming',
    name: 'Orgasming',
    triggerWord:
      'orgasming, head back, mouth open, trembling, ecstasy, beautiful woman, completely nude, climax, ahegao, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Orgasm expression',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'reverse_gang_bang',
    name: 'Reverse Gang Bang',
    triggerWord:
      'reverse gang bang, multiple women, group sex, beautiful women, completely nude, surrounding man, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Reverse gang bang',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'reversecowgirl',
    name: 'Reverse Cowgirl',
    triggerWord:
      'reversecowgirl, reverse cowgirl position, penis, sex, from behind, looking back, beautiful woman, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Reverse cowgirl position',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'riding_cowgirl',
    name: 'Riding Cowgirl',
    triggerWord:
      'riding cowgirl, cowgirl position, penis, sex, girl on top, beautiful woman, looking at viewer, hands on chest, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Riding cowgirl position',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'self_stroking',
    name: 'Self Stroking',
    triggerWord:
      'self stroking, masturbation, fingers, beautiful woman, completely nude, touching herself, legs spread, pov, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Self stroking / masturbation',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'sidefuck',
    name: 'Sidefuck',
    triggerWord:
      'sidefuck, side lying position, penis, sex, spooning, beautiful woman, completely nude, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Side-lying sex position',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'teasing',
    name: 'Teasing',
    triggerWord:
      'teasing, seductive pose, beautiful woman, partially undressed, biting lip, looking at viewer, lingerie pull down, sensual, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Seductive teasing pose',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'threesome',
    name: 'Threesome',
    triggerWord:
      'threesome, two men, beautiful woman, completely nude, double penetration, sandwich position, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Threesome sex',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'titty_fucking',
    name: 'Titty Fucking',
    triggerWord:
      'beautiful woman, titty fucking, paizuri, penis, pov crotch, open mouth, breasts squeezed together, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Titty fucking / paizuri',
    category: 'scene',
    defaultStrength: 0.95,
  },
  {
    id: 'undressing',
    name: 'Undressing',
    triggerWord:
      'undressing, pulled by self, beautiful woman, shorts pull, ass, pussy, from behind, looking back, smiling, masterpiece photography, lightrays, very detailed skin, 8k focus stacking',
    description: 'Undressing / strip tease',
    category: 'scene',
    defaultStrength: 0.95,
  },
];

/** All LoRAs grouped by category */
export function getLorasByCategory(): Record<ImageLoRACategory, ImageGenerationLoRA[]> {
  const result = {} as Record<ImageLoRACategory, ImageGenerationLoRA[]>;
  for (const cat of Object.keys(IMAGE_LORA_CATEGORIES) as ImageLoRACategory[]) {
    result[cat] = IMAGE_GENERATION_LORAS.filter((l) => l.category === cat);
  }
  return result;
}
