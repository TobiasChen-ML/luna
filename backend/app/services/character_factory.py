import asyncio
import logging
import random
import json
import uuid
from typing import Optional
from datetime import datetime

from app.core.database import db
from app.models.character import (
    CharacterCreate,
    OCCUPATION_TEMPLATES,
    ETHNICITY_IMAGE_STYLES,
    NATIONALITY_CONFIGS,
    generate_slug,
)
from app.services.character_service import character_service
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

LLM_PROFILE_PROMPT = """Generate a unique character for an AI companion app.

{trend_hints}

Requirements:
- The character should be diverse and avoid overused names (like Emma, Sophia, Olivia)
- Generate a realistic name appropriate for the given nationality
- Make the personality multi-dimensional with at least one unexpected trait
- The backstory should hint at interesting conversation topics
- The greeting should immediately establish the character's unique voice

Character constraints:
- Age range: {age_min}-{age_max}
- Suggested occupation direction: {occupation_hint}
- Suggested nationality direction: {nationality_hint}

Generate a JSON object with these fields:
{{
  "name": "string - a realistic first name",
  "age": integer,
  "ethnicity": "one of: white, asian, black, latina, middle_eastern",
  "nationality": "country code like: usa, japan, korea, china, germany, france, uk, italy, spain, brazil, india, russia, australia, canada, mexico, thailand, vietnam, philippines",
  "occupation": "a creative occupation string (not limited to presets)",
  "personality_tags": ["2-4 unique personality trait strings"],
  "description": "1-2 sentence character description (max 200 chars)",
  "personality_summary": "brief personality summary (max 100 chars)",
  "backstory": "short backstory (max 300 chars)",
  "greeting": "opening message in character's style (max 150 chars)"
}}

Ensure each character is unique, memorable, and has depth. Respond with valid JSON only."""

FALLBACK_NAMES = [
    "Aria", "Luna", "Zara", "Mei", "Sofia", "Yuki", "Lena", "Nina",
    "Mila", "Isla", "Kira", "Vera", "Sora", "Lina", "Dara", "Rina",
    "Eva", "Mia", "Ava", "Lea", "Nia", "Tara", "Sara", "Maya",
    "Freya", "Elara", "Nia", "Reina", "Anya", "Kiara", "Astrid", "Celeste",
    "Valentina", "Camille", "Emiko", "Priya", "Sienna", "Thalia", "Zoya",
]

FALLBACK_PERSONALITY_POOL = [
    "gentle", "caring", "playful", "mysterious", "confident",
    "shy", "adventurous", "intellectual", "romantic", "flirty",
    "witty", "dreamy", "sassy", "nurturing", "rebellious",
    "stoic", "eccentric", "melancholic", "mischievous", "philosophical",
    "spontaneous", "pragmatic", "whimsical", "resilient", "perceptive",
]

AVATAR_BACKGROUND_SCENES = [
    "on a sunny beach with waves behind her",
    "in a luxury hotel room, sitting on the bed",
    "in a modern shower with glass walls and steam",
    "on a rooftop terrace with city skyline at golden hour",
    "in a gym locker room with mirrors",
    "on a basketball court outdoors in sunlight",
    "in a cozy bedroom with soft morning sunlight streaming in",
    "in a stylish hotel bathroom with marble walls",
    "at a resort poolside with blue water behind her",
    "in a sunlit modern apartment living room",
    "outdoors in a park with dappled golden hour light",
    "in a hotel room balcony overlooking the ocean",
    "in a dressing room with ring lights",
    "in a luxury spa changing room",
    "on a sandy beach at sunset",
    "inside a quiet art gallery with white walls",
    "in a neon-lit city alley after rain",
    "at a sidewalk cafe with warm afternoon light",
    "in a library aisle with tall wooden shelves",
    "inside a minimalist photography studio",
    "in a greenhouse filled with tropical plants",
    "at a train station platform during golden hour",
    "in a vintage record store with colorful album covers",
    "beside a hotel lobby window with city reflections",
    "on a quiet residential street lined with trees",
    "inside a bright kitchen with marble counters",
    "in a dance rehearsal room with wooden floors",
    "near a lakeside pier with soft morning fog",
    "in a modern office lounge with glass walls",
    "on a rooftop garden with potted plants",
    "inside a boutique clothing shop with soft lighting",
    "in a museum corridor with dramatic overhead light",
    "at a night market with colorful lanterns",
    "beside a pool cabana with striped shadows",
    "inside a cozy book cafe with warm lamps",
]

AVATAR_PHOTO_STYLE_VARIANTS = [
    "candid lifestyle portrait photo",
    "editorial fashion portrait photo",
    "environmental portrait photo",
    "street-style portrait photo",
    "cinematic character portrait photo",
    "natural light portrait photo",
    "magazine-style portrait photo",
    "travel diary portrait photo",
    "documentary-style portrait photo",
    "polished studio portrait photo",
    "soft glamour portrait photo",
    "urban fashion lookbook photo",
    "relaxed social media portrait photo",
    "high-end dating profile portrait photo",
    "film still style portrait photo",
    "warm indoor lifestyle portrait photo",
    "outdoor golden-hour portrait photo",
    "minimalist clean portrait photo",
    "moody cinematic portrait photo",
    "playful candid portrait photo",
]

IMAGE_POSE_VARIANTS = [
    "standing in a relaxed contrapposto pose",
    "leaning lightly against the wall",
    "sitting at a three-quarter angle",
    "turning over one shoulder toward the camera",
    "kneeling on one knee with natural posture",
    "reclining diagonally across the frame",
    "walking slowly toward the camera",
    "standing with one hand at her waist",
    "sitting on the edge of a chair with crossed legs",
    "standing in profile with her face turned toward camera",
    "crouching playfully with balanced posture",
    "stepping out from a doorway mid-stride",
    "resting on one hip with asymmetrical shoulders",
    "perched on a windowsill at a diagonal angle",
    "standing with arms loosely folded below the chest",
    "sitting sideways with one knee raised",
    "standing with one shoulder closer to the lens",
    "walking across the frame with a natural stride",
    "sitting relaxed on a sofa arm",
    "standing beside a window with one knee bent",
    "leaning forward slightly with balanced posture",
    "standing centered with relaxed open shoulders",
    "sitting on stairs with an angled posture",
    "turning mid-step with natural movement",
    "standing near a doorway with soft posture",
    "sitting cross-legged in a relaxed pose",
    "leaning on a railing at a diagonal angle",
    "standing with weight shifted to one leg",
    "resting against a countertop with casual posture",
    "sitting at a cafe table in three-quarter view",
    "standing in a graceful S-curve pose",
    "looking over her shoulder while standing",
]

IMAGE_ACTION_VARIANTS = [
    "adjusting her hair naturally",
    "resting one hand on a nearby surface",
    "glancing aside before looking back",
    "stretching with relaxed shoulders",
    "holding a soft confident expression",
    "shifting her weight mid-step",
    "brushing hair away from her face",
    "posing with subtle hand movement",
    "tilting her chin while making direct eye contact",
    "lifting one hand as if greeting the viewer",
    "turning her shoulders as if caught candidly",
    "lightly touching her necklace",
    "looking back while taking a step forward",
    "settling into the seat with relaxed hands",
    "placing one hand behind her head",
    "reaching toward the camera in a candid moment",
    "holding a coffee cup near her waist",
    "turning a page in a book",
    "checking the light from a nearby window",
    "buttoning a jacket casually",
    "resting both hands loosely at her sides",
    "walking with one hand brushing her hair",
    "pausing as if listening to someone off camera",
    "smiling subtly with relaxed shoulders",
    "looking down briefly before meeting the camera",
    "holding sunglasses loosely in one hand",
    "adjusting the cuff of her sleeve",
    "touching the edge of a nearby chair",
    "turning slightly as if just called by name",
    "holding a small handbag at her side",
    "resting her elbows lightly on a table",
    "stepping forward with a confident expression",
    "looking out a window in a quiet moment",
    "laughing softly with natural expression",
    "standing still with composed eye contact",
    "tucking hair behind one ear",
]

