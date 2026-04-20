import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Loader2, RefreshCw, X, Play, Pause, CloudDownload, Edit2, Volume2, Search } from 'lucide-react';
import { api } from '@/services/api';

interface Voice {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  preview_url?: string;
  provider: string;
  provider_voice_id: string;
  model_id?: string;
  language: string;
  gender: string;
  tone?: string;
  settings?: Record<string, unknown>;
  is_active: boolean;
  usage_count: number;
  last_used_at?: string;
  created_at: string;
  updated_at?: string;
}

interface SyncResult {
  success: boolean;
  synced?: number;
  skipped?: number;
  total?: number;
  error?: string;
}

const PROVIDER_LABELS: Record<string, string> = {
  elevenlabs: 'ElevenLabs',
  dashscope: '通义千问',
};

const LANGUAGE_LABELS: Record<string, string> = {
  en: 'English',
  zh: '中文',
  ja: '日本語',
  ko: '한국어',
  multi: '多语言',
};

const TONE_LABELS: Record<string, string> = {
  warm: '温暖',
  seductive: '诱惑',
  calm: '平静',
  lively: '活泼',
  sweet: '甜美',
  mature: '成熟',
  elegant: '优雅',
  asmr: 'ASMR',
  husky: '沙哑',
  professional: '专业',
  friendly: '友好',
  expressive: '表现力',
  news: '新闻',
  confident: '自信',
};

