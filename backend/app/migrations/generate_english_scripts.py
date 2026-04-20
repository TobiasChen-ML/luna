"""
Generate all scripts with full English content
Run: python -m app.migrations.generate_english_scripts
"""
import asyncio
import json
import os
import random
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import db

RELATION_TYPE_CONFIGS = {
    'boss_subordinate': {'name': 'Boss & Subordinate', 'category': 'Workplace'},
    'colleagues': {'name': 'Colleagues', 'category': 'Workplace'},
    'classmates': {'name': 'Classmates', 'category': 'Campus'},
    'childhood_friends': {'name': 'Childhood Friends', 'category': 'Special'},
    'enemies_to_lovers': {'name': 'Enemies to Lovers', 'category': 'Special'},
    'strangers_to_lovers': {'name': 'Strangers to Lovers', 'category': 'Special'},
    'doctor_patient': {'name': 'Doctor & Patient', 'category': 'Social'},
    'teacher_student': {'name': 'Teacher & Student', 'category': 'Campus'},
    'arranged_marriage': {'name': 'Arranged Marriage', 'category': 'Special'},
    'contract_lovers': {'name': 'Contract Lovers', 'category': 'Special'},
    'ex_lovers': {'name': 'Ex-Lovers', 'category': 'Special'},
    'first_love_reunion': {'name': 'First Love Reunion', 'category': 'Special'},
    'neighbors': {'name': 'Neighbors', 'category': 'Social'},
    'roommates': {'name': 'Roommates', 'category': 'Campus'},
    'partners': {'name': 'Partners', 'category': 'Workplace'},
    'savior': {'name': 'Savior', 'category': 'Special'},
    'bodyguard_employer': {'name': 'Bodyguard & Employer', 'category': 'Social'},
    'master_servant': {'name': 'Master & Servant', 'category': 'Special'},
    'idol_fan': {'name': 'Idol & Fan', 'category': 'Social'},
    'senior_junior': {'name': 'Senior & Junior', 'category': 'Campus'},
    'tutor_student': {'name': 'Tutor & Student', 'category': 'Social'},
    'fake_lovers': {'name': 'Fake Lovers', 'category': 'Special'},
    'online_lovers': {'name': 'Online Lovers', 'category': 'Special'},
    'affair': {'name': 'Secret Affair', 'category': 'Special'},
    'principal_student': {'name': 'Principal & Student', 'category': 'Campus'},
    'homeroom_teacher_student': {'name': 'Homeroom Teacher & Student', 'category': 'Campus'},
    'grade_director_student': {'name': 'Grade Director & Student', 'category': 'Campus'},
    'dean_student': {'name': 'Dean & Student', 'category': 'Campus'},
    'discipline_master_student': {'name': 'Discipline Master & Student', 'category': 'Campus'},
    'dorm_manager_student': {'name': 'Dorm Manager & Student', 'category': 'Campus'},
    'aunt_paternal_nephew': {'name': 'Aunt & Nephew', 'category': 'Family'},
    'uncle_maternal_niece': {'name': 'Uncle & Niece', 'category': 'Family'},
    'aunt_maternal_nephew': {'name': 'Aunt & Nephew', 'category': 'Family'},
    'uncle_paternal_niece': {'name': 'Uncle & Niece', 'category': 'Family'},
    'aunt_paternal_niece': {'name': 'Aunt & Nephew', 'category': 'Family'},
    'stepsister_stepbrother': {'name': 'Stepsiblings', 'category': 'Family'},
    'sister_in_law': {'name': 'Sister-in-Law', 'category': 'Family'},
    'classmate_mother': {'name': "Classmate's Mother", 'category': 'Social'},
    'classmate_sister': {'name': "Classmate's Sister", 'category': 'Social'},
    'friend_sister': {'name': "Friend's Sister", 'category': 'Social'},
    'friend_older_sister': {'name': "Friend's Older Sister", 'category': 'Social'},
    'friend_mother': {'name': "Friend's Mother", 'category': 'Social'},
    'friend_brother': {'name': "Friend's Brother", 'category': 'Social'},
    'doctor_nurse': {'name': 'Doctor & Nurse', 'category': 'Social'},
    'nurse_patient': {'name': 'Nurse & Patient', 'category': 'Social'},
    'director_actor': {'name': 'Director & Actor', 'category': 'Social'},
    'convenience_store_owner': {'name': 'Store Owner & Customer', 'category': 'Social'},
    'bakery_owner_customer': {'name': 'Bakery Owner & Customer', 'category': 'Social'},
}