IMAGE_CAMERA_VARIANTS = [
    "waist-level camera angle",
    "slight high-angle portrait framing",
    "low-angle full-body framing",
    "three-quarter portrait composition",
    "close portrait with shallow depth of field",
    "wide environmental portrait framing",
    "35mm candid photography style",
    "50mm editorial portrait lens",
    "full-body vertical portrait with generous negative space",
    "dynamic diagonal composition",
    "over-the-shoulder portrait framing",
    "low side-angle fashion editorial framing",
    "mirror portrait perspective without a phone",
    "intimate medium close-up portrait crop",
    "floor-level upward perspective",
    "cinematic off-center composition",
    "horizontal waist-up environmental framing",
    "full-length editorial framing",
    "medium portrait with background context",
    "wide-angle lifestyle composition",
    "portrait lens with soft background compression",
    "candid side-profile composition",
    "centered clean catalogue framing",
    "asymmetric rule-of-thirds composition",
    "overhead soft-angle portrait framing",
    "long-lens street portrait perspective",
    "shoulder-level natural camera height",
    "low three-quarter fashion angle",
    "cinematic hallway depth perspective",
    "window-lit side angle portrait",
    "seated medium-wide composition",
    "walking shot with slight motion energy",
]

IMAGE_QUALITY_VARIANTS = [
    "soft cinematic lighting, natural skin texture",
    "crisp studio detail, balanced contrast",
    "warm golden-hour highlights, realistic shadows",
    "moody low-key lighting, high dynamic range",
    "clean editorial color grading, fine detail",
    "natural window light, subtle film grain",
    "high-end portrait photography, sharp focus",
    "ambient room lighting, realistic color tones",
    "subtle cinematic contrast, natural highlights",
    "soft overcast light, realistic skin detail",
    "editorial color palette, clean shadows",
    "bright airy lighting, crisp facial detail",
    "film-like grain, balanced warm tones",
    "studio-soft key light, smooth background falloff",
    "rich natural contrast, detailed fabric texture",
    "muted luxury color grading, accurate anatomy",
    "clean commercial photography, polished detail",
    "realistic lens rendering, depth and separation",
]

MATURE_BACKGROUND_VARIANTS = [
    "in a modern bedroom with linen sheets",
    "beside a tall window with city lights behind her",
    "in a minimalist studio with soft curtains",
    "on a hotel suite sofa with warm lamps",
    "near a bathroom vanity with marble reflections",
    "on a balcony with night skyline bokeh",
    "in a private lounge with cinematic shadows",
    "against a textured wall with soft side light",
    "in a candlelit hotel suite with warm practical lights",
    "on a plush chaise lounge with deep shadows",
    "in a private dressing room with silk curtains",
    "beside a freestanding bathtub with soft steam",
    "on a dark velvet sofa under a single key light",
    "in a loft bedroom with rain on the window",
    "near a low bed with dramatic side lighting",
    "in a moody studio with colored rim light",
]

VIDEO_MOTION_VARIANTS = [
    "slow head turn and subtle eye contact",
    "gentle breathing motion with a relaxed posture shift",
    "small shoulder movement and soft hand gesture",
    "slow hair movement with a calm gaze",
    "subtle weight shift and natural blinking",
    "smooth torso movement with steady expression",
    "slow camera-aware pose transition",
    "minimal cinematic movement, no abrupt motion",
    "slowly sits down and leans forward with controlled motion",
    "turns from profile to face camera while one hand moves through her hair",
    "takes two small steps toward camera with natural hip and shoulder movement",
    "raises one hand toward the lens, then lowers it with a soft smile",
    "shifts from seated pose to standing pose in one smooth transition",
    "arches her back slightly, then relaxes into a new pose",
    "rolls one shoulder and turns her torso toward the camera",
    "slowly reclines and changes hand placement with steady eye contact",
]

VIDEO_CAMERA_VARIANTS = [
    "slow push-in camera movement",
    "locked-off portrait camera with shallow depth of field",
    "gentle handheld portrait framing",
    "slow side-to-front camera drift",
    "medium shot with stable framing",
    "three-quarter portrait video composition",
    "smooth vertical pan from full body to face",
    "slow orbit from left side to frontal portrait",
    "gentle dolly-out revealing more of the room",
    "handheld close portrait with controlled parallax",
    "low-angle camera rising into eye-level framing",
    "slow rack focus from foreground to her face",
]

VIDEO_QUALITY_VARIANTS = [
    "cinematic lighting, clean temporal consistency",
    "high detail, stable anatomy, natural motion",
    "soft filmic color grading, smooth frames",
    "realistic skin texture, stable facial identity",
    "high quality video, coherent motion, no flicker",
    "balanced contrast, smooth motion, sharp subject focus",
]

_SPORT_KEYWORDS = {"athlete", "fitness", "dancer", "trainer", "basketball", "swimmer", "yoga", "sports", "gymnast"}
_LUXURY_KEYWORDS = {"model", "actress", "celebrity", "influencer", "escort", "hostess", "entertainer"}


