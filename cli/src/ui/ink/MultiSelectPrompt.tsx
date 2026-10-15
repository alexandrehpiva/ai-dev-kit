import { Box, Text, useInput } from 'ink';
import React, { useMemo, useState } from 'react';

import {
  DESCRIPTION_MAX_LINES,
  fitTerminal,
  promptListPageSize,
  summarizeSelectedChoices,
  terminalColumns,
  wrapDescription,
} from '../../utils/terminal-text.js';

import { computeSelection, impliedBy, pullsIn, toggleItem } from './multiselect-selection.js';

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
  /**
   * Values pulled in by a picked one (install: transitive dependencies; uninstall: dependents).
   * Must be transitive. They are shown marked in another color and cannot be unpicked while the
   * item that requires them stays picked.
   */
  cascade?: {
    onSelect?: (value: T) => T[];
  };
  onDone: (value: T[] | 'cancel') => void;
};

function focusableIndexes<T>(options: MultiSelectItem<T>[]): number[] {
  return options.map((item, index) => (item.separator ? -1 : index)).filter((index) => index >= 0);
}

/** Hint in the "dependency" color, wrapped to at most two lines of the terminal width. */
function YellowLines({ text, width }: { text: string; width: number }): React.ReactElement {
  return (
    <Box flexDirection="column">
      {wrapDescription(text, width - 2, 2).map((line, i) => (
        <Text key={i} color="yellow">
          {line}
        </Text>
      ))}
    </Box>
  );
}

export function MultiSelectPrompt<T>({
  message,
  options,
  required = false,
  cascade,
  onDone,
}: MultiSelectPromptProps<T>): React.ReactElement {
  const selectable = useMemo(() => focusableIndexes(options), [options]);
  const [focusPos, setFocusPos] = useState(0);
  const [explicit, setExplicit] = useState<Set<number>>(() => new Set());
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pageSize = promptListPageSize(6 + DESCRIPTION_MAX_LINES);
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

  const selection = useMemo(
    () => computeSelection(options, explicit, cascade),
    [options, explicit, cascade],
  );
  const labelOf = (index: number): string => options[index]?.label.replace(/^[^/]+\//, '') ?? '';

  const toggle = (index: number): void => {
    const result = toggleItem(options, index, selection, cascade);
    setExplicit(result.explicit);
    setNotice(
      result.blockedBy
        ? `Exigida por ${result.blockedBy.map(labelOf).join(', ')}: desmarque-${
            result.blockedBy.length > 1 ? 'as' : 'a'
          } antes.`
        : null,
    );
    setError(null);
  };

  const toggleAll = (): void => {
    setExplicit((prev) => (prev.size === selectable.length ? new Set() : new Set(selectable)));
    setNotice(null);
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
      const values = [...selection.all].sort((a, b) => a - b).map((i) => options[i]!.value);
      if (required && values.length === 0) {
        setError('Select at least one option');
        return;
      }
      onDone(values);
    }
  });

  const selectedLabels = [...explicit]
    .sort((a, b) => a - b)
    .map((i) => ({ short: options[i]?.label ?? '' }));
  const focusedPulls = focusIndex >= 0 ? pullsIn(options, focusIndex, cascade) : [];
  const focusedRequiredBy =
    focusIndex >= 0 && selection.implied.has(focusIndex)
      ? impliedBy(options, focusIndex, explicit, cascade)
      : [];

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
          const isExplicit = explicit.has(absolute);
          const isImplied = selection.implied.has(absolute);
          const mark = isExplicit || isImplied ? '●' : '○';
          const markColor = isExplicit ? 'green' : isImplied ? 'yellow' : undefined;
          const tag = isImplied ? ' (dependência)' : '';
          const label = fitTerminal(opt.label, width - 6 - tag.length);
          return (
            <Text key={absolute} color={isFocused ? 'cyan' : undefined} bold={isFocused}>
              {isFocused ? '❯ ' : '  '}
              <Text color={markColor}>{mark} </Text>
              {label}
              {isImplied ? <Text color="yellow">{tag}</Text> : null}
            </Text>
          );
        })}
      </Box>
      {focusedItem && !focusedItem.separator && focusedItem.hint?.trim() ? (
        <Box marginTop={1}>
          <Box flexDirection="column">
            {wrapDescription(focusedItem.hint, width - 2).map((line, i) => (
              <Text key={i} dimColor>
                {line}
              </Text>
            ))}
          </Box>
        </Box>
      ) : null}
      {focusedRequiredBy.length > 0 ? (
        <YellowLines
          text={`Marcada por: ${focusedRequiredBy.map(labelOf).join(', ')}`}
          width={width}
        />
      ) : focusedPulls.length > 0 ? (
        <YellowLines text={`Marca junto: ${focusedPulls.map(labelOf).join(', ')}`} width={width} />
      ) : null}
      {selectedLabels.length > 0 || selection.implied.size > 0 ? (
        <Box marginTop={1}>
          <Text dimColor>
            Selected: {summarizeSelectedChoices(selectedLabels)}
            {selection.implied.size > 0 ? ` · +${selection.implied.size} por dependência` : ''}
          </Text>
        </Box>
      ) : null}
      {notice ? <YellowLines text={notice} width={width} /> : null}
      {error ? (
        <Box marginTop={1}>
          <Text color="red">{error}</Text>
        </Box>
      ) : null}
      <Box marginTop={1}>
        <Text dimColor>
          space · a all · enter · esc
          {selection.implied.size > 0 ? '   ' : ''}
        </Text>
        {selection.implied.size > 0 ? <Text color="yellow">● dependência (vai junto)</Text> : null}
      </Box>
    </Box>
  );
}
