import { useState } from 'react';
import { Heart } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';
import { cn } from '@/utils/cn';

interface FavoriteButtonProps {
  characterId: string;
  initialFavorited?: boolean;
  size?: 'sm' | 'md' | 'lg';
  onFavoriteChange?: (isFavorited: boolean) => void;
}

export function FavoriteButton({
  characterId,
  initialFavorited = false,
  size = 'md',
  onFavoriteChange,
}: FavoriteButtonProps) {
  const { user } = useAuth();
  const [isFavorited, setIsFavorited] = useState(initialFavorited);
  const [isLoading, setIsLoading] = useState(false);

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  const handleToggleFavorite = async () => {
    if (!user || isLoading) return;

    setIsLoading(true);
    try {
      if (isFavorited) {
        await api.delete(`/characters/${characterId}/favorite`);
        setIsFavorited(false);
        onFavoriteChange?.(false);
      } else {
        await api.post(`/characters/${characterId}/favorite`);
        setIsFavorited(true);
        onFavoriteChange?.(true);
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) return null;

  return (
    <button
      onClick={handleToggleFavorite}
      disabled={isLoading}
      className={cn(
        'p-1.5 rounded-full transition-all duration-200',
        'hover:bg-white/10 backdrop-blur-sm',
        isLoading && 'opacity-50 cursor-not-allowed'
      )}
      title={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
    >
      <Heart
        className={cn(
          sizeClasses[size],
          'transition-colors duration-200',
          isFavorited
            ? 'fill-pink-500 text-pink-500'
            : 'text-white/70 hover:text-white'
        )}
      />
    </button>
  );
}