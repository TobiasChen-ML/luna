import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Loader2, Save, Check, AlertTriangle, X
} from 'lucide-react';
import { api } from '@/services/api';
import { useAdminAuth } from '@/hooks/useAdminAuth';

interface Story {
  id: string;
  title: string;
  title_en: string;
  summary: string;
  emotion_tones: string;
  relation_types: string;
  contrast_types: string;
  era: string;
  gender_target: string;
  character_gender: string;
  profession: string;
  length: string;
  age_rating: string;
  contrast_surface: string;
  contrast_truth: string;
  contrast_hook: string;
  script_seed: string;
  full_script: string;
  status: string;
  popularity: number;
}

const EMOTION_TONES = ['sweet', 'angst', 'healing', 'comedy', 'dark', 'suspense', 'revenge', 'ethical', 'rebirth', 'harem', 'thriller'];
const ERAS = ['modern_urban', 'modern_campus', 'ancient_palace', 'ancient_jianghu', 'ancient_xianxia', 'fantasy_demon', 'fantasy_dragon', 'fantasy_elf', 'fantasy_isekai', 'fantasy_youkai', 'fantasy_phoenix', 'future_cyberpunk', 'future_space', 'future_virtual', 'future_mecha', 'future_apocalypse', 'republic_concession', 'republic_warlord'];
const GENDERS = ['male', 'female'];
const CHARACTER_GENDERS = ['male_char', 'female_char'];
const LENGTHS = ['short', 'medium', 'long'];
const AGE_RATINGS = ['all', 'mature'];
const STATUSES = ['draft', 'pending', 'published'];

const LABELS: Record<string, Record<string, string>> = {
  era: {
    modern_urban: '现代都市', modern_campus: '现代校园', ancient_palace: '古代宫廷',
    ancient_jianghu: '古代江湖', ancient_xianxia: '古代仙侠', fantasy_demon: '玄幻魔界',
    fantasy_dragon: '玄幻龙族', fantasy_elf: '玄幻精灵', fantasy_isekai: '异世界',
    fantasy_youkai: '玄幻妖怪', fantasy_phoenix: '玄幻凤凰', future_cyberpunk: '未来赛博',
    future_space: '未来太空', future_virtual: '未来虚拟', future_mecha: '未来机甲',
    future_apocalypse: '未来末世', republic_concession: '民国租界', republic_warlord: '民国军阀'
  },
  character_gender: { male_char: '男主', female_char: '女主' },
  gender_target: { male: '面向男性', female: '面向女性' },
  length: { short: '短篇', medium: '中篇', long: '长篇' },
  age_rating: { all: '全年龄', mature: '成人' },
  status: { draft: '草稿', pending: '待审核', published: '已发布' },
  emotion_tones: {
    sweet: '甜蜜', angst: '虐心', healing: '治愈', comedy: '搞笑', dark: '暗黑',
    suspense: '悬疑', revenge: '复仇', ethical: '伦理', rebirth: '重生', harem: '后宫', thriller: '惊悚'
  }
};

function getLabel(category: string, key: string): string {
  return LABELS[category]?.[key] || key;
}

