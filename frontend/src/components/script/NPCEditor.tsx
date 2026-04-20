/**
 * NPC Editor
 * 
 * Edit NPC configuration in script
 */

import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Card } from '../common/Card';

interface NPCConfig {
  npc_id: string;
  name: string;
  description: string;
  role: string;
  voice_type: string;
  personality_brief: string;
}

interface NPCEditorProps {
  npcs: NPCConfig[];
  onAdd: (npc: NPCConfig) => void;
  onUpdate: (index: number, npc: NPCConfig) => void;
  onRemove: (index: number) => void;
}

const VOICE_TYPES = [
  { value: 'male_deep', label: 'Male - Deep' },
  { value: 'male_bright', label: 'Male - Bright' },
  { value: 'female_sweet', label: 'Female - Sweet' },
  { value: 'female_mature', label: 'Female - Mature' },
  { value: 'child', label: 'Child' },
  { value: 'elderly', label: 'Elderly' },
  { value: 'robotic', label: 'Robotic' },
];

export const NPCEditor: React.FC<NPCEditorProps> = ({
  npcs,
  onAdd,
  onUpdate,
  onRemove,
}) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  
  const [formData, setFormData] = useState<NPCConfig>({
    npc_id: '',
    name: '',
    description: '',
    role: '',
    voice_type: 'male_bright',
    personality_brief: '',
  });
  
  const resetForm = () => {
    setFormData({
      npc_id: '',
      name: '',
      description: '',
      role: '',
      voice_type: 'male_bright',
      personality_brief: '',
    });
    setEditingIndex(null);
    setShowAddForm(false);
  };
  
  const handleEdit = (index: number) => {
    setFormData(npcs[index]);
    setEditingIndex(index);
    setShowAddForm(true);
  };
  
  const handleSubmit = () => {
    if (!formData.name.trim()) return;
    
    const npc = {
      ...formData,
      npc_id: formData.npc_id || `npc_${Date.now()}`,
    };
    
    if (editingIndex !== null) {
      onUpdate(editingIndex, npc);
    } else {
      onAdd(npc);
    }
    
    resetForm();
  };
  
  return (
    <div className="space-y-4">
      {/* NPC List */}
      <div className="grid gap-4 md:grid-cols-2">
        {npcs.map((npc, index) => (
          <Card key={npc.npc_id} className="p-4 bg-gray-800/50">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
                    {npc.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">{npc.name}</h3>
                    <p className="text-gray-400 text-xs">{npc.role || 'NPC'}</p>
                  </div>
                </div>
                <p className="text-gray-400 text-sm mt-2 line-clamp-2">{npc.description}</p>
                <div className="flex gap-2 mt-2">
                  <span className="px-2 py-1 bg-blue-600/30 text-blue-300 text-xs rounded">
                    {VOICE_TYPES.find(v => v.value === npc.voice_type)?.label || npc.voice_type}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-3">
              <Button size="sm" variant="secondary" onClick={() => handleEdit(index)}>
                Edit
              </Button>
              <Button size="sm" variant="danger" onClick={() => onRemove(index)}>
                Delete
              </Button>
            </div>
          </Card>
        ))}
      </div>
      
      {/* Add/Edit form */}
      {showAddForm ? (
        <Card className="p-6 bg-gray-800/50">
          <h3 className="text-lg font-semibold text-white mb-4">
            {editingIndex !== null ? 'Edit NPC' : 'Add NPC'}
          </h3>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">NPC Name *</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g. bartender"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Role identity</label>
                <Input
                  value={formData.role}
                  onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                  placeholder="e.g. coffee shop owner"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1">Description</label>
              <textarea
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white resize-none"
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe this NPC's appearance..."
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1">Voice type</label>
              <select
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                value={formData.voice_type}
                onChange={(e) => setFormData(prev => ({ ...prev, voice_type: e.target.value }))}
              >
                {VOICE_TYPES.map(v => (
                  <option key={v.value} value={v.value}>{v.label}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1">Personality summary</label>
              <Input
                value={formData.personality_brief}
                onChange={(e) => setFormData(prev => ({ ...prev, personality_brief: e.target.value }))}
                placeholder="e.g. warm and outgoing, likes chatting"
              />
            </div>
            
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={resetForm}>
                Cancel
              </Button>
              <Button onClick={handleSubmit}>
                {editingIndex !== null ? 'Update NPC' : 'Add NPC'}
              </Button>
            </div>
          </div>
        </Card>
      ) : (
        <Button onClick={() => setShowAddForm(true)} className="w-full">
          + Add NPC
        </Button>
      )}
    </div>
  );
};






