import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import type { InstalledSkill, SkillInfo } from '../../types.js';
import {
  buildInteractiveSkillEntries,
  collectInstalledNamesForTarget,
  pickSkillForVariant,
  resolveDefaultVariant,
  resolveSkillFromEntry,
  toMultiselectOptions,
  CUSTOM_SEP,
} from './install-selection.ts';

function skill(partial: Partial<SkillInfo> & Pick<SkillInfo, 'name' | 'bucket'>): SkillInfo {
  return {
    storePath: `/store/skills/${partial.bucket}/${partial.name}`,
    description: `${partial.name} desc`,
    ...partial,
  };
}

function installed(
  partial: Partial<InstalledSkill> & Pick<InstalledSkill, 'name' | 'bucket' | 'target'>,
): InstalledSkill {
  return {
    targetPath: '/proj/.claude/skills',
    symlinkPath: `/proj/.claude/skills/${partial.name}`,
    ...partial,
  };
}

describe('collectInstalledNamesForTarget', () => {
  it('Given skills on claude with valid symlink When collecting Then only those names for that target', () => {
    // Given
    const skills = [
      installed({ name: 'grill-me', bucket: 'custom', target: 'claude' }),
      installed({ name: 'handoff', bucket: 'productivity', target: 'cursor' }),
      installed({ name: 'study', bucket: 'productivity', target: 'claude' }),
    ];

    // When
    const names = collectInstalledNamesForTarget(skills, 'claude', (s) =>
      s.name === 'study' ? 'missing' : 'valid',
    );

    // Then
    assert.deepEqual([...names].sort(), ['grill-me']);
  });

  it('Given replaced symlink When collecting Then name is treated as installed', () => {
    // Given
    const skills = [installed({ name: 'x', bucket: 'custom', target: 'cursor' })];

    // When
    const names = collectInstalledNamesForTarget(skills, 'cursor', () => 'replaced');

    // Then
    assert.ok(names.has('x'));
  });
});

describe('buildInteractiveSkillEntries', () => {
  it('Given official+custom same name When building Then one entry at official with both variants', () => {
    // Given
    const all = [
      skill({ name: 'grill-me', bucket: 'productivity' }),
      skill({ name: 'grill-me', bucket: 'custom' }),
      skill({ name: 'only-custom', bucket: 'custom' }),
      skill({ name: 'only-official', bucket: 'engineering' }),
    ];

    // When
    const entries = buildInteractiveSkillEntries(all, new Set());

    // Then
    assert.equal(entries.length, 3);
    const grill = entries.find((e) => e.name === 'grill-me');
    assert.ok(grill?.official && grill.custom);
    assert.equal(grill.official.bucket, 'productivity');
    assert.ok(entries.find((e) => e.name === 'only-custom')?.custom);
    assert.equal(entries.find((e) => e.name === 'only-custom')?.official, undefined);
  });

  it('Given installed name When building Then that skill is omitted', () => {
    // Given
    const all = [
      skill({ name: 'grill-me', bucket: 'productivity' }),
      skill({ name: 'grill-me', bucket: 'custom' }),
      skill({ name: 'handoff', bucket: 'productivity' }),
    ];

    // When
    const entries = buildInteractiveSkillEntries(all, new Set(['grill-me']));

    // Then
    assert.deepEqual(
      entries.map((e) => e.name),
      ['handoff'],
    );
  });
});

describe('toMultiselectOptions', () => {
  it('Given collision When mapping Then hint shows default custom and custom-only under separator', () => {
    // Given
    const entries = buildInteractiveSkillEntries(
      [
        skill({ name: 'grill-me', bucket: 'productivity' }),
        skill({ name: 'grill-me', bucket: 'custom' }),
        skill({ name: 'bot-wake', bucket: 'custom' }),
      ],
      new Set(),
    );

    // When
    const options = toMultiselectOptions(entries);

    // Then
    assert.equal(options[0]?.label, 'productivity/grill-me');
    assert.equal(options[0]?.hint, '→ custom (oficial disponível)');
    assert.equal(options[1]?.value, CUSTOM_SEP);
    assert.equal(options[2]?.label, 'custom/bot-wake');
  });
});

describe('resolveDefaultVariant', () => {
  it('Given both variants and no install When resolving Then custom', () => {
    // Given
    const official = skill({ name: 'study', bucket: 'productivity' });
    const custom = skill({ name: 'study', bucket: 'custom' });

    // When / Then
    assert.equal(resolveDefaultVariant(official, custom, undefined), 'custom');
  });

  it('Given installed official When resolving Then official', () => {
    // Given
    const official = skill({ name: 'study', bucket: 'productivity' });
    const custom = skill({ name: 'study', bucket: 'custom' });
    const inst = installed({ name: 'study', bucket: 'productivity', target: 'claude' });

    // When / Then
    assert.equal(resolveDefaultVariant(official, custom, inst), 'official');
  });
});

describe('pickSkillForVariant / resolveSkillFromEntry', () => {
  it('Given collision When picking custom Then returns custom skill', () => {
    // Given
    const entry = {
      name: 'study',
      official: skill({ name: 'study', bucket: 'productivity' }),
      custom: skill({ name: 'study', bucket: 'custom' }),
    };

    // When
    const picked = pickSkillForVariant(entry, 'custom');

    // Then
    assert.equal(picked.bucket, 'custom');
  });

  it('Given single official When resolving Then returns that skill', () => {
    // Given
    const entry = {
      name: 'foo',
      official: skill({ name: 'foo', bucket: 'engineering' }),
    };

    // When / Then
    assert.equal(resolveSkillFromEntry(entry).bucket, 'engineering');
  });
});
