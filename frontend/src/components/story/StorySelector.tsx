/**
 * StorySelector Component
 *
 * Modal for selecting and starting stories.
 * Shows available stories for the current character with progress indicators.
 * Supports replay with history tracking.
 */
import { useState, useEffect } from 'react';
import { BookOpen, CheckCircle, PlayCircle, X, Sparkles, RotateCcw, History, ChevronDown, ChevronUp } from 'lucide-react';
import { storyService } from '@/services/storyService';
import type { Story } from '@/types/story';

interface StorySelectorProps {
  characterId: string;
  sessionId: string | null;
  onSelectStory: (story: Story) => void;
  isOpen: boolean;
  onClose: () => void;
}

interface PlayHistoryEntry {
  play_id: string;
  play_index: number;
  status: string;
  ending_type: string | null;
  completion_time_minutes: number | null;
  started_at: string;
  completed_at: string | null;
  choices_count: number;
}

export function StorySelector({
  characterId,
  sessionId,
  onSelectStory,
  isOpen,
  onClose
}: StorySelectorProps) {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [startingStoryId, setStartingStoryId] = useState<string | null>(null);
  const [historyMap, setHistoryMap] = useState<Record<string, PlayHistoryEntry[]>>({});
  const [expandedStories, setExpandedStories] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (isOpen && characterId) {
      loadStories();
    }
  }, [isOpen, characterId]);

  const loadStories = async () => {
    setLoading(true);
    try {
      const data = await storyService.getAvailableStories(characterId);
      setStories(data);
      
      const historyPromises = data.map(async (story) => {
        try {
          const history = await storyService.getPlayHistory(story.id);
          return { storyId: story.id, history };
        } catch {
          return { storyId: story.id, history: [] };
        }
      });
      
      const historyResults = await Promise.all(historyPromises);
      const newHistoryMap: Record<string, PlayHistoryEntry[]> = {};
      historyResults.forEach(({ storyId, history }) => {
        newHistoryMap[storyId] = history;
      });
      setHistoryMap(newHistoryMap);
    } catch (error) {
      console.error('Failed to load stories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartStory = async (story: Story) => {
    if (!sessionId) return;

    setStartingStoryId(story.id);
    try {
      await storyService.startStory(story.id, sessionId);
      onSelectStory(story);
      onClose();
    } catch (error) {
      console.error('Failed to start story:', error);
    } finally {
      setStartingStoryId(null);
    }
  };

  const handleResumeStory = async (story: Story) => {
    if (!sessionId) return;

    setStartingStoryId(story.id);
    try {
      await storyService.resumeStory(story.id, sessionId);
      onSelectStory(story);
      onClose();
    } catch (error) {
      console.error('Failed to resume story:', error);
    } finally {
      setStartingStoryId(null);
    }
  };

  const handleReplayStory = async (story: Story) => {
    if (!sessionId) return;

    setStartingStoryId(story.id);
    try {
      await storyService.replayStory(story.id, sessionId);
      await loadStories();
      onSelectStory(story);
      onClose();
    } catch (error) {
      console.error('Failed to replay story:', error);
    } finally {
      setStartingStoryId(null);
    }
  };

  const toggleHistory = (storyId: string) => {
    setExpandedStories(prev => {
      const next = new Set(prev);
      if (next.has(storyId)) {
        next.delete(storyId);
      } else {
        next.add(storyId);
      }
      return next;
    });
  };

  const formatEnding = (ending: string | null) => {
    if (!ending) return null;
    const colors: Record<string, string> = {
      good: 'text-green-400',
      neutral: 'text-yellow-400',
      bad: 'text-red-400',
      secret: 'text-purple-400'
    };
    return <span className={colors[ending] || 'text-zinc-400'}>{ending}</span>;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-zinc-900 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden shadow-2xl border border-zinc-800">
        {/* Header */}
        <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="text-purple-400" size={20} />
            <h2 className="text-xl font-bold text-white">Stories</h2>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[60vh]">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mb-4" />
              <p className="text-zinc-400">Loading stories...</p>
            </div>
          ) : stories.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Sparkles className="text-zinc-600 mb-4" size={48} />
              <p className="text-zinc-400 mb-2">No stories available yet</p>
              <p className="text-zinc-500 text-sm">
                Keep chatting to unlock stories!
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {stories.map(story => (
                <div
                  key={story.id}
                  className="bg-zinc-800/50 rounded-lg p-4 flex gap-4 hover:bg-zinc-800 transition-colors border border-zinc-700/50"
                >
                  {/* Cover Image */}
                  {story.cover_image_url ? (
                    <img
                      src={story.cover_image_url}
                      alt={story.title}
                      className="w-24 h-24 object-cover rounded-lg flex-shrink-0"
                    />
                  ) : (
                    <div className="w-24 h-24 bg-gradient-to-br from-purple-600/30 to-pink-600/30 rounded-lg flex-shrink-0 flex items-center justify-center">
                      <BookOpen className="text-purple-400" size={32} />
                    </div>
                  )}

                  {/* Story Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <h3 className="font-semibold text-white truncate">{story.title}</h3>
                      {story.is_official && (
                        <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded flex-shrink-0">
                          Official
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-zinc-400 mb-3 line-clamp-2">
                      {story.description || 'No description'}
                    </p>

                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="text-xs text-zinc-500">
                        {story.total_nodes} scenes
                      </div>

                      {story.user_progress?.status === 'completed' ? (
                        <div className="flex items-center gap-2">
                          <span className="flex items-center gap-1 text-green-400 text-sm">
                            <CheckCircle size={16} />
                            Completed
                          </span>
                          <button
                            onClick={() => handleReplayStory(story)}
                            disabled={startingStoryId === story.id}
                            className="flex items-center gap-1 px-3 py-1.5 bg-purple-500/30 hover:bg-purple-500/50 text-purple-300 rounded-lg text-sm disabled:opacity-50 disabled:cursor-wait transition-colors"
                          >
                            {startingStoryId === story.id ? (
                              <div className="w-4 h-4 border-2 border-purple-300/30 border-t-purple-300 rounded-full animate-spin" />
                            ) : (
                              <RotateCcw size={14} />
                            )}
                            Replay
                          </button>
                        </div>
                      ) : story.user_progress?.status === 'in_progress' ? (
                        <button
                          onClick={() => handleResumeStory(story)}
                          disabled={startingStoryId === story.id}
                          className="flex items-center gap-1 px-3 py-1.5 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600 disabled:opacity-50 disabled:cursor-wait transition-colors"
                        >
                          {startingStoryId === story.id ? (
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          ) : (
                            <PlayCircle size={16} />
                          )}
                          Resume ({Math.round(story.user_progress.completion_percentage || 0)}%)
                        </button>
                      ) : (
                        <button
                          onClick={() => handleStartStory(story)}
                          disabled={startingStoryId === story.id}
                          className="flex items-center gap-1 px-3 py-1.5 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600 disabled:opacity-50 disabled:cursor-wait transition-colors"
                        >
                          {startingStoryId === story.id ? (
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          ) : (
                            <PlayCircle size={16} />
                          )}
                          Start Story
                        </button>
                      )}
                    </div>
                  </div>
                  
                  {historyMap[story.id] && historyMap[story.id].length > 0 && (
                    <div className="mt-3 border-t border-zinc-700/50 pt-2">
                      <button
                        onClick={() => toggleHistory(story.id)}
                        className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
                      >
                        <History size={12} />
                        {historyMap[story.id].length} play{historyMap[story.id].length > 1 ? 's' : ''}
                        {expandedStories.has(story.id) ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                      </button>
                      
                      {expandedStories.has(story.id) && (
                        <div className="mt-2 space-y-1">
                          {historyMap[story.id].map((entry) => (
                            <div key={entry.play_id} className="flex items-center justify-between text-xs bg-zinc-800/30 rounded px-2 py-1">
                              <span className="text-zinc-400">
                                #{entry.play_index} • {new Date(entry.started_at).toLocaleDateString()}
                              </span>
                              <div className="flex items-center gap-2">
                                {entry.ending_type && formatEnding(entry.ending_type)}
                                {entry.completion_time_minutes && (
                                  <span className="text-zinc-500">{entry.completion_time_minutes}min</span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-900/50">
          <p className="text-xs text-zinc-500 text-center">
            Stories unlock based on your relationship with the character
          </p>
        </div>
      </div>
    </div>
  );
}
