/** Terminal width helpers shared by prompts and list formatting. */

export function terminalColumns(fallback = 80): number {
  const cols = process.stdout.columns;
  return typeof cols === 'number' && cols > 20 ? cols : fallback;
}

/** Fit text to width; ellipsis when truncated. */
export function fitTerminal(text: string, maxWidth: number): string {
  if (maxWidth < 4) return text.slice(0, Math.max(0, maxWidth));
  if (text.length <= maxWidth) return text;
  return `${text.slice(0, maxWidth - 1)}…`;
}

/**
 * Single-line description for Inquirer (below the list). Collapses whitespace and
 * truncates at a word boundary when possible so it never wraps into a clipped 2nd line.
 */
export function fitDescriptionLine(text: string, maxWidth?: number): string {
  const width = maxWidth ?? Math.max(24, terminalColumns() - 2);
  const one = text.replace(/\s+/g, ' ').trim();
  if (one.length <= width) return one;
  const budget = Math.max(4, width - 1);
  const slice = one.slice(0, budget);
  const sp = slice.lastIndexOf(' ');
  if (sp >= Math.floor(budget * 0.45)) {
    return `${slice.slice(0, sp)}…`;
  }
  return `${slice}…`;
}

/** Leave room under the list for help tip + one description line. */
export function promptListPageSize(reservedBottomLines = 7): number {
  const rows = typeof process.stdout.rows === 'number' ? process.stdout.rows : 24;
  return Math.min(14, Math.max(5, rows - reservedBottomLines));
}

export function formatOptionName(label: string, hint?: string): string {
  const cols = terminalColumns();
  // Leave room for checkbox/pointer chrome (~6) and margins.
  const budget = Math.max(24, cols - 8);
  const labelPart = fitTerminal(label, Math.min(budget, Math.max(12, Math.floor(budget * 0.55))));
  if (!hint?.trim()) return labelPart;
  const remaining = budget - labelPart.length - 1;
  if (remaining < 8) return labelPart;
  return `${labelPart} ${fitTerminal(hint.trim(), remaining)}`;
}

/**
 * Compact answer line for Inquirer checkbox (avoids dumping every selected name).
 * Examples: `grill-me` | `grill-me, study` | `grill-me +11`
 */
export function summarizeSelectedChoices(
  selected: ReadonlyArray<{ short?: string; name?: string }>,
): string {
  const n = selected.length;
  if (n === 0) return 'nenhuma';
  const labels = selected.map((c) => {
    const raw = (c.short ?? c.name ?? '?').trim();
    // Prefer bare skill name when label is bucket/name.
    const slash = raw.lastIndexOf('/');
    return slash === -1 ? raw : raw.slice(slash + 1);
  });
  if (n === 1) return labels[0]!;
  if (n === 2) return `${labels[0]}, ${labels[1]}`;
  return `${labels[0]} +${n - 1}`;
}
