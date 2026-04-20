/**
 * Memory List Components
 * Display and manage character and global memories
 */

import { useState } from 'react';
import { Edit, Trash2, Calendar, TrendingUp, Globe, Check, X, Clock } from 'lucide-react';
import type { 
  Memory, 
  GlobalMemory, 
  GlobalMemorySuggestion,
  MemoryResponse,
  MemoryLayerType,
  GlobalMemoryCategory 
} from '@/services/memoryService';
import { 
  forgetMemory, 
  correctMemory,
  deleteGlobalMemory,
  confirmGlobalMemory,
  promoteToGlobalMemory,
} from '@/services/memoryService';
import { Button } from '@/components/ui/button';

// ==================== Memory List (Character-specific) ====================

interface MemoryListProps {
  memories: MemoryResponse;
  onRefresh: () => void;
}

export function MemoryList({ memories, onRefresh }: MemoryListProps) {
  const [editingMemory, setEditingMemory] = useState<Memory | null>(null);
  const [editContent, setEditContent] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (memoryId: string) => {
    if (!confirm('Are you sure you want to forget this memory?')) return;

    setDeletingId(memoryId);
    try {
      await forgetMemory(memories.character_id, [memoryId]);
      onRefresh();
    } catch (error) {
      console.error('Failed to delete memory:', error);
      alert('Failed to delete memory. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleCorrect = async () => {
    if (!editingMemory || !editContent.trim()) return;
    
    try {
      await correctMemory(memories.character_id, editingMemory.id, editContent);
      setEditingMemory(null);
      setEditContent('');
      onRefresh();
    } catch (error) {
      console.error('Failed to correct memory:', error);
      alert('Failed to update memory. Please try again.');
    }
  };

  const formatImportanceBar = (importance: number, decayed: number) => {
    const percentage = (decayed / 10) * 100;
    const color = percentage > 60 ? 'bg-green-500' : percentage > 30 ? 'bg-yellow-500' : 'bg-red-500';
    return (
      <div className="flex items-center gap-2">
        <div className="h-2 w-16 overflow-hidden rounded-full bg-zinc-700">
          <div className={`h-full ${color}`} style={{ width: `${percentage}%` }} />
        </div>
        <span className="text-xs text-gray-400">{decayed.toFixed(1)}/10</span>
      </div>
    );
  };

  if (!memories.semantic_facts.length && !memories.working_memory.length) {
    return (
      <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-8 text-center">
        <p className="text-gray-400">No memories stored yet. Start chatting to build memories!</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Semantic Facts */}
      {memories.semantic_facts.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
            <TrendingUp className="h-5 w-5 text-pink-400" />
            Semantic Facts
            <span className="rounded-full bg-pink-500/20 px-2 py-0.5 text-xs text-pink-400">
              {memories.semantic_facts.length}
            </span>
          </h3>
          <div className="space-y-2">
            {memories.semantic_facts.map((fact, index) => (
              <div
                key={index}
                className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3"
              >
                <span className="text-gray-300">{fact}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Working Memory */}
      {memories.working_memory.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
            <Clock className="h-5 w-5 text-purple-400" />
            Recent Context (Working Memory)
            <span className="rounded-full bg-purple-500/20 px-2 py-0.5 text-xs text-purple-400">
              {memories.working_memory.length}
            </span>
          </h3>
          <div className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-zinc-800">
                <thead className="bg-zinc-800/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-300">
                      Content
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-300">
                      Layer
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-300">
                      Importance
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-300">
                      Created
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-300">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {memories.working_memory.map((memory) => (
                    <tr key={memory.id} className="hover:bg-zinc-800/30">
                      <td className="px-4 py-3 text-sm text-white">
                        {editingMemory?.id === memory.id ? (
                          <input
                            type="text"
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                            className="w-full rounded border border-zinc-700 bg-zinc-800 px-2 py-1 text-white"
                            autoFocus
                          />
                        ) : (
                          <div className="max-w-md">{memory.content}</div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`rounded-full px-2 py-1 text-xs font-medium ${
                          memory.layer === 'working' ? 'bg-purple-500/10 text-purple-400' :
                          memory.layer === 'semantic' ? 'bg-pink-500/10 text-pink-400' :
                          'bg-blue-500/10 text-blue-400'
                        }`}>
                          {memory.layer}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {formatImportanceBar(memory.importance, memory.decayed_importance)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-400">
                        {memory.created_at ? new Date(memory.created_at).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-right text-sm">
                        <div className="flex justify-end gap-2">
                          {editingMemory?.id === memory.id ? (
                            <>
                              <button
                                onClick={handleCorrect}
                                className="rounded-lg p-1.5 text-green-400 hover:bg-zinc-800"
                              >
                                <Check className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => {
                                  setEditingMemory(null);
                                  setEditContent('');
                                }}
                                className="rounded-lg p-1.5 text-gray-400 hover:bg-zinc-800"
                              >
                                <X className="h-4 w-4" />
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => {
                                  setEditingMemory(memory);
                                  setEditContent(memory.content);
                                }}
                                className="rounded-lg p-1.5 text-gray-400 hover:bg-zinc-800 hover:text-pink-400"
                                title="Edit"
                              >
                                <Edit className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => handleDelete(memory.id)}
                                disabled={deletingId === memory.id}
                                className="rounded-lg p-1.5 text-gray-400 hover:bg-zinc-800 hover:text-red-400 disabled:opacity-50"
                                title="Forget"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Global Memories Section */}
      {memories.global_memories.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
            <Globe className="h-5 w-5 text-blue-400" />
            Global Preferences (Shared Across Characters)
            <span className="rounded-full bg-blue-500/20 px-2 py-0.5 text-xs text-blue-400">
              {memories.global_memories.length}
            </span>
          </h3>
          <div className="space-y-2">
            {memories.global_memories.map((memory) => (
              <div
                key={memory.id}
                className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3"
              >
                <div className="flex-1">
                  <p className="text-white">{memory.content}</p>
                  <div className="mt-1 flex gap-4 text-xs text-gray-400">
                    <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-blue-400">
                      {memory.category}
                    </span>
                    <span>Used {memory.reference_count} time(s)</span>
                  </div>
                </div>
                {!memory.is_confirmed && (
                  <span className="rounded-full bg-yellow-500/10 px-2 py-1 text-xs text-yellow-400">
                    Unconfirmed
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== Global Memory List ====================

interface GlobalMemoryListProps {
  memories: GlobalMemory[];
  onRefresh: () => void;
}

export function GlobalMemoryList({ memories, onRefresh }: GlobalMemoryListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);

  const handleDelete = async (memoryId: string) => {
    if (!confirm('Are you sure you want to delete this global preference?')) return;

    setDeletingId(memoryId);
    try {
      await deleteGlobalMemory(memoryId);
      onRefresh();
    } catch (error) {
      console.error('Failed to delete global memory:', error);
      alert('Failed to delete. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleConfirm = async (memoryId: string) => {
    setConfirmingId(memoryId);
    try {
      await confirmGlobalMemory(memoryId);
      onRefresh();
    } catch (error) {
      console.error('Failed to confirm global memory:', error);
      alert('Failed to confirm. Please try again.');
    } finally {
      setConfirmingId(null);
    }
  };

  const getCategoryColor = (category: GlobalMemoryCategory) => {
    switch (category) {
      case 'preference': return 'bg-green-500/10 text-green-400';
      case 'fact': return 'bg-blue-500/10 text-blue-400';
      case 'dislike': return 'bg-red-500/10 text-red-400';
      case 'interest': return 'bg-purple-500/10 text-purple-400';
      case 'relationship': return 'bg-pink-500/10 text-pink-400';
      default: return 'bg-gray-500/10 text-gray-400';
    }
  };

  if (memories.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-8 text-center">
        <Globe className="mx-auto h-12 w-12 text-gray-600" />
        <p className="mt-4 text-gray-400">
          No global preferences set. Global preferences are shared across all your AI companions.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-800">
          <thead className="bg-zinc-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-300">
                Content
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-300">
                Category
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-300">
                Confidence
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-300">
                Usage
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-300">
                Status
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-300">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {memories.map((memory) => (
              <tr key={memory.id} className="hover:bg-zinc-800/30">
                <td className="px-4 py-3 text-sm text-white">
                  <div className="max-w-md">{memory.content}</div>
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className={`rounded-full px-2 py-1 text-xs font-medium ${getCategoryColor(memory.category)}`}>
                    {memory.category}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-16 overflow-hidden rounded-full bg-zinc-700">
                      <div
                        className="h-full bg-gradient-to-r from-green-500 to-blue-500"
                        style={{ width: `${memory.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-400">{(memory.confidence * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-gray-400">
                  {memory.reference_count} time(s)
                </td>
                <td className="px-4 py-3 text-sm">
                  {memory.is_confirmed ? (
                    <span className="rounded-full bg-green-500/10 px-2 py-1 text-xs text-green-400">
                      Confirmed
                    </span>
                  ) : (
                    <span className="rounded-full bg-yellow-500/10 px-2 py-1 text-xs text-yellow-400">
                      Pending
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right text-sm">
                  <div className="flex justify-end gap-2">
                    {!memory.is_confirmed && (
                      <button
                        onClick={() => handleConfirm(memory.id)}
                        disabled={confirmingId === memory.id}
                        className="rounded-lg p-1.5 text-gray-400 hover:bg-zinc-800 hover:text-green-400 disabled:opacity-50"
                        title="Confirm"
                      >
                        <Check className="h-4 w-4" />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(memory.id)}
                      disabled={deletingId === memory.id}
                      className="rounded-lg p-1.5 text-gray-400 hover:bg-zinc-800 hover:text-red-400 disabled:opacity-50"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ==================== Promote Memory Modal ====================

interface PromoteMemoryModalProps {
  suggestions: GlobalMemorySuggestion[];
  onClose: () => void;
  onSuccess: () => void;
}

export function PromoteMemoryModal({ suggestions, onClose, onSuccess }: PromoteMemoryModalProps) {
  const [selectedCategory, setSelectedCategory] = useState<GlobalMemoryCategory>('preference');
  const [promoting, setPromoting] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const currentSuggestion = suggestions[selectedIndex];

  const handlePromote = async () => {
    if (!currentSuggestion) return;

    setPromoting(true);
    try {
      await promoteToGlobalMemory(currentSuggestion.source_character_id, selectedCategory);
      onSuccess();
    } catch (error) {
      console.error('Failed to promote memory:', error);
      alert('Failed to promote. Please try again.');
    } finally {
      setPromoting(false);
    }
  };

  if (!currentSuggestion) {
    onClose();
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border border-zinc-800 bg-zinc-900 p-6">
        <h2 className="mb-4 text-xl font-semibold text-white">Promote to Global Preference?</h2>
        
        <p className="mb-4 text-gray-300">{currentSuggestion.content}</p>

        <div className="mb-4">
          <label className="mb-2 block text-sm text-gray-400">Category</label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value as GlobalMemoryCategory)}
            className="w-full rounded border border-zinc-700 bg-zinc-800 px-3 py-2 text-white"
          >
            <option value="preference">Preference</option>
            <option value="fact">Fact</option>
            <option value="dislike">Dislike</option>
            <option value="interest">Interest</option>
            <option value="relationship">Relationship</option>
          </select>
        </div>

        <div className="mb-6 rounded-lg bg-zinc-800 p-3 text-sm text-gray-400">
          <p>This preference will be shared across all your AI companions.</p>
        </div>

        <div className="flex gap-3">
          <Button variant="outline" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button onClick={handlePromote} disabled={promoting} className="flex-1">
            {promoting ? 'Promoting...' : 'Promote'}
          </Button>
        </div>
      </div>
    </div>
  );
}
