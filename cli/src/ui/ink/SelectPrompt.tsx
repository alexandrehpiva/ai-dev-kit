import { Box, Text, useInput } from 'ink';
import React, { useMemo, useState } from 'react';

import {
  fitDescriptionLine,
  fitTerminal,
  promptListPageSize,
  terminalColumns,
} from '../../utils/terminal-text.js';

export type SelectItem<T> = {
  value: T;
  label: string;
  hint?: string;
};

export type SelectPromptProps<T> = {
  message: string;
  options: SelectItem<T>[];
  initialValue?: T;
  onDone: (value: T | 'cancel') => void;
};

function initialIndex<T>(options: SelectItem<T>[], initialValue?: T): number {
  if (initialValue === undefined || options.length === 0) return 0;
  const idx = options.findIndex((o) => Object.is(o.value, initialValue));
  return idx >= 0 ? idx : 0;
}

export function SelectPrompt<T>({
  message,
  options,
  initialValue,
  onDone,
}: SelectPromptProps<T>): React.ReactElement {
  const [focus, setFocus] = useState(() => initialIndex(options, initialValue));
  const pageSize = promptListPageSize(6);
  const width = terminalColumns();

  const windowStart = useMemo(() => {
    if (options.length <= pageSize) return 0;
    const half = Math.floor(pageSize / 2);
    return Math.max(0, Math.min(focus - half, options.length - pageSize));
  }, [focus, options.length, pageSize]);

  const visible = options.slice(windowStart, windowStart + pageSize);
  const focused = options[focus];

  useInput((_input, key) => {
    if (key.escape) {
      onDone('cancel');
      return;
    }
    if (key.upArrow) {
      setFocus((i) => (i <= 0 ? options.length - 1 : i - 1));
      return;
    }
    if (key.downArrow) {
      setFocus((i) => (i >= options.length - 1 ? 0 : i + 1));
      return;
    }
    if (key.return && focused) {
      onDone(focused.value);
    }
  });

  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text bold>{message}</Text>
      <Box flexDirection="column" marginTop={1}>
        {visible.map((opt, i) => {
          const absolute = windowStart + i;
          const isFocused = absolute === focus;
          const label = fitTerminal(opt.label, width - 4);
          return (
            <Text key={absolute} color={isFocused ? 'cyan' : undefined} bold={isFocused}>
              {isFocused ? '❯ ' : '  '}
              {label}
            </Text>
          );
        })}
      </Box>
      {focused?.hint?.trim() ? (
        <Box marginTop={1}>
          <Text dimColor>{fitDescriptionLine(focused.hint, width)}</Text>
        </Box>
      ) : null}
      <Box marginTop={1}>
        <Text dimColor>↑↓ · enter · esc</Text>
      </Box>
    </Box>
  );
}
