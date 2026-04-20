"""
Generate more script seeds to reach 1000 total
Run: python -m app.migrations.generate_more_scripts
"""
import asyncio
import json
import os
import random
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import db

EMOTION_TONES = ['sweet', 'angst', 'healing', 'comedy', 'dark', 'suspense', 'revenge', 'ethical', 'rebirth', 'harem', 'thriller']

RELATION_TYPES = [
    'boss_subordinate', 'colleagues', 'classmates', 'childhood_friends', 'enemies_to_lovers',
    'strangers_to_lovers', 'doctor_patient', 'teacher_student', 'arranged_marriage',
    'contract_lovers', 'ex_lovers', 'first_love_reunion', 'neighbors', 'roommates',
    'partners', 'savior', 'bodyguard_employer', 'master_servant', 'idol_fan',
    'senior_junior', 'tutor_student', 'fake_lovers', 'online_lovers', 'affair',
    'principal_student', 'homeroom_teacher_student', 'grade_director_student',
    'dean_student', 'discipline_master_student', 'dorm_manager_student',
    'professor_student', 'ta_student', 'aunt_paternal_nephew', 'uncle_maternal_niece',
    'aunt_maternal_nephew', 'uncle_paternal_niece', 'aunt_paternal_niece',
    'stepsister_stepbrother', 'sister_in_law', 'stepmother_stepson', 'stepfather_stepdaughter',
    'classmate_mother', 'classmate_sister', 'friend_sister', 'friend_older_sister',
    'friend_mother', 'friend_brother', 'doctor_nurse', 'nurse_patient',
    'director_actor', 'convenience_store_owner', 'bakery_owner_customer',
    'mother_in_law_son_in_law', 'father_in_law_daughter_in_law', 'older_sister_younger_brother',
    'older_brother_younger_sister', 'counselor_student', 'school_nurse_student',
    'landlord_tenant', 'streamer_viewer', 'coach_trainee'
]

ERAS = [
    'modern_urban', 'modern_campus', 'ancient_palace', 'ancient_jianghu', 'ancient_xianxia',
    'fantasy_demon', 'fantasy_dragon', 'fantasy_elf', 'fantasy_isekai', 'fantasy_youkai',
    'fantasy_phoenix', 'future_cyberpunk', 'future_space', 'future_virtual', 'future_mecha',
    'future_apocalypse', 'republic_concession', 'republic_warlord'
]

CHARACTER_GENDERS = ['male_char', 'female_char']

PROFESSIONS = {
    'modern_urban': ['business', 'doctor', 'lawyer', 'celebrity', 'chef', 'writer', 'artist', 'musician', 'athlete', 'detective', 'journalist', 'architect', 'programmer', 'model', 'photographer'],
    'modern_campus': ['student', 'professor', 'athlete', 'musician', 'artist', 'tutor', 'researcher'],
    'ancient_palace': ['emperor', 'prince', 'princess', 'general', 'minister', 'concubine', 'guard', 'physician', 'scholar'],
    'ancient_jianghu': ['swordsman', 'assassin', 'sect_leader', 'healer', 'merchant', 'noble', 'spy'],
    'ancient_xianxia': ['cultivator', 'demon_lord', 'fairy', 'elder', 'disciple', 'alchemist'],
    'fantasy_demon': ['demon_lord', 'demon_hunter', 'half_demon', 'sorcerer', 'priest'],
    'fantasy_dragon': ['dragon_king', 'dragon_knight', 'dragon_hunter', 'princess', 'sorcerer'],
    'fantasy_elf': ['elf_prince', 'elf_warrior', 'mage', 'ranger', 'healer'],
    'fantasy_isekai': ['hero', 'demon_king', 'sage', 'knight', 'merchant', 'adventurer'],
    'fantasy_youkai': ['youkai_lord', 'exorcist', 'half_youkai', 'shrine_maiden', 'samurai'],
    'fantasy_phoenix': ['phoenix_king', 'fire_mage', 'warrior', 'priest', 'princess'],
    'future_cyberpunk': ['hacker', 'corporate', 'mercenary', 'doctor', 'detective', 'rebel', 'ai', 'bounty_hunter'],
    'future_space': ['captain', 'pilot', 'scientist', 'alien', 'soldier', 'trader', 'explorer'],
    'future_virtual': ['developer', 'player', 'ai', 'moderator', 'streamer', 'tester'],
    'future_mecha': ['pilot', 'engineer', 'commander', 'scientist', 'soldier'],
    'future_apocalypse': ['survivor', 'soldier', 'scientist', 'leader', 'scavenger', 'healer'],
    'republic_concession': ['warlord', 'singer', 'spy', 'businessman', 'student', 'journalist', 'revolutionary'],
    'republic_warlord': ['warlord', 'general', 'spy', 'doctor', 'student', 'journalist', 'noble']
}

