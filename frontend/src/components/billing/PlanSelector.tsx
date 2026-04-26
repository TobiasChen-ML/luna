/**
 * PlanSelector - Component for choosing subscription plans
 */
import { useMemo, useState } from 'react';
import { Check, Crown, Loader2 } from 'lucide-react';
import { Button } from '../common/Button';
import type { SubscriptionTier, BillingPeriod, BillingPricingConfig } from '../../types';
import { billingService } from '../../services/billingService';

interface PlanSelectorProps {
  currentTier: SubscriptionTier;
  pricingConfig: BillingPricingConfig | null;
  onSelectPlan: (tier: SubscriptionTier, period: BillingPeriod) => Promise<void>;
}

interface PlanFeature {
  text: string;
  included: boolean;
}

interface Plan {
  tier: SubscriptionTier;
  name: string;
  monthlyPrice: number;
  yearlyPrice: number;
  monthlyCredits: number;
  dailyCheckin: number;
  characterLimit: number;
  features: PlanFeature[];
  highlight?: boolean;
}

export function PlanSelector({ currentTier, pricingConfig, onSelectPlan }: PlanSelectorProps) {
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>('month');
  const [loading, setLoading] = useState<SubscriptionTier | null>(null);

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
        monthlyCredits: freeBenefits?.monthly_credits ?? 0,
        dailyCheckin: freeBenefits?.daily_checkin_credits ?? 0,
        characterLimit: freeBenefits?.character_limit ?? 2,
        features: [
          { text: `${freeBenefits?.daily_checkin_credits ?? 0} daily check-in credits`, included: true },
          { text: `${freeBenefits?.character_limit ?? 2} AI companions`, included: true },
          { text: 'Basic chat features', included: true },
          { text: 'Image generation', included: false },
          { text: 'Video generation', included: false },
          { text: 'Voice calls', included: false },
        ],
      },
      {
        tier: 'premium',
        name: 'Premium',
        monthlyPrice: premiumPrices?.month ?? 0,
        yearlyPrice: premiumPrices?.year ?? 0,
        monthlyCredits: premiumBenefits?.monthly_credits ?? 0,
        dailyCheckin: premiumBenefits?.daily_checkin_credits ?? 0,
        characterLimit: premiumBenefits?.character_limit ?? 50,
        features: [
          { text: `${premiumBenefits?.monthly_credits ?? 0} monthly credits`, included: true },
          { text: `${premiumBenefits?.daily_checkin_credits ?? 0} daily check-in credits`, included: true },
          { text: `${premiumBenefits?.character_limit ?? 50} AI companions`, included: true },
          { text: 'Image generation', included: true },
          { text: 'Video generation', included: true },
          { text: 'Voice calls', included: true },
        ],
        highlight: true,
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

  const handleSelect = async (tier: SubscriptionTier) => {
    if (tier === 'free' || tier === currentTier) return;

    setLoading(tier);
    try {
      await onSelectPlan(tier, billingPeriod);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-6">
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
      <p className="text-center text-xs text-zinc-500">
        Need more usage? Extra credit packs are activated in Telegram with Stars.
      </p>

      {/* Plans Grid */}
      <div className="grid md:grid-cols-3 gap-6">
        {!pricingConfig && (
          <div className="md:col-span-3 rounded-xl border border-zinc-700 bg-zinc-800/50 p-6 text-center text-zinc-400">
            Loading pricing...
          </div>
        )}
        {pricingConfig && plans.map((plan) => {
          const price = billingPeriod === 'month' ? plan.monthlyPrice : plan.yearlyPrice;
          const isCurrentPlan = plan.tier === currentTier;
          const canUpgrade = plan.tier !== 'free' && !isCurrentPlan;

          return (
            <div
              key={plan.tier}
              className={`relative rounded-2xl p-6 transition-all ${
                plan.highlight
                  ? 'border-2 border-pink-500/50 bg-gradient-to-b from-pink-500/10 to-transparent'
                  : 'border border-zinc-700 bg-zinc-800/50'
              } ${isCurrentPlan ? 'ring-2 ring-pink-500' : ''}`}
            >
              {/* Current plan badge */}
              {isCurrentPlan && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-pink-500 rounded-full text-xs font-medium text-white">
                  Current Plan
                </div>
              )}

              {/* Popular badge */}
              {plan.highlight && !isCurrentPlan && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-gradient-to-r from-pink-500 to-purple-500 rounded-full text-xs font-medium text-white">
                  Most Popular
                </div>
              )}

              {/* Plan header */}
              <div className="text-center mb-6">
                <div className={`inline-flex p-3 rounded-xl mb-3 ${
                  plan.tier === 'premium' ? 'bg-amber-500/20' : 'bg-zinc-700'
                }`}>
                  <Crown className={`w-6 h-6 ${
                    plan.tier === 'premium' ? 'text-amber-400' : 'text-zinc-400'
                  }`} />
                </div>
                <h3 className="text-xl font-bold text-white">{plan.name}</h3>
                <div className="mt-2">
                  <span className="text-3xl font-bold text-white">
                    {billingService.formatPrice(price)}
                  </span>
                  {price > 0 && (
                    <span className="text-zinc-400 text-sm">
                      /{billingPeriod === 'month' ? 'mo' : 'yr'}
                    </span>
                  )}
                </div>
                {plan.monthlyCredits > 0 && (
                  <p className="text-sm text-zinc-400 mt-1">
                    {plan.monthlyCredits.toLocaleString()} credits/month
                  </p>
                )}
              </div>

              {/* Features list */}
              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <Check
                      className={`w-4 h-4 flex-shrink-0 ${
                        feature.included ? 'text-green-400' : 'text-zinc-600'
                      }`}
                    />
                    <span className={feature.included ? 'text-zinc-300' : 'text-zinc-500 line-through'}>
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>

              {/* Action button */}
              {canUpgrade ? (
                <Button
                  onClick={() => handleSelect(plan.tier)}
                  disabled={loading !== null}
                  className="w-full"
                  variant={plan.highlight ? 'primary' : 'outline'}
                >
                  {loading === plan.tier ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    `Continue with ${plan.name}`
                  )}
                </Button>
              ) : isCurrentPlan ? (
                <Button disabled className="w-full" variant="outline">
                  Current Plan
                </Button>
              ) : (
                <Button disabled className="w-full" variant="ghost">
                  Free Forever
                </Button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
