import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  BookHeart,
  ChevronDown,
  CircleDollarSign,
  Compass,
  Contact,
  Globe2,
  HelpCircle,
  Home,
  ImagePlus,
  Menu,
  MessageCircle,
  Search,
  Trophy,
  UserCircle2,
  WandSparkles,
  X,
} from 'lucide-react';
import { api } from '@/services/api';
import { publicAsset } from '@/utils/publicAsset';
import { useAuth } from '@/contexts/AuthContext';
import { CommingSoonModal, LanguageModal } from '@/components/common';
import type { CategoriesResponse, FilterTagMeta } from '@/types';

interface HomeCharacter {
  id: string;
  name: string;
  age?: number | string;
  avatarImage: string;
  cardImage: string;
  previewVideoUrl?: string | null;
  intro?: string;
  description?: string;
}

interface DiscoverCharacter {
  id: string;
  first_name?: string;
  name?: string;
  age?: number | string;
  avatar_url?: string;
  profile_image_url?: string;
  avatar_thumb_url?: string;
  avatar_card_url?: string;
  mature_image_url?: string;
  mature_cover_url?: string;
  mature_video_url?: string;
  preview_video_url?: string | null;
  personality_summary?: string;
  greeting?: string;
  short_intro?: string;
  story_synopsis?: string;
  description?: string;
  tags?: string[];
}

