import { useState, useRef } from 'react';
import { Maximize2, Sparkles } from 'lucide-react';
import { ImagePreviewModal } from '@/components/common';

interface SceneImageBannerProps {
  imageUrl: string;
  altText?: string;
}

export function SceneImageBanner({ imageUrl, altText = 'Scene illustration' }: SceneImageBannerProps) {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  return (
    <>
      <div className="my-3 w-full overflow-hidden rounded-xl relative group animate-in fade-in duration-500">
        {/* 16:9 aspect ratio container */}
        <div className="relative w-full aspect-video bg-zinc-900">
          {!loaded && (
            <div className="absolute inset-0 animate-pulse bg-zinc-800 rounded-xl" />
          )}
          <img
            ref={imgRef}
            src={imageUrl}
            alt={altText}
            className="w-full h-full object-cover rounded-xl"
            loading="lazy"
            onLoad={() => setLoaded(true)}
          />

          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent rounded-xl" />

          {/* AI label */}
          <div className="absolute bottom-2 left-3 flex items-center gap-1.5 text-xs text-white/70">
            <Sparkles size={11} className="text-primary-400" />
            <span>AI Scene</span>
          </div>

          {/* Fullscreen button */}
          <button
            onClick={() => setPreviewOpen(true)}
            className="absolute top-2 right-2 w-8 h-8 rounded-full bg-black/50 backdrop-blur flex items-center justify-center text-white/70 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
            aria-label="View fullscreen"
          >
            <Maximize2 size={14} />
          </button>
        </div>
      </div>

      <ImagePreviewModal
        isOpen={previewOpen}
        imageUrl={imageUrl}
        onClose={() => setPreviewOpen(false)}
      />
    </>
  );
}
