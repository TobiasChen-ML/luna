/**
 * Memory Edit Modal Component
 * Allows users to edit/correct a fact
 */

import { useState } from 'react';
import type { ChangeEvent } from 'react';
import { X } from 'lucide-react';
import type { FactSummary } from '@/services/memoryService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface MemoryEditModalProps {
  fact: FactSummary;
  onSave: (newContent: string, category?: string) => Promise<void>;
  onClose: () => void;
}

export function MemoryEditModal({ fact, onSave, onClose }: MemoryEditModalProps) {
  const [newContent, setNewContent] = useState(fact.content);
  const [category, setCategory] = useState(fact.category);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!newContent.trim()) return;

    setSaving(true);
    try {
      await onSave(newContent, category);
      onClose();
    } catch (error) {
      console.error('Failed to save fact:', error);
      alert('Failed to update fact. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="relative w-full max-w-md rounded-lg bg-zinc-900 p-6 shadow-xl">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">Edit Memory</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-gray-400 hover:bg-zinc-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-300">
              Fact Content
            </label>
            <textarea
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              rows={4}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-white placeholder-gray-500 focus:border-pink-500 focus:outline-none focus:ring-1 focus:ring-pink-500"
              placeholder="Enter corrected fact..."
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-300">
              Category
            </label>
            <Input
              value={category}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setCategory(e.target.value)}
              placeholder="e.g., personal_info, preferences, relationships"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 flex justify-end space-x-3">
          <Button variant="ghost" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving || !newContent.trim()}
            className="bg-pink-600 hover:bg-pink-700"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>
    </div>
  );
}
