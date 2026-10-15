import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  fitDescriptionLine,
  fitTerminal,
  formatOptionName,
  promptListPageSize,
  summarizeSelectedChoices,
  terminalColumns,
  wrapDescription,
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

describe('wrapDescription', () => {
  const full =
    'Gera diagramas de arquitetura de software no estilo dos docs oficiais de cloud (ícones reais, contêineres de fronteira, setas numeradas)';

  it('Given text that fits When wrapping Then returns one line without ellipsis', () => {
    assert.deepEqual(wrapDescription('Entrevista o usuário sobre um plano', 60), [
      'Entrevista o usuário sobre um plano',
    ]);
  });

  it('Given long text When wrapping Then breaks on words and keeps every word until the last line', () => {
    // Given / When
    const lines = wrapDescription(full, 40, 5);

    // Then
    assert.ok(lines.length > 1);
    assert.ok(lines.every((l) => l.length <= 40));
    assert.equal(lines.join(' '), full);
  });

  it('Given text longer than max lines When wrapping Then only the last line ends with ellipsis', () => {
    // Given / When
    const lines = wrapDescription(full, 30, 2);

    // Then
    assert.equal(lines.length, 2);
    assert.ok(lines.every((l) => l.length <= 30));
    assert.ok(lines[1]!.endsWith('…'));
    assert.ok(!lines[0]!.endsWith('…'));
  });

  it('Given empty text When wrapping Then no lines', () => {
    assert.deepEqual(wrapDescription('   ', 40), []);
  });

  it('Given a word longer than the width When wrapping Then never exceeds the width', () => {
    const lines = wrapDescription('x'.repeat(100), 20, 3);
    assert.ok(lines.every((l) => l.length <= 20));
  });
});
