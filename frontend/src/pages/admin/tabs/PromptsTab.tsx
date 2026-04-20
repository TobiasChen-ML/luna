import React, { useState, useEffect } from 'react';
import { Plus, Search, Edit, Trash2, Play, Loader2, RefreshCw, X } from 'lucide-react';
import { api } from '@/services/api';

interface Prompt {
  name: string;
  content: string;
  description?: string;
}

export default function PromptsTab() {
  const [loading, setLoading] = useState(true);
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchPrompts();
  }, []);

  const fetchPrompts = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/prompts');
      setPrompts(response.data?.prompts || []);
    } catch (error) {
      console.error('Failed to fetch prompts:', error);
      setMessage({ type: 'error', text: '加载提示词失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editingPrompt) return;
    setSaving(true);
    try {
      await api.post(`/admin/prompts/${editingPrompt.name}`, { content: editingPrompt.content });
      setMessage({ type: 'success', text: '保存成功' });
      setEditingPrompt(null);
      fetchPrompts();
    } catch (error) {
      setMessage({ type: 'error', text: '保存失败' });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async (name: string) => {
    try {
      const response = await api.post(`/admin/prompts/${name}/test`, {});
      setMessage({ type: 'success', text: `测试输出: ${response.data?.test_output?.slice(0, 50)}...` });
    } catch (error) {
      setMessage({ type: 'error', text: '测试失败' });
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center py-12"><Loader2 className="w-8 h-8 text-pink-500 animate-spin" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">提示词管理</h2>
          <p className="text-zinc-400 mt-1">编辑和测试系统提示词</p>
        </div>
        <button onClick={fetchPrompts} className="p-2 hover:bg-zinc-800 rounded-lg">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'}`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      <div className="grid gap-4">
        {prompts.map((prompt) => (
          <div key={prompt.name} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-white font-medium">{prompt.name}</h3>
                <p className="text-zinc-500 text-sm">{prompt.description || '无描述'}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleTest(prompt.name)} className="p-2 hover:bg-zinc-700 rounded-lg text-purple-400" title="测试">
                  <Play className="w-4 h-4" />
                </button>
                <button onClick={() => setEditingPrompt(prompt)} className="p-2 hover:bg-zinc-700 rounded-lg text-zinc-400" title="编辑">
                  <Edit className="w-4 h-4" />
                </button>
              </div>
            </div>
            <pre className="text-zinc-400 text-sm bg-zinc-800 p-3 rounded-lg overflow-auto max-h-32">
              {(prompt.content || '').slice(0, 200)}...
            </pre>
          </div>
        ))}
        {prompts.length === 0 && (
          <div className="text-center text-zinc-500 py-8">暂无提示词数据</div>
        )}
      </div>

      {editingPrompt && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 max-w-2xl w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">编辑提示词: {editingPrompt.name}</h3>
              <button onClick={() => setEditingPrompt(null)} className="p-1 hover:bg-zinc-700 rounded"><X className="w-5 h-5" /></button>
            </div>
            <textarea
              value={editingPrompt.content}
              onChange={(e) => setEditingPrompt({ ...editingPrompt, content: e.target.value })}
              className="w-full h-64 p-4 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none resize-none"
            />
            <div className="flex justify-end gap-3 mt-4">
              <button onClick={() => setEditingPrompt(null)} className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm">取消</button>
              <button onClick={handleSave} disabled={saving} className="px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium disabled:opacity-50">{saving ? '保存中...' : '保存'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}