import { useState, useEffect } from 'react';
import { Check, X, UserPlus } from 'lucide-react';
import { cn } from '@/utils/cn';
import { characterService } from '@/services/characterService';
import { getSafeAvatarUrl } from '@/utils/avatarUrlGuard';

interface Participant {
  id: string;
  name: string;
  avatar_url?: string;
}

interface ParticipantSelectorProps {
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
  maxParticipants?: number;
  className?: string;
}

export function ParticipantSelector({
  selectedIds,
  onSelectionChange,
  maxParticipants = 5,
  className,
}: ParticipantSelectorProps) {
  const [characters, setCharacters] = useState<Participant[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadCharacters();
  }, []);

  const loadCharacters = async () => {
    try {
      setLoading(true);
      const response = await characterService.getDiscoverCharacters({ limit: 50 });
      const chars = response.characters || [];
      setCharacters(chars);
    } catch (error) {
      console.error('Failed to load characters:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCharacters = characters.filter((char) =>
    char.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleToggle = (characterId: string) => {
    if (selectedIds.includes(characterId)) {
      onSelectionChange(selectedIds.filter((id) => id !== characterId));
    } else if (selectedIds.length < maxParticipants) {
      onSelectionChange([...selectedIds, characterId]);
    }
  };

  const handleRemove = (characterId: string) => {
    onSelectionChange(selectedIds.filter((id) => id !== characterId));
  };

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Select Participants</h3>
        <span className="text-sm text-zinc-400">
          {selectedIds.length} / {maxParticipants} selected
        </span>
      </div>

      {selectedIds.length > 0 && (
        <div className="flex flex-wrap gap-2 p-3 rounded-lg bg-zinc-800/50 border border-zinc-700">
          {selectedIds.map((id) => {
            const char = characters.find((c) => c.id === id);
            return (
              <div
                key={id}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/20 border border-purple-500/30"
              >
                {char?.avatar_url && (
                  <img
                    src={getSafeAvatarUrl(char.avatar_url)}
                    alt={char.name}
                    className="w-5 h-5 rounded-full object-cover"
                  />
                )}
                <span className="text-sm text-white">{char?.name || id}</span>
                <button
                  onClick={() => handleRemove(id)}
                  className="text-zinc-400 hover:text-white transition-colors"
                >
                  <X size={14} />
                </button>
              </div>
            );
          })}
        </div>
      )}

      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search characters..."
          className="w-full px-4 py-2 rounded-lg bg-zinc-800 border border-zinc-700 text-white placeholder:text-zinc-500 focus:outline-none focus:border-purple-500"
        />
        <UserPlus className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500" size={20} />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-[300px] overflow-y-auto">
          {filteredCharacters.map((char) => {
            const isSelected = selectedIds.includes(char.id);
            const isDisabled = !isSelected && selectedIds.length >= maxParticipants;
            const safeAvatar = getSafeAvatarUrl(char.avatar_url);

            return (
              <button
                key={char.id}
                onClick={() => handleToggle(char.id)}
                disabled={isDisabled}
                className={cn(
                  'flex items-center gap-3 p-3 rounded-lg border transition-all',
                  isSelected
                    ? 'bg-purple-500/20 border-purple-500/50 text-white'
                    : 'bg-zinc-800/50 border-zinc-700 text-zinc-300 hover:border-zinc-500',
                  isDisabled && 'opacity-50 cursor-not-allowed'
                )}
              >
                {safeAvatar ? (
                  <img
                    src={safeAvatar}
                    alt={char.name}
                    className="w-8 h-8 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center text-sm font-semibold">
                    {char.name.charAt(0)}
                  </div>
                )}
                <span className="flex-1 text-sm font-medium truncate">{char.name}</span>
                {isSelected && <Check size={16} className="text-purple-400" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}