import { useState, useEffect, useMemo, useRef } from 'react';
import { useSearchParams, useNavigate, useParams } from 'react-router-dom';
import { useTelegramBackButton } from '@/hooks/useTelegramBackButton';
import { ChatProvider, useChatContext } from '@/contexts/ChatContext';
import { useAuth } from '@/contexts/AuthContext';
import { useGeoContext } from '@/contexts/GeoContext';
import {
  CharacterSelector,
  MessageList,
  ChatInput,
  ConsentModal,
  SceneBanner,
  AgeVerificationModal,
  RealtimeCallModal,
} from '@/components/chat';
import { RelationshipDashboardCard } from '@/components/chat/RelationshipDashboardCard';
import { SceneChoices } from '@/components/chat/SceneChoices';
import { StoryCompletionModal } from '@/components/story';
import { RelationshipLockModal } from '@/components/character/RelationshipLockModal';
import { Button, CommingSoonModal, GalleryModal, LanguageModal } from '@/components/common';
import {
  BookHeart,
  CircleDollarSign,
  Compass,
  Contact,
  Globe2,
  HelpCircle,
  ImagePlus,
  Menu,
  Sparkles,
  AlertCircle,
  Image,
  Coins,
  Home,
  ShieldCheck,
  Trophy,
  WandSparkles,
  MessageCircle,
  UserCircle2,
  ChevronLeft,
  ChevronRight,
  MoreVertical,
  Video,
} from 'lucide-react';
import { api } from '@/services/api';
import { notificationService } from '@/services/notificationService';
import type { Character } from '@/types';
import type { VideoLoraAction } from '@/services/videoLoraService';
import { getSafeAvatarUrl } from '@/utils/avatarUrlGuard';
import { getErrorMessage, getInsufficientCreditsInfo } from '@/utils/apiError';
import { normalizeTaskStatus } from '@/utils/taskStatus';
import { AudioFocusProvider } from '@/contexts/AudioFocusContext';

interface CharacterMediaItem {
  type: 'image' | 'video';
  url: string;
}

type CharacterWithExtraMedia = Character & {
  avatar_url?: string | null;
  mature_image_url?: string | null;
  mature_cover_url?: string | null;
  mature_video_url?: string | null;
};

function formatCharacterDescription(character: Character) {
  const characterWithBackstory = character as Character & { backstory?: string };
  return characterWithBackstory.backstory?.trim() || character.background?.backstory?.trim() || '';
}

