/**
 * Trigger Editor
 * 
 * Edit trigger configuration in script
 */

import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Card } from '../common/Card';

interface ScriptTrigger {
  trigger_id: string;
  name: string;
  trigger_type: string;
  conditions: Record<string, unknown>;
  target_scene_id?: string;
  description?: string;
  one_time?: boolean;
}

interface SceneConfig {
  scene_id: string;
  name: string;
}

interface TriggerEditorProps {
  triggers: ScriptTrigger[];
  scenes: SceneConfig[];
  onAdd: (trigger: ScriptTrigger) => void;
  onUpdate: (index: number, trigger: ScriptTrigger) => void;
  onRemove: (index: number) => void;
}

const TRIGGER_TYPES = [
  { value: 'keyword', label: 'Keyword Trigger', description: 'Triggers when user message contains keywords' },
  { value: 'affection', label: 'Affection Trigger', description: 'Triggers when affection reaches a threshold' },
  { value: 'trust', label: 'Trust Trigger', description: 'Triggers when trust reaches a threshold' },
  { value: 'time', label: 'Time Trigger', description: 'Triggers after a set number of turns' },
  { value: 'emotion', label: 'Emotion Trigger', description: 'Triggers when a specific emotion is detected' },
  { value: 'custom', label: 'Custom Trigger', description: 'Custom condition' },
];

