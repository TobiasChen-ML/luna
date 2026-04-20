import React, { useCallback, useEffect, useState } from 'react';
import type { AxiosError } from 'axios';
import { useNavigate } from 'react-router-dom';

import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ugcService, type CreatorOverview } from '@/services/ugcService';
import { scriptService, type Script } from '@/services/scriptService';

type TabType = 'overview' | 'characters' | 'scripts';

type CharacterItem = {
  id: string;
  first_name: string;
  avatar_url?: string;
  is_public: boolean;
};

export const CreatorCenterPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [overview, setOverview] = useState<CreatorOverview | null>(null);
  const [characters, setCharacters] = useState<CharacterItem[]>([]);
  const [scripts, setScripts] = useState<Script[]>([]);

  const getErrorMessage = (err: unknown, fallback: string): string => {
    const axiosError = err as AxiosError<{ detail?: string }>;
    return axiosError?.response?.data?.detail || fallback;
  };

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [creatorOverview, myCharactersRes, myScriptsRes] = await Promise.all([
        ugcService.getCreatorOverview(),
        ugcService.getMyCharacters(1, 200),
        scriptService.getMyScripts(1, 200),
      ]);

      setOverview(creatorOverview);
      setCharacters(myCharactersRes.characters || []);
      setScripts(myScriptsRes.scripts || []);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to load creator center data.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <LoadingSpinner size="lg" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">Creator Center</h1>
            <p className="text-zinc-400 mt-2">Manage your characters and scripts.</p>
          </div>
          <Button variant="outline" onClick={() => navigate('/community')}>
            Browse Community Characters
          </Button>
        </div>

        {error && <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-red-300">{error}</div>}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-4">
            <p className="text-zinc-400 text-sm">Characters</p>
            <p className="text-2xl font-bold text-white mt-1">{overview?.characters_total ?? 0}</p>
            <p className="text-xs text-zinc-500 mt-1">Published: {overview?.characters_published ?? 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-zinc-400 text-sm">Scripts</p>
            <p className="text-2xl font-bold text-white mt-1">{overview?.scripts_total ?? 0}</p>
            <p className="text-xs text-zinc-500 mt-1">Active: {overview?.scripts_active ?? 0}</p>
          </Card>
        </div>

        <div className="flex gap-2 overflow-x-auto">
          {([
            ['overview', 'Overview'],
            ['characters', 'Characters'],
            ['scripts', 'Scripts'],
          ] as const).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveTab(key)}
              className={`rounded-lg px-4 py-2 text-sm whitespace-nowrap ${activeTab === key ? 'bg-primary-600 text-white' : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'}`}
            >
              {label}
            </button>
          ))}
        </div>

        {activeTab === 'overview' && (
          <Card className="p-5">
            <h2 className="text-lg font-semibold text-white mb-4">Summary</h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-lg bg-zinc-800/60 p-3">
                <p className="text-zinc-400">Total Characters</p>
                <p className="text-white text-xl font-semibold">{overview?.characters_total ?? 0}</p>
              </div>
              <div className="rounded-lg bg-zinc-800/60 p-3">
                <p className="text-zinc-400">Total Scripts</p>
                <p className="text-white text-xl font-semibold">{overview?.scripts_total ?? 0}</p>
              </div>
            </div>
          </Card>
        )}

        {activeTab === 'characters' && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {characters.map((char) => (
              <Card key={char.id} className="p-4">
                <div className="aspect-square rounded-lg bg-zinc-800 flex items-center justify-center mb-3 overflow-hidden">
                  {char.avatar_url ? (
                    <img src={char.avatar_url} alt={char.first_name} className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-3xl font-bold text-zinc-400">{char.first_name?.charAt(0) || '?'}</span>
                  )}
                </div>
                <p className="text-white font-medium truncate">{char.first_name}</p>
                <p className="text-xs text-zinc-400 mt-1">{char.is_public ? 'Published' : 'Draft'}</p>
                <Button size="sm" className="mt-3 w-full" onClick={() => navigate(`/create-script?character=${char.id}`)}>
                  New Script
                </Button>
              </Card>
            ))}
            {characters.length === 0 && <p className="text-zinc-400">No characters yet.</p>}
          </div>
        )}

        {activeTab === 'scripts' && (
          <div className="space-y-3">
            {scripts.map((script) => (
              <Card key={script.id} className="p-4 flex items-center justify-between gap-4">
                <div>
                  <p className="text-white font-medium">{script.title}</p>
                  <p className="text-sm text-zinc-400">{script.genre} · {script.status}</p>
                </div>
                <Button variant="secondary" size="sm" onClick={() => navigate(`/edit-script/${script.id}`)}>
                  Edit
                </Button>
              </Card>
            ))}
            {scripts.length === 0 && <p className="text-zinc-400">No scripts yet.</p>}
          </div>
        )}
      </div>
    </MainLayout>
  );
};

export default CreatorCenterPage;


