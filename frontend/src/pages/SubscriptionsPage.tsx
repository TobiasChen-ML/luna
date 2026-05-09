import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BadgeCheck, BookOpen, ExternalLink, Loader2, MessageCircleMore, Sparkles, Star, Wallet } from 'lucide-react';
import { Container } from '@/components/layout';
import { useAuth } from '@/contexts/AuthContext';
import { useTelegram } from '@/contexts/TelegramContext';
import { billingService } from '@/services/billingService';

type PaidTier = 'story_plus' | 'creator';
type SubscriptionCycle = '1m' | '3m' | '12m';
type CryptoAsset = 'USDT' | 'USDC';
type CryptoNetwork = 'POLYGON';

const cryptoNetworksByAsset: Record<CryptoAsset, CryptoNetwork[]> = {
  USDT: ['POLYGON'],
  USDC: ['POLYGON'],
};

interface CycleConfig {
  priceCents: number;
  compareAtPriceCents?: number;
  discountLabel?: string;
  label: string;
  shortLabel: string;
  checkoutDescription: string;
  metadataPeriod: 'month' | 'quarter' | 'year';
}

interface TierDef {
  id: PaidTier;
  name: string;
  monthlyCredits: number;
  icon: React.ReactNode;
  accent: string;
  cycles: Record<SubscriptionCycle, CycleConfig>;
}

const STAR_USD_CENTS = 2.04;
const usdCentsToStars = (priceCents: number) => Math.max(1, Math.round(priceCents / STAR_USD_CENTS));
const formatCents = (cents: number) => `$${(cents / 100).toFixed(2)}`;

const TIERS: TierDef[] = [
  {
    id: 'story_plus',
    name: 'Story+',
    monthlyCredits: 150,
    icon: <BookOpen size={18} />,
    accent: 'primary',
    cycles: {
      '1m': {
        priceCents: 999,
        label: '1 month',
        shortLabel: '/mo',
        checkoutDescription: 'Story+ — 1-month plan',
        metadataPeriod: 'month',
      },
      '3m': {
        priceCents: 1947,
        compareAtPriceCents: 2997,
        discountLabel: '35% OFF',
        label: '3 months',
        shortLabel: '/mo',
        checkoutDescription: 'Story+ — 3-month plan ($6.49/mo)',
        metadataPeriod: 'quarter',
      },
      '12m': {
        priceCents: 3588,
        compareAtPriceCents: 11988,
        discountLabel: '70% OFF',
        label: '12 months',
        shortLabel: '/mo',
        checkoutDescription: 'Story+ — 12-month plan ($2.99/mo)',
        metadataPeriod: 'year',
      },
    },
  },
  {
    id: 'creator',
    name: 'Creator',
    monthlyCredits: 300,
    icon: <Sparkles size={18} />,
    accent: 'amber',
    cycles: {
      '1m': {
        priceCents: 1999,
        label: '1 month',
        shortLabel: '/mo',
        checkoutDescription: 'Creator — 1-month plan',
        metadataPeriod: 'month',
      },
      '3m': {
        priceCents: 3897,
        compareAtPriceCents: 5997,
        discountLabel: '35% OFF',
        label: '3 months',
        shortLabel: '/mo',
        checkoutDescription: 'Creator — 3-month plan ($12.99/mo)',
        metadataPeriod: 'quarter',
      },
      '12m': {
        priceCents: 7188,
        compareAtPriceCents: 23988,
        discountLabel: '70% OFF',
        label: '12 months',
        shortLabel: '/mo',
        checkoutDescription: 'Creator — 12-month plan ($5.99/mo)',
        metadataPeriod: 'year',
      },
    },
  },
];

const CYCLE_ORDER: SubscriptionCycle[] = ['12m', '3m', '1m'];

const FEATURE_TABLE: { label: string; free: string; story_plus: string; creator: string }[] = [
  { label: 'Monthly credits', free: '20', story_plus: '150', creator: '300' },
  { label: 'Unlimited chat', free: 'Yes', story_plus: 'Yes', creator: 'Yes' },
  { label: 'Image generation', free: 'No', story_plus: 'Yes', creator: 'Yes' },
  { label: 'Generate story', free: 'No', story_plus: 'Yes', creator: 'Yes' },
  { label: 'Scene illustrations', free: 'No', story_plus: 'Yes', creator: 'Yes' },
  { label: 'Publish scripts', free: 'No', story_plus: 'No', creator: 'Yes' },
  { label: 'Creator revenue share', free: 'No', story_plus: 'No', creator: 'Yes' },
];

