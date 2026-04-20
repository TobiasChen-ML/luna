import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Loader2, RefreshCw, X, Copy, Check } from 'lucide-react';
import { api } from '@/services/api';

interface ApiKey {
  id: string;
  name: string;
  key?: string;
  created_at: string;
}

export default function ApiKeysTab() {
  const [loading, setLoading] = useState(true);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKey, setNewKey] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/api-keys');
      setApiKeys(response.data || []);
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newKeyName.trim()) return;
    setSaving(true);
    try {
      const response = await api.post('/admin/api-keys', { name: newKeyName });
      setNewKey(response.data?.key);
      setNewKeyName('');
      fetchApiKeys();
    } catch (error) {
      setMessage({ type: 'error', text: '创建失败' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (keyId: string) => {
    try {
      await api.delete(`/admin/api-keys/${keyId}`);
      setMessage({ type: 'success', text: '已删除' });
      fetchApiKeys();
    } catch (error) {
      setMessage({ type: 'error', text: '删除失败' });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return <div className="flex items-center justify-center py-12"><Loader2 className="w-8 h-8 text-pink-500 animate-spin" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">API密钥管理</h2>
          <p className="text-zinc-400 mt-1">创建和管理API访问密钥</p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium">
          <Plus className="w-4 h-4" />创建密钥
        </button>
      </div>

      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'}`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-zinc-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">名称</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">密钥前缀</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">创建时间</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-zinc-300">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {apiKeys.map((apiKey) => (
              <tr key={apiKey.id} className="hover:bg-zinc-800/30">
                <td className="px-4 py-3 text-white font-medium">{apiKey.name}</td>
                <td className="px-4 py-3 text-zinc-400 font-mono">{apiKey.key?.slice(0, 12) || 'sk_live_'}...</td>
                <td className="px-4 py-3 text-zinc-400 text-sm">{new Date(apiKey.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-3">
                  <button onClick={() => handleDelete(apiKey.id)} className="p-2 hover:bg-zinc-700 rounded-lg text-red-400" title="删除">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
            {apiKeys.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-zinc-500">暂无API密钥</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">创建API密钥</h3>
            {newKey ? (
              <div className="space-y-4">
                <p className="text-zinc-400">密钥已创建，请立即复制保存。此密钥只显示一次。</p>
                <div className="flex items-center gap-2 p-3 bg-zinc-800 rounded-lg">
                  <code className="text-sm text-pink-400 flex-1 overflow-auto">{newKey}</code>
                  <button onClick={() => copyToClipboard(newKey)} className="p-1 hover:bg-zinc-700 rounded">
                    {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
                <button onClick={() => { setShowCreateModal(false); setNewKey(null); }} className="w-full py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm">关闭</button>
              </div>
            ) : (
              <div className="space-y-4">
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="密钥名称"
                  className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
                <div className="flex gap-3">
                  <button onClick={() => setShowCreateModal(false)} className="flex-1 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm">取消</button>
                  <button onClick={handleCreate} disabled={saving || !newKeyName.trim()} className="flex-1 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium disabled:opacity-50">{saving ? '创建中...' : '创建'}</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}