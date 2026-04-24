import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Loader2, Save, Wand2, Image as ImageIcon, RefreshCw,
  Check, AlertTriangle, Trash2
} from 'lucide-react';
import { api } from '@/services/api';
import { useAdminAuth } from '@/hooks/useAdminAuth';

interface VoiceOption {
  id: string;
  name: string;
  display_name?: string;
  provider: string;
  provider_voice_id: string;
  language: string;
  gender: string;
}

interface Character {
  id: string;
  name: string;
  first_name?: string;
  slug: string;
  description?: string;
  age?: number;
  gender?: string;
  top_category?: string;
  personality_tags?: string[];
  personality_summary?: string;
  backstory?: string;
  greeting?: string;
  system_prompt?: string;
  avatar_url?: string;
  cover_url?: string;
  mature_image_url?: string;
  mature_cover_url?: string;
  mature_video_url?: string;
  voice_id?: string;
  meta_title?: string;
  meta_description?: string;
  is_public?: boolean;
  lifecycle_status?: string;
  popularity_score?: number;
  chat_count?: number;
  view_count?: number;
  created_at?: string;
}

interface StoryOption {
  id: string;
  title: string;
  status: string;
  age_rating?: string;
}

interface StoryBinding {
  script_id: string;
  weight: number;
  is_active: boolean;
  title?: string;
}

const PERSONALITY_OPTIONS = [
  'gentle', 'caring', 'playful', 'mysterious', 'confident', 'shy',
  'adventurous', 'intellectual', 'romantic', 'flirty', 'dominant',
  'submissive', 'funny', 'serious', 'creative', 'sweet'
];

const CATEGORY_OPTIONS = [
  { value: 'girls', label: 'Girls' },
  { value: 'anime', label: 'Anime' },
  { value: 'guys', label: 'Guys' },
];

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'draft', label: 'Draft' },
  { value: 'archived', label: 'Archived' },
];

