from dataclasses import dataclass
from typing import Optional


@dataclass
class LoRAConfig:
    id: str
    name: str
    trigger_word: str
    description: str
    default_strength: float = 0.95
    novita_model_name: Optional[str] = None


NOVITA_LORA_CONFIGS: dict[str, LoRAConfig] = {
    "blowjob": LoRAConfig(
        id="blowjob",
        name="Blowjob",
        trigger_word="blowjob, oral sex, penis in mouth, pov, beautiful woman on knees, looking up at viewer, completely nude, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Oral sex – blowjob POV",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "butterfly_sex": LoRAConfig(
        id="butterfly_sex",
        name="Butterfly Sex",
        trigger_word="butterfly sex, missionary position, penis, sex, legs raised, beautiful woman, looking at viewer, completely nude, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Butterfly / missionary sex position",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "cumshot": LoRAConfig(
        id="cumshot",
        name="Cumshot",
        trigger_word="projectile cum, cumshot, penis, pov, facial, covered in cum, beautiful woman kneeling, completely nude, looking at viewer, awaiting cum, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Cumshot / facial finish",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "doggy_style": LoRAConfig(
        id="doggy_style",
        name="Doggy Style",
        trigger_word="doggy style, doggy style position, penis, sex, beautiful woman, from behind, looking back, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Doggy style sex position",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "fivesome": LoRAConfig(
        id="fivesome",
        name="Fivesome",
        trigger_word="fivesome, group sex, multiple men, beautiful woman, completely nude, gangbang, all holes filled, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Fivesome group sex",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "foodtease": LoRAConfig(
        id="foodtease",
        name="Food Tease",
        trigger_word="foodtease, food play, licking food sensually, beautiful woman, completely nude, seductive expression, looking at viewer, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Sensual food teasing",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "foursome": LoRAConfig(
        id="foursome",
        name="Foursome",
        trigger_word="foursome, group sex, multiple partners, beautiful woman, completely nude, double penetration, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Foursome group sex",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "handjob": LoRAConfig(
        id="handjob",
        name="Handjob",
        trigger_word="handjob, stroking penis, pov, beautiful woman, hand wrapped around penis, looking at viewer, completely nude, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="POV handjob",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "licking_cock": LoRAConfig(
        id="licking_cock",
        name="Licking Cock",
        trigger_word="licking cock, tongue on penis, oral teasing, pov, beautiful woman, looking up at viewer, completely nude, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Cock licking / oral teasing",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "orgasming": LoRAConfig(
        id="orgasming",
        name="Orgasming",
        trigger_word="orgasming, head back, mouth open, trembling, ecstasy, beautiful woman, completely nude, climax, ahegao, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Orgasm expression",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "reverse_gang_bang": LoRAConfig(
        id="reverse_gang_bang",
        name="Reverse Gang Bang",
        trigger_word="reverse gang bang, multiple women, group sex, beautiful women, completely nude, surrounding man, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Reverse gang bang",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "reversecowgirl": LoRAConfig(
        id="reversecowgirl",
        name="Reverse Cowgirl",
        trigger_word="reversecowgirl, reverse cowgirl position, penis, sex, from behind, looking back, beautiful woman, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Reverse cowgirl position",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "riding_cowgirl": LoRAConfig(
        id="riding_cowgirl",
        name="Riding Cowgirl",
        trigger_word="riding cowgirl, cowgirl position, penis, sex, girl on top, beautiful woman, looking at viewer, hands on chest, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Riding cowgirl position",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "self_stroking": LoRAConfig(
        id="self_stroking",
        name="Self Stroking",
        trigger_word="self stroking, masturbation, fingers, beautiful woman, completely nude, touching herself, legs spread, pov, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Self stroking / masturbation",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "sidefuck": LoRAConfig(
        id="sidefuck",
        name="Sidefuck",
        trigger_word="sidefuck, side lying position, penis, sex, spooning, beautiful woman, completely nude, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Side-lying sex position",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "teasing": LoRAConfig(
        id="teasing",
        name="Teasing",
        trigger_word="teasing, seductive pose, beautiful woman, partially undressed, biting lip, looking at viewer, lingerie pull down, sensual, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Seductive teasing pose",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "threesome": LoRAConfig(
        id="threesome",
        name="Threesome",
        trigger_word="threesome, two men, beautiful woman, completely nude, double penetration, sandwich position, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Threesome sex",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "titty_fucking": LoRAConfig(
        id="titty_fucking",
        name="Titty Fucking",
        trigger_word="beautiful woman, titty fucking, paizuri, penis, pov crotch, open mouth, breasts squeezed together, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Titty fucking / paizuri",
        default_strength=0.95,
        novita_model_name=None,
    ),
    "undressing": LoRAConfig(
        id="undressing",
        name="Undressing",
        trigger_word="undressing, pulled by self, beautiful woman, shorts pull, ass, pussy, from behind, looking back, smiling, masterpiece photography, lightrays, very detailed skin, 8k focus stacking",
        description="Undressing / strip tease",
        default_strength=0.95,
        novita_model_name=None,
    ),
}


QUALITY_LORAS: list[dict] = [
    {"model_name": "add_detail_44319", "strength": 0.5, "description": "Add detail"},
    {"model_name": "more_details_59655", "strength": 0.5, "description": "More details"},
]


NEGATIVE_PROMPTS = {
    "default": "explicit, adult content, low quality, bad anatomy, blur, blurry, ugly, wrong proportions, watermark, bad eyes, bad hands, bad arms, deformed, disfigured, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck",
    "realistic": "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime), text, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, BadDream, UnrealisticDream",
}


def get_lora_config(lora_id: str) -> Optional[LoRAConfig]:
    return NOVITA_LORA_CONFIGS.get(lora_id)


def get_lora_trigger_word(lora_id: str) -> str:
    config = get_lora_config(lora_id)
    return config.trigger_word if config else ""


def get_lora_strength(lora_id: str) -> float:
    config = get_lora_config(lora_id)
    return config.default_strength if config else 0.7
