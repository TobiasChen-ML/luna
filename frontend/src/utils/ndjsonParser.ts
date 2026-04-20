export type NDJSONSegmentType = 'action' | 'dialogue' | 'inner' | 'hook' | 'scene' | 'npc' | 'narration' | 'state';

export interface NDJSONSegment {
  type: NDJSONSegmentType;
  text: string;
  speaker?: string;
  // state segment fields (type === 'state')
  trust_level?: string;
  current_goal?: string;
  plot_update?: string;
}

export interface NDJSONParserState {
  buffer: string;
  segments: NDJSONSegment[];
  parseErrors: number;
}

export function createNDJSONParserState(): NDJSONParserState {
  return {
    buffer: '',
    segments: [],
    parseErrors: 0
  };
}

function extractNextJSONObject(
  buffer: string
): { jsonText: string | null; rest: string; discardedPrefix: string } {
  const firstBraceIndex = buffer.indexOf('{');
  if (firstBraceIndex === -1) {
    return { jsonText: null, rest: buffer, discardedPrefix: '' };
  }

  const discardedPrefix = buffer.slice(0, firstBraceIndex);
  const candidate = buffer.slice(firstBraceIndex);

  let depth = 0;
  let inString = false;
  let escapeNext = false;

  for (let i = 0; i < candidate.length; i++) {
    const ch = candidate[i];

    if (escapeNext) {
      escapeNext = false;
      continue;
    }

    if (inString) {
      if (ch === '\\') {
        escapeNext = true;
        continue;
      }
      if (ch === '"') {
        inString = false;
      }
      continue;
    }

    if (ch === '"') {
      inString = true;
      continue;
    }

    if (ch === '{') {
      depth++;
      continue;
    }

    if (ch === '}') {
      depth--;
      if (depth === 0) {
        const jsonText = candidate.slice(0, i + 1);
        const rest = candidate.slice(i + 1);
        return { jsonText, rest, discardedPrefix };
      }
    }
  }

  return { jsonText: null, rest: candidate, discardedPrefix };
}

function coerceSegment(parsed: unknown): NDJSONSegment | null {
  if (!parsed || typeof parsed !== 'object') return null;
  const obj = parsed as Record<string, unknown>;

  const type = obj.type;
  const text = obj.text;
  const speaker = obj.speaker;

  const VALID_TYPES: NDJSONSegmentType[] = ['action', 'dialogue', 'inner', 'hook', 'scene', 'npc', 'narration', 'state'];
  if (!VALID_TYPES.includes(type as NDJSONSegmentType)) {
    return null;
  }

  if (type === 'state') {
    return {
      type: 'state',
      text: '',
      trust_level: typeof obj.trust_level === 'string' ? obj.trust_level : undefined,
      current_goal: typeof obj.current_goal === 'string' ? obj.current_goal : undefined,
      plot_update: typeof obj.plot_update === 'string' ? obj.plot_update : undefined,
    };
  }

  if (typeof text !== 'string') {
    return null;
  }

  if (type === 'dialogue') {
    if (typeof speaker === 'string' && speaker.trim().length > 0) {
      return { type, text, speaker };
    }
    return { type, text, speaker: 'She' };
  }

  if (type === 'npc') {
    return {
      type,
      text,
      speaker: typeof speaker === 'string' && speaker.trim() ? speaker.trim() : 'NPC',
    };
  }

  return { type: type as NDJSONSegmentType, text };
}

export function parseNDJSONDelta(
  state: NDJSONParserState,
  delta: string
): { newSegments: NDJSONSegment[]; updatedState: NDJSONParserState } {
  const newSegments: NDJSONSegment[] = [];

  state.buffer += delta;

  while (true) {
    const { jsonText, rest, discardedPrefix } = extractNextJSONObject(state.buffer);
    if (discardedPrefix.trim().length > 0) {
      state.parseErrors++;
    }
    state.buffer = rest;

    if (!jsonText) break;

    try {
      const parsed = JSON.parse(jsonText);
      const seg = coerceSegment(parsed);
      if (seg) {
        newSegments.push(seg);
        state.segments.push(seg);
      } else {
        state.parseErrors++;
      }
    } catch {
      state.parseErrors++;
    }
  }

  return { newSegments, updatedState: state };
}

export function isLikelyNDJSON(content: string): boolean {
  const trimmed = content.trim();
  // Starts with a JSON object containing type/text fields
  if (trimmed.startsWith('{') && (trimmed.includes('"type"') || trimmed.includes('"text"'))) {
    return true;
  }
  // LLM may emit a <thinking> block before the first JSON segment — still detect as NDJSON
  const firstBrace = trimmed.indexOf('{');
  if (firstBrace > 0 && firstBrace < 400) {
    const after = trimmed.slice(firstBrace);
    return after.includes('"type"') && after.includes('"text"');
  }
  return false;
}

export function segmentsToPlainText(segments: NDJSONSegment[]): string {
  return segments.map(seg => {
    switch (seg.type) {
      case 'state':
        return '';
      case 'action':
        return `*${seg.text}*`;
      case 'dialogue':
        return `"${seg.text}"`;
      case 'inner':
        return `(${seg.text})`;
      case 'hook':
        return seg.text;
      case 'scene':
      case 'narration':
        return seg.text;
      case 'npc':
        return seg.speaker ? `${seg.speaker}: ${seg.text}` : seg.text;
      default:
        return seg.text;
    }
  }).join('\n');
}

export function parseNDJSONContent(content: string): {
  segments: NDJSONSegment[];
  parseErrors: number;
} {
  const state = createNDJSONParserState();
  parseNDJSONDelta(state, content);
  return { segments: state.segments, parseErrors: state.parseErrors };
}