class CharacterFactory:
    _instance = None

    def __init__(self):
        self._llm_service = None
        self._media_service = None

    @classmethod
    def get_instance(cls) -> "CharacterFactory":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_llm_service(self):
        if self._llm_service is None:
            from app.services.llm_service import LLMService
            self._llm_service = LLMService.get_instance()
        return self._llm_service

    def _get_media_service(self):
        if self._media_service is None:
            from app.services.media_service import MediaService
            self._media_service = MediaService.get_instance()
        return self._media_service

    async def _get_novita_image_provider(self):
        media = self._get_media_service()
        provider = media.get_image_provider("novita")
        if provider is None:
            await media.refresh_providers()
            provider = media.get_image_provider("novita")
        return provider

    async def _get_txt2img_provider(self):
        media = self._get_media_service()
        provider = media.get_image_provider("z_image_turbo_lora")
        if provider is None:
            await media.refresh_providers()
            provider = media.get_image_provider("z_image_turbo_lora")
        if provider is None:
            provider = media.get_image_provider("novita")
        return provider

    def _get_novita_video_provider(self):
        return self._get_media_service().get_video_provider("novita")

    async def _get_active_elevenlabs_voice_ids(self) -> list[str]:
        rows = await db.execute(
            """
            SELECT provider_voice_id
            FROM voices
            WHERE provider = 'elevenlabs' AND is_active = 1
            """,
            fetch_all=True,
        )
        voice_ids = [str(row.get("provider_voice_id") or "").strip() for row in (rows or [])]
        return [voice_id for voice_id in voice_ids if voice_id]

    @staticmethod
    def _sample_from_pool(pool: list[str]) -> str:
        if not pool:
            return ""
        return pool[random.randrange(len(pool))]

    @staticmethod
    def _random_seed() -> int:
        return random.randint(1, 2_147_483_647)

    @classmethod
    def _sample_image_prompt_variation(
        cls, *, include_background: bool = False
    ) -> dict[str, str]:
        variation = {
            "style": cls._sample_from_pool(AVATAR_PHOTO_STYLE_VARIANTS),
            "pose": cls._sample_from_pool(IMAGE_POSE_VARIANTS),
            "action": cls._sample_from_pool(IMAGE_ACTION_VARIANTS),
            "camera": cls._sample_from_pool(IMAGE_CAMERA_VARIANTS),
            "quality": cls._sample_from_pool(IMAGE_QUALITY_VARIANTS),
        }
        if include_background:
            variation["background"] = cls._sample_from_pool(MATURE_BACKGROUND_VARIANTS)
        return variation

    @classmethod
    def _sample_video_prompt_variation(cls) -> dict[str, str]:
        return {
            "motion": cls._sample_from_pool(VIDEO_MOTION_VARIANTS),
            "action": cls._sample_from_pool(IMAGE_ACTION_VARIANTS),
            "camera": cls._sample_from_pool(VIDEO_CAMERA_VARIANTS),
            "quality": cls._sample_from_pool(VIDEO_QUALITY_VARIANTS),
            "background": cls._sample_from_pool(MATURE_BACKGROUND_VARIANTS),
        }

    @staticmethod
    def _pick_unique(pool: list[str], index: int) -> str:
        if not pool:
            return ""
        offset = random.randrange(len(pool))
        return pool[(index + offset) % len(pool)]

    @classmethod
    def _build_visual_brief(cls, index: int = 0, count: int = 1) -> dict[str, object]:
        """Build one visual brief with batch-spread choices and explicit seeds."""
        return {
            "batch_index": index,
            "batch_count": count,
            "avatar": {
                "style": cls._pick_unique(AVATAR_PHOTO_STYLE_VARIANTS, index),
                "background": cls._pick_unique(AVATAR_BACKGROUND_SCENES, index),
                "pose": cls._pick_unique(IMAGE_POSE_VARIANTS, index),
                "action": cls._pick_unique(IMAGE_ACTION_VARIANTS, index * 2),
                "camera": cls._pick_unique(IMAGE_CAMERA_VARIANTS, index * 3),
                "quality": cls._pick_unique(IMAGE_QUALITY_VARIANTS, index),
                "seed": cls._random_seed(),
            },
            "mature": {
                "pose": cls._pick_unique(IMAGE_POSE_VARIANTS, index + count + 3),
                "action": cls._pick_unique(IMAGE_ACTION_VARIANTS, index * 2 + count + 5),
                "camera": cls._pick_unique(IMAGE_CAMERA_VARIANTS, index * 3 + count + 7),
                "background": cls._pick_unique(MATURE_BACKGROUND_VARIANTS, index),
                "quality": cls._pick_unique(IMAGE_QUALITY_VARIANTS, index + count),
                "seed": cls._random_seed(),
            },
            "video": {
                "motion": cls._pick_unique(VIDEO_MOTION_VARIANTS, index),
                "action": cls._pick_unique(IMAGE_ACTION_VARIANTS, index * 2 + 1),
                "camera": cls._pick_unique(VIDEO_CAMERA_VARIANTS, index * 3 + 2),
                "background": cls._pick_unique(MATURE_BACKGROUND_VARIANTS, index + count),
                "quality": cls._pick_unique(VIDEO_QUALITY_VARIANTS, index),
                "seed": cls._random_seed(),
            },
        }

    @classmethod
    def _assign_batch_visual_briefs(cls, profiles: list[dict]) -> None:
        count = len(profiles)
        avatar_styles = random.sample(AVATAR_PHOTO_STYLE_VARIANTS, len(AVATAR_PHOTO_STYLE_VARIANTS))
        avatar_backgrounds = random.sample(AVATAR_BACKGROUND_SCENES, len(AVATAR_BACKGROUND_SCENES))
        avatar_poses = random.sample(IMAGE_POSE_VARIANTS, len(IMAGE_POSE_VARIANTS))
        avatar_actions = random.sample(IMAGE_ACTION_VARIANTS, len(IMAGE_ACTION_VARIANTS))
        avatar_cameras = random.sample(IMAGE_CAMERA_VARIANTS, len(IMAGE_CAMERA_VARIANTS))
        mature_poses = random.sample(IMAGE_POSE_VARIANTS, len(IMAGE_POSE_VARIANTS))
        mature_actions = random.sample(IMAGE_ACTION_VARIANTS, len(IMAGE_ACTION_VARIANTS))
        mature_cameras = random.sample(IMAGE_CAMERA_VARIANTS, len(IMAGE_CAMERA_VARIANTS))
        mature_backgrounds = random.sample(MATURE_BACKGROUND_VARIANTS, len(MATURE_BACKGROUND_VARIANTS))
        video_motions = random.sample(VIDEO_MOTION_VARIANTS, len(VIDEO_MOTION_VARIANTS))
        video_actions = random.sample(IMAGE_ACTION_VARIANTS, len(IMAGE_ACTION_VARIANTS))
        video_cameras = random.sample(VIDEO_CAMERA_VARIANTS, len(VIDEO_CAMERA_VARIANTS))
        video_backgrounds = random.sample(MATURE_BACKGROUND_VARIANTS, len(MATURE_BACKGROUND_VARIANTS))

        for index, profile in enumerate(profiles):
            profile["_visual_brief"] = {
                "batch_index": index,
                "batch_count": count,
                "avatar": {
                    "style": avatar_styles[index % len(avatar_styles)],
                    "background": avatar_backgrounds[index % len(avatar_backgrounds)],
                    "pose": avatar_poses[index % len(avatar_poses)],
                    "action": avatar_actions[index % len(avatar_actions)],
                    "camera": avatar_cameras[index % len(avatar_cameras)],
                    "quality": cls._pick_unique(IMAGE_QUALITY_VARIANTS, index),
                    "seed": cls._random_seed(),
                },
                "mature": {
                    "pose": mature_poses[index % len(mature_poses)],
                    "action": mature_actions[index % len(mature_actions)],
                    "camera": mature_cameras[index % len(mature_cameras)],
                    "background": mature_backgrounds[index % len(mature_backgrounds)],
                    "quality": cls._pick_unique(IMAGE_QUALITY_VARIANTS, index + count),
                    "seed": cls._random_seed(),
                },
                "video": {
                    "motion": video_motions[index % len(video_motions)],
                    "action": video_actions[index % len(video_actions)],
                    "camera": video_cameras[index % len(video_cameras)],
                    "background": video_backgrounds[index % len(video_backgrounds)],
                    "quality": cls._pick_unique(VIDEO_QUALITY_VARIANTS, index),
                    "seed": cls._random_seed(),
                },
            }

    def _get_random_background(self, profile: dict) -> str:
        occupation = profile.get("occupation", "").lower()
        if any(k in occupation for k in _SPORT_KEYWORDS):
            pool = [
                "on a basketball court outdoors in sunlight",
                "in a gym locker room with mirrors",
                "at a resort poolside with blue water behind her",
            ]
        elif any(k in occupation for k in _LUXURY_KEYWORDS):
            pool = [
                "in a luxury hotel room, sitting on the bed",
                "on a rooftop terrace with city skyline at golden hour",
                "in a stylish hotel bathroom with marble walls, taking a mirror selfie",
                "in a hotel room balcony overlooking the ocean",
            ]
        else:
            pool = AVATAR_BACKGROUND_SCENES
        return random.choice(pool)

    async def _get_active_loras_from_db(self, applies_to: str = "img2img") -> list[dict]:
        try:
            rows = await db.execute(
                "SELECT id, name, model_name, strength, trigger_word, description, "
                "example_prompt, example_negative_prompt, prompt_template_mode "
                "FROM lora_presets "
                "WHERE is_active = 1 AND (applies_to = ? OR applies_to = 'all') AND provider = 'novita'",
                (applies_to,),
                fetch_all=True,
            )
            return [dict(r) for r in (rows or [])]
        except Exception as e:
            logger.warning(f"Failed to load LoRAs from DB: {e}")
            return []

    async def _select_lora_from_db(self, applies_to: str, context: str = "") -> list[dict]:
        """Use LLM tool-calling to pick the best LoRA; random fallback on failure."""
        from app.services.lora_selector_service import select_lora

        chosen = await select_lora(context=context, applies_to=applies_to)
        if chosen:
            logger.info(f"[LoRA] Selected '{chosen['model_name']}' for {applies_to}")
            return [chosen]
        return []

    @staticmethod
    def _pick_random_template(raw: str) -> str:
        """Pick one template from a multiline/pipe-separated prompt template field."""
        text = (raw or "").strip()
        if not text:
            return ""

        # Preferred format: one template per line. Also support "||" as delimiter.
        candidates = [
            part.strip()
            for line in text.splitlines()
            for part in line.split("||")
            if part.strip()
        ]
        if not candidates:
            return ""
        return random.choice(candidates)

    @staticmethod
    def _compose_prompt_with_lora(base_prompt: str, lora: Optional[dict]) -> str:
        if not lora:
            return base_prompt
        mode = (lora.get("prompt_template_mode") or "append_trigger").strip().lower()
        example_prompt = CharacterFactory._pick_random_template(lora.get("example_prompt") or "")
        trigger_word = (lora.get("trigger_word") or "").strip()

        if mode == "use_example" and example_prompt:
            return f"{example_prompt}, {base_prompt}"
        if trigger_word:
            return f"{trigger_word}, {base_prompt}"
        return base_prompt

    @staticmethod
    def _compose_negative_with_lora(base_negative: str, lora: Optional[dict]) -> str:
        if not lora:
            return base_negative
        mode = (lora.get("prompt_template_mode") or "append_trigger").strip().lower()
        example_negative = CharacterFactory._pick_random_template(
            lora.get("example_negative_prompt") or ""
        )
        if mode == "use_example" and example_negative:
            return f"{example_negative}, {base_negative}"
        return base_negative

    async def _generate_mature_with_ipadapter(
        self,
        novita,
        *,
        name: str,
        age: int,
        ethnicity_style: dict,
        personality: str,
        sfw_avatar_url: str,
        loras: list[dict],
        visual_brief: Optional[dict[str, object]] = None,
    ) -> Optional[str]:
        """Generate Mature image using IPAdapter (character consistency) + DB LoRAs."""
        from app.services.media import IPAdapterConfig, LoRAConfig as MediaLoRAConfig

        try:
            face_base64 = await novita._download_image_base64(sfw_avatar_url)
        except Exception as e:
            logger.warning(f"IPAdapter download failed for {name}: {e}")
            return None

        mature_brief = (visual_brief or {}).get("mature", {}) if visual_brief else {}
        fallback_variation = self._sample_image_prompt_variation(include_background=True)
        image_variation = {
            "pose": mature_brief.get("pose") or fallback_variation["pose"],
            "action": mature_brief.get("action") or fallback_variation["action"],
            "camera": mature_brief.get("camera") or fallback_variation["camera"],
            "quality": mature_brief.get("quality") or fallback_variation["quality"],
            "background": mature_brief.get("background") or fallback_variation["background"],
        }
        seed = int(mature_brief.get("seed") or self._random_seed())
        base_prompt = (
            f"nude full body photo of a beautiful {age}-year-old {ethnicity_style['avatar']}, "
            f"{personality} personality, completely naked, perfect body, "
            f"{image_variation['pose']}, {image_variation['action']}, "
            f"{image_variation['background']}, {image_variation['camera']}, "
            f"{image_variation['quality']}, detailed skin, photorealistic, masterpiece photography, "
            "new pose and new composition different from the reference image, "
            "lightrays, very detailed skin, 8k focus stacking, looking at camera"
        )
        base_negative = (
            "low quality, bad anatomy, blur, blurry, ugly, wrong proportions, "
            "watermark, bad eyes, bad hands, bad arms, deformed, disfigured, "
            "extra fingers, mutated hands, poorly drawn hands, poorly drawn face, "
            "mutation, gross proportions, malformed limbs, missing arms, missing legs, "
            "extra arms, extra legs, fused fingers, too many fingers, long neck, "
            "clothing, clothes, dressed"
        )
        selected_lora = dict(loras[0]) if loras else None
        if selected_lora:
            mode = (selected_lora.get("prompt_template_mode") or "append_trigger").strip().lower()
            trigger_word = (selected_lora.get("trigger_word") or "").strip()
            if mode == "append_trigger" and trigger_word and "," in trigger_word:
                trigger_parts = [part.strip() for part in trigger_word.split(",") if part.strip()]
                if trigger_parts:
                    selected_lora["trigger_word"] = random.choice(trigger_parts)
            elif mode == "use_example":
                example_prompt = self._pick_random_template(
                    selected_lora.get("example_prompt") or ""
                )
                if example_prompt:
                    trigger = selected_lora.get("trigger_word", "").strip()
                    if trigger and trigger.lower() not in example_prompt.lower():
                        example_prompt = f"{trigger}, {example_prompt}"
                    selected_lora["example_prompt"] = example_prompt
        mature_prompt = self._compose_prompt_with_lora(base_prompt, selected_lora)
        mature_negative = self._compose_negative_with_lora(base_negative, selected_lora)

        lora_configs = [
            MediaLoRAConfig(model_name=l["model_name"], strength=l["strength"])
            for l in loras
        ] or None
        ip_adapters = [IPAdapterConfig(
            image_base64=face_base64,
            strength=0.45,
            model_name="ip-adapter_sdxl.bin",
        )]

        try:
            logger.info(f"[Step 2] Novita Mature IPAdapter for {name}...")
            task_id = await novita.img2img_async(
                init_image_url=sfw_avatar_url,
                prompt=mature_prompt,
                negative_prompt=mature_negative,
                model=novita.DEFAULT_MODEL,
                strength=0.45,
                width=768,
                height=1024,
                steps=28,
                guidance_scale=6.0,
                seed=seed,
                loras=lora_configs,
                ip_adapters=ip_adapters,
            )
            result = await novita.wait_for_task(task_id)
            if result.image_url:
                return await storage_service.upload_from_url(
                    result.image_url, folder="characters/mature"
                )
            logger.warning(f"Mature IPAdapter completed without image for {name}")
        except Exception as e:
            logger.error(f"Mature IPAdapter generation failed for {name}: {e}")

        return None

    async def _generate_and_save_video(
        self, character_id: str, profile: dict, image_url: str
    ) -> None:
        """Background task: generate Mature video and update character in DB."""
        try:
            video_url = await self._generate_character_video(profile, image_url)
            if video_url:
                from app.models.character import CharacterUpdate
                await character_service.update_character(
                    character_id, CharacterUpdate(mature_video_url=video_url)
                )
                logger.info(f"Mature video saved for character {character_id}")
        except Exception as e:
            logger.error(f"Background video generation failed for {character_id}: {e}")

    async def _generate_mature_variant(
        self,
        novita,
        *,
        name: str,
        prompt: str,
        base_image_urls: list[Optional[str]],
        negative_prompt: str,
        width: int,
        height: int,
        log_label: str,
    ) -> Optional[str]:
        """Generate an Mature image from any available source image.

        Prefer img2img when a SFW image exists, but fall back to txt2img when
        all source images are unavailable or unusable.
        """

        async def store_image(image_url: str, folder: str) -> str:
            try:
                return await storage_service.upload_from_url(image_url, folder=folder)
            except Exception as e:
                logger.warning(f"R2 upload failed for {log_label}: {e}")
                return image_url

        for source_url in [url for url in base_image_urls if url]:
            try:
                logger.info(f"[Step 2] Novita img2img {log_label} for {name}...")
                task_id = await novita.img2img_async(
                    init_image_url=source_url,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    strength=0.45,
                    width=width,
                    height=height,
                    steps=28,
                    guidance_scale=6.0,
                )
                result = await novita.wait_for_task(task_id)
                if result.image_url:
                    return await store_image(result.image_url, "characters/mature")
                logger.warning(
                    f"{log_label} img2img completed without image for {name} using {source_url}"
                )
            except Exception as e:
                logger.warning(
                    f"{log_label} img2img fallback failed for {name} using {source_url}: {e}"
                )

        try:
            logger.info(f"[Step 2] Novita txt2img {log_label} fallback for {name}...")
            task_id = await novita.txt2img_async(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=28,
                guidance_scale=6.0,
            )
            result = await novita.wait_for_task(task_id)
            if result.image_url:
                return await store_image(result.image_url, "characters/mature")
            logger.warning(f"{log_label} txt2img completed without image for {name}")
        except Exception as e:
            logger.error(f"Novita direct {log_label} generation failed for {name}: {e}")

        return None

    async def generate_batch(
        self,
        count: int,
        top_category: str = "girls",
        ethnicity: Optional[str] = None,
        nationality: Optional[str] = None,
        occupation: Optional[str] = None,
        personality_preferences: Optional[list[str]] = None,
        age_min: int = 20,
        age_max: int = 30,
        generate_images: bool = True,
        generate_video: bool = False,
        optimize_seo: bool = True,
        trend_context: Optional[dict] = None,
    ) -> list[dict]:
        logger.info(f"Starting batch generation of {count} characters (ethnicity={ethnicity}, nationality={nationality}, occupation={occupation})")

        profiles = await self._generate_ai_profiles(
            count=count,
            top_category=top_category,
            ethnicity=ethnicity,
            nationality=nationality,
            occupation=occupation,
            personality_preferences=personality_preferences,
            age_min=age_min,
            age_max=age_max,
            trend_context=trend_context,
        )
        self._assign_batch_visual_briefs(profiles)

        voice_ids = await self._get_active_elevenlabs_voice_ids()
        if not voice_ids:
            try:
                from app.services.voice_management_service import voice_management_service
                await voice_management_service.seed_curated_elevenlabs_voices()
                voice_ids = await self._get_active_elevenlabs_voice_ids()
            except Exception as e:
                logger.warning(f"Failed to seed curated voices for batch generation: {e}")

        created_characters = []

        for i, profile in enumerate(profiles):
            try:
                logger.info(f"Processing character {i+1}/{count}: {profile.get('name')}")

                if generate_images:
                    images = await self._generate_character_images(profile)
                    profile.update(images)

                if optimize_seo:
                    seo_data = await self._generate_seo_content(profile)
                    profile.update(seo_data)

                if voice_ids and not profile.get("voice_id"):
                    profile["voice_id"] = random.choice(voice_ids)

                character_create = CharacterCreate(
                    **{k: v for k, v in profile.items() if not k.startswith("_")}
                )
                character = await character_service.create_character(character_create)

                # Launch Mature video generation as a background task after character is saved
                character_id = character.get("id")
                if generate_video and character_id:
                    video_source = (
                        profile.get("mature_cover_url")
                        or profile.get("mature_image_url")
                        or profile.get("avatar_url")
                    )
                    if video_source:
                        asyncio.create_task(
                            self._generate_and_save_video(character_id, profile, video_source)
                        )

                created_characters.append(character)
                logger.info(f"Created character: {character.get('id')} - {character.get('name')}")

            except Exception as e:
                logger.error(f"Failed to create character {profile.get('name')}: {e}")
                continue

        logger.info(f"Batch generation complete: {len(created_characters)}/{count} characters created")
        return created_characters

    async def generate_from_template(
        self,
        template_id: str,
        variations: int = 1,
        ethnicity: Optional[str] = None,
        nationality: Optional[str] = None,
        generate_images: bool = True,
        generate_video: bool = False,
        optimize_seo: bool = True,
        trend_context: Optional[dict] = None,
    ) -> list[dict]:
        template = OCCUPATION_TEMPLATES.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        logger.info(f"Generating {variations} variations from template: {template_id}")

        created_characters = []

        for i in range(variations):
            try:
                profile = await self._generate_from_template(
                    template=template,
                    ethnicity=ethnicity,
                    nationality=nationality,
                    trend_context=trend_context,
                )

                profile["template_id"] = template_id
                profile["generation_mode"] = "template"
                profile["_visual_brief"] = self._build_visual_brief(index=i, count=variations)

                if generate_images:
                    images = await self._generate_character_images(profile)
                    profile.update(images)

                if optimize_seo:
                    seo_data = await self._generate_seo_content(profile)
                    profile.update(seo_data)

                character_create = CharacterCreate(
                    **{k: v for k, v in profile.items() if not k.startswith("_")}
                )
                character = await character_service.create_character(character_create)

                character_id = character.get("id")
                if generate_video and character_id:
                    video_source = (
                        profile.get("mature_cover_url")
                        or profile.get("mature_image_url")
                        or profile.get("avatar_url")
                    )
                    if video_source:
                        asyncio.create_task(
                            self._generate_and_save_video(character_id, profile, video_source)
                        )

                created_characters.append(character)

            except Exception as e:
                logger.error(f"Failed to create character from template: {e}")
                continue

        return created_characters

    async def generate_single_character(
        self,
        name: Optional[str] = None,
        top_category: str = "girls",
        ethnicity: Optional[str] = None,
        nationality: Optional[str] = None,
        occupation: Optional[str] = None,
        age_min: int = 20,
        age_max: int = 30,
        generate_images: bool = True,
        generate_video: bool = False,
        optimize_seo: bool = True,
        trend_context: Optional[dict] = None,
    ) -> dict:
        profile = await self._generate_ai_profiles(
            count=1,
            top_category=top_category,
            ethnicity=ethnicity,
            nationality=nationality,
            occupation=occupation,
            age_min=age_min,
            age_max=age_max,
            trend_context=trend_context,
        )

        if name:
            profile[0]["name"] = name
            profile[0]["first_name"] = name.split()[0] if " " in name else name
        profile[0]["_visual_brief"] = self._build_visual_brief(index=0, count=1)

        if generate_images:
            images = await self._generate_character_images(profile[0])
            profile[0].update(images)

        if optimize_seo:
            seo_data = await self._generate_seo_content(profile[0])
            profile[0].update(seo_data)

        character_create = CharacterCreate(
            **{k: v for k, v in profile[0].items() if not k.startswith("_")}
        )
        character = await character_service.create_character(character_create)

        if generate_video:
            character_id = character.get("id")
            video_source = (
                profile[0].get("mature_cover_url")
                or profile[0].get("mature_image_url")
                or profile[0].get("avatar_url")
            )
            if character_id and video_source:
                asyncio.create_task(
                    self._generate_and_save_video(character_id, profile[0], video_source)
                )

        return character

    async def generate_batch_trend_aware(
        self,
        count: int,
        top_category: str = "girls",
        generate_images: bool = True,
        generate_video: bool = False,
        optimize_seo: bool = True,
    ) -> list[dict]:
        try:
            from app.services.trend_service import trend_service
            trend_context = await trend_service.get_trend_weighted_attributes()
        except Exception as e:
            logger.warning(f"Failed to get trend context, using defaults: {e}")
            trend_context = None

        return await self.generate_batch(
            count=count,
            top_category=top_category,
            generate_images=generate_images,
            generate_video=generate_video,
            optimize_seo=optimize_seo,
            trend_context=trend_context,
        )

    async def regenerate_images(self, character_id: str) -> dict:
        character = await character_service.get_character_by_id(character_id)
        if not character:
            raise ValueError(f"Character not found: {character_id}")

        images = await self._generate_character_images(character)

        if not images.get("avatar_url"):
            raise RuntimeError(
                "Avatar image generation failed - no image URL returned. "
                "Check NOVITA_API_KEY is set and the Novita API is reachable."
            )

        update_data = {
            k: v for k, v in images.items()
            if k in {"avatar_url", "cover_url", "avatar_card_url", "profile_image_url",
                     "mature_image_url", "mature_cover_url"}
        }
        # cover and mature_cover are always aliased to their respective main images
        if "avatar_url" in update_data:
            update_data["cover_url"] = update_data["avatar_url"]
        if "mature_image_url" in update_data:
            update_data["mature_cover_url"] = update_data["mature_image_url"]

        from app.models.character import CharacterUpdate
        return await character_service.update_character(character_id, CharacterUpdate(**update_data))

    async def regenerate_video(self, character_id: str) -> dict:
        character = await character_service.get_character_by_id(character_id)
        if not character:
            raise ValueError(f"Character not found: {character_id}")

        mature_image = character.get("mature_image_url") or character.get("avatar_url")
        if not mature_image:
            raise ValueError(f"Character {character_id} has no image to animate")

        video_url = await self._generate_character_video(character, mature_image)

        if video_url:
            from app.models.character import CharacterUpdate
            updated = await character_service.update_character(
                character_id,
                CharacterUpdate(mature_video_url=video_url)
            )
            return updated

        raise ValueError("Video generation failed")

    async def _generate_ai_profiles(
        self,
        count: int,
        top_category: str = "girls",
        ethnicity: Optional[str] = None,
        nationality: Optional[str] = None,
        occupation: Optional[str] = None,
        personality_preferences: Optional[list[str]] = None,
        age_min: int = 20,
        age_max: int = 30,
        trend_context: Optional[dict] = None,
    ) -> list[dict]:
        profiles = []

        try:
            performance_weights = await self._get_performance_weights()
        except Exception:
            performance_weights = {}

        for _ in range(count):
            selected_ethnicity = ethnicity or await self._weighted_choice(
                "top_ethnicities", list(ETHNICITY_IMAGE_STYLES.keys()), performance_weights
            )
            selected_nationality = nationality or await self._weighted_choice(
                "top_nationalities", list(NATIONALITY_CONFIGS.keys()), performance_weights
            )
            selected_occupation = occupation or await self._weighted_choice(
                "top_occupations", list(OCCUPATION_TEMPLATES.keys()), performance_weights
            )

            occupation_hint = OCCUPATION_TEMPLATES.get(selected_occupation, {}).get("name", selected_occupation)
            nationality_hint = selected_nationality.upper()

            trend_hints = ""
            if trend_context:
                suggestions = []
                if trend_context.get("suggested_occupations"):
                    suggestions.append(f"Popular occupation types: {', '.join(trend_context['suggested_occupations'][:5])}")
                if trend_context.get("suggested_personality_tags"):
                    suggestions.append(f"Trending personality traits: {', '.join(trend_context['suggested_personality_tags'][:5])}")
                if trend_context.get("suggested_styles"):
                    suggestions.append(f"Popular visual styles: {', '.join(trend_context['suggested_styles'])}")
                if trend_context.get("suggested_scenarios"):
                    suggestions.append(f"Trending scenarios: {', '.join(trend_context['suggested_scenarios'])}")
                if suggestions:
                    trend_hints = "Current market trends:\n" + "\n".join(f"- {s}" for s in suggestions)

            if personality_preferences:
                trend_hints += f"\n\nUser-specified personality preferences: {', '.join(personality_preferences)}"

            try:
                profile = await self._generate_single_profile_with_llm(
                    age_min=age_min,
                    age_max=age_max,
                    occupation_hint=occupation_hint,
                    nationality_hint=nationality_hint,
                    trend_hints=trend_hints,
                    top_category=top_category,
                    fallback_ethnicity=selected_ethnicity,
                    fallback_nationality=selected_nationality,
                    fallback_occupation=selected_occupation,
                    personality_preferences=personality_preferences,
                )
            except Exception as e:
                logger.warning(f"LLM profile generation failed, using fallback: {e}")
                profile = self._generate_fallback_profile(
                    ethnicity=selected_ethnicity,
                    nationality=selected_nationality,
                    occupation=selected_occupation,
                    age_min=age_min,
                    age_max=age_max,
                    personality_preferences=personality_preferences,
                    top_category=top_category,
                )

            profile["age"] = random.randint(age_min, age_max)
            profiles.append(profile)

        return profiles

    async def _generate_single_profile_with_llm(
        self,
        age_min: int,
        age_max: int,
        occupation_hint: str,
        nationality_hint: str,
        trend_hints: str,
        top_category: str,
        fallback_ethnicity: str,
        fallback_nationality: str,
        fallback_occupation: str,
        personality_preferences: Optional[list[str]] = None,
    ) -> dict:
        llm = self._get_llm_service()

        prompt = LLM_PROFILE_PROMPT.format(
            trend_hints=trend_hints,
            age_min=age_min,
            age_max=age_max,
            occupation_hint=occupation_hint,
            nationality_hint=nationality_hint,
        )

        response = await llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=800,
        )

        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content
            content = content.rsplit("```", 1)[0] if "```" in content else content

        ai_data = json.loads(content)

        name = ai_data.get("name", random.choice(FALLBACK_NAMES))
        personality_tags = ai_data.get("personality_tags", random.sample(FALLBACK_PERSONALITY_POOL, 3))

        if personality_preferences:
            for pref in personality_preferences:
                if pref not in personality_tags:
                    personality_tags.insert(0, pref)
            personality_tags = personality_tags[:4]

        return {
            "name": name,
            "first_name": name.split()[0] if " " in name else name,
            "age": ai_data.get("age", random.randint(age_min, age_max)),
            "gender": "female",
            "ethnicity": ai_data.get("ethnicity", fallback_ethnicity),
            "nationality": ai_data.get("nationality", fallback_nationality),
            "occupation": ai_data.get("occupation", fallback_occupation),
            "top_category": top_category,
            "personality_tags": personality_tags,
            "description": ai_data.get("description", ""),
            "personality_summary": ai_data.get("personality_summary", ""),
            "backstory": ai_data.get("backstory", ""),
            "greeting": ai_data.get("greeting", ""),
            "generation_mode": "batch",
        }

    def _generate_fallback_profile(
        self,
        ethnicity: str,
        nationality: str,
        occupation: str,
        age_min: int,
        age_max: int,
        personality_preferences: Optional[list[str]] = None,
        top_category: str = "girls",
    ) -> dict:
        nationality_config = NATIONALITY_CONFIGS.get(nationality, NATIONALITY_CONFIGS["usa"])
        occupation_config = OCCUPATION_TEMPLATES.get(occupation, OCCUPATION_TEMPLATES["college_student"])

        extended_name_pool = nationality_config.get("name_pool", FALLBACK_NAMES) + FALLBACK_NAMES
        name = random.choice(extended_name_pool)

        age_range = occupation_config.get("age_range", (20, 30))
        age = random.randint(max(age_min, age_range[0]), min(age_max, age_range[1]))

        personality_pool = personality_preferences or occupation_config.get("personality_pool", FALLBACK_PERSONALITY_POOL)
        cultural_traits = nationality_config.get("cultural_traits", [])
        combined_pool = list(set(personality_pool + cultural_traits + FALLBACK_PERSONALITY_POOL))
        personality_tags = random.sample(combined_pool, min(3, len(combined_pool)))

        greeting_templates = occupation_config.get("greeting_templates", ["Hi, I'm {name}!"])
        greeting = random.choice(greeting_templates).format(name=name)

        return {
            "name": name,
            "first_name": name.split()[0] if " " in name else name,
            "age": age,
            "gender": "female",
            "ethnicity": ethnicity,
            "nationality": nationality,
            "occupation": occupation,
            "top_category": top_category,
            "personality_tags": personality_tags,
            "description": f"A {age}-year-old {occupation_config.get('name', occupation)} from {nationality}.",
            "personality_summary": f"{' and '.join(personality_tags[:2])}.",
            "backstory": "",
            "greeting": greeting,
            "generation_mode": "batch",
        }

    async def _generate_from_template(
        self,
        template: dict,
        ethnicity: Optional[str] = None,
        nationality: Optional[str] = None,
        trend_context: Optional[dict] = None,
    ) -> dict:
        selected_ethnicity = ethnicity or random.choice(list(ETHNICITY_IMAGE_STYLES.keys()))
        selected_nationality = nationality or random.choice(list(NATIONALITY_CONFIGS.keys()))

        nationality_config = NATIONALITY_CONFIGS.get(selected_nationality, NATIONALITY_CONFIGS["usa"])

        extended_name_pool = nationality_config.get("name_pool", FALLBACK_NAMES) + FALLBACK_NAMES
        name = random.choice(extended_name_pool)

        age_range = template.get("age_range", (20, 30))
        age = random.randint(age_range[0], age_range[1])

        extended_personality = template.get("personality_pool", FALLBACK_PERSONALITY_POOL) + FALLBACK_PERSONALITY_POOL
        extended_personality = list(set(extended_personality))
        personality_tags = random.sample(extended_personality, min(3, len(extended_personality)))

        if trend_context and trend_context.get("suggested_personality_tags"):
            trending = [t for t in trend_context["suggested_personality_tags"] if t not in personality_tags]
            if trending:
                personality_tags[0] = trending[0]

        greeting_templates = template.get("greeting_templates", ["Hi, I'm {name}!"])
        greeting = random.choice(greeting_templates).format(name=name)

        return {
            "name": name,
            "first_name": name,
            "age": age,
            "gender": "female",
            "ethnicity": selected_ethnicity,
            "nationality": selected_nationality,
            "occupation": template.get("name", "").lower().replace(" ", "_"),
            "top_category": "girls",
            "sub_category": template.get("name", ""),
            "personality_tags": personality_tags,
            "description": template.get("description", ""),
            "greeting": greeting,
            "backstory": f"{' '.join(template.get('background_hints', []))}",
            "generation_mode": "template",
        }

    async def _get_performance_weights(self) -> dict:
        try:
            from app.services.performance_analyzer import performance_analyzer
            result = await performance_analyzer.analyze_top_performers(days=30)
            return result if result else {}
        except Exception:
            return {}

    async def _weighted_choice(
        self,
        category: str,
        options: list[str],
        performance_weights: Optional[dict] = None,
    ) -> str:
        if performance_weights and performance_weights.get(category):
            weight_map = performance_weights[category]
            weights = [weight_map.get(opt, 0.3) for opt in options]
            total = sum(weights)
            if total > 0:
                r = random.uniform(0, total)
                cumulative = 0
                for opt, w in zip(options, weights):
                    cumulative += w
                    if r <= cumulative:
                        return opt

        return random.choice(options)

    async def _generate_character_images(self, profile: dict) -> dict:
        """Three-step image generation:
        1. Novita txt2img -> SFW full-body portrait (avatar = cover)
        2. Novita img2img + IPAdapter + DB LoRAs -> Mature (mature_image = mature_cover)
        3. Novita WAN2.1 img2video -> mature_video (launched as background task)
        """
        images: dict = {}

        name = profile.get("name", "Character")
        age = profile.get("age", 25)
        ethnicity = profile.get("ethnicity", "white")
        occupation = profile.get("occupation", "college_student")

        ethnicity_style = ETHNICITY_IMAGE_STYLES.get(ethnicity, ETHNICITY_IMAGE_STYLES["white"])
        occupation_config = OCCUPATION_TEMPLATES.get(occupation, {})
        personality = " ".join(profile.get("personality_tags", [])[:2])
        occupation_style = occupation_config.get("image_style", "professional woman")
        visual_brief = profile.get("_visual_brief") or self._build_visual_brief()
        avatar_brief = visual_brief.get("avatar", {}) if isinstance(visual_brief, dict) else {}
        background = avatar_brief.get("background") or self._get_random_background(profile)

        sfw_provider = await self._get_txt2img_provider()
        if not sfw_provider:
            logger.warning("Image provider not configured - skipping image generation")
            return images

        sfw_negative = (
            "nude, naked, explicit, adult content, low quality, bad anatomy, blur, blurry, "
            "ugly, watermark, deformed, disfigured"
        )

        # ── Step 1: SFW full-body portrait ───────────────────────────────────
        _sfw_context = f"{name}, {personality} personality, {occupation_style}"
        sfw_loras = await self._select_lora_from_db("txt2img", context=_sfw_context)
        def _pick_one_trigger(raw: str) -> str:
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            return random.choice(parts) if parts else ""

        sfw_trigger = " ".join(_pick_one_trigger(l["trigger_word"]) for l in sfw_loras if l.get("trigger_word"))
        sfw_trigger_part = f"{sfw_trigger}, " if sfw_trigger else ""
        sfw_variation = self._sample_image_prompt_variation()
        avatar_seed = int(avatar_brief.get("seed") or self._random_seed())
        avatar_prompt = (
            f"{avatar_brief.get('style') or sfw_variation['style']} of a {age}-year-old {ethnicity_style['avatar']}, "
            f"{background}, {occupation_style}, {personality} personality, "
            f"{sfw_trigger_part}"
            f"{avatar_brief.get('pose') or sfw_variation['pose']}, "
            f"{avatar_brief.get('action') or sfw_variation['action']}, "
            f"{avatar_brief.get('camera') or sfw_variation['camera']}, "
            f"{avatar_brief.get('quality') or sfw_variation['quality']}, "
            "photorealistic, high quality, 4k, detailed"
        )

        from app.services.media import LoRAConfig as MediaLoRAConfig
        sfw_lora_configs = [
            MediaLoRAConfig(model_name=l["model_name"], strength=l["strength"])
            for l in sfw_loras
        ] or None

        try:
            logger.info(f"[Step 1] Novita Z-Image-Turbo-LoRA SFW avatar for {name}...")
            task_id = await sfw_provider.txt2img_async(
                prompt=avatar_prompt,
                negative_prompt=sfw_negative,
                width=768,
                height=1024,
                loras=sfw_lora_configs,
                seed=avatar_seed,
            )
            result = await sfw_provider.wait_for_task(task_id)
            if result.image_url:
                try:
                    url = await storage_service.upload_from_url(
                        result.image_url, folder="characters/avatars"
                    )
                except Exception as e:
                    logger.warning(f"R2 upload failed for avatar: {e}")
                    url = result.image_url
                images["avatar_url"] = url
                images["cover_url"] = url        # cover = avatar (same image)
                images["avatar_card_url"] = url
                images["profile_image_url"] = url
            else:
                logger.error(
                    f"[Step 1] Novita task {task_id} completed with no image. "
                    f"Status={result.status}, error={result.error}"
                )
        except Exception as e:
            logger.error(f"Novita avatar generation failed for {name}: {e}")

        # ── Step 2: Mature with IPAdapter + LoRAs ──────────────────────────────
        sfw_avatar_url = images.get("avatar_url")
        if sfw_avatar_url:
            novita = await self._get_novita_image_provider() or sfw_provider
            mature_url = None
            retry_personalities = [
                personality,
                f"{personality} seductive".strip(),
                f"{personality} intimate lighting".strip(),
            ]
            for idx, personality_variant in enumerate(retry_personalities, start=1):
                _mature_context = (
                    f"{name}, {personality_variant} personality, "
                    f"{occupation_style}, mature scene, retry {idx}"
                )
                loras = await self._select_lora_from_db("img2img", context=_mature_context)
                mature_url = await self._generate_mature_with_ipadapter(
                    novita,
                    name=name,
                    age=age,
                    ethnicity_style=ethnicity_style,
                    personality=personality_variant,
                    sfw_avatar_url=sfw_avatar_url,
                    loras=loras,
                    visual_brief=visual_brief,
                )
                if mature_url:
                    logger.info(
                        "Mature image generated for %s on retry %s/3",
                        name,
                        idx,
                    )
                    break
                logger.warning(
                    "Mature image generation attempt %s/3 failed for %s",
                    idx,
                    name,
                )

            if mature_url:
                images["mature_image_url"] = mature_url
                images["mature_cover_url"] = mature_url  # mature_cover = mature_image
            else:
                logger.error(
                    "Mature image generation failed after 3 retries for %s; "
                    "downstream video may fall back to avatar_url.",
                    name,
                )

        return images

    async def _generate_character_video(self, profile: dict, mature_image_url: str) -> Optional[str]:
        """Novita WAN2.1 img2video - image_url passed directly, no base64."""
        try:
            novita_video = self._get_novita_video_provider()
            if not novita_video:
                logger.warning("Novita video provider not configured")
                return None

            name = profile.get("name", "Character")
            personality_tags = profile.get("personality_tags", [])
            personality = " ".join(personality_tags[:2]) if personality_tags else "sensual"
            visual_brief = profile.get("_visual_brief") or self._build_visual_brief()
            video_brief = visual_brief.get("video", {}) if isinstance(visual_brief, dict) else {}

            def _pick_one(raw: str) -> str:
                parts = [p.strip() for p in raw.split(",") if p.strip()]
                return random.choice(parts) if parts else ""

            lora_context = f"{name}, {personality} personality, mature video motion"
            video_loras = await self._select_lora_from_db("video", context=lora_context)
            trigger_words = " ".join(
                _pick_one(l["trigger_word"]) for l in video_loras if l.get("trigger_word")
            )
            from app.services.media import LoRAConfig as MediaLoRAConfig
            video_lora_configs = [
                MediaLoRAConfig(model_name=l["model_name"], strength=l["strength"])
                for l in video_loras
                if l.get("model_name")
            ] or None

            video_variation = self._sample_video_prompt_variation()
            video_seed = int(video_brief.get("seed") or self._random_seed())
            video_prompt = (
                f"a beautiful nude woman, {personality}, "
                f"{video_brief.get('motion') or video_variation['motion']}, "
                f"{video_brief.get('action') or video_variation['action']}, "
                f"{video_brief.get('camera') or video_variation['camera']}, "
                f"{video_brief.get('background') or video_variation['background']}, "
                f"{video_brief.get('quality') or video_variation['quality']}, "
                "clear full-body pose transition, visible hand movement, torso movement, "
                "natural body movement, expressive eye contact, slight blinking, "
                "smooth motion, coherent anatomy, high quality, cinematic"
            )
            if trigger_words:
                video_prompt = f"{trigger_words}, {video_prompt}"

            logger.info(f"[Step 3] Novita WAN2.1 Mature video for {name}...")
            result = await novita_video.generate_video(
                prompt=video_prompt,
                init_image=mature_image_url,
                width=832,
                height=480,
                steps=30,
                guidance_scale=5.0,
                flow_shift=5.0,
                seed=video_seed,
                enable_safety_checker=False,
                timeout_seconds=600,
                loras=video_lora_configs,
            )

            if result and result.video_url:
                try:
                    video_url = await storage_service.upload_from_url(
                        result.video_url, folder="characters/mature_videos"
                    )
                    logger.info(f"Mature video generated and uploaded for {name}")
                    return video_url
                except Exception as e:
                    logger.warning(f"R2 upload failed for Mature video: {e}")
                    return result.video_url

        except Exception as e:
            logger.error(f"Mature video generation failed: {e}")

        return None

    async def regenerate_mature_media(self, character_id: str, generate_video: bool = False) -> dict:
        """Regenerate Mature image (IPAdapter + LoRAs) and optionally launch video."""
        character = await character_service.get_character_by_id(character_id)
        if not character:
            raise ValueError(f"Character not found: {character_id}")

        sfw_avatar = character.get("avatar_url")
        if not sfw_avatar:
            raise ValueError(f"Character {character_id} has no SFW avatar for IPAdapter reference")

        novita = await self._get_novita_image_provider()
        if not novita:
            raise ValueError("Novita provider not configured")

        age = character.get("age", 25)
        ethnicity = character.get("ethnicity", "white")
        ethnicity_style = ETHNICITY_IMAGE_STYLES.get(ethnicity, ETHNICITY_IMAGE_STYLES["white"])
        personality_tags = character.get("personality_tags") or []
        personality = " ".join(personality_tags[:2]) if personality_tags else "sensual"
        name = character.get("name", "Character")

        _regen_context = f"{name}, {personality} personality, mature scene"
        loras = await self._select_lora_from_db("img2img", context=_regen_context)
        mature_url = await self._generate_mature_with_ipadapter(
            novita,
            name=name,
            age=age,
            ethnicity_style=ethnicity_style,
            personality=personality,
            sfw_avatar_url=sfw_avatar,
            loras=loras,
        )

        if not mature_url:
            fallback_prompt = (
                f"nude full body photo of a beautiful {age}-year-old {ethnicity_style['avatar']}, "
                f"{personality} personality, detailed skin, photorealistic, masterpiece photography, "
                "lightrays, very detailed skin, 8k focus stacking, looking at camera"
            )
            fallback_negative = (
                "low quality, bad anatomy, blur, blurry, ugly, wrong proportions, "
                "watermark, bad eyes, bad hands, bad arms, deformed, disfigured"
            )
            logger.warning(
                "Mature IPAdapter failed for %s (%s); trying non-IPAdapter fallback.",
                character_id,
                name,
            )
            mature_url = await self._generate_mature_variant(
                novita,
                name=name,
                prompt=fallback_prompt,
                base_image_urls=[sfw_avatar],
                negative_prompt=fallback_negative,
                width=768,
                height=1024,
                log_label="regenerate-mature-fallback",
            )

        update_data: dict = {}
        if mature_url:
            update_data["mature_image_url"] = mature_url
            update_data["mature_cover_url"] = mature_url  # mature_cover = mature_image
        else:
            raise RuntimeError(
                f"Mature generation failed for {character_id}: Novita returned no usable image"
            )

        if generate_video:
            video_source = mature_url or sfw_avatar
            asyncio.create_task(
                self._generate_and_save_video(character_id, character, video_source)
            )

        if update_data:
            from app.models.character import CharacterUpdate
            return await character_service.update_character(
                character_id, CharacterUpdate(**update_data)
            )

        return character

    async def _generate_seo_content(self, profile: dict) -> dict:
        seo_data = {}

        name = profile.get("name", "")
        slug = generate_slug(name)

        seo_data["slug"] = slug

        description = profile.get("description", "")
        if description:
            seo_data["meta_description"] = description[:160]

        nationality = profile.get("nationality", "")
        occupation = profile.get("occupation", "")
        meta_title = f"{name} - {occupation.title().replace('_', ' ')} | RoxyClub"
        if nationality:
            meta_title = f"{name} - {nationality.upper()} {occupation.title().replace('_', ' ')} | RoxyClub"
        seo_data["meta_title"] = meta_title[:200]

        personality_tags = profile.get("personality_tags", [])
        keywords = personality_tags + [name, "AI character", "virtual companion", "chat", occupation]
        if nationality:
            keywords.append(nationality)
        seo_data["keywords"] = list(set(keywords))[:10]

        seo_data["seo_optimized"] = True

        return seo_data


character_factory = CharacterFactory()
