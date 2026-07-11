import React from 'react';

import { ConfirmPrompt } from '../ui/ink/ConfirmPrompt.js';
import { MultiSelectPrompt, type MultiSelectPromptProps } from '../ui/ink/MultiSelectPrompt.js';
import { runInkPrompt } from '../ui/ink/run-prompt.js';
import { SelectPrompt, type SelectPromptProps } from '../ui/ink/SelectPrompt.js';
import { TextPrompt } from '../ui/ink/TextPrompt.js';

import { fitTerminal, summarizeSelectedChoices, terminalColumns } from './terminal-text.js';

export {
  fitDescriptionLine,
  fitTerminal,
  formatOptionName,
  promptListPageSize,
  summarizeSelectedChoices,
  terminalColumns,
} from './terminal-text.js';

/** Shared cancel sentinel — keeps call sites compatible with prior `isCancel` APIs. */
export const CANCEL = Symbol('aidk.cancel');

export const isTTY = Boolean(process.stdout.isTTY && process.stdin.isTTY);

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
  const result = await runInkPrompt<'cancel' | boolean>((done) =>
    React.createElement(ConfirmPrompt, {
      message: opts.message,
      initialValue: opts.initialValue,
      onDone: done,
    }),
  );
  return result === 'cancel' ? CANCEL : result;
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
  const props: SelectPromptProps<T> = {
    message: opts.message,
    options: opts.options,
    initialValue: opts.initialValue,
    onDone: (value) => {
      /* settled inside runInkPrompt */
      void value;
    },
  };
  const result = await runInkPrompt<T | 'cancel'>((done) => {
    props.onDone = done;
    return React.createElement(SelectPrompt as React.ComponentType<SelectPromptProps<T>>, props);
  });
  return result === 'cancel' ? CANCEL : result;
}

export interface MultiselectOption<T = string> {
  value: T;
  label: string;
  hint?: string;
  /** When true, rendered as a non-selectable section header. */
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
  const props: MultiSelectPromptProps<T> = {
    message: opts.message,
    options: opts.options,
    required: opts.required,
    onDone: (value) => {
      void value;
    },
  };
  const result = await runInkPrompt<T[] | 'cancel'>((done) => {
    props.onDone = done;
    return React.createElement(
      MultiSelectPrompt as React.ComponentType<MultiSelectPromptProps<T>>,
      props,
    );
  });
  if (result === 'cancel') return CANCEL;

  const summary = summarizeSelectedChoices(
    result.map((value) => {
      const opt = opts.options.find((o) => !o.separator && Object.is(o.value, value));
      return { short: opt?.label ?? String(value) };
    }),
  );
  console.log(`✔ ${fitTerminal(opts.message, terminalColumns() - 12)}  ${summary}`);
  return result;
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
  const result = await runInkPrompt<string | 'cancel'>((done) =>
    React.createElement(TextPrompt, {
      message: opts.message,
      placeholder: opts.placeholder,
      initialValue: opts.initialValue,
      validate: opts.validate,
      onDone: done,
    }),
  );
  return result === 'cancel' ? CANCEL : result;
}
