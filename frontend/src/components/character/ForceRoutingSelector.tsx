/**
 * Force Character Routing Selector (PRD v2026.02)
 *
 * Allows users to select or create force routing instructions
 * to prevent character personality drift in conversations.
 */
import { useState, useEffect } from 'react';
import { Button, Card } from '@/components/common';
import { Lock, Edit3, Check, X } from 'lucide-react';
import { api } from '@/services/api';
import type { ForceRoutingTemplate } from '@/types';

interface ForceRoutingSelectorProps {
  currentInstruction?: string;
  onSelect: (instruction: string, templateId?: string) => void;
  showCustomInput?: boolean;
  className?: string;
}

export function ForceRoutingSelector({
  currentInstruction = '',
  onSelect,
  showCustomInput = true,
  className = '',
}: ForceRoutingSelectorProps) {
  const [templates, setTemplates] = useState<ForceRoutingTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [customMode, setCustomMode] = useState(false);
  const [customText, setCustomText] = useState(currentInstruction);
  const [error, setError] = useState('');

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await api.get('/characters/force-routing/templates');
      if (response.data.success) {
        setTemplates(response.data.templates);
      }
    } catch (err) {
      console.error('Failed to load force routing templates:', err);
      setError('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateSelect = (template: ForceRoutingTemplate) => {
    setSelectedTemplateId(template.id);
    setCustomMode(false);
    onSelect(template.instruction, template.id);
  };

  const handleCustomSubmit = () => {
    if (!customText.trim()) {
      setError('Custom instruction cannot be empty');
      return;
    }
    setSelectedTemplateId(null);
    onSelect(customText.trim());
    setError('');
  };

  const handleCustomCancel = () => {
    setCustomMode(false);
    setCustomText(currentInstruction);
    setError('');
  };

  if (loading) {
    return (
      <div className="text-center py-4">
        <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-zinc-400 mt-2">Loading templates...</p>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start gap-3">
          <Lock className="w-5 h-5 text-primary-400 mt-1 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white">Force Character Routing</h3>
            <p className="text-sm text-zinc-400 mt-1">
              Select a personality template to prevent character drift. This instruction
              will be enforced at all times and cannot be overridden.
            </p>
          </div>
        </div>

        {/* Templates Grid */}
        {!customMode && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {templates.map((template) => (
              <button
                key={template.id}
                onClick={() => handleTemplateSelect(template)}
                className={`relative p-4 rounded-lg border-2 transition-all text-left ${
                  selectedTemplateId === template.id
                    ? 'border-primary-500 bg-primary-500/10'
                    : 'border-zinc-700 bg-zinc-800/50 hover:border-zinc-600'
                }`}
              >
                {selectedTemplateId === template.id && (
                  <div className="absolute top-2 right-2">
                    <Check className="w-5 h-5 text-primary-400" />
                  </div>
                )}
                <div className="font-semibold text-white mb-1">{template.name}</div>
                <div className="text-xs text-zinc-400">{template.description}</div>
              </button>
            ))}
          </div>
        )}

        {/* Custom Instruction */}
        {showCustomInput && (
          <div className="space-y-3">
            {!customMode ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCustomMode(true)}
                className="flex items-center gap-2"
              >
                <Edit3 size={16} />
                Write Custom Instruction
              </Button>
            ) : (
              <Card className="space-y-3">
                <label className="block">
                  <span className="text-sm font-medium text-white">Custom Instruction</span>
                  <textarea
                    value={customText}
                    onChange={(e) => setCustomText(e.target.value)}
                    placeholder="E.g., You MUST always be playful and teasing..."
                    className="w-full mt-2 px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:border-primary-500 focus:outline-none resize-none"
                    rows={4}
                  />
                </label>
                {error && <p className="text-sm text-red-400">{error}</p>}
                <div className="flex gap-2">
                  <Button onClick={handleCustomSubmit} size="sm" className="flex items-center gap-2">
                    <Check size={16} />
                    Apply Custom
                  </Button>
                  <Button
                    onClick={handleCustomCancel}
                    variant="ghost"
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    <X size={16} />
                    Cancel
                  </Button>
                </div>
              </Card>
            )}
          </div>
        )}

        {/* Current Selection Display */}
        {!customMode && selectedTemplateId && (
          <Card className="bg-primary-500/5 border-primary-500/20">
            <div className="text-sm">
              <span className="text-zinc-400">Selected: </span>
              <span className="text-white font-medium">
                {templates.find((t) => t.id === selectedTemplateId)?.name}
              </span>
            </div>
            <div className="text-xs text-zinc-500 mt-2 italic">
              {templates.find((t) => t.id === selectedTemplateId)?.instruction}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
