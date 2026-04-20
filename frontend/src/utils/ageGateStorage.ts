/**
 * Age Gate Storage Utilities
 * Handles localStorage and cookie storage for age verification state.
 */

const STORAGE_KEY = 'aigirl_age_verified';
const COOKIE_NAME = 'aigirl_age_gate';
const BLOCK_KEY = 'aigirl_age_blocked';
const TTL = 24 * 60 * 60 * 1000; // 24 hours
const BLOCK_TTL = 60 * 60 * 1000; // 1 hour block if under 18

interface AgeGateData {
  verified: boolean;
  timestamp: number;
  expiresAt: number;
}

interface BlockData {
  blocked: boolean;
  timestamp: number;
  expiresAt: number;
}

/**
 * Set age verified status in localStorage and cookie.
 */
export function setAgeVerified(): void {
  const data: AgeGateData = {
    verified: true,
    timestamp: Date.now(),
    expiresAt: Date.now() + TTL,
  };

  // localStorage
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // localStorage may not be available
  }

  // Cookie (for defense in depth)
  try {
    document.cookie = `${COOKIE_NAME}=1; max-age=${TTL / 1000}; path=/; SameSite=Strict`;
  } catch {
    // Cookie may not be available
  }
}

/**
 * Check if user has passed age verification.
 */
export function isAgeVerified(): boolean {
  // Check localStorage first
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const data: AgeGateData = JSON.parse(stored);
      if (data.verified && Date.now() < data.expiresAt) {
        return true;
      }
      // Clean up expired data
      localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // localStorage may not be available
  }

  // Fallback to cookie
  try {
    return document.cookie.includes(`${COOKIE_NAME}=1`);
  } catch {
    return false;
  }
}

/**
 * Clear age verification status.
 */
export function clearAgeVerified(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // localStorage may not be available
  }

  try {
    document.cookie = `${COOKIE_NAME}=; max-age=0; path=/; SameSite=Strict`;
  } catch {
    // Cookie may not be available
  }
}

/**
 * Set blocked status (user clicked "I am under 18").
 */
export function setBlocked(): void {
  const data: BlockData = {
    blocked: true,
    timestamp: Date.now(),
    expiresAt: Date.now() + BLOCK_TTL,
  };

  try {
    localStorage.setItem(BLOCK_KEY, JSON.stringify(data));
  } catch {
    // localStorage may not be available
  }
}

/**
 * Check if user is blocked (clicked "I am under 18").
 */
export function isBlocked(): boolean {
  try {
    const stored = localStorage.getItem(BLOCK_KEY);
    if (stored) {
      const data: BlockData = JSON.parse(stored);
      if (data.blocked && Date.now() < data.expiresAt) {
        return true;
      }
      // Clean up expired block
      localStorage.removeItem(BLOCK_KEY);
    }
  } catch {
    // localStorage may not be available
  }

  return false;
}

/**
 * Get remaining block time in milliseconds.
 */
export function getBlockTimeRemaining(): number {
  try {
    const stored = localStorage.getItem(BLOCK_KEY);
    if (stored) {
      const data: BlockData = JSON.parse(stored);
      if (data.blocked && Date.now() < data.expiresAt) {
        return data.expiresAt - Date.now();
      }
    }
  } catch {
    // localStorage may not be available
  }

  return 0;
}

/**
 * Clear blocked status.
 */
export function clearBlocked(): void {
  try {
    localStorage.removeItem(BLOCK_KEY);
  } catch {
    // localStorage may not be available
  }
}
