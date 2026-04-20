import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { api } from '@/services/api';

interface GeoState {
  allowed: boolean;
  countryCode: string;
  countryName: string;
  isLoading: boolean;
  isChecked: boolean;
}

interface GeoContextValue extends GeoState {
  recheckGeo: () => Promise<void>;
}

const GeoContext = createContext<GeoContextValue | undefined>(undefined);

const GEO_CACHE_KEY = 'aigirl_geo_check';
const GEO_CACHE_TTL = 1000 * 60 * 60; // 1 hour cache

interface CachedGeoData {
  allowed: boolean;
  countryCode: string;
  countryName: string;
  timestamp: number;
}

function getCachedGeo(): CachedGeoData | null {
  try {
    const cached = localStorage.getItem(GEO_CACHE_KEY);
    if (!cached) return null;

    const data: CachedGeoData = JSON.parse(cached);
    const now = Date.now();

    // Check if cache is still valid
    if (now - data.timestamp < GEO_CACHE_TTL) {
      return data;
    }

    // Cache expired
    localStorage.removeItem(GEO_CACHE_KEY);
    return null;
  } catch {
    return null;
  }
}

function setCachedGeo(data: Omit<CachedGeoData, 'timestamp'>): void {
  try {
    const cacheData: CachedGeoData = {
      ...data,
      timestamp: Date.now(),
    };
    localStorage.setItem(GEO_CACHE_KEY, JSON.stringify(cacheData));
  } catch {
    // Ignore localStorage errors
  }
}

export function useGeoContext() {
  const context = useContext(GeoContext);
  if (!context) {
    throw new Error('useGeoContext must be used within GeoProvider');
  }
  return context;
}

interface GeoProviderProps {
  children: ReactNode;
}

export function GeoProvider({ children }: GeoProviderProps) {
  const [state, setState] = useState<GeoState>({
    allowed: true, // Default to allowed until check completes
    countryCode: '',
    countryName: '',
    isLoading: true,
    isChecked: false,
  });

  const checkGeo = useCallback(async () => {
    // Check cache first
    const cached = getCachedGeo();
    if (cached) {
      setState({
        allowed: cached.allowed,
        countryCode: cached.countryCode,
        countryName: cached.countryName,
        isLoading: false,
        isChecked: true,
      });
      return;
    }

    setState(prev => ({ ...prev, isLoading: true }));

    try {
      const response = await api.get('/geo/check');
      const { allowed, country_code, country_name } = response.data;

      // Cache the result
      setCachedGeo({
        allowed,
        countryCode: country_code,
        countryName: country_name,
      });

      setState({
        allowed,
        countryCode: country_code,
        countryName: country_name,
        isLoading: false,
        isChecked: true,
      });
    } catch (error) {
      console.error('Geo check failed:', error);
      // On error, default to allowed (fail open)
      setState({
        allowed: true,
        countryCode: 'UNKNOWN',
        countryName: 'Unknown',
        isLoading: false,
        isChecked: true,
      });
    }
  }, []);

  const recheckGeo = useCallback(async () => {
    // Clear cache and recheck
    localStorage.removeItem(GEO_CACHE_KEY);
    await checkGeo();
  }, [checkGeo]);

  // Check geo on mount
  useEffect(() => {
    checkGeo();
  }, [checkGeo]);

  const value: GeoContextValue = {
    ...state,
    recheckGeo,
  };

  return <GeoContext.Provider value={value}>{children}</GeoContext.Provider>;
}