export function SubscriptionsPage() {
  const navigate = useNavigate();
  const { isAuthenticated, refreshUser } = useAuth();
  const { isTma, webApp } = useTelegram();

  const [selectedTierId, setSelectedTierId] = useState<PaidTier>('story_plus');
  const [billingCycle, setBillingCycle] = useState<SubscriptionCycle>('12m');
  const [loadingMethod, setLoadingMethod] = useState<'telegram' | 'crypto' | 'crypto-submit' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<CryptoAsset>('USDT');
  const [selectedNetwork, setSelectedNetwork] = useState<CryptoNetwork>('POLYGON');
  const [cryptoOrder, setCryptoOrder] = useState<Awaited<ReturnType<typeof billingService.createCryptoOrder>> | null>(null);
  const [txHash, setTxHash] = useState('');

  useEffect(() => {
    setError(null);
    setCryptoOrder(null);
    setTxHash('');
  }, [selectedTierId, billingCycle]);

  const selectedTier = TIERS.find((t) => t.id === selectedTierId) ?? TIERS[0];
  const selectedCycle = selectedTier.cycles[billingCycle];
  const selectedPrice = selectedCycle.priceCents;
  const selectedStars = usdCentsToStars(selectedPrice);

  const ensureAuth = () => {
    if (!isAuthenticated) {
      navigate('/register');
      return false;
    }
    return true;
  };

  const handleTelegramCheckout = async () => {
    setError(null);
    setSuccess(null);
    if (!ensureAuth()) return;
    try {
      setLoadingMethod('telegram');
      const order = await billingService.createTelegramStarsOrder({
        amount_stars: selectedStars,
        credits: selectedTier.monthlyCredits,
        product_type: 'subscription',
        tier: selectedTierId,
        billing_period: selectedCycle.metadataPeriod,
        pack_id: `subscription_${selectedTierId}_${billingCycle}`,
        title: `${selectedTier.name} Subscription`,
        description: selectedCycle.checkoutDescription,
        metadata: {
          source: 'subscriptions_page',
          tier: selectedTierId,
          billing_period: selectedCycle.metadataPeriod,
        },
      });

      const invoice = await billingService.createTelegramStarsInvoiceLink(order.order_id, {
        title: `${selectedTier.name} Subscription`,
        description: selectedCycle.checkoutDescription,
      });

      if (webApp) {
        webApp.openInvoice(invoice.invoice_link, async (status) => {
          if (status === 'paid') {
            setError(null);
            for (let attempt = 0; attempt < 5; attempt += 1) {
              const latestOrder = await billingService.getTelegramStarsOrder(order.order_id);
              if (latestOrder.status === 'paid') break;
              await new Promise((resolve) => setTimeout(resolve, 1200));
            }
            await refreshUser();
            setSuccess('Payment successful. Subscription is now active.');
            return;
          }
          if (status === 'cancelled') {
            setError('Payment cancelled.');
            return;
          }
          setError('Payment failed. Please try again.');
        });
      } else {
        window.location.href = invoice.invoice_link;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create Telegram Stars payment');
    } finally {
      setLoadingMethod(null);
    }
  };

  const handleCryptoCheckout = async () => {
    setError(null);
    setSuccess(null);
    setCryptoOrder(null);
    if (!ensureAuth()) return;
    try {
      setLoadingMethod('crypto');
      const order = await billingService.createCryptoOrder({
        asset: selectedAsset,
        network: selectedNetwork,
        product_type: 'subscription',
        tier: selectedTierId,
        billing_period: billingCycle,
        pack_id: `subscription_${selectedTierId}_${billingCycle}`,
        metadata: {
          source: 'subscriptions_page',
          tier: selectedTierId,
          billing_period: billingCycle,
          access_model: 'one_time_entitlement',
        },
      });
      setCryptoOrder(order);
      if (order.checkout_url) {
        window.location.href = order.checkout_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create crypto payment');
    } finally {
      setLoadingMethod(null);
    }
  };

  const handleCryptoAssetChange = (asset: CryptoAsset) => {
    setSelectedAsset(asset);
    setSelectedNetwork(cryptoNetworksByAsset[asset][0]);
    setCryptoOrder(null);
    setTxHash('');
  };

  const handleSubmitCryptoTx = async () => {
    if (!cryptoOrder || !txHash.trim()) return;
    try {
      setLoadingMethod('crypto-submit');
      await billingService.submitCryptoOrderTx(cryptoOrder.order_id, txHash.trim());
      const latest = await billingService.getCryptoOrder(cryptoOrder.order_id);
      setCryptoOrder(latest);
      setSuccess('Transaction submitted. Subscription activates after gateway confirmation.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit transaction');
    } finally {
      setLoadingMethod(null);
    }
  };

  return (
    <div className="min-h-screen pb-16 bg-zinc-950">
      <Container>
        {/* Sale banner */}
        <div className="mb-6 rounded-xl border border-fuchsia-400/50 bg-gradient-to-r from-[#8b3f8e] to-[#7c3a88] px-5 py-3 text-center text-sm font-semibold tracking-wide text-white">
          SPRING DAY SALE 70% OFF
          <span className="ml-4 rounded bg-blue-500 px-2 py-0.5 text-[11px] font-bold">JOIN NOW</span>
        </div>

        <div className="mx-auto max-w-5xl rounded-2xl border border-white/10 bg-gradient-to-br from-[#14161f] to-[#101219] p-5 md:p-8 overflow-hidden">
          <h1 className="text-center text-3xl sm:text-4xl font-heading font-bold text-white">Choose your Plan</h1>
          <p className="mt-2 text-center text-sm text-zinc-400">
            Purchases use Telegram Stars. Benefits work across Telegram Mini App, Web, and PWA.
          </p>

          {error && (
            <div className="mx-auto mt-5 max-w-2xl rounded-lg border border-red-400/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}
          {success && (
            <div className="mx-auto mt-5 max-w-2xl rounded-lg border border-emerald-400/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
              {success}
            </div>
          )}

          {/* Tier selector — horizontal scroll on mobile */}
          <div className="mt-7 flex gap-3 overflow-x-auto snap-x snap-mandatory pb-2 -mx-1 px-1 scrollbar-none">
            {/* Free card */}
            <div className="snap-start shrink-0 w-[72%] sm:w-auto sm:flex-1 rounded-2xl border border-white/10 bg-white/[0.03] p-4 flex flex-col gap-2 opacity-60">
              <div className="flex items-center gap-2 text-zinc-400">
                <MessageCircleMore size={18} />
                <span className="font-bold text-base">Free</span>
              </div>
              <p className="text-2xl font-extrabold text-white">$0</p>
              <p className="text-xs text-zinc-500">20 credits / mo</p>
              <ul className="mt-2 space-y-1 text-xs text-zinc-500">
                <li className="flex items-center gap-1.5"><BadgeCheck size={13} className="text-zinc-600" /> Basic chat</li>
                <li className="flex items-center gap-1.5"><BadgeCheck size={13} className="text-zinc-600" /> 2 characters</li>
              </ul>
              <p className="mt-auto text-xs text-zinc-600 font-medium">Current plan</p>
            </div>

            {/* Paid tier cards */}
            {TIERS.map((tier) => {
              const cycle = tier.cycles[billingCycle];
              const monthlyPrice = billingCycle === '12m'
                ? cycle.priceCents / 12
                : billingCycle === '3m'
                  ? cycle.priceCents / 3
                  : cycle.priceCents;
              const active = selectedTierId === tier.id;
              const isCreator = tier.id === 'creator';

              return (
                <button
                  key={tier.id}
                  onClick={() => setSelectedTierId(tier.id)}
                  className={`snap-start shrink-0 w-[72%] sm:w-auto sm:flex-1 rounded-2xl border p-4 text-left transition-all duration-200 flex flex-col gap-2 ${
                    active
                      ? isCreator
                        ? 'border-amber-400/60 bg-amber-500/10 shadow-[0_0_20px_rgba(245,158,11,0.15)]'
                        : 'border-primary-400/60 bg-primary-500/10 shadow-[0_0_20px_rgba(139,92,246,0.15)]'
                      : 'border-white/10 bg-white/[0.03] hover:border-white/20'
                  }`}
                >
                  {isCreator && (
                    <div className="self-start rounded-full bg-amber-400/20 border border-amber-400/30 px-2 py-0.5 text-[10px] font-bold text-amber-300 uppercase tracking-wide">
                      Best Value
                    </div>
                  )}
                  <div className={`flex items-center gap-2 ${isCreator ? 'text-amber-400' : 'text-primary-400'}`}>
                    {tier.icon}
                    <span className="font-bold text-base text-white">{tier.name}</span>
                  </div>
                  <div>
                    <span className="text-2xl font-extrabold text-white">{formatCents(monthlyPrice)}</span>
                    <span className="text-xs text-zinc-400">/mo</span>
                  </div>
                  {cycle.discountLabel && (
                    <span className="self-start rounded-full bg-rose-500/20 border border-rose-400/30 px-2 py-0.5 text-[10px] font-bold text-rose-300">
                      {cycle.discountLabel}
                    </span>
                  )}
                  <p className="text-xs text-zinc-400">{tier.monthlyCredits} credits / mo</p>
                  <ul className="mt-1 space-y-1 text-xs text-zinc-300">
                    <li className="flex items-center gap-1.5">
                      <BadgeCheck size={13} className={isCreator ? 'text-amber-400' : 'text-primary-400'} />
                      Generate stories
                    </li>
                    <li className="flex items-center gap-1.5">
                      <BadgeCheck size={13} className={isCreator ? 'text-amber-400' : 'text-primary-400'} />
                      Scene illustrations
                    </li>
                    {isCreator && (
                      <li className="flex items-center gap-1.5">
                        <BadgeCheck size={13} className="text-amber-400" />
                        Publish & earn
                      </li>
                    )}
                  </ul>
                  {active && (
                    <div className={`mt-auto self-start rounded-full px-3 py-1 text-xs font-semibold ${isCreator ? 'bg-amber-500/20 text-amber-300' : 'bg-primary-500/20 text-primary-300'}`}>
                      Selected
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Cycle selector */}
          <div className="mt-5 flex gap-2">
            {CYCLE_ORDER.map((cycle) => {
              const cfg = selectedTier.cycles[cycle];
              const active = billingCycle === cycle;
              return (
                <button
                  key={cycle}
                  onClick={() => setBillingCycle(cycle)}
                  className={`flex-1 rounded-xl border px-3 py-2.5 text-xs font-medium transition-all ${
                    active
                      ? 'border-rose-400/60 bg-rose-500/15 text-white'
                      : 'border-white/10 bg-white/[0.02] text-zinc-400 hover:border-zinc-500'
                  }`}
                >
                  <div className="font-semibold">{cfg.label}</div>
                  {cfg.discountLabel && (
                    <div className="mt-0.5 text-[10px] text-rose-300">{cfg.discountLabel}</div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Checkout */}
          <div className="mt-5 grid gap-5 lg:grid-cols-[1.3fr_1fr]">
            <div className="rounded-2xl border border-white/10 bg-[#141822]/85 p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm text-zinc-400">Selected plan</p>
                  <p className="font-bold text-white">{selectedTier.name} · {selectedCycle.label}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-extrabold text-white">{formatCents(selectedPrice)}</p>
                  <p className="text-xs text-amber-200 flex items-center gap-1 justify-end">
                    <Star size={11} className="fill-amber-300 text-amber-300" />
                    {selectedStars.toLocaleString()} Stars
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                <button
                  onClick={handleTelegramCheckout}
                  disabled={loadingMethod !== null}
                  className="flex w-full items-center justify-between gap-3 rounded-xl border border-pink-400/30 bg-pink-500 px-4 py-3 text-white transition hover:bg-pink-400 disabled:opacity-60"
                >
                  <span className="flex items-center gap-2">
                    {loadingMethod === 'telegram' ? <Loader2 className="h-4 w-4 animate-spin" /> : <MessageCircleMore className="h-4 w-4" />}
                    <span className="font-semibold">Pay with Telegram Stars</span>
                  </span>
                  {isTma && (
                    <span className="flex items-center gap-2">
                      <span className="inline-flex h-5 items-center rounded bg-white px-1.5 text-[10px] font-bold tracking-wide text-[#1434CB]">VISA</span>
                      <span className="inline-flex h-5 items-center rounded bg-white px-1.5 text-[10px] font-semibold text-zinc-900">
                        <span className="mr-0.5 inline-block h-2.5 w-2.5 rounded-full bg-[#EB001B]" />
                        <span className="-ml-1 inline-block h-2.5 w-2.5 rounded-full bg-[#F79E1B]" />
                      </span>
                    </span>
                  )}
                </button>

                <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                  <div className="mb-3 grid grid-cols-2 gap-2">
                    <select
                      value={selectedAsset}
                      onChange={(e) => handleCryptoAssetChange(e.target.value as CryptoAsset)}
                      className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white"
                    >
                      <option value="USDT">USDT</option>
                      <option value="USDC">USDC</option>
                    </select>
                    <select
                      value={selectedNetwork}
                      onChange={(e) => setSelectedNetwork(e.target.value as CryptoNetwork)}
                      className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white"
                    >
                      {cryptoNetworksByAsset[selectedAsset].map((network) => (
                        <option key={network} value={network}>Polygon</option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={handleCryptoCheckout}
                    disabled={loadingMethod !== null}
                    className="flex w-full items-center justify-between gap-3 rounded-xl border border-emerald-400/30 bg-emerald-500/15 px-4 py-3 text-emerald-100 transition hover:bg-emerald-500/25 disabled:opacity-60"
                  >
                    <span className="flex items-center gap-2">
                      {loadingMethod === 'crypto' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wallet className="h-4 w-4" />}
                      <span className="font-semibold">Pay with {selectedAsset}</span>
                    </span>
                    <span className="text-xs text-emerald-200">{selectedNetwork}</span>
                  </button>

                  {cryptoOrder && (
                    <div className="mt-3 space-y-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-100">
                      <div className="flex items-center justify-between gap-3">
                        <span>{cryptoOrder.asset} {cryptoOrder.network}</span>
                        <span>{cryptoOrder.amount_crypto ?? cryptoOrder.amount} {cryptoOrder.asset}</span>
                      </div>
                      {cryptoOrder.payment_address && (
                        <div className="break-all rounded bg-black/30 p-2 font-mono text-xs">{cryptoOrder.payment_address}</div>
                      )}
                      {cryptoOrder.payment_uri && (
                        <a href={cryptoOrder.payment_uri} className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-200 hover:text-emerald-100">
                          <ExternalLink className="h-3 w-3" />
                          Open wallet payment link
                        </a>
                      )}
                      <div className="flex gap-2">
                        <input
                          value={txHash}
                          onChange={(e) => setTxHash(e.target.value)}
                          placeholder="Transaction hash"
                          className="min-w-0 flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white"
                        />
                        <button
                          onClick={handleSubmitCryptoTx}
                          disabled={!txHash.trim() || loadingMethod === 'crypto-submit'}
                          className="rounded-lg bg-emerald-500 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"
                        >
                          {loadingMethod === 'crypto-submit' ? '...' : 'Submit'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <p className="mt-4 text-xs text-zinc-500">
                Crypto purchases activate a fixed access period, not auto-renewal.
              </p>
            </div>

            {/* Feature comparison table */}
            <div className="rounded-2xl border border-white/10 bg-[#141822]/85 p-5">
              <h3 className="text-base font-heading font-bold text-white mb-1">Plan comparison</h3>
              <p className="text-xs text-zinc-400 mb-4">All features included in each tier</p>

              <div className="rounded-xl border border-white/10 overflow-hidden">
                <div className="grid grid-cols-[1.4fr_0.7fr_0.7fr_0.7fr] bg-white/5 text-xs font-semibold text-zinc-300">
                  <div className="px-3 py-2">Feature</div>
                  <div className="px-2 py-2 text-center">Free</div>
                  <div className="px-2 py-2 text-center text-primary-300">Story+</div>
                  <div className="px-2 py-2 text-center text-amber-300">Creator</div>
                </div>

                {FEATURE_TABLE.map((row) => (
                  <div
                    key={row.label}
                    className="grid grid-cols-[1.4fr_0.7fr_0.7fr_0.7fr] border-t border-white/10 text-xs text-zinc-200"
                  >
                    <div className="px-3 py-2 text-zinc-300">{row.label}</div>
                    <div className="px-2 py-2 text-center text-zinc-500">{row.free}</div>
                    <div className="px-2 py-2 text-center text-primary-200">{row.story_plus}</div>
                    <div className="px-2 py-2 text-center text-amber-200">{row.creator}</div>
                  </div>
                ))}
              </div>

              <ul className="mt-4 space-y-2 text-xs text-zinc-400">
                <li className="flex items-start gap-2">
                  <BadgeCheck className="mt-0.5 h-3.5 w-3.5 text-primary-400 shrink-0" />
                  <span>Existing Premium subscribers keep all benefits — auto-mapped to Story+.</span>
                </li>
                <li className="flex items-start gap-2">
                  <BadgeCheck className="mt-0.5 h-3.5 w-3.5 text-primary-400 shrink-0" />
                  <span>Extra credit packs are available separately and never expire.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </Container>
    </div>
  );
}
