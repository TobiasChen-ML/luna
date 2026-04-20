import { Sparkles } from 'lucide-react';
import { publicAsset } from '@/utils/publicAsset';

interface CharacterImageProps {
  characterName: string;
  className?: string;
  fallbackGradient?: string;
  imageSrc?: string;
}

// Map character names to their static image paths
const CHARACTER_IMAGES: Record<string, string> = {
  'Luna': publicAsset('/images/luna.png'),
  'Aria': publicAsset('/images/aria.png'),
  'Sophia': publicAsset('/images/sophia.png'),
  'Maya': 'https://assets.roxyclub.ai/roxyclubgirl.jpg',
};

export function CharacterImage({
  characterName,
  className = '',
  fallbackGradient = 'from-primary-500/20 to-secondary-500/20',
  imageSrc
}: CharacterImageProps) {
  // Get the static image URL for this character
  // Priority: provided imageSrc > mapped image > undefined
  const imageUrl = imageSrc || CHARACTER_IMAGES[characterName];

  // If we have an image, show it
  if (imageUrl) {
    return (
      <div className={`rounded-lg overflow-hidden ${className}`}>
        <img
          src={imageUrl}
          alt={characterName}
          className="w-full h-full object-cover"
          loading="lazy"
          onError={(e) => {
            // If image fails to load, hide it and show gradient
            (e.target as HTMLImageElement).style.display = 'none';
          }}
        />
      </div>
    );
  }

  // Fallback to gradient if no image available
  return (
    <div className={`bg-gradient-to-br ${fallbackGradient} rounded-lg flex items-center justify-center group ${className}`}>
      <Sparkles size={48} className="text-primary-500/50 group-hover:text-primary-500 transition-colors" />
    </div>
  );
}
