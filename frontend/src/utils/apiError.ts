interface ErrorLike {
  response?: {
    status?: number;
    data?: unknown;
  };
  message?: string;
}

interface InsufficientCreditsLike {
  error?: unknown;
  error_code?: unknown;
  required?: unknown;
  available?: unknown;
  current?: unknown;
  message?: unknown;
}

export interface InsufficientCreditsInfo {
  required?: number;
  available?: number;
  message?: string;
}

function toNumber(value: unknown): number | undefined {
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined;
}

function toRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : null;
}

function extractInsufficientCredits(payload: unknown): InsufficientCreditsInfo | null {
  const record = toRecord(payload);
  if (!record) return null;

  const body = record as InsufficientCreditsLike;
  const errorCode = body.error ?? body.error_code;
  if (errorCode !== 'insufficient_credits') return null;

  const required = toNumber(body.required);
  const available = toNumber(body.available) ?? toNumber(body.current);
  const message = typeof body.message === 'string' ? body.message : undefined;

  return { required, available, message };
}

export function getInsufficientCreditsInfo(error: unknown): InsufficientCreditsInfo | null {
  const err = error as ErrorLike;
  if (err?.response?.status !== 402) return null;

  const data = err.response?.data;
  const detail = toRecord(data)?.detail;

  return extractInsufficientCredits(detail) || extractInsufficientCredits(data);
}

export function getErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'string' && error.trim()) return error;

  const err = error as ErrorLike;
  const data = err?.response?.data;
  const dataRecord = toRecord(data);
  const detail = dataRecord?.detail;

  if (typeof detail === 'string' && detail.trim()) return detail;
  if (typeof dataRecord?.message === 'string' && dataRecord.message.trim()) return dataRecord.message;
  if (typeof err?.message === 'string' && err.message.trim()) return err.message;

  return fallback;
}