export default function VoicesTab() {
  const [loading, setLoading] = useState(true);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  
  const [filters, setFilters] = useState({
    provider: '',
    language: '',
    gender: '',
    tone: '',
  });
  
  const [showFormModal, setShowFormModal] = useState(false);
  const [editingVoice, setEditingVoice] = useState<Voice | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    provider: 'elevenlabs',
    provider_voice_id: '',
    model_id: '',
    language: 'en',
    gender: 'female',
    tone: '',
    settings: {} as Record<string, unknown>,
  });
  
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);
  const [previewLoading, setPreviewLoading] = useState<string | null>(null);

  useEffect(() => {
    fetchVoices();
  }, [page, filters]);

  useEffect(() => {
    return () => {
      if (audioElement) {
        audioElement.pause();
        audioElement.src = '';
      }
    };
  }, [audioElement]);

  const fetchVoices = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('page_size', '50');
      if (filters.provider) params.append('provider', filters.provider);
      if (filters.language) params.append('language', filters.language);
      if (filters.gender) params.append('gender', filters.gender);
      if (filters.tone) params.append('tone', filters.tone);
      
      const response = await api.get(`/admin/api/voices?${params.toString()}`);
      setVoices(response.data?.voices || []);
      setTotal(response.data?.total || 0);
    } catch (error) {
      console.error('Failed to fetch voices:', error);
      setMessage({ type: 'error', text: '获取音色列表失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingVoice(null);
    setFormData({
      name: '',
      display_name: '',
      description: '',
      provider: 'elevenlabs',
      provider_voice_id: '',
      model_id: '',
      language: 'en',
      gender: 'female',
      tone: '',
      settings: {},
    });
    setShowFormModal(true);
  };

  const handleEdit = (voice: Voice) => {
    setEditingVoice(voice);
    setFormData({
      name: voice.name,
      display_name: voice.display_name || '',
      description: voice.description || '',
      provider: voice.provider,
      provider_voice_id: voice.provider_voice_id,
      model_id: voice.model_id || '',
      language: voice.language,
      gender: voice.gender,
      tone: voice.tone || '',
      settings: voice.settings || {},
    });
    setShowFormModal(true);
  };

  const handleSave = async () => {
    if (!formData.name.trim() || !formData.provider_voice_id.trim()) {
      setMessage({ type: 'error', text: '名称和厂商音色ID为必填项' });
      return;
    }
    
    setSaving(true);
    try {
      if (editingVoice) {
        await api.patch(`/admin/api/voices/${editingVoice.id}`, formData);
        setMessage({ type: 'success', text: '音色已更新' });
      } else {
        await api.post('/admin/api/voices', formData);
        setMessage({ type: 'success', text: '音色已创建' });
      }
      setShowFormModal(false);
      fetchVoices();
    } catch (error) {
      setMessage({ type: 'error', text: editingVoice ? '更新失败' : '创建失败' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (voiceId: string) => {
    if (!confirm('确定要删除这个音色吗？')) return;
    
    try {
      await api.delete(`/admin/api/voices/${voiceId}`);
      setMessage({ type: 'success', text: '音色已删除' });
      fetchVoices();
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      setMessage({ type: 'error', text: err.response?.data?.detail || '删除失败' });
    }
  };

  const handleSync = async (provider: string) => {
    setSyncing(provider);
    setSyncResult(null);
    try {
      const response = await api.post(`/admin/api/voices/sync/${provider}`);
      setSyncResult(response.data);
      if (response.data?.success) {
        setMessage({ type: 'success', text: `同步完成：新增 ${response.data.synced} 个，跳过 ${response.data.skipped} 个` });
      }
      fetchVoices();
    } catch (error) {
      setMessage({ type: 'error', text: '同步失败' });
    } finally {
      setSyncing(null);
    }
  };

  const handlePreview = async (voice: Voice) => {
    if (playingId === voice.id) {
      if (audioElement) {
        audioElement.pause();
        setPlayingId(null);
      }
      return;
    }
    
    if (audioElement) {
      audioElement.pause();
    }
    
    setPreviewLoading(voice.id);
    
    try {
      let audioUrl = voice.preview_url;
      
      if (!audioUrl) {
        const response = await api.post(`/admin/api/voices/${voice.id}/preview`, {});
        audioUrl = response.data?.audio_url;
      }
      
      if (audioUrl) {
        const audio = new Audio(audioUrl);
        audio.onended = () => setPlayingId(null);
        audio.onerror = () => {
          setMessage({ type: 'error', text: '音频播放失败' });
          setPlayingId(null);
        };
        setAudioElement(audio);
        audio.play();
        setPlayingId(voice.id);
      }
    } catch (error) {
      setMessage({ type: 'error', text: '预览生成失败' });
    } finally {
      setPreviewLoading(null);
    }
  };

  const resetFilters = () => {
    setFilters({ provider: '', language: '', gender: '', tone: '' });
    setPage(1);
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
          <h2 className="text-2xl font-bold text-white">音色管理</h2>
          <p className="text-zinc-400 mt-1">管理TTS音色，支持ElevenLabs和通义千问</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchVoices} className="p-2 hover:bg-zinc-800 rounded-lg" title="刷新">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'}`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-zinc-500" />
          <select
            value={filters.provider}
            onChange={(e) => setFilters({ ...filters, provider: e.target.value })}
            className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200"
          >
            <option value="">全部厂商</option>
            <option value="elevenlabs">ElevenLabs</option>
            <option value="dashscope">通义千问</option>
          </select>
          <select
            value={filters.language}
            onChange={(e) => setFilters({ ...filters, language: e.target.value })}
            className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200"
          >
            <option value="">全部语言</option>
            <option value="en">English</option>
            <option value="zh">中文</option>
            <option value="ja">日本語</option>
            <option value="ko">한국어</option>
          </select>
          <select
            value={filters.gender}
            onChange={(e) => setFilters({ ...filters, gender: e.target.value })}
            className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200"
          >
            <option value="">全部性别</option>
            <option value="female">女声</option>
            <option value="male">男声</option>
            <option value="neutral">中性</option>
          </select>
          <select
            value={filters.tone}
            onChange={(e) => setFilters({ ...filters, tone: e.target.value })}
            className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-200"
          >
            <option value="">全部声线</option>
            {Object.entries(TONE_LABELS).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
          {(filters.provider || filters.language || filters.gender || filters.tone) && (
            <button onClick={resetFilters} className="text-sm text-pink-400 hover:text-pink-300">清除筛选</button>
          )}
        </div>
        
        <div className="flex items-center gap-2 ml-auto">
          <button
            onClick={() => handleSync('elevenlabs')}
            disabled={syncing !== null}
            className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm disabled:opacity-50"
          >
            {syncing === 'elevenlabs' ? <Loader2 className="w-4 h-4 animate-spin" /> : <CloudDownload className="w-4 h-4" />}
            ElevenLabs
          </button>
          <button
            onClick={() => handleSync('dashscope')}
            disabled={syncing !== null}
            className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm disabled:opacity-50"
          >
            {syncing === 'dashscope' ? <Loader2 className="w-4 h-4 animate-spin" /> : <CloudDownload className="w-4 h-4" />}
            通义千问
          </button>
          <button
            onClick={handleCreate}
            className="flex items-center gap-2 px-4 py-1.5 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium"
          >
            <Plus className="w-4 h-4" />新增音色
          </button>
        </div>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-zinc-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">音色名称</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">厂商</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">语言</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">性别</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">声线</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">使用次数</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">状态</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-zinc-300">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {voices.map((voice) => (
              <tr key={voice.id} className="hover:bg-zinc-800/30">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <Volume2 className="w-5 h-5 text-pink-400" />
                    <div>
                      <div className="text-white font-medium">{voice.display_name || voice.name}</div>
                      {voice.description && (
                        <div className="text-zinc-500 text-xs truncate max-w-[200px]">{voice.description}</div>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    voice.provider === 'elevenlabs' ? 'bg-blue-900/50 text-blue-300' : 'bg-orange-900/50 text-orange-300'
                  }`}>
                    {PROVIDER_LABELS[voice.provider] || voice.provider}
                  </span>
                </td>
                <td className="px-4 py-3 text-zinc-400 text-sm">{LANGUAGE_LABELS[voice.language] || voice.language}</td>
                <td className="px-4 py-3 text-zinc-400 text-sm">{voice.gender === 'female' ? '女' : voice.gender === 'male' ? '男' : '中性'}</td>
                <td className="px-4 py-3 text-zinc-400 text-sm">{voice.tone ? TONE_LABELS[voice.tone] || voice.tone : '-'}</td>
                <td className="px-4 py-3 text-zinc-400 text-sm">{voice.usage_count || 0}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs ${
                    voice.is_active ? 'bg-green-900/50 text-green-400' : 'bg-zinc-700 text-zinc-400'
                  }`}>
                    {voice.is_active ? '启用' : '禁用'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => handlePreview(voice)}
                      disabled={previewLoading === voice.id}
                      className="p-2 hover:bg-zinc-700 rounded-lg text-blue-400"
                      title="预览"
                    >
                      {previewLoading === voice.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : playingId === voice.id ? (
                        <Pause className="w-4 h-4" />
                      ) : (
                        <Play className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={() => handleEdit(voice)}
                      className="p-2 hover:bg-zinc-700 rounded-lg text-yellow-400"
                      title="编辑"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(voice.id)}
                      className="p-2 hover:bg-zinc-700 rounded-lg text-red-400"
                      title="删除"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {voices.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-zinc-500">
                  暂无音色数据，点击"新增音色"或从厂商同步
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {total > 50 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 bg-zinc-800 rounded disabled:opacity-50"
          >
            上一页
          </button>
          <span className="text-zinc-400 text-sm">第 {page} 页，共 {Math.ceil(total / 50)} 页</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={page * 50 >= total}
            className="px-3 py-1 bg-zinc-800 rounded disabled:opacity-50"
          >
            下一页
          </button>
        </div>
      )}

      {showFormModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">{editingVoice ? '编辑音色' : '新增音色'}</h3>
              <button onClick={() => setShowFormModal(false)} className="p-1 hover:bg-zinc-700 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">名称 *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                    placeholder="例如：Rachel"
                  />
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">显示名称</label>
                  <input
                    type="text"
                    value={formData.display_name}
                    onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                    placeholder="例如：Rachel (ElevenLabs)"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm text-zinc-400 mb-1">描述</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none resize-none"
                  rows={2}
                  placeholder="音色描述..."
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">厂商 *</label>
                  <select
                    value={formData.provider}
                    onChange={(e) => setFormData({ ...formData, provider: e.target.value, language: e.target.value === 'dashscope' ? 'zh' : 'en' })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                  >
                    <option value="elevenlabs">ElevenLabs</option>
                    <option value="dashscope">通义千问</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">厂商音色ID *</label>
                  <input
                    type="text"
                    value={formData.provider_voice_id}
                    onChange={(e) => setFormData({ ...formData, provider_voice_id: e.target.value })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                    placeholder="例如：21m00Tcm4TlvDq8ikWAM"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">模型ID</label>
                  <input
                    type="text"
                    value={formData.model_id}
                    onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                    placeholder="可选"
                  />
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">语言</label>
                  <select
                    value={formData.language}
                    onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                  >
                    <option value="en">English</option>
                    <option value="zh">中文</option>
                    <option value="ja">日本語</option>
                    <option value="ko">한국어</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">性别</label>
                  <select
                    value={formData.gender}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                  >
                    <option value="female">女声</option>
                    <option value="male">男声</option>
                    <option value="neutral">中性</option>
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm text-zinc-400 mb-1">声线</label>
                <select
                  value={formData.tone}
                  onChange={(e) => setFormData({ ...formData, tone: e.target.value })}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                >
                  <option value="">无</option>
                  {Object.entries(TONE_LABELS).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowFormModal(false)}
                className="flex-1 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !formData.name.trim() || !formData.provider_voice_id.trim()}
                className="flex-1 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {saving ? '保存中...' : (editingVoice ? '更新' : '创建')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}