export default function CharacterEditPage() {
  const { characterId } = useParams<{ characterId: string }>();
  const navigate = useNavigate();
  const { isAdmin, loading: authLoading } = useAdminAuth();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [storyOptions, setStoryOptions] = useState<StoryOption[]>([]);
  const [bindings, setBindings] = useState<StoryBinding[]>([]);
  const [bindingsLoading, setBindingsLoading] = useState(false);
  const [bindingsSaving, setBindingsSaving] = useState(false);
  const [bindingsAutoMatching, setBindingsAutoMatching] = useState(false);
  const [newBindingScriptId, setNewBindingScriptId] = useState('');

  const [character, setCharacter] = useState<Character | null>(null);
  const [formData, setFormData] = useState<Character>({
    id: '',
    name: '',
    slug: '',
    age: 25,
    gender: 'female',
    top_category: 'girls',
    personality_tags: [],
    is_public: true,
    lifecycle_status: 'active',
  });

  useEffect(() => {
    if (characterId) {
      fetchCharacter();
      fetchStoryBindings(characterId);
    }
    fetchVoices();
    fetchStoryOptions();
  }, [characterId]);

  const fetchVoices = async () => {
    try {
      const response = await api.get('/admin/api/voices?page_size=200');
      setVoices(response.data?.voices || []);
    } catch {
      // non-critical, fall back to manual input
    }
  };

  const fetchCharacter = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/admin/characters/${characterId}`);
      const data = response.data || response;
      setCharacter(data);
      setFormData({
        ...data,
        personality_tags: data.personality_tags || [],
      });
    } catch (error) {
      setMessage({ type: 'error', text: '加载角色失败' });
    } finally {
      setLoading(false);
    }
  };

  const fetchStoryOptions = async () => {
    try {
      const response = await api.get('/admin/api/stories/options', {
        params: { status: 'published', page_size: 500 },
      });
      setStoryOptions(response.data?.items || []);
    } catch {
      setStoryOptions([]);
    }
  };

  const fetchStoryBindings = async (id: string) => {
    setBindingsLoading(true);
    try {
      const response = await api.get(`/admin/api/characters/${id}/story-bindings`);
      const items = (response.data?.items || []) as StoryBinding[];
      setBindings(items.map((item) => ({
        script_id: item.script_id,
        weight: Number(item.weight || 1),
        is_active: item.is_active !== false,
        title: item.title,
      })));
    } catch {
      setBindings([]);
    } finally {
      setBindingsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
      </div>
    );
  }

  if (!isAdmin) {
    return null;
  }
  
  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    
    try {
      await api.put(`/admin/api/characters/${characterId}`, formData);
      
      setMessage({ type: 'success', text: '保存成功' });
      fetchCharacter();
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || '保存失败',
      });
    } finally {
      setSaving(false);
    }
  };
  
  const handleRegenerateImages = async () => {
    setRegenerating(true);
    setMessage(null);

    try {
      await api.post(`/admin/api/characters/${characterId}/regenerate-images`);
      setMessage({ type: 'success', text: '图片重新生成成功' });
      fetchCharacter();
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || '图片生成失败',
      });
    } finally {
      setRegenerating(false);
    }
  };

  const handleRegenerateMatureImage = async () => {
    setRegenerating(true);
    setMessage(null);

    try {
      await api.post(
        `/admin/api/characters/${characterId}/regenerate-mature`,
        null,
        { params: { generate_video: false } }
      );
      setMessage({ type: 'success', text: 'Mature image regenerated successfully' });
      fetchCharacter();
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Mature image generation failed',
      });
    } finally {
      setRegenerating(false);
    }
  };

  const handleRegenerateMatureVideo = async () => {
    setRegenerating(true);
    setMessage(null);

    try {
      await api.post(`/admin/api/characters/${characterId}/regenerate-video`);
      setMessage({ type: 'success', text: 'Mature video regenerated successfully' });
      fetchCharacter();
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Mature video generation failed',
      });
    } finally {
      setRegenerating(false);
    }
  };  
  const handleAIFill = async () => {
    setSaving(true);
    setMessage(null);
    
    try {
      await api.post(`/admin/characters/${characterId}/ai-fill`);
      setMessage({ type: 'success', text: 'AI填充成功' });
      fetchCharacter();
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'AI填充失败',
      });
    } finally {
      setSaving(false);
    }
  };
  
  const togglePersonality = (trait: string) => {
    const current = formData.personality_tags || [];
    if (current.includes(trait)) {
      setFormData({
        ...formData,
        personality_tags: current.filter(t => t !== trait),
      });
    } else {
      setFormData({
        ...formData,
        personality_tags: [...current, trait],
      });
    }
  };

  const addBinding = () => {
    if (!newBindingScriptId) return;
    if (bindings.some((b) => b.script_id === newBindingScriptId)) return;
    const selected = storyOptions.find((item) => item.id === newBindingScriptId);
    setBindings((prev) => [
      ...prev,
      {
        script_id: newBindingScriptId,
        weight: 1,
        is_active: true,
        title: selected?.title || newBindingScriptId,
      },
    ]);
    setNewBindingScriptId('');
  };

  const removeBinding = (scriptId: string) => {
    setBindings((prev) => prev.filter((item) => item.script_id !== scriptId));
  };

  const updateBinding = (scriptId: string, patch: Partial<StoryBinding>) => {
    setBindings((prev) =>
      prev.map((item) => (item.script_id === scriptId ? { ...item, ...patch } : item))
    );
  };

  const saveBindings = async () => {
    if (!characterId) return;
    setBindingsSaving(true);
    setMessage(null);
    try {
      await api.put(`/admin/api/characters/${characterId}/story-bindings`, {
        items: bindings.map((item) => ({
          script_id: item.script_id,
          weight: Number(item.weight || 1),
          is_active: !!item.is_active,
        })),
      });
      setMessage({ type: 'success', text: 'Story bindings saved successfully' });
      await fetchStoryBindings(characterId);
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || '剧本绑定保存失败',
      });
    } finally {
      setBindingsSaving(false);
    }
  };

  const autoMatchBindings = async () => {
    if (!characterId) return;
    setBindingsAutoMatching(true);
    setMessage(null);
    try {
      const response = await api.post(`/admin/api/characters/${characterId}/story-bindings/auto-match`, {
        count: 5,
        apply: true,
        append: true,
      });
      const count = Number(response.data?.count || 0);
      setMessage({ type: 'success', text: `Auto-configured and added ${count} scripts` });
      await fetchStoryBindings(characterId);
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Auto-config failed',
      });
    } finally {
      setBindingsAutoMatching(false);
    }
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
      </div>
    );
  }
  
  if (!character) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-zinc-400">Character not found</div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="p-2 hover:bg-zinc-800 rounded-lg"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-2xl font-bold">编辑角色</h1>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={handleAIFill}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm disabled:opacity-50"
            >
              <Wand2 className="w-4 h-4" />
              AI填充
            </button>
            <button
              onClick={handleRegenerateImages}
              disabled={regenerating}
              className="flex items-center gap-2 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm disabled:opacity-50"
            >
              {regenerating ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              重新生成图片
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium disabled:opacity-50"
            >
              {saving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              保存
            </button>
          </div>
        </div>
        
        {message && (
          <div className={`mb-6 p-4 rounded-lg flex items-center gap-2 ${
            message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'
          }`}>
            {message.type === 'success' ? <Check className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
            {message.text}
          </div>
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4">基本信息</h2>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">角色名称</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Display Name</label>
                  <input
                    type="text"
                    value={formData.first_name || ''}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">年龄</label>
                  <input
                    type="number"
                    value={formData.age || 25}
                    onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) || 25 })}
                    min={18}
                    max={99}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">分类</label>
                  <select
                    value={formData.top_category || 'girls'}
                    onChange={(e) => setFormData({ ...formData, top_category: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                  >
                    {CATEGORY_OPTIONS.map((cat) => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="mt-4">
                <label className="block text-sm text-zinc-400 mb-2">Slug (URL)</label>
                <input
                  type="text"
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                />
              </div>
            </div>
            
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4">角色描述</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Description</label>
                  <textarea
                    value={formData.description || ''}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={2}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg resize-none"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Personality Summary</label>
                  <input
                    type="text"
                    value={formData.personality_summary || ''}
                    onChange={(e) => setFormData({ ...formData, personality_summary: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                    placeholder="Short personality summary for card display"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">鎬ф牸鏍囩</label>
                  <div className="flex flex-wrap gap-2">
                    {PERSONALITY_OPTIONS.map((trait) => (
                      <button
                        key={trait}
                        onClick={() => togglePersonality(trait)}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                          (formData.personality_tags || []).includes(trait)
                            ? 'bg-pink-600 text-white'
                            : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                        }`}
                      >
                        {trait}
                      </button>
                    ))}
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">背景故事</label>
                  <textarea
                    value={formData.backstory || ''}
                    onChange={(e) => setFormData({ ...formData, backstory: e.target.value })}
                    rows={3}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg resize-none"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">寮€场白</label>
                  <textarea
                    value={formData.greeting || ''}
                    onChange={(e) => setFormData({ ...formData, greeting: e.target.value })}
                    rows={2}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg resize-none"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">System Prompt</label>
                  <textarea
                    value={formData.system_prompt || ''}
                    onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                    rows={4}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg resize-none font-mono text-sm"
                  />
                </div>
              </div>
            </div>
            
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4">SEO设置</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">SEO鏍囬</label>
                  <input
                    type="text"
                    value={formData.meta_title || ''}
                    onChange={(e) => setFormData({ ...formData, meta_title: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                    placeholder="SEO鏍囬"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">SEO描述</label>
                  <textarea
                    value={formData.meta_description || ''}
                    onChange={(e) => setFormData({ ...formData, meta_description: e.target.value })}
                    rows={2}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg resize-none"
                    placeholder="SEO描述"
                  />
                </div>
              </div>
            </div>
          </div>
          
          <div className="space-y-6">
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4">SFW 图片资源</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">头像 (SFW)</label>
                  {formData.avatar_url ? (
                    <img
                      src={formData.avatar_url}
                      alt="Avatar"
                      className="w-32 h-32 rounded-lg object-cover"
                    />
                  ) : (
                    <div className="w-32 h-32 bg-zinc-800 rounded-lg flex items-center justify-center">
                      <ImageIcon className="w-8 h-8 text-zinc-600" />
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm text-zinc-400 mb-2">封面 (SFW)</label>
                  {formData.cover_url ? (
                    <img
                      src={formData.cover_url}
                      alt="Cover"
                      className="w-full h-48 rounded-lg object-cover"
                    />
                  ) : (
                    <div className="w-full h-48 bg-zinc-800 rounded-lg flex items-center justify-center">
                      <ImageIcon className="w-8 h-8 text-zinc-600" />
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-zinc-900 border border-red-900/40 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-red-400">Mature 鍐呭</h2>
                <div className="flex gap-2">
                  <button
                    onClick={handleRegenerateMatureImage}
                    disabled={regenerating}
                    className="px-3 py-1.5 bg-red-900/50 hover:bg-red-800/50 border border-red-700/50 rounded-lg text-xs text-red-300 flex items-center gap-1 disabled:opacity-50"
                  >
                    {regenerating ? <RefreshCw className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                    閲嶇敓鎴愬浘鐗?                  </button>
                  <button
                    onClick={handleRegenerateMatureVideo}
                    disabled={regenerating}
                    className="px-3 py-1.5 bg-red-900/50 hover:bg-red-800/50 border border-red-700/50 rounded-lg text-xs text-red-300 flex items-center gap-1 disabled:opacity-50"
                  >
                    {regenerating ? <RefreshCw className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                    閲嶇敓鎴愯棰?                  </button>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-zinc-500 mb-2">Mature 头像</label>
                    {character?.mature_image_url ? (
                      <img
                        src={character.mature_image_url}
                        alt="Mature Avatar"
                        className="w-full aspect-square rounded-lg object-cover"
                      />
                    ) : (
                      <div className="w-full aspect-square bg-zinc-800 rounded-lg flex items-center justify-center">
                        <span className="text-xs text-zinc-600">Not generated</span>
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="block text-xs text-zinc-500 mb-2">Mature 封面</label>
                    {character?.mature_cover_url ? (
                      <img
                        src={character.mature_cover_url}
                        alt="Mature Cover"
                        className="w-full aspect-square rounded-lg object-cover"
                      />
                    ) : (
                      <div className="w-full aspect-square bg-zinc-800 rounded-lg flex items-center justify-center">
                        <span className="text-xs text-zinc-600">Not generated</span>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-xs text-zinc-500 mb-2">Mature 视频</label>
                  {character?.mature_video_url ? (
                    <video
                      src={character.mature_video_url}
                      className="w-full rounded-lg"
                      controls
                      muted
                      loop
                    />
                  ) : (
                    <div className="w-full h-24 bg-zinc-800 rounded-lg flex items-center justify-center">
                      <span className="text-xs text-zinc-600">Not generated</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4">Status Settings</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">Lifecycle Status</label>
                  <select
                    value={formData.lifecycle_status || 'active'}
                    onChange={(e) => setFormData({ ...formData, lifecycle_status: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                  >
                    {STATUS_OPTIONS.map((status) => (
                      <option key={status.value} value={status.value}>{status.label}</option>
                    ))}
                  </select>
                </div>
                
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_public ?? true}
                    onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                    className="rounded border-zinc-600"
                  />
                  <span className="text-sm text-zinc-300">鍏紑鍙</span>
                </label>
              </div>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">剧本绑定（多选）</h2>
                <div className="flex items-center gap-2">
                  <button
                    onClick={autoMatchBindings}
                    disabled={bindingsAutoMatching || bindingsLoading}
                    className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 rounded text-xs font-medium disabled:opacity-50"
                  >
                    {bindingsAutoMatching ? '自动匹配中...' : '自动匹配 +5'}
                  </button>
                  <button
                    onClick={saveBindings}
                    disabled={bindingsSaving || bindingsLoading}
                    className="px-3 py-1.5 bg-pink-600 hover:bg-pink-500 rounded text-xs font-medium disabled:opacity-50"
                  >
                    {bindingsSaving ? '保存中...' : '保存绑定'}
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex gap-2">
                  <select
                    value={newBindingScriptId}
                    onChange={(e) => setNewBindingScriptId(e.target.value)}
                    className="flex-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm"
                  >
                    <option value="">选择一个已发布剧本</option>
                    {storyOptions.map((story) => (
                      <option key={story.id} value={story.id}>
                        {story.title} ({story.id})
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={addBinding}
                    disabled={!newBindingScriptId}
                    className="px-3 py-2 bg-zinc-700 hover:bg-zinc-600 rounded text-sm disabled:opacity-50"
                  >
                    添加
                  </button>
                </div>

                {bindingsLoading ? (
                  <div className="text-sm text-zinc-400">加载中...</div>
                ) : bindings.length === 0 ? (
                  <div className="text-sm text-zinc-500">暂无绑定剧本，聊天时不会触发随机剧本。</div>
                ) : (
                  <div className="space-y-2">
                    {bindings.map((binding) => (
                      <div key={binding.script_id} className="p-3 bg-zinc-800/60 rounded-lg space-y-2">
                        <div className="text-sm text-zinc-200 break-all">{binding.title || binding.script_id}</div>
                        <div className="text-xs text-zinc-500 break-all">{binding.script_id}</div>
                        <div className="flex items-center gap-3">
                          <label className="text-xs text-zinc-400">权重</label>
                          <input
                            type="number"
                            min={1}
                            max={1000}
                            value={binding.weight}
                            onChange={(e) =>
                              updateBinding(binding.script_id, {
                                weight: Number.parseInt(e.target.value || '1', 10) || 1,
                              })
                            }
                            className="w-24 px-2 py-1 bg-zinc-900 border border-zinc-700 rounded text-sm"
                          />
                          <label className="flex items-center gap-1 text-xs text-zinc-300">
                            <input
                              type="checkbox"
                              checked={binding.is_active}
                              onChange={(e) =>
                                updateBinding(binding.script_id, { is_active: e.target.checked })
                              }
                            />
                            启用
                          </label>
                          <button
                            onClick={() => removeBinding(binding.script_id)}
                            className="ml-auto p-1.5 text-red-400 hover:bg-zinc-700 rounded"
                            title="移除绑定"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4">语音设置</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">选择语音</label>
                  {voices.length > 0 ? (
                    <select
                      value={formData.voice_id || ''}
                      onChange={(e) => setFormData({ ...formData, voice_id: e.target.value })}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200"
                    >
                      <option value="">-- 不使用语音 --</option>
                      {voices.map((v) => (
                        <option key={v.id} value={v.provider_voice_id}>
                          {v.display_name || v.name}
                          {' '}({v.provider === 'elevenlabs' ? 'EL' : v.provider} / {v.gender === 'female' ? 'Female' : v.gender === 'male' ? 'Male' : 'Neutral'} / {v.provider_voice_id})
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      value={formData.voice_id || ''}
                      onChange={(e) => setFormData({ ...formData, voice_id: e.target.value })}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                      placeholder="e.g., 21m00Tcm4TlvDq8ikWAM"
                    />
                  )}
                  {formData.voice_id && (
                    <p className="text-xs text-zinc-500 mt-1">Voice ID: {formData.voice_id}</p>
                  )}
                </div>
              </div>
            </div>
            
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4">统计信息</h2>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-zinc-400">人气分数</span>
                  <span>{character.popularity_score || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">对话次数</span>
                  <span>{character.chat_count || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">浏览次数</span>
                  <span>{character.view_count || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">创建时间</span>
                  <span>{character.created_at ? new Date(character.created_at).toLocaleDateString() : '-'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