TITLE_TEMPLATES = {
    'sweet': [
        ('{name}的秘密', "{name}'s Secret"),
        ('温柔{title}', "Gentle {title}"),
        ('{name}的告白', "{name}'s Confession"),
        ('恋爱{title}', "Love {title}"),
    ],
    'angst': [
        ('{name}的眼泪', "{name}'s Tears"),
        ('错过的{title}', "Missed {title}"),
        ('{name}的挣扎', "{name}'s Struggle"),
        ('痛苦{title}', "Painful {title}"),
    ],
    'healing': [
        ('治愈{title}', "Healing {title}"),
        ('{name}的温柔', "{name}'s Gentleness"),
        ('重生{title}', "Reborn {title}"),
    ],
    'comedy': [
        ('搞笑{title}', "Funny {title}"),
        ('{name}的日常', "{name}'s Daily Life"),
        ('爆笑{title}', "Hilarious {title}"),
    ],
    'dark': [
        ('黑暗{title}', "Dark {title}"),
        ('{name}的深渊', "{name}'s Abyss"),
        ('堕落{title}', "Fallen {title}"),
    ],
    'suspense': [
        ('悬疑{title}', "Suspenseful {title}"),
        ('{name}的秘密', "{name}'s Secret"),
        ('真相{title}', "The Truth {title}"),
    ],
    'revenge': [
        ('复仇{title}', "Revenge {title}"),
        ('{name}的复仇', "{name}'s Revenge"),
        ('归来{title}', "Return {title}"),
    ],
}

CONTRAST_TEMPLATES = [
    ("表面{surface}，实际{truth}", "Secretly {truth} despite appearing {surface}", "只有你能看到{truth}的一面"),
    ("对外{surface}，对你{truth}", "{surface} to others, {truth} to you", "你的专属{truth}"),
    ("人前{surface}，人后{truth}", "{surface} in public, {truth} in private", "私下里的{truth}"),
]

SURFACE_TRAITS = ['冷漠', '温柔', '霸道', '傲娇', '腹黑', '阳光', '高冷', '毒舌', '害羞', '强势']
TRUTH_TRAITS = ['温柔', '脆弱', '可爱', '深情', '霸道', '害羞', '善良', '体贴', '孤独', '渴望爱']

NAMES_MALE = ['陆', '沈', '顾', '江', '傅', '霍', '谢', '萧', '叶', '温', '苏', '楚', '秦', '楚', '薄', '商', '谢', '裴', '霍', '晏']
NAMES_FEMALE = ['苏', '沈', '顾', '林', '叶', '江', '温', '楚', '秦', '白', '宋', '唐', '陈', '许', '周', '夏', '安', '姜', '乔', '季']

TITLE_WORDS = ['恋人', '契约', '秘密', '守护', '遇见', '心动', '约定', '命运', '心动', '温柔']


def generate_name(gender: str) -> str:
    surnames = NAMES_MALE if gender == 'male_char' else NAMES_FEMALE
    name_chars = '晨暮雪晴雨涵梓萱逸然'
    return random.choice(surnames) + ''.join([random.choice(name_chars) for _ in range(random.randint(1, 2))])


