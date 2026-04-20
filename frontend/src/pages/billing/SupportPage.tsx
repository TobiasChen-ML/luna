import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import billingService, { type SupportTicket } from '@/services/billingService';
import { useAuth } from '@/contexts/AuthContext';

type IssueType = 'missed_credits' | 'duplicate_charge' | 'other';

const ISSUE_OPTIONS: { value: IssueType; label: string; description: string }[] = [
  {
    value: 'missed_credits',
    label: 'Missed Credits',
    description: 'Payment completed but credits were not added to my account.',
  },
  {
    value: 'duplicate_charge',
    label: 'Duplicate Charge',
    description: 'I was charged more than once for the same purchase.',
  },
  {
    value: 'other',
    label: 'Other',
    description: 'Other billing issue not listed above.',
  },
];

export default function SupportPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [issueType, setIssueType] = useState<IssueType>('missed_credits');
  const [orderId, setOrderId] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState<SupportTicket | null>(null);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');

    if (description.trim().length < 10) {
      setError('Please provide at least 10 characters of description.');
      return;
    }

    setSubmitting(true);
    try {
      const ticket = await billingService.submitSupportTicket({
        issue_type: issueType,
        description: description.trim(),
        order_id: orderId.trim() || undefined,
      });
      setSubmitted(ticket as SupportTicket);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
        <div className="bg-zinc-900 rounded-2xl p-8 max-w-md w-full text-center">
          <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Ticket Submitted</h2>
          <p className="text-zinc-400 text-sm mb-1">
            Ticket ID: <span className="font-mono text-zinc-300">{submitted.id.slice(0, 8)}…</span>
          </p>
          <p className="text-zinc-400 text-sm mb-6">
            Our team will review your request and respond within 1–2 business days.
          </p>
          <button
            onClick={() => navigate('/billing')}
            className="w-full py-2.5 bg-pink-600 hover:bg-pink-700 text-white rounded-xl font-medium transition-colors"
          >
            Back to Billing
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 py-10 px-4">
      <div className="max-w-lg mx-auto">
        <button
          onClick={() => navigate('/billing')}
          className="text-zinc-400 hover:text-white text-sm mb-6 flex items-center gap-1 transition-colors"
        >
          ← Back to Billing
        </button>

        <h1 className="text-2xl font-bold text-white mb-1">Payment Support</h1>
        <p className="text-zinc-400 text-sm mb-8">
          Submit a request for missed credits or billing issues. We review every ticket manually.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Issue type */}
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-3">Issue Type</label>
            <div className="space-y-2">
              {ISSUE_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-colors ${
                    issueType === opt.value
                      ? 'border-pink-500 bg-pink-500/10'
                      : 'border-zinc-700 bg-zinc-900 hover:border-zinc-500'
                  }`}
                >
                  <input
                    type="radio"
                    name="issue_type"
                    value={opt.value}
                    checked={issueType === opt.value}
                    onChange={() => setIssueType(opt.value)}
                    className="mt-0.5 accent-pink-500"
                  />
                  <div>
                    <div className="text-sm font-medium text-white">{opt.label}</div>
                    <div className="text-xs text-zinc-400 mt-0.5">{opt.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Order ID */}
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1.5">
              Order ID <span className="text-zinc-500 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={orderId}
              onChange={(e) => setOrderId(e.target.value)}
              placeholder="e.g. ord_abc123 or transaction hash"
              maxLength={200}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-2.5 text-white
                         text-sm placeholder-zinc-500 focus:outline-none focus:border-pink-500 transition-colors"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1.5">
              Description <span className="text-zinc-500 font-normal">(min 10 chars)</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Please describe what happened, including payment date, amount, and any screenshots you can reference…"
              rows={5}
              maxLength={2000}
              required
              className="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-2.5 text-white
                         text-sm placeholder-zinc-500 focus:outline-none focus:border-pink-500 transition-colors resize-none"
            />
            <div className="text-xs text-zinc-500 text-right mt-1">{description.length} / 2000</div>
          </div>

          {/* Logged-in email notice */}
          {user?.email && (
            <p className="text-xs text-zinc-500">
              Submitting as <span className="text-zinc-300">{user.email}</span>
            </p>
          )}

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 text-red-400 text-sm bg-red-400/10 rounded-xl px-4 py-3">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 bg-pink-600 hover:bg-pink-700 disabled:opacity-50
                       text-white rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Submitting…
              </>
            ) : (
              'Submit Request'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
