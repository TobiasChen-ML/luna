import { createContext, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

interface AudioFocusContextValue {
  isAudioSuppressed: boolean;
  setAudioSuppressed: (suppressed: boolean) => void;
}

const AudioFocusContext = createContext<AudioFocusContextValue | undefined>(undefined);

export function AudioFocusProvider({ children }: { children: ReactNode }) {
  const [isAudioSuppressed, setAudioSuppressed] = useState(false);

  const value = useMemo(
    () => ({
      isAudioSuppressed,
      setAudioSuppressed,
    }),
    [isAudioSuppressed]
  );

  return <AudioFocusContext.Provider value={value}>{children}</AudioFocusContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAudioFocus() {
  const context = useContext(AudioFocusContext);
  return (
    context || {
      isAudioSuppressed: false,
      setAudioSuppressed: () => undefined,
    }
  );
}
