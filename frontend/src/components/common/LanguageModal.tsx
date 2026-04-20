import { Check, X } from 'lucide-react';
import { useEffect, useState } from 'react';

interface LanguageModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface LanguageOption {
  code: string;
  name: string;
  shortCode: string;
}

const LOCAL_STORAGE_KEY = 'preferred_language_code';

const interfaceAndChat: LanguageOption[] = [
  { code: 'en', name: 'English', shortCode: 'EN' },
  { code: 'fr', name: 'Francois', shortCode: 'FR' },
  { code: 'de', name: 'Deutsch', shortCode: 'DE' },
];

const interfaceOnly: LanguageOption[] = [
  { code: 'es', name: 'Espanol', shortCode: 'ES' },
  { code: 'it', name: 'Italiano', shortCode: 'IT' },
  { code: 'jp', name: 'Japanese', shortCode: 'JP' },
  { code: 'nl', name: 'Nederlands', shortCode: 'NL' },
  { code: 'pt-br', name: 'Portugues', shortCode: 'BR' },
];

export function LanguageModal({ isOpen, onClose }: LanguageModalProps) {
  const [selectedLanguage, setSelectedLanguage] = useState<string>(() => {
    if (typeof window === 'undefined') return 'en';
    return window.localStorage.getItem(LOCAL_STORAGE_KEY) || 'en';
  });

  useEffect(() => {
    if (!isOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  const selectLanguage = (code: string) => {
    setSelectedLanguage(code);
    window.localStorage.setItem(LOCAL_STORAGE_KEY, code);
  };

  if (!isOpen) return null;

  const renderOption = (option: LanguageOption) => {
    const selected = selectedLanguage === option.code;
    const isEnglish = option.code === 'en';
    return (
      <button
        key={option.code}
        onClick={() => isEnglish && selectLanguage(option.code)}
        disabled={!isEnglish}
        className={`rounded-xl border px-4 py-3 text-left transition-colors ${
          isEnglish && selected
            ? 'border-pink-500 bg-pink-500/10 text-white'
            : 'cursor-not-allowed border-white/8 text-zinc-600 opacity-40'
        }`}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold">{option.name}</span>
            <span className="text-xs">{option.shortCode}</span>
          </div>
          {isEnglish && selected && <Check size={16} className="text-pink-400" />}
        </div>
      </button>
    );
  };

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/70 px-4 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl rounded-2xl border border-white/10 bg-[#101115] p-6 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-zinc-400 transition-colors hover:text-white"
          aria-label="Close language modal"
        >
          <X size={16} />
        </button>

        <h3 className="text-3xl font-bold text-white">Select your language</h3>

        <div className="mt-8">
          <p className="text-xl font-semibold text-white">Interface + Chat</p>
          <p className="mt-1 text-sm text-zinc-400">Website and chat fully supported</p>
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">{interfaceAndChat.map(renderOption)}</div>
        </div>

        <div className="my-8 border-t border-white/10" />

        <div>
          <p className="text-xl font-semibold text-white">Interface only</p>
          <p className="mt-1 text-sm text-zinc-400">Website available, chat not yet supported</p>
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">{interfaceOnly.map(renderOption)}</div>
        </div>
      </div>
    </div>
  );
}
