import type { Message, NDJSONSegment } from '@/types/chat';
import { cn } from '@/utils/cn';
import { format } from 'date-fns';
import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ImagePreviewModal } from '../common';
import { Volume2, Loader2, Mic, Video, Play, WandSparkles, X, FileText } from 'lucide-react';
import { api } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { useChatContext } from '@/contexts/ChatContext';
import { useAudioFocus } from '@/contexts/AudioFocusContext';
import { getSafeAvatarUrl } from '@/utils/avatarUrlGuard';
import { getInsufficientCreditsInfo } from '@/utils/apiError';
import { VoiceNotePlayer } from './VoiceNotePlayer';
import { VideoLoraSelector } from '@/components/video/VideoLoraSelector';
import type { VideoLoraAction } from '@/services/videoLoraService';

interface InnerMonologueBubbleProps {
  content: string;
  isStreaming: boolean;
  characterAvatar?: string;
  characterName?: string;
}

export function InnerMonologueBubble({
  content,
  isStreaming,
  characterAvatar,
  characterName,
}: InnerMonologueBubbleProps) {
  const safeAvatar = getSafeAvatarUrl(characterAvatar);

  return (
    <div className="flex gap-3 mb-2 animate-in fade-in duration-300">
      {safeAvatar ? (
        <div className="flex-shrink-0 w-10 h-10 rounded-full overflow-hidden border border-purple-500/20 opacity-60">
          <img src={safeAvatar} alt={characterName || 'AI'} className="w-full h-full object-cover" />
        </div>
      ) : (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-white/5 border border-purple-500/20 opacity-60 flex items-center justify-center text-sm text-purple-400">
          {characterName?.charAt(0) || 'AI'}
        </div>
      )}
      <div
        className={cn(
          'max-w-[70%] px-4 py-2.5 rounded-2xl rounded-tl-sm',
          'bg-purple-950/30 border border-purple-500/15',
          'text-zinc-400 text-sm italic leading-relaxed',
          isStreaming && 'animate-pulse'
        )}
      >
        <span className="text-purple-400/60 not-italic mr-1.5">💭</span>
        {content}
      </div>
    </div>
  );
}
function extractQuotedText(text: string): string {
  const chinese = text.match(/“([^”]+)”/);
  if (chinese?.[1]) return chinese[1].trim();

  const ascii = text.match(/"([^"]+)"/);
  if (ascii?.[1]) return ascii[1].trim();

  return text.trim();
}

function normalizeDialogueText(text: string): string {
  const trimmed = text.trim();
  const m = trimmed.match(/^\s*[^:：]{1,30}[:：]\s*(.*)$/);
  const rest = (m?.[1] ?? trimmed).trim();
  return extractQuotedText(rest);
}

function normalizeLegacyDialogueLines(content: string): string {
  const lines = content.split('\n');
  const normalized = lines.map((line) => {
    const m = line.match(/^\s*[^:：]{1,30}[:：]\s*[“”]/);
    if (!m) return line;
    return normalizeDialogueText(line);
  });
  return normalized.join('\n');
}

function SegmentRenderer({ segments }: { segments: NDJSONSegment[] }) {
  return (
    <div className="space-y-2">
      {segments.map((seg, idx) => {
        switch (seg.type) {
          case 'state':
            return null;
          case 'scene':
            return (
              <p key={idx} className="text-amber-200/70 italic text-sm border-l-2 border-amber-500/30 pl-3">
                {seg.text}
              </p>
            );
          case 'narration':
            return (
              <p key={idx} className="text-zinc-300 text-sm leading-relaxed">
                {seg.text}
              </p>
            );
          case 'action':
            return (
              <p key={idx} className="text-zinc-400 italic text-sm">
                {seg.text}
              </p>
            );
          case 'dialogue':
            return (
              <p key={idx} className="text-white">
                {seg.speaker && seg.speaker !== 'She' && (
                  <span className="text-primary-300 font-semibold mr-1">{seg.speaker}:</span>
                )}
                {normalizeDialogueText(seg.text)}
              </p>
            );
          case 'npc':
            return (
              <div key={idx} className="pl-3 border-l-2 border-zinc-600/50">
                <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wide">
                  {seg.speaker}
                </span>
                <p className="text-zinc-200 text-sm mt-0.5">{seg.text}</p>
              </div>
            );
          case 'inner':
            return (
              <p key={idx} className="text-purple-300 italic text-sm opacity-80">
                ({seg.text})
              </p>
            );
          case 'hook':
            return (
              <p key={idx} className="text-primary-300 font-medium mt-2">
                {seg.text}
              </p>
            );
          default:
            return (
              <p key={idx} className="text-white">{seg.text}</p>
            );
        }
      })}
    </div>
  );
}

