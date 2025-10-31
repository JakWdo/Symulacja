// Utilities for normalizing and sanitizing LLM Markdown outputs

// Normalize common formatting issues from LLM outputs so they render cleanly
export function normalizeMarkdown(input: string | null | undefined): string {
  if (!input) return '';
  let value = String(input);

  // 1) Replace double or repeated colons :: -> :
  value = value.replace(/:{2,}/g, ':');

  // 2) Ensure a single space after a colon when followed by non-space
  value = value.replace(/:\s*(?=\S)/g, ': ');

  // 3) Fix cases like 'Title**:' -> '**Title**:' while keeping bullets
  value = value.replace(
    /(^|\n)(\s*(?:[-+*]\s+)?)((?!\*\*)[^:\n]*?)\*\*:\s*/g,
    (_match, lineStart: string, bullet: string, text: string) =>
      `${lineStart}${bullet}**${text.trim()}**: `
  );

  // 4) Remove accidentally bolded colons like '**:' -> ':'
  value = value.replace(/\*\*\s*:/g, ':');

  // 5) Convert unicode bullets to markdown bullets
  value = value.replace(/(^|\n)\s*•\s+/g, '$1- ');

  // 6) Ensure bullets have a space: '-text' -> '- text'
  value = value.replace(/(^|\n)(\s*[-+*])(\S)/g, '$1$2 $3');

  // 7) If bold markers are unmatched (odd count), strip all '**'
  const stars = value.match(/\*\*/g);
  if (stars && stars.length % 2 === 1) {
    value = value.replace(/\*\*/g, '');
  }

  // 8) Trim trailing spaces per line and overall
  value = value.replace(/[ \t]+$/gm, '');

  return value.trim();
}