function ChatContent() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  // TMA: native back button navigates to the character list
  useTelegramBackButton(() => navigate('/discover'));
  const { user, refreshUser, isAuthenticated } = useAuth();
  useGeoContext();
  const {
    currentCharacter,
    setCurrentCharacter,
    messages,
    sessionId,
    isLoading: isSessionLoading,
    isTyping,
    sendMessage,
    preloadSession,
    addLocalMessage,
    updateLocalMessage,
    // PRD v3: Scene gameplay
    sceneChoices,
    clearSceneChoices,
    // Story completion
    storyCompletedData,
    clearStoryCompletedData,
    // Scene banner
    sceneBanner,
    ageVerificationRequired,
    ageVerificationMessage,
    clearAgeVerificationRequired,
    showInsufficientCreditsModal,
    intimacy,
    relationshipStage,
    relationshipDashboard,
  } = useChatContext();

  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [loadingCharacter, setLoadingCharacter] = useState(false);
  const [mediaIndex, setMediaIndex] = useState(0);
  const [error, setError] = useState('');
  const [isGalleryOpen, setIsGalleryOpen] = useState(false);
  // PRD v2026.02: Relationship locking
  const [showRelationshipLockModal, setShowRelationshipLockModal] = useState(false);
  const [lockingRelationship, setLockingRelationship] = useState(false);
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const [leftPanelWidth, setLeftPanelWidth] = useState(320);
  const [rightPanelWidth, setRightPanelWidth] = useState(320);
  const [resizingPanel, setResizingPanel] = useState<'left' | 'right' | null>(null);
  const [isDesktopNavCollapsed, setIsDesktopNavCollapsed] = useState(false);
  const [isMobileActionsOpen, setIsMobileActionsOpen] = useState(false);
  const [isLanguageModalOpen, setIsLanguageModalOpen] = useState(false);
  const [isCommingSoonModalOpen, setIsCommingSoonModalOpen] = useState(false);
  const isAdultMode = true;
  const [isRealtimeCallOpen, setIsRealtimeCallOpen] = useState(false);
  const desktopLayoutRef = useRef<HTMLDivElement | null>(null);
  const mediaTouchStartXRef = useRef<number | null>(null);
  const desktopNavWidth = isDesktopNavCollapsed ? 82 : 220;
  const { slug } = useParams<{ slug?: string }>();
  // slug-based route: resolve character ID from slug before using it
  const [slugResolvedId, setSlugResolvedId] = useState<string | null>(null);
  useEffect(() => {
    if (!slug) return;
    api.get<{ id: string }>(`/characters/by-slug/${slug}`)
      .then((r) => setSlugResolvedId(r.data.id))
      .catch(() => setSlugResolvedId(null));
  }, [slug]);

  const characterIdFromUrl = slug ? slugResolvedId : searchParams.get('character');
  const failedCharacterLoadRef = useRef<string | null>(null);
  const prewarmKeyRef = useRef<string | null>(null);

  useEffect(() => {
    const mobileBreakpoint = window.matchMedia('(max-width: 1023px)');
    const noActiveCharacter = !characterIdFromUrl && !currentCharacter;

    if (mobileBreakpoint.matches && noActiveCharacter) {
      setIsMobileSidebarOpen(true);
    }
  }, [characterIdFromUrl, currentCharacter]);

  const imagePromptTemplates = useMemo(() => {
    const characterName = currentCharacter?.first_name || 'the character';
    return [
      `Portrait photo, ${characterName}, soft cinematic lighting, upper body, looking at camera, detailed skin, shallow depth of field, high quality.`,
      `Full body fashion image, ${characterName}, street style outfit, confident pose, urban background, natural light, ultra-detailed, 4k.`,
      `Romantic scene image, ${characterName}, warm golden-hour light, elegant dress, gentle smile, bokeh lights, photo-realistic.`,
      `Anime-style character art, ${characterName}, dynamic pose, vivid colors, clean linework, detailed face, studio quality.`,
      `Beach vacation photo, ${characterName}, summer outfit, wind in hair, sunset sky, realistic shadows, high-resolution image.`,
      `Indoor cozy portrait, ${characterName}, casual sweater, window light, candid expression, cinematic color grading, detailed image.`,
    ];
  }, [currentCharacter?.first_name]);

  useEffect(() => {
    const leftSaved = Number(window.localStorage.getItem('chat_left_panel_width'));
    const rightSaved = Number(window.localStorage.getItem('chat_right_panel_width'));
    const navCollapsedSaved = window.localStorage.getItem('chat_left_nav_collapsed');
    if (Number.isFinite(leftSaved) && leftSaved >= 260 && leftSaved <= 520) {
      setLeftPanelWidth(leftSaved);
    }
    if (Number.isFinite(rightSaved) && rightSaved >= 260 && rightSaved <= 520) {
      setRightPanelWidth(rightSaved);
    }
    if (navCollapsedSaved === '1') {
      setIsDesktopNavCollapsed(true);
    }
  }, []);

  const currentCharacterWithMedia = currentCharacter as CharacterWithExtraMedia | null;
  const characterAvatarUrl =
    currentCharacter?.profile_image_url ||
    currentCharacter?.media_urls?.avatar ||
    currentCharacterWithMedia?.avatar_url;

  const mediaItems = useMemo<CharacterMediaItem[]>(() => {
    if (!currentCharacter || !currentCharacterWithMedia) return [];

    const media: CharacterMediaItem[] = [];
    const seen = new Set<string>();
    const pushUnique = (type: 'image' | 'video', url?: string | null) => {
      if (!url) return;
      const cleaned = url.trim();
      if (!cleaned || seen.has(cleaned)) return;
      seen.add(cleaned);
      media.push({ type, url: cleaned });
    };

    // Guests: only SFW avatar. Authenticated users: SFW + Mature image + Mature video.
    pushUnique('image', characterAvatarUrl);

    if (isAuthenticated) {
      pushUnique(
        'image',
        currentCharacterWithMedia.mature_image_url || currentCharacterWithMedia.mature_cover_url
      );
      pushUnique('video', currentCharacterWithMedia.mature_video_url);
    }

    return media;
  }, [characterAvatarUrl, currentCharacter, currentCharacterWithMedia, isAuthenticated]);

  useEffect(() => {
    setMediaIndex(0);
  }, [currentCharacter?.id]);

  const activeMedia =
    mediaItems[Math.min(mediaIndex, Math.max(mediaItems.length - 1, 0))] || null;

  const showPreviousMedia = () => {
    if (mediaItems.length <= 1) return;
    setMediaIndex((prev) => (prev - 1 + mediaItems.length) % mediaItems.length);
  };

  const showNextMedia = () => {
    if (mediaItems.length <= 1) return;
    setMediaIndex((prev) => (prev + 1) % mediaItems.length);
  };

  const handleMediaTouchStart = (event: React.TouchEvent<HTMLDivElement>) => {
    mediaTouchStartXRef.current = event.touches[0]?.clientX ?? null;
  };

  const handleMediaTouchEnd = (event: React.TouchEvent<HTMLDivElement>) => {
    const startX = mediaTouchStartXRef.current;
    mediaTouchStartXRef.current = null;
    if (startX == null || mediaItems.length <= 1) return;
    const endX = event.changedTouches[0]?.clientX ?? startX;
    const deltaX = endX - startX;
    const swipeThreshold = 40;
    if (Math.abs(deltaX) < swipeThreshold) return;
    if (deltaX > 0) {
      showPreviousMedia();
    } else {
      showNextMedia();
    }
  };
  const safeCharacterAvatar = getSafeAvatarUrl(characterAvatarUrl);
  const generatedVideoBaseImages = useMemo<string[]>(() => {
    if (!currentCharacter) return [];
    const seen = new Set<string>();
    const images: string[] = [];
    // Prefer latest generated images from current chat for this character.
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      const msg = messages[i];
      if (msg.role !== 'assistant') continue;
      if (!msg.image_url) continue;
      if (msg.character_id && msg.character_id !== currentCharacter.id) continue;
      const url = msg.image_url.trim();
      if (!url || seen.has(url)) continue;
      seen.add(url);
      images.push(url);
    }
    return images;
  }, [currentCharacter, messages]);

  // Load character from URL parameter.
  // Fire session init and character fetch concurrently. Session init only needs
  // character_id, which is already known from the URL.
  const loadingCharacterIdRef = useRef<string | null>(null);
  useEffect(() => {
    const characterId = characterIdFromUrl;
    if (!characterId) return;
    if (failedCharacterLoadRef.current === characterId) return;
    if (currentCharacter) return;
    if (loadingCharacterIdRef.current !== characterId) {
      loadingCharacterIdRef.current = characterId;
      // Kick off session init immediately (parallel with character detail fetch)
      preloadSession(characterId);
      loadCharacter(characterId).finally(() => {
        loadingCharacterIdRef.current = null;
      });
    }
  }, [characterIdFromUrl, currentCharacter, preloadSession]);

  const loadCharacter = async (characterId: string) => {
    setLoadingCharacter(true);
    setError('');

    const normalizeCharacter = (data: any) => {
      const sanitize = (u?: string) => (typeof u === 'string' ? u.replace(/`/g, '').trim() : undefined);
      const pvRaw = typeof data?.video_url === 'object' ? data.video_url : data.profile_videos;
      const pv = pvRaw
        ? {
            IDLE_VIDEO_URL: sanitize(pvRaw.IDLE_VIDEO_URL) || pvRaw.IDLE_VIDEO_URL,
            TALKING_VIDEO_URL: sanitize(pvRaw.TALKING_VIDEO_URL) || pvRaw.TALKING_VIDEO_URL,
          }
        : undefined;
      return { ...data, profile_videos: pv };
    };

    try {
      // Add 15s timeout to prevent infinite loading
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timed out')), 15000)
      );

      const response = await Promise.race([
        api.get<Character>(`/characters/${characterId}`),
        timeoutPromise
      ]) as any;

      const data: any = response.data;
      failedCharacterLoadRef.current = null;
      setCurrentCharacter(normalizeCharacter(data));
    } catch (err: any) {
      failedCharacterLoadRef.current = characterId;
      console.error('Failed to load character:', err);
      setError('Failed to load character. Please try again or select another character.');
    } finally {
      setLoadingCharacter(false);
    }
  };
  const handleSelectCharacter = (character: Character) => {
    setCurrentCharacter(character);
    setMediaIndex(0);
    setIsRealtimeCallOpen(false);
    // Update URL
    navigate(`/chat?character=${character.id}`, { replace: true });
  };

  const handleSendMessage = async (
    content: string,
    options?: { immediate?: boolean }
  ) => {
    setError('');

    // PRD v2026.02: Check if relationship needs to be locked
    if (
      currentCharacter &&
      !currentCharacter.relationship_locked &&
      currentCharacter.relationship_role &&
      currentCharacter.user_role &&
      messages.length === 0 // First message
    ) {
      // Show lock confirmation modal
      setPendingMessage(content);
      setShowRelationshipLockModal(true);
      return;
    }

    try {
      await sendMessage(content, { ...options, voiceMode: 'auto', isAdultMode });
    } catch (err: any) {
      console.error('Failed to send message:', err);
      setError('Failed to send message. Please try again.');
    }
  };

  const handleCompleteText = async (draft: string): Promise<string> => {
    const normalized = draft.trim();
    if (!normalized || !currentCharacter) return draft;

    try {
      const response = await api.post<{ completed_text: string }>('/chat/complete-text', {
        character_id: currentCharacter.id,
        message: normalized,
      });
      return response.data.completed_text || draft;
    } catch (err) {
      console.error('Failed to complete text:', err);
      setError('AI complete failed. Please try again.');
      return draft;
    }
  };

  // Pre-warm critical dependencies on chat entry.
  useEffect(() => {
    if (!isAuthenticated) {
      prewarmKeyRef.current = null;
      return;
    }

    const characterId = characterIdFromUrl;
    const prewarmKey = characterId || '__no_character__';
    if (prewarmKeyRef.current === prewarmKey) return;
    prewarmKeyRef.current = prewarmKey;

    if (characterId) {
      preloadSession(characterId);
    }

    void Promise.allSettled([
      refreshUser(),
      notificationService.connect(),
    ]);
  }, [isAuthenticated, characterIdFromUrl, preloadSession, refreshUser]);

  const handleGenerateImage = async (prompt: string, poseImageUrl?: string, loraId?: string) => {
    const normalized = prompt.trim();
    if (!normalized || !currentCharacter) return;

    const tempId = `fal-gen-${Date.now()}`;

    // Show user prompt bubble
    addLocalMessage({
      id: `${tempId}-user`,
      role: 'user',
      content: `Generate: ${normalized}`,
      timestamp: new Date().toISOString(),
      character_id: currentCharacter.id,
    });

    // Show generating placeholder
    addLocalMessage({
      id: tempId,
      role: 'assistant',
      content: 'Generating image...',
      timestamp: new Date().toISOString(),
      character_id: currentCharacter.id,
      metadata: { fal_local: true },
    });

    try {
      const isPoseRequest = Boolean(poseImageUrl);
      // With a LoRA or without pose: use Novita img2img (JuggernautXL Lightning).
      // With a pose reference image only: use the existing OpenPose + InstantID path.
      const endpoint = isPoseRequest
        ? '/images/generate-pose-mature'
        : '/images/generate-mature-lora';

      const response = await api.post<{ task_id: string; status: string }>(
        endpoint,
        isPoseRequest
          ? {
              prompt: normalized,
              character_id: currentCharacter.id,
              pose_image_url: poseImageUrl,
              session_id: sessionId,
              lora_id: loraId ?? null,
            }
          : {
              prompt: normalized,
              character_id: currentCharacter.id,
              session_id: sessionId,
              lora_id: loraId ?? null,
            }
      );
      await refreshUser();

      const { task_id } = response.data;

      // Primary: SSE notification. Backup: delayed HTTP polling. Timeout: 6 min.
      const TIMEOUT_MS = 360_000;
      const FALLBACK_POLL_DELAY_MS = 30_000;
      const FALLBACK_POLL_INTERVAL_MS = 5_000;
      let resolved = false;
      let pollFallbackTimer: ReturnType<typeof setTimeout> | null = null;
      let pollInterval: ReturnType<typeof setInterval> | null = null;

      const cleanup = () => {
        resolved = true;
        unsubDone();
        unsubFailed();
        if (pollFallbackTimer) clearTimeout(pollFallbackTimer);
        if (pollInterval) clearInterval(pollInterval);
        clearTimeout(timeoutId);
      };

      const unsubDone = notificationService.on('image_done', (data) => {
        if (data.message_id !== task_id || resolved) return;
        cleanup();
        updateLocalMessage(tempId, {
          content: '',
          image_url: data.image_url,
          metadata: { fal_local: true },
        });
      });

      const unsubFailed = notificationService.on('image_failed', (data) => {
        if (data.task_id !== task_id || resolved) return;
        cleanup();
        updateLocalMessage(tempId, { content: data.error || 'Image generation failed.' });
      });

      const pollOnce = async () => {
        if (resolved) return;
        try {
          const res = await api.get<{ status: string; result?: { data?: string } }>(
            `/images/tasks/${task_id}`
          );
          const { status, result } = res.data;
          const normalizedStatus = normalizeTaskStatus(status);
          if (normalizedStatus === 'succeeded' && result?.data) {
            cleanup();
            updateLocalMessage(tempId, {
              content: '',
              image_url: result.data,
              metadata: { fal_local: true },
            });
          } else if (normalizedStatus === 'failed') {
            cleanup();
            updateLocalMessage(tempId, { content: 'Image generation failed.' });
          }
        } catch {
          // Ignore poll errors — SSE remains active
        }
      };

      pollFallbackTimer = setTimeout(() => {
        if (resolved) return;
        void pollOnce();
        pollInterval = setInterval(pollOnce, FALLBACK_POLL_INTERVAL_MS);
      }, FALLBACK_POLL_DELAY_MS);

      const timeoutId = setTimeout(() => {
        if (!resolved) {
          cleanup();
          updateLocalMessage(tempId, { content: 'Image generation timed out. Please try again.' });
        }
      }, TIMEOUT_MS);
    } catch (err: any) {
      const insufficientCredits = getInsufficientCreditsInfo(err);
      if (insufficientCredits) {
        showInsufficientCreditsModal(insufficientCredits.required, insufficientCredits.available);
      }
      updateLocalMessage(tempId, {
        content: getErrorMessage(err, 'Image generation failed. Please try again.'),
      });
    }
  };

  const handleGenerateVideo = async (
    prompt: string,
    action?: VideoLoraAction,
    baseImageUrl?: string
  ) => {
    const normalized = prompt.trim();
    if (!normalized || !currentCharacter) return;
    if (!baseImageUrl) {
      alert('Please select a generated image as the base image.');
      return;
    }

    const tempId = `hunyuan-gen-${Date.now()}`;

    addLocalMessage({
      id: `${tempId}-user`,
      role: 'user',
      content: `Generate video: ${normalized}`,
      timestamp: new Date().toISOString(),
      character_id: currentCharacter.id,
    });

    addLocalMessage({
      id: tempId,
      role: 'assistant',
      content: 'Generating video...',
      timestamp: new Date().toISOString(),
      character_id: currentCharacter.id,
      metadata: { video_local: true },
    });

    try {
      const response = await api.post<{ task_id: string; status: string }>(
        '/images/generate-video-wan-character',
        {
          prompt: normalized,
          character_id: currentCharacter.id,
          session_id: sessionId,
          image_url: baseImageUrl,
          lora_preset_id: action?.lora_preset_id,
          selected_trigger_word: action?.trigger_word,
        }
      );
      await refreshUser();

      const { task_id } = response.data;
      const TIMEOUT_MS = 360_000;
      const FALLBACK_POLL_DELAY_MS = 30_000;
      const FALLBACK_POLL_INTERVAL_MS = 5_000;
      let resolved = false;
      let pollFallbackTimer: ReturnType<typeof setTimeout> | null = null;
      let pollInterval: ReturnType<typeof setInterval> | null = null;

      const cleanup = () => {
        resolved = true;
        unsubDone();
        unsubFailed();
        if (pollFallbackTimer) clearTimeout(pollFallbackTimer);
        if (pollInterval) clearInterval(pollInterval);
        clearTimeout(timeoutId);
      };

      const unsubDone = notificationService.on('video_completed', (data) => {
        if (data.task_id !== task_id || resolved) return;
        cleanup();
        updateLocalMessage(tempId, {
          content: '',
          video_url: data.video_url,
          metadata: { video_local: true },
        });
      });

      const unsubFailed = notificationService.on('video_failed', (data) => {
        if (data.task_id !== task_id || resolved) return;
        cleanup();
        updateLocalMessage(tempId, { content: data.error || 'Video generation failed.' });
      });

      const pollOnce = async () => {
        if (resolved) return;
        try {
          const res = await api.get<{ status: string; result?: { data?: string; video_url?: string } }>(
            `/images/tasks/${task_id}`
          );
          const status = normalizeTaskStatus(res.data?.status);
          if (status === 'succeeded') {
            const videoUrl = res.data?.result?.video_url || res.data?.result?.data;
            if (videoUrl) {
              cleanup();
              updateLocalMessage(tempId, {
                content: '',
                video_url: videoUrl,
                metadata: { video_local: true },
              });
            }
            return;
          }
          if (status === 'failed') {
            cleanup();
            updateLocalMessage(tempId, { content: 'Video generation failed.' });
          }
        } catch {
          // keep polling
        }
      };

      pollFallbackTimer = setTimeout(() => {
        if (resolved) return;
        void pollOnce();
        pollInterval = setInterval(pollOnce, FALLBACK_POLL_INTERVAL_MS);
      }, FALLBACK_POLL_DELAY_MS);

      const timeoutId = setTimeout(() => {
        if (resolved) return;
        cleanup();
        updateLocalMessage(tempId, {
          content: 'Video generation timed out. Please try again.',
        });
      }, TIMEOUT_MS);
    } catch (err: any) {
      const insufficientCredits = getInsufficientCreditsInfo(err);
      if (insufficientCredits) {
        showInsufficientCreditsModal(insufficientCredits.required, insufficientCredits.available);
      }
      updateLocalMessage(tempId, {
        content: getErrorMessage(err, 'Video generation failed. Please try again.'),
      });
    }
  };

  const handleConfirmLock = async () => {
    if (!currentCharacter) return;

    try {
      setLockingRelationship(true);

      // Call lock endpoint
      const response = await api.post(
        `/characters/${currentCharacter.id}/lock-relationship`,
        null,
        {
          params: {
            relationship_role: currentCharacter.relationship_role,
            user_role: currentCharacter.user_role,
          },
        }
      );

      if (response.data.success) {
        // Update character state to reflect lock
        setCurrentCharacter({
          ...currentCharacter,
          relationship_locked: true,
          relationship_locked_at: response.data.locked_at,
        });

        // Close modal
        setShowRelationshipLockModal(false);

        // Send pending message
        if (pendingMessage) {
          await sendMessage(pendingMessage, { voiceMode: 'auto', isAdultMode });
          setPendingMessage(null);
        }
      }
    } catch (err: any) {
      console.error('Failed to lock relationship:', err);
      setError('Failed to lock relationship. Please try again.');
    } finally {
      setLockingRelationship(false);
    }
  };

  const handleCancelLock = () => {
    setShowRelationshipLockModal(false);
    setPendingMessage(null);
  };

  // PRD v3: Scene choice selection
  const handleSceneChoiceSelect = (choice: string) => {
    handleSendMessage(choice);
    clearSceneChoices();
  };

  useEffect(() => {
    if (!resizingPanel) return;

    const onMouseMove = (event: MouseEvent) => {
      const layout = desktopLayoutRef.current;
      if (!layout) return;

      const rect = layout.getBoundingClientRect();
      const isDesktop = window.innerWidth >= 1024;
      if (!isDesktop) return;

      const iconRailWidth = desktopNavWidth;
      const minLeft = 260;
      const minRight = 260;
      const minCenter = 420;
      const available = rect.width - iconRailWidth;

      if (resizingPanel === 'left') {
        const proposed = event.clientX - rect.left - iconRailWidth;
        const maxLeft = Math.max(minLeft, available - rightPanelWidth - minCenter);
        const next = Math.min(Math.max(proposed, minLeft), maxLeft);
        setLeftPanelWidth(next);
        window.localStorage.setItem('chat_left_panel_width', String(Math.round(next)));
      } else {
        const proposed = rect.right - event.clientX;
        const maxRight = Math.max(minRight, available - leftPanelWidth - minCenter);
        const next = Math.min(Math.max(proposed, minRight), maxRight);
        setRightPanelWidth(next);
        window.localStorage.setItem('chat_right_panel_width', String(Math.round(next)));
      }
    };

    const onMouseUp = () => {
      setResizingPanel(null);
    };

    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    return () => {
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [desktopNavWidth, leftPanelWidth, rightPanelWidth, resizingPanel]);

  const navItems = [
    { label: 'Home', icon: Home, onClick: () => navigate('/') },
    { label: 'Discover', icon: Compass, onClick: () => navigate('/discover') },
    { label: 'Chat', icon: MessageCircle, onClick: () => navigate('/chat'), active: true },
    { label: 'Collection', icon: BookHeart, onClick: () => navigate('/collection') },
    { label: 'Generate Image', icon: ImagePlus, onClick: () => navigate('/generate-image') },
    { label: 'Create Character', icon: WandSparkles, onClick: () => navigate('/create-character') },
    { label: 'My AI', icon: UserCircle2, onClick: () => navigate('/characters') },
    { label: 'Premium', icon: CircleDollarSign, onClick: () => navigate('/subscriptions') },
  ];

  const settingItems = [
    { label: 'English', icon: Globe2, onClick: () => setIsLanguageModalOpen(true) },
    { label: 'Discord', icon: MessageCircle, onClick: () => {} },
    { label: 'Help Center', icon: HelpCircle, onClick: () => navigate('/faq') },
    { label: 'Contact Us', icon: Contact, onClick: () => window.open('mailto:support@roxyclub.ai', '_self') },
    { label: 'Affiliate', icon: Trophy, onClick: () => {} },
  ];

  const toggleDesktopNav = () => {
    const next = !isDesktopNavCollapsed;
    setIsDesktopNavCollapsed(next);
    window.localStorage.setItem('chat_left_nav_collapsed', next ? '1' : '0');
  };

  return (
    <div className="relative z-20 flex h-full min-h-[100dvh] w-full flex-col overflow-hidden">
      {/* Top Bar */}
      <div className="relative bg-zinc-900 border-b border-white/10 px-2 sm:px-4 py-2 sm:py-3 flex items-center gap-2 sm:gap-4 flex-shrink-0">
        {/* Mobile Menu Button */}
        <button
          type="button"
          onClick={() => setIsMobileSidebarOpen((prev) => !prev)}
          className="text-zinc-400 hover:text-white lg:hidden"
          aria-label="Toggle chat list"
          aria-expanded={isMobileSidebarOpen}
        >
          <Menu size={24} />
        </button>

        {/* Home Button */}
        <button
          onClick={() => navigate('/')}
          className="text-zinc-400 hover:text-white lg:hidden"
          title="Back to Home"
        >
          <Home size={24} />
        </button>

        {/* Desktop Nav Collapse Button (moved from left sidebar) */}
        <button
          onClick={toggleDesktopNav}
          className="hidden lg:inline-flex text-zinc-300 hover:text-white"
          title={isDesktopNavCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <Menu size={22} />
        </button>

        {/* Brand */}
        <button
          onClick={() => navigate('/')}
          className="flex-1 min-w-0 text-left font-heading font-bold text-[0.625rem] leading-none text-white hover:text-zinc-100 transition-colors sm:text-sm sm:leading-normal lg:text-lg"
          title="Go to Home"
        >
          RoxyClub.ai
        </button>

        {/* Action Buttons */}
        <div className="flex shrink-0 items-center gap-2">
          {/* Credits Display */}
          <div className="flex h-9 shrink-0 items-center gap-1 rounded-full border border-yellow-500/20 bg-yellow-500/10 px-2 text-yellow-500 sm:h-auto sm:gap-1.5 sm:px-3 sm:py-1.5">
            <Coins size={14} className="sm:w-4 sm:h-4" />
            <span className="font-medium text-xs sm:text-sm">{user?.credits || 0}</span>
          </div>
          <button
            type="button"
            onClick={() => setIsMobileActionsOpen((prev) => !prev)}
            className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/5 text-zinc-200 hover:bg-white/10 hover:text-white lg:hidden"
            aria-label="Open chat actions"
            aria-expanded={isMobileActionsOpen}
          >
            <MoreVertical size={18} />
          </button>
          <Button
            variant="outline"
            size="sm"
            className="hidden h-9 shrink-0 items-center gap-2 p-2 sm:h-auto sm:px-3 lg:flex"
            onClick={() => navigate('/billing')}
            title="Buy Credits"
          >
            <CircleDollarSign size={16} />
            <span className="hidden sm:inline">Buy Credits</span>
          </Button>

          {currentCharacter && (
            <>
              {/* Gallery Button */}
              <Button
                variant="outline"
                size="sm"
                className="hidden h-9 shrink-0 items-center gap-2 p-2 sm:h-auto sm:px-3 lg:flex"
                onClick={() => setIsGalleryOpen(true)}
                title="Gallery"
              >
                <Image size={16} />
                <span className="hidden sm:inline">Gallery</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="hidden h-9 shrink-0 items-center gap-2 p-2 sm:h-auto sm:px-3 lg:flex"
                onClick={() => setShowConsentModal(true)}
                title="Explicit Consent"
              >
                <ShieldCheck size={16} />
                <span className="hidden sm:inline">Consent</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsRealtimeCallOpen(true)}
                disabled={!currentCharacter || !sessionId || isSessionLoading}
                className="hidden h-9 shrink-0 items-center gap-2 p-2 sm:h-auto sm:px-3 lg:flex"
                title="通话"
              >
                <Video size={16} />
                <span className="hidden sm:inline">通话</span>
              </Button>

            </>
          )}
        </div>

        {isMobileActionsOpen && (
          <div className="absolute right-2 top-[calc(100%+0.5rem)] z-50 w-52 overflow-hidden rounded-lg border border-white/10 bg-zinc-950 shadow-xl shadow-black/40 lg:hidden">
            <button
              type="button"
              onClick={() => {
                setIsMobileActionsOpen(false);
                navigate('/billing');
              }}
              className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm text-zinc-200 hover:bg-white/10 hover:text-white"
            >
              <CircleDollarSign size={16} />
              <span>Buy Credits</span>
            </button>
            {currentCharacter && (
              <>
                <button
                  type="button"
                  onClick={() => {
                    setIsMobileActionsOpen(false);
                    setIsGalleryOpen(true);
                  }}
                  className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm text-zinc-200 hover:bg-white/10 hover:text-white"
                >
                  <Image size={16} />
                  <span>Gallery</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsMobileActionsOpen(false);
                    setShowConsentModal(true);
                  }}
                  className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm text-zinc-200 hover:bg-white/10 hover:text-white"
                >
                  <ShieldCheck size={16} />
                  <span>Consent</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsMobileActionsOpen(false);
                    setIsRealtimeCallOpen(true);
                  }}
                  disabled={!currentCharacter || !sessionId || isSessionLoading}
                  className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm text-zinc-200 hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:text-zinc-600 disabled:hover:bg-transparent"
                >
                  <Video size={16} />
                  <span>Call</span>
                </button>
              </>
            )}
          </div>
        )}
      </div>

      <div ref={desktopLayoutRef} className="flex-1 flex overflow-hidden bg-black">
        {/* Desktop Left Navbar */}
        <aside
          className="hidden lg:flex border-r border-white/10 bg-[#0a0b0f] flex-col transition-all duration-200"
          style={{ width: `${desktopNavWidth}px` }}
        >
          <div className="px-3 pt-4 pb-3 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.label}
                  onClick={item.onClick}
                  title={item.label}
                  className={`w-full rounded-xl border transition-colors ${
                    isDesktopNavCollapsed
                      ? 'h-10 flex items-center justify-center'
                      : 'px-3 py-2 text-sm flex items-center gap-2'
                  } ${
                    item.active
                      ? 'bg-zinc-700/40 border-zinc-500/70 text-white'
                      : 'border-white/10 text-zinc-300 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <Icon size={15} />
                  {!isDesktopNavCollapsed && <span>{item.label}</span>}
                </button>
              );
            })}
          </div>

          <div className="mt-auto p-3 space-y-2 border-t border-white/10">
            {settingItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.label}
                  onClick={item.onClick}
                  title={item.label}
                  className={`w-full rounded-xl border border-white/10 text-zinc-300 hover:bg-white/5 hover:text-white transition-colors ${
                    isDesktopNavCollapsed
                      ? 'h-10 flex items-center justify-center'
                      : 'px-3 py-2 text-sm flex items-center gap-2'
                  }`}
                >
                  <Icon size={15} />
                  {!isDesktopNavCollapsed && <span>{item.label}</span>}
                </button>
              );
            })}
            {!isDesktopNavCollapsed && (
              <div className="pt-2 text-[10px] text-zinc-500">Privacy Notice | Terms of Service</div>
            )}
          </div>
        </aside>

        {/* Character Sidebar / Chat List */}
        <div className="hidden lg:block shrink-0" style={{ width: `${leftPanelWidth}px` }}>
          <CharacterSelector
            currentCharacterId={currentCharacter?.id}
            currentCharacter={currentCharacter}
            onSelectCharacter={handleSelectCharacter}
            isMobileOpen={isMobileSidebarOpen}
            onMobileClose={() => setIsMobileSidebarOpen(false)}
            disabled={isTyping}
            className="lg:w-full"
          />
        </div>
        <CharacterSelector
          currentCharacterId={currentCharacter?.id}
          currentCharacter={currentCharacter}
          onSelectCharacter={handleSelectCharacter}
          isMobileOpen={isMobileSidebarOpen}
          onMobileClose={() => setIsMobileSidebarOpen(false)}
          disabled={isTyping}
          className="lg:hidden"
        />

        <div
          className="hidden lg:block w-1 cursor-col-resize bg-white/5 hover:bg-primary-500/40 transition-colors"
          onMouseDown={() => setResizingPanel('left')}
          onDoubleClick={() => {
            setLeftPanelWidth(320);
            window.localStorage.setItem('chat_left_panel_width', '320');
          }}
          title="Drag to resize chat list"
        />

        {/* Mobile Sidebar Overlay */}
        {isMobileSidebarOpen && (
          <div
            onClick={() => setIsMobileSidebarOpen(false)}
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          />
        )}

        {/* Main Chat Area */}
        <div className="relative flex-1 min-w-[420px] flex flex-col overflow-hidden bg-black">
          {safeCharacterAvatar && (
            <div
              className="absolute inset-0 lg:hidden bg-cover bg-center bg-no-repeat opacity-50 pointer-events-none"
              style={{ backgroundImage: `url(${safeCharacterAvatar})` }}
            />
          )}
          {loadingCharacter || (currentCharacter && isSessionLoading) ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-4">
                <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                <p className="text-zinc-400">
                  {loadingCharacter ? 'Loading character...' : 'Preparing chat...'}
                </p>
              </div>
            </div>
          ) : !currentCharacter ? (
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="text-center space-y-6 max-w-md">
                <div className="w-20 h-20 bg-gradient-primary rounded-full flex items-center justify-center mx-auto">
                  <Sparkles size={32} className="text-white" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-2xl font-heading font-bold text-white">
                    Welcome to AI Companion
                  </h2>
                  <p className="text-zinc-400">
                    Select a character from the chat list to start chatting
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="relative z-10 flex-1 flex flex-col min-h-0">
              {/* Error Message */}
              {error && (
                <div className="mx-4 mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/50 flex items-start gap-2">
                  <AlertCircle size={20} className="text-red-500 flex-shrink-0 mt-0.5" />
                  <p className="text-red-500 text-sm">{error}</p>
                </div>
              )}

              {/* Scene Banner (script scene / recap) */}
              {sceneBanner && (
                <SceneBanner
                  scene={sceneBanner.scene}
                  synopsis={sceneBanner.synopsis}
                  characterName={currentCharacter.first_name}
                />
              )}

              <div className="px-3 pt-2 pb-1 lg:hidden">
                <div className="rounded-xl border border-white/10 bg-zinc-900/70 p-3">
                  <div className="grid grid-cols-4 gap-2 text-center">
                    <div>
                      <div className="text-[11px] text-zinc-400">Intimacy</div>
                      <div className="text-sm font-semibold text-pink-400">{intimacy}</div>
                    </div>
                    <div>
                      <div className="text-[11px] text-zinc-400">Trust</div>
                      <div className="text-sm font-semibold text-emerald-400">{relationshipDashboard.trust}</div>
                    </div>
                    <div>
                      <div className="text-[11px] text-zinc-400">Desire</div>
                      <div className="text-sm font-semibold text-rose-400">{relationshipDashboard.desire}</div>
                    </div>
                    <div>
                      <div className="text-[11px] text-zinc-400">Stage</div>
                      <div className="text-sm font-semibold text-white">{relationshipStage}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <MessageList
                messages={messages}
                isTyping={isTyping}
                characterName={currentCharacter.first_name}
                characterAvatar={safeCharacterAvatar}
                sessionId={sessionId || undefined}
              />

              {/* PRD v3: Scene Choices (priority over regular suggestions) */}
              {sceneChoices && sceneChoices.choices.length > 0 && (
                <SceneChoices
                  choices={sceneChoices.choices}
                  onSelect={handleSceneChoiceSelect}
                  disabled={isTyping || isSessionLoading}
                  sceneInfo={sceneChoices.sceneState}
                />
              )}

              {/* Chat Input */}
              <ChatInput
                onSend={handleSendMessage}
                onCompleteText={handleCompleteText}
                onGenerateImage={handleGenerateImage}
                onGenerateVideo={handleGenerateVideo}
                generatedVideoBaseImages={generatedVideoBaseImages}
                imagePromptTemplates={imagePromptTemplates}
                disabled={isSessionLoading || !currentCharacter}
                placeholder={`Message ${currentCharacter.first_name}...`}
              />
            </div>
          )}
        </div>

        {/* Desktop Character Detail Panel */}
        <div
          className="hidden lg:block w-1 cursor-col-resize bg-white/5 hover:bg-primary-500/40 transition-colors"
          onMouseDown={() => setResizingPanel('right')}
          onDoubleClick={() => {
            setRightPanelWidth(320);
            window.localStorage.setItem('chat_right_panel_width', '320');
          }}
          title="Drag to resize character panel"
        />

        <aside
          className="hidden lg:flex border-l border-white/10 bg-zinc-950 flex-col shrink-0"
          style={{ width: `${rightPanelWidth}px` }}
        >
          <div className="p-4 border-b border-white/10">
            <h3 className="text-sm uppercase tracking-wide text-zinc-400">Character</h3>
            <p className="text-lg font-semibold text-white mt-1 truncate">
              {currentCharacter?.first_name || 'No character selected'}
            </p>
          </div>

          <div className="p-4 flex-1 overflow-y-auto space-y-4">
            <div
              className="relative rounded-xl overflow-hidden bg-black border border-white/10"
              onTouchStart={handleMediaTouchStart}
              onTouchEnd={handleMediaTouchEnd}
            >
              {activeMedia ? (
                activeMedia.type === 'video' ? (
                  <video
                    src={activeMedia.url}
                    controls
                    className="w-full aspect-[3/4] object-cover bg-black"
                  />
                ) : (
                  <img
                    src={activeMedia.url}
                    alt={currentCharacter?.first_name || 'Character media'}
                    className="w-full aspect-[3/4] object-cover bg-black"
                  />
                )
              ) : (
                <div className="w-full aspect-[3/4] flex items-center justify-center text-zinc-500">
                  No media
                </div>
              )}

              {mediaItems.length > 1 && (
                <>
                  <button
                    onClick={showPreviousMedia}
                    className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/60 border border-white/20 text-white flex items-center justify-center hover:bg-black/80"
                    title="Previous media"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <button
                    onClick={showNextMedia}
                    className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/60 border border-white/20 text-white flex items-center justify-center hover:bg-black/80"
                    title="Next media"
                  >
                    <ChevronRight size={16} />
                  </button>
                </>
              )}
            </div>

            {activeMedia && (
              <div className="text-xs text-zinc-400 flex items-center gap-2">
                {activeMedia.type === 'video' ? <Video size={14} /> : <Image size={14} />}
                <span>{mediaIndex + 1}/{mediaItems.length || 1}</span>
              </div>
            )}

            <div className="rounded-xl border border-white/10 bg-zinc-900/70 p-4">
              <h4 className="text-sm font-semibold text-white mb-2">Description</h4>
              <p className="text-sm text-zinc-300 whitespace-pre-line">
                {currentCharacter
                  ? formatCharacterDescription(currentCharacter) || 'No background story available.'
                  : ''}
              </p>
            </div>

            <RelationshipDashboardCard
              stage={relationshipStage}
              intimacy={intimacy}
              trust={relationshipDashboard.trust}
              desire={relationshipDashboard.desire}
              dependency={relationshipDashboard.dependency}
            />
          </div>
        </aside>
      </div>
      
      {currentCharacter && (
        <RealtimeCallModal
          isOpen={isRealtimeCallOpen}
          characterId={currentCharacter.id}
          sessionId={sessionId}
          characterName={currentCharacter.first_name}
          onClose={() => setIsRealtimeCallOpen(false)}
        />
      )}

      {/* Gallery Modal */}
      <GalleryModal
        isOpen={isGalleryOpen}
        onClose={() => setIsGalleryOpen(false)}
        characterId={currentCharacter?.id || ''}
        characterName={currentCharacter?.first_name || ''}
      />

      {/* Story Completion Modal */}
      {storyCompletedData && sessionId && (
        <StoryCompletionModal
          data={storyCompletedData}
          sessionId={sessionId}
          onClose={clearStoryCompletedData}
        />
      )}

      {/* PRD v2026.02: Relationship Lock Modal */}
      {currentCharacter && (
        <RelationshipLockModal
          isOpen={showRelationshipLockModal}
          onClose={handleCancelLock}
          onConfirm={handleConfirmLock}
          characterName={currentCharacter.first_name || 'Character'}
          characterRole={currentCharacter.relationship_role || 'Character'}
          userRole={currentCharacter.user_role || 'You'}
          isLoading={lockingRelationship}
        />
      )}

      {currentCharacter && (
        <ConsentModal
          isOpen={showConsentModal}
          characterId={currentCharacter.id}
          characterName={currentCharacter.first_name}
          onClose={() => setShowConsentModal(false)}
        />
      )}

      <AgeVerificationModal
        isOpen={ageVerificationRequired}
        message={ageVerificationMessage}
        onClose={clearAgeVerificationRequired}
        onVerified={clearAgeVerificationRequired}
      />

      <LanguageModal
        isOpen={isLanguageModalOpen}
        onClose={() => setIsLanguageModalOpen(false)}
      />
      <CommingSoonModal
        isOpen={isCommingSoonModalOpen}
        onClose={() => setIsCommingSoonModalOpen(false)}
      />
    </div>
  );
}

export function ChatPage() {
  return (
    <ChatProvider>
      <AudioFocusProvider>
        <ChatContent />
      </AudioFocusProvider>
    </ChatProvider>
  );
}



