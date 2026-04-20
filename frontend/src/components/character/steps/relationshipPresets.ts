export type RelationshipCategory =
  | 'Romantic'
  | 'Professional'
  | 'Fantasy'
  | 'Everyday'
  | 'Friends'
  | 'Adventure'
  | 'Power'
  | 'Supernatural';

export interface RelationshipPreset {
  id: string;
  characterRole: string;
  userRole: string;
  defaultTone: string;
  category: RelationshipCategory;
}

export const RELATIONSHIP_PRESETS: RelationshipPreset[] = [
  // ── Romantic ──────────────────────────────────────────────────────────────
  { id: 'r01', characterRole: 'Girlfriend',        userRole: 'Boyfriend',        defaultTone: 'sweet',     category: 'Romantic' },
  { id: 'r02', characterRole: 'Boyfriend',         userRole: 'Girlfriend',        defaultTone: 'sweet',     category: 'Romantic' },
  { id: 'r03', characterRole: 'Wife',              userRole: 'Husband',           defaultTone: 'sweet',     category: 'Romantic' },
  { id: 'r04', characterRole: 'Husband',           userRole: 'Wife',              defaultTone: 'sweet',     category: 'Romantic' },
  { id: 'r05', characterRole: 'Fiancée',           userRole: 'Fiancé',            defaultTone: 'sweet',     category: 'Romantic' },
  { id: 'r06', characterRole: 'Secret Admirer',    userRole: 'Crush',             defaultTone: 'teasing',   category: 'Romantic' },
  { id: 'r07', characterRole: 'Childhood Sweetheart', userRole: 'Childhood Friend', defaultTone: 'sweet',  category: 'Romantic' },
  { id: 'r08', characterRole: 'Ex-Girlfriend',     userRole: 'Ex-Boyfriend',      defaultTone: 'cold',      category: 'Romantic' },
  { id: 'r09', characterRole: 'Long-Distance Lover', userRole: 'Partner',         defaultTone: 'sweet',     category: 'Romantic' },
  { id: 'r10', characterRole: 'Soulmate',          userRole: 'Soulmate',          defaultTone: 'sweet',     category: 'Romantic' },
  { id: 'r11', characterRole: 'Tsundere Crush',    userRole: 'Oblivious Target',  defaultTone: 'teasing',   category: 'Romantic' },
  { id: 'r12', characterRole: 'Yandere Lover',     userRole: 'Beloved',           defaultTone: 'dominant',  category: 'Romantic' },
  { id: 'teen', characterRole: 'Kuudere Partner',   userRole: 'Devoted Partner',   defaultTone: 'cold',      category: 'Romantic' },

  // ── Professional ──────────────────────────────────────────────────────────
  { id: 'p01', characterRole: 'Boss',              userRole: 'Employee',          defaultTone: 'dominant',  category: 'Professional' },
  { id: 'p02', characterRole: 'Manager',           userRole: 'Subordinate',       defaultTone: 'dominant',  category: 'Professional' },
  { id: 'p03', characterRole: 'CEO',               userRole: 'Personal Assistant',defaultTone: 'dominant',  category: 'Professional' },
  { id: 'p04', characterRole: 'Director',          userRole: 'Intern',            defaultTone: 'dominant',  category: 'Professional' },
  { id: 'p05', characterRole: 'Mentor',            userRole: 'Mentee',            defaultTone: 'supportive',category: 'Professional' },
  { id: 'p06', characterRole: 'Senior Colleague',  userRole: 'Junior Colleague',  defaultTone: 'supportive',category: 'Professional' },
  { id: 'p07', characterRole: 'Professor',         userRole: 'Student',           defaultTone: 'supportive',category: 'Professional' },
  { id: 'p08', characterRole: 'Teacher',           userRole: 'Student',           defaultTone: 'supportive',category: 'Professional' },
  { id: 'p09', characterRole: 'Coach',             userRole: 'Athlete',           defaultTone: 'supportive',category: 'Professional' },
  { id: 'p10', characterRole: 'Personal Trainer',  userRole: 'Client',            defaultTone: 'supportive',category: 'Professional' },
  { id: 'p11', characterRole: 'Tutor',             userRole: 'Student',           defaultTone: 'supportive',category: 'Professional' },
  { id: 'p12', characterRole: 'Music Teacher',     userRole: 'Pupil',             defaultTone: 'supportive',category: 'Professional' },
  { id: 'p13', characterRole: 'Fashion Designer',  userRole: 'Model',             defaultTone: 'dominant',  category: 'Professional' },
  { id: 'p14', characterRole: 'Agent',             userRole: 'Talent',            defaultTone: 'dominant',  category: 'Professional' },
  { id: 'p15', characterRole: 'Therapist',         userRole: 'Client',            defaultTone: 'supportive',category: 'Professional' },

  // ── Fantasy ───────────────────────────────────────────────────────────────
  { id: 'f01', characterRole: 'Princess',          userRole: 'Knight',            defaultTone: 'sweet',     category: 'Fantasy' },
  { id: 'f02', characterRole: 'Queen',             userRole: 'Royal Guard',        defaultTone: 'dominant',  category: 'Fantasy' },
  { id: 'f03', characterRole: 'Empress',           userRole: 'Vassal',            defaultTone: 'dominant',  category: 'Fantasy' },
  { id: 'f04', characterRole: 'Maid',              userRole: 'Master',            defaultTone: 'sweet',     category: 'Fantasy' },
  { id: 'f05', characterRole: 'Butler',            userRole: 'Lady of the House', defaultTone: 'sweet',     category: 'Fantasy' },
  { id: 'f06', characterRole: 'Witch',             userRole: 'Apprentice',        defaultTone: 'dominant',  category: 'Fantasy' },
  { id: 'f07', characterRole: 'Sorceress',         userRole: 'Seeker',            defaultTone: 'mysterious',category: 'Fantasy' },
  { id: 'f08', characterRole: 'Elf',               userRole: 'Adventurer',        defaultTone: 'friendly',  category: 'Fantasy' },
  { id: 'f09', characterRole: 'Dragon Rider',      userRole: 'Tamer',             defaultTone: 'dominant',  category: 'Fantasy' },
  { id: 'f10', characterRole: 'Noble Lady',        userRole: 'Retainer',          defaultTone: 'dominant',  category: 'Fantasy' },
  { id: 'f11', characterRole: 'Warrior Princess',  userRole: 'Companion',         defaultTone: 'friendly',  category: 'Fantasy' },
  { id: 'f12', characterRole: 'Healer',            userRole: 'Warrior',           defaultTone: 'supportive',category: 'Fantasy' },
  { id: 'f13', characterRole: 'Villain',           userRole: 'Hero',              defaultTone: 'dominant',  category: 'Fantasy' },
  { id: 'f14', characterRole: 'Idol',              userRole: 'Fan',               defaultTone: 'teasing',   category: 'Fantasy' },
  { id: 'f15', characterRole: 'Samurai',           userRole: 'Lord',              defaultTone: 'dominant',  category: 'Fantasy' },

  // ── Everyday ──────────────────────────────────────────────────────────────
  { id: 'e01', characterRole: 'Neighbor',          userRole: 'Neighbor',          defaultTone: 'friendly',  category: 'Everyday' },
  { id: 'e02', characterRole: 'Barista',           userRole: 'Regular',           defaultTone: 'friendly',  category: 'Everyday' },
  { id: 'e03', characterRole: 'Doctor',            userRole: 'Patient',           defaultTone: 'supportive',category: 'Everyday' },
  { id: 'e04', characterRole: 'Nurse',             userRole: 'Patient',           defaultTone: 'supportive',category: 'Everyday' },
  { id: 'e05', characterRole: 'Chef',              userRole: 'Diner',             defaultTone: 'friendly',  category: 'Everyday' },
  { id: 'e06', characterRole: 'Librarian',         userRole: 'Visitor',           defaultTone: 'friendly',  category: 'Everyday' },
  { id: 'e07', characterRole: 'Florist',           userRole: 'Customer',          defaultTone: 'sweet',     category: 'Everyday' },
  { id: 'e08', characterRole: 'Landlady',          userRole: 'Tenant',            defaultTone: 'friendly',  category: 'Everyday' },
  { id: 'e09', characterRole: 'Yoga Instructor',   userRole: 'Student',           defaultTone: 'supportive',category: 'Everyday' },
  { id: 'e10', characterRole: 'Bakery Owner',      userRole: 'Regular',           defaultTone: 'sweet',     category: 'Everyday' },
  { id: 'e11', characterRole: 'Bookstore Clerk',   userRole: 'Bookworm',          defaultTone: 'friendly',  category: 'Everyday' },
  { id: 'e12', characterRole: 'Roommate',          userRole: 'Roommate',          defaultTone: 'friendly',  category: 'Everyday' },
  { id: 'e13', characterRole: 'Convenience Store Clerk', userRole: 'Regular',    defaultTone: 'friendly',  category: 'Everyday' },
  { id: 'e14', characterRole: 'Vet',               userRole: 'Pet Owner',         defaultTone: 'supportive',category: 'Everyday' },
  { id: 'e15', characterRole: 'Stylist',           userRole: 'Client',            defaultTone: 'friendly',  category: 'Everyday' },

  // ── Friends ───────────────────────────────────────────────────────────────
  { id: 'fr01', characterRole: 'Best Friend',       userRole: 'Best Friend',       defaultTone: 'friendly',  category: 'Friends' },
  { id: 'fr02', characterRole: 'Big Sister',        userRole: 'Little Brother',    defaultTone: 'sweet',     category: 'Friends' },
  { id: 'fr03', characterRole: 'Big Brother',       userRole: 'Little Sister',     defaultTone: 'sweet',     category: 'Friends' },
  { id: 'fr04', characterRole: 'Childhood Friend',  userRole: 'Childhood Friend',  defaultTone: 'friendly',  category: 'Friends' },
  { id: 'fr05', characterRole: 'Study Buddy',       userRole: 'Study Buddy',       defaultTone: 'friendly',  category: 'Friends' },
  { id: 'fr06', characterRole: 'Classmate',         userRole: 'Classmate',         defaultTone: 'friendly',  category: 'Friends' },
  { id: 'fr07', characterRole: 'Gym Buddy',         userRole: 'Gym Buddy',         defaultTone: 'friendly',  category: 'Friends' },
  { id: 'fr08', characterRole: 'Online Friend',     userRole: 'Online Friend',     defaultTone: 'friendly',  category: 'Friends' },
  { id: 'fr09', characterRole: 'Pen Pal',           userRole: 'Pen Pal',           defaultTone: 'sweet',     category: 'Friends' },
  { id: 'fr10', characterRole: 'Travel Companion',  userRole: 'Travel Companion',  defaultTone: 'friendly',  category: 'Friends' },
  { id: 'fr11', characterRole: 'Gaming Partner',    userRole: 'Gaming Partner',    defaultTone: 'teasing',   category: 'Friends' },

  // ── Adventure ─────────────────────────────────────────────────────────────
  { id: 'a01', characterRole: 'Guardian',           userRole: 'Ward',              defaultTone: 'supportive',category: 'Adventure' },
  { id: 'a02', characterRole: 'Bodyguard',          userRole: 'VIP',               defaultTone: 'dominant',  category: 'Adventure' },
  { id: 'a03', characterRole: 'Detective',          userRole: 'Partner',           defaultTone: 'friendly',  category: 'Adventure' },
  { id: 'a04', characterRole: 'Spy',                userRole: 'Handler',           defaultTone: 'cold',      category: 'Adventure' },
  { id: 'a05', characterRole: 'Soldier',            userRole: 'Commander',         defaultTone: 'dominant',  category: 'Adventure' },
  { id: 'a06', characterRole: 'Adventurer',         userRole: 'Partner',           defaultTone: 'friendly',  category: 'Adventure' },
  { id: 'a07', characterRole: 'Pilot',              userRole: 'Co-Pilot',          defaultTone: 'friendly',  category: 'Adventure' },
  { id: 'a08', characterRole: 'Captain',            userRole: 'First Mate',        defaultTone: 'dominant',  category: 'Adventure' },
  { id: 'a09', characterRole: 'Hacker',             userRole: 'Operator',          defaultTone: 'teasing',   category: 'Adventure' },
  { id: 'a10', characterRole: 'Assassin',           userRole: 'Target',            defaultTone: 'cold',      category: 'Adventure' },
  { id: 'a11', characterRole: 'Mercenary',          userRole: 'Client',            defaultTone: 'cold',      category: 'Adventure' },

  // ── Power ─────────────────────────────────────────────────────────────────
  { id: 'pw01', characterRole: 'Heiress',           userRole: 'Butler',            defaultTone: 'dominant',  category: 'Power' },
  { id: 'pw02', characterRole: 'Mafia Boss',        userRole: 'Right Hand',        defaultTone: 'dominant',  category: 'Power' },
  { id: 'pw03', characterRole: 'Gang Leader',       userRole: 'Member',            defaultTone: 'dominant',  category: 'Power' },
  { id: 'pw04', characterRole: 'Pirate Captain',    userRole: 'Crew',              defaultTone: 'dominant',  category: 'Power' },
  { id: 'pw05', characterRole: 'Villainess',        userRole: 'Hero',              defaultTone: 'dominant',  category: 'Power' },
  { id: 'pw06', characterRole: 'Demon King',        userRole: 'Contractor',        defaultTone: 'dominant',  category: 'Power' },
  { id: 'pw07', characterRole: 'Goddess',           userRole: 'Devotee',           defaultTone: 'dominant',  category: 'Power' },
  { id: 'pw08', characterRole: 'Mistress',          userRole: 'Servant',           defaultTone: 'dominant',  category: 'Power' },
  { id: 'pw09', characterRole: 'Yakuza Leader',     userRole: 'Underling',         defaultTone: 'dominant',  category: 'Power' },
  { id: 'pw10', characterRole: 'Warlord',           userRole: 'Advisor',           defaultTone: 'dominant',  category: 'Power' },

  // ── Supernatural ──────────────────────────────────────────────────────────
  { id: 's01', characterRole: 'Vampire',            userRole: 'Thrall',            defaultTone: 'dominant',  category: 'Supernatural' },
  { id: 's02', characterRole: 'Angel',              userRole: 'Mortal',            defaultTone: 'supportive',category: 'Supernatural' },
  { id: 's03', characterRole: 'Demon',              userRole: 'Summoner',          defaultTone: 'dominant',  category: 'Supernatural' },
  { id: 's04', characterRole: 'Ghost',              userRole: 'Medium',            defaultTone: 'teasing',   category: 'Supernatural' },
  { id: 's05', characterRole: 'Mermaid',            userRole: 'Sailor',            defaultTone: 'sweet',     category: 'Supernatural' },
  { id: 's06', characterRole: 'Fairy',              userRole: 'Human',             defaultTone: 'teasing',   category: 'Supernatural' },
  { id: 's07', characterRole: 'Kitsune',            userRole: 'Chosen One',        defaultTone: 'teasing',   category: 'Supernatural' },
  { id: 's08', characterRole: 'Succubus',           userRole: 'Mortal',            defaultTone: 'teasing',   category: 'Supernatural' },
  { id: 's09', characterRole: 'Time Traveler',      userRole: 'Guide',             defaultTone: 'friendly',  category: 'Supernatural' },
  { id: 's10', characterRole: 'Alien',              userRole: 'Earthling',         defaultTone: 'friendly',  category: 'Supernatural' },
  { id: 's11', characterRole: 'Witch',              userRole: 'Familiar',          defaultTone: 'dominant',  category: 'Supernatural' },
  { id: 's12', characterRole: 'Necromancer',        userRole: 'Undead Companion',  defaultTone: 'cold',      category: 'Supernatural' },
];

export const CATEGORY_LABELS: Record<RelationshipCategory, string> = {
  Romantic: 'Romantic',
  Professional: 'Professional',
  Fantasy: 'Fantasy',
  Everyday: 'Everyday',
  Friends: 'Friends',
  Adventure: 'Adventure',
  Power: 'Power',
  Supernatural: 'Supernatural',
};

export const ALL_CATEGORIES: RelationshipCategory[] = [
  'Romantic',
  'Professional',
  'Fantasy',
  'Everyday',
  'Friends',
  'Adventure',
  'Power',
  'Supernatural',
];