export default function StoryEditPage() {
  const { storyId } = useParams<{ storyId: string }>();
  const navigate = useNavigate();
  const { isAdmin, loading: authLoading } = useAdminAuth();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  const [formData, setFormData] = useState<Story>({
    id: '',
    title: '',
    title_en: '',
    summary: '',
    emotion_tones: '[]',
    relation_types: '[]',
    contrast_types: '[]',
    era: 'modern_urban',
    gender_target: 'male',
    character_gender: 'female_char',
    profession: '',
    length: 'medium',
    age_rating: 'all',
    contrast_surface: '',
    contrast_truth: '',
    contrast_hook: '',
    script_seed: '{}',
    full_script: '',
    status: 'draft',
    popularity: 0,
  });

  const fetchStory = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/admin/stories/${storyId}/edit`);
      const data = response.data?.story || response.data || response;
      setFormData({
        ...data,
        emotion_tones: data.emotion_tones || '[]',
        relation_types: data.relation_types || '[]',
        contrast_types: data.contrast_types || '[]',
        script_seed: data.script_seed || '{}',
      });
    } catch (error) {
      console.error('Failed to fetch story:', error);
      setMessage({ type: 'error', text: '加载剧本失败' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading || !isAdmin) return;
    if (storyId) {
      fetchStory();
    } else {
      setLoading(false);
    }
  }, [storyId, authLoading, isAdmin]);

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
      if (storyId) {
        await api.post(`/admin/stories/${storyId}/update`, formData);
        setMessage({ type: 'success', text: '保存成功' });
      } else {
        await api.post('/admin/stories/create', formData);
        setMessage({ type: 'success', text: '创建成功' });
        navigate(-1);
      }
    } catch (error) {
      console.error('Failed to save story:', error);
      setMessage({ type: 'error', text: '保存失败' });
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field: keyof Story, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleArrayToggle = (field: 'emotion_tones' | 'relation_types' | 'contrast_types', value: string) => {
    const arr = JSON.parse(formData[field] || '[]');
    const newArr = arr.includes(value) ? arr.filter((v: string) => v !== value) : [...arr, value];
    setFormData(prev => ({ ...prev, [field]: JSON.stringify(newArr) }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="p-2 hover:bg-zinc-800 rounded-lg"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-2xl font-bold">
              {storyId ? '编辑剧本' : '创建剧本'}
            </h1>
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            保存
          </button>
        </div>

        {message && (
          <div className={`p-4 rounded-lg flex items-center gap-2 mb-6 ${
            message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'
          }`}>
            {message.type === 'success' ? <Check className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
            {message.text}
            <button onClick={() => setMessage(null)} className="ml-auto">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        <div className="space-y-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">基本信息</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-1">标题 (中文)</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleChange('title', e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">标题 (英文)</label>
                <input
                  type="text"
                  value={formData.title_en}
                  onChange={(e) => handleChange('title_en', e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-sm text-zinc-400 mb-1">摘要</label>
                <textarea
                  value={formData.summary}
                  onChange={(e) => handleChange('summary', e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">分类标签</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-1">时代背景</label>
                <select
                  value={formData.era}
                  onChange={(e) => handleChange('era', e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                >
                  {ERAS.map(e => (
                    <option key={e} value={e}>{getLabel('era', e)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">角色性别</label>
                <select
                  value={formData.character_gender}
                  onChange={(e) => handleChange('character_gender', e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                >
                  {CHARACTER_GENDERS.map(g => (
                    <option key={g} value={g}>{getLabel('character_gender', g)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">目标受众</label>
                <select
                  value={formData.gender_target}
                  onChange={(e) => handleChange('gender_target', e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                >
                  {GENDERS.map(g => (
                    <option key={g} value={g}>{getLabel('gender_target', g)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">职业</label>
                <input
                  type="text"
                  value={formData.profession}
                  onChange={(e) => handleChange('profession', e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">篇幅</label>
                <select
                  value={formData.length}
                  onChange={(e) => handleChange('length', e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                >
                  {LENGTHS.map(l => (
                    <option key={l} value={l}>{getLabel('length', l)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">年龄分级</label>
                <select
                  value={formData.age_rating}
                  onChange={(e) => handleChange('age_rating', e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                >
                  {AGE_RATINGS.map(a => (
                    <option key={a} value={a}>{getLabel('age_rating', a)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">状态</label>
                <select
                  value={formData.status}
                  onChange={(e) => handleChange('status', e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                >
                  {STATUSES.map(s => (
                    <option key={s} value={s}>{getLabel('status', s)}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mt-4">
              <label className="block text-sm text-zinc-400 mb-2">情感基调</label>
              <div className="flex flex-wrap gap-2">
                {EMOTION_TONES.map(tone => {
                  const selected = JSON.parse(formData.emotion_tones || '[]').includes(tone);
                  return (
                    <button
                      key={tone}
                      type="button"
                      onClick={() => handleArrayToggle('emotion_tones', tone)}
                      className={`px-3 py-1 rounded-full text-sm transition-colors ${
                        selected
                          ? 'bg-pink-600 text-white'
                          : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                      }`}
                    >
                      {getLabel('emotion_tones', tone)}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">反差设定</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-1">表面形象</label>
                <textarea
                  value={formData.contrast_surface}
                  onChange={(e) => handleChange('contrast_surface', e.target.value)}
                  rows={2}
                  placeholder="角色在外人面前的样子..."
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">真实面貌</label>
                <textarea
                  value={formData.contrast_truth}
                  onChange={(e) => handleChange('contrast_truth', e.target.value)}
                  rows={2}
                  placeholder="角色私下的真实样子..."
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">吸引点</label>
                <textarea
                  value={formData.contrast_hook}
                  onChange={(e) => handleChange('contrast_hook', e.target.value)}
                  rows={2}
                  placeholder="只有你能看到的特别之处..."
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">剧本内容 (JSON)</h2>
            <div>
              <label className="block text-sm text-zinc-400 mb-1">完整剧本</label>
              <textarea
                value={formData.full_script || ''}
                onChange={(e) => handleChange('full_script', e.target.value)}
                rows={10}
                placeholder="JSON 格式的完整剧本..."
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none font-mono text-sm"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
