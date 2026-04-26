import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RoxyShellLayout } from '@/components/layout';
import { Button, Card, Modal } from '@/components/common';
import { CharacterWizardProvider, useWizard } from '@/contexts/CharacterWizardContext';
import { useAuth } from '@/contexts/AuthContext';
import { WizardProgress, WizardNavigation } from '@/components/character';
import {
  Step1StyleSelection,
  Step3Relationship,
  Step4Appearance,
  Step5Personality,
  Step6Voice,
  Step7BackgroundBoundaries,
  Step8SceneOpening,
  Step9Confirm,
} from '@/components/character/steps';
import { Shuffle, RotateCcw } from 'lucide-react';
import { api } from '@/services/api';
import { toChatUrl } from '@/utils/chatUrl';
import { resolveVoiceProviderId } from '@/types/character';

const FREE_CHARACTER_LIMIT = 2;
const OFFER_DURATION_MS = 30 * 60 * 1000;
const OFFER_STORAGE_KEY = 'create_character_premium_offer_ends_at';

function formatOfferCountdown(msRemaining: number) {
  const totalSeconds = Math.max(0, Math.floor(msRemaining / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function CreateCharacterContent() {
  const navigate = useNavigate();
  const { currentStep, characterData, randomizeAll, resetWizard } = useWizard();
  const { user } = useAuth();
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [avatarGenerationCount, setAvatarGenerationCount] = useState(0);
  const [freeLimitModalOpen, setFreeLimitModalOpen] = useState(false);
  const [offerEndsAt, setOfferEndsAt] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());

  const ensureOfferEndsAt = () => {
    const raw = window.localStorage.getItem(OFFER_STORAGE_KEY);
    const parsed = raw ? Number(raw) : NaN;
    const currentNow = Date.now();
    const valid = Number.isFinite(parsed) && parsed > currentNow + 1000;
    const next = valid ? parsed : currentNow + OFFER_DURATION_MS;
    window.localStorage.setItem(OFFER_STORAGE_KEY, String(next));
    setOfferEndsAt(next);
  };

  useEffect(() => {
    if (!freeLimitModalOpen) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [freeLimitModalOpen]);

  const offerCountdownText = useMemo(() => {
    if (!offerEndsAt) return null;
    const remaining = offerEndsAt - now;
    return remaining > 0 ? formatOfferCountdown(remaining) : '00:00:00';
  }, [offerEndsAt, now]);

  const handleComplete = async () => {
    setError('');

    if ((user?.subscription_tier || 'free') === 'free') {
      try {
        const quotaResponse = await api.get<{ items?: Array<{ id: string }>; total?: number }>(
          '/characters/my',
          { params: { page: 1, page_size: 1 } }
        );
        const createdCount =
          typeof quotaResponse.data?.total === 'number'
            ? quotaResponse.data.total
            : Array.isArray(quotaResponse.data?.items)
              ? quotaResponse.data.items.length
              : 0;

        if (createdCount >= FREE_CHARACTER_LIMIT) {
          ensureOfferEndsAt();
          setFreeLimitModalOpen(true);
          return;
        }
      } catch (limitCheckError) {
        console.error('Failed to check character limit:', limitCheckError);
        // Do not block creation on quota-check transient failures.
      }
    }

    setCreating(true);

    try {
      const relationPayload =
        characterData.relation
          ? {
              ...characterData.relation,
              relationship_type: characterData.personality.relationship,
            }
          : characterData.personality.relationship
            ? { relationship_type: characterData.personality.relationship }
            : null;

      const characterPayload = {
        name: characterData.identity.firstName,
        gender: 'female',
        voice_id: resolveVoiceProviderId(characterData.voiceProfile),
        style: characterData.style,
        base_info: {
          age: characterData.identity.age,
          race: characterData.identity.race || null,
          voice_profile: characterData.voiceProfile || null,
          appearance: {
            body_type: characterData.appearance.bodyType,
            skin_tone: characterData.appearance.skinTone,
            hair_style: characterData.hair.style,
            hair_color: characterData.hair.color,
            eye_color: characterData.face.eyeColor,
            lip_color: characterData.face.lipColor,
          },
          occupation: characterData.background.profession,
        },
        outfit: {
          style: characterData.outfit.style,
          description: characterData.outfit.description,
        },
        background: {
          occupation: characterData.background.profession,
          hobbies: characterData.background.hobbies,
          backstory: characterData.background.backstory,
        },
        personality_summary: characterData.personalitySummary || null,
        personality_example: characterData.personalityExample || null,
        preferences: characterData.preferences || null,
        chat_rules: characterData.chatRules || null,
        greeting: characterData.scene?.openingMessage || null,
        scene_preset: characterData.scene?.environment || null,
        template: characterData.template || null,
        avatar_url: characterData.avatarUrl || null,
        relation: relationPayload,
        personality_tags: characterData.personality.tags,
        relationship_role: characterData.relation?.character_role || null,
        user_role: characterData.relation?.user_role || null,
        consistency_config: characterData.consistency_config || null,
      };

      const response = await api.post('/characters', characterPayload);

      resetWizard();
      setAvatarGenerationCount(0);

      navigate(toChatUrl(response.data));
    } catch (err: unknown) {
      console.error('Failed to create character:', err);
      const detail = (
        err as { response?: { data?: { detail?: unknown } } }
      )?.response?.data?.detail;
      if (Array.isArray(detail)) {
        const messages = detail
          .map((e) => {
            if (typeof e === 'object' && e !== null) {
              const entry = e as { msg?: string; message?: string };
              return entry.msg || entry.message || 'Validation error';
            }
            return 'Validation error';
          })
          .join('; ');
        setError(messages || 'Validation failed. Please check your input.');
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Failed to create character. Please try again.');
      }
    } finally {
      setCreating(false);
    }
  };

  const handleStartOver = () => {
    resetWizard();
    setAvatarGenerationCount(0);
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <Step1StyleSelection />;
      case 2:
        return <Step3Relationship />;
      case 3:
        return <Step4Appearance />;
      case 4:
        return <Step5Personality />;
      case 5:
        return <Step6Voice />;
      case 6:
        return <Step7BackgroundBoundaries />;
      case 7:
        return <Step8SceneOpening />;
      case 8:
        return (
          <Step9Confirm
            avatarGenerationCount={avatarGenerationCount}
            onAvatarGenerated={() => setAvatarGenerationCount((prev) => prev + 1)}
          />
        );
      default:
        return <Step1StyleSelection />;
    }
  };

  return (
    <RoxyShellLayout contentClassName="max-w-[1100px] py-8">
      <div>
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-heading font-bold mb-4">
            Create Your <span className="gradient-text">AI Character</span>
          </h1>
          <p className="text-xl text-zinc-400">
            Design every detail of your perfect AI companion
          </p>
        </div>

        <div className="flex justify-center flex-wrap gap-4 mb-8">
          <Button
            variant="outline"
            size="sm"
            onClick={randomizeAll}
            className="flex items-center gap-2"
          >
            <Shuffle size={16} />
            Randomize All
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleStartOver}
            className="flex items-center gap-2"
          >
            <RotateCcw size={16} />
            Start Over
          </Button>
        </div>

        <WizardProgress />

        {error && (
          <div className="max-w-4xl mx-auto mb-8">
            <Card className="bg-red-500/10 border-red-500/50">
              <p className="text-red-500">{error}</p>
            </Card>
          </div>
        )}

        <div className="mb-8">{renderStep()}</div>

        <div className="max-w-4xl mx-auto">
          <WizardNavigation onComplete={handleComplete} />
        </div>

        <Modal
          isOpen={freeLimitModalOpen}
          onClose={() => setFreeLimitModalOpen(false)}
          className="max-w-md"
        >
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-white">Character Limit Reached</h3>
            <p className="text-zinc-300 text-sm">
              Free users can create up to 2 characters.
            </p>
            <p className="text-amber-300 text-sm">
              Premium yearly plan: limited-time 70% OFF
            </p>
            {offerCountdownText && (
              <p className="text-sm text-zinc-200">
                Countdown: <span className="font-mono">{offerCountdownText}</span> (30 minutes)
              </p>
            )}
            <div className="flex gap-3">
              <Button
                variant="primary"
                className="flex-1"
                onClick={() => {
                  setFreeLimitModalOpen(false);
                  navigate('/billing');
                }}
              >
                Go to Billing
              </Button>
              <Button
                variant="secondary"
                className="flex-1"
                onClick={() => setFreeLimitModalOpen(false)}
              >
                Later
              </Button>
            </div>
          </div>
        </Modal>

        {creating && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
            <Card glass className="text-center space-y-4 max-w-md">
              <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <h3 className="text-xl font-semibold">Creating Your Character...</h3>
              <p className="text-zinc-400">
                Generating unique AI personality and appearance
              </p>
              <p className="text-sm text-zinc-500">This may take 20-30 seconds</p>
            </Card>
          </div>
        )}
      </div>
    </RoxyShellLayout>
  );
}

export function CreateCharacterPage() {
  return (
    <CharacterWizardProvider>
      <CreateCharacterContent />
    </CharacterWizardProvider>
  );
}
