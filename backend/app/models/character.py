import uuid
from datetime import datetime
from typing import Optional, Any, Literal
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

ReviewStatus = Literal["pending", "approved", "rejected"]

Ethnicity = Literal["white", "asian", "black", "latina", "middle_eastern"]
Nationality = Literal["usa", "japan", "korea", "china", "germany", "france", "uk", "italy", "spain", "brazil", "india", "russia", "australia", "canada", "mexico", "thailand", "vietnam", "philippines"]


def generate_character_id() -> str:
    return f"char_{uuid.uuid4().hex[:12]}"


def generate_slug(name: str, max_length: int = 150) -> str:
    import re
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = re.sub(r'^-+|-+$', '', slug)
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    return slug or f"character-{uuid.uuid4().hex[:6]}"


class Character(Base):
    __tablename__ = "characters"
    
    id = Column(String(50), primary_key=True, default=generate_character_id)
    
    name = Column(String(100), nullable=False)
    first_name = Column(String(50), nullable=True)
    slug = Column(String(150), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), default="female")
    
    ethnicity = Column(String(30), nullable=True)
    nationality = Column(String(30), nullable=True)
    occupation = Column(String(50), nullable=True)
    
    top_category = Column(String(30), default="girls", index=True)
    sub_category = Column(String(50), nullable=True)
    filter_tags = Column(JSON, nullable=True)
    personality_tags = Column(JSON, nullable=True)
    keywords = Column(JSON, nullable=True)
    
    personality_summary = Column(Text, nullable=True)
    personality_example = Column(Text, nullable=True)
    backstory = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    greeting = Column(Text, nullable=True)
    
    avatar_url = Column(String(512), nullable=True)
    cover_url = Column(String(512), nullable=True)
    avatar_card_url = Column(String(512), nullable=True)
    profile_image_url = Column(String(512), nullable=True)
    preview_video_url = Column(String(512), nullable=True)
    
    voice_id = Column(String(100), nullable=True)
    
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(Text, nullable=True)
    seo_optimized = Column(Boolean, default=False)
    
    is_official = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=True, index=True)
    template_id = Column(String(50), nullable=True)
    generation_mode = Column(String(20), default="manual")
    
    popularity_score = Column(Float, default=0.0)
    chat_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    creator_id = Column(String(50), nullable=True)
    family_id = Column(String(50), nullable=True)
    lifecycle_status = Column(String(20), default="active")
    
    review_status = Column(String(20), default="approved")
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_id = Column(String(50), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    extra_data = Column(JSON, nullable=True)


class CharacterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    first_name: Optional[str] = Field(None, max_length=50)
    slug: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    age: Optional[int] = Field(None, ge=18, le=99)
    gender: Optional[str] = "female"
    
    ethnicity: Optional[str] = None
    nationality: Optional[str] = None
    occupation: Optional[str] = None
    
    top_category: Optional[str] = "girls"
    sub_category: Optional[str] = None
    filter_tags: Optional[list[str]] = None
    personality_tags: Optional[list[str]] = None
    keywords: Optional[list[str]] = None
    
    personality_summary: Optional[str] = Field(None, max_length=500)
    personality_example: Optional[str] = None
    backstory: Optional[str] = None
    system_prompt: Optional[str] = None
    greeting: Optional[str] = None

    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    avatar_card_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    mature_image_url: Optional[str] = None
    mature_cover_url: Optional[str] = None
    mature_video_url: Optional[str] = None

    voice_id: Optional[str] = None

    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = None

    is_public: bool = True
    template_id: Optional[str] = None
    generation_mode: Optional[str] = "manual"

    review_status: Optional[ReviewStatus] = "approved"


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    first_name: Optional[str] = Field(None, max_length=50)
    slug: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    age: Optional[int] = Field(None, ge=18, le=99)
    gender: Optional[str] = None
    
    ethnicity: Optional[str] = None
    nationality: Optional[str] = None
    occupation: Optional[str] = None
    
    top_category: Optional[str] = None
    sub_category: Optional[str] = None
    filter_tags: Optional[list[str]] = None
    personality_tags: Optional[list[str]] = None
    keywords: Optional[list[str]] = None
    
    personality_summary: Optional[str] = Field(None, max_length=500)
    personality_example: Optional[str] = None
    backstory: Optional[str] = None
    system_prompt: Optional[str] = None
    greeting: Optional[str] = None

    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    avatar_card_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    mature_image_url: Optional[str] = None
    mature_cover_url: Optional[str] = None
    mature_video_url: Optional[str] = None

    voice_id: Optional[str] = None

    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = None
    seo_optimized: Optional[bool] = None
    
    is_public: Optional[bool] = None
    lifecycle_status: Optional[str] = None
    
    review_status: Optional[ReviewStatus] = None
    rejection_reason: Optional[str] = None


class CharacterBatchGenerate(BaseModel):
    count: int = Field(..., ge=1, le=50)
    top_category: str = "girls"
    ethnicity: Optional[str] = None
    nationality: Optional[str] = None
    occupation: Optional[str] = None
    personality_preferences: Optional[list[str]] = None
    age_min: Optional[int] = Field(20, ge=18)
    age_max: Optional[int] = Field(30, le=99)
    generate_images: bool = True
    generate_video: bool = False
    optimize_seo: bool = True


class CharacterFromTemplate(BaseModel):
    template_id: str
    variations: int = Field(1, ge=1, le=10)
    ethnicity: Optional[str] = None
    nationality: Optional[str] = None
    generate_images: bool = True
    generate_video: bool = False
    optimize_seo: bool = True


class CharacterReviewAction(BaseModel):
    action: Literal["approve", "reject"]
    rejection_reason: Optional[str] = Field(None, max_length=500)


class CharacterResponse(BaseModel):
    id: str
    name: str
    first_name: Optional[str] = None
    slug: str
    description: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    
    ethnicity: Optional[str] = None
    nationality: Optional[str] = None
    occupation: Optional[str] = None
    
    top_category: Optional[str] = None
    sub_category: Optional[str] = None
    filter_tags: Optional[list[str]] = None
    personality_tags: Optional[list[str]] = None
    
    personality_summary: Optional[str] = None
    greeting: Optional[str] = None
    
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    avatar_card_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    mature_image_url: Optional[str] = None
    mature_cover_url: Optional[str] = None
    mature_video_url: Optional[str] = None

    voice_id: Optional[str] = None

    is_official: bool = True
    is_public: bool = True
    popularity_score: float = 0.0
    chat_count: int = 0
    
    review_status: Optional[ReviewStatus] = "approved"
    rejection_reason: Optional[str] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class CharacterDetailResponse(CharacterResponse):
    personality_example: Optional[str] = None
    backstory: Optional[str] = None
    system_prompt: Optional[str] = None
    
    profile_image_url: Optional[str] = None
    
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: Optional[list[str]] = None
    seo_optimized: bool = False
    
    template_id: Optional[str] = None
    generation_mode: Optional[str] = None
    lifecycle_status: Optional[str] = None
    
    updated_at: Optional[datetime] = None


ETHNICITY_IMAGE_STYLES: dict[str, dict[str, str]] = {
    "white": {
        "avatar": "caucasian woman, european features, fair skin, photorealistic",
        "cover": "caucasian woman, european descent, photorealistic",
        "description": "European descent"
    },
    "asian": {
        "avatar": "east asian woman, asian features, smooth skin, photorealistic",
        "cover": "east asian woman, photorealistic",
        "description": "East Asian descent"
    },
    "black": {
        "avatar": "african american woman, dark skin, beautiful features, photorealistic",
        "cover": "african american woman, photorealistic",
        "description": "African descent"
    },
    "latina": {
        "avatar": "latina woman, hispanic features, warm skin tone, photorealistic",
        "cover": "latina woman, hispanic descent, photorealistic",
        "description": "Hispanic/Latina descent"
    },
    "middle_eastern": {
        "avatar": "middle eastern woman, olive skin, beautiful features, photorealistic",
        "cover": "middle eastern woman, photorealistic",
        "description": "Middle Eastern descent"
    }
}

NATIONALITY_CONFIGS: dict[str, dict[str, Any]] = {
    "usa": {
        "name_pool": ["Emma", "Sophia", "Olivia", "Ava", "Isabella", "Mia", "Charlotte", "Amelia", "Harper", "Evelyn"],
        "background_hints": ["american city", "new york apartment", "los angeles", "chicago downtown"],
        "greeting_style": "casual, friendly",
        "cultural_traits": ["outgoing", "confident", "friendly"]
    },
    "japan": {
        "name_pool": ["Sakura", "Yuki", "Hana", "Miyu", "Rina", "Haruka", "Akiko", "Emi", "Yui", "Mio"],
        "background_hints": ["tokyo", "japanese apartment", "shibuya", "shinjuku", "kyoto temple"],
        "greeting_style": "polite, gentle",
        "cultural_traits": ["polite", "gentle", "thoughtful"]
    },
    "korea": {
        "name_pool": ["Ji-woo", "Seo-jun", "Ha-eun", "Min-ji", "Su-bin", "Yuna", "Ji-min", "Eun-ji", "Soo-min", "Hye-won"],
        "background_hints": ["seoul", "korean cafe", "gangnam", "han river", "korean street"],
        "greeting_style": "cheerful, cute",
        "cultural_traits": ["cheerful", "caring", "hardworking"]
    },
    "china": {
        "name_pool": ["Xia", "Mei", "Ling", "Ying", "Fang", "Jing", "Hui", "Lian", "Qing", "Wen"],
        "background_hints": ["shanghai", "beijing", "chinese garden", "modern chinese city"],
        "greeting_style": "warm, hospitable",
        "cultural_traits": ["warm", "family-oriented", "intelligent"]
    },
    "germany": {
        "name_pool": ["Emma", "Hannah", "Mia", "Lena", "Lea", "Anna", "Marie", "Laura", "Julia", "Sarah"],
        "background_hints": ["berlin", "munich", "german cafe", "european architecture"],
        "greeting_style": "direct, honest",
        "cultural_traits": ["direct", "intelligent", "reliable"]
    },
    "france": {
        "name_pool": ["Camille", "Chloe", "Manon", "Lea", "Sarah", "Alice", "Juliette", "Louise", "Emma", "Zoe"],
        "background_hints": ["paris", "french cafe", "eiffel tower", "french countryside"],
        "greeting_style": "romantic, elegant",
        "cultural_traits": ["romantic", "elegant", "artistic"]
    },
    "uk": {
        "name_pool": ["Olivia", "Amelia", "Isla", "Ava", "Ivy", "Freya", "Lily", "Florence", "Willow", "Sienna"],
        "background_hints": ["london", "british pub", "english countryside", "oxford"],
        "greeting_style": "polite, witty",
        "cultural_traits": ["polite", "witty", "sophisticated"]
    },
    "italy": {
        "name_pool": ["Sofia", "Giulia", "Aurora", "Alice", "Ginevra", "Chiara", "Francesca", "Alessia", "Martina", "Sara"],
        "background_hints": ["rome", "venice", "italian cafe", "tuscan countryside", "milan"],
        "greeting_style": "passionate, warm",
        "cultural_traits": ["passionate", "warm", "expressive"]
    },
    "spain": {
        "name_pool": ["Lucia", "Sofia", "Maria", "Paula", "Daniela", "Carla", "Alba", "Ana", "Laura", "Marta"],
        "background_hints": ["barcelona", "madrid", "spanish plaza", "beach", "flamenco"],
        "greeting_style": "lively, affectionate",
        "cultural_traits": ["lively", "passionate", "social"]
    },
    "brazil": {
        "name_pool": ["Isabella", "Sophia", "Alice", "Julia", "Manuela", "Laura", "Luiza", "Valentina", "Helena", "Beatriz"],
        "background_hints": ["rio de janeiro", "brazilian beach", "sao paulo", "copacabana"],
        "greeting_style": "energetic, friendly",
        "cultural_traits": ["energetic", "friendly", "carefree"]
    },
    "india": {
        "name_pool": ["Priya", "Ananya", "Aisha", "Diya", "Kavya", "Neha", "Pooja", "Riya", "Sana", "Zara"],
        "background_hints": ["mumbai", "delhi", "indian palace", "bollywood", "temple"],
        "greeting_style": "warm, respectful",
        "cultural_traits": ["warm", "family-oriented", "traditional"]
    },
    "russia": {
        "name_pool": ["Anastasia", "Sofia", "Anna", "Maria", "Daria", "Polina", "Alisa", "Victoria", "Elena", "Natalia"],
        "background_hints": ["moscow", "st petersburg", "russian winter", "ballet theater"],
        "greeting_style": "elegant, mysterious",
        "cultural_traits": ["elegant", "mysterious", "intelligent"]
    },
    "australia": {
        "name_pool": ["Charlotte", "Olivia", "Amelia", "Mia", "Sophia", "Chloe", "Emily", "Ella", "Grace", "Lily"],
        "background_hints": ["sydney", "melbourne", "australian beach", "outback"],
        "greeting_style": "laid-back, adventurous",
        "cultural_traits": ["laid-back", "adventurous", "friendly"]
    },
    "canada": {
        "name_pool": ["Olivia", "Emma", "Charlotte", "Amelia", "Sophia", "Chloe", "Ella", "Scarlett", "Aria", "Harper"],
        "background_hints": ["toronto", "vancouver", "canadian wilderness", "montreal"],
        "greeting_style": "friendly, polite",
        "cultural_traits": ["friendly", "polite", "nature-loving"]
    },
    "mexico": {
        "name_pool": ["Sofia", "Valentina", "Camila", "Ximena", "Isabella", "Maria", "Renata", "Victoria", "Andrea", "Natalia"],
        "background_hints": ["mexico city", "cancun beach", "colonial town", "fiesta"],
        "greeting_style": "warm, festive",
        "cultural_traits": ["warm", "festive", "family-oriented"]
    },
    "thailand": {
        "name_pool": ["Pim", "Nook", "Mai", "Dao", "Som", "Fah", "Mook", "Aom", "Bam", "Gig"],
        "background_hints": ["bangkok", "thai temple", "phuket beach", "floating market"],
        "greeting_style": "gentle, sweet",
        "cultural_traits": ["gentle", "sweet", "hospitable"]
    },
    "vietnam": {
        "name_pool": ["Linh", "Mai", "Hanh", "Thao", "Nga", "Huong", "Lan", "Van", "Ha", "My"],
        "background_hints": ["ho chi minh city", "hanoi", "halong bay", "vietnamese cafe"],
        "greeting_style": "gentle, hardworking",
        "cultural_traits": ["gentle", "hardworking", "hospitable"]
    },
    "philippines": {
        "name_pool": ["Maria", "Anna", "Sofia", "Isabella", "Angel", "Grace", "Joy", "Hope", "Faith", "Love"],
        "background_hints": ["manila", "philippine beach", "tropical island", "manila bay"],
        "greeting_style": "cheerful, hospitable",
        "cultural_traits": ["cheerful", "hospitable", "family-oriented"]
    }
}

OCCUPATION_TEMPLATES: dict[str, dict[str, Any]] = {
    "college_student": {
        "name": "大学生",
        "description": "Young, energetic college student",
        "age_range": (19, 23),
        "personality_pool": ["playful", "smart", "romantic", "shy", "energetic", "curious", "studious", "ambitious"],
        "background_hints": ["university", "dorm", "library", "campus cafe", "student life", "lecture hall"],
        "style_keywords": ["casual", "youthful", "trendy", "fresh"],
        "image_style": "young woman, college student, casual clothes, natural makeup, friendly smile",
        "greeting_templates": [
            "Hey! I'm {name}, a student at the university. Want to study together?",
            "Hi there! I'm {name}. Just finished my classes, what about you?",
            "Oh hey! I'm {name}. Are you a student here too?"
        ]
    },
    "office_worker": {
        "name": "公司职员",
        "description": "Professional, independent career woman",
        "age_range": (25, 32),
        "personality_pool": ["mature", "independent", "intelligent", "confident", "ambitious", "professional", "organized"],
        "background_hints": ["office", "corporate", "business district", "career", "professional", "meeting room"],
        "style_keywords": ["professional", "elegant", "sophisticated", "classy"],
        "image_style": "professional woman, business attire, office setting, confident expression",
        "greeting_templates": [
            "Hello, I'm {name}. Nice to meet you. How can I help you today?",
            "Hi, I'm {name}. Just finished a meeting. How's your day going?",
            "Good day! I'm {name}. Taking a quick break from work. What's up?"
        ]
    },
    "doctor": {
        "name": "医生",
        "description": "Caring, intelligent medical professional",
        "age_range": (28, 38),
        "personality_pool": ["caring", "intelligent", "calm", "compassionate", "professional", "patient", "dedicated"],
        "background_hints": ["hospital", "clinic", "medical center", "white coat", "stethoscope"],
        "style_keywords": ["professional", "caring", "trustworthy", "clean"],
        "image_style": "female doctor, white coat, stethoscope, hospital background, caring smile",
        "greeting_templates": [
            "Hello, I'm Dr. {name}. How are you feeling today?",
            "Hi, I'm {name}. Is there something I can help you with?",
            "Good to see you! I'm {name}. Taking care of your health is my priority."
        ]
    },
    "nurse": {
        "name": "护士",
        "description": "Compassionate, attentive healthcare worker",
        "age_range": (23, 32),
        "personality_pool": ["caring", "patient", "gentle", "attentive", "warm", "compassionate", "hardworking"],
        "background_hints": ["hospital ward", "nurses station", "medical equipment", "patient care"],
        "style_keywords": ["caring", "gentle", "warm", "approachable"],
        "image_style": "female nurse, scrubs, hospital setting, warm caring smile",
        "greeting_templates": [
            "Hi there! I'm Nurse {name}. How can I make you more comfortable?",
            "Hello! I'm {name}. I'll be taking care of you today.",
            "Hey sweetie, I'm {name}. Is there anything you need?"
        ]
    },
    "teacher": {
        "name": "教师",
        "description": "Patient, knowledgeable educator",
        "age_range": (25, 35),
        "personality_pool": ["patient", "knowledgeable", "caring", "encouraging", "intelligent", "warm", "organized"],
        "background_hints": ["classroom", "school", "university", "library", "books", "chalkboard"],
        "style_keywords": ["professional", "approachable", "intelligent", "warm"],
        "image_style": "female teacher, professional attire, classroom setting, warm smile",
        "greeting_templates": [
            "Hello! I'm Ms. {name}. Are you here to learn something new?",
            "Hi there! I'm {name}. Education is my passion. What would you like to know?",
            "Welcome! I'm {name}. I love helping others learn. How can I help you?"
        ]
    },
    "model": {
        "name": "模特",
        "description": "Stunning, confident fashion model",
        "age_range": (20, 28),
        "personality_pool": ["confident", "photogenic", "elegant", "charismatic", "stylish", "ambitious", "disciplined"],
        "background_hints": ["fashion show", "photo studio", "runway", "designer clothes", "magazine cover"],
        "style_keywords": ["glamorous", "stylish", "elegant", "fashionable"],
        "image_style": "stunning female model, high fashion, professional photography, elegant pose",
        "greeting_templates": [
            "Hi! I'm {name}. Just finished a photoshoot. What do you think?",
            "Hello there! I'm {name}. Fashion is my life. Got any style questions?",
            "Hey! I'm {name}. Always happy to meet new people. What brings you here?"
        ]
    },
    "influencer": {
        "name": "网红博主",
        "description": "Trendy, social media personality",
        "age_range": (22, 28),
        "personality_pool": ["trendy", "social", "charismatic", "creative", "outgoing", "entertaining", "authentic"],
        "background_hints": ["instagram", "tiktok", "content creation", "social media", "trending", "lifestyle"],
        "style_keywords": ["trendy", "photogenic", "stylish", "relatable"],
        "image_style": "social media influencer, trendy outfit, perfect lighting, instagram aesthetic",
        "greeting_templates": [
            "Hey guys! I'm {name}. Welcome to my world! Don't forget to like and subscribe!",
            "Hi! I'm {name}. Creating content is my life. Want to be in my next video?",
            "Hello beautiful people! I'm {name}. Let's make today amazing!"
        ]
    },
    "gamer": {
        "name": "游戏玩家",
        "description": "Passionate, skilled gamer",
        "age_range": (19, 27),
        "personality_pool": ["competitive", "passionate", "strategic", "witty", "focused", "geeky", "enthusiastic"],
        "background_hints": ["gaming setup", "rgb lights", "streaming", "esports", "controller", "headset"],
        "style_keywords": ["casual", "geeky", "relatable", "enthusiastic"],
        "image_style": "female gamer, gaming headset, led lights background, casual clothes, focused expression",
        "greeting_templates": [
            "Yo! I'm {name}. Just finished a ranked match. Wanna play together?",
            "Hey! I'm {name}. GG! What games do you play?",
            "Hi there! I'm {name}. Let's see if you can beat my high score!"
        ]
    },
    "streamer": {
        "name": "主播",
        "description": "Entertaining, engaging live streamer",
        "age_range": (20, 28),
        "personality_pool": ["entertaining", "charismatic", "witty", "engaging", "energetic", "creative", "authentic"],
        "background_hints": ["streaming room", "webcam", "chat interaction", "content creation", "live broadcast"],
        "style_keywords": ["entertaining", "expressive", "relatable", "energetic"],
        "image_style": "female streamer, streaming setup, webcam, expressive face, colorful background",
        "greeting_templates": [
            "Hey chat! I'm {name}. Welcome to the stream! What's up?",
            "Hi everyone! I'm {name}. Thanks for tuning in! What should we do today?",
            "Hello! I'm {name}. Stream is live! Let's have some fun!"
        ]
    },
    "chef": {
        "name": "厨师",
        "description": "Creative, passionate culinary artist",
        "age_range": (25, 35),
        "personality_pool": ["creative", "passionate", "perfectionist", "warm", "energetic", "patient", "generous"],
        "background_hints": ["restaurant kitchen", "cooking", "ingredients", "fine dining", "culinary arts"],
        "style_keywords": ["professional", "creative", "warm", "passionate"],
        "image_style": "female chef, chef uniform, professional kitchen, passionate expression",
        "greeting_templates": [
            "Hello! I'm Chef {name}. Ready to cook something amazing together?",
            "Hi there! I'm {name}. Food is my art. What's your favorite dish?",
            "Welcome to my kitchen! I'm {name}. Let me cook something special for you."
        ]
    },
    "barista": {
        "name": "咖啡师",
        "description": "Friendly, skilled coffee artist",
        "age_range": (21, 28),
        "personality_pool": ["friendly", "warm", "creative", "patient", "chatty", "attentive", "cheerful"],
        "background_hints": ["coffee shop", "espresso machine", "latte art", "cafe atmosphere", "morning rush"],
        "style_keywords": ["cozy", "warm", "friendly", "artistic"],
        "image_style": "female barista, cafe apron, warm smile, cozy coffee shop background",
        "greeting_templates": [
            "Welcome! I'm {name}. What can I get for you today?",
            "Hi there! I'm {name}. The usual, or feeling adventurous today?",
            "Hey! I'm {name}. I make the best lattes in town. Want to try?"
        ]
    },
    "artist": {
        "name": "艺术家",
        "description": "Creative, passionate artist",
        "age_range": (22, 30),
        "personality_pool": ["creative", "passionate", "mysterious", "artistic", "dreamy", "expressive", "unique"],
        "background_hints": ["art studio", "gallery", "painting", "canvas", "creative space", "bohemian"],
        "style_keywords": ["artistic", "bohemian", "creative", "unique"],
        "image_style": "artistic woman, creative style, art studio background, dreamy expression",
        "greeting_templates": [
            "Hello~ I'm {name}. I was just working on a new painting. Do you like art?",
            "Hi! I'm {name}. The world is so beautiful when you see it through colors, isn't it?",
            "Hey! I'm {name}. Let me show you my latest creation!"
        ]
    },
    "musician": {
        "name": "音乐家",
        "description": "Talented, soulful musician",
        "age_range": (21, 30),
        "personality_pool": ["creative", "passionate", "emotional", "expressive", "talented", "dedicated", "free-spirited"],
        "background_hints": ["music studio", "stage", "instruments", "concert", "recording", "live performance"],
        "style_keywords": ["artistic", "expressive", "cool", "passionate"],
        "image_style": "female musician, holding instrument, stage lighting, passionate expression",
        "greeting_templates": [
            "Hey! I'm {name}. Music is my life. Want to hear me play?",
            "Hi there! I'm {name}. Just wrote a new song. Care to listen?",
            "Hello! I'm {name}. Let's make some beautiful music together."
        ]
    },
    "dancer": {
        "name": "舞者",
        "description": "Graceful, athletic dancer",
        "age_range": (20, 28),
        "personality_pool": ["graceful", "athletic", "passionate", "disciplined", "expressive", "energetic", "artistic"],
        "background_hints": ["dance studio", "stage", "rehearsal", "choreography", "performance", "mirror room"],
        "style_keywords": ["graceful", "athletic", "elegant", "expressive"],
        "image_style": "female dancer, dance studio, elegant pose, athletic body, expressive movement",
        "greeting_templates": [
            "Hi! I'm {name}. Dance is how I express myself. Want to see?",
            "Hello! I'm {name}. Just finished rehearsal. Do you like dancing?",
            "Hey there! I'm {name}. Let me dance for you!"
        ]
    },
    "fitness_trainer": {
        "name": "健身教练",
        "description": "Energetic, motivating fitness enthusiast",
        "age_range": (24, 32),
        "personality_pool": ["energetic", "motivating", "confident", "disciplined", "positive", "athletic", "encouraging"],
        "background_hints": ["gym", "fitness center", "workout equipment", "training session", "healthy lifestyle"],
        "style_keywords": ["athletic", "fit", "energetic", "motivating"],
        "image_style": "fit woman, athletic wear, gym setting, confident and energetic",
        "greeting_templates": [
            "Hey! I'm {name}, your fitness coach. Ready for a workout?",
            "Hi there! I'm {name}. Let's get those gains! What's your fitness goal?",
            "Hello! I'm {name}. No pain, no gain! Let's train together!"
        ]
    },
    "yoga_instructor": {
        "name": "瑜伽教练",
        "description": "Peaceful, balanced yoga practitioner",
        "age_range": (24, 35),
        "personality_pool": ["peaceful", "balanced", "flexible", "calm", "mindful", "patient", "spiritual"],
        "background_hints": ["yoga studio", "meditation", "zen garden", "peaceful space", "yoga mat"],
        "style_keywords": ["peaceful", "natural", "flexible", "calm"],
        "image_style": "female yoga instructor, yoga pose, peaceful background, calm expression",
        "greeting_templates": [
            "Namaste. I'm {name}. Ready to find your inner peace?",
            "Hello, I'm {name}. Let's breathe and stretch together.",
            "Hi there! I'm {name}. Yoga changed my life. Let me show you."
        ]
    },
    "fashion_designer": {
        "name": "时装设计师",
        "description": "Creative, trendsetting designer",
        "age_range": (25, 35),
        "personality_pool": ["creative", "trendy", "visionary", "perfectionist", "stylish", "innovative", "artistic"],
        "background_hints": ["design studio", "fashion show", "sketches", "fabric", "sewing machine", "atelier"],
        "style_keywords": ["chic", "creative", "sophisticated", "trendsetting"],
        "image_style": "fashion designer woman, chic outfit, design studio, stylish glasses, creative environment",
        "greeting_templates": [
            "Hi! I'm {name}. I create fashion. What's your style?",
            "Hello! I'm {name}. Fashion is my passion. Want to see my designs?",
            "Hey there! I'm {name}. Let me design something beautiful for you."
        ]
    },
    "journalist": {
        "name": "记者",
        "description": "Curious, truth-seeking journalist",
        "age_range": (25, 35),
        "personality_pool": ["curious", "intelligent", "brave", "articulate", "perceptive", "persistent", "honest"],
        "background_hints": ["newsroom", "interview", "press conference", "investigation", "media", "breaking news"],
        "style_keywords": ["professional", "intelligent", "brave", "articulate"],
        "image_style": "female journalist, professional attire, press badge, confident expression",
        "greeting_templates": [
            "Hi! I'm {name}, a journalist. Got an interesting story to tell?",
            "Hello there! I'm {name}. I'm always looking for the truth. What's your story?",
            "Hey! I'm {name}. Mind if I ask you a few questions?"
        ]
    },
    "lawyer": {
        "name": "律师",
        "description": "Sharp, persuasive legal professional",
        "age_range": (28, 40),
        "personality_pool": ["intelligent", "persuasive", "analytical", "confident", "articulate", "determined", "sharp"],
        "background_hints": ["law firm", "courtroom", "legal documents", "briefcase", "office", "justice"],
        "style_keywords": ["professional", "sharp", "sophisticated", "confident"],
        "image_style": "female lawyer, business suit, courtroom or law office, confident expression",
        "greeting_templates": [
            "Hello. I'm {name}, attorney at law. How can I help you?",
            "Hi there! I'm {name}. I fight for justice. What's your case?",
            "Good day. I'm {name}. Let's discuss your legal matters."
        ]
    },
    "scientist": {
        "name": "科学家",
        "description": "Brilliant, curious researcher",
        "age_range": (26, 38),
        "personality_pool": ["intelligent", "curious", "analytical", "focused", "innovative", "dedicated", "brilliant"],
        "background_hints": ["laboratory", "research", "experiments", "microscope", "science", "discovery"],
        "style_keywords": ["intelligent", "focused", "professional", "curious"],
        "image_style": "female scientist, lab coat, laboratory background, focused intelligent expression",
        "greeting_templates": [
            "Hello! I'm Dr. {name}. I study the mysteries of the universe.",
            "Hi there! I'm {name}. Science is my passion. What fascinates you?",
            "Greetings! I'm {name}. Every day is a new discovery in my lab."
        ]
    },
    "pilot": {
        "name": "飞行员",
        "description": "Adventurous, skilled aviator",
        "age_range": (26, 38),
        "personality_pool": ["adventurous", "confident", "calm", "disciplined", "brave", "reliable", "exciting"],
        "background_hints": ["cockpit", "airport", "airplane", "sky", "travel", "aviation"],
        "style_keywords": ["professional", "adventurous", "confident", "cool"],
        "image_style": "female pilot, pilot uniform, cockpit background, confident smile",
        "greeting_templates": [
            "Hi! I'm Captain {name}. Ready for takeoff?",
            "Hello there! I'm {name}. I fly through the skies. Where should we go?",
            "Hey! I'm {name}. The sky is my office. Love to travel?"
        ]
    },
    "photographer": {
        "name": "摄影师",
        "description": "Creative, observant photographer",
        "age_range": (23, 35),
        "personality_pool": ["creative", "observant", "artistic", "patient", "passionate", "detail-oriented", "expressive"],
        "background_hints": ["photo studio", "camera", "lenses", "outdoor shoot", "editing", "gallery"],
        "style_keywords": ["creative", "artistic", "cool", "observant"],
        "image_style": "female photographer, camera in hand, artistic style, creative background",
        "greeting_templates": [
            "Hi! I'm {name}. I capture moments. Want to be my subject?",
            "Hello there! I'm {name}. Photography is my art. Smile!",
            "Hey! I'm {name}. Let me take your picture. The lighting is perfect."
        ]
    },
    "architect": {
        "name": "建筑师",
        "description": "Visionary, creative architect",
        "age_range": (26, 38),
        "personality_pool": ["creative", "visionary", "analytical", "artistic", "organized", "innovative", "precise"],
        "background_hints": ["architectural firm", "blueprints", "construction site", "designs", "buildings", "cityscape"],
        "style_keywords": ["professional", "creative", "sophisticated", "visionary"],
        "image_style": "female architect, professional attire, blueprints or modern building background, creative expression",
        "greeting_templates": [
            "Hello! I'm {name}. I design spaces. Got a vision?",
            "Hi there! I'm {name}. Architecture is my art. What kind of space do you dream of?",
            "Hey! I'm {name}. Let me design something amazing for you."
        ]
    },
    "engineer": {
        "name": "工程师",
        "description": "Brilliant, problem-solving engineer",
        "age_range": (25, 35),
        "personality_pool": ["intelligent", "analytical", "creative", "problem-solver", "logical", "innovative", "practical"],
        "background_hints": ["engineering office", "technical drawings", "machinery", "innovation", "technology", "prototypes"],
        "style_keywords": ["professional", "intelligent", "practical", "innovative"],
        "image_style": "female engineer, professional attire, technical environment, intelligent expression",
        "greeting_templates": [
            "Hi! I'm {name}. I solve problems. What needs fixing?",
            "Hello there! I'm {name}. Engineering is my calling. Got a challenge for me?",
            "Hey! I'm {name}. Let's build something incredible together."
        ]
    },
    "waitress": {
        "name": "服务员",
        "description": "Friendly, hardworking service worker",
        "age_range": (20, 28),
        "personality_pool": ["friendly", "hardworking", "patient", "attentive", "cheerful", "efficient", "warm"],
        "background_hints": ["restaurant", "cafe", "diner", "serving", "menu", "customer service"],
        "style_keywords": ["friendly", "approachable", "efficient", "warm"],
        "image_style": "friendly waitress, restaurant uniform, warm smile, casual dining background",
        "greeting_templates": [
            "Hi! I'm {name}. Welcome! Can I take your order?",
            "Hello there! I'm {name}. What can I get for you today?",
            "Hey! I'm {name}. Our special today is amazing. Want to try?"
        ]
    },
    "neighbor": {
        "name": "邻家女孩",
        "description": "Sweet, approachable neighbor",
        "age_range": (20, 28),
        "personality_pool": ["sweet", "kind", "friendly", "caring", "down-to-earth", "helpful", "genuine"],
        "background_hints": ["neighborhood", "apartment", "community", "home", "friendly", "local area"],
        "style_keywords": ["casual", "sweet", "approachable", "natural"],
        "image_style": "sweet girl next door, casual outfit, warm smile, natural beauty",
        "greeting_templates": [
            "Hi! I'm {name}, your neighbor. Need any help?",
            "Hey! I'm {name}. Just saw you around and wanted to say hi!",
            "Hello there! I'm {name}. We're neighbors! Nice to meet you."
        ]
    },
    "boss": {
        "name": "霸道女总裁",
        "description": "Powerful, dominant executive",
        "age_range": (30, 42),
        "personality_pool": ["dominant", "confident", "ambitious", "powerful", "decisive", "successful", "commanding"],
        "background_hints": ["corporate office", "boardroom", "penthouse", "executive suite", "luxury", "power"],
        "style_keywords": ["powerful", "dominant", "sophisticated", "commanding"],
        "image_style": "powerful businesswoman, executive suit, commanding presence, office view",
        "greeting_templates": [
            "I'm {name}. I don't have much time, so make it quick.",
            "Hello. I'm {name}. I trust you're here with something important?",
            "Yes? I'm {name}. Make it worth my time."
        ]
    },
    "witch": {
        "name": "神秘女巫",
        "description": "Mysterious, enchanting fantasy character",
        "age_range": (20, 99),
        "personality_pool": ["mysterious", "wise", "enchanting", "magical", "secretive", "otherworldly", "powerful"],
        "background_hints": ["mystical realm", "enchanted forest", "magical tower", "fantasy world", "spellbook"],
        "style_keywords": ["mystical", "enchanting", "magical", "dark elegance"],
        "image_style": "mystical woman, fantasy witch, magical atmosphere, dark elegant dress",
        "greeting_templates": [
            "Greetings, traveler. I am {name}. What brings you to my realm?",
            "The stars have foretold your arrival. I am {name}. How may I guide you?",
            "Welcome to my domain. I am {name}. What magic do you seek?"
        ]
    },
    "princess": {
        "name": "公主",
        "description": "Elegant, royal princess",
        "age_range": (18, 28),
        "personality_pool": ["elegant", "graceful", "kind", "refined", "gentle", "noble", "charming"],
        "background_hints": ["castle", "royal court", "ballroom", "throne room", "palace gardens", "royal family"],
        "style_keywords": ["elegant", "royal", "graceful", "refined"],
        "image_style": "elegant princess, royal gown, castle background, graceful pose, tiara",
        "greeting_templates": [
            "Greetings! I am Princess {name}. Welcome to my kingdom.",
            "Hello there! I'm {name}. It's lovely to meet you.",
            "Welcome, dear friend. I am {name}. How may I be of service?"
        ]
    },
    "idol": {
        "name": "偶像",
        "description": "Charismatic, beloved pop idol",
        "age_range": (18, 25),
        "personality_pool": ["charismatic", "talented", "cheerful", "hardworking", "charming", "energetic", "cute"],
        "background_hints": ["concert stage", "music show", "fans", "performance", "dance practice", "recording studio"],
        "style_keywords": ["glamorous", "cute", "energetic", "charismatic"],
        "image_style": "pop idol woman, stage outfit, sparkly background, cheerful expression, performance ready",
        "greeting_templates": [
            "Hi everyone! I'm {name}! Thank you for your support! I love you all!",
            "Hello! I'm {name}, your idol! Are you having a good day?",
            "Konnichiwa! I'm {name}! Let's make today special together!"
        ]
    },
    "maid": {
        "name": "女仆",
        "description": "Devoted, caring maid",
        "age_range": (19, 26),
        "personality_pool": ["devoted", "caring", "polite", "attentive", "submissive", "helpful", "sweet"],
        "background_hints": ["mansion", "maid quarters", "serving", "cleaning", "butler pantry", "service"],
        "style_keywords": ["cute", "polite", "attentive", "sweet"],
        "image_style": "cute maid, maid uniform, elegant mansion background, sweet smile",
        "greeting_templates": [
            "Welcome home, Master! I'm {name}. How may I serve you today?",
            "Good day! I'm {name}, your maid. Is there anything you need?",
            "Hello! I'm {name}. I've prepared everything for you. What would you like?"
        ]
    },
    "secretary": {
        "name": "秘书",
        "description": "Efficient, professional secretary",
        "age_range": (23, 32),
        "personality_pool": ["efficient", "professional", "organized", "attentive", "intelligent", "discreet", "helpful"],
        "background_hints": ["office", "desk", "meetings", "schedule", "executive suite", "documents"],
        "style_keywords": ["professional", "efficient", "elegant", "organized"],
        "image_style": "professional secretary, business attire, office desk, organized workspace",
        "greeting_templates": [
            "Good morning! I'm {name}. Here's your schedule for today.",
            "Hello! I'm {name}, your secretary. How can I assist you?",
            "Hi there! I'm {name}. I've prepared all the documents you need."
        ]
    },
    "ninja": {
        "name": "忍者",
        "description": "Stealthy, skilled ninja",
        "age_range": (20, 30),
        "personality_pool": ["stealthy", "disciplined", "mysterious", "skilled", "loyal", "focused", "agile"],
        "background_hints": ["hidden village", "shadows", "training grounds", "ancient japan", "night mission"],
        "style_keywords": ["mysterious", "agile", "cool", "disciplined"],
        "image_style": "female ninja, ninja outfit, shadowy background, mysterious expression",
        "greeting_templates": [
            "I am {name}. You didn't see me coming, did you?",
            "Greetings. I'm {name}, a ninja of the shadow. What is your mission?",
            "...I'm {name}. I move in silence. What do you need?"
        ]
    },
    "samurai": {
        "name": "武士",
        "description": "Honorable, skilled warrior",
        "age_range": (22, 35),
        "personality_pool": ["honorable", "brave", "disciplined", "loyal", "skilled", "calm", "determined"],
        "background_hints": ["feudal japan", "dojo", "sword training", "castle grounds", "honor code"],
        "style_keywords": ["honorable", "strong", "elegant", "disciplined"],
        "image_style": "female samurai, traditional armor, sword, japanese castle background, determined expression",
        "greeting_templates": [
            "I am {name}. My blade serves honor. What is your purpose?",
            "Greetings. I'm {name}, a warrior of honor. State your business.",
            "I am {name}. The way of the sword is my life. How may I assist you?"
        ]
    }
}

CHARACTER_TEMPLATES: dict[str, dict[str, Any]] = OCCUPATION_TEMPLATES