EMOTION_TONES = ['sweet', 'angst', 'healing', 'comedy', 'dark', 'suspense', 'revenge', 'ethical', 'rebirth', 'thriller']
ERAS = ['modern_urban', 'modern_campus', 'ancient_palace', 'ancient_jianghu', 'republic_era', 'fantasy_realm', 'scifi_future']

SURFACE_TRAITS = ['cold', 'stern', 'arrogant', 'shy', 'domineering', 'cheerful', 'aloof', 'sarcastic', 'nervous', 'confident']
TRUE_TRAITS = ['gentle', 'vulnerable', 'caring', 'passionate', 'lonely', 'playful', 'romantic', 'protective', 'insecure', 'devoted']

PROFESSIONS = {
    'modern_urban': ['CEO', 'doctor', 'lawyer', 'chef', 'writer', 'artist', 'musician', 'athlete', 'detective', 'programmer'],
    'modern_campus': ['student', 'professor', 'teacher', 'counselor', 'coach'],
    'ancient_palace': ['emperor', 'prince', 'princess', 'general', 'minister', 'concubine', 'guard', 'physician'],
    'ancient_jianghu': ['swordsman', 'assassin', 'sect_leader', 'healer', 'merchant', 'noble'],
    'republic_era': ['warlord', 'singer', 'spy', 'businessman', 'student', 'journalist'],
    'fantasy_realm': ['mage', 'knight', 'elf', 'dragon_rider', 'sorcerer', 'fairy'],
    'scifi_future': ['captain', 'pilot', 'scientist', 'AI', 'bounty_hunter', 'rebel'],
}

FIRST_NAMES_MALE = ['Alexander', 'James', 'Michael', 'David', 'William', 'Daniel', 'Christopher', 'Matthew', 'Andrew', 'Joshua', 'Ryan', 'Brandon', 'Justin', 'Kevin', 'Tyler']
FIRST_NAMES_FEMALE = ['Emma', 'Olivia', 'Sophia', 'Isabella', 'Mia', 'Charlotte', 'Amelia', 'Harper', 'Evelyn', 'Abigail', 'Emily', 'Elizabeth', 'Samantha', 'Victoria', 'Grace']
LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Anderson', 'Taylor', 'Thomas', 'Moore', 'Jackson']

PROGRESSION_TEMPLATES = [
    {'start': 'Your paths cross unexpectedly', 'build': 'You begin to see a different side of them', 'climax': 'The tension becomes undeniable', 'resolve': 'You cross a line there is no coming back from'},
    {'start': 'Circumstances force you together', 'build': 'The walls between you start to crack', 'climax': 'Neither of you can deny the truth anymore', 'resolve': 'You decide to embrace what is forbidden'},
    {'start': 'What begins as a simple arrangement', 'build': 'The lines between duty and desire blur', 'climax': 'One moment changes everything', 'resolve': 'You choose each other despite the consequences'},
    {'start': 'You never expected to feel this way', 'build': 'Every interaction becomes charged with meaning', 'climax': 'The truth spills out', 'resolve': 'You step into the unknown together'},
]

KEY_NODE_NAMES = ['First Encounter', 'Misunderstanding', 'Growing Closer', 'Realization', 'Testing the Waters', 'Confession', 'Hesitation', 'Decision', 'Crisis', 'Resolution']

