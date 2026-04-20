import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import {
  isAgeVerified,
  setAgeVerified,
  isBlocked,
  setBlocked,
  getBlockTimeRemaining,
  clearBlocked
} from '@/utils/ageGateStorage';

interface AgeGateContextType {
  /** Whether user has passed age verification */
  isVerified: boolean;
  /** Whether user is blocked (clicked "I am under 18") */
  isUserBlocked: boolean;
  /** Remaining block time in milliseconds */
  blockTimeRemaining: number;
  /** Loading state during initialization */
  loading: boolean;
  /** Mark user as verified (18+) */
  verify: () => void;
  /** Block user (under 18) */
  block: () => void;
}

const AgeGateContext = createContext<AgeGateContextType | undefined>(undefined);

export function AgeGateProvider({ children }: { children: React.ReactNode }) {
  const [isVerified, setIsVerified] = useState(false);
  const [isUserBlocked, setIsUserBlocked] = useState(false);
  const [blockTimeRemaining, setBlockTimeRemaining] = useState(0);
  const [loading, setLoading] = useState(true);

  // Initialize state from storage
  useEffect(() => {
    const verified = isAgeVerified();
    const blocked = isBlocked();
    const blockTime = getBlockTimeRemaining();

    setIsVerified(verified);
    setIsUserBlocked(blocked);
    setBlockTimeRemaining(blockTime);
    setLoading(false);
  }, []);

  // Update block time remaining periodically
  useEffect(() => {
    if (!isUserBlocked) return;

    const interval = setInterval(() => {
      const remaining = getBlockTimeRemaining();
      setBlockTimeRemaining(remaining);

      if (remaining <= 0) {
        clearBlocked();
        setIsUserBlocked(false);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isUserBlocked]);

  const verify = useCallback(() => {
    setAgeVerified();
    setIsVerified(true);
  }, []);

  const block = useCallback(() => {
    setBlocked();
    setIsUserBlocked(true);
    setBlockTimeRemaining(getBlockTimeRemaining());
  }, []);

  return (
    <AgeGateContext.Provider
      value={{
        isVerified,
        isUserBlocked,
        blockTimeRemaining,
        loading,
        verify,
        block
      }}
    >
      {children}
    </AgeGateContext.Provider>
  );
}

export function useAgeGate(): AgeGateContextType {
  const context = useContext(AgeGateContext);
  if (context === undefined) {
    throw new Error('useAgeGate must be used within an AgeGateProvider');
  }
  return context;
}
