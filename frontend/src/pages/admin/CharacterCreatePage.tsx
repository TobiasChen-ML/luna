import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Loader2, Wand2, Sparkles, Check, AlertTriangle,
  Image as ImageIcon, RefreshCw
} from 'lucide-react';
import { api } from '@/services/api';
import { useAdminAuth } from '@/hooks/useAdminAuth';
import { CHARACTER_TEMPLATES } from '@/types/character-templates';

type GenerationMode = 'batch' | 'template' | 'manual';

interface CharacterForm {
  name: string;
  first_name: string;
  age: number;
  description: string;
  top_category: string;
  personality_tags: string[];
  backstory: string;
  greeting: string;
  generate_images: boolean;
  generate_video: boolean;
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

export default function CharacterCreatePage() {
  const navigate = useNavigate();
  const { isAdmin, loading: authLoading } = useAdminAuth();
  const [mode, setMode] = useState<GenerationMode>('batch');
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  const [batchConfig, setBatchConfig] = useState({
    count: 5,
    top_category: 'girls',
    personality_preferences: [] as string[],
    age_min: 20,
    age_max: 30,
    generate_images: true,
    optimize_seo: true,
  });
  
  const [templateConfig, setTemplateConfig] = useState({
    template_id: 'college_student',
    variations: 1,
    generate_images: true,
    optimize_seo: true,
  });
  
  const [manualForm, setManualForm] = useState<CharacterForm>({
    name: '',
    first_name: '',
    age: 25,
    description: '',
    top_category: 'girls',
    personality_tags: [],
    backstory: '',
    greeting: '',
    generate_images: true,
    generate_video: true,
  });
  
  const [templates, setTemplates] = useState<any[]>([]);

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/admin/api/character-templates');
      setTemplates(response.data || []);
    } catch (error) {
      setTemplates(CHARACTER_TEMPLATES);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

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

  const handleBatchGenerate = async () => {
    setGenerating(true);
    setMessage(null);
    
    try {
      const response = await api.post('/admin/api/characters/batch-generate', batchConfig);
      
      if (response.data?.success) {
        setMessage({
          type: 'success',
          text: `成功创建 ${response.data.created_count} 个角色`,
        });
        
        if (response.data.created_count > 0) {
          setTimeout(() => {
            navigate(-1);
          }, 2000);
        }
      }
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || '批量生成失败',
      });
    } finally {
      setGenerating(false);
    }
  };
  
  const handleTemplateGenerate = async () => {
    setGenerating(true);
    setMessage(null);
    
    try {
      const response = await api.post('/admin/api/characters/from-template', templateConfig);
      
      if (response.data?.success) {
        setMessage({
          type: 'success',
          text: `成功创建 ${response.data.created_count} 个角色`,
        });
        
        if (response.data.created_count > 0) {
          setTimeout(() => {
            navigate(-1);
          }, 2000);
        }
      }
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || '模板生成失败',
      });
    } finally {
      setGenerating(false);
    }
  };
  
  const handleManualCreate = async () => {
    if (!manualForm.name.trim()) {
      setMessage({ type: 'error', text: '请输入角色名称' });
      return;
    }
    
    setGenerating(true);
    setMessage(null);
    
    try {
      await api.post('/admin/api/characters', manualForm);
      
      setMessage({
        type: 'success',
        text: '角色创建成功',
      });
      
      setTimeout(() => {
        navigate(-1);
      }, 1500);
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || '创建失败',
      });
    } finally {
      setGenerating(false);
    }
  };
  
  const togglePersonality = (trait: string, target: 'batch' | 'manual') => {
    if (target === 'batch') {
      const current = batchConfig.personality_preferences;
      if (current.includes(trait)) {
        setBatchConfig({
          ...batchConfig,
          personality_preferences: current.filter(t => t !== trait),
        });
      } else {
        setBatchConfig({
          ...batchConfig,
          personality_preferences: [...current, trait],
        });
      }
    } else {
      const current = manualForm.personality_tags;
      if (current.includes(trait)) {
        setManualForm({
          ...manualForm,
          personality_tags: current.filter(t => t !== trait),
        });
      } else {
        setManualForm({
          ...manualForm,
          personality_tags: [...current, trait],
        });
      }
    }
  };
  
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-zinc-800 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-2xl font-bold">创建角色</h1>
        </div>
        
        <div className="flex gap-2 mb-6">
          {(['batch', 'template', 'manual'] as GenerationMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                mode === m
                  ? 'bg-pink-600 text-white'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
              }`}
            >
              {m === 'batch' ? '批量AI生成' : m === 'template' ? '模板变体' : '手动创建'}
            </button>
          ))}
        </div>
        
        {message && (
          <div className={`mb-6 p-4 rounded-lg flex items-center gap-2 ${
            message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'
          }`}>
            {message.type === 'success' ? <Check className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
            {message.text}
          </div>
        )}
        
        {mode === 'batch' && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-2">生成数量</label>
                <input
                  type="number"
                  value={batchConfig.count}
                  onChange={(e) => setBatchConfig({ ...batchConfig, count: parseInt(e.target.value) || 1 })}
                  min={1}
                  max={50}
                  className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-2">分类</label>
                <select
                  value={batchConfig.top_category}
                  onChange={(e) => setBatchConfig({ ...batchConfig, top_category: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                >
                  {CATEGORY_OPTIONS.map((cat) => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-2">最小年龄</label>
                <input
                  type="number"
                  value={batchConfig.age_min}
                  onChange={(e) => setBatchConfig({ ...batchConfig, age_min: parseInt(e.target.value) || 18 })}
                  min={18}
                  max={99}
                  className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-2">最大年龄</label>
                <input
                  type="number"
                  value={batchConfig.age_max}
                  onChange={(e) => setBatchConfig({ ...batchConfig, age_max: parseInt(e.target.value) || 30 })}
                  min={18}
                  max={99}
                  className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm text-zinc-400 mb-2">性格偏好（可选）</label>
              <div className="flex flex-wrap gap-2">
                {PERSONALITY_OPTIONS.map((trait) => (
                  <button
                    key={trait}
                    onClick={() => togglePersonality(trait, 'batch')}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                      batchConfig.personality_preferences.includes(trait)
                        ? 'bg-pink-600 text-white'
                        : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                    }`}
                  >
                    {trait}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={batchConfig.generate_images}
                  onChange={(e) => setBatchConfig({ ...batchConfig, generate_images: e.target.checked })}
                  className="rounded border-zinc-600"
                />
                <span className="text-sm text-zinc-300">自动生成图片</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={batchConfig.optimize_seo}
                  onChange={(e) => setBatchConfig({ ...batchConfig, optimize_seo: e.target.checked })}
                  className="rounded border-zinc-600"
                />
                <span className="text-sm text-zinc-300">SEO优化</span>
              </label>
            </div>
            
            <button
              onClick={handleBatchGenerate}
              disabled={generating}
              className="w-full py-3 bg-pink-600 hover:bg-pink-500 rounded-lg font-medium flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {generating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  生成中...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  开始批量生成
                </>
              )}
            </button>
          </div>
        )}
        
        {mode === 'template' && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-6">
            <div>
              <label className="block text-sm text-zinc-400 mb-2">选择模板</label>
              <select
                value={templateConfig.template_id}
                onChange={(e) => setTemplateConfig({ ...templateConfig, template_id: e.target.value })}
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
              >
                {templates.map((t: any) => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm text-zinc-400 mb-2">变体数量</label>
              <input
                type="number"
                value={templateConfig.variations}
                onChange={(e) => setTemplateConfig({ ...templateConfig, variations: parseInt(e.target.value) || 1 })}
                min={1}
                max={10}
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
              />
            </div>
            
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={templateConfig.generate_images}
                  onChange={(e) => setTemplateConfig({ ...templateConfig, generate_images: e.target.checked })}
                  className="rounded border-zinc-600"
                />
                <span className="text-sm text-zinc-300">自动生成图片</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={templateConfig.optimize_seo}
                  onChange={(e) => setTemplateConfig({ ...templateConfig, optimize_seo: e.target.checked })}
                  className="rounded border-zinc-600"
                />
                <span className="text-sm text-zinc-300">SEO优化</span>
              </label>
            </div>
            
            <button
              onClick={handleTemplateGenerate}
              disabled={generating}
              className="w-full py-3 bg-pink-600 hover:bg-pink-500 rounded-lg font-medium flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {generating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  生成中...
                </>
              ) : (
                <>
                  <Wand2 className="w-5 h-5" />
                  从模板创建
                </>
              )}
            </button>
          </div>
        )}
        
        {mode === 'manual' && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-2">角色名称 *</label>
                <input
                  type="text"
                  value={manualForm.name}
                  onChange={(e) => setManualForm({ ...manualForm, name: e.target.value })}
                  placeholder="输入角色名称"
                  className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-2">名字（显示用）</label>
                <input
                  type="text"
                  value={manualForm.first_name}
                  onChange={(e) => setManualForm({ ...manualForm, first_name: e.target.value })}
                  placeholder="Emma"
                  className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-2">年龄</label>
                <input
                  type="number"
                  value={manualForm.age}
                  onChange={(e) => setManualForm({ ...manualForm, age: parseInt(e.target.value) || 25 })}
                  min={18}
                  max={99}
                  className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-2">分类</label>
                <select
                  value={manualForm.top_category}
                  onChange={(e) => setManualForm({ ...manualForm, top_category: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
                >
                  {CATEGORY_OPTIONS.map((cat) => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm text-zinc-400 mb-2">简介</label>
              <textarea
                value={manualForm.description}
                onChange={(e) => setManualForm({ ...manualForm, description: e.target.value })}
                placeholder="角色简介..."
                rows={2}
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg resize-none"
              />
            </div>
            
            <div>
              <label className="block text-sm text-zinc-400 mb-2">性格标签</label>
              <div className="flex flex-wrap gap-2">
                {PERSONALITY_OPTIONS.map((trait) => (
                  <button
                    key={trait}
                    onClick={() => togglePersonality(trait, 'manual')}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                      manualForm.personality_tags.includes(trait)
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
                value={manualForm.backstory}
                onChange={(e) => setManualForm({ ...manualForm, backstory: e.target.value })}
                placeholder="角色背景故事..."
                rows={3}
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg resize-none"
              />
            </div>
            
            <div>
              <label className="block text-sm text-zinc-400 mb-2">开场白</label>
              <textarea
                value={manualForm.greeting}
                onChange={(e) => setManualForm({ ...manualForm, greeting: e.target.value })}
                placeholder="角色的开场白..."
                rows={2}
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg resize-none"
              />
            </div>

            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={manualForm.generate_images}
                  onChange={(e) => setManualForm({ ...manualForm, generate_images: e.target.checked })}
                  className="w-4 h-4 accent-pink-500"
                />
                <span className="text-sm text-zinc-300">生成图片 (SFW + Mature)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={manualForm.generate_video}
                  onChange={(e) => setManualForm({ ...manualForm, generate_video: e.target.checked })}
                  disabled={!manualForm.generate_images}
                  className="w-4 h-4 accent-pink-500 disabled:opacity-50"
                />
                <span className="text-sm text-zinc-300">生成视频 (Mature)</span>
              </label>
            </div>

            <button
              onClick={handleManualCreate}
              disabled={generating || !manualForm.name.trim()}
              className="w-full py-3 bg-pink-600 hover:bg-pink-500 rounded-lg font-medium flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {generating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  创建中...
                </>
              ) : (
                <>
                  <Check className="w-5 h-5" />
                  创建角色
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
