/**
 * Script Preview Component
 * 
 * Preview script structure and flow
 */

import React from 'react';
import { Card } from '../common/Card';

interface SceneConfig {
  scene_id: string;
  name: string;
  description: string;
  atmosphere: string;
}

interface ScriptTrigger {
  trigger_id: string;
  name: string;
  trigger_type: string;
  target_scene_id?: string;
}

interface ScriptPreviewProps {
  title: string;
  description: string;
  genre: string;
  worldSetting: string;
  openingLine: string;
  scenes: SceneConfig[];
  triggers: ScriptTrigger[];
  startSceneId?: string;
}

export const ScriptPreview: React.FC<ScriptPreviewProps> = ({
  title,
  description,
  genre,
  worldSetting,
  openingLine,
  scenes,
  triggers,
  startSceneId,
}) => {
  return (
    <div className="script-preview space-y-6">
      {/* Title card */}
      <Card className="p-6 bg-gradient-to-br from-purple-900/50 to-pink-900/50 border-purple-500/30">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">{title || 'Untitled Script'}</h1>
            <p className="text-gray-300 mt-2">{description || 'No description yet'}</p>
          </div>
          <span className="px-3 py-1 bg-purple-600/50 text-purple-200 rounded-full text-sm">
            {genre}
          </span>
        </div>
        
        {worldSetting && (
          <div className="mt-4 p-3 bg-black/20 rounded-lg">
            <p className="text-gray-400 text-sm">World setting</p>
            <p className="text-gray-200">{worldSetting}</p>
          </div>
        )}
        
        {openingLine && (
          <div className="mt-4 p-3 bg-black/20 rounded-lg border-l-4 border-purple-500">
            <p className="text-gray-400 text-sm">Opening Line</p>
            <p className="text-white italic">"{openingLine}"</p>
          </div>
        )}
      </Card>
      
      {/* Scene flow diagram */}
      <Card className="p-6 bg-gray-800/50">
        <h2 className="text-lg font-semibold text-white mb-4">Scene Flow</h2>
        
        {scenes.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No scenes yet, please add scenes first</p>
        ) : (
          <div className="space-y-4">
            {scenes.map((scene, index) => {
              const isStart = scene.scene_id === startSceneId || (index === 0 && !startSceneId);
              const incomingTriggers = triggers.filter(t => t.target_scene_id === scene.scene_id);
              
              return (
                <div key={scene.scene_id} className="relative">
                  {/* Connector */}
                  {index > 0 && (
                    <div className="absolute left-6 -top-4 w-0.5 h-4 bg-gray-600" />
                  )}
                  
                  <div className={`flex items-start gap-4 p-4 rounded-lg ${
                    isStart ? 'bg-green-900/30 border border-green-500/30' : 'bg-gray-700/50'
                  }`}>
                    {/* Scene marker */}
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold ${
                      isStart ? 'bg-green-600' : 'bg-purple-600'
                    }`}>
                      {index + 1}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-white font-semibold">{scene.name}</h3>
                        {isStart && (
                          <span className="px-2 py-0.5 bg-green-600/50 text-green-200 text-xs rounded">
                            Start Scene
                          </span>
                        )}
                      </div>
                      <p className="text-gray-400 text-sm mt-1">{scene.description}</p>
                      
                      {/* Trigger entries */}
                      {incomingTriggers.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {incomingTriggers.map(trigger => (
                            <span
                              key={trigger.trigger_id}
                              className="px-2 py-1 bg-yellow-600/30 text-yellow-300 text-xs rounded flex items-center gap-1"
                            >
                              ← {trigger.name}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <span className="px-2 py-1 bg-blue-600/30 text-blue-300 text-xs rounded">
                      {scene.atmosphere}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>
      
      {/* Trigger list */}
      {triggers.length > 0 && (
        <Card className="p-6 bg-gray-800/50">
          <h2 className="text-lg font-semibold text-white mb-4">Triggers ({triggers.length})</h2>
          
          <div className="grid gap-3 md:grid-cols-2">
            {triggers.map(trigger => (
              <div
                key={trigger.trigger_id}
                className="p-3 bg-gray-700/50 rounded-lg flex items-center justify-between"
              >
                <div>
                  <p className="text-white text-sm">{trigger.name}</p>
                  <p className="text-gray-400 text-xs">{trigger.trigger_type}</p>
                </div>
                {trigger.target_scene_id && (
                  <span className="text-green-400 text-xs">
                    → {scenes.find(s => s.scene_id === trigger.target_scene_id)?.name || '?'}
                  </span>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
