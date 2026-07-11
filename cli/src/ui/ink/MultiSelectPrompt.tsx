import { Box, Text, useInput } from 'ink';
import React, { useMemo, useState } from 'react';

import {
  fitDescriptionLine,
  fitTerminal,
  promptListPageSize,
  summarizeSelectedChoices,
  terminalColumns,
} from '../../utils/terminal-text.js';

export type MultiSelectItem<T> = {
  value: T;
  label: string;
  hint?: string;
  separator?: boolean;
};

export type MultiSelectPromptProps<T> = {
  message: string;
  options: MultiSelectItem<T>[];
  required?: boolean;
  onDone: (value: T[] | 'cancel') => void;
};

function focusableIndexes<T>(options: MultiSelectItem<T>[]): number[] {
  return options.map((item, index) => (item.separator ? -1 : index)).filter((index) => index >= 0);
}

export function MultiSelectPrompt<T>({
  message,
  options,
  required = false,
  onDone,
}: MultiSelectPromptProps<T>): React.ReactElement {
  const selectable = useMemo(() => focusableIndexes(options), [options]);
  const [focusPos, setFocusPos] = useState(0);
  const [selected, setSelected] = useState<Set<number>>(() => new Set());
  const [error, setError] = useState<string | null>(null);

  const pageSize = promptListPageSize(6);
  const width = terminalColumns();
  const focusIndex = selectable.length === 0 ? -1 : (selectable[focusPos] ?? selectable[0]!);
  const focusedItem = focusIndex >= 0 ? options[focusIndex] : undefined;

  const windowStart = useMemo(() => {
    if (options.length <= pageSize) return 0;
    const anchor = focusIndex >= 0 ? focusIndex : 0;
    const half = Math.floor(pageSize / 2);
    return Math.max(0, Math.min(anchor - half, options.length - pageSize));
  }, [focusIndex, options.length, pageSize]);

  const visible = options.slice(windowStart, windowStart + pageSize);

  const toggle = (index: number): void => {
    if (index < 0 || options[index]?.separator) return;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
    setError(null);
  };

  const toggleAll = (): void => {
    setSelected((prev) => {
      if (prev.size === selectable.length) return new Set();
      return new Set(selectable);
    });
    setError(null);
  };

  useInput((input, key) => {
    if (key.escape) {
      onDone('cancel');
      return;
    }
    if (selectable.length === 0) return;
    if (key.upArrow) {
      setFocusPos((p) => (p <= 0 ? selectable.length - 1 : p - 1));
      return;
    }
    if (key.downArrow) {
      setFocusPos((p) => (p >= selectable.length - 1 ? 0 : p + 1));
      return;
    }
    if (input === ' ') {
      toggle(focusIndex);
      return;
    }
    if (input === 'a' || input === 'A') {
      toggleAll();
      return;
    }
    if (key.return) {
      const values = [...selected].sort((a, b) => a - b).map((i) => options[i]!.value);
      if (required && values.length === 0) {
        setError('Select at least one option');
        return;
      }
      onDone(values);
    }
  });

  const selectedLabels = [...selected]
    .sort((a, b) => a - b)
    .map((i) => ({ short: options[i]?.label ?? '' }));

  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text bold>{message}</Text>
      <Box flexDirection="column" marginTop={1}>
        {visible.map((opt, i) => {
          const absolute = windowStart + i;
          if (opt.separator) {
            return (
              <Text key={`sep-${absolute}`} dimColor>
                {fitTerminal(`── ${opt.label} `, width - 2)}
              </Text>
            );
          }
          const isFocused = absolute === focusIndex;
          const isSelected = selected.has(absolute);
          const mark = isSelected ? '●' : '○';
          const label = fitTerminal(opt.label, width - 6);
          return (
            <Text key={absolute} color={isFocused ? 'cyan' : undefined} bold={isFocused}>
              {isFocused ? '❯ ' : '  '}
              <Text color={isSelected ? 'green' : undefined}>{mark} </Text>
              {label}
            </Text>
          );
        })}
      </Box>
      {focusedItem && !focusedItem.separator && focusedItem.hint?.trim() ? (
        <Box marginTop={1}>
          <Text dimColor>{fitDescriptionLine(focusedItem.hint, width)}</Text>
        </Box>
      ) : null}
      {selectedLabels.length > 0 ? (
        <Box marginTop={1}>
          <Text dimColor>Selected: {summarizeSelectedChoices(selectedLabels)}</Text>
        </Box>
      ) : null}
      {error ? (
        <Box marginTop={1}>
          <Text color="red">{error}</Text>
        </Box>
      ) : null}
      <Box marginTop={1}>
        <Text dimColor>space · a all · enter · esc</Text>
      </Box>
    </Box>
  );
}
