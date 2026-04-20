/**
 * Edit Script Page
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { ScriptEditor } from '../components/script/ScriptEditor';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { scriptService, Script } from '../services/scriptService';

export const EditScriptPage: React.FC = () => {
  const navigate = useNavigate();
  const { scriptId } = useParams<{ scriptId: string }>();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [script, setScript] = useState<Script | null>(null);
  
  // Load script data
  useEffect(() => {
    if (scriptId) {
      loadScript();
    }
  }, [scriptId]);
  
  const loadScript = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await scriptService.getScript(scriptId!);
      setScript(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Load failed');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSave = async (data: Record<string, unknown>) => {
    setError(null);
    
    try {
      await scriptService.updateScript(scriptId!, data as never);
      navigate(`/scripts/${scriptId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
      throw err;
    }
  };
  
  const handleCancel = () => {
    navigate(-1);
  };
  
  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <LoadingSpinner size="lg" />
        </div>
      </MainLayout>
    );
  }
  
  if (error || !script) {
    return (
      <MainLayout>
        <div className="max-w-2xl mx-auto px-4 py-16 text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Load failed</h1>
          <p className="text-gray-400 mb-8">{error || 'Script not found'}</p>
          <button
            onClick={() => navigate('/creator-center')}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Back to Creator Center
          </button>
        </div>
      </MainLayout>
    );
  }
  
  return (
    <MainLayout>
      <ScriptEditor
        characterId={script.character_id}
        initialData={{
          title: script.title,
          description: script.description,
          genre: script.genre,
          world_setting: script.world_setting,
          user_role: script.user_role,
          user_role_description: script.user_role_description,
          opening_line: script.opening_line,
          scenes: script.scenes,
          npcs: script.npcs,
          triggers: script.triggers,
          start_scene_id: script.start_scene_id,
          tags: script.tags,
        }}
        onSave={handleSave}
        onCancel={handleCancel}
      />
    </MainLayout>
  );
};

export default EditScriptPage;
