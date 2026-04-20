/**
 * Memory Management Page
 * PRD v3 Section 8.3 - User-facing memory management UI
 * Updated with importance decay and global memory support
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, Brain, FileText, Globe, ArrowLeft, Plus, Sparkles } from 'lucide-react';
import { MainLayout } from '@/components/layout';
import { Container } from '@/components/layout/Container';
import { MemoryList, GlobalMemoryList, PromoteMemoryModal } from '@/components/memory/MemoryList';
import {
  getCharacterMemories,
  getGlobalMemories,
  getGlobalMemorySuggestions,
  getMemoryStats,
  type MemoryResponse,
  type GlobalMemory,
  type GlobalMemorySuggestion,
  type MemoryStats,
} from '@/services/memoryService';
import { Button } from '@/components/ui/button';

type TabType = 'character' | 'global' | 'suggestions';

export function MemoryManagementPage() {
  const { characterId } = useParams<{ characterId: string }>();
  const navigate = useNavigate();

  const [memories, setMemories] = useState<MemoryResponse | null>(null);
  const [globalMemories, setGlobalMemories] = useState<GlobalMemory[]>([]);
  const [suggestions, setSuggestions] = useState<GlobalMemorySuggestion[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<TabType>('character');
  const [showPromoteModal, setShowPromoteModal] = useState(false);

  useEffect(() => {
    loadData();
  }, [characterId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [globalData, statsData] = await Promise.all([
        getGlobalMemories(),
        getMemoryStats(),
      ]);
      
      setGlobalMemories(globalData.memories);
      setStats(statsData);

      if (characterId) {
        const data = await getCharacterMemories(characterId);
        setMemories(data);
      }

      try {
        const suggestionsData = await getGlobalMemorySuggestions();
        setSuggestions(suggestionsData.suggestions);
      } catch {
        // Suggestions endpoint may fail for new users
        setSuggestions([]);
      }
    } catch (err: unknown) {
      console.error('Failed to load memories:', err);
      setError('Failed to load memories. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { 
      id: 'character' as TabType, 
      label: 'Character Memories', 
      icon: Brain, 
      count: memories ? memories.semantic_facts.length + memories.working_memory.length : 0 
    },
    { 
      id: 'global' as TabType, 
      label: 'Global Preferences', 
      icon: Globe, 
      count: globalMemories.length,
    },
    { 
      id: 'suggestions' as TabType, 
      label: 'Suggestions', 
      icon: Sparkles, 
      count: suggestions.length,
    },
  ];

  return (
    <MainLayout>
      <Container className="py-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="mb-4 text-gray-400 hover:text-white"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="mb-2 text-3xl font-bold text-white">Memory Management</h1>
              <p className="text-gray-400">
                View and manage what your AI companions remember about you
              </p>
            </div>
            {stats && (
              <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
                <div className="text-sm text-gray-400">Total Memories</div>
                <div className="text-2xl font-bold text-white">{stats.total}</div>
                <div className="mt-2 flex gap-2 text-xs">
                  <span className="text-pink-400">Working: {stats.by_layer.working}</span>
                  <span className="text-purple-400">Episodic: {stats.by_layer.episodic}</span>
                  <span className="text-blue-400">Semantic: {stats.by_layer.semantic}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex min-h-[400px] items-center justify-center">
            <div className="text-center">
              <Loader2 className="mx-auto h-12 w-12 animate-spin text-pink-500" />
              <p className="mt-4 text-gray-400">Loading memories...</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="rounded-lg border border-red-900 bg-red-950/20 p-6">
            <p className="text-red-400">{error}</p>
            <Button onClick={loadData} className="mt-4">
              Try Again
            </Button>
          </div>
        )}

        {/* Content */}
        {!loading && !error && (
          <>
            {/* Tab Navigation */}
            <div className="mb-6 flex space-x-2 border-b border-zinc-800">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setSelectedTab(tab.id)}
                    className={`flex items-center space-x-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                      selectedTab === tab.id
                        ? 'border-pink-500 text-pink-500'
                        : 'border-transparent text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{tab.label}</span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        selectedTab === tab.id
                          ? 'bg-pink-500/20 text-pink-400'
                          : 'bg-zinc-800 text-gray-400'
                      }`}
                    >
                      {tab.count}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Tab Content */}
            <div className="min-h-[400px]">
              {selectedTab === 'character' && memories && (
                <MemoryList
                  memories={memories}
                  onRefresh={loadData}
                />
              )}

              {selectedTab === 'global' && (
                <GlobalMemoryList
                  memories={globalMemories}
                  onRefresh={loadData}
                />
              )}

              {selectedTab === 'suggestions' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <p className="text-gray-400">
                      Memories that appear across multiple characters can be promoted to global preferences
                    </p>
                  </div>
                  
                  {suggestions.length === 0 ? (
                    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-8 text-center">
                      <Sparkles className="mx-auto h-12 w-12 text-gray-600" />
                      <p className="mt-4 text-gray-400">No suggestions yet. Keep chatting to build memories!</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {suggestions.map((suggestion, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 p-4"
                        >
                          <div className="flex-1">
                            <p className="text-white">{suggestion.content}</p>
                            <div className="mt-2 flex gap-4 text-xs text-gray-400">
                              <span>Category: {suggestion.category}</span>
                              <span>Seen in {suggestion.occurrence_count} character(s)</span>
                              <span>Confidence: {(suggestion.suggested_confidence * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                          <Button
                            size="sm"
                            onClick={() => setShowPromoteModal(true)}
                          >
                            <Plus className="mr-1 h-4 w-4" />
                            Promote
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Episodic Summary */}
            {selectedTab === 'character' && memories?.episodic_summary && (
              <div className="mt-8 rounded-lg border border-zinc-800 bg-zinc-900 p-6">
                <h3 className="mb-3 text-lg font-semibold text-white">Recent Episode Summary</h3>
                <p className="text-gray-300">{memories.episodic_summary}</p>
              </div>
            )}
          </>
        )}

        {/* Promote Modal */}
        {showPromoteModal && (
          <PromoteMemoryModal
            suggestions={suggestions}
            onClose={() => setShowPromoteModal(false)}
            onSuccess={() => {
              setShowPromoteModal(false);
              loadData();
            }}
          />
        )}
      </Container>
    </MainLayout>
  );
}
