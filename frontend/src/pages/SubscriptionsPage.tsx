import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BadgeCheck, Bitcoin, Copy, ExternalLink, Loader2, MessageCircleMore, RefreshCcw } from 'lucide-react';
import { Container } from '@/components/layout';
import { useAuth } from '@/contexts/AuthContext';
import { billingService, type BillingPricingConfig } from '@/services/billingService';
import type { SubscriptionTier } from '@/types';

interface Plan {
  tier: Exclude<SubscriptionTier, 'free'>;
  name: string;
  monthlyCredits: number;
}

type SubscriptionCycle = '1m' | '3m' | '12m';

interface CycleConfig {
  priceCents: number;
  compareAtPriceCents?: number;
  discountLabel?: string;
  label: string;
  checkoutDescription: string;
  metadataPeriod: 'month' | 'quarter' | 'year';
  monthlyCredits: number;
}

const plans: Plan[] = [{ tier: 'premium', name: 'Premium', monthlyCredits: 100 }];

const cycleConfig: Record<SubscriptionCycle, CycleConfig> = {
  '1m': {
    priceCents: 1399,
    compareAtPriceCents: undefined,
    discountLabel: '',
    label: '1 month',
    checkoutDescription: '1-month plan',
    metadataPeriod: 'month',
    monthlyCredits: 100,
  },
  '3m': {
    priceCents: 2697,
    compareAtPriceCents: 4197,
    discountLabel: '35% OFF',
    label: '3 months',
    checkoutDescription: '3-month plan ($8.99/mo)',
    metadataPeriod: 'quarter',
    monthlyCredits: 100,
  },
  '12m': {
    priceCents: 4788,
    compareAtPriceCents: 16788,
    discountLabel: '70% OFF',
    label: '12 months',
    checkoutDescription: '12-month plan ($3.99/mo)',
    metadataPeriod: 'year',
    monthlyCredits: 100,
  },
};

