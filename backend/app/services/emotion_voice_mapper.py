import re
from typing import Optional

EMOTION_PRESETS: dict[str, dict[str, float]] = {
    "撒娇":  {"stability": 0.25, "similarity_boost": 0.90, "style": 0.75, "use_speaker_boost": True},
    "开心":  {"stability": 0.35, "similarity_boost": 0.85, "style": 0.65, "use_speaker_boost": True},
    "兴奋":  {"stability": 0.20, "similarity_boost": 0.85, "style": 0.85, "use_speaker_boost": True},
    "生气":  {"stability": 0.70, "similarity_boost": 0.80, "style": 0.80, "use_speaker_boost": True},
    "委屈":  {"stability": 0.55, "similarity_boost": 0.88, "style": 0.60, "use_speaker_boost": True},
    "害羞":  {"stability": 0.45, "similarity_boost": 0.88, "style": 0.50, "use_speaker_boost": True},
    "悲伤":  {"stability": 0.65, "similarity_boost": 0.82, "style": 0.40, "use_speaker_boost": False},
    "温柔":  {"stability": 0.40, "similarity_boost": 0.87, "style": 0.45, "use_speaker_boost": True},
    "平静":  {"stability": 0.55, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": False},
    "惊讶":  {"stability": 0.30, "similarity_boost": 0.85, "style": 0.70, "use_speaker_boost": True},
    "担心":  {"stability": 0.50, "similarity_boost": 0.83, "style": 0.45, "use_speaker_boost": False},
    "调皮":  {"stability": 0.28, "similarity_boost": 0.88, "style": 0.78, "use_speaker_boost": True},
    # English aliases
    "playful":  {"stability": 0.28, "similarity_boost": 0.88, "style": 0.78, "use_speaker_boost": True},
    "happy":    {"stability": 0.35, "similarity_boost": 0.85, "style": 0.65, "use_speaker_boost": True},
    "sad":      {"stability": 0.65, "similarity_boost": 0.82, "style": 0.40, "use_speaker_boost": False},
    "angry":    {"stability": 0.70, "similarity_boost": 0.80, "style": 0.80, "use_speaker_boost": True},
    "excited":  {"stability": 0.20, "similarity_boost": 0.85, "style": 0.85, "use_speaker_boost": True},
    "gentle":   {"stability": 0.40, "similarity_boost": 0.87, "style": 0.45, "use_speaker_boost": True},
    "shy":      {"stability": 0.45, "similarity_boost": 0.88, "style": 0.50, "use_speaker_boost": True},
    "default":  {"stability": 0.50, "similarity_boost": 0.75, "style": 0.30, "use_speaker_boost": False},
}

_EMOTION_TAG_RE = re.compile(r"^\[emotion:([^\]]+)\]\s*", re.IGNORECASE)


def get_voice_settings(emotion: Optional[str]) -> dict[str, float]:
    """Return a copy so callers can safely add fields like 'speed'."""
    if not emotion:
        return dict(EMOTION_PRESETS["default"])
    return dict(EMOTION_PRESETS.get(emotion.strip(), EMOTION_PRESETS["default"]))


def parse_emotion_tag(text: str) -> tuple[str, str]:
    """Return (emotion_label, clean_text). Empty string if no tag found."""
    m = _EMOTION_TAG_RE.match(text or "")
    if not m:
        return "", text
    return m.group(1).strip(), text[m.end():]
