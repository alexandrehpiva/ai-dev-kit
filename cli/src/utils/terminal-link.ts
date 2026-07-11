const ESC = '\x1b';
const BEL = '\x07';
const OSC = `${ESC}]`;

/**
 * OSC 8 hyperlink — clickable in iTerm2, VS Code terminal and other modern
 * terminals. Falls back to "text (url)" when the terminal doesn't support it.
 *
 * Format: ESC ] 8 ; ; URL BEL  text  ESC ] 8 ; ; BEL
 */
export function terminalLink(text: string, url: string): string {
  if (!supportsHyperlinks()) return `${text} (${url})`;
  return `${OSC}8;;${url}${BEL}${text}${OSC}8;;${BEL}`;
}

export function fileLink(text: string, absolutePath: string): string {
  // encodeURI keeps the path separators while escaping spaces and accents,
  // which are common in this environment's paths.
  return terminalLink(text, `file://${encodeURI(absolutePath)}`);
}

function supportsHyperlinks(): boolean {
  const { TERM_PROGRAM, TERM, COLORTERM, CI } = process.env;
  if (CI) return false;
  if (TERM_PROGRAM === 'iTerm.app') return true;
  if (TERM_PROGRAM === 'vscode') return true;
  if (COLORTERM === 'truecolor') return true;
  if (TERM?.startsWith('xterm')) return true;
  return false;
}