export const TriggerEditor: React.FC<TriggerEditorProps> = ({
  triggers,
  scenes,
  onAdd,
  onUpdate,
  onRemove,
}) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  
  const [formData, setFormData] = useState<ScriptTrigger>({
    trigger_id: '',
    name: '',
    trigger_type: 'keyword',
    conditions: {},
    target_scene_id: '',
    description: '',
    one_time: false,
  });
  
  // Condition value (depends on trigger type)
  const [conditionValue, setConditionValue] = useState('');
  
  const resetForm = () => {
    setFormData({
      trigger_id: '',
      name: '',
      trigger_type: 'keyword',
      conditions: {},
      target_scene_id: '',
      description: '',
      one_time: false,
    });
    setConditionValue('');
    setEditingIndex(null);
    setShowAddForm(false);
  };
  
  const handleEdit = (index: number) => {
    const trigger = triggers[index];
    setFormData(trigger);
    
    // Parse condition value
    if (trigger.trigger_type === 'keyword' && trigger.conditions.keywords) {
      setConditionValue((trigger.conditions.keywords as string[]).join(', '));
    } else if (['affection', 'trust'].includes(trigger.trigger_type) && trigger.conditions.min) {
      setConditionValue(String(trigger.conditions.min));
    } else if (trigger.trigger_type === 'time' && trigger.conditions.turns) {
      setConditionValue(String(trigger.conditions.turns));
    }
    
    setEditingIndex(index);
    setShowAddForm(true);
  };
  
  const handleSubmit = () => {
    if (!formData.name.trim()) return;
    
    // Build conditions
    let conditions: Record<string, unknown> = {};
    
    switch (formData.trigger_type) {
      case 'keyword':
        conditions = { keywords: conditionValue.split(',').map(k => k.trim()).filter(Boolean) };
        break;
      case 'affection':
      case 'trust':
        conditions = { min: parseInt(conditionValue) || 0 };
        break;
      case 'time':
        conditions = { turns: parseInt(conditionValue) || 5 };
        break;
      case 'emotion':
        conditions = { emotion: conditionValue || 'happy' };
        break;
      default:
        conditions = formData.conditions;
    }
    
    const trigger = {
      ...formData,
      trigger_id: formData.trigger_id || `trigger_${Date.now()}`,
      conditions,
    };
    
    if (editingIndex !== null) {
      onUpdate(editingIndex, trigger);
    } else {
      onAdd(trigger);
    }
    
    resetForm();
  };
  
  const getTriggerTypeLabel = (type: string) => {
    return TRIGGER_TYPES.find(t => t.value === type)?.label || type;
  };
  
  const getConditionDisplay = (trigger: ScriptTrigger) => {
    switch (trigger.trigger_type) {
      case 'keyword':
        return `Keywords: ${(trigger.conditions.keywords as string[])?.join(', ') || 'None'}`;
      case 'affection':
        return `Affection >= ${trigger.conditions.min || 0}`;
      case 'trust':
        return `Trust >= ${trigger.conditions.min || 0}`;
      case 'time':
        return `${trigger.conditions.turns || 0} turns later`;
      case 'emotion':
        return `Emotion: ${trigger.conditions.emotion || 'None'}`;
      default:
        return JSON.stringify(trigger.conditions);
    }
  };
  
  return (
    <div className="space-y-4">
      {/* Trigger list */}
      <div className="space-y-3">
        {triggers.map((trigger, index) => (
          <Card key={trigger.trigger_id} className="p-4 bg-gray-800/50">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-white font-semibold">{trigger.name}</h3>
                  {trigger.one_time && (
                    <span className="px-2 py-0.5 bg-yellow-600/30 text-yellow-300 text-xs rounded">
                      One-time
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  <span className="px-2 py-1 bg-purple-600/30 text-purple-300 text-xs rounded">
                    {getTriggerTypeLabel(trigger.trigger_type)}
                  </span>
                  <span className="px-2 py-1 bg-blue-600/30 text-blue-300 text-xs rounded">
                    {getConditionDisplay(trigger)}
                  </span>
                  {trigger.target_scene_id && (
                    <span className="px-2 py-1 bg-green-600/30 text-green-300 text-xs rounded">
                      {'-> '} {scenes.find(s => s.scene_id === trigger.target_scene_id)?.name || trigger.target_scene_id}
                    </span>
                  )}
                </div>
                {trigger.description && (
                  <p className="text-gray-400 text-sm mt-2">{trigger.description}</p>
                )}
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => handleEdit(index)}>
                  Edit
                </Button>
                <Button size="sm" variant="danger" onClick={() => onRemove(index)}>
                  Delete
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
      
      {/* Add/Edit form */}
      {showAddForm ? (
        <Card className="p-6 bg-gray-800/50">
          <h3 className="text-lg font-semibold text-white mb-4">
            {editingIndex !== null ? 'Edit Trigger' : 'Add trigger'}
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Trigger Name *</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g. unlock private dialogue"
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1">Trigger type</label>
              <select
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                value={formData.trigger_type}
                onChange={(e) => {
                  setFormData(prev => ({ ...prev, trigger_type: e.target.value }));
                  setConditionValue('');
                }}
              >
                {TRIGGER_TYPES.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
              <p className="text-gray-500 text-xs mt-1">
                {TRIGGER_TYPES.find(t => t.value === formData.trigger_type)?.description}
              </p>
            </div>
            
            {/* Condition input */}
            <div>
              <label className="block text-sm text-gray-400 mb-1">
                {formData.trigger_type === 'keyword' && 'Trigger keywords (comma-separated)'}
                {['affection', 'trust'].includes(formData.trigger_type) && 'Minimum value'}
                {formData.trigger_type === 'time' && 'Turn count'}
                {formData.trigger_type === 'emotion' && 'Target emotion'}
              </label>
              <Input
                value={conditionValue}
                onChange={(e) => setConditionValue(e.target.value)}
                placeholder={
                  formData.trigger_type === 'keyword' ? 'e.g. like, love, together' :
                  ['affection', 'trust'].includes(formData.trigger_type) ? 'e.g. 50' :
                  formData.trigger_type === 'time' ? 'e.g. 50' :
                  formData.trigger_type === 'emotion' ? 'e.g. happy, sad, angry' :
                  'Enter condition value'
                }
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1">Target Scene (optional)</label>
              <select
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                value={formData.target_scene_id || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, target_scene_id: e.target.value }))}
              >
                <option value="">Do not switch scene</option>
                {scenes.map(s => (
                  <option key={s.scene_id} value={s.scene_id}>{s.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1">Description (optional)</label>
              <Input
                value={formData.description || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Trigger description..."
              />
            </div>
            
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="one_time"
                checked={formData.one_time || false}
                onChange={(e) => setFormData(prev => ({ ...prev, one_time: e.target.checked }))}
                className="rounded bg-gray-700 border-gray-600"
              />
              <label htmlFor="one_time" className="text-gray-400 text-sm">
                One-time trigger (does not repeat after firing)
              </label>
            </div>
            
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={resetForm}>
                Cancel
              </Button>
              <Button onClick={handleSubmit}>
                {editingIndex !== null ? 'Update trigger' : 'Add trigger'}
              </Button>
            </div>
          </div>
        </Card>
      ) : (
        <Button onClick={() => setShowAddForm(true)} className="w-full">
          + Add trigger
        </Button>
      )}
    </div>
  );
};











