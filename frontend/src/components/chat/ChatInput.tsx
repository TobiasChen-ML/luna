import { useState, useRef, useEffect, useCallback } from 'react';
import type { KeyboardEvent } from 'react';
import { Button } from '@/components/common';
import { Camera, FileText, Send, Smile, Video, WandSparkles, X } from 'lucide-react';
import { cn } from '@/utils/cn';
import EmojiPicker, { type EmojiClickData, Theme } from 'emoji-picker-react';
import { VideoLoraSelector } from '@/components/video/VideoLoraSelector';
import { ImageLoraSelector } from '@/components/image/ImageLoraSelector';
import type { ImageGenerationLoRA } from '@/config/imageGenerationLoras';
import type { VideoLoraAction } from '@/services/videoLoraService';

interface PoseOption {
  id: string;
  label: string;
  thumbnailUrl: string;
}

// TODO: Replace thumbnailUrl values with your actual pose reference image URLs
const CHAT_POSE_PRESETS: PoseOption[] = [
  { id: 'standing', label: 'Standing', thumbnailUrl: '' },
  { id: 'sitting', label: 'Sitting', thumbnailUrl: '' },
  { id: 'kneeling', label: 'Kneeling', thumbnailUrl: '' },
  { id: 'lying_side', label: 'Lying Side', thumbnailUrl: '' },
  { id: 'lean_back', label: 'Lean Back', thumbnailUrl: '' },
  { id: 'bend_forward', label: 'Bend Forward', thumbnailUrl: '' },
  { id: 'on_all_fours', label: 'On All Fours', thumbnailUrl: '' },
  { id: 'seated_spread', label: 'Seated Spread', thumbnailUrl: '' },
];

