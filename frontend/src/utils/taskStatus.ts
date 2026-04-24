export type NormalizedTaskStatus = 'pending' | 'processing' | 'succeeded' | 'failed';

export function normalizeTaskStatus(rawStatus?: string | null): NormalizedTaskStatus {
  const normalized = (rawStatus || '').trim().toLowerCase();
  const value = normalized.startsWith('task_status_')
    ? normalized.slice('task_status_'.length)
    : normalized;

  if (['succeed', 'succeeded', 'success', 'completed', 'complete', 'ready', 'done'].includes(value)) {
    return 'succeeded';
  }
  if (['failed', 'fail', 'error', 'cancelled', 'canceled'].includes(value)) {
    return 'failed';
  }
  if (['queued', 'queue', 'pending', 'submitted'].includes(value)) {
    return 'pending';
  }
  if (['running', 'processing', 'in_progress', 'progress'].includes(value)) {
    return 'processing';
  }

  // Default to non-terminal so polling continues for unknown provider variants.
  return 'processing';
}

