import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container } from '@/components/layout';
import { CharacterImage } from '@/components/common';
import { Loader2, User, Star } from 'lucide-react';
import { api } from '@/services/api';
import { toChatUrl } from '@/utils/chatUrl';

interface CreatorCharacter {
  id: string;
  name?: string;
  first_name?: string;
  avatar_url?: string;
  profile_image_url?: string;
  personality_tags?: string[];
  tags?: string[];
  style?: string;
}

interface CreatorProfile {
  user_id: string;
  display_name: string;
  avatar_url: string;
  bio: string;
  character_count: number;
  characters: CreatorCharacter[];
}

export function CreatorProfilePage() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const [creator, setCreator] = useState<CreatorProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!userId) return;
    api.get<CreatorProfile>(`/creators/${userId}`)
      .then((res) => setCreator(res.data))
      .catch((err) => {
        if (err?.response?.status === 404) setNotFound(true);
      })
      .finally(() => setLoading(false));
  }, [userId]);

  const getName = (char: CreatorCharacter) => char.first_name || char.name || 'Character';
  const getAvatar = (char: CreatorCharacter) => char.avatar_url || char.profile_image_url;
  const getTags = (char: CreatorCharacter) => char.personality_tags || char.tags || [];

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 size={40} className="animate-spin text-primary-500" />
      </div>
    );
  }

  if (notFound || !creator) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-zinc-400 text-lg">Creator not found.</p>
        <button onClick={() => navigate(-1)} className="text-primary-400 text-sm hover:underline">
          Go back
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 pb-20">
      <Container>
        {/* Creator Header */}
        <div className="flex flex-col items-center text-center mb-16">
          {creator.avatar_url ? (
            <img
              src={creator.avatar_url}
              alt={creator.display_name}
              className="w-24 h-24 rounded-full object-cover border-2 border-primary-500/40 mb-4"
            />
          ) : (
            <div className="w-24 h-24 rounded-full bg-primary-500/20 flex items-center justify-center mb-4">
              <User size={40} className="text-primary-300" />
            </div>
          )}
          <h1 className="text-3xl font-heading font-bold mb-2">{creator.display_name}</h1>
          {creator.bio && (
            <p className="text-zinc-400 max-w-md mb-3">{creator.bio}</p>
          )}
          <span className="text-sm text-zinc-500">
            {creator.character_count} character{creator.character_count !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Character Grid */}
        {creator.characters.length === 0 ? (
          <p className="text-center text-zinc-500">No public characters yet.</p>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {creator.characters.map((char) => {
              const name = getName(char);
              const avatar = getAvatar(char);
              const tags = getTags(char);
              return (
                <div
                  key={char.id}
                  className="card-glass hover:border-primary-500/50 transition-all cursor-pointer group"
                  onClick={() => navigate(toChatUrl(char))}
                >
                  <div className="relative">
                    <CharacterImage
                      characterName={name}
                      imageSrc={avatar}
                      className="aspect-[3/4] mb-4"
                    />
                    <div className="absolute top-2 right-2">
                      <div className="flex gap-1">
                        {[...Array(5)].map((_, i) => (
                          <Star key={i} size={14} className="fill-yellow-500 text-yellow-500" />
                        ))}
                      </div>
                    </div>
                  </div>
                  <h3 className="text-xl font-heading font-bold mb-2">{name}</h3>
                  {char.style && (
                    <p className="text-primary-500 text-sm font-semibold mb-2">{char.style}</p>
                  )}
                  <div className="flex flex-wrap gap-2">
                    {tags.slice(0, 3).map((tag, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 text-xs rounded-full bg-primary-500/10 text-primary-300 border border-primary-500/20"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Container>
    </div>
  );
}