interface ChatInputProps {
  onSend: (message: string, options?: { immediate?: boolean }) => void;
  onCompleteText?: (draft: string) => Promise<string>;
  onGenerateImage?: (prompt: string, poseImageUrl?: string, loraId?: string) => void | Promise<void>;
  onGenerateVideo?: (
    prompt: string,
    action?: VideoLoraAction,
    baseImageUrl?: string
  ) => void | Promise<void>;
  generatedVideoBaseImages?: string[];
  imagePromptTemplates?: string[];
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  onCompleteText,
  onGenerateImage,
  onGenerateVideo,
  generatedVideoBaseImages = [],
  imagePromptTemplates = [],
  disabled = false,
  placeholder = 'Type your message...',
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [imagePrompt, setImagePrompt] = useState('');
  const [videoPrompt, setVideoPrompt] = useState('');
  const [showImagePrompt, setShowImagePrompt] = useState(false);
  const [showVideoPrompt, setShowVideoPrompt] = useState(false);
  const [selectedPoseId, setSelectedPoseId] = useState<string | null>(null);
  const [selectedImageLora, setSelectedImageLora] = useState<ImageGenerationLoRA | null>(null);
  const [selectedLora, setSelectedLora] = useState<VideoLoraAction | null>(null);
  const [selectedVideoBaseImage, setSelectedVideoBaseImage] = useState<string | null>(null);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [actionLabelMode, setActionLabelMode] = useState<'full' | 'compact' | 'icon'>('full');
  const [isCompleting, setIsCompleting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const videoTextareaRef = useRef<HTMLTextAreaElement>(null);
  const emojiPickerRef = useRef<HTMLDivElement>(null);
  const imagePromptRef = useRef<HTMLDivElement>(null);
  const videoPromptRef = useRef<HTMLDivElement>(null);
  const actionsRowRef = useRef<HTMLDivElement>(null);
  const lastTemplateIndexRef = useRef<number>(-1);

  const handleSend = (immediate = false) => {
    if (message.trim() && !disabled) {
      onSend(message, { immediate });
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleComplete = async () => {
    if (disabled || isCompleting || !onCompleteText) return;
    const draft = message.trim();
    if (!draft) return;

    setIsCompleting(true);
    try {
      const completed = await onCompleteText(draft);
      if (completed && completed.trim()) setMessage(completed);
    } finally {
      setIsCompleting(false);
    }

    if (textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(true);
    }
  };

  const handleInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
    const target = e.currentTarget;
    setMessage(target.value);
    target.style.height = 'auto';
    target.style.height = Math.min(target.scrollHeight, 150) + 'px';
  };

  const handleEmojiClick = (emojiData: EmojiClickData) => {
    setMessage((prev) => prev + emojiData.emoji);
    if (textareaRef.current) textareaRef.current.focus();
  };

  const toggleEmojiPicker = () => {
    setShowImagePrompt(false);
    setShowVideoPrompt(false);
    setShowEmojiPicker((prev) => !prev);
  };

  const pickRandomTemplate = useCallback(() => {
    if (imagePromptTemplates.length === 0) return '';
    if (imagePromptTemplates.length === 1) {
      lastTemplateIndexRef.current = 0;
      return imagePromptTemplates[0];
    }
    let nextIndex = Math.floor(Math.random() * imagePromptTemplates.length);
    while (nextIndex === lastTemplateIndexRef.current) {
      nextIndex = Math.floor(Math.random() * imagePromptTemplates.length);
    }
    lastTemplateIndexRef.current = nextIndex;
    return imagePromptTemplates[nextIndex];
  }, [imagePromptTemplates]);

  const toggleImagePrompt = useCallback(() => {
    if (disabled || !onGenerateImage) return;
    setShowEmojiPicker(false);
    setShowVideoPrompt(false);
    if (showImagePrompt) { setShowImagePrompt(false); return; }
    setImagePrompt(pickRandomTemplate());
    setShowImagePrompt(true);
  }, [disabled, onGenerateImage, showImagePrompt, pickRandomTemplate]);

  const toggleVideoPrompt = () => {
    if (disabled || !onGenerateVideo) return;
    setShowEmojiPicker(false);
    setShowImagePrompt(false);
    if (showVideoPrompt) { setShowVideoPrompt(false); return; }
    setVideoPrompt('');
    setSelectedLora(null);
    setSelectedVideoBaseImage(generatedVideoBaseImages[0] || null);
    setShowVideoPrompt(true);
  };

  const handleLoraSelect = (lora: VideoLoraAction | null) => {
    setSelectedLora(lora);
    if (!lora) return;
    // Replace prompt with the scene's default prompt
    setVideoPrompt(lora.default_prompt);
    setTimeout(() => videoTextareaRef.current?.focus(), 50);
  };

  const handleImageLoraSelect = (lora: ImageGenerationLoRA | null) => {
    setSelectedImageLora(lora);
    if (!lora) return;
    // triggerWord is the full scene prompt — replace entirely
    setImagePrompt(lora.triggerWord);
  };

  const handleSendImagePrompt = async () => {
    if (!imagePrompt.trim() || disabled || !onGenerateImage) return;
    const selectedPose = CHAT_POSE_PRESETS.find((p) => p.id === selectedPoseId);
    await onGenerateImage(
      imagePrompt.trim(),
      selectedPose?.thumbnailUrl || undefined,
      selectedImageLora?.id,
    );
    setImagePrompt('');
    setSelectedPoseId(null);
    setSelectedImageLora(null);
    setShowImagePrompt(false);
  };

  const handleSendVideoPrompt = async () => {
    if (!videoPrompt.trim() || disabled || !onGenerateVideo || !selectedVideoBaseImage) return;
    await onGenerateVideo(videoPrompt.trim(), selectedLora ?? undefined, selectedVideoBaseImage);
    setVideoPrompt('');
    setSelectedLora(null);
    setSelectedVideoBaseImage(null);
    setShowVideoPrompt(false);
  };

  const handleImagePromptKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void handleSendImagePrompt(); }
  };

