/**
 * CancelPage - Displayed when user cancels Stripe checkout
 */
import { Link } from 'react-router-dom';
import { XCircle, ArrowLeft, HelpCircle } from 'lucide-react';
import { Container } from '../../components/layout/Container';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';

export default function CancelPage() {
  return (
    <div className="min-h-screen bg-neutral-950 flex items-center justify-center py-12">
      <Container size="sm">
        <Card glass className="p-8 text-center">
          {/* Cancel Icon */}
          <div className="flex justify-center mb-6">
            <div className="p-4 rounded-full bg-zinc-700">
              <XCircle className="w-16 h-16 text-zinc-400" />
            </div>
          </div>

          {/* Title */}
          <h1 className="text-3xl font-bold text-white mb-3">
            Checkout Canceled
          </h1>

          {/* Description */}
          <p className="text-zinc-400 mb-6">
            No worries! Your payment was not processed. You can try again whenever you're ready.
          </p>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link to="/billing">
              <Button className="w-full sm:w-auto">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Billing
              </Button>
            </Link>
            <Link to="/subscriptions">
              <Button variant="outline" className="w-full sm:w-auto">
                View Plans
              </Button>
            </Link>
          </div>

          {/* Help Link */}
          <div className="mt-8 pt-6 border-t border-zinc-700">
            <p className="text-sm text-zinc-500 mb-2">
              Having trouble with payment?
            </p>
            <a
              href="mailto:support@roxyclub.ai"
              className="inline-flex items-center gap-1 text-sm text-pink-400 hover:text-pink-300 transition-colors"
            >
              <HelpCircle className="w-4 h-4" />
              Contact Support
            </a>
          </div>
        </Card>
      </Container>
    </div>
  );
}


