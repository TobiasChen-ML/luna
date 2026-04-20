/**
 * Scene Editor
 * 
 * Edit scene configuration in script
 */

import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Card } from '../common/Card';

interface SceneConfig {
  scene_id: string;
  name: string;
  description: string;
  atmosphere: string;
  time_of_day: string;
  ambient_sounds: string[];
  available_npcs: string[];
}

interface NPCConfig {
  npc_id: string;
  name: string;
}

interface SceneEditorProps {
  scenes: SceneConfig[];
  npcs: NPCConfig[];
  onAdd: (scene: SceneConfig) => void;
  onUpdate: (index: number, scene: SceneConfig) => void;
  onRemove: (index: number) => void;
}

const ATMOSPHERES = [
  { value: 'peaceful', label: 'Peaceful' },
  { value: 'romantic', label: 'Romantic' },
  { value: 'tense', label: 'Tense' },
  { value: 'mysterious', label: 'Mysterious' },
  { value: 'exciting', label: 'Exciting' },
  { value: 'melancholic', label: 'Melancholic' },
  { value: 'cozy', label: 'Cozy' },
  { value: 'dangerous', label: 'Dangerous' },
];

const TIME_OF_DAY = [
  { value: 'morning', label: 'Morning' },
  { value: 'afternoon', label: 'Afternoon' },
  { value: 'evening', label: 'Evening' },
  { value: 'night', label: 'Night' },
  { value: 'late_night', label: 'Late Night' },
];

export const SceneEditor: React.FC<SceneEditorProps> = ({
  scenes,
  npcs,
  onAdd,
  onUpdate,
  onRemove,
}) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  
  const [formData, setFormData] = useState<SceneConfig>({
    scene_id: '',
    name: '',
    description: '',
    atmosphere: 'peaceful',
    time_of_day: 'afternoon',
    ambient_sounds: [],
    available_npcs: [],
  });
  
  const resetForm = () => {
    setFormData({
      scene_id: '',
      name: '',
      description: '',
      atmosphere: 'peaceful',
      time_of_day: 'afternoon',
      ambient_sounds: [],
      available_npcs: [],
    });
    setEditingIndex(null);
    setShowAddForm(false);
  };
  
  const handleEdit = (index: number) => {
    setFormData(scenes[index]);
    setEditingIndex(index);
    setShowAddForm(true);
  };
  
  const handleSubmit = () => {
    if (!formData.name.trim()) return;
    
    const scene = {
      ...formData,
      scene_id: formData.scene_id || `scene_${Date.now()}`,
    };
    
    if (editingIndex !== null) {
      onUpdate(editingIndex, scene);
    } else {
      onAdd(scene);
    }
    
    resetForm();
  };
  
  const toggleNPC = (npcId: string) => {
    setFormData(prev => ({
      ...prev,
      available_npcs: prev.available_npcs.includes(npcId)
        ? prev.available_npcs.filter(id => id !== npcId)
        : [...prev.available_npcs, npcId],
    }));
  };
  
  return (
    <div className="space-y-4">
      {/* Scene list */}
      <div className="grid gap-4">
        {scenes.map((scene, index) => (
          <Card key={scene.scene_id} className="p-4 bg-gray-800/50">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white">{scene.name}</h3>
                <p className="text-gray-400 text-sm mt-1">{scene.description}</p>
                <div className="flex gap-2 mt-2">
                  <span className="px-2 py-1 bg-purple-600/30 text-purple-300 text-xs rounded">
                    {ATMOSPHERES.find(a => a.value === scene.atmosphere)?.label || scene.atmosphere}
                  </span>
                  <span className="px-2 py-1 bg-blue-600/30 text-blue-300 text-xs rounded">
                    {TIME_OF_DAY.find(t => t.value === scene.time_of_day)?.label || scene.time_of_day}
                  </span>
                  {scene.available_npcs.length > 0 && (
                    <span className="px-2 py-1 bg-green-600/30 text-green-300 text-xs rounded">
                      {scene.available_npcs.length} NPC
                    </span>
                  )}
                </div>
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
            {editingIndex !== null ? 'Edit Scene' : 'Add scene'}
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Scene Name *</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g. coffee shop"
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1">Scene Description</label>
              <textarea
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white resize-none"
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe this scene..."
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Atmosphere</label>
                <select
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                  value={formData.atmosphere}
                  onChange={(e) => setFormData(prev => ({ ...prev, atmosphere: e.target.value }))}
                >
                  {ATMOSPHERES.map(a => (
                    <option key={a.value} value={a.value}>{a.label}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Time</label>
                <select
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                  value={formData.time_of_day}
                  onChange={(e) => setFormData(prev => ({ ...prev, time_of_day: e.target.value }))}
                >
                  {TIME_OF_DAY.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1">Ambient sounds</label>
              <Input
                value={formData.ambient_sounds.join(', ')}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  ambient_sounds: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                }))}
                placeholder="e.g. rain, coffee machine, soft music"
              />
            </div>
            
            {npcs.length > 0 && (
              <div>
                <label className="block text-sm text-gray-400 mb-1">Available NPCs</label>
                <div className="flex flex-wrap gap-2">
                  {npcs.map(npc => (
                    <button
                      key={npc.npc_id}
                      className={`px-3 py-1 rounded-full text-sm transition-colors ${
                        formData.available_npcs.includes(npc.npc_id)
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                      }`}
                      onClick={() => toggleNPC(npc.npc_id)}
                    >
                      {npc.name}
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={resetForm}>
                Cancel
              </Button>
              <Button onClick={handleSubmit}>
                {editingIndex !== null ? 'Update scene' : 'Add scene'}
              </Button>
            </div>
          </div>
        </Card>
      ) : (
        <Button onClick={() => setShowAddForm(true)} className="w-full">
          + Add scene
        </Button>
      )}
    </div>
  );
};




