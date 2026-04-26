import React, { useEffect, useState } from 'react';
import { Loader2, RefreshCw, Search } from 'lucide-react';
import { api } from '@/services/api';

interface Character {
  id: string;
  name: string;
  first_name?: string;
  description?: string;
  top_category?: string;
  lifecycle_status?: string;
  created_at?: string;
  creator_id?: string;
}

export default function UserCharactersTab() {
  const [loading, setLoading] = useState(true);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchCharacters();
  }, [page, searchQuery]);

  const fetchCharacters = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '20',
      });
      if (searchQuery) {
        params.set('search', searchQuery);
      }
      const response = await api.get(`/admin/api/user-characters?${params.toString()}`);
      setCharacters(response.data?.items || []);
      setTotal(response.data?.total || 0);
    } catch (error) {
      console.error('Failed to fetch user characters:', error);
      setCharacters([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchCharacters();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">角色用户管理</h2>
          <p className="text-zinc-400 mt-1">仅显示用户创建角色（共 {total} 个）</p>
        </div>
        <button onClick={fetchCharacters} className="p-2 hover:bg-zinc-800 rounded-lg">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="搜索用户角色..."
            className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
          />
        </div>
        <button
          onClick={handleSearch}
          className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm"
        >
          搜索
        </button>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-zinc-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">角色</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">创建者</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">分类</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">状态</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">创建时间</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {characters.map((character) => (
              <tr key={character.id} className="hover:bg-zinc-800/30">
                <td className="px-4 py-3">
                  <p className="text-white font-medium">{character.first_name || character.name}</p>
                  <p className="text-zinc-500 text-sm truncate max-w-xs">{character.description || '-'}</p>
                </td>
                <td className="px-4 py-3 text-zinc-300 text-sm">{character.creator_id || '-'}</td>
                <td className="px-4 py-3 text-zinc-300 text-sm">{character.top_category || '-'}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 rounded-full text-xs bg-zinc-700 text-zinc-300">
                    {character.lifecycle_status || 'draft'}
                  </span>
                </td>
                <td className="px-4 py-3 text-zinc-400 text-sm">
                  {character.created_at ? new Date(character.created_at).toLocaleDateString() : '-'}
                </td>
              </tr>
            ))}
            {characters.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-zinc-500">
                  暂无用户角色数据
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {total > 20 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            上一页
          </button>
          <span className="text-zinc-400 text-sm">
            第 {page} 页，共 {Math.ceil(total / 20)} 页
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page * 20 >= total}
            className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
}
