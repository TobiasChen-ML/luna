/**
 * Step 3: Relationship Identity
 *
 * Select a relationship pair from ~100 presets, searchable by keyword.
 * character_role + user_role are always set together to avoid mismatches.
 */
import { useState, useMemo } from 'react';
import { Search } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useWizard } from '@/contexts/CharacterWizardContext';
import { WizardStep } from '../WizardStep';
import {
  RELATIONSHIP_PRESETS,
  ALL_CATEGORIES,
  CATEGORY_LABELS,
  type RelationshipCategory,
} from './relationshipPresets';

const TONE_OPTIONS = [
  { value: 'sweet',      label: 'Sweet',      color: 'text-pink-400   border-pink-500/40' },
  { value: 'dominant',   label: 'Dominant',   color: 'text-red-400    border-red-500/40' },
  { value: 'cold',       label: 'Cold',       color: 'text-blue-400   border-blue-500/40' },
  { value: 'friendly',   label: 'Friendly',   color: 'text-green-400  border-green-500/40' },
  { value: 'supportive', label: 'Supportive', color: 'text-yellow-400 border-yellow-500/40' },
  { value: 'teasing',    label: 'Teasing',    color: 'text-purple-400 border-purple-500/40' },
  { value: 'mysterious', label: 'Mysterious', color: 'text-indigo-400 border-indigo-500/40' },
];

export function Step3Relationship() {
  const { characterData, updateNestedField } = useWizard();

  const [query, setQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<RelationshipCategory | 'All'>('All');

  const currentRelation = characterData.relation ?? {
    character_role: '',
    user_role: '',
    relationship_tone: 'sweet',
  };

  // ── Filter logic ────────────────────────────────────────────────────────
  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim();
    return RELATIONSHIP_PRESETS.filter((p) => {
      const matchCategory =
        activeCategory === 'All' || p.category === activeCategory;
      const matchQuery =
        !q ||
        p.characterRole.toLowerCase().includes(q) ||
        p.userRole.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q);
      return matchCategory && matchQuery;
    });
  }, [query, activeCategory]);

  // ── Handlers ─────────────────────────────────────────────────────────────
  const handleSelect = (characterRole: string, userRole: string, defaultTone: string) => {
    updateNestedField('relation', {
      character_role: characterRole,
      user_role: userRole,
      relationship_tone: currentRelation.relationship_tone || defaultTone,
    });
  };

  const handleToneChange = (tone: string) => {
    updateNestedField('relation.relationship_tone', tone);
  };

  const isSelected = (characterRole: string, userRole: string) =>
    currentRelation.character_role === characterRole &&
    currentRelation.user_role === userRole;

  return (
    <WizardStep
      title="Relationship Identity"
      description="Choose the dynamic between you and your character"
    >
      <div className="space-y-6">

        {/* ── Search ── */}
        <div className="relative">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none"
          />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search relationships… e.g. boss, mermaid, best friend"
            className={cn(
              'w-full pl-9 pr-4 py-2.5 rounded-lg text-sm',
              'bg-zinc-900 border border-zinc-700',
              'focus:outline-none focus:border-primary-500',
              'text-white placeholder:text-zinc-500',
            )}
          />
        </div>

        {/* ── Category chips ── */}
        <div className="flex flex-wrap gap-2">
          {(['All', ...ALL_CATEGORIES] as const).map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={cn(
                'px-3 py-1 rounded-full text-xs font-medium transition-colors',
                activeCategory === cat
                  ? 'bg-primary-500 text-white'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700',
              )}
            >
              {cat === 'All' ? 'All' : CATEGORY_LABELS[cat]}
            </button>
          ))}
        </div>

        {/* ── Preset grid ── */}
        <div
          className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 overflow-y-auto pr-1"
          style={{ maxHeight: '340px' }}
        >
          {filtered.length === 0 ? (
            <p className="col-span-full text-center text-sm text-zinc-500 py-8">
              No results for "{query}"
            </p>
          ) : (
            filtered.map((preset) => (
              <button
                key={preset.id}
                onClick={() =>
                  handleSelect(preset.characterRole, preset.userRole, preset.defaultTone)
                }
                className={cn(
                  'flex flex-col items-start px-3 py-2.5 rounded-lg border transition-all text-left',
                  isSelected(preset.characterRole, preset.userRole)
                    ? 'border-primary-500 bg-primary-500/10 text-white'
                    : 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:border-zinc-500 hover:bg-zinc-800',
                )}
              >
                <span className="text-xs font-semibold leading-snug capitalize">
                  {preset.characterRole}
                </span>
                <span className="text-[10px] text-zinc-500 leading-snug mt-0.5">
                  ↳ you: {preset.userRole}
                </span>
              </button>
            ))
          )}
        </div>

        {/* ── Tone override ── */}
        <div>
          <label className="block text-sm font-medium mb-3">Relationship Tone</label>
          <div className="flex flex-wrap gap-2">
            {TONE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => handleToneChange(opt.value)}
                className={cn(
                  'px-3 py-1.5 rounded-lg border-2 text-xs font-medium transition-all',
                  currentRelation.relationship_tone === opt.value
                    ? `${opt.color} bg-current/10`
                    : 'border-zinc-700 text-zinc-400 hover:border-zinc-600',
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <p className="text-xs text-zinc-500 mt-1.5">
            Override the default tone for this relationship
          </p>
        </div>

        {/* ── Preview ── */}
        {currentRelation.character_role && currentRelation.user_role && (
          <div className="rounded-lg border border-primary-500/30 bg-primary-500/5 px-4 py-3 text-center">
            <p className="text-xs text-zinc-500 mb-1">Selected relationship</p>
            <p className="text-base">
              <span className="text-primary-400 font-semibold capitalize">
                {currentRelation.character_role}
              </span>
              <span className="text-zinc-600 mx-2">↔</span>
              <span className="text-white font-medium capitalize">
                {currentRelation.user_role}
              </span>
            </p>
            <p className="text-xs text-zinc-500 mt-1 capitalize">
              Tone: {currentRelation.relationship_tone}
            </p>
          </div>
        )}

      </div>
    </WizardStep>
  );
}
