import { X } from 'lucide-react';
import { useEffect } from 'react';
import { publicAsset } from '@/utils/publicAsset';

interface CommingSoonModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommingSoonModal({ isOpen, onClose }: CommingSoonModalProps) {
  const previewAvatars = [
    { name: 'Aria', src: publicAsset('/images/aria.png') },
    { name: 'Luna', src: publicAsset('/images/luna.png') },
    { name: 'Maya', src: publicAsset('/images/maya.png') },
    { name: 'Sophia', src: publicAsset('/images/sophia.png') },
  ];

  useEffect(() => {
    if (!isOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/75 px-4 backdrop-blur-sm">
      <button
        type="button"
        className="absolute inset-0 cursor-default"
        aria-label="Close comming soon modal backdrop"
        onClick={onClose}
      />
      <div className="relative w-full max-w-lg overflow-hidden rounded-3xl border border-pink-400/25 bg-[#0f1118] p-6 shadow-[0_22px_90px_rgba(0,0,0,0.65)]">
        <div className="pointer-events-none absolute -left-16 -top-16 h-56 w-56 rounded-full bg-pink-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-16 -right-12 h-56 w-56 rounded-full bg-indigo-500/20 blur-3xl" />

        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full border border-white/15 bg-white/5 p-1.5 text-zinc-400 transition-colors hover:text-white"
          aria-label="Close comming soon modal"
        >
          <X size={16} />
        </button>

        <div className="relative">
          <div className="mb-3 inline-flex items-center rounded-full border border-pink-400/35 bg-pink-500/15 px-3 py-1 text-xs font-semibold tracking-wide text-pink-200">
            NEW CATEGORY IN PROGRESS
          </div>
          <h3 className="text-3xl font-extrabold tracking-tight text-white">Comming Soon</h3>
          <p className="mt-2 max-w-md text-sm leading-relaxed text-zinc-300">
            We are preparing more Anime and Guys characters with better style, voice and stories.
          </p>

          <div className="mt-6 flex items-center">
            {previewAvatars.map((avatar, index) => (
              <div
                key={avatar.name}
                className={`relative ${index > 0 ? '-ml-3' : ''}`}
              >
                <img
                  src={avatar.src}
                  alt={avatar.name}
                  className="h-14 w-14 rounded-full border-2 border-[#0f1118] object-cover shadow-lg"
                />
              </div>
            ))}
            <div className="ml-3 text-sm text-zinc-300">
              <span className="font-semibold text-white">4+ avatars</span> ready for the next drop
            </div>
          </div>

          <div className="mt-6 flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl bg-pink-500 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-pink-400"
            >
              Got It
            </button>
            <span className="text-xs text-zinc-400">Stay tuned</span>
          </div>
        </div>
      </div>
    </div>
  );
}
