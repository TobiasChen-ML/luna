import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Play, Loader2, RefreshCw, X, Save, Eye, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '@/services/api';

interface PromptTemplate {
  id: string;
  name: string;
  category: string;
  content: string;
  variables: Record<string, any> | null;
  priority: number;
  description: string | null;
  is_active: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

interface Category {
  value: string;
  label: string;
}

export default function TemplatesTab() {
  const [loading, setLoading] = useState(true);
  const [prompts, setPrompts] = useState<PromptTemplate[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<PromptTemplate | null>(null);
  const [testingPrompt, setTestingPrompt] = useState<PromptTemplate | null>(null);
  const [testOutput, setTestOutput] = useState<string | null>(null);
  const [testVariables, setTestVariables] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [expandedPrompt, setExpandedPrompt] = useState<string | null>(null);

  const [newPrompt, setNewPrompt] = useState({
    name: '',
    category: 'character_setting',
    content: '',
    description: '',
    priority: 100,
    variables: {} as Record<string, any>,
  });

  useEffect(() => {
    fetchPrompts();
    fetchCategories();
  }, []);

  const fetchPrompts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterCategory) params.set('category', filterCategory);
      params.set('include_inactive', 'true');
      const response = await api.get(`/admin/prompts?${params.toString()}`);
      setPrompts(response.data || []);
    } catch (error) {
      console.error('Failed to fetch prompts:', error);
      setMessage({ type: 'error', text: '加载提示词失败' });
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get('/admin/prompts/categories');
      setCategories(response.data || []);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  useEffect(() => {
    if (!loading) fetchPrompts();
  }, [filterCategory]);

  const handleCreate = async () => {
    if (!newPrompt.name || !newPrompt.content) {
      setMessage({ type: 'error', text: '名称和内容不能为空' });
      return;
    }
    setSaving(true);
    try {
      await api.post('/admin/prompts', newPrompt);
      setMessage({ type: 'success', text: '创建成功' });
      setShowCreateForm(false);
      setNewPrompt({ name: '', category: 'character_setting', content: '', description: '', priority: 100, variables: {} });
      fetchPrompts();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || '创建失败' });
    } finally {
      setSaving(false);
    }
  };

  const handleSave = async () => {
    if (!editingPrompt) return;
    setSaving(true);
    try {
      await api.put(`/admin/prompts/${editingPrompt.name}`, {
        content: editingPrompt.content,
        description: editingPrompt.description,
        priority: editingPrompt.priority,
      });
      setMessage({ type: 'success', text: '保存成功' });
      setEditingPrompt(null);
      fetchPrompts();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || '保存失败' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`确定要停用提示词 "${name}" 吗？`)) return;
    try {
      await api.delete(`/admin/prompts/${name}`);
      setMessage({ type: 'success', text: '已停用' });
      fetchPrompts();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || '操作失败' });
    }
  };

  const handleTest = async () => {
    if (!testingPrompt) return;
    setTesting(true);
    setTestOutput(null);
    try {
      const response = await api.post(`/admin/prompts/${testingPrompt.name}/test`, {
        variables: testVariables,
      });
      setTestOutput(response.data?.rendered || '无输出');
    } catch (err: any) {
      setTestOutput(`错误: ${err.response?.data?.detail || '测试失败'}`);
    } finally {
      setTesting(false);
    }
  };

  const openTestModal = (prompt: PromptTemplate) => {
    setTestingPrompt(prompt);
    const vars = prompt.variables || {};
    const defaults: Record<string, any> = {};
    for (const [key, value] of Object.entries(vars)) {
      defaults[key] = value ?? '';
    }
    setTestVariables(defaults);
    setTestOutput(null);
  };

  const getCategoryLabel = (cat: string) => {
    return categories.find(c => c.value === cat)?.label || cat.replace(/_/g, ' ');
  };

  if (loading) {
    return <div className="flex items-center justify-center py-12"><Loader2 className="w-8 h-8 text-pink-500 animate-spin" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">提示词管理</h2>
          <p className="text-zinc-400 mt-1">管理系统提示词模板</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-white"
          >
            <option value="">全部类型</option>
            {categories.map(c => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
          <button onClick={fetchPrompts} className="p-2 hover:bg-zinc-800 rounded-lg text-zinc-400">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium"
          >
            <Plus className="w-4 h-4" />创建模板
          </button>
        </div>
      </div>

      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'}`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {showCreateForm && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">创建提示词模板</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm text-zinc-400 mb-1">名称</label>
              <input
                type="text"
                value={newPrompt.name}
                onChange={(e) => setNewPrompt({ ...newPrompt, name: e.target.value })}
                placeholder="e.g. my_custom_prompt"
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-zinc-400 mb-1">类型</label>
              <select
                value={newPrompt.category}
                onChange={(e) => setNewPrompt({ ...newPrompt, category: e.target.value })}
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
              >
                {categories.map(c => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-zinc-400 mb-1">优先级 (1-1000)</label>
              <input
                type="number"
                value={newPrompt.priority}
                onChange={(e) => setNewPrompt({ ...newPrompt, priority: parseInt(e.target.value) || 100 })}
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
              />
            </div>
          </div>
          <div className="mb-4">
            <label className="block text-sm text-zinc-400 mb-1">描述</label>
            <input
              type="text"
              value={newPrompt.description}
              onChange={(e) => setNewPrompt({ ...newPrompt, description: e.target.value })}
              placeholder="模板描述"
              className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm text-zinc-400 mb-1">内容 (支持 Jinja2 模板语法)</label>
            <textarea
              value={newPrompt.content}
              onChange={(e) => setNewPrompt({ ...newPrompt, content: e.target.value })}
              rows={8}
              placeholder="输入提示词内容..."
              className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 text-sm font-mono resize-none focus:border-pink-500 focus:outline-none"
            />
          </div>
          <div className="flex justify-end gap-3">
            <button onClick={() => setShowCreateForm(false)} className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm">取消</button>
            <button onClick={handleCreate} disabled={saving} className="px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium disabled:opacity-50">
              {saving ? '创建中...' : '创建'}
            </button>
          </div>
        </div>
      )}

      <div className="grid gap-3">
        {prompts.map((prompt) => (
          <div key={prompt.name} className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-zinc-800/30"
              onClick={() => setExpandedPrompt(expandedPrompt === prompt.name ? null : prompt.name)}
            >
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  prompt.category === 'safety_rules' ? 'bg-red-900/50 text-red-300' :
                  prompt.category === 'script_instruction' ? 'bg-purple-900/50 text-purple-300' :
                  prompt.category === 'character_setting' ? 'bg-blue-900/50 text-blue-300' :
                  prompt.category === 'relationship_state' ? 'bg-pink-900/50 text-pink-300' :
                  prompt.category === 'world_setting' ? 'bg-green-900/50 text-green-300' :
                  prompt.category === 'memory_context' ? 'bg-yellow-900/50 text-yellow-300' :
                  prompt.category === 'plot_context' ? 'bg-orange-900/50 text-orange-300' :
                  prompt.category === 'output_instruction' ? 'bg-cyan-900/50 text-cyan-300' :
                  'bg-zinc-700 text-zinc-300'
                }`}>
                  {getCategoryLabel(prompt.category)}
                </span>
                <div>
                  <h3 className="text-white font-medium text-sm">{prompt.name}</h3>
                  {prompt.description && <p className="text-zinc-500 text-xs mt-0.5">{prompt.description}</p>}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-zinc-600 text-xs">P{prompt.priority}</span>
                {!prompt.is_active && <span className="px-1.5 py-0.5 bg-red-900/50 text-red-400 rounded text-xs">停用</span>}
                <button
                  onClick={(e) => { e.stopPropagation(); openTestModal(prompt); }}
                  className="p-1.5 hover:bg-zinc-700 rounded-lg text-purple-400"
                  title="测试"
                >
                  <Play className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); setEditingPrompt({ ...prompt }); }}
                  className="p-1.5 hover:bg-zinc-700 rounded-lg text-zinc-400"
                  title="编辑"
                >
                  <Edit className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(prompt.name); }}
                  className="p-1.5 hover:bg-zinc-700 rounded-lg text-red-400"
                  title="停用"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
                {expandedPrompt === prompt.name ? <ChevronUp className="w-4 h-4 text-zinc-500" /> : <ChevronDown className="w-4 h-4 text-zinc-500" />}
              </div>
            </div>

            {expandedPrompt === prompt.name && (
              <div className="px-4 pb-4 border-t border-zinc-800">
                <pre className="text-zinc-400 text-xs bg-zinc-800 p-3 rounded-lg overflow-auto max-h-64 mt-3 whitespace-pre-wrap font-mono">
                  {prompt.content}
                </pre>
                {prompt.variables && Object.keys(prompt.variables).length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-zinc-500 mb-1">模板变量:</p>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(prompt.variables).map(([key, value]) => (
                        <span key={key} className="px-2 py-0.5 bg-zinc-800 rounded text-xs text-zinc-400">
                          {key}: {JSON.stringify(value)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {prompts.length === 0 && (
          <div className="text-center text-zinc-500 py-8">
            暂无提示词数据
            <button onClick={async () => {
              try {
                await api.post('/admin/prompts/initialize-defaults');
                setMessage({ type: 'success', text: '默认模板已初始化' });
                fetchPrompts();
              } catch (err: any) {
                setMessage({ type: 'error', text: '初始化失败' });
              }
            }} className="ml-2 text-pink-400 hover:text-pink-300 underline text-sm">
              初始化默认模板
            </button>
          </div>
        )}
      </div>

      {editingPrompt && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">编辑提示词: {editingPrompt.name}</h3>
              <button onClick={() => setEditingPrompt(null)} className="p-1 hover:bg-zinc-700 rounded"><X className="w-5 h-5" /></button>
            </div>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-1">类型</label>
                <span className="px-2 py-1 rounded text-xs bg-zinc-700 text-zinc-300">{getCategoryLabel(editingPrompt.category)}</span>
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">优先级</label>
                <input
                  type="number"
                  value={editingPrompt.priority}
                  onChange={(e) => setEditingPrompt({ ...editingPrompt, priority: parseInt(e.target.value) || 100 })}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
                />
              </div>
            </div>
            <div className="mb-4">
              <label className="block text-sm text-zinc-400 mb-1">描述</label>
              <input
                type="text"
                value={editingPrompt.description || ''}
                onChange={(e) => setEditingPrompt({ ...editingPrompt, description: e.target.value })}
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm text-zinc-400 mb-1">内容 (支持 Jinja2 语法: {'{{ }}'}, {'{% %}'})</label>
              <textarea
                value={editingPrompt.content}
                onChange={(e) => setEditingPrompt({ ...editingPrompt, content: e.target.value })}
                rows={16}
                className="w-full p-4 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 text-sm font-mono resize-none focus:border-pink-500 focus:outline-none"
              />
            </div>
            <div className="flex justify-end gap-3">
              <button onClick={() => setEditingPrompt(null)} className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm">取消</button>
              <button onClick={handleSave} disabled={saving} className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium disabled:opacity-50">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}

      {testingPrompt && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">测试提示词: {testingPrompt.name}</h3>
              <button onClick={() => { setTestingPrompt(null); setTestOutput(null); }} className="p-1 hover:bg-zinc-700 rounded"><X className="w-5 h-5" /></button>
            </div>

            {Object.keys(testVariables).length > 0 && (
              <div className="mb-4">
                <label className="block text-sm text-zinc-400 mb-2">输入变量</label>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(testVariables).map(([key, value]) => (
                    <div key={key}>
                      <label className="block text-xs text-zinc-500 mb-1">{key}</label>
                      <input
                        type="text"
                        value={typeof value === 'object' ? JSON.stringify(value) : String(value ?? '')}
                        onChange={(e) => {
                          let parsed: any = e.target.value;
                          try { parsed = JSON.parse(e.target.value); } catch {}
                          setTestVariables({ ...testVariables, [key]: parsed });
                        }}
                        className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm text-zinc-400 mb-1">模板内容</label>
              <pre className="text-zinc-500 text-xs bg-zinc-800 p-3 rounded-lg max-h-32 overflow-auto whitespace-pre-wrap font-mono">
                {testingPrompt.content.slice(0, 300)}...
              </pre>
            </div>

            <div className="flex gap-3 mb-4">
              <button
                onClick={handleTest}
                disabled={testing}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {testing ? '渲染中...' : '渲染预览'}
              </button>
            </div>

            {testOutput !== null && (
              <div>
                <label className="block text-sm text-zinc-400 mb-1">渲染结果</label>
                <pre className="text-green-300 text-sm bg-zinc-800 border border-green-900/50 p-4 rounded-lg max-h-64 overflow-auto whitespace-pre-wrap font-mono">
                  {testOutput}
                </pre>
              </div>
            )}

            <div className="flex justify-end mt-4">
              <button onClick={() => { setTestingPrompt(null); setTestOutput(null); }} className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm">关闭</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