KEY_NODE_DESCRIPTIONS = [
    'The moment your eyes meet, something shifts in the air',
    'A misunderstanding creates distance, but also reveals hidden feelings',
    'You find yourselves seeking each other out more often',
    'You realize this is more than just attraction',
    'A moment of vulnerability tests the waters between you',
    'Words are finally spoken that cannot be taken back',
    'Doubts creep in about whether this is right',
    'A choice must be made, and there is no turning back',
    'External forces threaten to tear you apart',
    'Through everything, you find your way back to each other',
]

ENDING_GOOD = [
    'Against all odds, you find happiness together, cherishing every stolen moment',
    'You choose love over convention, building a life that is uniquely yours',
    'The world may not understand, but you have each other, and that is enough',
]

ENDING_NEUTRAL = [
    'You both step back, uncertain, but the connection remains, waiting for the right time',
    'The future is unclear, but the bond between you cannot be easily broken',
    'Neither of you is ready to take the final step, yet neither can truly let go',
]

ENDING_BAD = [
    'Circumstances force you apart, leaving only bittersweet memories of what could have been',
    'The weight of everything becomes too much, and you let go with heavy hearts',
    'Some loves are not meant to last, but the lessons remain forever',
]

ENDING_SECRET = [
    'You keep your love hidden, a precious secret that only the two of you share',
    'In the shadows, you build a world that is yours alone',
    'Perhaps in another life, you could be open about what you mean to each other',
]


def generate_name(gender: str) -> str:
    first_names = FIRST_NAMES_MALE if gender == 'male' else FIRST_NAMES_FEMALE
    return f"{random.choice(first_names)} {random.choice(LAST_NAMES)}"


