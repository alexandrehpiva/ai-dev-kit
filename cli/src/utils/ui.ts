import * as clack from '@clack/prompts';

export const isTTY = Boolean(process.stdout.isTTY && process.stdin.isTTY);

export function intro(title: string): void {
  if (isTTY) clack.intro(title);
  else console.log(`\n▸ ${title}`);
}

export function outro(msg: string): void {
  if (isTTY) clack.outro(msg);
  else if (msg) console.log(msg);
}

export function log(msg: string): void {
  console.log(msg);
}

export function spinner(): { start: (msg: string) => void; stop: (msg: string) => void } {
  if (isTTY) {
    const s = clack.spinner();
    return { start: (m) => s.start(m), stop: (m) => s.stop(m) };
  }
  return { start: (m) => console.log(m), stop: (m) => console.log(`✓ ${m}`) };
}

export async function confirm(opts: {
  message: string;
  initialValue?: boolean;
}): Promise<boolean | symbol> {
  if (!isTTY) return opts.initialValue ?? false;
  return clack.confirm(opts);
}

export async function select<T>(opts: Parameters<typeof clack.select<T>>[0]): Promise<T | symbol> {
  if (!isTTY) {
    throw new Error(
      `Interactive prompt required but stdin is not a TTY. Use flags to skip prompts.`,
    );
  }
  return clack.select<T>(opts);
}

export async function multiselect<T>(
  opts: Parameters<typeof clack.multiselect<T>>[0],
): Promise<T[] | symbol> {
  if (!isTTY) {
    throw new Error(
      `Interactive prompt required but stdin is not a TTY. Use flags to skip prompts.`,
    );
  }
  return clack.multiselect<T>(opts);
}

export async function text(opts: {
  message: string;
  placeholder?: string;
  initialValue?: string;
  validate?: (v: string) => string | undefined;
}): Promise<string | symbol> {
  if (!isTTY) {
    throw new Error(
      `Interactive prompt required but stdin is not a TTY. Use flags to skip prompts.`,
    );
  }
  return clack.text(opts);
}

export function cancel(msg: string): void {
  if (isTTY) clack.cancel(msg);
  else console.error(msg);
}

export function isCancel(value: unknown): value is symbol {
  return clack.isCancel(value);
}
