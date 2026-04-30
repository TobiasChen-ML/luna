/**
 * Billing Service - API client for subscription and credit management
 */
import { auth } from '@/config/firebase';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

// Types
export type SubscriptionTier = 'free' | 'premium';
export type BillingPeriod = 'month' | 'year';
export type SubscriptionStatus = 'active' | 'past_due' | 'canceled' | 'incomplete';
export type PaymentType = 'subscription' | 'credit_pack' | 'refund';
export type PaymentStatus = 'succeeded' | 'pending' | 'failed' | 'refunded';

export interface Subscription {
  id: string;
  user_id: string;
  tier: SubscriptionTier;
  billing_period: BillingPeriod;
  status: SubscriptionStatus;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  canceled_at: string | null;
  created_at: string;
}

export interface CurrentSubscription {
  subscription: Subscription | null;
  tier: SubscriptionTier;
  is_active: boolean;
}

export interface CreditPack {
  id: string;
  name: string;
  credits: number;
  price_cents: number;
  currency: string;
  description: string;
  is_popular: boolean;
}

export interface SubscriptionPricePoint {
  month: number;
  year: number;
  currency: string;
}

export interface TierBenefitConfig {
  monthly_credits: number;
  daily_checkin_credits: number;
  character_limit: number;
}

export interface CreditCostConfig {
  message: number;
  image: number;
  video: number;
  voice_call_per_minute: number;
}

export interface BillingPricingConfig {
  subscription_prices: Record<SubscriptionTier, SubscriptionPricePoint>;
  credit_costs: CreditCostConfig;
  tier_benefits: Record<SubscriptionTier, TierBenefitConfig>;
}

export interface CreditBalance {
  total: number;
  monthly_remaining: number;
  purchased: number;
  next_reset: string | null;
  subscription_tier: SubscriptionTier;
}

export interface PaymentHistoryItem {
  id: string;
  type: PaymentType;
  amount_cents: number;
  currency: string;
  status: PaymentStatus;
  credits_granted: number | null;
  description: string;
  created_at: string;
}

export interface PaymentHistoryResponse {
  payments: PaymentHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface CheckoutResponse {
  checkout_url: string;
  session_id: string;
}

export interface GatewayOrderResponse {
  order_id: string;
  status: string;
  asset?: string;
  network?: string;
  amount?: number;
  amount_crypto?: number;
  amount_usd_cents?: number;
  credits?: number;
  product_type?: 'credit_pack' | 'subscription';
  pack_id?: string;
  tier?: SubscriptionTier;
  billing_period?: string;
  payment_address?: string;
  wallet_address?: string;
  payment_uri?: string;
  checkout_url?: string;
  expires_at?: string;
  raw: Record<string, unknown>;
}

export interface TelegramInvoiceLinkResponse {
  order_id: string;
  status: string;
  invoice_link: string;
  raw: Record<string, unknown>;
}

let pricingConfigCache: BillingPricingConfig | null = null;

// Helper to get auth token
async function getAuthToken(): Promise<string | null> {
  try {
    const user = auth.currentUser;
    if (!user) return null;
    return await user.getIdToken();
  } catch (error) {
    console.error('Failed to get Firebase auth token for billing request:', error);
    return null;
  }
}

// Helper for authenticated API calls
async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = await getAuthToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  return fetch(url, {
    ...options,
    headers,
  });
}

