import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  fitDescriptionLine,
  fitTerminal,
  formatOptionName,
  promptListPageSize,
  summarizeSelectedChoices,
  terminalColumns,
} from './terminal-text.ts';

describe('fitTerminal', () => {
  it('Given short text When fitting Then returns unchanged', () => {
    assert.equal(fitTerminal('abc', 10), 'abc');
  });

  it('Given long text When fitting Then ellipsis', () => {
    assert.equal(fitTerminal('abcdefghij', 5), 'abcd…');
  });
});

describe('fitDescriptionLine', () => {
  it('Given long text When fitting Then prefers word boundary and stays one line', () => {
    // Given
    const text = 'Guia para criar apps macOS em Swift (SwiftUI, AppKit) e publicar no Homebrew';

    // When
    const line = fitDescriptionLine(text, 40);

    // Then
    assert.ok(line.length <= 40);
    assert.ok(line.endsWith('…'));
    assert.equal(line.includes('\n'), false);
    assert.ok(!/\sS…$/.test(line));
  });
});

describe('promptListPageSize', () => {
  it('Given reserved lines When computing Then leaves room below the list', () => {
    assert.ok(promptListPageSize(7) >= 5);
    assert.ok(promptListPageSize(7) <= 14);
  });
});

describe('formatOptionName', () => {
  it('Given label and hint When formatting Then stays within column budget', () => {
    // Given / When
    const name = formatOptionName(
      'knowledge/knowledge-base',
      'Template e bootstrap para criar uma skill custom de Knowledge Base compartilhada muito longa',
    );

    // Then
    assert.ok(name.length <= Math.max(24, terminalColumns() - 8));
    assert.ok(name.includes('knowledge/knowledge-base'.slice(0, 10)));
  });
});

describe('summarizeSelectedChoices', () => {
  it('Given many selections When summarizing Then shows first name plus count', () => {
    // Given
    const selected = [
      { short: 'productivity/grill-me' },
      { short: 'productivity/study' },
      { short: 'custom/bot-wake' },
    ];

    // When / Then
    assert.equal(summarizeSelectedChoices(selected), 'grill-me +2');
  });

  it('Given one selection When summarizing Then returns bare name', () => {
    assert.equal(summarizeSelectedChoices([{ short: 'engineering/code-review' }]), 'code-review');
  });
});
