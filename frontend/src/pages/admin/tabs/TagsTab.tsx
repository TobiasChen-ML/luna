import React, { useState, useEffect } from 'react';
import {
  Plus, Edit, Trash2, Loader2, X, Check, AlertTriangle, Tags, ChevronDown, Search
} from 'lucide-react';
import { api } from '@/services/api';

interface Tag {
  id: string;
  category: string;
  name: string;
  name_en?: string;
  description?: string;
  examples?: string[];
  parent_id?: string;
}

const CATEGORIES = [
  { id: 'emotion_tones', name: '情感基调' },
  { id: 'relation_types', name: '关系类型' },
  { id: 'contrast_types', name: '反差类型' },
  { id: 'eras', name: '时代背景' },
  { id: 'professions', name: '职业' },
  { id: 'gender_targets', name: '目标受众' },
  { id: 'character_genders', name: '角色性别' },
  { id: 'lengths', name: '篇幅' },
  { id: 'age_ratings', name: '年龄分级' },
];

const DEFAULT_TAG: Partial<Tag> = {
  id: '',
  category: 'relation_types',
  name: '',
  name_en: '',
  description: '',
  examples: [],
};

export default function TagsTab() {
  const [loading, setLoading] = useState(true);
  const [tags, setTags] = useState<Tag[]>([]);
  const [total, setTotal] = useState(0);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  
  const [showModal, setShowModal] = useState(false);
  const [editingTag, setEditingTag] = useState<Partial<Tag>>({ ...DEFAULT_TAG });
  const [isNew, setIsNew] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Tag | null>(null);

  useEffect(() => {
    fetchTags();
  }, [categoryFilter]);

  const fetchTags = async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { page_size: 500 };
      if (categoryFilter) params.category = categoryFilter;
      
      const response = await api.get('/admin/tags', { params });
      let data = response.data?.tags || [];
      
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        data = data.filter((t: Tag) => 
          t.id.toLowerCase().includes(query) || 
          t.name.toLowerCase().includes(query) ||
          (t.name_en && t.name_en.toLowerCase().includes(query))
        );
      }
      
      setTags(data);
      setTotal(response.data?.total || data.length);
    } catch (error) {
      console.error('Failed to fetch tags:', error);
      setMessage({ type: 'error', text: '加载标签失败' });
    } finally {
      setLoading(false);
    }
  };

  const getCategoryName = (categoryId: string): string => {
    return CATEGORIES.find(c => c.id === categoryId)?.name || categoryId;
  };

  const openCreateModal = () => {
    setEditingTag({ ...DEFAULT_TAG, category: categoryFilter || 'relation_types' });
    setIsNew(true);
    setShowModal(true);
  };

  const openEditModal = (tag: Tag) => {
    setEditingTag({ ...tag, examples: tag.examples || [] });
    setIsNew(false);
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!editingTag.id?.trim() || !editingTag.category || !editingTag.name?.trim()) {
      setMessage({ type: 'error', text: 'ID、分类和名称为必填项' });
      return;
    }
    
    setSaving(true);
    try {
      if (isNew) {
        await api.post('/admin/tags', editingTag);
        setMessage({ type: 'success', text: '创建成功' });
      } else {
        await api.put(`/admin/tags/${editingTag.id}`, editingTag);
        setMessage({ type: 'success', text: '更新成功' });
      }
      setShowModal(false);
      fetchTags();
    } catch (error: any) {
      const detail = error?.response?.data?.detail || '操作失败';
      setMessage({ type: 'error', text: detail });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setSaving(true);
    try {
      await api.delete(`/admin/tags/${deleteTarget.id}`);
      setMessage({ type: 'success', text: '删除成功' });
      setShowDeleteModal(false);
      setDeleteTarget(null);
      fetchTags();
    } catch (error) {
      setMessage({ type: 'error', text: '删除失败' });
    } finally {
      setSaving(false);
    }
  };

  const groupedTags = React.useMemo(() => {
    const groups: Record<string, Tag[]> = {};
    for (const tag of tags) {
      if (!groups[tag.category]) groups[tag.category] = [];
      groups[tag.category].push(tag);
    }
    return groups;
  }, [tags]);

  if (loading && tags.length === 0) {
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
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Tags className="w-7 h-7" />
            标签管理
          </h2>
          <p className="text-zinc-400 mt-1">共 {total} 个标签</p>
        </div>
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchTags()}
              placeholder="搜索标签..."
              className="pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
            />
          </div>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
          >
            <option value="">全部分类</option>
            {CATEGORIES.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            新建标签
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

      {Object.entries(groupedTags).map(([category, categoryTags]) => (
        <div key={category} className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="bg-zinc-800/50 px-4 py-3 border-b border-zinc-800">
            <h3 className="text-lg font-semibold text-white">
              {getCategoryName(category)}
              <span className="ml-2 text-sm font-normal text-zinc-400">({categoryTags.length})</span>
            </h3>
          </div>
          <div className="p-4">
            <div className="flex flex-wrap gap-2">
              {categoryTags.map(tag => (
                <div
                  key={tag.id}
                  className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800 rounded-lg group hover:bg-zinc-700 transition-colors"
                >
                  <div className="text-sm">
                    <span className="text-white">{tag.name}</span>
                    {tag.name_en && <span className="text-zinc-500 ml-1">({tag.name_en})</span>}
                  </div>
                  <span className="text-xs text-zinc-600">{tag.id}</span>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => openEditModal(tag)}
                      className="p-1 hover:bg-zinc-600 rounded text-zinc-400 hover:text-white"
                    >
                      <Edit className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => { setDeleteTarget(tag); setShowDeleteModal(true); }}
                      className="p-1 hover:bg-red-600 rounded text-zinc-400 hover:text-red-300"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 max-w-lg w-full mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">
              {isNew ? '新建标签' : '编辑标签'}
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-1">ID *</label>
                <input
                  type="text"
                  value={editingTag.id || ''}
                  onChange={(e) => setEditingTag(prev => ({ ...prev, id: e.target.value }))}
                  disabled={!isNew}
                  placeholder="如: principal_student"
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none disabled:opacity-50"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">分类 *</label>
                <select
                  value={editingTag.category || ''}
                  onChange={(e) => setEditingTag(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                >
                  {CATEGORIES.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">名称 (中文) *</label>
                <input
                  type="text"
                  value={editingTag.name || ''}
                  onChange={(e) => setEditingTag(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="如: 校长×学生"
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">名称 (英文)</label>
                <input
                  type="text"
                  value={editingTag.name_en || ''}
                  onChange={(e) => setEditingTag(prev => ({ ...prev, name_en: e.target.value }))}
                  placeholder="如: Principal x Student"
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">描述</label>
                <textarea
                  value={editingTag.description || ''}
                  onChange={(e) => setEditingTag(prev => ({ ...prev, description: e.target.value }))}
                  rows={2}
                  placeholder="标签描述..."
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
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
              确定要删除标签 <span className="text-white">「{deleteTarget?.name}」</span> 吗？此操作无法撤销。
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => { setShowDeleteModal(false); setDeleteTarget(null); }}
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
