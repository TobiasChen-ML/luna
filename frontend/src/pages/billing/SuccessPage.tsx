/**
 * SuccessPage - Displayed after successful Stripe checkout
 */
import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { CheckCircle, Loader2, ArrowRight, MessageCircle } from 'lucide-react';
import { Container } from '../../components/layout/Container';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { useAuth } from '../../contexts/AuthContext';

export default function SuccessPage() {
  const [searchParams] = useSearchParams();
  const { refreshUser } = useAuth();
  const [refreshing, setRefreshing] = useState(true);

  const sessionId = searchParams.get('session_id');
  const type = searchParams.get('type'); // 'credits' for credit pack purchase

  useEffect(() => {
    // Refresh user data to get updated credits/subscription
    const refresh = async () => {
      setRefreshing(true);
      try {
        await refreshUser();
      } catch (err) {
        console.error('Failed to refresh user:', err);
      } finally {
        setRefreshing(false);
      }
    };

    // Add a small delay to ensure webhook has processed
    const timer = setTimeout(refresh, 2000);
    return () => clearTimeout(timer);
  }, [refreshUser]);

  return (
    <div className="min-h-screen bg-neutral-950 flex items-center justify-center py-12">
      <Container size="sm">
        <Card glass className="p-8 text-center">
          {/* Success Icon */}
          <div className="flex justify-center mb-6">
            <div className="p-4 rounded-full bg-green-500/20">
              <CheckCircle className="w-16 h-16 text-green-400" />
            </div>
          </div>

          {/* Title */}
          <h1 className="text-3xl font-bold text-white mb-3">
            {type === 'credits' ? 'Credits Added!' : 'Subscription Activated!'}
          </h1>

          {/* Description */}
          <p className="text-zinc-400 mb-6">
            {type === 'credits'
              ? 'Your credits have been added to your account. They never expire, so use them whenever you want!'
              : 'Thank you for subscribing! Your account has been upgraded and you now have access to all premium features.'}
          </p>

          {/* Loading state while refreshing */}
          {refreshing && (
            <div className="flex items-center justify-center gap-2 text-zinc-400 mb-6">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Updating your account...</span>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link to="/chat">
              <Button className="w-full sm:w-auto">
                <MessageCircle className="w-4 h-4 mr-2" />
                Start Chatting
              </Button>
            </Link>
            <Link to="/billing">
              <Button variant="outline" className="w-full sm:w-auto">
                View Billing
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>

          {/* Session ID for reference */}
          {sessionId && (
            <p className="mt-6 text-xs text-zinc-600">
              Reference: {sessionId.slice(0, 20)}...
            </p>
          )}
        </Card>
      </Container>
    </div>
  );
}
