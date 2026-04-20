import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Image as ImageIcon,
  Plus,
  Trash2,
  Clock,
  CheckCircle,
  XCircle,
} from 'lucide-react';

import { GalleryModal } from '@/components/common';
import { RoxyShellLayout } from '@/components/layout';
import type { Character, ReviewStatus } from '@/types';
import { api } from '@/services/api';
import { toChatUrl } from '@/utils/chatUrl';

const extractSection = (text: string | undefined, keyword: string): string => {
  if (!text) return '';
  const sections = text.split('## ');
  const section = sections.find(s => s.toLowerCase().includes(keyword.toLowerCase()));
  if (!section) return '';
  return section.split('\n').slice(1).join('\n').trim();
};

const ReviewStatusBadge = ({ status, rejectionReason }: { status?: ReviewStatus; rejectionReason?: string }) => {
  if (!status || status === 'approved') return null;
  
  if (status === 'pending') {
    return (
      <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-yellow-500/20 border border-yellow-400/30 text-yellow-200 text-xs font-medium">
        <Clock size={12} />
        <span>Pending Review</span>
      </div>
    );
  }
  
  if (status === 'rejected') {
    return (
      <div className="absolute top-3 left-3 flex flex-col gap-1">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/20 border border-red-400/30 text-red-200 text-xs font-medium">
          <XCircle size={12} />
          <span>Rejected</span>
        </div>
        {rejectionReason && (
          <div className="px-2.5 py-1 rounded bg-red-500/10 border border-red-400/20 text-red-200 text-xs max-w-[200px]">
            {rejectionReason}
          </div>
        )}
      </div>
    );
  }
  
  return null;
};

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export function MyCharactersPage() {
  const navigate = useNavigate();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [galleryCharacter, setGalleryCharacter] = useState<Character | null>(null);

  useEffect(() => {
    loadCharacters();
  }, []);

  const loadCharacters = async () => {
    try {
      const response = await api.get<PaginatedResponse<Character>>('/characters/my');
      if (response.data && Array.isArray(response.data.items)) {
        setCharacters(response.data.items);
      } else if (Array.isArray(response.data)) {
        setCharacters(response.data);
      } else {
        console.error('API returned unexpected format:', response.data);
        setCharacters([]);
      }
    } catch (error) {
      console.error('Failed to load characters:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (characterId: string) => {
    if (!window.confirm('Are you sure you want to delete this character? This action cannot be undone.')) {
      return;
    }

    setDeleting(characterId);
    try {
      await api.delete(`/characters/${characterId}`);
      setCharacters((prev) => prev.filter((c) => c.id !== characterId));
    } catch (error) {
      console.error('Failed to delete character:', error);
      alert('Failed to delete character. Please try again.');
    } finally {
      setDeleting(null);
    }
  };

  const handleChat = (character: Character) => {
    if (character.review_status === 'pending' || character.review_status === 'rejected') {
      alert('This character is still under review and cannot be chatted with yet.');
      return;
    }
    navigate(toChatUrl(character));
  };

  return (
    <RoxyShellLayout>
      <div>
          <h1 className="mb-7 text-center text-5xl font-bold tracking-tight">
            My AI
          </h1>

          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            <button
              onClick={() => navigate('/create-character')}
              className="group relative h-[470px] rounded-[14px] bg-[#e85b80] hover:bg-[#e34f76] transition-colors flex items-center justify-center"
            >
              <div className="flex flex-col items-center text-white">
                <span className="w-14 h-14 rounded-full bg-white text-[#e85b80] flex items-center justify-center mb-4">
                  <Plus size={32} />
                </span>
                <span className="text-[38px] font-bold leading-none">Create new AI</span>
              </div>
            </button>

            {loading &&
              [1, 2, 3].map((i) => (
                <div key={i} className="h-[470px] rounded-[14px] border border-white/10 bg-white/5 animate-pulse" />
              ))}

            {!loading &&
              characters.map((character) => {
                const personalityText = extractSection(character.system_prompt, 'Personality Profile');
                const summary = personalityText
                  ? personalityText.replace(/[#*]/g, '').replace(/\s+/g, ' ').trim().slice(0, 120)
                  : '';

                return (
                  <button
                    key={character.id}
                    onClick={() => handleChat(character)}
                    className="group relative h-[470px] overflow-hidden rounded-[14px] border border-white/10 text-left transition-colors hover:border-white/30"
                  >
                    <ReviewStatusBadge 
                      status={character.review_status} 
                      rejectionReason={character.rejection_reason} 
                    />
                    
                    {character.profile_image_url ? (
                      <img
                        src={character.profile_image_url}
                        alt={character.first_name}
                        className="absolute inset-0 h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                      />
                    ) : (
                      <div className="absolute inset-0 bg-gradient-to-br from-pink-500/30 to-purple-500/30" />
                    )}

                    <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/35 to-transparent" />

                    <div className="absolute top-3 right-3 flex items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setGalleryCharacter(character);
                        }}
                        className="h-8 w-8 rounded-full border border-white/20 bg-black/35 text-zinc-100 hover:bg-black/60 flex items-center justify-center"
                        title="Gallery"
                      >
                        <ImageIcon size={15} />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(character.id);
                        }}
                        disabled={deleting === character.id}
                        className="h-8 w-8 rounded-full border border-red-300/30 bg-red-500/20 text-red-100 hover:bg-red-500/35 disabled:opacity-50 flex items-center justify-center"
                        title="Delete"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>

                    <div className="absolute bottom-0 left-0 right-0 p-4">
                      <div className="flex items-baseline gap-2">
                        <h3 className="text-3xl font-extrabold leading-none text-white">
                          {character.first_name}
                        </h3>
                        {character.age !== undefined && character.age !== null ? (
                          <span className="text-zinc-200 text-2xl">{character.age}</span>
                        ) : null}
                      </div>
                      {summary && (
                        <p className="mt-2 text-sm text-zinc-200/90 line-clamp-2">
                          {summary}
                        </p>
                      )}
                    </div>
                  </button>
                );
              })}
          </section>

          {!loading && characters.length === 0 && (
            <div className="mt-6 rounded-xl border border-white/10 bg-black/30 px-6 py-5 text-zinc-300">
              No characters yet. Click "Create new AI" to start.
            </div>
          )}
      </div>

      <GalleryModal
        isOpen={!!galleryCharacter}
        onClose={() => setGalleryCharacter(null)}
        characterId={galleryCharacter?.id || ''}
        characterName={galleryCharacter?.first_name || ''}
      />
    </RoxyShellLayout>
  );
}