def generate_script(relation_type: str, config: dict, index: int) -> dict:
    char_gender = 'male_char' if random.random() > 0.3 else 'female_char'
    name = generate_name(char_gender.replace('_char', ''))
    
    surface = random.choice(SURFACE_TRAITS)
    truth = random.choice(TRUE_TRAITS)
    progression = random.choice(PROGRESSION_TEMPLATES)
    
    era = random.choice(ERAS)
    profession = random.choice(PROFESSIONS.get(era, ['business']))
    emotion_tone = random.choice(EMOTION_TONES)
    
    title = f"{name}'s Secret"
    title_en = title
    summary = f"A {config['name']} story. On the surface, they seem {surface}, but beneath lies someone who is {truth}. Only you can see who they really are."
    
    num_key_nodes = random.randint(3, 6)
    selected_indices = sorted(random.sample(range(len(KEY_NODE_NAMES)), num_key_nodes))
    key_nodes = [
        {
            'name': KEY_NODE_NAMES[i],
            'description': KEY_NODE_DESCRIPTIONS[i],
            'trigger': f'Triggers when affection reaches {30 + i * 15}%'
        }
        for i in selected_indices
    ]
    
    script_seed = {
        'character': {
            'name': '{{character_name}}',
            'age': random.randint(22, 40),
            'surface_identity': surface,
            'true_identity': truth,
            'profession': profession,
        },
        'contrast': {
            'surface': surface,
            'truth': truth,
            'hook': f'Only you can make them show their {truth} side',
        },
        'progression': {
            'start': progression['start'],
            'build': progression['build'],
            'climax': progression['climax'],
            'resolve': progression['resolve'],
        },
        'key_nodes': key_nodes,
        'endings': {
            'good': random.choice(ENDING_GOOD),
            'neutral': random.choice(ENDING_NEUTRAL),
            'bad': random.choice(ENDING_BAD),
            'secret': random.choice(ENDING_SECRET),
        }
    }
    
    full_script = {
        'prologue': f"You are {{{{character_name}}}}, someone who appears {surface} to the world. But inside, you are {truth}. When you meet them, something begins to change...",
        'opening_scene': progression['start'],
        'character_inner_state': {
            'initial': f'Outwardly {surface}, inwardly {truth}',
            'development': 'As the story progresses, your feelings grow harder to hide',
            'climax': 'You can no longer deny what you feel',
        },
        'narrative_beats': [
            {'scene': progression['start'], 'emotion': 'anticipation', 'hint': 'Pay attention to small details'},
            {'scene': progression['build'], 'emotion': 'growing attachment', 'hint': 'Notice how they look at you'},
            {'scene': progression['climax'], 'emotion': 'heart racing', 'hint': 'This moment will define everything'},
            {'scene': progression['resolve'], 'emotion': 'warmth', 'hint': 'The choice is yours'},
        ],
        'dialogue_hints': {
            'style': f'Speak in a way that reflects {surface} exterior with {truth} undertones',
            'key_phrases': [
                '"I have never shown this side to anyone..."',
                '"We should not be doing this..."',
                '"Do not tell anyone about this..."',
            ],
        },
        'branching_points': [
            {
                'trigger': key_nodes[0]['trigger'] if key_nodes else 'When affection reaches 30%',
                'choices': [
                    {'text': 'Respond warmly', 'effect': 'Affection +20, enter romantic path'},
                    {'text': 'Keep your distance', 'effect': 'Affection -10, stay guarded'},
                ]
            },
            {
                'trigger': key_nodes[-1]['trigger'] if key_nodes and len(key_nodes) > 1 else 'When affection reaches 60%',
                'choices': [
                    {'text': 'Confess your feelings', 'effect': 'Enter relationship ending'},
                    {'text': 'Suppress your emotions', 'effect': 'Enter secret longing ending'},
                ]
            }
        ],
    }
    
    emotion_tones = [emotion_tone]
    if random.random() > 0.5:
        emotion_tones.append(random.choice([t for t in EMOTION_TONES if t != emotion_tone]))
    
    script_id = f"script_{relation_type}_{index:04d}"
    
    return {
        'id': script_id,
        'title': title,
        'title_en': title_en,
        'summary': summary,
        'emotion_tones': json.dumps(emotion_tones),
        'relation_types': json.dumps([relation_type]),
        'contrast_types': json.dumps(['identity', 'personality']),
        'era': era,
        'gender_target': 'female' if char_gender == 'male_char' else 'male',
        'character_gender': char_gender,
        'profession': profession,
        'length': random.choice(['short', 'medium', 'long']),
        'age_rating': 'mature',
        'contrast_surface': f'Appears {surface}',
        'contrast_truth': f'Actually {truth}',
        'contrast_hook': f'Only you can see their {truth} side',
        'script_seed': json.dumps(script_seed),
        'full_script': json.dumps(full_script),
        'status': 'published'
    }


async def generate_scripts():
    await db.connect()
    
    print("Clearing existing scripts...")
    await db.execute("DELETE FROM script_library")
    
    scripts_per_type = 25
    total_generated = 0
    now = datetime.utcnow().isoformat()
    
    for relation_type, config in RELATION_TYPE_CONFIGS.items():
        print(f"Generating {scripts_per_type} scripts for {config['name']}...")
        
        for i in range(scripts_per_type):
            script = generate_script(relation_type, config, i + 1)
            
            try:
                await db.execute(
                    """INSERT INTO script_library 
                       (id, title, title_en, summary, emotion_tones, relation_types, 
                        contrast_types, era, gender_target, character_gender, profession,
                        length, age_rating, contrast_surface, contrast_truth, contrast_hook,
                        script_seed, full_script, status, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        script['id'], script['title'], script['title_en'], script['summary'],
                        script['emotion_tones'], script['relation_types'], script['contrast_types'],
                        script['era'], script['gender_target'], script['character_gender'],
                        script['profession'], script['length'], script['age_rating'],
                        script['contrast_surface'], script['contrast_truth'], script['contrast_hook'],
                        script['script_seed'], script['full_script'], script['status'], now, now
                    )
                )
                total_generated += 1
            except Exception as e:
                print(f"Error: {e}")
    
    count = await db.execute("SELECT COUNT(*) as count FROM script_library", fetch=True)
    print(f"\nDone! Total scripts: {count['count']}")


if __name__ == "__main__":
    asyncio.run(generate_scripts())
