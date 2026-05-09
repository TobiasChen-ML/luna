import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Loader2, Save, Wand2, Image as ImageIcon, RefreshCw,
  Check, AlertTriangle, Trash2, Play, Pause, Upload, Film
} from 'lucide-react';
import { api } from '@/services/api';
import { useAdminAuth } from '@/hooks/useAdminAuth';

interface VoiceOption {
  id: string;
  name: string;
  display_name?: string;
  preview_url?: string;
  provider: string;
  provider_voice_id: string;
  language: string;
  gender: string;
}

const PREVIEW_TEXT = 'hey, handsome boy.';

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
  profile_image_url?: string;
  preview_video_url?: string;
  mature_image_url?: string;
  mature_cover_url?: string;
  mature_video_url?: string;
  voice_id?: string;
  meta_title?: string;
  meta_description?: string;
  is_official?: boolean;
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

type CharacterImageField =
  | 'avatar_url'
  | 'cover_url'
  | 'profile_image_url'
  | 'mature_image_url'
  | 'mature_cover_url';
type CharacterVideoField = 'preview_video_url' | 'mature_video_url';
type CharacterMediaField = CharacterImageField | CharacterVideoField;
type MediaGenerationMode = 'img2img' | 'img2video';

const CHARACTER_IMAGE_FIELDS: CharacterImageField[] = [
  'avatar_url',
  'cover_url',
  'profile_image_url',
  'mature_image_url',
  'mature_cover_url',
];

const CHARACTER_VIDEO_FIELDS: CharacterVideoField[] = [
  'preview_video_url',
  'mature_video_url',
];

const CHARACTER_MEDIA_FIELD_LABELS: Record<CharacterMediaField, string> = {
  avatar_url: '头像',
  cover_url: '封面',
  profile_image_url: '主页主图',
  mature_image_url: '图片 1',
  mature_cover_url: '图片 2 / 封面',
  preview_video_url: 'Discover 视频',
  mature_video_url: '主页视频',
};