  const handleVideoPromptKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void handleSendVideoPrompt(); }
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (imagePromptRef.current && !imagePromptRef.current.contains(event.target as Node)) {
        setShowImagePrompt(false);
      }
      if (videoPromptRef.current && !videoPromptRef.current.contains(event.target as Node)) {
        setShowVideoPrompt(false);
      }
      if (emojiPickerRef.current && !emojiPickerRef.current.contains(event.target as Node)) {
        setShowEmojiPicker(false);
      }
    };

    if (showEmojiPicker || showImagePrompt || showVideoPrompt) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showEmojiPicker, showImagePrompt, showVideoPrompt]);

  useEffect(() => {
    const row = actionsRowRef.current;
    if (!row || typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver(([entry]) => {
      const width = entry.contentRect.width;
      if (width < 620) setActionLabelMode('icon');
      else if (width < 820) setActionLabelMode('compact');
      else setActionLabelMode('full');
    });
    observer.observe(row);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const handleTriggerShootPhoto = () => {
      if (!disabled && onGenerateImage) {
        toggleImagePrompt();
      }
    };
    window.addEventListener('triggerShootPhoto', handleTriggerShootPhoto);
    return () => window.removeEventListener('triggerShootPhoto', handleTriggerShootPhoto);
  }, [disabled, onGenerateImage, toggleImagePrompt]);

  return (
    <div className="sticky bottom-0 left-0 right-0 border-t border-white/10 bg-zinc-900/95 backdrop-blur-md px-2 py-3 sm:p-4 pb-safe z-20 flex-shrink-0">
      <div className="max-w-4xl mx-auto">
        <div ref={actionsRowRef} className="flex items-center gap-2 sm:gap-3">

          {/* Shoot Photo + Shoot Video side by side */}
          <div className="relative flex flex-row gap-2 shrink-0">

            {/* Shoot Photo */}
            <div className="relative">
              <Button
                type="button"
                onClick={toggleImagePrompt}
                disabled={disabled || !onGenerateImage}
                className={cn(
                  'h-12 px-3 flex items-center justify-center gap-1.5 border border-primary-400/50',
                  'bg-gradient-to-r from-primary-600/80 to-fuchsia-500/75 hover:from-primary-500 hover:to-fuchsia-400',
                  'text-white shadow-lg shadow-primary-700/20',
                  showImagePrompt && 'ring-2 ring-primary-300/60'
                )}
                aria-label="Shoot photo"
                title="Shoot photo"
              >
                <Camera size={12} />
                {actionLabelMode !== 'icon' && (
                  <span className="text-[11px] font-semibold tracking-wide leading-none">
                    {actionLabelMode === 'compact' ? 'Photo' : 'Shoot Photo'}
                  </span>
                )}
              </Button>

              {showImagePrompt && onGenerateImage && (
                <div
                  ref={imagePromptRef}
                  className="absolute bottom-full left-0 mb-2 w-[min(90vw,570px)] rounded-xl border border-white/15 bg-zinc-900/95 p-3 shadow-xl z-50"
                >
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-semibold text-white">Shoot Photo</p>
                    <button type="button" onClick={() => setShowImagePrompt(false)} className="text-zinc-400 hover:text-white" aria-label="Close">
                      <X size={16} />
                    </button>
                  </div>

                  {/* LoRA selector */}
                  <div className="mb-2">
                    <div className="mb-1.5 flex items-center justify-between">
                      <p className="text-xs text-zinc-400">Style / Position LoRA (optional)</p>
                      {selectedImageLora && (
                        <button
                          type="button"
                          onClick={() => setSelectedImageLora(null)}
                          className="text-[11px] text-zinc-500 hover:text-white transition-colors"
                        >
                          Clear
                        </button>
                      )}
                    </div>
                    <ImageLoraSelector
                      selectedId={selectedImageLora?.id ?? null}
                      onSelect={handleImageLoraSelect}
                      variant="compact"
                    />
                  </div>

                  <textarea
                    value={imagePrompt}
                    onChange={(e) => setImagePrompt(e.target.value)}
                    onKeyDown={handleImagePromptKeyDown}
                    placeholder="Describe the image you want..."
                    rows={4}
                    className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-zinc-500 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                  />
                  <div className="mt-2 flex justify-end">
                    <Button
                      type="button"
                      onClick={() => void handleSendImagePrompt()}
                      disabled={disabled || !imagePrompt.trim()}
                      className="h-9 px-3 text-sm flex items-center gap-1.5"
                    >
                      <Send size={14} />
                      Send
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {/* Shoot Video */}
            <div className="relative">
              <Button
                type="button"
                onClick={toggleVideoPrompt}
                disabled={disabled || !onGenerateVideo}
                className={cn(
                  'h-12 px-3 flex items-center justify-center gap-1.5 border border-violet-400/50',
                  'bg-gradient-to-r from-violet-600/80 to-indigo-500/75 hover:from-violet-500 hover:to-indigo-400',
                  'text-white shadow-lg shadow-violet-700/20',
                  showVideoPrompt && 'ring-2 ring-violet-300/60'
                )}
                aria-label="Shoot video"
                title="Shoot video"
              >
                <Video size={12} />
                {actionLabelMode !== 'icon' && (
                  <span className="text-[11px] font-semibold tracking-wide leading-none">
                    {actionLabelMode === 'compact' ? 'Video' : 'Shoot Video'}
                  </span>
                )}
              </Button>

              {showVideoPrompt && onGenerateVideo && (
                <div
                  ref={videoPromptRef}
                  className="absolute bottom-full left-0 mb-2 w-[min(90vw,630px)] rounded-xl border border-white/15 bg-zinc-900/95 p-3 shadow-xl z-50"
                >
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-semibold text-white">Shoot Video</p>
                    <button type="button" onClick={() => setShowVideoPrompt(false)} className="text-zinc-400 hover:text-white" aria-label="Close">
                      <X size={16} />
                    </button>
                  </div>

                  <div className="mb-3">
                    <div className="mb-1.5 flex items-center justify-between">
                      <p className="text-xs text-zinc-400">Base Image (Required)</p>
                      <p className="text-[11px] text-zinc-500">{generatedVideoBaseImages.length} available</p>
                    </div>
                    {generatedVideoBaseImages.length > 0 ? (
                      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-white/10">
                        {generatedVideoBaseImages.map((url, index) => {
                          const isSelected = selectedVideoBaseImage === url;
                          return (
                            <button
                              key={`${url}-${index}`}
                              type="button"
                              onClick={() => setSelectedVideoBaseImage(url)}
                              title={`Generated image ${index + 1}`}
                              className={cn(
                                'relative h-16 w-16 flex-shrink-0 overflow-hidden rounded-lg border',
                                isSelected
                                  ? 'border-violet-400 ring-2 ring-violet-400/60'
                                  : 'border-white/10 hover:border-white/30'
                              )}
                            >
                              <img
                                src={url}
                                alt={`Generated image ${index + 1}`}
                                className="h-full w-full object-cover"
                                loading="lazy"
                              />
                            </button>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="rounded-lg border border-dashed border-white/15 bg-white/5 px-3 py-2 text-xs text-zinc-400">
                        No generated images yet. Please shoot a photo first.
                      </p>
                    )}
                  </div>

                  {/* LoRA selector */}
                  <div className="mb-3">
                    <div className="mb-1.5 flex items-center justify-between">
                      <p className="text-xs text-zinc-400">Scene / Action</p>
                      {selectedLora && (
                        <button
                          type="button"
                          onClick={() => { setSelectedLora(null); setVideoPrompt(''); }}
                          className="text-[11px] text-zinc-500 hover:text-white transition-colors"
                        >
                          Clear
                        </button>
                      )}
                    </div>
                    <VideoLoraSelector
                      selectedId={selectedLora?.id ?? null}
                      onSelect={handleLoraSelect}
                      variant="compact"
                    />
                    {selectedLora && (
                      <p className="mt-1.5 text-[10px] text-violet-300/80">
                        Scene: <span className="font-mono">{selectedLora.action_label}</span>
                      </p>
                    )}
                  </div>

                  <textarea
                    ref={videoTextareaRef}
                    value={videoPrompt}
                    onChange={(e) => setVideoPrompt(e.target.value)}
                    onKeyDown={handleVideoPromptKeyDown}
                    placeholder="Select a scene above, then describe the character and setting..."
                    rows={4}
                    className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-zinc-500 resize-none focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                  />
                  <div className="mt-2 flex justify-end">
                    <Button
                      type="button"
                      onClick={() => void handleSendVideoPrompt()}
                      disabled={disabled || !videoPrompt.trim() || !selectedVideoBaseImage}
                      className="h-9 px-3 text-sm flex items-center gap-1.5 bg-violet-600 hover:bg-violet-500 border-violet-500"
                    >
                      <WandSparkles size={14} />
                      Generate
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Message Input */}
          <div className="relative flex-1 min-w-[220px] sm:min-w-[300px]">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled}
              rows={1}
              className={cn(
                'w-full px-4 py-3 pr-12 rounded-xl bg-white/5 border border-white/10',
                'text-white placeholder:text-zinc-500 resize-none',
                'focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50',
                'disabled:opacity-50 disabled:cursor-not-allowed transition-all min-h-12'
              )}
              style={{ maxHeight: '150px' }}
            />
            <button
              type="button"
              onClick={toggleEmojiPicker}
              className={cn(
                'absolute right-3 bottom-3 transition-colors',
                showEmojiPicker ? 'text-primary-400' : 'text-zinc-400 hover:text-primary-400'
              )}
              disabled={disabled}
              aria-label="Open emoji picker"
            >
              <Smile size={20} />
            </button>
            {showEmojiPicker && (
              <div ref={emojiPickerRef} className="absolute bottom-full right-0 mb-2 z-50">
                <EmojiPicker
                  onEmojiClick={handleEmojiClick}
                  theme={Theme.DARK}
                  width={320}
                  height={400}
                  searchPlaceHolder="Search emojis..."
                  previewConfig={{ showPreview: false }}
                />
              </div>
            )}
          </div>

          <Button
            type="button"
            onClick={() => void handleComplete()}
            disabled={disabled || isCompleting || !onCompleteText || !message.trim()}
            className={cn(
              'h-12 px-3 sm:px-4 shrink-0 whitespace-nowrap flex items-center gap-2',
              'bg-cyan-500/20 border border-cyan-300/40 text-cyan-100',
              'hover:bg-cyan-400/25 hover:border-cyan-200/60 transition-colors'
            )}
            style={{ display: 'none' }}
            title="Complete draft with AI"
            aria-label="AI complete text"
          >
            <FileText size={16} />
            {actionLabelMode !== 'icon' && (
              <span className="text-sm font-semibold tracking-wide">
                {isCompleting
                  ? (actionLabelMode === 'compact' ? 'Completing' : 'Completing...')
                  : (actionLabelMode === 'compact' ? 'AI Complete' : 'AI Complete Text')}
              </span>
            )}
          </Button>

          <Button
            onClick={() => handleSend(true)}
            disabled={disabled || !message.trim()}
            className="h-12 px-4 sm:px-6 shrink-0 flex items-center gap-2"
            aria-label="Send message"
          >
            <Send size={18} />
            {actionLabelMode !== 'icon' && <span>Send</span>}
          </Button>
        </div>

        <p className="text-xs text-zinc-500 mt-2 text-center hidden sm:block">
          Press Enter to send, Shift + Enter for new line
        </p>
      </div>
    </div>
  );
}