// Billing Service
export const billingService = {
  // ==================== Subscription ====================

  /**
   * Get current user's subscription status
   */
  async getCurrentSubscription(): Promise<CurrentSubscription> {
    const response = await authFetch(`${API_BASE}/billing/subscriptions/current`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get subscription');
    }

    return response.json();
  },

  /**
   * Create checkout session for subscription
   */
  async createSubscriptionCheckout(
    tier: SubscriptionTier,
    billingPeriod: BillingPeriod = 'month'
  ): Promise<CheckoutResponse> {
    const response = await authFetch(`${API_BASE}/billing/subscriptions/checkout`, {
      method: 'POST',
      body: JSON.stringify({
        tier,
        billing_period: billingPeriod,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create checkout');
    }

    return response.json();
  },

  /**
   * Get customer portal URL for managing subscription
   */
  async getPortalUrl(returnUrl?: string): Promise<string> {
    const response = await authFetch(`${API_BASE}/billing/subscriptions/portal`, {
      method: 'POST',
      body: JSON.stringify({ return_url: returnUrl }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get portal URL');
    }

    const data = await response.json();
    return data.portal_url;
  },

  /**
   * Cancel subscription at period end
   */
  async cancelSubscription(): Promise<{ success: boolean; cancel_at: string; message: string }> {
    const response = await authFetch(`${API_BASE}/billing/subscriptions/cancel`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to cancel subscription');
    }

    return response.json();
  },

  /**
   * Reactivate a canceled subscription
   */
  async reactivateSubscription(): Promise<{ success: boolean; message: string }> {
    const response = await authFetch(`${API_BASE}/billing/subscriptions/reactivate`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to reactivate subscription');
    }

    return response.json();
  },

  // ==================== Credit Packs ====================

  /**
   * Get available credit packs
   */
  async getCreditPacks(): Promise<CreditPack[]> {
    const response = await fetch(`${API_BASE}/billing/credit-packs`);

    if (!response.ok) {
      throw new Error('Failed to get credit packs');
    }

    const data = await response.json();
    return data.packs;
  },

  /**
   * Get pricing config (single source from backend config)
   */
  async getPricingConfig(): Promise<BillingPricingConfig> {
    if (pricingConfigCache) {
      return pricingConfigCache;
    }

    const response = await fetch(`${API_BASE}/billing/pricing`);

    if (!response.ok) {
      throw new Error('Failed to get pricing config');
    }

    const data = (await response.json()) as BillingPricingConfig;
    pricingConfigCache = data;
    return data;
  },

  /**
   * Create checkout session for credit pack purchase
   */
  async createCreditPackCheckout(packId: string): Promise<CheckoutResponse> {
    const response = await authFetch(`${API_BASE}/billing/credit-packs/checkout`, {
      method: 'POST',
      body: JSON.stringify({ pack_id: packId }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create checkout');
    }

    return response.json();
  },

  // ==================== USDT Gateway ====================

  async createCryptoOrder(payload: {
    asset: 'USDT' | 'USDC';
    network: 'POLYGON';
    product_type: 'credit_pack' | 'subscription';
    pack_id?: string;
    tier?: SubscriptionTier;
    billing_period?: string;
    metadata?: Record<string, unknown>;
  }): Promise<GatewayOrderResponse> {
    const response = await authFetch(`${API_BASE}/billing/crypto/orders`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create crypto order');
    }

    return response.json();
  },

  async getCryptoOrder(orderId: string): Promise<GatewayOrderResponse> {
    const response = await authFetch(`${API_BASE}/billing/crypto/orders/${orderId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to query crypto order');
    }

    return response.json();
  },

  async submitCryptoOrderTx(orderId: string, tx_hash: string): Promise<{ success: boolean; message: string }> {
    const response = await authFetch(`${API_BASE}/billing/crypto/orders/${orderId}/submit`, {
      method: 'POST',
      body: JSON.stringify({ tx_hash }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit crypto transaction');
    }

    return response.json();
  },

  async createUsdtOrder(payload: {
    amount_usdt: number;
    credits?: number;
    pack_id?: string;
    metadata?: Record<string, unknown>;
  }): Promise<GatewayOrderResponse> {
    const response = await authFetch(`${API_BASE}/billing/usdt/orders`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create USDT order');
    }

    return response.json();
  },

  async getUsdtOrder(orderId: string): Promise<GatewayOrderResponse> {
    const response = await authFetch(`${API_BASE}/billing/usdt/orders/${orderId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to query USDT order');
    }

    return response.json();
  },

  async submitUsdtOrderTx(orderId: string, tx_hash: string): Promise<GatewayOrderResponse> {
    const response = await authFetch(`${API_BASE}/billing/usdt/orders/${orderId}/submit`, {
      method: 'POST',
      body: JSON.stringify({ tx_hash }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit USDT transaction');
    }

    return response.json();
  },

  async refreshUsdtOrder(orderId: string): Promise<GatewayOrderResponse> {
    const response = await authFetch(`${API_BASE}/billing/usdt/orders/${orderId}/refresh`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to refresh USDT order');
    }

    return response.json();
  },

  // ==================== Telegram Stars Gateway ====================

  async createTelegramStarsOrder(payload: {
    amount_stars: number;
    credits?: number;
    product_type?: 'credit_pack' | 'subscription';
    tier?: SubscriptionTier;
    billing_period?: string;
    pack_id?: string;
    title?: string;
    description?: string;
    metadata?: Record<string, unknown>;
  }): Promise<GatewayOrderResponse> {
    const response = await authFetch(`${API_BASE}/billing/telegram-stars/orders`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create Telegram Stars order');
    }

    return response.json();
  },

  async createTelegramStarsInvoiceLink(
    orderId: string,
    payload?: { title?: string; description?: string }
  ): Promise<TelegramInvoiceLinkResponse> {
    const response = await authFetch(
      `${API_BASE}/billing/telegram-stars/orders/${orderId}/invoice-link`,
      {
        method: 'POST',
        body: JSON.stringify(payload || {}),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create Telegram invoice link');
    }

    return response.json();
  },

  async getTelegramStarsOrder(orderId: string): Promise<GatewayOrderResponse> {
    const response = await authFetch(
      `${API_BASE}/billing/telegram-stars/orders/${orderId}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get Telegram Stars order');
    }

    return response.json();
  },

  // ==================== Credits ====================

  /**
   * Get detailed credit balance breakdown
   */
  async getCreditBalance(): Promise<CreditBalance> {
    const response = await authFetch(`${API_BASE}/billing/credits/balance`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get credit balance');
    }

    return response.json();
  },

  // ==================== Payment History ====================

  /**
   * Get payment history
   */
  async getPaymentHistory(limit = 20, offset = 0): Promise<PaymentHistoryResponse> {
    const response = await authFetch(
      `${API_BASE}/billing/history?limit=${limit}&offset=${offset}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get payment history');
    }

    return response.json();
  },

  // ==================== Helpers ====================

  /**
   * Format price from cents to display string
   */
  formatPrice(cents: number, currency = 'usd'): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(cents / 100);
  },

  /**
   * Get tier display name
   */
  getTierDisplayName(tier: SubscriptionTier): string {
    const names: Record<SubscriptionTier, string> = {
      free: 'Free',
      premium: 'Premium',
    };
    return names[tier] || tier;
  },

  /**
   * Redirect to Stripe checkout
   */
  redirectToCheckout(checkoutUrl: string): void {
    window.location.href = checkoutUrl;
  },

  // ── Support Tickets ───────────────────────────────────────────────────────

  async submitSupportTicket(payload: {
    issue_type: 'missed_credits' | 'duplicate_charge' | 'other';
    description: string;
    order_id?: string;
  }): Promise<{ id: string; status: string }> {
    const resp = await authFetch(`${API_BASE}/billing/support`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error((err as { detail?: string }).detail || 'Failed to submit ticket');
    }
    return resp.json();
  },

  async listMyTickets(): Promise<SupportTicket[]> {
    const resp = await authFetch(`${API_BASE}/billing/support`);
    if (!resp.ok) throw new Error('Failed to load tickets');
    return resp.json();
  },
};

export interface SupportTicket {
  id: string;
  user_email: string;
  order_id: string | null;
  issue_type: string;
  description: string;
  status: string;
  credits_granted: number | null;
  created_at: string;
}

export default billingService;
