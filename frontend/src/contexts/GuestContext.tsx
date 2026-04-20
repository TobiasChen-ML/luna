import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import type { ReactNode } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export interface GuestMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  image_url?: string;
  video_url?: string;
  audio_url?: string;
  timestamp: string;
}

interface GuestContextValue {
  isGuestMode: boolean;
  setIsGuestMode: (value: boolean) => void;
  guestCredits: number;
  isCreditsExhausted: boolean;
  guestMessages: GuestMessage[];
  fetchGuestCredits: () => Promise<void>;
  sendGuestMessage: (characterId: string, message: string) => Promise<GuestMessage | null>;
  clearGuestMessages: () => void;
  isLoading: boolean;
  isSending: boolean;
}

const GuestContext = createContext<GuestContextValue | undefined>(undefined);

export function useGuestContext() {
  const context = useContext(GuestContext);
  if (!context) {
    throw new Error('useGuestContext must be used within GuestProvider');
  }
  return context;
}

interface GuestProviderProps {
  children: ReactNode;
}

export function GuestProvider({ children }: GuestProviderProps) {
  const [isGuestMode, setIsGuestMode] = useState(false);
  const [guestCredits, setGuestCredits] = useState(20);
  const [isCreditsExhausted, setIsCreditsExhausted] = useState(false);
  const [guestMessages, setGuestMessages] = useState<GuestMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const fetchGuestCredits = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/chat/guest/credits`);
      setGuestCredits(response.data.credits);
      setIsCreditsExhausted(response.data.is_exhausted);
    } catch (error) {
      console.error('Failed to fetch guest credits:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendGuestMessage = useCallback(async (
    characterId: string,
    message: string
  ): Promise<GuestMessage | null> => {
    if (isSending) return null;

    setIsSending(true);

    // Add user message immediately (optimistic)
    const userMsg: GuestMessage = {
      id: `guest-user-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    setGuestMessages(prev => [...prev, userMsg]);

    try {
      const response = await axios.post(`${API_BASE}/chat/guest/send`, {
        character_id: characterId,
        message: message
      });

      const assistantMsg: GuestMessage = {
        id: `guest-assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.content,
        image_url: response.data.image_url || undefined,
        video_url: response.data.video_url || undefined,
        audio_url: response.data.audio_url || undefined,
        timestamp: new Date().toISOString()
      };

      setGuestMessages(prev => [...prev, assistantMsg]);
      setGuestCredits(response.data.credits_remaining);
      setIsCreditsExhausted(response.data.is_exhausted);

      return assistantMsg;
    } catch (error: unknown) {
      console.error('Guest message failed:', error);

      // Check if credits exhausted
      if (axios.isAxiosError(error) && error.response?.status === 402) {
        setIsCreditsExhausted(true);
        setGuestCredits(0);
      }

      // Remove optimistic user message on error
      setGuestMessages(prev => prev.filter(m => m.id !== userMsg.id));
      return null;
    } finally {
      setIsSending(false);
    }
  }, [isSending]);

  const clearGuestMessages = useCallback(() => {
    setGuestMessages([]);
  }, []);

  // Fetch credits when entering guest mode
  useEffect(() => {
    if (isGuestMode) {
      fetchGuestCredits();
    } else {
      // Clear messages when exiting guest mode
      setGuestMessages([]);
    }
  }, [isGuestMode, fetchGuestCredits]);

  const value: GuestContextValue = {
    isGuestMode,
    setIsGuestMode,
    guestCredits,
    isCreditsExhausted,
    guestMessages,
    fetchGuestCredits,
    sendGuestMessage,
    clearGuestMessages,
    isLoading,
    isSending,
  };

  return <GuestContext.Provider value={value}>{children}</GuestContext.Provider>;
}
