import {
  Separator,
  checkbox,
  confirm as inquirerConfirm,
  input,
  select as inquirerSelect,
} from '@inquirer/prompts';

import {
  fitDescriptionLine,
  fitTerminal,
  promptListPageSize,
  summarizeSelectedChoices,
  terminalColumns,
} from './terminal-text.js';

export {
  fitDescriptionLine,
  fitTerminal,
  formatOptionName,
  promptListPageSize,
  summarizeSelectedChoices,
  terminalColumns,
} from './terminal-text.js';

/** Shared cancel sentinel — keeps call sites compatible with the old clack `isCancel`. */
export const CANCEL = Symbol('aidk.cancel');

export const isTTY = Boolean(process.stdout.isTTY && process.stdin.isTTY);

function isExitPromptError(err: unknown): boolean {
  if (!err || typeof err !== 'object') return false;
  const name = (err as { name?: string }).name;
  return name === 'ExitPromptError' || name === 'AbortPromptError';
}

export function intro(title: string): void {
  console.log(`\n▸ ${title}\n`);
}

export function outro(msg: string): void {
  if (msg) console.log(`\n${msg}\n`);
}

export function log(msg: string): void {
  console.log(msg);
}

export function cancel(msg: string): void {
  console.error(msg);
}

export function isCancel(value: unknown): value is typeof CANCEL {
  return value === CANCEL;
}

export function spinner(): { start: (msg: string) => void; stop: (msg: string) => void } {
  if (!isTTY) {
    return { start: (m) => console.log(m), stop: (m) => console.log(`✓ ${m}`) };
  }

  const frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
  let i = 0;
  let timer: ReturnType<typeof setInterval> | undefined;
  let current = '';

  const clearLine = (): void => {
    process.stdout.write('\r\x1b[K');
  };

  return {
    start(m: string): void {
      current = m;
      if (timer) clearInterval(timer);
      timer = setInterval(() => {
        const frame = frames[i % frames.length];
        i += 1;
        process.stdout.write(`\r${frame} ${current}`);
      }, 80);
    },
    stop(m: string): void {
      if (timer) clearInterval(timer);
      timer = undefined;
      clearLine();
      console.log(`✓ ${m}`);
    },
  };
}

export async function confirm(opts: {
  message: string;
  initialValue?: boolean;
}): Promise<boolean | typeof CANCEL> {
  if (!isTTY) return opts.initialValue ?? false;
  try {
    return await inquirerConfirm({
      message: opts.message,
      default: opts.initialValue ?? false,
    });
  } catch (err) {
    if (isExitPromptError(err)) return CANCEL;
    throw err;
  }
}

export interface SelectOption<T> {
  value: T;
  label: string;
  hint?: string;
}

export async function select<T>(opts: {
  message: string;
  options: SelectOption<T>[];
  initialValue?: T;
}): Promise<T | typeof CANCEL> {
  if (!isTTY) {
    throw new Error(
      `Interactive prompt required but stdin is not a TTY. Use flags to skip prompts.`,
    );
  }
  try {
    return await inquirerSelect({
      message: opts.message,
      default: opts.initialValue,
      choices: opts.options.map((o) => {
        const name = fitTerminal(o.label, terminalColumns() - 8);
        return {
          name,
          value: o.value,
          short: name,
          description: o.hint?.trim() ? fitDescriptionLine(o.hint) : undefined,
        };
      }),
      pageSize: promptListPageSize(),
    });
  } catch (err) {
    if (isExitPromptError(err)) return CANCEL;
    throw err;
  }
}

export interface MultiselectOption<T = string> {
  value: T;
  label: string;
  hint?: string;
  /** When true, rendered as a non-selectable section header (Inquirer Separator). */
  separator?: boolean;
}

export async function multiselect<T>(opts: {
  message: string;
  options: MultiselectOption<T>[];
  required?: boolean;
}): Promise<T[] | typeof CANCEL> {
  if (!isTTY) {
    throw new Error(
      `Interactive prompt required but stdin is not a TTY. Use flags to skip prompts.`,
    );
  }

  const choices = opts.options.map((o) => {
    if (o.separator) {
      return new Separator(fitTerminal(o.label, terminalColumns() - 4));
    }
    const name = fitTerminal(String(o.label), terminalColumns() - 8);
    return {
      name,
      value: o.value,
      // Answer line uses `short` / renderSelectedChoices — keep short = label only.
      short: name,
      description: o.hint?.trim() ? fitDescriptionLine(o.hint) : undefined,
    };
  });

  try {
    const selected = await checkbox({
      message: opts.message,
      required: opts.required ?? false,
      pageSize: promptListPageSize(),
      choices,
      theme: {
        style: {
          renderSelectedChoices: (
            selection: ReadonlyArray<{ short?: string; name?: string }>,
          ): string => summarizeSelectedChoices(selection),
        },
      },
    });
    return selected as T[];
  } catch (err) {
    if (isExitPromptError(err)) return CANCEL;
    throw err;
  }
}

export async function text(opts: {
  message: string;
  placeholder?: string;
  initialValue?: string;
  validate?: (v: string) => string | undefined;
}): Promise<string | typeof CANCEL> {
  if (!isTTY) {
    throw new Error(
      `Interactive prompt required but stdin is not a TTY. Use flags to skip prompts.`,
    );
  }
  try {
    return await input({
      message: opts.message,
      default: opts.initialValue,
      validate: (v) => {
        if (!opts.validate) return true;
        const err = opts.validate(v);
        return err === undefined ? true : err;
      },
    });
  } catch (err) {
    if (isExitPromptError(err)) return CANCEL;
    throw err;
  }
}
