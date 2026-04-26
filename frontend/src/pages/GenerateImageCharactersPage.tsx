import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Loader2,
  Sparkles,
} from 'lucide-react';

import { api } from '@/services/api';
import { RoxyShellLayout } from '@/components/layout';
import type { Character } from '@/types';

interface CharacterLike {
  id: string;
  name?: string;
  first_name?: string;
  age?: number | string;
  images?: string[];
  profile_image_url?: string;
  avatar_url?: string;
  media_urls?: {
    avatar?: string;
  };
}

interface CharacterCardItem {
  id: string;
  name: string;
  age?: number | string;
  image: string;
  source: 'official' | 'user';
}

interface PaginatedCharactersResponse {
  items?: Character[];
}

function getCharacterName(character: CharacterLike): string {
  return character.first_name || character.name || 'Character';
}

function getCharacterImage(character: CharacterLike): string {
  return (
    character.images?.[0] ||
    character.media_urls?.avatar ||
    character.avatar_url ||
    character.profile_image_url ||
    ''
  );
}

export function GenerateImageCharactersPage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [officialCharacters, setOfficialCharacters] = useState<CharacterCardItem[]>([]);
  const [myCharacters, setMyCharacters] = useState<CharacterCardItem[]>([]);

  useEffect(() => {
    const fetchCharacters = async () => {
      setIsLoading(true);
      try {
        const [officialResult, myResult] = await Promise.allSettled([
          api.get<CharacterLike[]>('/characters/official'),
          api.get<PaginatedCharactersResponse | Character[]>('/characters/my'),
        ]);

        const officialRows = officialResult.status === 'fulfilled' && Array.isArray(officialResult.value.data)
          ? officialResult.value.data
          : [];
        const myRows = myResult.status === 'fulfilled'
          ? (
            Array.isArray(myResult.value.data)
              ? myResult.value.data
              : (Array.isArray(myResult.value.data?.items) ? myResult.value.data.items : [])
          )
          : [];

        const normalizedOfficial = officialRows
          .map((char) => ({
            id: char.id,
            name: getCharacterName(char),
            age: char.age,
            image: getCharacterImage(char),
            source: 'official' as const,
          }))
          .filter((char) => Boolean(char.image));

        const normalizedMine = myRows
          .map((char) => ({
            id: char.id,
            name: getCharacterName(char),
            age: char.age,
            image: getCharacterImage(char),
            source: 'user' as const,
          }))
          .filter((char) => Boolean(char.image));

        setOfficialCharacters(normalizedOfficial);
        setMyCharacters(normalizedMine);
      } catch (error) {
        console.error('Failed to fetch characters:', error);
        setOfficialCharacters([]);
        setMyCharacters([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCharacters();
  }, []);

  return (
    <RoxyShellLayout>
      <div>
          <div className="mb-6 flex items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-zinc-200 hover:bg-white/10"
              aria-label="Back"
            >
              <span className="text-xl leading-none">&larr;</span>
            </button>
            <div className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 p-1 text-sm">
              <span className="rounded-lg bg-indigo-500/20 border border-indigo-400/40 px-3 py-1 text-indigo-200">Girls</span>
              <span className="rounded-lg px-3 py-1 text-zinc-400">Anime</span>
              <span className="rounded-lg px-3 py-1 text-zinc-400">Guys</span>
            </div>
            <div className="ml-2">
              <div className="flex items-center gap-2 text-lg font-bold">
                <Sparkles className="h-5 w-5 text-pink-300" />
                Generate Image
              </div>
              <div className="text-sm text-zinc-400">Choose a character</div>
            </div>
          </div>

          {isLoading ? (
            <div className="rounded-2xl border border-white/10 bg-black/30 px-8 py-14 text-center text-zinc-400">
              <Loader2 className="mx-auto mb-3 h-8 w-8 animate-spin" />
              Loading characters...
            </div>
          ) : myCharacters.length === 0 && officialCharacters.length === 0 ? (
            <div className="rounded-2xl border border-white/10 bg-black/30 px-8 py-14 text-center text-zinc-400">
              No characters available now.
            </div>
          ) : (
            <div className="space-y-8">
              {myCharacters.length > 0 ? (
                <section>
                  <div className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-300">My Characters</div>
                  <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
                    {myCharacters.map((char) => (
                      <button
                        key={`${char.source}-${char.id}`}
                        onClick={() => navigate(`/generate-image/${char.id}`)}
                        className="group relative h-[320px] overflow-hidden rounded-[18px] border border-white/10 text-left transition-colors hover:border-white/25"
                      >
                        <img
                          src={char.image}
                          alt={char.name}
                          className="absolute inset-0 h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent" />
                        <div className="absolute bottom-3 left-3 right-3 rounded-full bg-black/45 px-3 py-2 text-center">
                          <span className="text-xl font-extrabold leading-none text-white">
                            {char.name}
                          </span>
                          {char.age !== undefined && char.age !== null ? (
                            <span className="ml-2 text-zinc-300">{char.age}</span>
                          ) : null}
                        </div>
                      </button>
                    ))}
                  </div>
                </section>
              ) : null}

              {officialCharacters.length > 0 ? (
                <section>
                  <div className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-300">Official Characters</div>
                  <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
                    {officialCharacters.map((char) => (
                      <button
                        key={`${char.source}-${char.id}`}
                        onClick={() => navigate(`/generate-image/${char.id}`)}
                        className="group relative h-[320px] overflow-hidden rounded-[18px] border border-white/10 text-left transition-colors hover:border-white/25"
                      >
                        <img
                          src={char.image}
                          alt={char.name}
                          className="absolute inset-0 h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent" />
                        <div className="absolute bottom-3 left-3 right-3 rounded-full bg-black/45 px-3 py-2 text-center">
                          <span className="text-xl font-extrabold leading-none text-white">
                            {char.name}
                          </span>
                          {char.age !== undefined && char.age !== null ? (
                            <span className="ml-2 text-zinc-300">{char.age}</span>
                          ) : null}
                        </div>
                      </button>
                    ))}
                  </div>
                </section>
              ) : null}
            </div>
          )}
      </div>
    </RoxyShellLayout>
  );
}