interface MessageBubbleProps {
  message: Message;
  characterName?: string;
  characterAvatar?: string;
  sessionId?: string;
}

export function MessageBubble({ message, characterName, characterAvatar, sessionId }: MessageBubbleProps) {
  const isCallReport = message.metadata?.type === 'voice_call_report';
  const isUser = message.role === 'user' || isCallReport;
  const isVoiceCall = message.metadata?.source === 'voice_call';
  const isVirtualNDJSONSegment = Boolean((message.metadata as any)?.virtual_ndjson_segment);
  const isLastVirtualNDJSONSegment = Boolean((message.metadata as any)?.virtual_ndjson_last_segment);
  const parentMessageId = (message.metadata as any)?.parent_message_id as string | undefined;
  const audioMessageId = isVirtualNDJSONSegment && parentMessageId ? parentMessageId : message.id;
  const [showImagePreview, setShowImagePreview] = useState(false);
  const [showVoiceTranscript, setShowVoiceTranscript] = useState(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isAnimatingImage, setIsAnimatingImage] = useState(false);
  const [showAnimatePrompt, setShowAnimatePrompt] = useState(false);
  const [animatePrompt, setAnimatePrompt] = useState('');
  const [selectedLora, setSelectedLora] = useState<VideoLoraAction | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const { refreshUser } = useAuth();
  const { registerAnimateTask, pendingVideoTasks, showInsufficientCreditsModal } = useChatContext();
  const { isAudioSuppressed } = useAudioFocus();
  const [animatingTaskId, setAnimatingTaskId] = useState<string | null>(null);
  const safeCharacterAvatar = getSafeAvatarUrl(characterAvatar);
  const safeContent =
    typeof message.content === 'string'
      ? message.content
      : (message.content == null ? '' : String(message.content));

  // Detect message type and status
  const messageType = message.message_type || 'text';
  const messageStatus = message.status || 'ready';
  const isGenerating = messageStatus === 'generating';
  const isVoiceNote = messageType === 'voice_note';
  const isVoiceNoteFailed = isVoiceNote && messageStatus === 'failed' && !message.audio_url;
  const isVoicePending = Boolean(message.metadata?.voice_pending) && !message.audio_url;
  const transcriptText =
    (typeof message.transcript === 'string' && message.transcript.trim()) ||
    (typeof message.metadata?.transcript === 'string' && message.metadata.transcript.trim()) ||
    (safeContent.trim() || '');

  const handlePlayVoice = async () => {
    if (isUser || !sessionId || isAudioSuppressed) return;

    try {
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      setIsPlayingAudio(false);
      setIsLoadingAudio(true);

      let audioUrl = message.audio_url;
      let creditsDeducted = false;

      // If audio not cached, generate and cache it
      if (!audioUrl) {
        const response = await api.post(
          `/chat/messages/${audioMessageId}/audio?session_id=${sessionId}`
        );

        if (response.data.success && response.data.audio_url) {
          audioUrl = response.data.audio_url;
          // Update local message cache (optional - will be available on next load)
          message.audio_url = audioUrl;

          // Check if credits were deducted (not cached)
          if (!response.data.cached && response.data.credits_deducted) {
            creditsDeducted = true;
          }
        } else {
          throw new Error('Failed to generate audio');
        }
      }

      // Refresh user credits if they were deducted
      if (creditsDeducted) {
        await refreshUser();
      }

      // Create and play audio
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onloadeddata = () => {
        setIsLoadingAudio(false);
        setIsPlayingAudio(true);
      };

      audio.onended = () => {
        setIsPlayingAudio(false);
        audioRef.current = null;
      };

      audio.onerror = () => {
        setIsLoadingAudio(false);
        setIsPlayingAudio(false);
        console.error('Failed to play audio');
      };

      await audio.play();
    } catch (error: any) {
      console.error('Failed to play voice:', error);

      const insufficientCredits = getInsufficientCreditsInfo(error);
      if (insufficientCredits) {
        showInsufficientCreditsModal(insufficientCredits.required, insufficientCredits.available);
      }

      setIsLoadingAudio(false);
      setIsPlayingAudio(false);
    }
  };

  const handleAnimateLoraSelect = (lora: VideoLoraAction | null) => {
    setSelectedLora(lora);
    if (!lora) return;
    setAnimatePrompt(lora.default_prompt);
  };

  const handleAnimateImage = async (prompt: string, action?: VideoLoraAction) => {
    if (!message.image_url || !sessionId) return;

    const characterId = message.character_id || undefined;

    setShowAnimatePrompt(false);

    try {
      setIsAnimatingImage(true);
      const response = await api.post<{ task_id: string; status: string }>(
        '/images/generate-video-wan-character',
        {
          prompt,
          character_id: characterId,
          session_id: sessionId,
          image_url: message.image_url,
          lora_preset_id: action?.lora_preset_id,
          selected_trigger_word: action?.trigger_word,
        }
      );
      const taskId = response.data.task_id;

      if (taskId) {
        setAnimatingTaskId(taskId);
        registerAnimateTask(taskId, sessionId);
      } else {
        setIsAnimatingImage(false);
      }

    } catch (error: any) {
      console.error('Failed to animate image:', error);

      const insufficientCredits = getInsufficientCreditsInfo(error);
      if (insufficientCredits) {
        showInsufficientCreditsModal(insufficientCredits.required, insufficientCredits.available);
      } else {
        alert('Failed to start video generation. Please try again.');
      }
      setIsAnimatingImage(false);
      setAnimatingTaskId(null);
    }
  };

  // Cleanup audio on unmount
  useEffect(() => {
    if (isAudioSuppressed && audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setIsPlayingAudio(false);
      setIsLoadingAudio(false);
    }
  }, [isAudioSuppressed]);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!animatingTaskId) return;
    const task = pendingVideoTasks.find((item) => item.taskId === animatingTaskId);
    if (!task) return;

    if (task.status === 'completed' || task.status === 'failed') {
      setIsAnimatingImage(false);
      setAnimatingTaskId(null);
    }
  }, [animatingTaskId, pendingVideoTasks]);

  return (
    <div
      className={cn(
        'flex gap-3 mb-4 animate-in slide-in-from-bottom-2',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      {!isUser && safeCharacterAvatar ? (
        <div className="flex-shrink-0 w-10 h-10 rounded-full overflow-hidden border border-primary-500/30">
          <img src={safeCharacterAvatar} alt={characterName || 'AI'} className="w-full h-full object-cover" />
        </div>
      ) : (
        <div
          className={cn(
            'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm',
            isUser
              ? 'bg-gradient-primary text-white'
              : 'bg-white/10 text-primary-400 border border-primary-500/30'
          )}
        >
          {isUser ? 'You' : characterName?.charAt(0) || 'AI'}
        </div>
      )}

      {/* Message Content */}
      <div className={cn('flex-1 max-w-[90%] sm:max-w-[80%] md:max-w-[70%]', isUser && 'flex flex-col items-end')}>
        <div
          className={cn(
            'px-4 py-3 rounded-2xl relative',
            isUser
              ? 'bg-gradient-primary text-white rounded-tr-sm'
              : 'glass-effect text-white rounded-tl-sm',
            isVoiceCall && 'border-l-4 border-purple-500' // Visual indicator for voice call messages
          )}
        >
          {/* Voice Call Badge */}
          {isVoiceCall && (
            <div className="absolute -top-2 -left-2 bg-purple-500 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1 shadow-lg">
              <Mic size={12} />
              <span>Voice</span>
            </div>
          )}

          {/* Generating Status Skeleton Loader */}
          {isGenerating ? (
            <div className="space-y-2 animate-pulse">
              <div className="h-4 bg-zinc-700/50 rounded w-3/4"></div>
              <div className="h-4 bg-zinc-700/50 rounded w-full"></div>
              <div className="h-4 bg-zinc-700/50 rounded w-5/6"></div>
              <div className="flex items-center gap-2 mt-3 text-sm text-zinc-500">
                <Loader2 size={16} className="animate-spin" />
                <span>Generating {messageType}...</span>
              </div>
            </div>
          ) : isVoiceNote && message.audio_url ? (
            // Voice Note Player
            <div className="space-y-2">
              <VoiceNotePlayer
                messageId={message.id}
                audioUrl={message.audio_url}
                duration={message.duration || 0}
                isGenerating={false}
                cost={message.cost}
              />
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setShowVoiceTranscript((prev) => !prev)}
                  className="inline-flex items-center gap-1 rounded-full border border-white/15 px-2 py-1 text-[11px] text-zinc-300 hover:text-white hover:border-white/30"
                >
                  <FileText size={12} />
                  {showVoiceTranscript ? 'Hide text' : 'Show text'}
                </button>
                <span className="text-[11px] text-zinc-500">{Math.max(1, Math.round(message.duration || 0))}s</span>
              </div>
              {showVoiceTranscript && (
                <div className="rounded-lg border border-white/10 bg-black/30 p-2 text-xs text-zinc-200 whitespace-pre-wrap">
                  {transcriptText || 'No transcript available.'}
                </div>
              )}
            </div>
          ) : isVoiceNoteFailed ? (
            <div className="space-y-2">
              <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-2 text-sm text-rose-200">
                Voice generation failed. Fallback to text.
              </div>
              {safeContent && (
                <div className="text-sm text-zinc-200 whitespace-pre-wrap">{safeContent}</div>
              )}
              <div className="text-xs text-zinc-500">{message.error || 'voice_note_failed'}</div>
            </div>
          ) : isCallReport ? (
            <div className="flex items-center gap-2 text-base font-medium min-w-[180px] justify-between">
              <span>{safeContent}</span>
              <Video size={20} className="text-white/80" />
            </div>
          ) : message.isNDJSON && message.segments && message.segments.length > 0 ? (
            <div className={cn(
              "max-w-none break-words",
              !isUser && !message.image_url && !message.video_url && "pr-12"
            )}>
              <SegmentRenderer segments={message.segments} />
            </div>
          ) : (
            <div className={cn(
              "prose prose-invert prose-sm max-w-none break-words [&>*:first-child]:mt-0 [&>*:last-child]:mb-0",
              !isUser && !message.image_url && !message.video_url && "pr-12"
            )}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {isUser ? safeContent : normalizeLegacyDialogueLines(safeContent)}
              </ReactMarkdown>
            </div>
          )}
          {isVoicePending && (
            <div className="mt-2 inline-flex items-center gap-1.5 text-xs text-zinc-400">
              <Loader2 size={12} className="animate-spin" />
              <span>Generating voice...</span>
            </div>
          )}
          {!isVoicePending && message.error && !isVoiceNoteFailed && (
            <div className="mt-2 text-xs text-rose-300/80">Voice unavailable, showing text reply.</div>
          )}

          {message.metadata?.show_photo_button && !isUser && (
            <div className="mt-3 flex justify-start">
              <button
                onClick={() => {
                  const event = new CustomEvent('triggerShootPhoto');
                  window.dispatchEvent(event);
                }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-primary-600/80 to-fuchsia-500/75 hover:from-primary-500 hover:to-fuchsia-400 text-white text-sm font-medium shadow-lg shadow-primary-700/20 border border-primary-400/50 transition-all"
              >
                📸 拍张照片
              </button>
            </div>
          )}

          {/* Voice Button for Character Messages - Only show on text-only messages */}
          {!isUser && !message.image_url && !message.video_url && !isCallReport && !isVoiceNote && (!isVirtualNDJSONSegment || isLastVirtualNDJSONSegment) && (
            <button
              onClick={handlePlayVoice}
              disabled={isLoadingAudio || isAudioSuppressed}
              className={cn(
                'absolute top-2 right-2 w-10 h-10 rounded-full flex items-center justify-center transition-all shadow-lg',
                'bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20',
                isPlayingAudio && 'bg-primary-500/50 border-primary-400',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
              title={isAudioSuppressed ? '通话中音频已暂停' : 'Play voice (1 credit)'}
            >
              {isAudioSuppressed ? (
                <Mic size={20} className="text-white" />
              ) : isLoadingAudio ? (
                <Loader2 size={20} className="text-white animate-spin" />
              ) : (
                <Volume2 size={20} className={cn('text-white', isPlayingAudio && 'animate-pulse')} />
              )}
            </button>
          )}
          {message.image_url && !isGenerating && (
            <>
              <div className="mt-3 rounded-lg overflow-hidden relative group">
                <img
                  src={message.image_url}
                  alt="Generated content"
                  className="w-full h-auto max-w-full sm:max-w-[300px] object-cover cursor-pointer hover:opacity-90 transition-opacity"
                  loading="lazy"
                  onClick={() => setShowImagePreview(true)}
                />

                {/* Animate Button (Image to Video) 鈥?Wan 2.1 */}
                {!isUser && sessionId && (
                  <button
                    onClick={() => setShowAnimatePrompt((v) => !v)}
                    disabled={isAnimatingImage}
                    className={cn(
                      'absolute bottom-2 right-2 px-3 py-1.5 rounded-lg',
                      'bg-primary-500/90 hover:bg-primary-600/90 text-white text-sm font-medium',
                      'flex items-center gap-1.5 shadow-lg backdrop-blur-sm',
                      'opacity-100 transition-all',
                      'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                    title="Animate this image into a video"
                  >
                    {isAnimatingImage ? (
                      <>
                        <Loader2 size={16} className="animate-spin" />
                        <span>Animating...</span>
                      </>
                    ) : (
                      <>
                        <Play size={16} fill="white" />
                        <span>Animate</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {/* Animate prompt panel */}
              {showAnimatePrompt && !isAnimatingImage && (
                <div className="mt-2 rounded-xl border border-white/10 bg-zinc-900/95 p-3 shadow-xl">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-semibold text-white">Shoot Video</p>
                    <button
                      type="button"
                      onClick={() => setShowAnimatePrompt(false)}
                      className="text-zinc-400 hover:text-white"
                      aria-label="Close"
                    >
                      <X size={16} />
                    </button>
                  </div>
                  <div className="mb-3">
                    <div className="mb-1.5 flex items-center justify-between">
                      <p className="text-xs text-zinc-400">Scene / Action</p>
                      {selectedLora && (
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedLora(null);
                            setAnimatePrompt('');
                          }}
                          className="text-[11px] text-zinc-500 hover:text-white transition-colors"
                        >
                          Clear
                        </button>
                      )}
                    </div>
                    <VideoLoraSelector
                      selectedId={selectedLora?.id ?? null}
                      onSelect={handleAnimateLoraSelect}
                      variant="compact"
                    />
                    {selectedLora && (
                      <p className="mt-1.5 text-[10px] text-violet-300/80">
                        Scene: <span className="font-mono">{selectedLora.action_label}</span>
                      </p>
                    )}
                  </div>
                  <input
                    type="text"
                    value={animatePrompt}
                    onChange={(e) => setAnimatePrompt(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && animatePrompt.trim()) {
                        handleAnimateImage(animatePrompt.trim(), selectedLora ?? undefined);
                      }
                      if (e.key === 'Escape') setShowAnimatePrompt(false);
                    }}
                    className="w-full rounded-lg bg-zinc-800 border border-white/10 px-3 py-2 text-sm text-white placeholder:text-zinc-500 focus:outline-none focus:border-primary-400"
                    placeholder="Select a scene above, then describe the character and setting..."
                    autoFocus
                  />
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => animatePrompt.trim() && handleAnimateImage(animatePrompt.trim(), selectedLora ?? undefined)}
                      disabled={!animatePrompt.trim()}
                      className="flex-1 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-40 px-3 py-1.5 text-sm font-medium text-white transition-colors flex items-center justify-center gap-1.5"
                    >
                      <WandSparkles size={14} />
                      Generate
                    </button>
                    <button
                      onClick={() => {
                        setShowAnimatePrompt(false);
                        setSelectedLora(null);
                      }}
                      className="px-3 py-1.5 rounded-lg bg-zinc-700 hover:bg-zinc-600 text-sm text-zinc-300 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              <ImagePreviewModal
                isOpen={showImagePreview}
                onClose={() => setShowImagePreview(false)}
                imageUrl={message.image_url}
              />
            </>
          )}
          {message.video_url && !isGenerating && (
            <div className="mt-3 rounded-lg overflow-hidden">
              <video
                src={message.video_url}
                controls
                className="w-full h-auto max-w-full sm:max-w-[300px]"
                playsInline
              />
            </div>
          )}
        </div>
        <span className="text-xs text-zinc-500 mt-1 px-1">
          {(() => {
            try {
              const dateStr = message.timestamp || (message as any).created_at;
              if (!dateStr) return '';
              return format(new Date(dateStr), 'HH:mm');
            } catch {
              return '';
            }
          })()}
        </span>
      </div>
    </div>
  );
}