def generate_script(index: int) -> dict:
    era = random.choice(ERAS)
    emotion_tone = random.choice(EMOTION_TONES)
    relation_type = random.choice(RELATION_TYPES)
    character_gender = random.choice(CHARACTER_GENDERS)
    profession = random.choice(PROFESSIONS.get(era, ['business']))
    
    name = generate_name(character_gender.replace('_char', ''))
    title_word = random.choice(TITLE_WORDS)
    
    template = random.choice(TITLE_TEMPLATES.get(emotion_tone, TITLE_TEMPLATES['sweet']))
    title = template[0].format(name=name, title=title_word)
    title_en = template[1].format(name=name, title=title_word)
    
    contrast = random.choice(CONTRAST_TEMPLATES)
    surface = random.choice(SURFACE_TRAITS)
    truth = random.choice(TRUTH_TRAITS)
    
    contrast_surface = contrast[0].format(surface=surface, truth=truth)
    contrast_truth = contrast[1].format(surface=surface, truth=truth)
    contrast_hook = contrast[2].format(truth=truth)
    
    summary = f"{emotion_tone}风格的{relation_type}故事"
    
    emotion_tones = [emotion_tone]
    if random.random() > 0.5:
        emotion_tones.append(random.choice([t for t in EMOTION_TONES if t != emotion_tone]))
    
    relation_types = [relation_type]
    if random.random() > 0.6:
        relation_types.append(random.choice([t for t in RELATION_TYPES if t != relation_type]))
    
    script_id = f"auto_{index:04d}"
    
    return {
        'id': script_id,
        'title': title,
        'title_en': title_en,
        'summary': summary,
        'emotion_tones': json.dumps(emotion_tones, ensure_ascii=False),
        'relation_types': json.dumps(relation_types, ensure_ascii=False),
        'contrast_types': json.dumps(['identity', 'personality'], ensure_ascii=False),
        'era': era,
        'gender_target': 'female' if character_gender == 'male_char' else 'male',
        'character_gender': character_gender,
        'profession': profession,
        'length': random.choice(['short', 'medium', 'long']),
        'age_rating': random.choice(['all', 'mature']),
        'contrast_surface': contrast_surface,
        'contrast_truth': contrast_truth,
        'contrast_hook': contrast_hook,
        'script_seed': json.dumps({
            'character': {'name': '{{character_name}}', 'profession': profession},
            'generated': True
        }, ensure_ascii=False),
        'status': 'published'
    }


async def generate_scripts():
    await db.connect()
    
    count_result = await db.execute("SELECT COUNT(*) as count FROM script_library", fetch=True)
    current_count = count_result['count'] if count_result else 0
    target = 1000
    to_generate = target - current_count
    
    print(f"Current scripts: {current_count}")
    print(f"Need to generate: {to_generate}")
    
    if to_generate <= 0:
        print("Already have enough scripts!")
        return
    
    batch_size = 100
    generated = 0
    
    for batch_start in range(0, to_generate, batch_size):
        batch_count = min(batch_size, to_generate - batch_start)
        scripts = []
        
        for i in range(batch_count):
            script = generate_script(current_count + batch_start + i + 1)
            scripts.append(script)
        
        for script in scripts:
            now = datetime.utcnow().isoformat()
            await db.execute(
                """INSERT OR REPLACE INTO script_library 
                   (id, title, title_en, summary, emotion_tones, relation_types, 
                    contrast_types, era, gender_target, character_gender, profession,
                    length, age_rating, contrast_surface, contrast_truth, contrast_hook,
                    script_seed, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    script['id'], script['title'], script['title_en'], script['summary'],
                    script['emotion_tones'], script['relation_types'], script['contrast_types'],
                    script['era'], script['gender_target'], script['character_gender'],
                    script['profession'], script['length'], script['age_rating'],
                    script['contrast_surface'], script['contrast_truth'], script['contrast_hook'],
                    script['script_seed'], script['status'], now, now
                )
            )
        
        generated += batch_count
        print(f"Generated {generated}/{to_generate} scripts...")
    
    final_count = await db.execute("SELECT COUNT(*) as count FROM script_library", fetch=True)
    print(f"Done! Total scripts: {final_count['count']}")


if __name__ == "__main__":
    asyncio.run(generate_scripts())
