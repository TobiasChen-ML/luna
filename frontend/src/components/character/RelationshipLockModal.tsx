/**
 * Relationship Lock Confirmation Modal (PRD v2026.02)
 *
 * Displays confirmation before locking character relationship.
 * Once locked, character role and user role cannot be changed.
 */
import { Modal } from '@/components/common';
import { Button } from '@/components/common';
import { Lock, AlertTriangle } from 'lucide-react';

interface RelationshipLockModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  characterName: string;
  characterRole: string;
  userRole: string;
  isLoading?: boolean;
}

export function RelationshipLockModal({
  isOpen,
  onClose,
  onConfirm,
  characterName,
  characterRole,
  userRole,
  isLoading = false,
}: RelationshipLockModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Lock Relationship">
      <div className="space-y-6">
        {/* Warning Badge */}
        <div className="flex items-center gap-3 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <AlertTriangle className="w-6 h-6 text-amber-400 flex-shrink-0" />
          <p className="text-sm text-amber-200">
            This action cannot be undone. Once locked, you cannot change this relationship.
          </p>
        </div>

        {/* Relationship Summary */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Lock className="w-5 h-5 text-primary-400" />
            Confirm Relationship
          </h3>

          <div className="bg-zinc-800/50 border border-zinc-700 rounded-lg p-4 space-y-3">
            <div>
              <span className="text-sm text-zinc-400">Character:</span>
              <p className="text-white font-medium">{characterName}</p>
            </div>

            <div className="border-t border-zinc-700 pt-3">
              <span className="text-sm text-zinc-400">Character's Role:</span>
              <p className="text-white font-medium">{characterRole}</p>
            </div>

            <div className="border-t border-zinc-700 pt-3">
              <span className="text-sm text-zinc-400">Your Role:</span>
              <p className="text-white font-medium">{userRole}</p>
            </div>
          </div>
        </div>

        {/* Explanation */}
        <div className="space-y-2 text-sm text-zinc-400">
          <p>
            <strong className="text-white">Why lock?</strong> This ensures{' '}
            {characterName} maintains consistent personality and behavior across all
            conversations.
          </p>
          <p>
            For example, if {characterName} is your <strong className="text-white">{characterRole}</strong>{' '}
            and you are a <strong className="text-white">{userRole}</strong>, they will always behave
            accordingly in every scenario.
          </p>
          <p className="text-amber-300">
            To use a different relationship, you'll need to create a new character.
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <Button
            onClick={onClose}
            disabled={isLoading}
            variant="secondary"
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 bg-primary-600 hover:bg-primary-700"
          >
            {isLoading ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Locking...
              </>
            ) : (
              <>
                <Lock className="w-4 h-4 mr-2" />
                Lock Relationship
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
