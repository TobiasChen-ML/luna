import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus, Search, Edit, Trash2, MoreVertical,
  Loader2, Wand2, RefreshCw, X, Check, AlertTriangle
} from 'lucide-react';
import { api } from '@/services/api';

interface Character {
  id: string;
  name: string;
  first_name?: string;
  description?: string;
  avatar_url?: string;
  top_category?: string;
  age?: number;
  personality_tags?: string[];
  is_public?: boolean;
  lifecycle_status?: string;
  popularity_score?: number;
  chat_count?: number;
  created_at: string;
  creator_id?: string;
}

export default function CharactersTab() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

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
      
      const response = await api.get(`/admin/api/characters?${params.toString()}`);
      setCharacters(response.data?.items || response.data || []);
      setTotal(response.data?.total || 0);
    } catch (error) {
      console.error('Failed to fetch characters:', error);
      setMessage({ type: 'error', text: '加载角色失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchCharacters();
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setSaving(true);
    try {
      if (deleteTarget === 'batch' && selectedIds.length > 0) {
        await api.post('/admin/api/characters/batch-delete', { ids: selectedIds });
        setSelectedIds([]);
      } else {
        await api.delete(`/admin/api/characters/${deleteTarget}`);
      }
      setMessage({ type: 'success', text: '删除成功' });
      fetchCharacters();
    } catch (error) {
      setMessage({ type: 'error', text: '删除失败' });
    } finally {
      setSaving(false);
      setShowDeleteModal(false);
      setDeleteTarget(null);
    }
  };

  const handleAIFill = async (characterId: string) => {
    setSaving(true);
    try {
      await api.post(`/admin/characters/${characterId}/ai-fill`);
      setMessage({ type: 'success', text: 'AI填充已启动' });
    } catch (error) {
      setMessage({ type: 'error', text: 'AI填充失败' });
    } finally {
      setSaving(false);
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === characters.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(characters.map(c => c.id));
    }
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
          <h2 className="text-2xl font-bold text-white">角色管理</h2>
          <p className="text-zinc-400 mt-1">管理和编辑所有角色 (共 {total} 个)</p>
        </div>
        <button
          onClick={() => navigate('/admin/characters/create')}
          className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          创建角色
        </button>
      </div>

      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'
        }`}>
          {message.type === 'success' ? <Check className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
          {message.text}
          <button onClick={() => setMessage(null)} className="ml-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <div className="flex items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="搜索角色..."
            className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
          />
        </div>
        <button
          onClick={handleSearch}
          className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm"
        >
          搜索
        </button>
        <button
          onClick={fetchCharacters}
          className="p-2 hover:bg-zinc-800 rounded-lg"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {selectedIds.length > 0 && (
        <div className="flex items-center gap-4 p-4 bg-zinc-800/50 rounded-lg">
          <span className="text-sm text-zinc-300">已选择 {selectedIds.length} 个角色</span>
          <button
            onClick={() => {
              setDeleteTarget('batch');
              setShowDeleteModal(true);
            }}
            className="px-3 py-1 bg-red-600 hover:bg-red-500 rounded text-sm"
          >
            批量删除
          </button>
          <button
            onClick={() => setSelectedIds([])}
            className="px-3 py-1 bg-zinc-700 hover:bg-zinc-600 rounded text-sm"
          >
            取消选择
          </button>
        </div>
      )}

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-zinc-800/50">
            <tr>
              <th className="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  checked={selectedIds.length === characters.length && characters.length > 0}
                  onChange={toggleSelectAll}
                  className="rounded border-zinc-600"
                />
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">角色</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">分类</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">状态</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">人气</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">创建时间</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-zinc-300">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {characters.map((character) => (
              <tr key={character.id} className="hover:bg-zinc-800/30">
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(character.id)}
                    onChange={() => toggleSelect(character.id)}
                    className="rounded border-zinc-600"
                  />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    {character.avatar_url ? (
                      <img
                        src={character.avatar_url}
                        alt={character.name}
                        className="w-10 h-10 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-zinc-700 flex items-center justify-center text-sm">
                        {character.name.charAt(0)}
                      </div>
                    )}
                    <div>
                      <p className="text-white font-medium">{character.name}</p>
                      <p className="text-zinc-500 text-sm truncate max-w-xs">
                        {character.description || '无描述'}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-zinc-300 text-sm capitalize">{character.top_category || 'girls'}</span>
                  {character.age && (
                    <span className="text-zinc-500 text-sm ml-1">· {character.age}</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    character.lifecycle_status === 'active'
                      ? 'bg-green-900/50 text-green-400'
                      : character.lifecycle_status === 'draft'
                        ? 'bg-yellow-900/50 text-yellow-400'
                        : 'bg-zinc-700 text-zinc-400'
                  }`}>
                    {character.lifecycle_status || 'active'}
                  </span>
                </td>
                <td className="px-4 py-3 text-zinc-400 text-sm">
                  <div>{character.popularity_score?.toFixed(1) || '0.0'}</div>
                  <div className="text-zinc-600 text-xs">{character.chat_count || 0} chats</div>
                </td>
                <td className="px-4 py-3 text-zinc-400 text-sm">
                  {character.created_at ? new Date(character.created_at).toLocaleDateString() : '-'}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => handleAIFill(character.id)}
                      className="p-2 hover:bg-zinc-700 rounded-lg text-purple-400"
                      title="AI填充"
                    >
                      <Wand2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => navigate(`/admin/characters/${character.id}/edit`)}
                      className="p-2 hover:bg-zinc-700 rounded-lg text-zinc-400"
                      title="编辑"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        setDeleteTarget(character.id);
                        setShowDeleteModal(true);
                      }}
                      className="p-2 hover:bg-zinc-700 rounded-lg text-red-400"
                      title="删除"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {characters.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-zinc-500">
                  暂无角色数据
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {total > 20 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            上一页
          </button>
          <span className="text-zinc-400 text-sm">
            第 {page} 页，共 {Math.ceil(total / 20)} 页
          </span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={page * 20 >= total}
            className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一页
          </button>
        </div>
      )}

      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center gap-3 text-red-400 mb-4">
              <AlertTriangle className="w-6 h-6" />
              <h3 className="text-lg font-semibold text-white">确认删除</h3>
            </div>
            <p className="text-zinc-400 mb-6">
              {deleteTarget === 'batch'
                ? `确定要删除选中的 ${selectedIds.length} 个角色吗？`
                : '确定要删除这个角色吗？此操作无法撤销。'}
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeleteTarget(null);
                }}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm"
              >
                取消
              </button>
              <button
                onClick={handleDelete}
                disabled={saving}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {saving ? '删除中...' : '确认删除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
