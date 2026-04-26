import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Loader2, Save, Eye, EyeOff, RefreshCw, Check, X, Plus, Trash2, Edit2, AlertTriangle } from 'lucide-react';
import { api } from '@/services/api';
import {
  createOpenPosePreset,
  deleteOpenPosePreset,
  fetchAdminOpenPosePresets,
  type OpenPosePreset,
  updateOpenPosePreset,
  uploadOpenPoseImage,
} from '@/services/openposePresetService';

interface ModelInfo {
  id: string;
  display_name: string;
  context_size?: number;
  input_price?: number;
  output_price?: number;
  features?: string[];
  description?: string;
  base_model?: string;
  is_sdxl?: boolean;
  is_mature?: boolean;
  cover_url?: string;
}

interface ConfigField {
  key: string;
  label: string;
  type: string;
  placeholder?: string;
  default?: string;
  required: boolean;
  secret: boolean;
  description?: string;
  value?: string;
  options?: { value: string; label: string }[];
  model_provider?: string;
}

interface ConfigGroup {
  group: string;
  label: string;
  description?: string;
  fields: ConfigField[];
}

interface Preset {
  id: string;
  name: string;
  category: string;
  config: Record<string, string>;
  is_active: boolean;
  is_builtin: boolean;
  created_at?: string;
  updated_at?: string;
}

type LoRAAppliesTo = 'txt2img' | 'img2img' | 'video' | 'all';
type LoRAFormatType = 'civitai' | 'sdxl';
type LoRAPromptTemplateMode = 'append_trigger' | 'use_example';

function detectLoraFormat(modelName: string): LoRAFormatType {
  return modelName.startsWith('civitai:') ? 'civitai' : 'sdxl';
}

const LORA_FORMAT_LABELS: Record<LoRAFormatType, { label: string; color: string }> = {
  civitai: { label: 'Z-Turbo', color: 'bg-orange-900/60 text-orange-300' },
  sdxl:    { label: 'SDXL',    color: 'bg-blue-900/60 text-blue-300' },
};

interface LoRAPreset {
  id: string;
  name: string;
  model_name: string;
  strength: number;
  trigger_word: string;
  example_prompt: string;
  example_negative_prompt: string;
  prompt_template_mode: LoRAPromptTemplateMode;
  applies_to: LoRAAppliesTo;
  provider: string;
  is_active: boolean | number;
}

const EMPTY_LORA: Omit<LoRAPreset, 'id'> = {
  name: '',
  model_name: '',
  strength: 0.6,
  trigger_word: '',
  example_prompt: '',
  example_negative_prompt: '',
  prompt_template_mode: 'append_trigger',
  applies_to: 'all',
  provider: 'novita',
  is_active: true,
};

const EMPTY_OPENPOSE = {
  name: '',
  image_url: '',
  is_active: true,
};

const FIELD_CONDITIONS: Record<string, (provider: string) => boolean> = {
  LLM_LOCAL_BASE_URL: (p) => p === 'ollama',
};

const TXT2IMG_PROVIDER_KEYS: Record<string, string[]> = {
  novita: ['NOVITA_API_KEY', 'NOVITA_BASE_URL', 'NOVITA_WEBHOOK_BASE_URL'],
  z_image_turbo_lora: ['NOVITA_API_KEY', 'NOVITA_BASE_URL', 'NOVITA_WEBHOOK_BASE_URL'],
  fal: ['FAL_API_KEY', 'FAL_BASE_URL'],
};

const IMG2VIDEO_PROVIDER_KEYS: Record<string, string[]> = {
  novita: ['NOVITA_API_KEY', 'NOVITA_BASE_URL', 'NOVITA_WEBHOOK_BASE_URL'],
  sora: ['SORA_API_KEY', 'SORA_BASE_URL'],
};

const TXT2IMG_PARAM_KEYS = new Set([
  'IMAGE_TXT2IMG_MODEL',
  'IMAGE_DEFAULT_WIDTH', 'IMAGE_DEFAULT_HEIGHT',
  'IMAGE_DEFAULT_STEPS', 'IMAGE_DEFAULT_CFG',
]);

const IMG2IMG_PARAM_KEYS = new Set([
  'IMAGE_IMG2IMG_MODEL',
  'IMG2IMG_STRENGTH',
  'IP_ADAPTER_STRENGTH',
  'OPENPOSE_CONTROLNET_STRENGTH',
  'IMG2IMG_SAMPLER',
]);

const VIDEO_PARAM_KEYS = new Set([
  'VIDEO_MODEL',
]);

const IMAGE_PRESET_KEYS = [
  'IMAGE_PROVIDER', 'IMAGE_TXT2IMG_MODEL', 'IMAGE_IMG2IMG_MODEL',
  'IMAGE_DEFAULT_WIDTH', 'IMAGE_DEFAULT_HEIGHT',
  'IMAGE_DEFAULT_STEPS', 'IMAGE_DEFAULT_CFG',
  'IMG2IMG_STRENGTH', 'IP_ADAPTER_STRENGTH', 'OPENPOSE_CONTROLNET_STRENGTH', 'IMG2IMG_SAMPLER',
];

const VIDEO_PRESET_KEYS = [
  'VIDEO_PROVIDER', 'VIDEO_MODEL',
];

