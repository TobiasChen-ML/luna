/**
 * TelegramStarsPayment — Stars credit pack purchase UI for Telegram Mini App.
 *
 * Flow:
 *   1. User taps a pack → create order → get invoice link → openInvoice()
 *   2. On 'paid' callback → poll order status until confirmed (max 30s)
 *   3. Call onSuccess so parent can refresh credit balance
 */
import { useState } from 'react';
import { CheckCircle, Loader2, Star, XCircle } from 'lucide-react';
import { useTelegram } from '@/contexts/TelegramContext';
import { billingService } from '@/services/billingService';

// ─── Stars pack definitions ──────────────────────────────────────────────────
// 1 Star ≈ $0.013 USD. Adjust amounts as needed.

interface StarsPack {
  id: string;
  label: string;
  credits: number;
  stars: number;
  isPopular?: boolean;
  description: string;
}

const STARS_PACKS: StarsPack[] = [
  { id: 'stars_starter', label: 'Starter',  credits: 50,   stars: 75,   description: '50 credits' },
  { id: 'stars_popular', label: 'Popular',  credits: 200,  stars: 250,  description: '200 credits', isPopular: true },
  { id: 'stars_power',   label: 'Power',    credits: 500,  stars: 550,  description: '500 credits' },
  { id: 'stars_ultra',   label: 'Ultra',    credits: 1000, stars: 990,  description: '1000 credits' },
];

// ─── Types ───────────────────────────────────────────────────────────────────

type PaymentState =
  | { status: 'idle' }
  | { status: 'loading'; packId: string }
  | { status: 'paid'; credits: number }
  | { status: 'cancelled' }
  | { status: 'failed'; message: string };

interface TelegramStarsPaymentProps {
  onSuccess?: (creditsAdded: number) => void;
}

// ─── Polling helper ──────────────────────────────────────────────────────────

async function pollOrderPaid(orderId: string, maxWaitMs = 30_000): Promise<boolean> {
  const interval = 2_000;
  const deadline = Date.now() + maxWaitMs;

  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, interval));
    try {
      const order = await billingService.getTelegramStarsOrder(orderId);
      if (order.status === 'paid') return true;
      if (order.status === 'failed') return false;
    } catch {
      // Network hiccup — keep polling
    }
  }
  return false;
}

// ─── Component ───────────────────────────────────────────────────────────────

export function TelegramStarsPayment({ onSuccess }: TelegramStarsPaymentProps) {
  const { webApp } = useTelegram();
  const [state, setState] = useState<PaymentState>({ status: 'idle' });

  const handleBuy = async (pack: StarsPack) => {
    if (!webApp) return;

    setState({ status: 'loading', packId: pack.id });

    try {
      // 1. Create order on backend
      const order = await billingService.createTelegramStarsOrder({
        amount_stars: pack.stars,
        credits: pack.credits,
        pack_id: pack.id,
        title: `${pack.credits} Credits`,
        description: `Top up ${pack.credits} AIGirl credits`,
        metadata: { purchase_type: 'credit_pack' },
      });

      // 2. Get Telegram invoice link
      const { invoice_link } = await billingService.createTelegramStarsInvoiceLink(
        order.order_id
      );

      // 3. Open native Telegram payment UI
      webApp.openInvoice(invoice_link, async (invoiceStatus) => {
        if (invoiceStatus === 'paid') {
          // 4. Poll backend until payment confirmed by webhook
          const confirmed = await pollOrderPaid(order.order_id);
          if (confirmed) {
            setState({ status: 'paid', credits: pack.credits });
            onSuccess?.(pack.credits);
          } else {
            setState({
              status: 'failed',
              message: 'Payment received but credits are taking longer than expected. Please check your balance in a moment.',
            });
          }
        } else if (invoiceStatus === 'cancelled') {
          setState({ status: 'cancelled' });
        } else {
          setState({ status: 'failed', message: 'Payment failed. Please try again.' });
        }
      });
    } catch (err) {
      setState({
        status: 'failed',
        message: err instanceof Error ? err.message : 'Something went wrong.',
      });
    }
  };

  // ── Success state ──
  if (state.status === 'paid') {
    return (
      <div className="flex flex-col items-center gap-4 py-10 px-6 text-center">
        <CheckCircle className="w-16 h-16 text-green-400" />
        <h3 className="text-xl font-bold text-white">Payment Successful!</h3>
        <p className="text-zinc-400">
          {state.credits} credits have been added to your account.
        </p>
        <button
          onClick={() => setState({ status: 'idle' })}
          className="mt-2 px-6 py-2 rounded-full bg-pink-600 text-white text-sm font-semibold"
        >
          Buy More
        </button>
      </div>
    );
  }

  // ── Cancelled state ──
  if (state.status === 'cancelled') {
    return (
      <div className="flex flex-col items-center gap-4 py-10 px-6 text-center">
        <XCircle className="w-12 h-12 text-zinc-500" />
        <p className="text-zinc-400">Payment cancelled.</p>
        <button
          onClick={() => setState({ status: 'idle' })}
          className="px-6 py-2 rounded-full bg-zinc-700 text-white text-sm font-semibold"
        >
          Back
        </button>
      </div>
    );
  }

  // ── Error state ──
  if (state.status === 'failed') {
    return (
      <div className="flex flex-col items-center gap-4 py-10 px-6 text-center">
        <XCircle className="w-12 h-12 text-red-400" />
        <p className="text-zinc-300 text-sm">{state.message}</p>
        <button
          onClick={() => setState({ status: 'idle' })}
          className="px-6 py-2 rounded-full bg-zinc-700 text-white text-sm font-semibold"
        >
          Try Again
        </button>
      </div>
    );
  }

  // ── Pack grid ──
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" />
        <h3 className="text-lg font-bold text-white">Buy Credits with Stars</h3>
      </div>
      <p className="text-xs text-zinc-400 mb-4">
        Pay with Telegram Stars — no credit card needed.
      </p>

      <div className="grid grid-cols-2 gap-3">
        {STARS_PACKS.map((pack) => {
          const isLoading = state.status === 'loading' && state.packId === pack.id;
          const isAnyLoading = state.status === 'loading';

          return (
            <button
              key={pack.id}
              onClick={() => handleBuy(pack)}
              disabled={isAnyLoading}
              className={`
                relative flex flex-col items-center gap-2 p-4 rounded-2xl border
                transition-all active:scale-95
                ${pack.isPopular
                  ? 'border-pink-500 bg-pink-500/10'
                  : 'border-zinc-700 bg-zinc-800/60'}
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              {pack.isPopular && (
                <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded-full bg-pink-600 text-[10px] font-bold text-white uppercase tracking-wide">
                  Popular
                </span>
              )}

              {isLoading ? (
                <Loader2 className="w-6 h-6 text-pink-400 animate-spin" />
              ) : (
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                  <span className="text-xl font-bold text-white">{pack.stars}</span>
                </div>
              )}

              <span className="text-sm font-semibold text-white">{pack.label}</span>
              <span className="text-xs text-zinc-400">{pack.description}</span>
            </button>
          );
        })}
      </div>

      <p className="text-[11px] text-zinc-500 text-center pt-2">
        Stars are Telegram's virtual currency. 1 Star ≈ $0.013 USD.
      </p>
    </div>
  );
}
