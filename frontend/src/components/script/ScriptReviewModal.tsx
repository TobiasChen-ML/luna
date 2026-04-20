import React, { useState } from 'react';
import { X, Check, XCircle, Clock, MessageSquare, Loader2 } from 'lucide-react';
import { scriptService } from '@/services/scriptService';
import type { Script } from '@/services/scriptService';

interface ScriptReviewModalProps {
  script: Script;
  isOpen: boolean;
  onClose: () => void;
  onAction: () => void;
}

export const ScriptReviewModal: React.FC<ScriptReviewModalProps> = ({
  script,
  isOpen,
  onClose,
  onAction
}) => {
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [reviews, setReviews] = useState<Array<{
    id: string;
    action: string;
    comment: string | null;
    reviewer_id: string;
    created_at: string;
  }> | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  if (!isOpen) return null;

  const handleApprove = async () => {
    setLoading(true);
    try {
      await scriptService.approveScript(script.id, comment || undefined);
      onAction();
      onClose();
    } catch (error) {
      console.error('Failed to approve:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!comment.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }
    setLoading(true);
    try {
      await scriptService.rejectScript(script.id, comment);
      onAction();
      onClose();
    } catch (error) {
      console.error('Failed to reject:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    if (reviews) return;
    try {
      const data = await scriptService.getScriptReviews(script.id);
      setReviews(data);
    } catch (error) {
      console.error('Failed to load reviews:', error);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-zinc-900 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden shadow-2xl border border-zinc-800">
        <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="text-purple-400" size={20} />
            <h2 className="text-xl font-bold text-white">Review Script</h2>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-4 overflow-y-auto max-h-[50vh]">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-white mb-2">{script.title}</h3>
            <p className="text-zinc-400 text-sm">{script.description || 'No description'}</p>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
            <div>
              <span className="text-zinc-500">Genre:</span>
              <span className="text-zinc-300 ml-2">{script.genre || 'N/A'}</span>
            </div>
            <div>
              <span className="text-zinc-500">Author:</span>
              <span className="text-zinc-300 ml-2">{script.author_type}</span>
            </div>
            <div>
              <span className="text-zinc-500">Status:</span>
              <span className={`ml-2 px-2 py-0.5 rounded text-xs ${
                script.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400' :
                script.status === 'published' ? 'bg-green-500/20 text-green-400' :
                'bg-zinc-700 text-zinc-400'
              }`}>
                {script.status}
              </span>
            </div>
            <div>
              <span className="text-zinc-500">Created:</span>
              <span className="text-zinc-300 ml-2">
                {new Date(script.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm text-zinc-400 mb-2">
              Comment {script.status === 'pending' && <span className="text-red-400">(required for rejection)</span>}
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-white resize-none focus:border-purple-500 focus:outline-none"
              rows={3}
              placeholder="Add a comment about this script..."
            />
          </div>

          <button
            onClick={() => { setShowHistory(!showHistory); loadHistory(); }}
            className="flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-300 mb-4"
          >
            <Clock size={16} />
            {showHistory ? 'Hide' : 'Show'} Review History
          </button>

          {showHistory && reviews && (
            <div className="bg-zinc-800/50 rounded-lg p-3 space-y-2">
              {reviews.length === 0 ? (
                <p className="text-zinc-500 text-sm">No review history</p>
              ) : (
                reviews.map((review) => (
                  <div key={review.id} className="text-sm border-b border-zinc-700 pb-2 last:border-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        review.action === 'approve' ? 'bg-green-500/20 text-green-400' :
                        review.action === 'reject' ? 'bg-red-500/20 text-red-400' :
                        review.action === 'submit' ? 'bg-blue-500/20 text-blue-400' :
                        'bg-zinc-700 text-zinc-400'
                      }`}>
                        {review.action}
                      </span>
                      <span className="text-zinc-500 text-xs">
                        {new Date(review.created_at).toLocaleString()}
                      </span>
                    </div>
                    {review.comment && (
                      <p className="text-zinc-300">{review.comment}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <div className="p-4 border-t border-zinc-800 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm text-zinc-300"
          >
            Cancel
          </button>
          {script.status === 'pending' && (
            <>
              <button
                onClick={handleReject}
                disabled={loading || !comment.trim()}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <XCircle size={16} />}
                Reject
              </button>
              <button
                onClick={handleApprove}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
                Approve & Publish
              </button>
            </>
          )}
          {script.status === 'draft' && script.author_type === 'admin' && (
            <button
              onClick={async () => {
                setLoading(true);
                try {
                  await scriptService.submitForReview(script.id, comment || undefined);
                  onAction();
                  onClose();
                } catch (error) {
                  console.error('Failed to submit:', error);
                } finally {
                  setLoading(false);
                }
              }}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm font-medium disabled:opacity-50"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Clock size={16} />}
              Submit for Review
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScriptReviewModal;