export function SubscriptionsPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [selectedTier] = useState<Plan['tier']>('premium');
  const [billingCycle, setBillingCycle] = useState<SubscriptionCycle>('12m');
  const [loadingMethod, setLoadingMethod] = useState<'usdt' | 'telegram' | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [usdtOrder, setUsdtOrder] = useState<Record<string, unknown> | null>(null);
  const [usdtOrderId, setUsdtOrderId] = useState<string>('');
  const [txHash, setTxHash] = useState('');
  const [pricingConfig, setPricingConfig] = useState<BillingPricingConfig | null>(null);

  const selectedPlan = useMemo(
    () => plans.find((plan) => plan.tier === selectedTier) ?? plans[0],
    [selectedTier]
  );

  const selectedCycle = cycleConfig[billingCycle];
  const selectedPrice = selectedCycle.priceCents;
  const selectedPeriodLabel = selectedCycle.label;
  const saleEnds = '07 Min 10 Sec';
  const cycleOrder: SubscriptionCycle[] = ['12m', '3m', '1m'];
  const formatCents = (cents: number) => `$${(cents / 100).toFixed(2)}`;
  const freeBenefits = pricingConfig?.tier_benefits.free;
  const premiumBenefits = pricingConfig?.tier_benefits.premium;
  const creditCosts = pricingConfig?.credit_costs;

  useEffect(() => {
    const loadPricing = async () => {
      try {
        const config = await billingService.getPricingConfig();
        setPricingConfig(config);
      } catch (err) {
        console.error('Failed to load pricing config:', err);
      }
    };
    loadPricing();
  }, []);

  const ensureAuth = () => {
    if (!isAuthenticated) {
      navigate('/register');
      return false;
    }
    return true;
  };

  const handleUsdtCheckout = async () => {
    setError(null);
    if (!ensureAuth()) return;

    try {
      setLoadingMethod('usdt');
      const order = await billingService.createUsdtOrder({
        amount_usdt: Number((selectedPrice / 100).toFixed(2)),
        credits: selectedCycle.monthlyCredits,
        pack_id: `subscription_${selectedTier}_${billingCycle}`,
        metadata: {
          source: 'subscriptions_page',
          tier: selectedTier,
          billing_period: selectedCycle.metadataPeriod,
        },
      });
      setUsdtOrder(order.raw);
      setUsdtOrderId(order.order_id);
      setTxHash('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create USDT order');
    } finally {
      setLoadingMethod(null);
    }
  };

  const handleSubmitTxHash = async () => {
    if (!usdtOrderId || !txHash.trim()) return;
    try {
      setLoadingMethod('usdt');
      const updated = await billingService.submitUsdtOrderTx(usdtOrderId, txHash.trim());
      setUsdtOrder(updated.raw);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit transaction hash');
    } finally {
      setLoadingMethod(null);
    }
  };

  const handleRefreshUsdt = async () => {
    if (!usdtOrderId) return;
    try {
      setLoadingMethod('usdt');
      const updated = await billingService.refreshUsdtOrder(usdtOrderId);
      setUsdtOrder(updated.raw);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh USDT order status');
    } finally {
      setLoadingMethod(null);
    }
  };

  const handleTelegramCheckout = async () => {
    setError(null);
    if (!ensureAuth()) return;

    try {
      setLoadingMethod('telegram');
      const amountStars = selectedPrice;
      const order = await billingService.createTelegramStarsOrder({
        amount_stars: amountStars,
        credits: selectedCycle.monthlyCredits,
        pack_id: `subscription_${selectedTier}_${billingCycle}`,
        title: `${selectedPlan.name} Subscription`,
        description: selectedCycle.checkoutDescription,
        metadata: {
          source: 'subscriptions_page',
          tier: selectedTier,
          billing_period: selectedCycle.metadataPeriod,
        },
      });

      const invoice = await billingService.createTelegramStarsInvoiceLink(order.order_id, {
        title: `${selectedPlan.name} Subscription`,
        description: selectedCycle.checkoutDescription,
      });

      window.open(invoice.invoice_link, '_blank', 'noopener,noreferrer');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create Telegram Stars payment');
    } finally {
      setLoadingMethod(null);
    }
  };

  const usdtAddress = typeof usdtOrder?.payment_address === 'string' ? usdtOrder.payment_address : '';
  const usdtAmount = typeof usdtOrder?.amount_usdt === 'number' ? usdtOrder.amount_usdt : null;
  const usdtStatus = typeof usdtOrder?.status === 'string' ? usdtOrder.status : null;

  return (
    <div className="min-h-screen pb-16 bg-zinc-950">
      <Container>
        <div className="mb-6 rounded-xl border border-fuchsia-400/50 bg-gradient-to-r from-[#8b3f8e] to-[#7c3a88] px-5 py-3 text-center text-sm font-semibold tracking-wide text-white">
          SPRING DAY SALE 70% OFF
          <span className="ml-4 rounded bg-blue-500 px-2 py-0.5 text-[11px] font-bold">JOIN NOW</span>
          <span className="ml-4 text-[12px] text-white/80">{saleEnds}</span>
        </div>

        <div className="mx-auto max-w-5xl rounded-2xl border border-white/10 bg-gradient-to-br from-[#14161f] to-[#101219] p-5 md:p-8 overflow-hidden relative">
          <h1 className="text-center text-4xl font-heading font-bold text-white">Choose your Plan</h1>
          <p className="mt-2 text-center text-sm text-zinc-400">
            100% anonymous. You can cancel anytime.
          </p>

          {error && (
            <div className="mx-auto mt-5 max-w-2xl rounded-lg border border-red-400/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <div className="mt-7 grid gap-6 lg:grid-cols-[1.2fr_1fr]">
            <div className="rounded-2xl border border-white/10 bg-[#141822]/85 p-5 md:p-6 relative">
              <h2 className="text-3xl font-black leading-tight">
                <span className="text-lime-400">Spring Sale</span> <span className="text-white">for New Users</span>
              </h2>
              <p className="mt-2 text-sm text-zinc-300">Discount ends soon. <span className="text-rose-400">Don&apos;t miss out!</span></p>

              <div className="mt-5 space-y-3">
                {cycleOrder.map((cycle) => {
                  const cfg = cycleConfig[cycle];
                  const active = billingCycle === cycle;
                  return (
                    <button
                      key={cycle}
                      onClick={() => setBillingCycle(cycle)}
                      className={`w-full rounded-xl border px-4 py-3 text-left transition ${
                        active
                          ? 'border-rose-400 bg-rose-500/10 shadow-[0_0_0_1px_rgba(251,113,133,0.35)]'
                          : 'border-white/15 bg-white/[0.02] hover:border-zinc-500'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          {cycle === '12m' && (
                            <div className="mb-2 inline-flex rounded-full bg-rose-400 px-2 py-0.5 text-[10px] font-bold text-white">BEST CHOICE</div>
                          )}
                          <div className="text-xl font-bold text-white">{cfg.label}</div>
                          {cfg.discountLabel && <div className="mt-1 text-xs font-semibold text-rose-300">{cfg.discountLabel}</div>}
                        </div>
                        <div className="text-right">
                          {cfg.compareAtPriceCents && (
                            <div className="text-sm text-zinc-400 line-through">{formatCents(cfg.compareAtPriceCents / (cycle === '12m' ? 12 : 3))}</div>
                          )}
                          <div className="text-4xl font-extrabold leading-none text-white">{formatCents(cfg.priceCents / (cycle === '12m' ? 12 : cycle === '3m' ? 3 : 1))}</div>
                          <div className="text-xs text-zinc-400">/month</div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>

              <div className="mt-4 space-y-2 text-xs text-zinc-400">
                <p className="flex items-center gap-2"><BadgeCheck className="h-3.5 w-3.5 text-lime-400" /> Charge shown as &apos;EverAI&apos; on your bank statement</p>
                <p className="flex items-center gap-2"><BadgeCheck className="h-3.5 w-3.5 text-lime-400" /> No hidden fees �?Cancel subscription at any time</p>
              </div>

              <div className="mt-5 space-y-3">
                <button
                  onClick={handleTelegramCheckout}
                  disabled={loadingMethod !== null}
                  className="flex w-full items-center justify-between gap-3 rounded-xl border border-pink-400/30 bg-pink-500 px-4 py-3 text-white transition hover:bg-pink-400 disabled:opacity-60"
                >
                  <span className="flex items-center gap-2">
                    {loadingMethod === 'telegram' ? <Loader2 className="h-4 w-4 animate-spin" /> : <MessageCircleMore className="h-4 w-4" />}
                    <span className="font-semibold">Pay via Telegram Stars (VISA/MASTER)</span>
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="inline-flex h-5 items-center rounded bg-white px-1.5 text-[10px] font-bold tracking-wide text-[#1434CB]">
                      VISA
                    </span>
                    <span className="inline-flex h-5 items-center rounded bg-white px-1.5 text-[10px] font-semibold text-zinc-900">
                      <span className="mr-0.5 inline-block h-2.5 w-2.5 rounded-full bg-[#EB001B]" />
                      <span className="-ml-1 inline-block h-2.5 w-2.5 rounded-full bg-[#F79E1B]" />
                    </span>
                  </span>
                </button>

                <button
                  onClick={handleUsdtCheckout}
                  disabled={loadingMethod !== null}
                  className="flex w-full items-center justify-center gap-2 rounded-xl border border-zinc-700 bg-zinc-800/90 px-4 py-3 font-semibold text-white transition hover:bg-zinc-700 disabled:opacity-60"
                >
                  {loadingMethod === 'usdt' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Bitcoin className="h-4 w-4" />}
                  Pay with USDT
                </button>
              </div>

              <p className="mt-4 text-xs text-zinc-500 relative z-10">
                Selected: {selectedPlan.name} {selectedPeriodLabel}. Amount: {billingService.formatPrice(selectedPrice)}.
              </p>
              <p className="mt-1 text-xs text-zinc-500 relative z-10">
                Extra credit packs are available separately and never expire.
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-[#141822]/85 p-5 md:p-6 relative overflow-hidden">
              <h3 className="text-xl font-heading font-bold text-white">Free vs Premium</h3>
              <p className="mt-1 text-xs text-zinc-400">Compare key limits and daily credits</p>

              <div className="mt-4 rounded-xl border border-white/10 overflow-hidden">
                <div className="grid grid-cols-[1.3fr_0.85fr_0.85fr] bg-white/5 text-xs font-semibold text-zinc-300">
                  <div className="px-3 py-2">Feature</div>
                  <div className="px-3 py-2 text-center">Free</div>
                  <div className="px-3 py-2 text-center">Premium</div>
                </div>

                {[
                  {
                    feature: 'Daily login credits',
                    free: `${freeBenefits?.daily_checkin_credits ?? 2} / day`,
                    premium: `${premiumBenefits?.daily_checkin_credits ?? 2} / day`,
                  },
                  {
                    feature: 'Active characters',
                    free: `${freeBenefits?.character_limit ?? 2}`,
                    premium: `${premiumBenefits?.character_limit ?? 50}`,
                  },
                  {
                    feature: 'Image generation',
                    free: 'No',
                    premium: `Yes (${creditCosts?.image ?? 2} credits/image)`,
                  },
                  {
                    feature: 'Video generation',
                    free: 'No',
                    premium: `Yes (${creditCosts?.video ?? 4} credits/video)`,
                  },
                ].map((row) => (
                  <div
                    key={row.feature}
                    className="grid grid-cols-[1.3fr_0.85fr_0.85fr] border-t border-white/10 text-xs text-zinc-200"
                  >
                    <div className="px-3 py-2 text-zinc-300">{row.feature}</div>
                    <div className="px-3 py-2 text-center">{row.free}</div>
                    <div className="px-3 py-2 text-center text-amber-200">{row.premium}</div>
                  </div>
                ))}
              </div>

              <ul className="mt-4 space-y-2 text-xs text-zinc-300">
                <li className="flex items-start gap-2">
                  <BadgeCheck className="mt-0.5 h-3.5 w-3.5 text-amber-300" />
                  <span>Premium includes {selectedPlan.monthlyCredits.toLocaleString()} monthly credits from subscription.</span>
                </li>
                <li className="flex items-start gap-2">
                  <BadgeCheck className="mt-0.5 h-3.5 w-3.5 text-amber-300" />
                  <span>Text messaging is unlimited on Premium.</span>
                </li>
              </ul>
            </div>
          </div>

          {usdtOrderId && (
            <div className="mt-6 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-emerald-200">USDT Order Created</p>
                  <p className="text-xs text-zinc-400">Order ID: {usdtOrderId}</p>
                </div>
                <button
                  type="button"
                  onClick={handleRefreshUsdt}
                  disabled={loadingMethod !== null}
                  className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-200 hover:bg-zinc-800"
                >
                  <RefreshCcw className="h-3.5 w-3.5" />
                  Refresh Status
                </button>
              </div>

              {usdtAddress && (
                <div className="mt-3 rounded-lg border border-zinc-700 bg-zinc-900/80 p-3">
                  <p className="text-xs text-zinc-400">Pay to address</p>
                  <p className="mt-1 break-all text-sm text-white">{usdtAddress}</p>
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(usdtAddress)}
                    className="mt-2 inline-flex items-center gap-1 text-xs text-zinc-300 hover:text-white"
                  >
                    <Copy className="h-3.5 w-3.5" />
                    Copy address
                  </button>
                </div>
              )}

              <div className="mt-3 text-xs text-zinc-300">
                Amount: {usdtAmount ?? '-'} USDT | Status: <span className="font-semibold">{usdtStatus ?? '-'}</span>
              </div>

              <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                <input
                  value={txHash}
                  onChange={(e) => setTxHash(e.target.value)}
                  placeholder="Paste tx hash after transfer"
                  className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white outline-none ring-0 placeholder:text-zinc-500 focus:border-pink-500"
                />
                <button
                  type="button"
                  onClick={handleSubmitTxHash}
                  disabled={!txHash.trim() || loadingMethod !== null}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
                >
                  <ExternalLink className="h-4 w-4" />
                  Submit Tx Hash
                </button>
              </div>
            </div>
          )}
        </div>
      </Container>
    </div>
  );
}
