import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  UNINSTALL_ALL,
  buildUninstallMultiselectOptions,
  resolveUninstallSelection,
} from './uninstall-selection.ts';

describe('resolveUninstallSelection', () => {
  it('Given all sentinel When resolving Then returns every symlink path', () => {
    // Given
    const all = ['/a/grill-me', '/a/study'];
    const selected = [UNINSTALL_ALL];

    // When
    const result = resolveUninstallSelection(selected, all);

    // Then
    assert.deepEqual(result, all);
  });

  it('Given all sentinel plus individuals When resolving Then still returns every path', () => {
    // Given
    const all = ['/a/grill-me', '/a/study', '/a/handoff'];
    const selected = [UNINSTALL_ALL, '/a/grill-me'];

    // When
    const result = resolveUninstallSelection(selected, all);

    // Then
    assert.deepEqual(result, all);
  });

  it('Given only individuals When resolving Then returns those paths', () => {
    // Given
    const all = ['/a/grill-me', '/a/study'];
    const selected = ['/a/study'];

    // When
    const result = resolveUninstallSelection(selected, all);

    // Then
    assert.deepEqual(result, ['/a/study']);
  });
});

describe('buildUninstallMultiselectOptions', () => {
  it('Given installed skills When building Then all option is first', () => {
    // Given
    const skills = [
      {
        symlinkPath: '/p/.cursor/skills/grill-me',
        bucket: 'productivity',
        name: 'grill-me',
        target: 'cursor',
      },
    ];

    // When
    const options = buildUninstallMultiselectOptions(skills);

    // Then
    assert.equal(options[0]?.value, UNINSTALL_ALL);
    assert.equal(options[0]?.label, 'Todas as skills');
    assert.equal(options[1]?.value, '/p/.cursor/skills/grill-me');
  });
});
