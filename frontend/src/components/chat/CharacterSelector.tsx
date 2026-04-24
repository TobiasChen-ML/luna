import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Character } from '@/types';
import { MessageSquare, X, Search } from 'lucide-react';
import { cn } from '@/utils/cn';
import { api } from '@/services/api';
import { Button } from '@/components/common';

interface CharacterSelectorProps {
  currentCharacterId?: string;
  onSelectCharacter: (character: Character) => void;
  isMobileOpen?: boolean;
  onMobileClose?: () => void;
  disabled?: boolean;
  className?: string;
}

export function CharacterSelector({
  currentCharacterId,
  onSelectCharacter,
  isMobileOpen = false,
  onMobileClose,
  disabled = false,
  className,
}: CharacterSelectorProps) {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;

    api.get<Character[]>('/characters')
      .then((charsRes) => {
        if (cancelled) return;
        setCharacters(charsRes.data);
      })
      .catch((error) => {
        if (cancelled) return;
        console.error('Failed to load characters:', error);
        setError('Failed to load characters.');
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });

    return () => { cancelled = true; };
  }, []);

  const normalizeName = (character: { name?: string; first_name?: string }) =>
    character.first_name || character.name || 'Unknown';

  const filterBySearch = <T extends { name?: string; first_name?: string }>(items: T[]) => {
    if (!searchTerm.trim()) return items;
    const query = searchTerm.toLowerCase();
    return items.filter((item) => normalizeName(item).toLowerCase().includes(query));
  };

  const filteredCharacters = filterBySearch(characters);

  return (
    <div
      className={cn(
        'h-full flex flex-col bg-zinc-900 border-r border-white/10',
        // Mobile: slide-in overlay
        'fixed inset-y-0 left-0 w-80 z-40 transform transition-transform duration-300',
        // Desktop: persistent sidebar
        'lg:static lg:z-auto lg:translate-x-0',
        isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        className
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <h2 className="text-xl font-heading font-bold">Chat List</h2>
        <button onClick={onMobileClose} className="lg:hidden text-zinc-400 hover:text-white">
          <X size={24} />
        </button>
      </div>

      {/* Search */}
      <div className="px-4 pt-3">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10">
          <Search size={16} className="text-zinc-400" />
          <input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search your characters"
            className="flex-1 bg-transparent text-sm text-white placeholder:text-zinc-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 pt-3">
          <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">
            {error}
          </div>
        </div>
      )}

      {/* Character List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 rounded-lg bg-white/5 animate-pulse" />
            ))}
          </div>
        ) : filteredCharacters.length === 0 ? (
          <div className="text-center py-8 space-y-4">
            <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto">
              <MessageSquare size={24} className="text-zinc-500" />
            </div>
            <p className="text-zinc-400 text-sm">
              {characters.length === 0 ? 'No characters yet' : 'No matches found'}
            </p>
          </div>
        ) : (
          filteredCharacters.map((character) => {
            const displayName = normalizeName(character);
            const avatarInitial = displayName.charAt(0).toUpperCase() || '?';

            return (
            <button
              key={character.id}
              disabled={disabled}
              onClick={() => {
                if (disabled) return;
                onSelectCharacter(character);
                onMobileClose?.();
              }}
              title={disabled ? "Please wait for the reply to finish" : ""}
              className={cn(
                'w-full p-3 rounded-lg text-left transition-all',
                disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-white/5 hover:scale-[1.02]',
                currentCharacterId === character.id
                  ? 'bg-gradient-primary/20 border-2 border-primary-500'
                  : 'bg-white/5 border border-white/10'
              )}
            >
              <div className="flex items-start gap-3">
                {/* Avatar */}
                {character.profile_image_url || character.media_urls?.avatar ? (
                  <img 
                    src={character.profile_image_url || character.media_urls?.avatar} 
                    alt={displayName}
                    className="w-12 h-12 rounded-full object-cover flex-shrink-0 border border-white/10"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-gradient-primary flex items-center justify-center flex-shrink-0 text-white font-semibold">
                    {avatarInitial}
                  </div>
                )}

                {/* Character Info */}
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-white truncate">
                    {displayName}, {character.age}
                  </h3>
                  <p className="text-sm text-zinc-400 truncate">
                    {(character.personality_tags || []).slice(0, 2).join(', ')}
                  </p>
                  <p className="text-xs text-zinc-500 mt-1">{character.style}</p>
                </div>
              </div>
            </button>
          )})
        )}
      </div>

      {/* Create New Button removed */}
      <div className="p-4 border-t border-white/10">
        <Button
          variant="primary"
          className="w-full"
          onClick={() => {
            if (disabled) return;
            onMobileClose?.();
            navigate('/create-character');
          }}
          disabled={disabled}
        >
          Create Character
        </Button>
      </div>
    </div>
  );
}
