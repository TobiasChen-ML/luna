import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus, Search, Edit, Trash2, Loader2, X, Check, AlertTriangle, Filter, ChevronDown
} from 'lucide-react';
import { api } from '@/services/api';

interface Story {
  id: string;
  title: string;
  title_en: string;
  summary: string;
  emotion_tones: string;
  relation_types: string;
  character_gender: string;
  era: string;
  profession: string;
  status: string;
  popularity: number;
  created_at: string;
  updated_at: string;
}

interface ScriptTag {
  id: string;
  category: string;
  name: string;
  name_en?: string;
}

interface TagsData {
  emotion_tones: ScriptTag[];
  relation_types: ScriptTag[];
  eras: ScriptTag[];
  character_genders: ScriptTag[];
}

const STATUSES = ['all', 'draft', 'pending', 'published'];

const STATUS_LABELS: Record<string, string> = {
  all: '全部', draft: '草稿', pending: '待审核', published: '已发布'
};

export default function StoriesTab() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stories, setStories] = useState<Story[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  const [statusFilter, setStatusFilter] = useState('all');
  const [emotionToneFilter, setEmotionToneFilter] = useState('');
  const [relationTypeFilter, setRelationTypeFilter] = useState('');
  const [characterGenderFilter, setCharacterGenderFilter] = useState('');
  const [eraFilter, setEraFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  
  const [tags, setTags] = useState<TagsData>({
    emotion_tones: [],
    relation_types: [],
    eras: [],
    character_genders: []
  });
  const [tagsLoading, setTagsLoading] = useState(true);

  const pageSize = 50;

  useEffect(() => {
    fetchTags();
  }, []);

  useEffect(() => {
    fetchStories();
  }, [page, statusFilter, emotionToneFilter, relationTypeFilter, characterGenderFilter, eraFilter]);

  const fetchTags = async () => {
    try {
      const response = await api.get('/script-library/tags');
      setTags(response.data || {});
    } catch (error) {
      console.error('Failed to fetch tags:', error);
    } finally {
      setTagsLoading(false);
    }
  };

  const getTagName = (category: keyof TagsData, id: string): string => {
    const tag = tags[category]?.find(t => t.id === id);
    return tag?.name || id;
  };

  const fetchStories = async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (searchQuery.trim()) params.search = searchQuery;
      if (statusFilter !== 'all') params.status = statusFilter;
      if (emotionToneFilter) params.emotion_tone = emotionToneFilter;
      if (relationTypeFilter) params.relation_type = relationTypeFilter;
      if (characterGenderFilter) params.character_gender = characterGenderFilter;
      if (eraFilter) params.era = eraFilter;
      
      const response = await api.get('/admin/stories', { params });
      setStories(response.data?.stories || []);
      setTotal(response.data?.total || 0);
    } catch (error) {
      console.error('Failed to fetch stories:', error);
      setMessage({ type: 'error', text: '加载剧本失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setSaving(true);
    try {
      if (deleteTarget === 'batch' && selectedIds.length > 0) {
        await api.post('/admin/api/stories/batch-delete', { ids: selectedIds });
        setSelectedIds([]);
      } else {
        await api.post(`/admin/stories/${deleteTarget}/delete`);
      }
      setMessage({ type: 'success', text: '删除成功' });
      fetchStories();
    } catch (error) {
      setMessage({ type: 'error', text: '删除失败' });
    } finally {
      setSaving(false);
      setShowDeleteModal(false);
      setDeleteTarget(null);
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === stories.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(stories.map(s => s.id));
    }
  };

  const clearFilters = () => {
    setStatusFilter('all');
    setEmotionToneFilter('');
    setRelationTypeFilter('');
    setCharacterGenderFilter('');
    setEraFilter('');
    setSearchQuery('');
  };

  const hasActiveFilters = statusFilter !== 'all' || emotionToneFilter || relationTypeFilter || characterGenderFilter || eraFilter || searchQuery;

  if (loading && stories.length === 0) {
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
          <h2 className="text-2xl font-bold text-white">剧本管理</h2>
          <p className="text-zinc-400 mt-1">共 {total} 个剧本</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${
              showFilters || hasActiveFilters
                ? 'bg-purple-600 text-white'
                : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'
            }`}
          >
            <Filter className="w-4 h-4" />
            筛选
            <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
          <button
            onClick={() => navigate('/admin/stories/create')}
            className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            创建剧本
          </button>
        </div>
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

      {showFilters && (
        <div className="bg-zinc-800/50 rounded-xl p-4 space-y-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-xs text-zinc-400 mb-1">搜索</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && fetchStories()}
                  placeholder="标题、标题(英)、摘要..."
                  className="w-full pl-10 pr-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="min-w-[120px]">
              <label className="block text-xs text-zinc-400 mb-1">状态</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
              >
                {STATUSES.map(s => (
                  <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                ))}
              </select>
            </div>

            <div className="min-w-[140px]">
              <label className="block text-xs text-zinc-400 mb-1">情感基调</label>
              <select
                value={emotionToneFilter}
                onChange={(e) => setEmotionToneFilter(e.target.value)}
                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
              >
                <option value="">全部</option>
                {tags.emotion_tones.map(t => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>

            <div className="min-w-[140px]">
              <label className="block text-xs text-zinc-400 mb-1">关系类型</label>
              <select
                value={relationTypeFilter}
                onChange={(e) => setRelationTypeFilter(e.target.value)}
                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
              >
                <option value="">全部</option>
                {tags.relation_types.map(t => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>

            <div className="min-w-[120px]">
              <label className="block text-xs text-zinc-400 mb-1">角色性别</label>
              <select
                value={characterGenderFilter}
                onChange={(e) => setCharacterGenderFilter(e.target.value)}
                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
              >
                <option value="">全部</option>
                {tags.character_genders.map(g => (
                  <option key={g.id} value={g.id}>{g.name}</option>
                ))}
              </select>
            </div>

            <div className="min-w-[140px]">
              <label className="block text-xs text-zinc-400 mb-1">时代背景</label>
              <select
                value={eraFilter}
                onChange={(e) => setEraFilter(e.target.value)}
                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
              >
                <option value="">全部</option>
                {tags.eras.map(e => (
                  <option key={e.id} value={e.id}>{e.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2">
            {hasActiveFilters && (
              <button onClick={clearFilters} className="px-4 py-2 text-zinc-400 hover:text-white text-sm">
                清除筛选
              </button>
            )}
            <button onClick={fetchStories} className="px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm">
              应用筛选
            </button>
          </div>
        </div>
      )}

      {selectedIds.length > 0 && (
        <div className="flex items-center gap-4 p-4 bg-zinc-800/50 rounded-lg">
          <span className="text-sm text-zinc-300">已选择 {selectedIds.length} 个剧本</span>
          <button
            onClick={() => { setDeleteTarget('batch'); setShowDeleteModal(true); }}
            className="px-3 py-1 bg-red-600 hover:bg-red-500 rounded text-sm"
          >
            批量删除
          </button>
          <button onClick={() => setSelectedIds([])} className="px-3 py-1 bg-zinc-700 hover:bg-zinc-600 rounded text-sm">
            取消选择
          </button>
        </div>
      )}

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-zinc-800/50">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input type="checkbox" checked={selectedIds.length === stories.length && stories.length > 0} onChange={toggleSelectAll} className="rounded border-zinc-600" />
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">标题</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">情感</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">关系</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">性别</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">时代</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">状态</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">创建时间</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-zinc-300">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {stories.map((story) => (
                <tr key={story.id} className="hover:bg-zinc-800/30">
                  <td className="px-4 py-3">
                    <input type="checkbox" checked={selectedIds.includes(story.id)} onChange={() => toggleSelect(story.id)} className="rounded border-zinc-600" />
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <p className="text-white font-medium">{story.title}</p>
                      {story.title_en && <p className="text-zinc-500 text-xs">{story.title_en}</p>}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 bg-pink-900/30 text-pink-300 rounded text-xs">
                      {story.emotion_tones ? JSON.parse(story.emotion_tones).map((t: string) => getTagName('emotion_tones', t)).join(', ') : '-'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 bg-purple-900/30 text-purple-300 rounded text-xs">
                      {story.relation_types ? JSON.parse(story.relation_types).map((t: string) => getTagName('relation_types', t)).join(', ') : '-'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-zinc-400 text-sm">
                    {story.character_gender ? getTagName('character_genders', story.character_gender) : '-'}
                  </td>
                  <td className="px-4 py-3 text-zinc-400 text-sm">
                    {story.era ? getTagName('eras', story.era) : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      story.status === 'published' ? 'bg-green-900/50 text-green-400' : 
                      story.status === 'pending' ? 'bg-yellow-900/50 text-yellow-400' : 
                      'bg-zinc-700 text-zinc-400'
                    }`}>
                      {STATUS_LABELS[story.status] || story.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-zinc-400 text-sm">
                    {story.created_at ? new Date(story.created_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => navigate(`/admin/stories/${story.id}/edit`)} className="p-2 hover:bg-zinc-700 rounded-lg text-zinc-400" title="编辑">
                        <Edit className="w-4 h-4" />
                      </button>
                      <button onClick={() => { setDeleteTarget(story.id); setShowDeleteModal(true); }} className="p-2 hover:bg-zinc-700 rounded-lg text-red-400" title="删除">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {stories.length === 0 && (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-zinc-500">暂无剧本数据</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {total > pageSize && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-zinc-400">
            显示 {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, total)} / {total}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <span className="px-3 py-1 text-zinc-300">{page}</span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page * pageSize >= total}
              className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
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
              {deleteTarget === 'batch' ? `确定要删除选中的 ${selectedIds.length} 个剧本吗？` : '确定要删除这个剧本吗？此操作无法撤销。'}
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => { setShowDeleteModal(false); setDeleteTarget(null); }} className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm">取消</button>
              <button onClick={handleDelete} disabled={saving} className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm font-medium disabled:opacity-50">
                {saving ? '删除中...' : '确认删除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
