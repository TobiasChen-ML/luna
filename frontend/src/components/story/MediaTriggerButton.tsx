/**
 * MediaTriggerButton Component
 *
 * Allows users to manually trigger media generation (images, videos)
 * during story gameplay. Shows generation status and progress.
 */
import { useState, useCallback } from 'react';
import { Image, Video, Loader2, Check, AlertCircle } from 'lucide-react';

interface MediaCue {
  cue_id: string;
  type: 'image' | 'video';
  prompt: string;
  min_intimacy?: number;
}

interface MediaTriggerButtonProps {
  scriptId: string;
  nodeId: string;
  cueId: string;
  mediaCue: MediaCue;
  sessionId: string;
  characterId: string;
  currentIntimacy?: number;
  onMediaGenerated?: (result: MediaGenerationResult) => void;
  disabled?: boolean;
}

interface MediaGenerationResult {
  success: boolean;
  task_id?: string;
  media_type?: string;
  image_url?: string;
  video_url?: string;
  estimated_seconds?: number;
  reason?: string;
  error?: string;
}

type GenerationStatus = 'idle' | 'checking' | 'generating' | 'success' | 'error';

export function MediaTriggerButton({
  scriptId,
  nodeId,
  cueId,
  mediaCue,
  sessionId,
  characterId,
  currentIntimacy = 0,
  onMediaGenerated,
  disabled = false
}: MediaTriggerButtonProps) {
  const [status, setStatus] = useState<GenerationStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);

  const canTrigger = !mediaCue.min_intimacy || currentIntimacy >= mediaCue.min_intimacy;
  const isImage = mediaCue.type === 'image';
  const Icon = isImage ? Image : Video;

  const handleTrigger = useCallback(async () => {
    if (!canTrigger || status === 'generating' || status === 'checking') return;

    setStatus('checking');
    setError(null);

    try {
      const checkResponse = await fetch(`/api/scripts/${scriptId}/media/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id: nodeId,
          cue_id: cueId,
          session_id: sessionId
        })
      });

      if (!checkResponse.ok) {
        throw new Error('Failed to check media trigger');
      }

      const checkResult = await checkResponse.json();

      if (!checkResult.allowed) {
        setError(getReasonMessage(checkResult.reason));
        setStatus('error');
        return;
      }

      setStatus('generating');
      setProgress(0);

      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 1000);

      const triggerResponse = await fetch(`/api/scripts/${scriptId}/media/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id: nodeId,
          cue_id: cueId,
          session_id: sessionId,
          character_id: characterId
        })
      });

      clearInterval(progressInterval);

      if (!triggerResponse.ok) {
        throw new Error('Failed to trigger media generation');
      }

      const result: MediaGenerationResult = await triggerResponse.json();
      setProgress(100);

      if (result.success) {
        setStatus('success');
        setMediaUrl(result.image_url || result.video_url || null);
        onMediaGenerated?.(result);
      } else {
        setError(result.reason || result.error || 'Generation failed');
        setStatus('error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setStatus('error');
    }
  }, [scriptId, nodeId, cueId, sessionId, characterId, canTrigger, status, onMediaGenerated]);

  return (
    <div className="media-trigger-button">
      <button
        onClick={handleTrigger}
        disabled={disabled || !canTrigger || status === 'generating' || status === 'checking'}
        className={`
          w-full px-4 py-3 rounded-lg text-sm transition-all flex items-center justify-center gap-2
          ${status === 'success'
            ? 'bg-green-600/20 border border-green-500/30 text-green-400'
            : status === 'error'
              ? 'bg-red-600/20 border border-red-500/30 text-red-400'
              : !canTrigger
                ? 'bg-zinc-800/50 border border-zinc-700 text-zinc-500 cursor-not-allowed'
                : 'bg-purple-600/20 border border-purple-500/30 hover:bg-purple-500/30 text-purple-300'
          }
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
      >
        {status === 'idle' && (
          <>
            <Icon size={18} />
            <span>Generate {isImage ? 'Scene Image' : 'Video'}</span>
          </>
        )}

        {status === 'checking' && (
          <>
            <Loader2 size={18} className="animate-spin" />
            <span>Checking...</span>
          </>
        )}

        {status === 'generating' && (
          <>
            <Loader2 size={18} className="animate-spin" />
            <span>Generating {progress}%...</span>
          </>
        )}

        {status === 'success' && (
          <>
            <Check size={18} />
            <span>{isImage ? 'Image' : 'Video'} Generated</span>
          </>
        )}

        {status === 'error' && (
          <>
            <AlertCircle size={18} />
            <span>Failed</span>
          </>
        )}
      </button>

      {!canTrigger && (
        <p className="mt-1 text-xs text-zinc-500">
          Requires intimacy level {mediaCue.min_intimacy} (current: {currentIntimacy})
        </p>
      )}

      {error && (
        <p className="mt-1 text-xs text-red-400">{error}</p>
      )}

      {mediaUrl && status === 'success' && (
        <div className="mt-2">
          {isImage ? (
            <img
              src={mediaUrl}
              alt="Generated scene"
              className="w-full rounded-lg border border-purple-500/30"
            />
          ) : (
            <video
              src={mediaUrl}
              controls
              className="w-full rounded-lg border border-purple-500/30"
            />
          )}
        </div>
      )}
    </div>
  );
}

function getReasonMessage(reason: string): string {
  const messages: Record<string, string> = {
    'node_not_found': 'Story node not found',
    'no_media_cue': 'No media available for this scene',
    'cue_id_mismatch': 'Media cue not found',
    'session_not_found': 'Session not found',
    'already_triggered': 'Media already generated for this scene',
    'insufficient_intimacy': 'Relationship level not high enough',
    'no_prompt': 'No generation prompt available',
    'unsupported_media_type': 'Media type not supported',
    'generation_failed': 'Failed to generate media'
  };
  return messages[reason] || reason;
}