export default function AdminSettingsPage() {
  const [groups, setGroups] = useState<ConfigGroup[]>([]);
  const [activeGroup, setActiveGroup] = useState<string>('llm');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [editValues, setEditValues] = useState<Record<string, string>>({});
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [availableModels, setAvailableModels] = useState<Record<string, ModelInfo[]>>({});
  const [modelsLoading, setModelsLoading] = useState<string | null>(null);

  const [imagePresets, setImagePresets] = useState<Preset[]>([]);
  const [videoPresets, setVideoPresets] = useState<Preset[]>([]);
  const [presetsLoading, setPresetsLoading] = useState(false);
  const [showSavePreset, setShowSavePreset] = useState<'image' | 'video' | null>(null);
  const [newPresetName, setNewPresetName] = useState('');
  const [activatingPreset, setActivatingPreset] = useState<string | null>(null);

  const [loraPresets, setLoraPresets] = useState<LoRAPreset[]>([]);
  const [loraLoading, setLoraLoading] = useState(false);
  const [loraForm, setLoraForm] = useState<Omit<LoRAPreset, 'id'>>(EMPTY_LORA);
  const [editingLoraId, setEditingLoraId] = useState<string | null>(null);
  const [loraFormSection, setLoraFormSection] = useState<LoRAAppliesTo | null>(null);
  const [showLoraForm, setShowLoraForm] = useState(false);
  const [loraSaving, setLoraSaving] = useState(false);
  const [loraFormatType, setLoraFormatType] = useState<LoRAFormatType>('sdxl');
  const [openPosePresets, setOpenPosePresets] = useState<OpenPosePreset[]>([]);
  const [openPoseLoading, setOpenPoseLoading] = useState(false);
  const [openPoseSaving, setOpenPoseSaving] = useState(false);
  const [openPoseUploading, setOpenPoseUploading] = useState(false);
  const [openPoseForm, setOpenPoseForm] = useState(EMPTY_OPENPOSE);
  const [editingOpenPoseId, setEditingOpenPoseId] = useState<string | null>(null);

  const currentProvider = useMemo(() => {
    if (editValues.LLM_PROVIDER !== undefined) return editValues.LLM_PROVIDER;
    const llmGroup = groups.find(g => g.group === 'llm');
    const providerField = llmGroup?.fields.find(f => f.key === 'LLM_PROVIDER');
    return providerField?.value || providerField?.default || 'novita';
  }, [editValues.LLM_PROVIDER, groups]);

  const imageProvider = useMemo(() => {
    if (editValues.IMAGE_PROVIDER !== undefined) return editValues.IMAGE_PROVIDER;
    const mediaGroup = groups.find(g => g.group === 'media');
    const field = mediaGroup?.fields.find(f => f.key === 'IMAGE_PROVIDER');
    return field?.value || field?.default || 'novita';
  }, [editValues.IMAGE_PROVIDER, groups]);

  const videoProvider = useMemo(() => {
    if (editValues.VIDEO_PROVIDER !== undefined) return editValues.VIDEO_PROVIDER;
    const mediaGroup = groups.find(g => g.group === 'media');
    const field = mediaGroup?.fields.find(f => f.key === 'VIDEO_PROVIDER');
    return field?.value || field?.default || 'novita';
  }, [editValues.VIDEO_PROVIDER, groups]);

  useEffect(() => {
    fetchConfigs();
  }, []);

  useEffect(() => {
    if (currentProvider) {
      fetchModelsForProvider(currentProvider);
    }
    if (currentProvider !== 'novita') {
      fetchModelsForProvider('novita');
    }
  }, [currentProvider]);

  useEffect(() => {
    if (activeGroup === 'media') {
      fetchPresets();
      fetchLoraPresets();
      fetchOpenPosePresets();
      fetchModelsForProvider('novita_image');
    }
  }, [activeGroup]);

  const fetchConfigs = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/api/config');
      setGroups(response.data.groups || []);
      if (response.data.groups?.length > 0 && !activeGroup) {
        setActiveGroup(response.data.groups[0].group);
      }
    } catch (error) {
      console.error('Failed to fetch configs:', error);
      setMessage({ type: 'error', text: 'Failed to load configurations' });
    } finally {
      setLoading(false);
    }
  };

  const fetchModelsForProvider = async (provider: string) => {
    if (availableModels[provider] && availableModels[provider].length > 0) return;
    setModelsLoading(provider);
    try {
      const response = await api.get(`/admin/api/config/models/${provider}`);
      setAvailableModels(prev => ({ ...prev, [provider]: response.data.models || [] }));
    } catch (error) {
      console.error(`Failed to fetch models for ${provider}:`, error);
    } finally {
      setModelsLoading(null);
    }
  };

  const fetchPresets = useCallback(async () => {
    setPresetsLoading(true);
    try {
      const [imageRes, videoRes] = await Promise.all([
        api.get('/admin/api/presets/image'),
        api.get('/admin/api/presets/video'),
      ]);
      setImagePresets(imageRes.data.presets || []);
      setVideoPresets(videoRes.data.presets || []);
    } catch (error) {
      console.error('Failed to fetch presets:', error);
    } finally {
      setPresetsLoading(false);
    }
  }, []);

  const fetchLoraPresets = useCallback(async () => {
    setLoraLoading(true);
    try {
      const res = await api.get('/admin/loras');
      setLoraPresets(res.data.loras || []);
    } catch (error) {
      console.error('Failed to fetch LoRA presets:', error);
    } finally {
      setLoraLoading(false);
    }
  }, []);

  const fetchOpenPosePresets = useCallback(async () => {
    setOpenPoseLoading(true);
    try {
      setOpenPosePresets(await fetchAdminOpenPosePresets());
    } catch (error) {
      console.error('Failed to fetch OpenPose presets:', error);
    } finally {
      setOpenPoseLoading(false);
    }
  }, []);

  const resetOpenPoseForm = () => {
    setOpenPoseForm(EMPTY_OPENPOSE);
    setEditingOpenPoseId(null);
  };

  const handleOpenPoseUpload = async (file: File | null) => {
    if (!file) return;
    setOpenPoseUploading(true);
    try {
      const imageUrl = await uploadOpenPoseImage(file);
      setOpenPoseForm((form) => ({ ...form, image_url: imageUrl }));
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to upload pose image' });
    } finally {
      setOpenPoseUploading(false);
    }
  };

  const handleOpenPoseSubmit = async () => {
    if (!openPoseForm.name.trim() || !openPoseForm.image_url.trim()) return;
    setOpenPoseSaving(true);
    try {
      if (editingOpenPoseId) {
        await updateOpenPosePreset(editingOpenPoseId, openPoseForm);
        setMessage({ type: 'success', text: 'OpenPose updated' });
      } else {
        await createOpenPosePreset(openPoseForm);
        setMessage({ type: 'success', text: 'OpenPose created' });
      }
      resetOpenPoseForm();
      await fetchOpenPosePresets();
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save OpenPose' });
    } finally {
      setOpenPoseSaving(false);
    }
  };

  const handleOpenPoseEdit = (pose: OpenPosePreset) => {
    setEditingOpenPoseId(pose.id);
    setOpenPoseForm({
      name: pose.name,
      image_url: pose.image_url,
      is_active: Boolean(pose.is_active),
    });
  };

  const handleOpenPoseDelete = async (id: string) => {
    if (!window.confirm('Delete this OpenPose preset?')) return;
    try {
      await deleteOpenPosePreset(id);
      setMessage({ type: 'success', text: 'OpenPose deleted' });
      await fetchOpenPosePresets();
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to delete OpenPose' });
    }
  };

  const closeLoraForm = () => {
    setShowLoraForm(false);
    setEditingLoraId(null);
    setLoraFormSection(null);
    setLoraForm(EMPTY_LORA);
    setLoraFormatType('sdxl');
  };

  const handleLoraSubmit = async () => {
    if (!loraForm.name.trim() || !loraForm.model_name.trim()) return;
    setLoraSaving(true);
    try {
      if (editingLoraId) {
        await api.put(`/admin/loras/${editingLoraId}`, loraForm);
        setMessage({ type: 'success', text: 'LoRA updated' });
      } else {
        await api.post('/admin/loras', loraForm);
        setMessage({ type: 'success', text: 'LoRA created' });
      }
      closeLoraForm();
      await fetchLoraPresets();
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save LoRA' });
    } finally {
      setLoraSaving(false);
    }
  };

  const handleLoraDelete = async (id: string) => {
    if (!window.confirm('Delete this LoRA preset?')) return;
    try {
      await api.delete(`/admin/loras/${id}`);
      setMessage({ type: 'success', text: 'LoRA deleted' });
      await fetchLoraPresets();
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to delete LoRA' });
    }
  };

  const handleLoraEdit = (lora: LoRAPreset, section: LoRAAppliesTo) => {
    setLoraForm({
      name: lora.name,
      model_name: lora.model_name,
      strength: lora.strength,
      trigger_word: lora.trigger_word,
      example_prompt: lora.example_prompt || '',
      example_negative_prompt: lora.example_negative_prompt || '',
      prompt_template_mode: lora.prompt_template_mode || 'append_trigger',
      applies_to: lora.applies_to,
      provider: lora.provider,
      is_active: Boolean(lora.is_active),
    });
    setLoraFormatType(detectLoraFormat(lora.model_name));
    setEditingLoraId(lora.id);
    setLoraFormSection(section);
    setShowLoraForm(true);
  };

  const handleActivatePreset = async (presetId: string) => {
    setActivatingPreset(presetId);
    try {
      await api.put(`/admin/api/presets/${presetId}/activate`);
      setMessage({ type: 'success', text: 'Preset activated' });
      await fetchPresets();
      await fetchConfigs();
      setEditValues({});
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to activate preset';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setActivatingPreset(null);
    }
  };

  const handleCreatePreset = async (category: 'image' | 'video') => {
    if (!newPresetName.trim()) return;
    const presetKeys = category === 'image' ? IMAGE_PRESET_KEYS : VIDEO_PRESET_KEYS;
    const config: Record<string, string> = {};

    const mediaGroup = groups.find(g => g.group === 'media');
    if (mediaGroup) {
      for (const key of presetKeys) {
        const field = mediaGroup.fields.find(f => f.key === key);
        const value = editValues[key] ?? field?.value ?? field?.default ?? '';
        if (value) config[key] = value;
      }
    }

    try {
      await api.post('/admin/api/presets', {
        name: newPresetName.trim(),
        category,
        config,
      });
      setNewPresetName('');
      setShowSavePreset(null);
      setMessage({ type: 'success', text: `Preset "${newPresetName}" created` });
      await fetchPresets();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to create preset';
      setMessage({ type: 'error', text: errorMsg });
    }
  };

  const handleDeletePreset = async (presetId: string) => {
    try {
      await api.delete(`/admin/api/presets/${presetId}`);
      setMessage({ type: 'success', text: 'Preset deleted' });
      await fetchPresets();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to delete preset';
      setMessage({ type: 'error', text: errorMsg });
    }
  };

  const handleSaveGroup = async (group: string) => {
    setSaving(true);
    setMessage(null);
    try {
      const groupFields = groups.find(g => g.group === group)?.fields || [];
      const values: Record<string, string> = {};

      for (const field of groupFields) {
        const editedValue = editValues[field.key];
        if (editedValue !== undefined) {
          values[field.key] = editedValue;
        }
      }

      if (Object.keys(values).length === 0) {
        setMessage({ type: 'error', text: 'No changes to save' });
        setSaving(false);
        return;
      }

      await api.put(`/admin/api/config/${group}`, { values });
      setMessage({ type: 'success', text: 'Configuration saved successfully' });

      setEditValues({});
      await fetchConfigs();
    } catch (error) {
      console.error('Failed to save config:', error);
      setMessage({ type: 'error', text: 'Failed to save configuration' });
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (key: string, value: string) => {
    setEditValues(prev => ({ ...prev, [key]: value }));
  };

  const handleTestEmail = async () => {
    setTesting(true);
    try {
      const res = await api.post('/admin/api/config/test/email', {});
      setMessage({ type: 'success', text: res.data.message });
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Email test failed';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setTesting(false);
    }
  };

  const toggleShowSecret = (key: string) => {
    setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const shouldShowField = (field: ConfigField): boolean => {
    const condition = FIELD_CONDITIONS[field.key];
    if (condition) return condition(currentProvider);
    return true;
  };

  const getModelProvider = (field: ConfigField): string => {
    if (field.model_provider) return field.model_provider;
    return currentProvider;
  };

  const renderField = (field: ConfigField, overrideModelProvider?: string) => {
    if (!shouldShowField(field)) return null;

    const currentValue = editValues[field.key] ?? (field.secret ? '' : (field.value ?? ''));
    const isSecret = field.secret;
    const showValue = showSecrets[field.key];
    const fieldPlaceholder = isSecret && field.value ? field.value : field.placeholder;
    const modelProvider = overrideModelProvider || getModelProvider(field);

    return (
      <div key={field.key} className="space-y-1">
        <label className="block text-sm font-medium text-zinc-200">
          {field.label}
          {field.required && <span className="text-red-400 ml-1">*</span>}
          {isSecret && (
            <button
              type="button"
              onClick={() => toggleShowSecret(field.key)}
              className="ml-2 text-zinc-400 hover:text-zinc-200"
            >
              {showValue ? <EyeOff className="w-4 h-4 inline" /> : <Eye className="w-4 h-4 inline" />}
            </button>
          )}
        </label>

        {field.description && (
          <p className="text-xs text-zinc-500">{field.description}</p>
        )}

        {field.type === 'boolean' ? (
          <select
            value={currentValue}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
          >
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        ) : field.type === 'select' ? (
          <select
            value={currentValue}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
          >
            <option value="">-- Select an option --</option>
            {(field.options || []).map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        ) : field.type === 'model_select' ? (
          <input
            type="text"
            value={currentValue}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            placeholder={field.placeholder || '-- Enter model id --'}
            className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
          />
        ) : field.type === 'number' ? (
          <input
            type="number"
            value={currentValue}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            placeholder={field.placeholder}
            className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
          />
        ) : (
          <input
            type={isSecret && !showValue ? 'password' : 'text'}
            value={currentValue}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            placeholder={fieldPlaceholder}
            className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
          />
        )}

        {field.default && (
          <p className="text-xs text-zinc-600">Default: {field.default}</p>
        )}
      </div>
    );
  };

  const renderPresetSelector = (category: 'image' | 'video', presets: Preset[]) => {
    const label = category === 'image' ? '图片预设' : '视频预设';
    const savingPreset = showSavePreset === category;

    return (
      <div className="mb-6 p-4 bg-zinc-800/50 rounded-lg border border-zinc-700/50">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-zinc-300">{label}</h3>
          <div className="flex items-center gap-2">
            {savingPreset ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={newPresetName}
                  onChange={(e) => setNewPresetName(e.target.value)}
                  placeholder="Preset name..."
                  className="px-2 py-1 text-xs bg-zinc-900 border border-zinc-600 rounded text-zinc-200 w-40 focus:border-pink-500 focus:outline-none"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleCreatePreset(category);
                    if (e.key === 'Escape') { setShowSavePreset(null); setNewPresetName(''); }
                  }}
                />
                <button
                  onClick={() => handleCreatePreset(category)}
                  disabled={!newPresetName.trim()}
                  className="px-2 py-1 text-xs bg-pink-600 hover:bg-pink-500 rounded disabled:opacity-50"
                >
                  Save
                </button>
                <button
                  onClick={() => { setShowSavePreset(null); setNewPresetName(''); }}
                  className="px-2 py-1 text-xs bg-zinc-700 hover:bg-zinc-600 rounded"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowSavePreset(category)}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-zinc-700 hover:bg-zinc-600 rounded text-zinc-300"
              >
                <Plus className="w-3 h-3" />
                Save as Preset
              </button>
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {presetsLoading ? (
            <Loader2 className="w-4 h-4 text-zinc-400 animate-spin" />
          ) : presets.length === 0 ? (
            <span className="text-xs text-zinc-500">No presets. Save current config as a preset.</span>
          ) : (
            presets.map(preset => (
              <div
                key={preset.id}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-colors ${
                  preset.is_active
                    ? 'bg-pink-600 text-white shadow-lg shadow-pink-600/20'
                    : 'bg-zinc-700 text-zinc-300 hover:bg-zinc-600'
                }`}
                onClick={() => {
                  if (!preset.is_active && activatingPreset !== preset.id) {
                    handleActivatePreset(preset.id);
                  }
                }}
              >
                {activatingPreset === preset.id ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : null}
                <span>{preset.name}</span>
                {preset.is_active && (
                  <span className="ml-1 px-1 py-0.5 bg-white/20 rounded text-[10px]">ACTIVE</span>
                )}
                {!preset.is_builtin && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeletePreset(preset.id);
                    }}
                    className="ml-1 text-zinc-400 hover:text-red-400"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  const renderLoraSection = (appliesTo: LoRAAppliesTo, label: string) => {
    const visible = loraPresets.filter(
      (l) => l.applies_to === appliesTo || l.applies_to === 'all'
    );
    const formBelongsHere = showLoraForm && loraFormSection === appliesTo;

    // Which LoRA format is compatible with the current provider for this section
    const compatibleFormat: LoRAFormatType | null =
      appliesTo === 'img2img' ? 'sdxl' :
      appliesTo === 'txt2img' ? (imageProvider === 'z_image_turbo_lora' ? 'civitai' : 'sdxl') :
      null; // video: no format restriction yet

    const isIncompatible = (lora: LoRAPreset) => {
      if (compatibleFormat === null) return false;
      return detectLoraFormat(lora.model_name) !== compatibleFormat;
    };

    // Placeholder and hint text driven by the selected format type in the form
    const modelNamePlaceholder =
      loraFormatType === 'civitai'
        ? 'e.g. civitai:2268008@2617751'
        : 'e.g. 44319 (Novita model id)';

    const showFormatSelector = loraForm.applies_to === 'txt2img' || loraForm.applies_to === 'img2img' || appliesTo !== 'video';

    return (
      <div className="mt-4 border border-zinc-700 rounded-lg p-4 bg-zinc-800/50">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
            {label} LoRA 库
          </span>
          <button
            onClick={() => {
              const defaultFormat: LoRAFormatType =
                appliesTo === 'txt2img' && imageProvider === 'z_image_turbo_lora' ? 'civitai' : 'sdxl';
              setLoraFormatType(defaultFormat);
              setLoraForm({ ...EMPTY_LORA, applies_to: appliesTo });
              setEditingLoraId(null);
              setLoraFormSection(appliesTo);
              setShowLoraForm(true);
            }}
            className="flex items-center gap-1 px-2 py-1 bg-pink-600/20 hover:bg-pink-600/40 text-pink-400 rounded text-xs"
          >
            <Plus className="w-3 h-3" /> 添加 LoRA
          </button>
        </div>

        {loraLoading ? (
          <div className="flex justify-center py-3">
            <Loader2 className="w-4 h-4 animate-spin text-zinc-500" />
          </div>
        ) : visible.length === 0 ? (
          <p className="text-xs text-zinc-600 py-2">暂无 LoRA，点击"添加 LoRA"创建</p>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="text-zinc-500 border-b border-zinc-700">
                <th className="text-left pb-2 font-medium">名称</th>
                <th className="text-left pb-2 font-medium">格式</th>
                <th className="text-left pb-2 font-medium">模型 ID</th>
                <th className="text-left pb-2 font-medium w-12">强度</th>
                <th className="text-left pb-2 font-medium w-14">状态</th>
                <th className="w-14" />
              </tr>
            </thead>
            <tbody>
              {visible.map((lora) => {
                const fmt = appliesTo === 'video' ? null : detectLoraFormat(lora.model_name);
                const incompatible = isIncompatible(lora);
                return (
                  <tr key={lora.id} className={`border-b border-zinc-700/50 hover:bg-zinc-700/20 ${incompatible ? 'opacity-60' : ''}`}>
                    <td className="py-2 pr-2 font-medium text-zinc-200">
                      <div className="flex items-center gap-1">
                        {incompatible && (
                          <span title={`当前 Provider (${imageProvider}) 不支持此格式，生成时会被跳过`}>
                            <AlertTriangle className="w-3 h-3 text-yellow-500 shrink-0" />
                          </span>
                        )}
                        {lora.name}
                      </div>
                    </td>
                    <td className="py-2 pr-2">
                      {fmt ? (
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${LORA_FORMAT_LABELS[fmt].color}`}>
                          {LORA_FORMAT_LABELS[fmt].label}
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-purple-900/60 text-purple-300">WAN</span>
                      )}
                    </td>
                    <td className="py-2 pr-2 text-zinc-400 max-w-[160px] truncate" title={lora.model_name}>
                      {lora.model_name}
                    </td>
                    <td className="py-2 pr-2 text-zinc-400">{lora.strength}</td>
                    <td className="py-2 pr-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        lora.is_active ? 'bg-green-900/50 text-green-400' : 'bg-zinc-700 text-zinc-500'
                      }`}>
                        {lora.is_active ? '启用' : '禁用'}
                      </span>
                    </td>
                    <td className="py-2">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleLoraEdit(lora, appliesTo)}
                          className="p-1 hover:text-pink-400 text-zinc-500 transition-colors"
                          title="编辑"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => handleLoraDelete(lora.id)}
                          className="p-1 hover:text-red-400 text-zinc-500 transition-colors"
                          title="删除"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        {formBelongsHere && (
          <div className="mt-4 pt-4 border-t border-zinc-700 space-y-3">
            <h4 className="text-xs font-semibold text-zinc-300">
              {editingLoraId ? '编辑 LoRA' : '新建 LoRA'}
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-zinc-400 mb-1">名称 *</label>
                <input
                  value={loraForm.name}
                  onChange={(e) => setLoraForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. Asian Style v2"
                  className="w-full bg-zinc-900 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white placeholder-zinc-600 focus:border-pink-500 outline-none"
                />
              </div>

              {/* 格式类型选择器：仅 txt2img / img2img 显示 */}
              {showFormatSelector && appliesTo !== 'video' && (
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">模型格式</label>
                  <select
                    value={loraFormatType}
                    onChange={(e) => {
                      const fmt = e.target.value as LoRAFormatType;
                      setLoraFormatType(fmt);
                      // 切换格式时清空 model_name 避免残留
                      setLoraForm((f) => ({ ...f, model_name: '' }));
                    }}
                    className="w-full bg-zinc-900 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:border-pink-500 outline-none"
                  >
                    <option value="sdxl">Novita SDXL (model id)</option>
                    <option value="civitai">Z-Image-Turbo (civitai:XXXXX@XXXXX)</option>
                  </select>
                  {appliesTo === 'img2img' && loraFormatType === 'civitai' && (
                    <p className="mt-1 text-[10px] text-yellow-500 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      图生图固定使用 SDXL，civitai 格式会被跳过
                    </p>
                  )}
                </div>
              )}

              <div className={showFormatSelector && appliesTo !== 'video' ? '' : 'col-span-1'}>
                <label className="block text-xs text-zinc-400 mb-1">模型 ID *</label>
                <input
                  value={loraForm.model_name}
                  onChange={(e) => setLoraForm((f) => ({ ...f, model_name: e.target.value }))}
                  placeholder={modelNamePlaceholder}
                  className="w-full bg-zinc-900 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white placeholder-zinc-600 focus:border-pink-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs text-zinc-400 mb-1">强度 (0.0 – 2.0)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="2"
                  value={loraForm.strength}
                  onChange={(e) => {
                    const v = parseFloat(e.target.value);
                    setLoraForm((f) => ({ ...f, strength: isNaN(v) ? 0 : v }));
                  }}
                  className="w-full bg-zinc-900 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:border-pink-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs text-zinc-400 mb-1">适用范围</label>
                <select
                  value={loraForm.applies_to}
                  onChange={(e) => setLoraForm((f) => ({ ...f, applies_to: e.target.value as LoRAAppliesTo }))}
                  className="w-full bg-zinc-900 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:border-pink-500 outline-none"
                >
                  <option value="all">全部</option>
                  <option value="txt2img">文生图</option>
                  <option value="img2img">图生图</option>
                  <option value="video">图生视频</option>
                </select>
              </div>

              <div className="col-span-2">
                <label className="block text-xs text-zinc-400 mb-1">触发词（可选，自动追加到提示词前）</label>
                <input
                  value={loraForm.trigger_word}
                  onChange={(e) => setLoraForm((f) => ({ ...f, trigger_word: e.target.value }))}
                  placeholder="e.g. asian style, detailed skin"
                  className="w-full bg-zinc-900 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white placeholder-zinc-600 focus:border-pink-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs text-zinc-400 mb-1">Prompt 模式</label>
                <select
                  value={loraForm.prompt_template_mode}
                  onChange={(e) => setLoraForm((f) => ({ ...f, prompt_template_mode: e.target.value as LoRAPromptTemplateMode }))}
                  className="w-full bg-zinc-900 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:border-pink-500 outline-none"
                >
                  <option value="append_trigger">append_trigger（触发词前置）</option>
                  <option value="use_example">use_example（示例模板）</option>
                </select>
              </div>

              <div className="col-span-2">
                <label className="block text-xs text-zinc-400 mb-1">示例正向 Prompt（可选）</label>
                <textarea
                  value={loraForm.example_prompt}
                  onChange={(e) => setLoraForm((f) => ({ ...f, example_prompt: e.target.value }))}
                  placeholder="可配置多条示例，每行一条；生成时会随机选择一条"
                  rows={3}
                  className="w-full bg-zinc-900 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white placeholder-zinc-600 focus:border-pink-500 outline-none resize-y"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-xs text-zinc-400 mb-1">示例负向 Prompt（可选）</label>
                <textarea
                  value={loraForm.example_negative_prompt}
                  onChange={(e) => setLoraForm((f) => ({ ...f, example_negative_prompt: e.target.value }))}
                  placeholder="可配置多条示例，每行一条；生成时会随机选择一条"
                  rows={3}
                  className="w-full bg-zinc-900 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white placeholder-zinc-600 focus:border-pink-500 outline-none resize-y"
                />
              </div>

              <div className="flex items-center gap-2">
                <label className="text-xs text-zinc-400">启用</label>
                <input
                  type="checkbox"
                  checked={Boolean(loraForm.is_active)}
                  onChange={(e) => setLoraForm((f) => ({ ...f, is_active: e.target.checked }))}
                  className="accent-pink-500"
                />
              </div>
            </div>

            <div className="flex gap-2 justify-end">
              <button
                onClick={closeLoraForm}
                className="px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 rounded text-xs"
              >
                取消
              </button>
              <button
                onClick={handleLoraSubmit}
                disabled={loraSaving || !loraForm.name.trim() || !loraForm.model_name.trim()}
                className="flex items-center gap-1 px-3 py-1.5 bg-pink-600 hover:bg-pink-500 rounded text-xs font-medium disabled:opacity-50"
              >
                {loraSaving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
                保存
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderOpenPoseSection = () => {
    return (
      <div className="mt-6 rounded-lg border border-zinc-700/60 bg-zinc-800/30 p-4">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-semibold text-zinc-200">OpenPose / DWPose presets</h4>
            <p className="mt-1 text-xs text-zinc-500">
              Upload pose reference images. Users see the pose name; generation sends the image through ControlNet.
            </p>
          </div>
          {openPoseLoading && <Loader2 className="h-4 w-4 animate-spin text-zinc-400" />}
        </div>

        <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-[1fr_1.4fr_auto]">
          <input
            value={openPoseForm.name}
            onChange={(e) => setOpenPoseForm((form) => ({ ...form, name: e.target.value }))}
            placeholder="Pose name"
            className="rounded bg-zinc-900 border border-zinc-600 px-3 py-2 text-sm text-white placeholder-zinc-600 focus:border-pink-500 outline-none"
          />
          <div className="flex gap-2">
            <input
              value={openPoseForm.image_url}
              onChange={(e) => setOpenPoseForm((form) => ({ ...form, image_url: e.target.value }))}
              placeholder="Image URL or upload"
              className="min-w-0 flex-1 rounded bg-zinc-900 border border-zinc-600 px-3 py-2 text-sm text-white placeholder-zinc-600 focus:border-pink-500 outline-none"
            />
            <label className="inline-flex cursor-pointer items-center gap-1 rounded bg-zinc-700 px-3 py-2 text-xs hover:bg-zinc-600">
              {openPoseUploading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
              Upload
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  void handleOpenPoseUpload(e.target.files?.[0] || null);
                  e.currentTarget.value = '';
                }}
              />
            </label>
          </div>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-1 text-xs text-zinc-400">
              <input
                type="checkbox"
                checked={openPoseForm.is_active}
                onChange={(e) => setOpenPoseForm((form) => ({ ...form, is_active: e.target.checked }))}
                className="accent-pink-500"
              />
              Active
            </label>
            {editingOpenPoseId && (
              <button onClick={resetOpenPoseForm} className="rounded bg-zinc-700 px-2 py-2 text-xs hover:bg-zinc-600">
                Cancel
              </button>
            )}
            <button
              onClick={handleOpenPoseSubmit}
              disabled={openPoseSaving || !openPoseForm.name.trim() || !openPoseForm.image_url.trim()}
              className="inline-flex items-center gap-1 rounded bg-pink-600 px-3 py-2 text-xs font-medium hover:bg-pink-500 disabled:opacity-50"
            >
              {openPoseSaving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
              {editingOpenPoseId ? 'Update' : 'Add'}
            </button>
          </div>
        </div>

        {openPosePresets.length === 0 ? (
          <div className="rounded border border-dashed border-zinc-700 px-3 py-4 text-center text-xs text-zinc-500">
            No OpenPose presets yet.
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {openPosePresets.map((pose) => (
              <div key={pose.id} className="overflow-hidden rounded-lg border border-zinc-700 bg-zinc-900">
                <div className="aspect-[3/4] bg-zinc-800">
                  <img src={pose.image_url} alt={pose.name} className="h-full w-full object-cover" loading="lazy" />
                </div>
                <div className="space-y-2 p-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-xs font-medium text-zinc-200">{pose.name}</span>
                    <span className={`rounded px-1.5 py-0.5 text-[10px] ${pose.is_active ? 'bg-green-900/50 text-green-300' : 'bg-zinc-700 text-zinc-400'}`}>
                      {pose.is_active ? 'Active' : 'Off'}
                    </span>
                  </div>
                  <div className="flex justify-end gap-1">
                    <button onClick={() => handleOpenPoseEdit(pose)} className="rounded p-1 text-zinc-500 hover:text-pink-400" title="Edit">
                      <Edit2 className="h-3 w-3" />
                    </button>
                    <button onClick={() => void handleOpenPoseDelete(pose.id)} className="rounded p-1 text-zinc-500 hover:text-red-400" title="Delete">
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderMediaGroup = () => {
    const mediaGroup = groups.find(g => g.group === 'media');
    if (!mediaGroup) return null;

    const providerSelectField = mediaGroup.fields.find(f => f.key === 'IMAGE_PROVIDER');
    const txt2imgFields = mediaGroup.fields.filter(f => TXT2IMG_PARAM_KEYS.has(f.key));
    const img2imgFields = mediaGroup.fields.filter(f => IMG2IMG_PARAM_KEYS.has(f.key));
    const videoProviderField = mediaGroup.fields.find(f => f.key === 'VIDEO_PROVIDER');
    const videoFields = mediaGroup.fields.filter(f => VIDEO_PARAM_KEYS.has(f.key));

    const txt2imgCredentialKeys = TXT2IMG_PROVIDER_KEYS[imageProvider] || [];
    const txt2imgCredentialFields = mediaGroup.fields.filter(f => txt2imgCredentialKeys.includes(f.key));
    const Z_TURBO_HIDDEN_KEYS = new Set(['IMAGE_TXT2IMG_MODEL', 'IMAGE_DEFAULT_STEPS', 'IMAGE_DEFAULT_CFG']);
    const isZTurbo = imageProvider === 'z_image_turbo_lora';

    const videoCredentialKeys = IMG2VIDEO_PROVIDER_KEYS[videoProvider] || [];
    const videoCredentialFields = mediaGroup.fields.filter(f => videoCredentialKeys.includes(f.key));

    return (
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-white">{mediaGroup.label}</h2>
          {mediaGroup.description && (
            <p className="text-zinc-400 text-sm mt-1">{mediaGroup.description}</p>
          )}
        </div>

        <div className="mb-8">
          <h3 className="text-sm font-semibold text-zinc-400 mb-4 pb-2 border-b border-zinc-700">
            文生图 (Text to Image)
          </h3>
          <div className="space-y-4">
            {providerSelectField && renderField(providerSelectField)}
            {/* Provider → LoRA 格式提示横幅 */}
            {imageProvider === 'z_image_turbo_lora' ? (
              <div className="flex items-start gap-2 px-3 py-2 bg-orange-900/20 border border-orange-700/40 rounded-lg text-xs text-orange-300">
                <span className="mt-0.5">⚡</span>
                <span>
                  当前使用 <strong>Z-Image-Turbo</strong> 端点，LoRA 需填写{' '}
                  <code className="bg-orange-900/40 px-1 rounded">civitai:XXXXXX@YYYYYYY</code> 格式（CivitAI 模型 ID）
                </span>
              </div>
            ) : imageProvider === 'novita' ? (
              <div className="flex items-start gap-2 px-3 py-2 bg-blue-900/20 border border-blue-700/40 rounded-lg text-xs text-blue-300">
                <span className="mt-0.5">🖼</span>
                <span>
                  当前使用 <strong>Novita SDXL</strong> 端点，LoRA 需填写{' '}
                  <code className="bg-blue-900/40 px-1 rounded">model_id</code>（Novita 模型 ID）
                </span>
              </div>
            ) : null}
            {txt2imgCredentialFields.map(f => renderField(f))}
            {txt2imgFields
              .filter(f => !isZTurbo || !Z_TURBO_HIDDEN_KEYS.has(f.key))
              .map(f => renderField(f, 'novita_image'))}
          </div>
          {renderLoraSection('txt2img', '文生图')}
        </div>

        {renderPresetSelector('image', imagePresets)}

        <div className="mb-8">
          <h3 className="text-sm font-semibold text-zinc-400 mb-4 pb-2 border-b border-zinc-700">
            图生图 (Image to Image)
          </h3>
          <div className="flex items-start gap-2 px-3 py-2 mb-4 bg-blue-900/20 border border-blue-700/40 rounded-lg text-xs text-blue-300">
            <span className="mt-0.5">🖼</span>
            <span>
              图生图固定使用 <strong>Novita SDXL</strong> 端点（<code className="bg-blue-900/40 px-1 rounded">/async/img2img</code>），
              LoRA 可直接填写 <code className="bg-blue-900/40 px-1 rounded">model_id</code>
            </span>
          </div>
          <div className="space-y-4">
            {img2imgFields.map(f => renderField(f, imageProvider === 'fal' ? 'fal' : 'novita_image'))}
          </div>
          {renderOpenPoseSection()}
          {renderLoraSection('img2img', '图生图')}
        </div>

        <div className="mb-8">
          <h3 className="text-sm font-semibold text-zinc-400 mb-4 pb-2 border-b border-zinc-700">
            图生视频 (Image to Video)
          </h3>
          <div className="space-y-4">
            {videoProviderField && renderField(videoProviderField)}
            {videoProvider === 'novita' && (
              <p className="text-xs text-zinc-500 -mt-2">
                使用文生图的 Novita API Key
              </p>
            )}
            {videoProvider === 'sora' && videoCredentialFields.map(f => renderField(f))}
            {videoFields.map(f => renderField(f))}
          </div>
          {renderLoraSection('video', '图生视频')}
        </div>

        {renderPresetSelector('video', videoPresets)}

        <div className="mt-6 pt-6 border-t border-zinc-800 flex justify-end gap-3">
          <button
            onClick={() => setEditValues({})}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm"
          >
            Reset
          </button>
          <button
            onClick={() => handleSaveGroup('media')}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save Changes
          </button>
        </div>
      </div>
    );
  };

  const activeGroupData = groups.find(g => g.group === activeGroup);

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">System Configuration</h1>
            <p className="text-zinc-400 text-sm mt-1">Manage API keys and service settings</p>
          </div>
          <button
            onClick={fetchConfigs}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {message && (
          <div className={`mb-6 p-4 rounded-lg flex items-center gap-2 ${
            message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'
          }`}>
            {message.type === 'success' ? <Check className="w-5 h-5" /> : <X className="w-5 h-5" />}
            {message.text}
          </div>
        )}

        <div className="flex gap-6">
          <div className="w-48 shrink-0">
            <nav className="space-y-1">
              {groups.map((group) => (
                <button
                  key={group.group}
                  onClick={() => setActiveGroup(group.group)}
                  className={`w-full text-left px-4 py-2 rounded-lg text-sm transition-colors ${
                    activeGroup === group.group
                      ? 'bg-pink-600 text-white'
                      : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'
                  }`}
                >
                  {group.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="flex-1">
            {activeGroup === 'media' ? (
              renderMediaGroup()
            ) : activeGroupData ? (
              <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
                <div className="mb-6">
                  <h2 className="text-lg font-semibold text-white">{activeGroupData.label}</h2>
                  {activeGroupData.description && (
                    <p className="text-zinc-400 text-sm mt-1">{activeGroupData.description}</p>
                  )}
                </div>

                <div className="space-y-4">
                  {activeGroupData.fields.map(f => renderField(f))}
                </div>

                <div className="mt-6 pt-6 border-t border-zinc-800 flex justify-end gap-3">
                  <button
                    onClick={() => setEditValues({})}
                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm"
                  >
                    Reset
                  </button>
                  {activeGroup === 'email' && (
                    <button
                      onClick={handleTestEmail}
                      disabled={testing}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium disabled:opacity-50"
                    >
                      {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>📧</span>}
                      Test Email
                    </button>
                  )}
                  <button
                    onClick={() => handleSaveGroup(activeGroup)}
                    disabled={saving}
                    className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    Save Changes
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