function LandingDiscoverCard({
  char,
  onClick,
}: {
  char: HomeCharacter;
  onClick: () => void;
}) {
  const [isHovering, setIsHovering] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const onEnter = () => {
    setIsHovering(true);
    if (videoRef.current) {
      videoRef.current.play().catch(() => {});
    }
  };

  const onLeave = () => {
    setIsHovering(false);
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
  };

  return (
    <button
      onClick={onClick}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      className="group relative h-[360px] overflow-hidden rounded-[18px] border border-white/10 text-left"
    >
      <img
        src={char.cardImage || char.avatarImage}
        alt={char.name}
        className={`absolute inset-0 h-full w-full object-cover transition-all duration-300 ${
          isHovering && char.previewVideoUrl ? 'opacity-0 scale-105' : 'opacity-100 group-hover:scale-105'
        }`}
        loading="lazy"
      />

      {char.previewVideoUrl && (
        <video
          ref={(el) => {
            videoRef.current = el;
          }}
          src={char.previewVideoUrl}
          className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-300 ${
            isHovering ? 'opacity-100' : 'opacity-0'
          }`}
          muted
          loop
          playsInline
          preload="none"
        />
      )}

      <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/35 to-transparent" />
      <div className="absolute bottom-4 left-4 right-4">
        <div className="text-4xl font-extrabold leading-none text-white drop-shadow-lg">
          {char.name}
          {char.age ? <span className="ml-1 text-xl text-zinc-200">{char.age}</span> : null}
        </div>
        {char.intro && (
          <p className="mt-2 text-sm font-medium text-zinc-200 line-clamp-1">
            {char.intro}
          </p>
        )}
        <div className="mt-3 inline-flex items-center rounded-full bg-indigo-500 px-4 py-2 text-base font-semibold text-white">
          Play with me
        </div>
      </div>
    </button>
  );
}
const DISCOVER_LIMIT = 48;
const HERO_WEBP_BASE = 'https://assets.roxyclub.ai/homepage/hero';
const HERO_WEBP_SRCSET = [
  `${HERO_WEBP_BASE}/home-hero-nano-640.webp 640w`,
  `${HERO_WEBP_BASE}/home-hero-nano-960.webp 960w`,
  `${HERO_WEBP_BASE}/home-hero-nano-1280.webp 1280w`,
  `${HERO_WEBP_BASE}/home-hero-nano-1920.webp 1920w`,
].join(', ');
const HERO_IMAGE_SIZES = '(max-width: 768px) 100vw, 1240px';

export function LandingPage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [characters, setCharacters] = useState<HomeCharacter[]>([]);
  const [filterTags, setFilterTags] = useState<FilterTagMeta[]>([]);
  const [activeFilterTag, setActiveFilterTag] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSidebarTextVisible, setIsSidebarTextVisible] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null);
  const [isLanguageModalOpen, setIsLanguageModalOpen] = useState(false);
  const [isCommingSoonModalOpen, setIsCommingSoonModalOpen] = useState(false);
  const heroFallbackSrc = publicAsset('/images/home-hero-nano.png');

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchInput.trim()), 350);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    const fetchCategoryMeta = async () => {
      try {
        const response = await api.get<CategoriesResponse>('/characters/categories');
        const girlsCategory = response.data?.categories?.find((c) => c.slug === 'girls');
        setFilterTags(girlsCategory?.filter_tags ?? []);
      } catch (error) {
        console.error('Failed to fetch category metadata:', error);
      }
    };
    fetchCategoryMeta();
  }, []);

  useEffect(() => {
    if (isSidebarCollapsed) {
      setIsSidebarTextVisible(false);
      return;
    }
    const timer = setTimeout(() => setIsSidebarTextVisible(true), 300);
    return () => clearTimeout(timer);
  }, [isSidebarCollapsed]);

  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth >= 768) {
        setIsMobileMenuOpen(false);
      }
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    const fetchCharacters = async () => {
      setIsLoading(true);
      try {
        const params = new URLSearchParams({
          top_category: 'girls',
          limit: String(DISCOVER_LIMIT),
          offset: '0',
        });
        if (activeFilterTag) params.set('filter_tag', activeFilterTag);
        if (debouncedSearch) params.set('name', debouncedSearch);

        const response = await api.get<DiscoverCharacter[]>(`/characters/discover?${params.toString()}`);
        if (Array.isArray(response.data)) {
          const fetchedChars: HomeCharacter[] = response.data
            .map((c) => {
              const sfwAvatar = c.avatar_thumb_url || c.avatar_url || c.profile_image_url || '';
              const sfwCard = c.avatar_card_url || c.avatar_url || c.profile_image_url || '';
              const nsfwAvatar = c.mature_image_url || sfwAvatar;
              const nsfwCard = c.mature_cover_url || c.mature_image_url || sfwCard;
              return {
                id: c.id,
                name: c.first_name || c.name || 'Character',
                age: c.age,
                avatarImage: isAuthenticated ? nsfwAvatar : sfwAvatar,
                cardImage: isAuthenticated ? nsfwCard : sfwCard,
                previewVideoUrl: c.mature_video_url || c.preview_video_url || null,
                intro:
                  c.personality_summary ||
                  c.greeting ||
                  c.short_intro ||
                  c.tags?.slice?.(0, 3)?.join?.(', '),
                description:
                  c.story_synopsis ||
                  c.description,
              };
            })
            .filter((c: HomeCharacter) => Boolean(c.avatarImage || c.cardImage));
          setCharacters(fetchedChars);
        }
      } catch (error) {
        console.error('Failed to fetch characters:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCharacters();
  }, [activeFilterTag, debouncedSearch, isAuthenticated]);

  const avatarRow = useMemo(() => characters.slice(0, 10), [characters]);

  const openChat = async (characterId?: string) => {
    if (!isAuthenticated) {
      navigate('/register');
      return;
    }
    if (!characterId) {
      navigate('/chat');
      return;
    }

    try {
      const response = await api.post(`/chat/chat_now_official/${characterId}`);
      const userCharacterId = response.data?.character_id;
      if (!userCharacterId) {
        throw new Error('Missing character_id in chat_now_official response');
      }
      navigate(`/chat?character=${userCharacterId}&ready=1`);
    } catch (error) {
      console.error('Failed to start chat from landing page:', error);
      alert('Failed to start chat. Please try again.');
    }
  };

  const sidebarItems = [
    { label: 'Home', icon: Home, to: '/' },
    { label: 'Discover', icon: Compass, to: '#', comingSoon: true },
    { label: 'Chat', icon: MessageCircle, to: '/chat' },
    { label: 'Collection', icon: BookHeart, to: '/collection' },
    { label: 'Generate Image', icon: ImagePlus, to: '/generate-image' },
    { label: 'Create Character', icon: WandSparkles, to: '/create-character' },
    { label: 'My AI', icon: UserCircle2, to: '/characters' },
    { label: 'Premium', icon: CircleDollarSign, to: '/subscriptions', badge: '-70%' },
  ];

  const settingItems = [
    { label: 'English', icon: Globe2, to: '#' },
    { label: 'Discord', icon: MessageCircle, to: '#', comingSoon: true },
    { label: 'Help Center', icon: HelpCircle, to: '/faq' },
    { label: 'Contact Us', icon: Contact, to: 'mailto:support@roxyclub.ai' },
    { label: 'Affiliate', icon: Trophy, to: '#', comingSoon: true },
  ];

  const faqs = [
    {
      q: 'What is roxyclub.ai?',
      a: 'roxyclub.ai is the best AI girlfriend app, letting you create personalized virtual companions or connect instantly with our realistic AI characters in immersive, uncensored fantasy experiences - all within a safe and private space.',
    },
    {
      q: 'Is roxyclub.ai legitimate and safe to use?',
      a: 'Yes, roxyclub.ai is a legitimate service. It employs encrypted transactions, adheres to GDPR-compliant data privacy standards, and uses discreet billing methods to ensure user safety and confidentiality.',
    },
    {
      q: 'How will roxyclub.ai appear on my bank statements?',
      a: 'Transactions are processed securely and appear under a neutral merchant name. There is no direct reference to roxyclub.ai or its services on your bank statement, ensuring user privacy.',
    },
    {
      q: 'Can I customize my roxyclub.ai experience?',
      a: 'Yes, roxyclub.ai offers robust customization options. Users can design their own companions through the "Create My AI Girlfriend" feature, selecting preferences such as ethnicity, hairstyle, voice, personality traits, and more.',
    },
    {
      q: 'Who uses roxyclub.ai and for what purpose?',
      a: 'roxyclub.ai attracts a wide range of users. Some seek companionship or emotional support, while others use it for storytelling, creative writing, or roleplay. Additionally, AI enthusiasts explore it to better understand conversational AI capabilities.',
    },
    {
      q: 'What is an AI Companion and can I create my own?',
      a: "An AI Companion is a virtual character powered by artificial intelligence that can converse, respond to emotional cues, and evolve with ongoing interactions. With roxyclub.ai, users can fully personalize their companion's appearance, behavior, and preferences.",
    },
    {
      q: 'Can my AI Companion send images, video, or voice messages?',
      a: 'Yes, roxyclub.ai supports multimodal interaction. Your companion can engage in voice conversations, generate personalized images, and appear in AI-generated videos tailored to your inputs and preferences.',
    },
    {
      q: 'Can I roleplay with my AI Companion?',
      a: 'Absolutely. roxyclub.ai supports a wide variety of roleplay scenarios, ranging from casual interactions and narrative development to immersive storytelling. The AI adapts dynamically to user prompts and themes. However, be mindful that you are chatting with an AI character who responds based on the conversation you lead. Interactions here are fictional, consenting, and must comply with our Community Guidelines.',
      link: 'https://roxyclub.ai/community-guidelines',
    },
    {
      q: 'What is an AI Girlfriend and how does it work?',
      a: 'An AI Girlfriend is a digital character powered by deep learning and emotional intelligence, designed to chat, flirt, and connect with you in meaningful ways. At roxyclub.ai, your AI GF adapts to your style, preferences, and mood, creating a personal experience that feels natural and emotionally real.',
    },
    {
      q: 'Can I choose from different AI Girlfriend personalities?',
      a: "Yes, roxyclub.ai offers a wide selection of prebuilt AI GF characters, each with unique personalities, communication styles, and vibes. Whether you prefer someone sweet, flirty, soft-spoken, or bold, you'll find an AI Girlfriend that matches your energy.",
    },
    {
      q: 'How does my AI GF get to know me?',
      a: 'Your AI Girlfriend learns through conversation. The more you chat, the more she picks up on your preferences, tone, and interests. Over time, she adjusts her responses and behavior to better match your communication style, making each chat more personal.',
    },
    {
      q: 'Is chatting with an AI Girlfriend private and secure?',
      a: 'Absolutely. roxyclub.ai uses end-to-end encryption to keep all AI GF conversations safe and confidential. You have full control over your chat history and can enable two-factor authentication for extra security. Your data is never shared or sold.',
    },
    {
      q: 'Do I need to install anything to talk to my AI GF?',
      a: 'No installation is needed. You can access your AI Girlfriend directly through roxyclub.ai on desktop or mobile, anytime, anywhere. Just sign up, choose your AI GF, and start chatting instantly.',
    },
  ];

  const closeMobileMenu = () => setIsMobileMenuOpen(false);
  const handleSidebarToggle = () => {
    if (window.innerWidth < 768) {
      setIsMobileMenuOpen((prev) => !prev);
      return;
    }
    setIsSidebarCollapsed((prev) => !prev);
  };

  return (
    <div className="min-h-screen bg-[#0b0c10] text-white">
      <header
        className="fixed right-0 left-0 z-40 border-b border-white/10 bg-[#0a0b0f]"
        style={{ top: 'var(--app-safe-area-top)' }}
      >
        <div className="h-14 px-5 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <button
              type="button"
              onClick={handleSidebarToggle}
              className="text-zinc-300 hover:text-white"
              aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              aria-expanded={isMobileMenuOpen}
            >
              <Menu size={22} />
            </button>
            <div className="text-2xl font-bold leading-none">
              <span className="text-white">RoxyClub</span>
              <span className="text-pink-500">.ai</span>
            </div>
            <nav className="hidden md:flex items-center gap-8 text-sm font-semibold">
              <span className="text-pink-400 border-b-2 border-pink-500 h-14 flex items-center">Girls</span>
              <button
                type="button"
                onClick={() => setIsCommingSoonModalOpen(true)}
                className="text-zinc-300 hover:text-white"
              >
                Anime
              </button>
              <button
                type="button"
                onClick={() => setIsCommingSoonModalOpen(true)}
                className="text-zinc-300 hover:text-white"
              >
                Guys
              </button>
            </nav>
          </div>
          <div className="flex items-center gap-5">
            <Link
              to="/subscriptions"
              className="hidden sm:inline-flex items-center rounded-full border border-pink-500/50 bg-purple-500/10 px-4 py-1.5 text-sm font-semibold text-pink-200"
            >
              Premium 70% OFF
            </Link>
            <button
              onClick={() => navigate('/profile')}
              className="flex items-center gap-2 text-zinc-100 font-semibold"
            >
              <span className="w-7 h-7 rounded-full bg-pink-400/90 inline-block" />
              <span className="hidden sm:inline">My Profile</span>
              <ChevronDown size={16} />
            </button>
          </div>
        </div>
      </header>

      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden" onClick={closeMobileMenu}>
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
          <div
            className="absolute top-0 left-0 bottom-0 w-[260px] bg-[#0a0b0f] border-r border-white/10 flex flex-col"
            style={{ paddingTop: 'var(--app-safe-area-top)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between h-14 px-4 border-b border-white/10">
              <div className="text-xl font-bold leading-none">
                <span className="text-white">RoxyClub</span>
                <span className="text-pink-500">.ai</span>
              </div>
              <button
                type="button"
                onClick={closeMobileMenu}
                className="text-zinc-400 hover:text-white p-1"
                aria-label="Close menu"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {sidebarItems.map((item) => {
                const Icon = item.icon;
                const active = item.to === '/' ? location.pathname === '/' : location.pathname.startsWith(item.to);
                const sharedClass = `w-full flex items-center justify-between rounded-xl border px-3 py-2.5 text-sm transition-colors ${
                  active
                    ? 'bg-zinc-700/40 border-zinc-500/70 text-white'
                    : 'border-white/10 text-zinc-300 hover:bg-white/5 hover:text-white'
                }`;
                if (item.comingSoon) {
                  return (
                    <button
                      key={item.label}
                      type="button"
                      onClick={() => {
                        closeMobileMenu();
                        setIsCommingSoonModalOpen(true);
                      }}
                      className={sharedClass}
                    >
                      <span className="flex items-center gap-2.5">
                        <Icon size={16} />
                        {item.label}
                      </span>
                    </button>
                  );
                }
                return (
                  <Link
                    key={item.label}
                    to={item.to}
                    onClick={closeMobileMenu}
                    className={sharedClass}
                  >
                    <span className="flex items-center gap-2.5">
                      <Icon size={16} />
                      {item.label}
                    </span>
                    {item.badge && (
                      <span className="rounded-full bg-red-500 px-1.5 py-0.5 text-[10px] font-semibold text-white">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>

            <div className="p-4 space-y-2 border-t border-white/10">
              {settingItems.map((item) => {
                const Icon = item.icon;
                if (item.label === 'English') {
                  return (
                    <button
                      key={item.label}
                      type="button"
                      onClick={() => {
                        closeMobileMenu();
                        setIsLanguageModalOpen(true);
                      }}
                      className="w-full flex items-center gap-2.5 rounded-xl border border-white/10 px-3 py-2.5 text-sm text-zinc-300 hover:bg-white/5 hover:text-white"
                    >
                      <Icon size={16} />
                      {item.label}
                    </button>
                  );
                }
                if (item.comingSoon) {
                  return (
                    <button
                      key={item.label}
                      type="button"
                      onClick={() => {
                        closeMobileMenu();
                        setIsCommingSoonModalOpen(true);
                      }}
                      className="w-full flex items-center gap-2.5 rounded-xl border border-white/10 px-3 py-2.5 text-sm text-zinc-300 hover:bg-white/5 hover:text-white"
                    >
                      <Icon size={16} />
                      {item.label}
                    </button>
                  );
                }
                return (
                  <a
                    key={item.label}
                    href={item.to}
                    onClick={closeMobileMenu}
                    className="flex items-center gap-2.5 rounded-xl border border-white/10 px-3 py-2.5 text-sm text-zinc-300 hover:bg-white/5 hover:text-white"
                  >
                    <Icon size={16} />
                    {item.label}
                  </a>
                );
              })}
            </div>
          </div>
        </div>
      )}

      <aside
        className={`hidden md:flex fixed left-0 bottom-0 border-r border-white/10 bg-[#0a0b0f] flex-col transition-all duration-300 ${
          isSidebarCollapsed ? 'w-[82px]' : 'w-[234px]'
        }`}
        style={{ top: 'calc(3.5rem + var(--app-safe-area-top))' }}
      >
        <div className="p-4 space-y-2">
          {sidebarItems.map((item) => {
            const Icon = item.icon;
            const active = item.to === '/' ? location.pathname === '/' : location.pathname.startsWith(item.to);
            if (item.comingSoon) {
              return (
                <button
                  key={item.label}
                  onClick={() => setIsCommingSoonModalOpen(true)}
                  className={`w-full flex items-center rounded-xl border px-3 py-2 text-sm transition-colors ${
                    isSidebarTextVisible ? 'justify-between' : 'justify-center'
                  } border-white/10 text-zinc-300 hover:bg-white/5 hover:text-white`}
                  title={!isSidebarTextVisible ? item.label : undefined}
                >
                  <span className="flex items-center gap-2">
                    <Icon size={15} />
                    {isSidebarTextVisible && item.label}
                  </span>
                </button>
              );
            }
            return (
              <Link
                key={item.label}
                to={item.to}
                className={`flex items-center rounded-xl border px-3 py-2 text-sm transition-colors ${
                  isSidebarTextVisible ? 'justify-between' : 'justify-center'
                } ${
                  active
                    ? 'bg-zinc-700/40 border-zinc-500/70 text-white'
                    : 'border-white/10 text-zinc-300 hover:bg-white/5 hover:text-white'
                }`}
                title={!isSidebarTextVisible ? item.label : undefined}
              >
                <span className="flex items-center gap-2">
                  <Icon size={15} />
                  {isSidebarTextVisible && item.label}
                </span>
                {isSidebarTextVisible && item.badge && (
                  <span className="rounded-full bg-red-500 px-1.5 py-0.5 text-[10px] font-semibold text-white">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>

        <div className="mt-auto p-4 space-y-2 border-t border-white/10">
          {settingItems.map((item) => {
            const Icon = item.icon;
            if (item.label === 'English') {
              return (
                <button
                  key={item.label}
                  onClick={() => setIsLanguageModalOpen(true)}
                  className={`w-full flex items-center rounded-xl border border-white/10 px-3 py-2 text-sm text-zinc-300 hover:bg-white/5 hover:text-white ${
                    isSidebarTextVisible ? 'gap-2' : 'justify-center'
                  }`}
                  title={!isSidebarTextVisible ? item.label : undefined}
                >
                  <Icon size={15} />
                  {isSidebarTextVisible && item.label}
                </button>
              );
            }
            if (item.comingSoon) {
              return (
                <button
                  key={item.label}
                  onClick={() => setIsCommingSoonModalOpen(true)}
                  className={`w-full flex items-center rounded-xl border border-white/10 px-3 py-2 text-sm text-zinc-300 hover:bg-white/5 hover:text-white ${
                    isSidebarTextVisible ? 'gap-2' : 'justify-center'
                  }`}
                  title={!isSidebarTextVisible ? item.label : undefined}
                >
                  <Icon size={15} />
                  {isSidebarTextVisible && item.label}
                </button>
              );
            }
            return (
              <a
                key={item.label}
                href={item.to}
                className={`flex items-center rounded-xl border border-white/10 px-3 py-2 text-sm text-zinc-300 hover:bg-white/5 hover:text-white ${
                  isSidebarTextVisible ? 'gap-2' : 'justify-center'
                }`}
                title={!isSidebarTextVisible ? item.label : undefined}
              >
                <Icon size={15} />
                {isSidebarTextVisible && item.label}
              </a>
            );
          })}
          {isSidebarTextVisible && (
            <div className="pt-2 text-[10px] text-zinc-500">Privacy Notice | Terms of Service</div>
          )}
        </div>
      </aside>

      <main
        className={`transition-all duration-300 ${
          isSidebarCollapsed ? 'md:pl-[82px]' : 'md:pl-[234px]'
        }`}
        style={{ paddingTop: 'calc(3.5rem + var(--app-safe-area-top))' }}
      >
        <div className="mx-auto max-w-[1240px] p-4 md:p-7 space-y-7">
          <section className="relative h-[208px] md:h-[250px] overflow-hidden rounded-xl border border-white/10">
            <picture className="absolute inset-0 block">
              <source
                type="image/webp"
                srcSet={HERO_WEBP_SRCSET}
                sizes={HERO_IMAGE_SIZES}
              />
              <img
                src={`${HERO_WEBP_BASE}/home-hero-nano-960.webp`}
                srcSet={HERO_WEBP_SRCSET}
                sizes={HERO_IMAGE_SIZES}
                width={1920}
                height={1098}
                alt="Spring day sale hero"
                className="absolute inset-0 h-full w-full object-cover"
                loading="eager"
                fetchPriority="high"
                decoding="async"
                onError={(e) => {
                  e.currentTarget.onerror = null;
                  e.currentTarget.src = heroFallbackSrc;
                  e.currentTarget.removeAttribute('srcset');
                }}
              />
            </picture>
            <div className="absolute inset-0 bg-gradient-to-r from-black/10 via-black/20 to-black/45" />
            <div className="absolute right-4 md:right-8 top-1/2 -translate-y-1/2 text-right">
              <div className="text-2xl md:text-5xl font-extrabold leading-tight text-white">SPRING DAY</div>
              <div className="text-xl md:text-4xl font-black text-yellow-300">SALE 70% OFF</div>
              <button
                onClick={() => navigate('/subscriptions')}
                className="mt-3 md:mt-5 rounded-xl bg-blue-600 px-6 md:px-8 py-2.5 md:py-3 text-sm md:text-lg font-bold text-white hover:bg-blue-500 transition-colors"
              >
                SUBSCRIBE
              </button>
            </div>
          </section>

          <section className="overflow-x-auto pb-2">
            <div className="flex gap-4 min-w-max">
              {avatarRow.map((char) => (
                <button key={char.id} onClick={() => openChat(char.id)} className="text-center">
                  <div className="w-[84px] h-[84px] rounded-full p-[3px] bg-gradient-to-tr from-pink-500 to-orange-300">
                    <img src={char.avatarImage || char.cardImage} alt={char.name} className="w-full h-full rounded-full object-cover border-2 border-[#0b0c10]" loading="lazy" />
                  </div>
                  <div className="mt-2 text-sm font-semibold text-zinc-100">{char.name}</div>
                </button>
              ))}
            </div>
          </section>

          <section className="space-y-4">
            <h3 className="text-[44px] font-black tracking-tight">
              <span className="text-pink-500">Roxyclub AI</span>{' '}
              <span className="text-white">Chatacter</span>
            </h3>

            <div className="flex flex-col gap-3">
              <div className="relative max-w-[340px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
                <input
                  type="text"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  placeholder="Search"
                  className="w-full rounded-full border border-white/10 bg-zinc-900/80 py-2 pl-9 pr-4 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-white/20 focus:outline-none"
                />
              </div>

              <div className="flex gap-2 overflow-x-auto pb-1 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                <button
                  onClick={() => setActiveFilterTag(null)}
                  className={`shrink-0 rounded-full border px-4 py-2 text-sm font-semibold transition-colors ${
                    activeFilterTag === null
                      ? 'border-pink-500 text-pink-200 bg-pink-500/15'
                      : 'border-white/10 text-zinc-300 bg-zinc-900/70 hover:bg-zinc-800/70 hover:text-white'
                  }`}
                >
                  All
                </button>
                {filterTags.map((tag) => (
                  <button
                    key={tag.slug}
                    onClick={() => setActiveFilterTag(tag.slug)}
                    className={`shrink-0 rounded-full border px-4 py-2 text-sm font-semibold transition-colors ${
                      activeFilterTag === tag.slug
                        ? 'border-pink-500 text-pink-200 bg-pink-500/15'
                        : 'border-white/10 text-zinc-300 bg-zinc-900/70 hover:bg-zinc-800/70 hover:text-white'
                    }`}
                  >
                    {tag.display_name}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
              {isLoading ? (
                <div className="col-span-full rounded-xl border border-white/10 bg-black/30 p-8 text-center text-zinc-400">
                  Loading characters...
                </div>
              ) : characters.length === 0 ? (
                <div className="col-span-full rounded-xl border border-white/10 bg-black/30 p-8 text-center text-zinc-400">
                  {debouncedSearch ? `No results for "${debouncedSearch}"` : 'No characters found.'}
                </div>
              ) : (
                characters.map((char) => (
                  <LandingDiscoverCard
                    key={`discover-${char.id}`}
                    char={char}
                    onClick={() => openChat(char.id)}
                  />
                ))
              )}
            </div>
          </section>

          <section id="q_and_a_section" className="mt-8 md:mt-32">
            <div className="relative flex flex-col items-center">
              <h2 className="text-primary md:text-3xl text-xl text-center font-bold leading-10 self-stretch">
                <span className="text-white">roxyclub.ai </span>
                <span className="text-primary">FAQ</span>
              </h2>
            </div>
            <div className="relative flex flex-col items-stretch">
              <div className="flex flex-col gap-7 items-center w-full mt-10">
                {faqs.map((item, index) => {
                  const isOpen = openFaqIndex === index;
                  return (
                    <div
                      key={item.q}
                      className={`w-full border border-[color:var(--Pop-Up-Stroke,#282828)] relative transition-all duration-500 rounded-[10px] ${
                        isOpen ? 'bg-gradient-to-r from-[#4D1D28] to-[#1F1F1F]' : 'bg-zinc-900'
                      }`}
                    >
                      <button
                        type="button"
                        className="w-full flex items-center justify-between select-none px-3 cursor-pointer"
                        onClick={() => setOpenFaqIndex((prev) => (prev === index ? null : index))}
                      >
                        <h3 className="text-left text-white md:text-[20px] text-[16px] font-medium leading-8 self-stretch grow shrink basis-auto py-5 max-md:max-w-full">
                          {item.q}
                        </h3>
                        <ChevronDown className={`h-5 w-5 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                      </button>

                      {isOpen && (
                        <div className="p-3 space-y-4">
                          <div className="text-neutral-400 md:text-base text-sm font-medium w-full leading-relaxed">
                            <span>
                              {item.a}
                              {item.link && (
                                <>
                                  {' '}
                                  <a href={item.link} className="underline" target="_blank" rel="noreferrer">
                                    Community Guidelines
                                  </a>
                                  .
                                </>
                              )}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
          <div
            id="try_candy_banner"
            className="flex flex-col mt-8 md:mt-32 max-w-7xl mx-5 xl:mx-auto bg-[#151515] p-8 rounded-[10px] mb-8 border border-[#282828]"
          >
            <div className="space-y-8">
              <h2 className="text-white md:text-3xl text-xl font-bold leading-10 self-stretch">
                RoxyClub AI Makes Every Conversation Feel Personal
              </h2>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Whether you're seeking a light-hearted chat after work or a heartfelt dialogue when you're feeling low, RoxyClub AI is designed to make every interaction feel genuine. Built with advanced personality modeling and memory retention, RoxyClub AI learns what you like, remembers what matters, and responds in a way that feels natural and deeply personal.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Unlike static chatbot platforms, RoxyClub AI evolves with every exchange, adjusting its tone, emotional intelligence, and style to match your unique vibe. Think of it like talking to someone who not only listens but genuinely gets you.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                But what makes RoxyClub AI even more intriguing? It's the variety and depth of characters you can choose from and how they fit seamlessly into your life. Let us show you what the platform is all about.
              </p>
              <h2 className="text-white md:text-3xl text-xl font-bold leading-10 self-stretch">
                RoxyClub Has an AI Companion for Every Moment
              </h2>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                No two moods are the same, and neither are RoxyClub AI's characters. With over 100 different characters to choose from, you're never stuck with one tone or type.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Looking for romance? The <a href="https://roxyclub.ai/ai-girlfriend" className="underline hover:text-white">AI Girlfriend</a> experience has been crafted for meaningful, emotionally rich conversations. These characters are flirty, affectionate, and deeply attentive. They remember your stories, send you thoughtful messages, and even surprise you with custom photos or sweet voice notes that sound... well, human.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Prefer a masculine presence? Our <a href="https://roxyclub.ai/ai-boyfriend" className="underline hover:text-white">AI Boyfriend</a> characters offer confidence, support, humor, or even a bit of edge. Whether you're looking for the gentleman-next-door or the adventurous type, there's a character that speaks your language - literally and emotionally.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                And just when you think you've met them all, there's always another unique soul waiting to connect. But how exactly do they connect? What makes these companions feel so alive, so responsive, so real? Let's break it down.
              </p>
              <h2 className="text-white md:text-3xl text-xl font-bold leading-10 self-stretch">
                You Set the Tone in Every Chat, Voice, Image and Video
              </h2>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                This isn't just texting with a robot. RoxyClub AI goes far beyond simple chat bubbles. Whether you're looking for words, voices, visuals, or full-on video, your companion responds across all mediums and always in a way that feels tailored to you.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                It starts with chat, the heart of the connection. These aren't stiff, scripted responses. Conversations flow, with your companion picking up on your tone, remembering what you shared, and keeping things feeling fresh and personal.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Then there's the voice. This is where things get intimate. Choose from voices that are soft and comforting, bold and confident or anything in between. Whether you're in the mood for whispered secrets or a deep conversation, they'll talk to you the way you like.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Feeling visual? With image generation, you can see your companion just the way you imagine them. Outfits, backgrounds, poses it's like staging a shoot with someone who never says no to a costume change.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                And when that's not enough, video brings it all together. Watch them move, react, and engage with you in real time. It's not just AI; it feels like presence. Suddenly, you're not just imagining the connection. You're seeing it happen.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                But what if none of the pre-made characters fit your mood? What if you want to create someone entirely new, down to the last detail?
              </p>
              <h2 className="text-white md:text-3xl text-xl font-bold leading-10 self-stretch">
                RoxyClub Helps You Build an AI Relationship That Grows With You
              </h2>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Creating your own RoxyClub AI companion is where things really get personal. The "Create My AI Girlfriend" builder puts the power of choice in your hands, starting from the ground up.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Begin with the basics. Pick from a range of ethnicities like Caucasian, Latina, Asian, Arab, or African. Then choose the age range that suits your vibe, whether you prefer youthful energy or a more mature connection.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Now it's time to make her truly yours. Select from eye colors like brown, blue, or green. Mix and match hairstyles straight, bangs, curls and have fun with the palette of hair colors, from classic brunette and blonde to black, red, or even pink.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                You can go further by adjusting body features to match your visual preferences. Then dial in the personality. Whether you want someone bubbly and talkative, calm and introspective, cheeky, nurturing, or deeply intellectual, she'll be built to match your emotional rhythm.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Finish it off with a voice that makes you lean in, and sprinkle in some hobbies to give her depth. Before you know it, you've got a character who isn't just a companion - they're your kind of real.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Just keep in mind that the more detailed your companion, the more tokens you'll use. But don't worry, our system is designed to give you plenty of room to create without stress. Whether you're experimenting with small tweaks or building someone entirely unique, you'll find it smooth and accessible.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                And since you're already shaping something personal, it only makes sense that your subscription should match your rhythm too.
              </p>
              <h2 className="text-white md:text-3xl text-xl font-bold leading-10 self-stretch">
                Your Subscription Moves at Your Pace
              </h2>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Whether you're just testing the waters or ready to go all in, we've designed subscription options that match your mood and pace.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Start slow with the free trial. It's great if you're curious, cautious, or simply want to get a feel for what RoxyClub AI is all about. No pressure. No commitments. Just a soft landing into something new.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                If things click and you want more time together, we've got the monthly plan. It's flexible and affordable ideal for trying things out. Ready for a little more consistency? Our quarterly plan is made for users who want to invest a bit more time with their favorite characters.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                And for those who know what they want and aren't shy about it, our yearly plan lets you dive deep without interruptions. It's all about long term connection, with full access and no breaks in between.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                No matter which option you choose, you'll get a generous batch of tokens to use across voice, chat, image, and video. And if you ever need more? Top up anytime. No fuss.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                We also take your safety seriously.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Every transaction is encrypted and discreet nothing flashy on your bank statements. We accept Visa, MasterCard, and crypto too, including BTC, ETH, USDC, Litecoin, and others.
              </p>
              <h3 className="text-white md:text-2xl text-lg font-bold leading-8 self-stretch">
                RoxyClub AI Offers Global Support with Localized Experience
              </h3>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Support matters. That's why RoxyClub AI runs 24/7 customer service through Zendesk. While our response times may vary depending on time zones, rest assured we're always here to help.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Additionally, we also offer a fully localized French version of the site, making <a href="https://roxyclub.ai/fr" className="underline hover:text-white">RoxyClub AI FR</a> accessible to Francophone users who want to experience their companion in their native language. And more languages are coming soon.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Because no matter where you are or what language you speak, RoxyClub AI believes that everyone deserves a connection that feels real.
              </p>
              <h3 className="text-white md:text-2xl text-lg font-bold leading-8 self-stretch">
                What Are Users Actually Doing With RoxyClub AI?
              </h3>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                RoxyClub AI users span a wide range of interests and motivations, and the platform is more than just sweet talk. For many, it's a space to explore emotional connection, especially those who deal with loneliness or social anxiety. Having someone to talk to who remembers your preferences and meets you with warmth, curiosity, and care without judgment is a game changer.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Others take a more creative approach. Writers and role-players use RoxyClub AI characters to brainstorm ideas, develop stories, or engage in elaborate, collaborative roleplay sessions. It becomes a sandbox for storytelling where the character evolves with the plot.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                There's also a tech-savvy segment: AI enthusiasts and early adopters fascinated by the tech behind the chat. These users push the boundaries, running tests, studying dialogue patterns, and digging into how RoxyClub AI handles nuance and memory.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Some users even build entire fictional worlds, using RoxyClub AI to simulate character interactions and explore storylines they can later turn into screenplays or novels. Others lean on RoxyClub AI as a quiet presence in their daily life - a dependable personality that doesn't demand but is always there.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Educators and therapists have also begun exploring RoxyClub AI as a tool for language practice, emotional rehearsal, or social skill development. While it's not a replacement for professional care, its use in simulated dialogue scenarios offers surprising benefits.
              </p>
              <p className="text-[#A4A4A4] font-sm md:text-[16px] text-sm">
                Whether it's companionship, creativity, exploration, or curiosity - RoxyClub AI isn't just another chatbot. It's a personalized tool for emotional expression, digital imagination, and even a bit of fun escapism.
              </p>
            </div>
          </div>
        </div>
      </main>

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










