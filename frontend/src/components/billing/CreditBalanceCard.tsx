/**
 * CreditBalanceCard - Displays credit balance breakdown
 */
import { Coins, RefreshCw, ShoppingCart } from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import type { CreditBalance } from '../../types';

interface CreditBalanceCardProps {
  balance: CreditBalance | null;
  loading?: boolean;
  onBuyCredits: () => void;
}

export function CreditBalanceCard({
  balance,
  loading,
  onBuyCredits,
}: CreditBalanceCardProps) {
  if (loading) {
    return (
      <Card glass className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-zinc-700 rounded w-1/3" />
          <div className="h-12 bg-zinc-700 rounded w-1/2" />
          <div className="h-4 bg-zinc-700 rounded w-2/3" />
        </div>
      </Card>
    );
  }

  const total = balance?.total ?? 0;
  const monthly = balance?.monthly_remaining ?? 0;
  const purchased = balance?.purchased ?? 0;
  const nextReset = balance?.next_reset
    ? new Date(balance.next_reset).toLocaleDateString()
    : null;

  // Calculate percentages for the bar
  const monthlyPercent = total > 0 ? (monthly / total) * 100 : 0;
  const purchasedPercent = total > 0 ? (purchased / total) * 100 : 0;

  return (
    <Card glass className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-pink-500/20">
            <Coins className="w-6 h-6 text-pink-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Credits</h3>
            <p className="text-sm text-zinc-400">Available balance</p>
          </div>
        </div>

        <Button variant="outline" size="sm" onClick={onBuyCredits}>
          <ShoppingCart className="w-4 h-4 mr-1" />
          Buy More
        </Button>
      </div>

      {/* Total Credits */}
      <div className="mb-4">
        <span className="text-4xl font-bold text-white">{total.toLocaleString()}</span>
        <span className="text-zinc-400 ml-2">credits</span>
      </div>

      {/* Credit Breakdown Bar */}
      <div className="mb-4">
        <div className="h-3 bg-zinc-800 rounded-full overflow-hidden flex">
          {monthlyPercent > 0 && (
            <div
              className="bg-gradient-to-r from-pink-500 to-purple-500 h-full transition-all duration-300"
              style={{ width: `${monthlyPercent}%` }}
            />
          )}
          {purchasedPercent > 0 && (
            <div
              className="bg-gradient-to-r from-blue-500 to-cyan-500 h-full transition-all duration-300"
              style={{ width: `${purchasedPercent}%` }}
            />
          )}
        </div>
      </div>

      {/* Breakdown Details */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gradient-to-r from-pink-500 to-purple-500" />
            <span className="text-zinc-400">Monthly Credits</span>
          </div>
          <span className="text-white font-medium">{monthly.toLocaleString()}</span>
        </div>

        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500" />
            <span className="text-zinc-400">Purchased Credits</span>
          </div>
          <span className="text-white font-medium">{purchased.toLocaleString()}</span>
        </div>

        {/* Reset info */}
        {nextReset && (
          <div className="flex items-center gap-2 pt-2 border-t border-zinc-700 text-xs text-zinc-500">
            <RefreshCw className="w-3 h-3" />
            <span>Monthly credits reset on {nextReset}</span>
          </div>
        )}
      </div>
    </Card>
  );
}