const getApiErrorMessage = (error: unknown, fallback: string) => {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === 'string' ? detail : fallback;
};

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
  const [previewLoading, setPreviewLoading] = useState(false);
  const [playingVoiceDbId, setPlayingVoiceDbId] = useState<string | null>(null);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);
  const [uploadingField, setUploadingField] = useState<CharacterMediaField | null>(null);
  const [mediaGenerating, setMediaGenerating] = useState<MediaGenerationMode | null>(null);
  const [img2imgTargetField, setImg2imgTargetField] = useState<CharacterImageField>('mature_image_url');
  const [img2imgSourceField, setImg2imgSourceField] = useState<CharacterImageField>('avatar_url');
  const [img2imgPrompt, setImg2imgPrompt] = useState('');
  const [img2videoTargetField, setImg2videoTargetField] = useState<CharacterVideoField>('mature_video_url');
  const [img2videoSourceField, setImg2videoSourceField] = useState<CharacterImageField>('mature_image_url');
  const [img2videoPrompt, setImg2videoPrompt] = useState('');

  const [character, setCharacter] = useState<Character | null>(null);
  const [formData, setFormData] = useState<Character>({
    id: '',
    name: '',
    slug: '',
    age: 25,
    gender: 'female',
    top_category: 'girls',
    personality_tags: [],
    is_official: true,
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

  useEffect(() => {
    return () => {
      if (audioElement) {
        audioElement.pause();
        audioElement.src = '';
      }
    };
  }, [audioElement]);

  const fetchVoices = async () => {
    try {
      const response = await api.get('/admin/api/voices?page_size=200');
      setVoices(response.data?.voices || []);
    } catch {
      // non-critical, fall back to manual input
    }
  };

  const getSelectedVoice = () =>
    voices.find((voice) => voice.provider_voice_id === (formData.voice_id || '')) || null;

  const handlePreviewVoice = async () => {
    const selectedVoice = getSelectedVoice();
    if (!selectedVoice) return;

    if (playingVoiceDbId === selectedVoice.id) {
      if (audioElement) {
        audioElement.pause();
      }
      setPlayingVoiceDbId(null);
      return;
    }

    if (audioElement) {
      audioElement.pause();
    }

    setPreviewLoading(true);
    try {
      let audioUrl = selectedVoice.preview_url;
      if (!audioUrl) {
        const response = await api.post(`/admin/api/voices/${selectedVoice.id}/preview`, {
          text: PREVIEW_TEXT,
        });
        audioUrl = response.data?.audio_url;
        if (audioUrl) {
          setVoices((prev) =>
            prev.map((voice) =>
              voice.id === selectedVoice.id ? { ...voice, preview_url: audioUrl } : voice
            )
          );
        }
      }
      if (!audioUrl) return;

      const audio = new Audio(audioUrl);
      audio.onended = () => setPlayingVoiceDbId(null);
      audio.onerror = () => setPlayingVoiceDbId(null);
      setAudioElement(audio);
      await audio.play();
      setPlayingVoiceDbId(selectedVoice.id);
    } finally {
      setPreviewLoading(false);
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

  const applyMediaResult = (field: CharacterMediaField, url?: string, updatedCharacter?: Character) => {
    if (updatedCharacter) {
      setCharacter(updatedCharacter);
    } else if (url) {
      setCharacter((prev) => (prev ? { ...prev, [field]: url } : prev));
    }
    if (url) {
      setFormData((prev) => ({ ...prev, [field]: url }));
    }
  };

  const handleMediaUpload = async (field: CharacterMediaField, file: File) => {
    if (!characterId) return;
    setUploadingField(field);
    setMessage(null);

    const body = new FormData();
    body.append('field', field);
    body.append('file', file);

    try {
      const response = await api.post(`/admin/api/characters/${characterId}/media/upload`, body);
      applyMediaResult(field, response.data?.url, response.data?.character);
      setMessage({ type: 'success', text: `${CHARACTER_MEDIA_FIELD_LABELS[field]} 已上传` });
    } catch (error: unknown) {
      setMessage({
        type: 'error',
        text: getApiErrorMessage(error, '上传失败'),
      });
    } finally {
      setUploadingField(null);
    }
  };

  const handleGenerateImageMedia = async () => {
    if (!characterId) return;
    setMediaGenerating('img2img');
    setMessage(null);

    try {
      const response = await api.post(`/admin/api/characters/${characterId}/media/generate-image`, {
        target_field: img2imgTargetField,
        source_field: img2imgSourceField,
        prompt: img2imgPrompt.trim() || undefined,
      });
      applyMediaResult(img2imgTargetField, response.data?.url, response.data?.character);
      setMessage({ type: 'success', text: `img2img 已生成到 ${CHARACTER_MEDIA_FIELD_LABELS[img2imgTargetField]}` });
    } catch (error: unknown) {
      setMessage({
        type: 'error',
        text: getApiErrorMessage(error, 'img2img 生成失败'),
      });
    } finally {
      setMediaGenerating(null);
    }
  };

  const handleGenerateVideoMedia = async () => {
    if (!characterId) return;
    setMediaGenerating('img2video');
    setMessage(null);

    try {
      const response = await api.post(`/admin/api/characters/${characterId}/media/generate-video`, {
        target_field: img2videoTargetField,
        source_field: img2videoSourceField,
        prompt: img2videoPrompt.trim() || undefined,
      });
      applyMediaResult(img2videoTargetField, response.data?.url, response.data?.character);
      setMessage({ type: 'success', text: `img2video 已生成到 ${CHARACTER_MEDIA_FIELD_LABELS[img2videoTargetField]}` });
    } catch (error: unknown) {
      setMessage({
        type: 'error',
        text: getApiErrorMessage(error, 'img2video 生成失败'),
      });
    } finally {
      setMediaGenerating(null);
    }
  };

  const renderMediaUpload = (field: CharacterMediaField, accept: string) => {
    const disabled = Boolean(uploadingField || mediaGenerating);
    return (
      <label
        className={`inline-flex items-center gap-1.5 rounded-lg border border-zinc-700 px-2.5 py-1.5 text-xs text-zinc-300 ${
          disabled ? 'opacity-50 pointer-events-none' : 'cursor-pointer hover:bg-zinc-800'
        }`}
      >
        {uploadingField === field ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <Upload className="h-3.5 w-3.5" />
        )}
        上传
        <input
          type="file"
          accept={accept}
          disabled={disabled}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            e.currentTarget.value = '';
            if (file) {
              void handleMediaUpload(field, file);
            }
          }}
        />
      </label>
    );
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

  const isDiscoverVisible = Boolean(
    formData.is_official &&
    (formData.is_public ?? true) &&
    (formData.lifecycle_status || 'active') === 'active'
  );
  const discoverMediaCount = [
    formData.profile_image_url,
    formData.preview_video_url,
    formData.mature_image_url,
    formData.mature_cover_url,
    formData.mature_video_url,
  ].filter(Boolean).length;

  const handlePublishToDiscover = () => {
    setFormData({
      ...formData,
      is_official: true,
      is_public: true,
      lifecycle_status: 'active',
    });
  };
  
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
                  <label className="block text-sm text-zinc-400 mb-2">性格标签</label>
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
                  <label className="block text-sm text-zinc-400 mb-2">开场白</label>
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
                  <label className="block text-sm text-zinc-400 mb-2">SEO 标题</label>
                  <input
                    type="text"
                    value={formData.meta_title || ''}
                    onChange={(e) => setFormData({ ...formData, meta_title: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                    placeholder="SEO 标题"
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
              <div className="bg-zinc-900 border border-pink-900/40 rounded-xl p-6">
                <div className="flex items-start justify-between gap-4 mb-5">
                  <div>
                    <h2 className="text-lg font-semibold text-pink-200">主页 / Discover 内容</h2>
                    <p className="text-xs text-zinc-500 mt-1">
                      {discoverMediaCount} 个素材 · {isDiscoverVisible ? 'Discover 可见' : '未进入 Discover'}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    isDiscoverVisible
                      ? 'bg-green-900/50 text-green-300'
                      : 'bg-zinc-800 text-zinc-400'
                  }`}>
                    {isDiscoverVisible ? 'Live' : 'Hidden'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-4">
                  <label className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_official ?? true}
                      onChange={(e) => setFormData({ ...formData, is_official: e.target.checked })}
                      className="rounded border-zinc-600"
                    />
                    <span className="text-sm text-zinc-300">加入 Discover</span>
                  </label>
                  <label className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_public ?? true}
                      onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                      className="rounded border-zinc-600"
                    />
                    <span className="text-sm text-zinc-300">公开展示</span>
                  </label>
                </div>

                <button
                  type="button"
                  onClick={handlePublishToDiscover}
                  className="mb-5 w-full rounded-lg bg-pink-600 px-4 py-2 text-sm font-medium text-white hover:bg-pink-500"
                >
                  设为 Discover 可见
                </button>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">主页短文案</label>
                    <input
                      type="text"
                      value={formData.personality_summary || ''}
                      onChange={(e) => setFormData({ ...formData, personality_summary: e.target.value })}
                      maxLength={500}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                      placeholder="Shown under the profile name"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">主页详情文案</label>
                    <textarea
                      value={formData.description || ''}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={3}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg resize-none"
                      placeholder="Shown on the profile and Discover cards"
                    />
                  </div>

                  <div>
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <label className="text-sm text-zinc-400">主页主图 URL</label>
                      {renderMediaUpload('profile_image_url', 'image/*')}
                    </div>
                    <input
                      type="url"
                      value={formData.profile_image_url || ''}
                      onChange={(e) => setFormData({ ...formData, profile_image_url: e.target.value })}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                      placeholder="https://..."
                    />
                    {formData.profile_image_url && (
                      <img
                        src={formData.profile_image_url}
                        alt="Profile preview"
                        className="mt-3 h-32 w-full rounded-lg object-cover"
                      />
                    )}
                  </div>

                  <div>
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <label className="text-sm text-zinc-400">Discover 视频 URL</label>
                      {renderMediaUpload('preview_video_url', 'video/*')}
                    </div>
                    <input
                      type="url"
                      value={formData.preview_video_url || ''}
                      onChange={(e) => setFormData({ ...formData, preview_video_url: e.target.value })}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                      placeholder="https://..."
                    />
                    {formData.preview_video_url && (
                      <video
                        src={formData.preview_video_url}
                        className="mt-3 h-40 w-full rounded-lg object-cover"
                        controls
                        muted
                        loop
                      />
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <label className="text-xs text-zinc-500">图片 1</label>
                        {renderMediaUpload('mature_image_url', 'image/*')}
                      </div>
                      <input
                        type="url"
                        value={formData.mature_image_url || ''}
                        onChange={(e) => setFormData({ ...formData, mature_image_url: e.target.value })}
                        className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm"
                        placeholder="Image URL"
                      />
                      {formData.mature_image_url && (
                        <img
                          src={formData.mature_image_url}
                          alt="Image 1 preview"
                          className="mt-2 aspect-square w-full rounded-lg object-cover"
                        />
                      )}
                    </div>
                    <div>
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <label className="text-xs text-zinc-500">图片 2 / 封面</label>
                        {renderMediaUpload('mature_cover_url', 'image/*')}
                      </div>
                      <input
                        type="url"
                        value={formData.mature_cover_url || ''}
                        onChange={(e) => setFormData({ ...formData, mature_cover_url: e.target.value })}
                        className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm"
                        placeholder="Image URL"
                      />
                      {formData.mature_cover_url && (
                        <img
                          src={formData.mature_cover_url}
                          alt="Image 2 preview"
                          className="mt-2 aspect-square w-full rounded-lg object-cover"
                        />
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <label className="text-sm text-zinc-400">主页视频 URL</label>
                      {renderMediaUpload('mature_video_url', 'video/*')}
                    </div>
                    <input
                      type="url"
                      value={formData.mature_video_url || ''}
                      onChange={(e) => setFormData({ ...formData, mature_video_url: e.target.value })}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                      placeholder="https://..."
                    />
                    {formData.mature_video_url && (
                      <video
                        src={formData.mature_video_url}
                        className="mt-3 h-40 w-full rounded-lg object-cover"
                        controls
                        muted
                        loop
                      />
                    )}
                  </div>

                  <div className="border-t border-zinc-800 pt-4">
                    <div className="mb-3 flex items-center gap-2 text-sm font-medium text-zinc-200">
                      <Wand2 className="h-4 w-4 text-pink-400" />
                      复用 img2img / img2video
                    </div>

                    <div className="space-y-5">
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-xs text-zinc-500 mb-1.5">来源图片</label>
                            <select
                              value={img2imgSourceField}
                              onChange={(e) => setImg2imgSourceField(e.target.value as CharacterImageField)}
                              className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm"
                            >
                              {CHARACTER_IMAGE_FIELDS.map((field) => (
                                <option key={field} value={field}>
                                  {CHARACTER_MEDIA_FIELD_LABELS[field]}{formData[field] ? '' : '（空）'}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="block text-xs text-zinc-500 mb-1.5">写入图片</label>
                            <select
                              value={img2imgTargetField}
                              onChange={(e) => setImg2imgTargetField(e.target.value as CharacterImageField)}
                              className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm"
                            >
                              {CHARACTER_IMAGE_FIELDS.map((field) => (
                                <option key={field} value={field}>
                                  {CHARACTER_MEDIA_FIELD_LABELS[field]}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>
                        <textarea
                          value={img2imgPrompt}
                          onChange={(e) => setImg2imgPrompt(e.target.value)}
                          rows={2}
                          className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm resize-none"
                          placeholder="img2img prompt，不填则使用角色默认文案"
                        />
                        <button
                          type="button"
                          onClick={handleGenerateImageMedia}
                          disabled={Boolean(mediaGenerating || uploadingField)}
                          className="inline-flex items-center gap-2 rounded-lg bg-pink-600 px-3 py-2 text-sm font-medium text-white hover:bg-pink-500 disabled:opacity-50"
                        >
                          {mediaGenerating === 'img2img' ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Wand2 className="h-4 w-4" />
                          )}
                          生成图片
                        </button>
                      </div>

                      <div className="space-y-3 border-t border-zinc-800 pt-4">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-xs text-zinc-500 mb-1.5">来源图片</label>
                            <select
                              value={img2videoSourceField}
                              onChange={(e) => setImg2videoSourceField(e.target.value as CharacterImageField)}
                              className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm"
                            >
                              {CHARACTER_IMAGE_FIELDS.map((field) => (
                                <option key={field} value={field}>
                                  {CHARACTER_MEDIA_FIELD_LABELS[field]}{formData[field] ? '' : '（空）'}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="block text-xs text-zinc-500 mb-1.5">写入视频</label>
                            <select
                              value={img2videoTargetField}
                              onChange={(e) => setImg2videoTargetField(e.target.value as CharacterVideoField)}
                              className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm"
                            >
                              {CHARACTER_VIDEO_FIELDS.map((field) => (
                                <option key={field} value={field}>
                                  {CHARACTER_MEDIA_FIELD_LABELS[field]}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>
                        <textarea
                          value={img2videoPrompt}
                          onChange={(e) => setImg2videoPrompt(e.target.value)}
                          rows={2}
                          className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm resize-none"
                          placeholder="img2video prompt，不填则使用角色默认动作"
                        />
                        <button
                          type="button"
                          onClick={handleGenerateVideoMedia}
                          disabled={Boolean(mediaGenerating || uploadingField)}
                          className="inline-flex items-center gap-2 rounded-lg bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
                        >
                          {mediaGenerating === 'img2video' ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Film className="h-4 w-4" />
                          )}
                          生成视频
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                <h2 className="text-lg font-semibold mb-4">SFW 图片资源</h2>

                <div className="space-y-4">
                  <div>
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <label className="text-sm text-zinc-400">头像 (SFW)</label>
                      {renderMediaUpload('avatar_url', 'image/*')}
                    </div>
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
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <label className="text-sm text-zinc-400">封面 (SFW)</label>
                      {renderMediaUpload('cover_url', 'image/*')}
                    </div>
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
                <h2 className="text-lg font-semibold text-red-400">Mature 资源</h2>
                <div className="flex gap-2">
                  <button
                    onClick={handleRegenerateMatureImage}
                    disabled={regenerating}
                    className="px-3 py-1.5 bg-red-900/50 hover:bg-red-800/50 border border-red-700/50 rounded-lg text-xs text-red-300 flex items-center gap-1 disabled:opacity-50"
                  >
                    {regenerating ? <RefreshCw className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                    重新生成图片                  </button>
                  <button
                    onClick={handleRegenerateMatureVideo}
                    disabled={regenerating}
                    className="px-3 py-1.5 bg-red-900/50 hover:bg-red-800/50 border border-red-700/50 rounded-lg text-xs text-red-300 flex items-center gap-1 disabled:opacity-50"
                  >
                    {regenerating ? <RefreshCw className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                    重新生成视频                  </button>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-zinc-500 mb-2">Mature 头像</label>
                    {formData.mature_image_url ? (
                      <img
                        src={formData.mature_image_url}
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
                    {formData.mature_cover_url ? (
                      <img
                        src={formData.mature_cover_url}
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
                  {formData.mature_video_url ? (
                    <video
                      src={formData.mature_video_url}
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
              <h2 className="text-lg font-semibold mb-4">状态设置</h2>

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
                    <>
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
                      <button
                        type="button"
                        onClick={handlePreviewVoice}
                        disabled={!formData.voice_id || previewLoading}
                        className="mt-2 px-3 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm disabled:opacity-50"
                        title="试听"
                      >
                        {previewLoading ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : playingVoiceDbId && getSelectedVoice()?.id === playingVoiceDbId ? (
                          <Pause className="w-4 h-4" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </button>
                    </>
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

