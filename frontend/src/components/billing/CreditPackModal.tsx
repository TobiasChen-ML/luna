/**
 * CreditPackModal - Modal for purchasing credit packs
 */
import { useState, useEffect } from 'react';
import { X, Coins, Sparkles, Loader2, MessageCircleMore } from 'lucide-react';
import { Button } from '../common/Button';
import type { CreditPack } from '../../types';
import { billingService } from '../../services/billingService';
import { useTelegram } from '../../contexts/TelegramContext';
import { openTelegramMiniApp } from '../../utils/telegram';

interface CreditPackModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const STAR_USD_CENTS = 2.04;
const usdCentsToStars = (priceCents: number) => Math.max(1, Math.round(priceCents / STAR_USD_CENTS));

export function CreditPackModal({ isOpen, onClose }: CreditPackModalProps) {
  const { isTma, webApp } = useTelegram();
  const [packs, setPacks] = useState<CreditPack[]>([]);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadPacks();
    }
  }, [isOpen]);

  const loadPacks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await billingService.getCreditPacks();
      setPacks(data.filter((pack) => pack.id !== 'pack_test_1star'));
    } catch (err) {
      setError('Failed to load credit packs');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTelegramPurchase = async (pack: CreditPack) => {
    if (!isTma) {
      openTelegramMiniApp(`credits_${pack.id}`);
      return;
    }

    try {
      setPurchasing(`${pack.id}:telegram`);
      setError(null);
      const amountStars = usdCentsToStars(pack.price_cents);
      const order = await billingService.createTelegramStarsOrder({
        amount_stars: amountStars,
        credits: pack.credits,
        product_type: 'credit_pack',
        pack_id: pack.id,
        title: `${pack.name} Credit Pack`,
        description: pack.description || `${pack.credits} credits`,
        metadata: {
          source: 'billing_credit_pack_modal',
          product: 'credit_pack',
        },
      });
      const invoice = await billingService.createTelegramStarsInvoiceLink(order.order_id, {
        title: `${pack.name} Credit Pack`,
        description: pack.description || `${pack.credits} credits`,
      });
      if (webApp) {
        webApp.openInvoice(invoice.invoice_link, (status) => {
          setPurchasing(null);
          if (status === 'paid') {
            setError(null);
            onClose();
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
      setError(err instanceof Error ? err.message : 'Failed to start Telegram Stars payment');
      setPurchasing(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto p-4 sm:items-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative flex max-h-[calc(100dvh-2rem)] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-zinc-700 bg-zinc-900 shadow-2xl">
        {/* Header */}
        <div className="shrink-0 flex items-center justify-between p-6 border-b border-zinc-700">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-pink-500/20">
              <Coins className="w-5 h-5 text-pink-400" />
            </div>
            <h2 className="text-xl font-semibold text-white">Buy Credits</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <X className="w-5 h-5 text-zinc-400" />
          </button>
        </div>

        {/* Content */}
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-pink-400 animate-spin" />
            </div>
          ) : error && packs.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-red-400 mb-4">{error}</p>
              <Button variant="outline" onClick={loadPacks}>
                Try Again
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-zinc-400 mb-6">
                Purchase additional credits that never expire. Web and PWA users continue in
                Telegram to activate credits with Stars.
              </p>
              {error && (
                <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                  {error}
                </div>
              )}

              {packs.map((pack) => (
                <div
                  key={pack.id}
                  className={`relative p-4 rounded-xl border transition-all ${
                    pack.is_popular
                      ? 'border-pink-500/50 bg-pink-500/5'
                      : 'border-zinc-700 bg-zinc-800/50 hover:border-zinc-600'
                  }`}
                >
                  {/* Popular badge */}
                  {pack.is_popular && (
                    <div className="absolute -top-3 left-4 px-3 py-1 bg-gradient-to-r from-pink-500 to-purple-500 rounded-full text-xs font-medium text-white flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      Popular
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{pack.name}</h3>
                      <p className="text-sm text-zinc-400">{pack.description}</p>
                      <div className="mt-2 flex items-center gap-2">
                        <Coins className="w-4 h-4 text-pink-400" />
                        <span className="text-white font-medium">
                          {pack.credits.toLocaleString()} credits
                        </span>
                      </div>
                    </div>

                    <div className="text-right min-w-[180px]">
                      <div className="text-2xl font-bold text-white mb-3">
                        {billingService.formatPrice(pack.price_cents, pack.currency)}
                      </div>
                      <div className="mb-3 text-xs font-semibold text-amber-200">
                        {usdCentsToStars(pack.price_cents).toLocaleString()} Stars
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleTelegramPurchase(pack)}
                        disabled={purchasing !== null}
                      >
                        {purchasing === `${pack.id}:telegram` ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                            Processing...
                          </>
                        ) : (
                          <>
                            <MessageCircleMore className="w-4 h-4 mr-1" />
                            {isTma ? 'Telegram Stars' : 'Continue in Telegram'}
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="shrink-0 border-t border-zinc-700 p-4 text-center">
          <p className="text-xs text-zinc-500">
            Purchased credits never expire. Digital purchases are completed with Telegram Stars.
          </p>
        </div>
      </div>
    </div>
  );
}
