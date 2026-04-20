import React, { useCallback, useEffect, useRef, useState } from 'react';
import type { AxiosError } from 'axios';
import { Search, Copy, Check, Users } from 'lucide-react';

import { MainLayout } from '@/components/layout/MainLayout';
import { Button } from '@/components/common/Button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ugcService, type CommunityCharacter } from '@/services/ugcService';
import { useAuth } from '@/contexts/AuthContext';

type SortBy = 'published_at' | 'downloads';

const PAGE_SIZE = 20;

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

function Toast({ message, onDone }: { message: string; onDone: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onDone, 2500);
    return () => clearTimeout(timer);
  }, [onDone]);

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 rounded-xl bg-zinc-800 border border-zinc-700 px-5 py-3 text-sm text-white shadow-xl">
      {message}
    </div>
  );
}

interface CharacterCardProps {
  char: CommunityCharacter;
  currentUserEmail: string | null;
  onFork: (charId: string) => Promise<void>;
  forkedIds: Set<string>;
}

function CharacterCard({ char, currentUserEmail, onFork, forkedIds }: CharacterCardProps) {
  const [loading, setLoading] = useState(false);
  const isOwn = char.owner_id === currentUserEmail;
  const alreadyForked = forkedIds.has(char.id);
  const disabled = isOwn || alreadyForked || loading;

  const handleFork = async () => {
    if (disabled) return;
    setLoading(true);
    try {
      await onFork(char.id);
    } finally {
      setLoading(false);
    }
  };

  const tags = char.personality_tags?.slice(0, 2) ?? [];

  return (
    <div className="card-glass rounded-2xl overflow-hidden group relative flex flex-col hover:scale-[1.02] transition-transform duration-200">
      {/* Avatar */}
      <div className="aspect-[3/4] bg-zinc-800 relative overflow-hidden">
        {char.avatar_url ? (
          <img
            src={char.avatar_url}
            alt={char.first_name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-5xl font-bold text-zinc-500">
              {char.first_name?.charAt(0) || '?'}
            </span>
          </div>
        )}

        {/* Fork button - visible on hover */}
        <button
          type="button"
          onClick={handleFork}
          disabled={disabled}
          className={`absolute bottom-3 right-3 rounded-xl px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 shadow-lg transition-all
            opacity-0 group-hover:opacity-100
            ${disabled
              ? 'bg-zinc-700 text-zinc-400 cursor-default'
              : 'bg-primary-600 hover:bg-primary-500 text-white'
            }`}
        >
          {loading ? (
            <LoadingSpinner size="sm" />
          ) : alreadyForked || isOwn ? (
            <><Check className="w-3 h-3" /> In Library</>
          ) : (
            <><Copy className="w-3 h-3" /> Fork</>
          )}
        </button>
      </div>

      {/* Info */}
      <div className="p-3 flex flex-col gap-1 flex-1">
        <p className="text-white font-semibold truncate">{char.first_name}</p>
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {tags.map((tag) => (
              <span key={tag} className="text-xs rounded-full bg-zinc-700/60 px-2 py-0.5 text-zinc-300">
                {tag}
              </span>
            ))}
          </div>
        )}
        <p className="text-xs text-zinc-500 mt-auto">by {char.creator_nickname}</p>
      </div>
    </div>
  );
}

export const CommunityPage: React.FC = () => {
  const { user } = useAuth();
  const currentUserEmail = user?.email ?? null;

  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<SortBy>('published_at');
  const [page, setPage] = useState(1);

  const [characters, setCharacters] = useState<CommunityCharacter[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [forkedIds, setForkedIds] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<string | null>(null);

  const debouncedSearch = useDebounce(search, 400);
  const abortRef = useRef<AbortController | null>(null);

  const load = useCallback(async (
    q: string,
    sort: SortBy,
    p: number,
  ) => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);
    try {
      const result = await ugcService.browseCommunityCharacters({
        search: q || undefined,
        sort_by: sort,
        page: p,
        pageSize: PAGE_SIZE,
      });
      setCharacters(result.characters);
      setTotal(result.total);
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      if (axiosErr?.code === 'ERR_CANCELED') return;
      setError(axiosErr?.response?.data?.detail ?? 'Load failed, please try again');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, sortBy]);

  useEffect(() => {
    void load(debouncedSearch, sortBy, page);
  }, [load, debouncedSearch, sortBy, page]);

  const handleFork = async (charId: string) => {
    try {
      const result = await ugcService.forkCharacter(charId);
      setForkedIds((prev) => new Set([...prev, charId]));
      setToast(result.message);
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      const msg = axiosErr?.response?.data?.detail ?? 'Fork failed';
      if (msg.includes('limit')) {
        setToast('Character limit reached. Please upgrade your subscription.');
      } else {
        setToast(msg);
      }
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-2">
            <Users className="w-7 h-7 text-primary-400" />
            Community Characters
          </h1>
          <p className="text-zinc-400 mt-1">Discover characters created by other users</p>
        </div>

        {/* Search + Sort */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <input
              type="text"
              placeholder="Search character names..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-xl bg-zinc-800 border border-zinc-700 pl-9 pr-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-primary-500"
            />
          </div>
          <div className="flex gap-2">
            {(['published_at', 'downloads'] as const).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSortBy(s)}
                className={`rounded-xl px-4 py-2 text-sm whitespace-nowrap transition-colors
                  ${sortBy === s
                    ? 'bg-primary-600 text-white'
                    : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700 border border-zinc-700'
                  }`}
              >
                {s === 'published_at' ? 'Newest' : 'Hottest'}
              </button>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Grid */}
        {loading ? (
          <div className="flex justify-center py-20">
            <LoadingSpinner size="lg" />
          </div>
        ) : characters.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-zinc-500">
            <Users className="w-12 h-12 mb-3 opacity-30" />
            <p className="text-sm">No public characters yet</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
            {characters.map((char) => (
              <CharacterCard
                key={char.id}
                char={char}
                currentUserEmail={currentUserEmail}
                onFork={handleFork}
                forkedIds={forkedIds}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-3 pt-4">
            <Button
              variant="secondary"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </Button>
            <span className="text-sm text-zinc-400">
              {page} / {totalPages}
            </span>
            <Button
              variant="secondary"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
    </MainLayout>
  );
};

export default CommunityPage;


