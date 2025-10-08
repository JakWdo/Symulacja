import type { FocusGroup } from '@/types';

const TARGET_PREFIX = 'target_participants=';

export function parseTargetContext(context?: string | null): { target: number; text: string } {
  if (!context) {
    return { target: 6, text: '' };
  }

  const lines = context.split('\n');
  const firstLine = lines[0] ?? '';
  if (firstLine.startsWith(TARGET_PREFIX)) {
    const raw = firstLine.slice(TARGET_PREFIX.length).trim();
    const parsed = Number.parseInt(raw, 10);
    if (Number.isFinite(parsed)) {
      return {
        target: Math.max(2, parsed),
        text: lines.slice(1).join('\n'),
      };
    }
  }

  return { target: 6, text: context };
}

export function composeTargetContext(target: number, text: string): string {
  const prefix = `${TARGET_PREFIX}${Math.max(2, target)}`;
  const trimmed = text.trim();
  return trimmed ? `${prefix}\n${trimmed}` : prefix;
}

export function getTargetParticipants(focusGroup: FocusGroup): number {
  return parseTargetContext(focusGroup.project_context).target;
}
