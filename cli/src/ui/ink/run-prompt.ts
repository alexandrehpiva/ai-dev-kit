import { render } from 'ink';
import type { ReactElement } from 'react';

/**
 * Render a one-shot Ink app that resolves when `done` is called.
 * Keeps Commander command handlers async/Promise-based.
 */
export async function runInkPrompt<T>(
  createElement: (done: (value: T) => void) => ReactElement,
): Promise<T> {
  return new Promise<T>((resolve) => {
    let settled = false;
    let unmountFn: (() => void) | undefined;

    const done = (value: T): void => {
      if (settled) return;
      settled = true;
      unmountFn?.();
      resolve(value);
    };

    const instance = render(createElement(done));
    unmountFn = (): void => {
      instance.unmount();
    };
  });
}
