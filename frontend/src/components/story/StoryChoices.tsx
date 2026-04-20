/**
 * StoryChoices Component
 *
 * Displays interactive story choices during active story gameplay.
 * Enhanced version of SceneChoices with story-specific features:
 * - Locked choices with requirements
 * - Narrative phase indicator
 * - Turns remaining counter
 * - Free text input with natural language matching
 */
import { useState, useCallback } from 'react';
import { BookOpen, Lock, ArrowRight, Send, Loader2 } from 'lucide-react';
import type { StoryChoice, NarrativePhase } from '@/types/story';

interface StoryChoicesProps {
  choices: StoryChoice[];
  narrativePhase: NarrativePhase | null;
  turnsRemaining: number | null;
  storyTitle?: string;
  storyId: string;
  nodeId?: string;
  onSelect: (choiceId: string) => void;
  onFreeTextMatch?: (result: MatchResult) => void;
  disabled?: boolean;
  enableFreeInput?: boolean;
}

interface MatchResult {
  matched: boolean;
  choice?: StoryChoice;
  confidence: number;
  method: string;
}

const phaseLabels: Record<NarrativePhase, string> = {
  opening: 'Opening',
  rising: 'Rising Action',
  climax: 'Climax',
  resolution: 'Resolution',
};

const phaseColors: Record<NarrativePhase, string> = {
  opening: 'bg-blue-500/20 text-blue-400',
  rising: 'bg-yellow-500/20 text-yellow-400',
  climax: 'bg-red-500/20 text-red-400',
  resolution: 'bg-green-500/20 text-green-400',
};

export function StoryChoices({
  choices,
  narrativePhase,
  turnsRemaining,
  storyTitle,
  storyId,
  nodeId,
  onSelect,
  onFreeTextMatch,
  disabled,
  enableFreeInput = true
}: StoryChoicesProps) {
  const [inputMode, setInputMode] = useState<'buttons' | 'input'>('buttons');
  const [userInput, setUserInput] = useState('');
  const [isMatching, setIsMatching] = useState(false);
  const [matchError, setMatchError] = useState<string | null>(null);

  if (choices.length === 0) return null;

  const handleMatchChoice = useCallback(async () => {
    if (!userInput.trim() || isMatching) return;

    setIsMatching(true);
    setMatchError(null);

    try {
      const response = await fetch(`/api/stories/${storyId}/match-choice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_message: userInput.trim(),
          node_id: nodeId,
          choices
        })
      });

      if (!response.ok) {
        throw new Error('Match request failed');
      }

      const result: MatchResult = await response.json();

      if (result.matched && result.choice) {
        onSelect(result.choice.id);
        onFreeTextMatch?.(result);
        setUserInput('');
        setInputMode('buttons');
      } else {
        setMatchError('No matching choice found. Please select an option below or rephrase your input.');
      }
    } catch (err) {
      setMatchError(err instanceof Error ? err.message : 'Matching failed');
    } finally {
      setIsMatching(false);
    }
  }, [userInput, storyId, nodeId, choices, onSelect, onFreeTextMatch, isMatching]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleMatchChoice();
    }
  }, [handleMatchChoice]);

  return (
    <div className="px-2 py-3 sm:px-4 sm:py-4 border-t border-purple-500/30 bg-gradient-to-t from-purple-950/50 to-transparent flex-shrink-0">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <BookOpen size={16} className="text-purple-400" />
            <span className="text-sm font-medium text-purple-300">
              {storyTitle ? `Story: ${storyTitle}` : 'Story Choice'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {narrativePhase && (
              <span className={`px-2 py-0.5 text-xs rounded capitalize ${phaseColors[narrativePhase]}`}>
                {phaseLabels[narrativePhase]}
              </span>
            )}
            {turnsRemaining !== null && turnsRemaining > 0 && (
              <span className="text-xs text-zinc-500">
                {turnsRemaining} turn{turnsRemaining !== 1 ? 's' : ''} left
              </span>
            )}
            {enableFreeInput && (
              <button
                onClick={() => setInputMode(inputMode === 'buttons' ? 'input' : 'buttons')}
                className="text-xs text-purple-400 hover:text-purple-300 transition-colors"
              >
                {inputMode === 'buttons' ? 'Type response' : 'Show options'}
              </button>
            )}
          </div>
        </div>

        {inputMode === 'input' && enableFreeInput ? (
          <div className="space-y-2">
            <div className="flex gap-2">
              <input
                type="text"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your response..."
                disabled={disabled || isMatching}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none disabled:opacity-50"
              />
              <button
                onClick={handleMatchChoice}
                disabled={disabled || isMatching || !userInput.trim()}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isMatching ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Send size={16} />
                )}
              </button>
            </div>
            
            {matchError && (
              <p className="text-xs text-amber-400">{matchError}</p>
            )}
            
            <button
              onClick={() => setInputMode('buttons')}
              className="text-xs text-zinc-500 hover:text-zinc-400"
            >
              Or select from predefined options ↓
            </button>
          </div>
        ) : null}

        <div className={`flex flex-col gap-2 ${inputMode === 'input' ? 'mt-2 opacity-70' : ''}`}>
          {choices.map((choice, index) => (
            <button
              key={choice.id}
              onClick={() => !choice.locked && onSelect(choice.id)}
              disabled={disabled || choice.locked}
              className={`
                w-full px-4 py-3 rounded-lg text-sm text-left transition-all
                flex items-center justify-between gap-2
                ${choice.locked
                  ? 'bg-zinc-800/50 text-zinc-500 cursor-not-allowed border border-zinc-700'
                  : 'bg-white/5 hover:bg-purple-500/20 border border-purple-500/30 hover:border-purple-400 text-zinc-200 hover:text-white'
                }
                disabled:opacity-50
              `}
            >
              <span className="flex items-center gap-3 min-w-0">
                <span className={`
                  w-6 h-6 rounded-full text-xs flex items-center justify-center font-medium flex-shrink-0
                  ${choice.locked
                    ? 'bg-zinc-700 text-zinc-500'
                    : 'bg-purple-500/20 text-purple-400 group-hover:bg-purple-500/40'
                  }
                `}>
                  {index + 1}
                </span>
                <span className="truncate">{choice.text}</span>
              </span>

              {choice.locked ? (
                <span className="flex items-center gap-1 text-xs text-zinc-500 flex-shrink-0">
                  <Lock size={12} />
                  <span className="hidden sm:inline">{choice.lock_reason || 'Locked'}</span>
                </span>
              ) : (
                <ArrowRight size={16} className="text-purple-400 flex-shrink-0" />
              )}
            </button>
          ))}
        </div>

        {inputMode === 'buttons' && (
          <p className="mt-2 text-xs text-zinc-500 text-center">
            {enableFreeInput 
              ? 'Click a choice or type your own response'
              : 'Click a choice to continue'
            }
          </p>
        )}
      </div>
    </div>
  );
}
