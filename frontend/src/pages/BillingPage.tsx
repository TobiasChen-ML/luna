/**
 * BillingPage - Main billing and subscription management page
 */
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CreditCard, History, Loader2, RefreshCw } from 'lucide-react';
import { Container } from '../components/layout/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { SubscriptionCard } from '../components/billing/SubscriptionCard';
import { CreditBalanceCard } from '../components/billing/CreditBalanceCard';
import { PlanSelector } from '../components/billing/PlanSelector';
import { CreditPackModal } from '../components/billing/CreditPackModal';
import { billingService, type CurrentSubscription, type CreditBalance, type PaymentHistoryItem } from '../services/billingService';
import { useTelegram } from '../contexts/TelegramContext';
import { openTelegramMiniApp } from '../utils/telegram';
import type { SubscriptionTier, BillingPeriod, BillingPricingConfig } from '../types';

export default function BillingPage() {
  const { isTma } = useTelegram();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [subscription, setSubscription] = useState<CurrentSubscription | null>(null);
  const [creditBalance, setCreditBalance] = useState<CreditBalance | null>(null);
  const [paymentHistory, setPaymentHistory] = useState<PaymentHistoryItem[]>([]);
  const [pricingConfig, setPricingConfig] = useState<BillingPricingConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [subscriptionBusy, setSubscriptionBusy] = useState(false);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [showPlanSelector, setShowPlanSelector] = useState(false);

  useEffect(() => {
    loadBillingData();
  }, []);

  useEffect(() => {
    if (searchParams.get('buyCredits') === '1') {
      setShowCreditModal(true);
    }
  }, [searchParams]);

  const loadBillingData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [subData, balanceData, historyData, pricingData] = await Promise.all([
        billingService.getCurrentSubscription(),
        billingService.getCreditBalance(),
        billingService.getPaymentHistory(10),
        billingService.getPricingConfig(),
      ]);

      setSubscription(subData);
      setCreditBalance(balanceData);
      setPaymentHistory(historyData.payments);
      setPricingConfig(pricingData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load billing data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    try {
      const portalUrl = await billingService.getPortalUrl();
      window.location.href = portalUrl;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to open billing portal');
    }
  };

  const handleCancelSubscription = async () => {
    try {
      setSubscriptionBusy(true);
      setError(null);
      setSuccess(null);
      const result = await billingService.cancelSubscription();
      await loadBillingData();
      setSuccess(result.message || 'Your subscription will stay active until the current period ends.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel subscription');
    } finally {
      setSubscriptionBusy(false);
    }
  };

  const handleReactivateSubscription = async () => {
    try {
      setSubscriptionBusy(true);
      setError(null);
      setSuccess(null);
      const result = await billingService.reactivateSubscription();
      await loadBillingData();
      setSuccess(result.message || 'Your subscription has been reactivated.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reactivate subscription');
    } finally {
      setSubscriptionBusy(false);
    }
  };

  const handleSelectPlan = async (tier: SubscriptionTier, period: BillingPeriod) => {
    if (!isTma) {
      openTelegramMiniApp(`subscription_${tier}_${period}`);
      return;
    }

    navigate('/subscriptions');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-pink-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 py-8">
      <Container size="lg">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Billing</h1>
            <p className="text-zinc-400">Manage your subscription and credits</p>
          </div>
          <Button variant="outline" onClick={loadBillingData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-lg text-green-300">
            {success}
          </div>
        )}

        {!isTma && (
          <div className="mb-8 rounded-2xl border border-sky-500/30 bg-sky-500/10 p-5">
            <h2 className="text-lg font-semibold text-sky-100">Purchases happen in Telegram</h2>
            <p className="mt-1 text-sm text-sky-200/90">
              Web and PWA access can use your active benefits. To upgrade or buy credits,
              continue in the Telegram Mini App and pay with Telegram Stars.
            </p>
            <Button className="mt-4" onClick={() => openTelegramMiniApp('billing')}>
              Continue in Telegram
            </Button>
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Subscription Card */}
          <SubscriptionCard
            subscription={subscription?.subscription || null}
            tier={subscription?.tier || 'free'}
            pricingConfig={pricingConfig}
            isActive={subscription?.is_active || false}
            onManage={handleManageSubscription}
            onUpgrade={() => setShowPlanSelector(true)}
            onCancel={handleCancelSubscription}
            onReactivate={handleReactivateSubscription}
            isManaging={subscriptionBusy}
          />

          {/* Credit Balance Card */}
          <CreditBalanceCard
            balance={creditBalance}
            onBuyCredits={() => setShowCreditModal(true)}
          />
        </div>

        {/* Plan Selector Section */}
        {showPlanSelector && (
          <div className="mb-8">
            <Card glass className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-white">Choose a Plan</h2>
                <Button variant="ghost" size="sm" onClick={() => setShowPlanSelector(false)}>
                  Cancel
                </Button>
              </div>
              <PlanSelector
                currentTier={subscription?.tier || 'free'}
                pricingConfig={pricingConfig}
                onSelectPlan={handleSelectPlan}
              />
            </Card>
          </div>
        )}

        {/* Upgrade CTA for Free Users */}
        {subscription?.tier === 'free' && !showPlanSelector && (
          <Card glass className="p-6 mb-8 bg-gradient-to-r from-pink-500/10 to-purple-500/10 border-pink-500/30">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-white mb-1">
                  Ready to unlock more?
                </h3>
                <p className="text-zinc-400">
                  Upgrade in Telegram to unlock more features here and across supported access points.
                </p>
              </div>
              <Button onClick={() => setShowPlanSelector(true)}>
                View Plans
              </Button>
            </div>
          </Card>
        )}

        {/* Payment History */}
        <Card glass className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-zinc-700">
              <History className="w-5 h-5 text-zinc-400" />
            </div>
            <h2 className="text-xl font-semibold text-white">Payment History</h2>
          </div>

          {paymentHistory.length === 0 ? (
            <div className="text-center py-8 text-zinc-500">
              <CreditCard className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No payment history yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-zinc-400 border-b border-zinc-700">
                    <th className="pb-3 font-medium">Date</th>
                    <th className="pb-3 font-medium">Description</th>
                    <th className="pb-3 font-medium">Amount</th>
                    <th className="pb-3 font-medium">Credits</th>
                    <th className="pb-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {paymentHistory.map((payment) => (
                    <tr key={payment.id} className="border-b border-zinc-800">
                      <td className="py-4 text-sm text-zinc-300">
                        {new Date(payment.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-4 text-sm text-white">
                        {payment.description}
                      </td>
                      <td className="py-4 text-sm text-white font-medium">
                        {billingService.formatPrice(payment.amount_cents, payment.currency)}
                      </td>
                      <td className="py-4 text-sm text-zinc-300">
                        {payment.credits_granted
                          ? `+${payment.credits_granted.toLocaleString()}`
                          : '-'}
                      </td>
                      <td className="py-4">
                        <span
                          className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${
                            payment.status === 'succeeded'
                              ? 'bg-green-500/20 text-green-400'
                              : payment.status === 'pending'
                              ? 'bg-yellow-500/20 text-yellow-400'
                              : payment.status === 'failed'
                              ? 'bg-red-500/20 text-red-400'
                              : 'bg-zinc-700 text-zinc-400'
                          }`}
                        >
                          {payment.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </Container>

      {/* Credit Pack Modal */}
      <CreditPackModal
        isOpen={showCreditModal}
        onClose={() => {
          setShowCreditModal(false);
          if (searchParams.get('buyCredits') === '1') {
            navigate('/billing', { replace: true });
          }
        }}
      />
    </div>
  );
}
