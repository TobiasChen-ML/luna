export interface HunyuanVideoLoRA {
  id: string;
  name: string;
  /** Direct Civitai download URL — sent as loras[].path to Novita */
  civitaiId: string;
  /** Full scene prompt auto-filled when this LoRA is selected */
  defaultPrompt: string;
  description: string;
  defaultStrength: number;
}

export const HUNYUAN_VIDEO_LORAS: HunyuanVideoLoRA[] = [
  {
    id: 'foot_job',
    name: 'Foot Job',
    civitaiId: 'https://civitai.com/api/download/models/2249774?type=Model&format=SafeTensor',
    defaultPrompt:
      'footjob,A man\'s penis slowly emerges from outside the screen, sliding between a woman\'s legs. She takes the lead, quickly rubbing it with her feet in a fast, rhythmic motion to perform a footjob',
    description: 'Footjob scene with rhythmic foot motion',
    defaultStrength: 0.8,
  },
  {
    id: 'tit_job',
    name: 'Tit Job',
    civitaiId: 'https://civitai.com/api/download/models/2514326?type=Model&format=SafeTensor',
    defaultPrompt:
      'A man appears and inserts his penis between her breasts, after which the woman stimulates it with both breasts, wrapping them tightly around his shaft with her hands and moving them up and down.',
    description: 'Titjob / paizuri scene',
    defaultStrength: 0.8,
  },
  {
    id: 'fingering',
    name: 'Fingering',
    civitaiId: 'https://civitai.com/api/download/models/1694292?type=Model&format=SafeTensor',
    defaultPrompt:
      'She inserts two fingers into her pussy. She masturbates by sliding her fingers in and out of her pussy.',
    description: 'Self-fingering masturbation scene',
    defaultStrength: 0.8,
  },
  {
    id: 'blow_job',
    name: 'Blow Job',
    civitaiId: 'https://civitai.com/api/download/models/2021249?type=Model&format=SafeTensor',
    defaultPrompt:
      'A woman performs oral sex on a man. She moves her head up and down while she sucks the shaft of the penis. The view is POV.',
    description: 'POV blowjob scene',
    defaultStrength: 0.8,
  },
  {
    id: 'cum_on_face',
    name: 'Cum on Face',
    civitaiId: 'https://civitai.com/api/download/models/1860691?type=Model&format=SafeTensor',
    defaultPrompt: 'cum on face, cum in mouth,cum shoots from a penis,cum on tongue',
    description: 'Facial / cum shot scene',
    defaultStrength: 0.8,
  },
];
