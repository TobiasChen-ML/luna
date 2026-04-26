import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container } from '@/components/layout';
import { Button } from '@/components/common';
import { Check, Loader2, Crown } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { billingService } from '@/services/billingService';
import { openTelegramMiniApp } from '@/utils/telegram';
import type { SubscriptionTier, BillingPeriod, CreditPack, BillingPricingConfig } from '@/types';

interface Plan {
  tier: SubscriptionTier;
  name: string;
  monthlyPrice: number;
  yearlyPrice: number;
  description: string;
  features: string[];
  popular?: boolean;
}

export function PricingPage() {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>('month');
  const [loading] = useState<SubscriptionTier | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creditPacks, setCreditPacks] = useState<CreditPack[]>([]);
  const [pricingConfig, setPricingConfig] = useState<BillingPricingConfig | null>(null);

  const currentTier = user?.subscription_tier || 'free';

  useEffect(() => {
    const loadPricingPageData = async () => {
      try {
        const [packs, pricing] = await Promise.all([
          billingService.getCreditPacks(),
          billingService.getPricingConfig(),
        ]);
        setCreditPacks(packs);
        setPricingConfig(pricing);
      } catch (err) {
        console.error('Failed to load pricing page data:', err);
        setError('Failed to load pricing configuration');
      }
    };

    loadPricingPageData();
  }, []);

  const plans: Plan[] = useMemo(() => {
    const freeBenefits = pricingConfig?.tier_benefits.free;
    const premiumBenefits = pricingConfig?.tier_benefits.premium;
    const premiumPrices = pricingConfig?.subscription_prices.premium;

    return [
      {
        tier: 'free',
        name: 'Free',
        monthlyPrice: 0,
        yearlyPrice: 0,
        description: 'Start the story for free',
        features: [
          'Daily story credits',
          `${freeBenefits?.character_limit ?? 2} active characters`,
          'Core branching dialogue',
          'Community support',
        ],
      },
      {
        tier: 'premium',
        name: 'Premium',
        monthlyPrice: premiumPrices?.month ?? 0,
        yearlyPrice: premiumPrices?.year ?? 0,
        description: 'Maximum story depth',
        features: [
          `${premiumBenefits?.monthly_credits ?? 0} monthly credits`,
          `${premiumBenefits?.daily_checkin_credits ?? 0} daily check-in credits`,
          `${premiumBenefits?.character_limit ?? 50} active characters`,
          'Image generation',
          'Video generation',
          'Voice calls',
          'Fastest response time',
          'VIP priority support',
        ],
        popular: true,
      },
    ];
  }, [pricingConfig]);

  const yearlyDiscountPercent = useMemo(() => {
    const monthly = pricingConfig?.subscription_prices.premium.month ?? 0;
    const yearly = pricingConfig?.subscription_prices.premium.year ?? 0;
    if (monthly <= 0 || yearly <= 0) return 0;
    const yearlyMonthlyEquivalent = yearly / 12;
    const discount = (1 - yearlyMonthlyEquivalent / monthly) * 100;
    return Math.max(0, Math.round(discount));
  }, [pricingConfig]);

  const handleSelectPlan = async (tier: SubscriptionTier) => {
    setError(null);

    // Free tier - just go to register or chat
    if (tier === 'free') {
      navigate(isAuthenticated ? '/chat' : '/register');
      return;
    }

    // For paid tiers, user needs to be authenticated
    if (!isAuthenticated) {
      navigate('/register');
      return;
    }

    // If already on this tier, go to billing
    if (tier === currentTier) {
      navigate('/billing');
      return;
    }

    openTelegramMiniApp(`subscription_${tier}_${billingPeriod}`);
  };

  const getButtonText = (tier: SubscriptionTier) => {
    if (tier === 'free') return 'Get Started';
    if (tier === currentTier) return 'Current Plan';
    return 'Continue in Telegram';
  };

  return (
    <div className="min-h-screen pt-24 pb-20">
      <Container>
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl md:text-6xl font-heading font-bold mb-6">
            Simple, Transparent{' '}
            <span className="gradient-text">Pricing</span>
          </h1>
          <p className="text-xl text-zinc-400 max-w-3xl mx-auto mb-8">
            Choose how fast you want to progress through scenes and relationship levels.
            Purchases are completed in Telegram with Stars. Once activated, your benefits work
            across Telegram Mini App, Web, and PWA.
          </p>
          <p className="mx-auto mb-8 max-w-2xl rounded-xl border border-sky-500/30 bg-sky-500/10 px-4 py-3 text-sm text-sky-200">
            Web and PWA access are for using existing benefits. Upgrade or buy credits by
            continuing in Telegram.
          </p>

          {/* Billing Period Toggle */}
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => setBillingPeriod('month')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                billingPeriod === 'month'
                  ? 'bg-pink-500/20 text-pink-400 border border-pink-500/30'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod('year')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                billingPeriod === 'year'
                  ? 'bg-pink-500/20 text-pink-400 border border-pink-500/30'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              Yearly
              {yearlyDiscountPercent > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full">
                  Save {yearlyDiscountPercent}%
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="max-w-md mx-auto mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-center">
            {error}
          </div>
        )}

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-20">
          {!pricingConfig && (
            <div className="md:col-span-3 card-glass p-6 text-center text-zinc-400">
              Loading pricing...
            </div>
          )}
          {pricingConfig && plans.map((plan) => {
            const price = billingPeriod === 'month' ? plan.monthlyPrice : plan.yearlyPrice;
            const isCurrentPlan = plan.tier === currentTier;

            return (
              <div
                key={plan.tier}
                className={`card-glass space-y-6 relative ${
                  plan.popular
                    ? 'border-primary-500 transform md:scale-105'
                    : ''
                } ${isCurrentPlan ? 'ring-2 ring-pink-500' : ''}`}
              >
                {/* Popular Badge */}
                {plan.popular && !isCurrentPlan && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-primary rounded-full text-xs font-bold">
                    MOST POPULAR
                  </div>
                )}

                {/* Current Plan Badge */}
                {isCurrentPlan && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-pink-500 rounded-full text-xs font-bold text-white">
                    CURRENT PLAN
                  </div>
                )}

                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Crown
                      size={20}
                      className={
                        plan.tier === 'premium'
                          ? 'text-amber-400'
                          : 'text-zinc-500'
                      }
                    />
                    <h3 className="text-2xl font-heading font-bold">{plan.name}</h3>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-5xl font-bold">
                      {billingService.formatPrice(price)}
                    </span>
                    {price > 0 && (
                      <span className="text-zinc-400">
                        /{billingPeriod === 'month' ? 'mo' : 'yr'}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-zinc-500 mt-2">{plan.description}</p>
                </div>

                <ul className="space-y-3">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-center gap-3 text-zinc-300">
                      <Check size={18} className="text-primary-500 flex-shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  variant={plan.popular ? 'primary' : 'secondary'}
                  className="w-full"
                  onClick={() => handleSelectPlan(plan.tier)}
                  disabled={loading !== null || isCurrentPlan}
                >
                  {loading === plan.tier ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Opening Telegram...
                    </>
                  ) : (
                    getButtonText(plan.tier)
                  )}
                </Button>
              </div>
            );
          })}
        </div>

        {/* Credit Costs Info */}
        <div className="max-w-4xl mx-auto mb-20">
          <h2 className="text-2xl font-heading font-bold text-center mb-8">
            Credit Costs
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { name: 'Story Reply (Free for paid)', cost: pricingConfig?.credit_costs.message ?? 0 },
              { name: 'Image Generation', cost: pricingConfig?.credit_costs.image ?? 0 },
              { name: 'Video Generation', cost: pricingConfig?.credit_costs.video ?? 0 },
              { name: 'Voice Call (per min)', cost: pricingConfig?.credit_costs.voice_call_per_minute ?? 0 },
            ].map((item) => (
              <div key={item.name} className="card-glass text-center p-4">
                <p className="text-2xl font-bold text-white mb-1">{item.cost}</p>
                <p className="text-sm text-zinc-400">{item.name}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Token Packs */}
        <div className="max-w-5xl mx-auto mb-20">
          <h2 className="text-2xl font-heading font-bold text-center mb-2">
            Token Packs
          </h2>
          <p className="text-center text-zinc-400 mb-8">
            Need more usage? Buy additional tokens in Telegram. Purchased tokens never expire
            and can be used here after activation.
          </p>

          {creditPacks.length > 0 ? (
            <div className="grid md:grid-cols-3 gap-6">
              {creditPacks.map((pack) => (
                <div
                  key={pack.id}
                  className={`card-glass p-6 text-center ${
                    pack.is_popular ? 'border border-pink-500/40' : ''
                  }`}
                >
                  {pack.is_popular && (
                    <div className="inline-block mb-3 px-3 py-1 rounded-full bg-pink-500/20 text-pink-300 text-xs font-semibold">
                      MOST POPULAR
                    </div>
                  )}
                  <h3 className="text-xl font-bold text-white">{pack.name}</h3>
                  <p className="text-sm text-zinc-400 mt-1">{pack.description}</p>
                  <p className="text-3xl font-bold text-white mt-4">
                    {pack.credits.toLocaleString()}
                  </p>
                  <p className="text-sm text-zinc-400">tokens</p>
                  <p className="text-xl font-semibold text-white mt-3">
                    {billingService.formatPrice(pack.price_cents, pack.currency)}
                  </p>
                  <Button
                    className="w-full mt-4"
                    onClick={() => {
                      if (!isAuthenticated) {
                        navigate('/register');
                        return;
                      }
                      openTelegramMiniApp(`credits_${pack.id}`);
                    }}
                  >
                    Buy in Telegram
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="card-glass p-6 text-center text-zinc-400">
              Token packs are available from Billing.
            </div>
          )}
        </div>

        {/* FAQ Section */}
        <div className="max-w-3xl mx-auto space-y-6">
          <h2 className="text-3xl font-heading font-bold text-center mb-8">
            Pricing FAQs
          </h2>

          {[
            {
              q: 'Can I switch plans anytime?',
              a: "Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately, and we'll prorate the difference.",
            },
            {
              q: 'What payment methods do you accept?',
              a: 'Digital purchases are completed in the Telegram Mini App using Telegram Stars. Web and PWA users are redirected to Telegram to activate paid benefits.',
            },
            {
              q: 'Do unused credits roll over?',
              a: "Monthly subscription credits reset each billing cycle and don't roll over. However, purchased credit packs never expire!",
            },
            {
              q: 'Can I buy extra credits?',
              a: 'Yes. Extra credit packs are purchased in Telegram with Stars, then the credits can be used across Telegram Mini App, Web, and PWA.',
            },
            {
              q: 'Can I cancel my subscription?',
              a: 'Absolutely. You can cancel anytime from your billing page. Your subscription will remain active until the end of your billing period.',
            },
          ].map((faq, idx) => (
            <div key={idx} className="card-glass space-y-3">
              <h3 className="text-xl font-heading font-bold text-white">{faq.q}</h3>
              <p className="text-zinc-400">{faq.a}</p>
            </div>
          ))}
        </div>
      </Container>
    </div>
  );
}
