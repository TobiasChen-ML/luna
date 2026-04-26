/**
 * Script Editor - Main Component
 * 
 * v3.1 features:
 * - Script basic info editing
 * - Scene list management
 * - NPC configuration
 * - Trigger configuration
 * - DAG visual editor
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Card } from '../common/Card';
import { SceneEditor } from './SceneEditor';
import { NPCEditor } from './NPCEditor';
import { TriggerEditor } from './TriggerEditor';
import { DagEditor } from './DagEditor';
import { scriptService } from '@/services/scriptService';
import type { ScriptNode, ScriptNodeCreate } from '@/services/scriptService';

// Type definitions
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
  description: string;
  role: string;
  voice_type: string;
  personality_brief: string;
}

interface ScriptTrigger {
  trigger_id: string;
  name: string;
  trigger_type: string;
  conditions: Record<string, unknown>;
  target_scene_id?: string;
}

interface ScriptData {
  [key: string]: unknown;
  id?: string;
  title: string;
  description: string;
  genre: string;
  character_id: string;
  world_setting: string;
  user_role: string;
  user_role_description: string;
  opening_line: string;
  scenes: SceneConfig[];
  npcs: NPCConfig[];
  triggers: ScriptTrigger[];
  start_scene_id?: string;
  tags: string[];
}

interface ScriptEditorProps {
  characterId: string;
  initialData?: Partial<ScriptData>;
  onSave: (data: ScriptData) => Promise<{ id?: string } | void>;
  onCancel: () => void;
}

const GENRES = [
  { value: 'romance', label: 'Romance' },
  { value: 'adventure', label: 'Adventure' },
  { value: 'mystery', label: 'Mystery' },
  { value: 'slice_of_life', label: 'Slice of Life' },
  { value: 'fantasy', label: 'Fantasy' },
  { value: 'sci_fi', label: 'Sci-Fi' },
  { value: 'drama', label: 'Drama' },
  { value: 'comedy', label: 'Comedy' },
];

export const ScriptEditor: React.FC<ScriptEditorProps> = ({
  characterId,
  initialData,
  onSave,
  onCancel,
}) => {
  const [activeTab, setActiveTab] = useState<'basic' | 'scenes' | 'npcs' | 'triggers' | 'dag'>('basic');
  const [scriptId, setScriptId] = useState<string | null>(
    typeof initialData?.id === 'string' ? initialData.id : null
  );
  const [dagNodes, setDagNodes] = useState<ScriptNode[]>([]);
  
  const [scriptData, setScriptData] = useState<ScriptData>({
    title: initialData?.title || '',
    description: initialData?.description || '',
    genre: initialData?.genre || 'romance',
    character_id: characterId,
    world_setting: initialData?.world_setting || '',
    user_role: initialData?.user_role || '',
    user_role_description: initialData?.user_role_description || '',
    opening_line: initialData?.opening_line || '',
    scenes: initialData?.scenes || [],
    npcs: initialData?.npcs || [],
    triggers: initialData?.triggers || [],
    start_scene_id: initialData?.start_scene_id,
    tags: initialData?.tags || [],
  });
  
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (scriptId) {
      loadDagNodes();
    }
  }, [scriptId]);
  
  const loadDagNodes = async () => {
    if (!scriptId) return;
    try {
      const script = await scriptService.getScript(scriptId);
      setDagNodes(script.nodes || []);
    } catch (err) {
      console.error('Failed to load DAG nodes:', err);
    }
  };
  
  // Update basic info
  const updateField = useCallback((field: keyof ScriptData, value: unknown) => {
    setScriptData(prev => ({ ...prev, [field]: value }));
  }, []);
  
  // Add scene
  const addScene = useCallback((scene: SceneConfig) => {
    setScriptData(prev => ({
      ...prev,
      scenes: [...prev.scenes, scene],
    }));
  }, []);
  
  // Update scene
  const updateScene = useCallback((index: number, scene: SceneConfig) => {
    setScriptData(prev => ({
      ...prev,
      scenes: prev.scenes.map((s, i) => i === index ? scene : s),
    }));
  }, []);
  
  // Delete scene
  const removeScene = useCallback((index: number) => {
    setScriptData(prev => ({
      ...prev,
      scenes: prev.scenes.filter((_, i) => i !== index),
    }));
  }, []);
  
  // Add NPC
  const addNPC = useCallback((npc: NPCConfig) => {
    setScriptData(prev => ({
      ...prev,
      npcs: [...prev.npcs, npc],
    }));
  }, []);
  
  // Update NPC
  const updateNPC = useCallback((index: number, npc: NPCConfig) => {
    setScriptData(prev => ({
      ...prev,
      npcs: prev.npcs.map((n, i) => i === index ? npc : n),
    }));
  }, []);
  
  // Delete NPC
  const removeNPC = useCallback((index: number) => {
    setScriptData(prev => ({
      ...prev,
      npcs: prev.npcs.filter((_, i) => i !== index),
    }));
  }, []);
  
  // Add trigger
  const addTrigger = useCallback((trigger: ScriptTrigger) => {
    setScriptData(prev => ({
      ...prev,
      triggers: [...prev.triggers, trigger],
    }));
  }, []);
  
  // Update trigger
  const updateTrigger = useCallback((index: number, trigger: ScriptTrigger) => {
    setScriptData(prev => ({
      ...prev,
      triggers: prev.triggers.map((t, i) => i === index ? trigger : t),
    }));
  }, []);
  
  // Delete trigger
  const removeTrigger = useCallback((index: number) => {
    setScriptData(prev => ({
      ...prev,
      triggers: prev.triggers.filter((_, i) => i !== index),
    }));
  }, []);
  
  const handleSave = async () => {
    if (!scriptData.title.trim()) {
      setError('Please enter a script title');
      return;
    }
    
    setSaving(true);
    setError(null);
    
    try {
      const result = await onSave(scriptData);
      if (result?.id) {
        setScriptId(result.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };
  
  const handleDagNodesChange = useCallback((nodes: ScriptNode[]) => {
    setDagNodes(nodes);
  }, []);
  
  const handleNodeCreate = useCallback(async (node: ScriptNodeCreate): Promise<ScriptNode> => {
    if (!scriptId) {
      throw new Error('Script must be saved first');
    }
    const created = await scriptService.createNode({ ...node, script_id: scriptId });
    loadDagNodes();
    return created;
  }, [scriptId]);
  
  const handleNodeUpdate = useCallback(async (nodeId: string, data: Partial<ScriptNode>) => {
    if (!scriptId) return;
    await scriptService.updateNode(nodeId, { ...data, script_id: scriptId });
  }, [scriptId]);
  
  const handleNodeDelete = useCallback(async (nodeId: string) => {
    if (!scriptId) return;
    await scriptService.deleteNode(nodeId, scriptId);
    loadDagNodes();
  }, [scriptId]);
  
  return (
    <div className="script-editor max-w-4xl mx-auto p-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white">
          {initialData ? 'Edit Script' : 'Create New Script'}
        </h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save script'}
          </Button>
        </div>
      </div>
      
      {/* Error message */}
      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-300 px-4 py-2 rounded mb-4">
          {error}
        </div>
      )}
      
      {/* Tab navigation */}
      <div className="flex gap-1 mb-6 bg-gray-800 rounded-lg p-1">
        {[
          { key: 'basic', label: 'Basic Info' },
          { key: 'dag', label: `DAG (${dagNodes.length})` },
          { key: 'scenes', label: `Scenes (${scriptData.scenes.length})` },
          { key: 'npcs', label: `NPC (${scriptData.npcs.length})` },
          { key: 'triggers', label: `Triggers (${scriptData.triggers.length})` },
        ].map(tab => (
          <button
            key={tab.key}
            className={`flex-1 py-2 px-4 rounded-md transition-colors ${
              activeTab === tab.key
                ? 'bg-purple-600 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
            onClick={() => setActiveTab(tab.key as typeof activeTab)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Content area */}
      <div className="space-y-6">
        {/* Basic Info */}
        {activeTab === 'basic' && (
          <Card className="p-6 bg-gray-800/50">
            <h2 className="text-lg font-semibold text-white mb-4">Basic Info</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Script Title *</label>
                <Input
                  value={scriptData.title}
                  onChange={(e) => updateField('title', e.target.value)}
                  placeholder="Enter script title"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Script summary</label>
                <textarea
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white resize-none"
                  rows={3}
                  value={scriptData.description}
                  onChange={(e) => updateField('description', e.target.value)}
                  placeholder="Describe your script..."
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Genre</label>
                  <select
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                    value={scriptData.genre}
                    onChange={(e) => updateField('genre', e.target.value)}
                  >
                    {GENRES.map(g => (
                      <option key={g.value} value={g.value}>{g.label}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Start Scene</label>
                  <select
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                    value={scriptData.start_scene_id || ''}
                    onChange={(e) => updateField('start_scene_id', e.target.value)}
                  >
                    <option value="">Select start scene</option>
                    {scriptData.scenes.map(s => (
                      <option key={s.scene_id} value={s.scene_id}>{s.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">World setting</label>
                <textarea
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white resize-none"
                  rows={2}
                  value={scriptData.world_setting}
                  onChange={(e) => updateField('world_setting', e.target.value)}
                  placeholder="Describe the world background of the script..."
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">User Role</label>
                  <Input
                    value={scriptData.user_role}
                    onChange={(e) => updateField('user_role', e.target.value)}
                    placeholder="User identity in this script"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Role Description</label>
                  <Input
                    value={scriptData.user_role_description}
                    onChange={(e) => updateField('user_role_description', e.target.value)}
                    placeholder="Brief user role description"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Opening Line</label>
                <textarea
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white resize-none"
                  rows={3}
                  value={scriptData.opening_line}
                  onChange={(e) => updateField('opening_line', e.target.value)}
                  placeholder="The first line the character says at script start..."
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Tags</label>
                <Input
                  value={scriptData.tags.join(', ')}
                  onChange={(e) => updateField('tags', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
                  placeholder="Enter tags separated by commas"
                />
              </div>
            </div>
          </Card>
        )}
        
        {/* DAG Editor */}
        {activeTab === 'dag' && (
          <Card className="p-0 bg-gray-800/50 overflow-hidden h-[600px]">
            {scriptId ? (
              <DagEditor
                scriptId={scriptId}
                initialNodes={dagNodes}
                onNodesChange={handleDagNodesChange}
                onNodeCreate={handleNodeCreate}
                onNodeUpdate={handleNodeUpdate}
                onNodeDelete={handleNodeDelete}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400">
                <p>Save the script first to use the DAG editor</p>
              </div>
            )}
          </Card>
        )}
        
        {/* Scene Editor */}
        {activeTab === 'scenes' && (
          <SceneEditor
            scenes={scriptData.scenes}
            npcs={scriptData.npcs}
            onAdd={addScene}
            onUpdate={updateScene}
            onRemove={removeScene}
          />
        )}
        
        {/* NPC Editor */}
        {activeTab === 'npcs' && (
          <NPCEditor
            npcs={scriptData.npcs}
            onAdd={addNPC}
            onUpdate={updateNPC}
            onRemove={removeNPC}
          />
        )}
        
        {/* Trigger Editor */}
        {activeTab === 'triggers' && (
          <TriggerEditor
            triggers={scriptData.triggers}
            scenes={scriptData.scenes}
            onAdd={addTrigger}
            onUpdate={updateTrigger}
            onRemove={removeTrigger}
          />
        )}
      </div>
    </div>
  );
};




