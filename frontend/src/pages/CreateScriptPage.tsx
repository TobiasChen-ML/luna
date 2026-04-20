/**
 * Create Script Page
 * 
 * v3.1 features:
 * - Create from template
 * - Full custom creation
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { ScriptEditor } from '../components/script/ScriptEditor';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { scriptService } from '../services/scriptService';
import { ugcService } from '../services/ugcService';

export const CreateScriptPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const characterId = searchParams.get('character');
  const templateId = searchParams.get('template');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialData, setInitialData] = useState<Record<string, unknown> | undefined>();
  
  // If there is a template ID, load template data
  useEffect(() => {
    if (templateId) {
      loadTemplate();
    }
  }, [templateId]);
  
  const loadTemplate = async () => {
    setLoading(true);
    try {
      const { templates } = await ugcService.getTemplates();
      const template = templates.find(t => t.id === templateId);
      
      if (template) {
        setInitialData({
          title: template.name,
          description: template.description,
          genre: template.genre,
          world_setting: template.world_setting,
        });
      }
    } catch (err) {
      console.error('Failed to load template:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSave = async (data: Record<string, unknown>) => {
    setError(null);
    
    if (!characterId) {
      setError('Please select a character first');
      return;
    }
    
    try {
      const script = await scriptService.createScript({
        ...data,
        character_id: characterId,
      } as never);
      
      // Navigate to script details or edit page
      navigate(`/scripts/${script.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Creation failed');
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
  
  if (!characterId) {
    return (
      <MainLayout>
        <div className="max-w-2xl mx-auto px-4 py-16 text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Choose Character</h1>
          <p className="text-gray-400 mb-8">Please select a character before creating a script</p>
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
      {error && (
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="bg-red-500/20 border border-red-500 text-red-300 px-4 py-2 rounded">
            {error}
          </div>
        </div>
      )}
      
      <ScriptEditor
        characterId={characterId}
        initialData={initialData}
        onSave={handleSave}
        onCancel={handleCancel}
      />
    </MainLayout>
  );
};

export default CreateScriptPage;

