import { useState } from 'react';
import { ChevronDown, ChevronUp, BookOpen } from 'lucide-react';

interface SceneBannerProps {
  scene: string | null;
  synopsis: string | null;
  characterName: string;
}

export function SceneBanner({ scene, synopsis, characterName }: SceneBannerProps) {
  const [expanded, setExpanded] = useState(true);

  if (!scene && !synopsis) return null;

  return (
    <div className="pointer-events-none absolute top-3 left-0 right-0 z-50 flex justify-center px-3">
    <div className="pointer-events-auto w-4/5 sm:w-3/5 rounded-xl border border-amber-500/30 bg-amber-900/20 backdrop-blur-sm overflow-hidden">
      {/* Header row — always visible */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-2 px-4 py-2.5 text-left"
      >
        <BookOpen size={15} className="text-amber-400 flex-shrink-0" />
        <span className="text-amber-300 text-xs font-semibold tracking-wide uppercase flex-1">
          {scene ? `Script Scene: ${scene}` : `Story with ${characterName}`}
        </span>
        {synopsis && (
          expanded
            ? <ChevronUp size={15} className="text-amber-400 flex-shrink-0" />
            : <ChevronDown size={15} className="text-amber-400 flex-shrink-0" />
        )}
      </button>

      {/* Synopsis — collapsible */}
      {synopsis && expanded && (
        <div className="px-4 pb-3 border-t border-amber-500/20">
          <p className="text-xs text-zinc-300 font-medium mt-2 mb-0.5 text-amber-200/80">Recap</p>
          <p className="text-xs text-zinc-400 leading-relaxed">{synopsis}</p>
        </div>
      )}
    </div>
    </div>
  );
}
