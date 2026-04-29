/**
 * SubscriptionCard - Displays current subscription status
 */
import { Crown, Calendar, AlertCircle, Loader2, RotateCcw, XCircle } from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import type { Subscription, SubscriptionTier, BillingPricingConfig } from '../../types';
import { billingService } from '../../services/billingService';

interface SubscriptionCardProps {
  subscription: Subscription | null;
  tier: SubscriptionTier;
  pricingConfig: BillingPricingConfig | null;
  isActive: boolean;
  onManage: () => void;
  onUpgrade: () => void;
  onCancel?: () => void;
  onReactivate?: () => void;
  isManaging?: boolean;
}

const tierColors: Record<SubscriptionTier, string> = {
  free: 'text-zinc-400',
  premium: 'text-amber-400',
};

const tierBadgeColors: Record<SubscriptionTier, string> = {
  free: 'bg-zinc-800 text-zinc-300',
  premium: 'bg-gradient-to-r from-amber-900/50 to-orange-900/50 text-amber-300 border border-amber-500/30',
};

export function SubscriptionCard({
  subscription,
  tier,
  pricingConfig,
  isActive,
  onManage,
  onUpgrade,
  onCancel,
  onReactivate,
  isManaging = false,
}: SubscriptionCardProps) {
  const tierName = billingService.getTierDisplayName(tier);
  const periodEnd = subscription?.current_period_end
    ? new Date(subscription.current_period_end).toLocaleDateString()
    : null;

  const monthlyCredits = pricingConfig?.tier_benefits[tier]?.monthly_credits ?? 0;

  return (
    <Card glass className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${tier === 'premium' ? 'bg-amber-500/20' : 'bg-zinc-700'}`}>
            <Crown className={`w-6 h-6 ${tierColors[tier]}`} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Subscription</h3>
            <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${tierBadgeColors[tier]}`}>
              {tierName}
            </span>
          </div>
        </div>

        {tier !== 'free' && isActive && subscription?.cancel_at_period_end && onReactivate && (
          <Button variant="outline" size="sm" onClick={onReactivate} disabled={isManaging}>
            {isManaging ? (
              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            ) : (
              <RotateCcw className="w-3 h-3 mr-1" />
            )}
            Reactivate
          </Button>
        )}
      </div>

      {/* Subscription Details */}
      {tier === 'free' ? (
        <div className="space-y-3">
          <p className="text-zinc-400 text-sm">
            You're on the free plan. Upgrade to get more credits and features.
          </p>
          <Button onClick={onUpgrade} className="w-full">
            Upgrade Now
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Period info */}
          {periodEnd && (
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <Calendar className="w-4 h-4" />
              <span>
                {subscription?.cancel_at_period_end
                  ? `Cancels on ${periodEnd}`
                  : `Renews on ${periodEnd}`}
              </span>
            </div>
          )}

          {/* Cancellation warning */}
          {subscription?.cancel_at_period_end && (
            <div className="flex items-start gap-2 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
              <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-amber-200">
                Your subscription will end on {periodEnd}. You'll lose access to {tierName} features.
              </p>
            </div>
          )}

          {/* Monthly credits info */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-zinc-400">Monthly Credits</span>
            <span className="text-white font-medium">
              {monthlyCredits.toLocaleString()}
            </span>
          </div>

          {isActive && !subscription?.cancel_at_period_end && onCancel && (
            <Button
              variant="outline"
              size="sm"
              onClick={onCancel}
              disabled={isManaging}
              className="w-full border-red-500/40 text-red-300 hover:bg-red-500/10"
            >
              {isManaging ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <XCircle className="w-4 h-4 mr-2" />
              )}
              Cancel at Period End
            </Button>
          )}

          {isActive && !onCancel && (
            <Button variant="outline" size="sm" onClick={onManage}>
              Manage Subscription
            </Button>
          )}
        </div>
      )}
    </Card>
  );
}
