import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { buildInteractiveSkillEntries } from '../commands/skills/install-selection.ts';
import type { InstalledSkill, SkillInfo } from '../types.js';
import {
  buildDependencyCascade,
  expandWithDependencies,
  findMissingDependencies,
  findInstalledDependents,
  parseDependencies,
  resolveDependencyClosure,
  resolveDependents,
  resolveReference,
} from './dependencies.ts';

function skill(name: string, dependencies: string[] = [], bucket = 'productivity'): SkillInfo {
  return { name, bucket, storePath: `/store/${bucket}/${name}`, description: name, dependencies };
}

describe('parseDependencies', () => {
  it('Given a block list When parsing Then returns each entry', () => {
    const md =
      '---\nname: a\ndependencies:\n  - b\n  - "productivity/c"  # soft note\ndescription: x\n---\nbody';
    assert.deepEqual(parseDependencies(md), ['b', 'productivity/c']);
  });

  it('Given an inline list When parsing Then returns each entry', () => {
    assert.deepEqual(parseDependencies("---\ndependencies: [b, 'c']\n---\n"), ['b', 'c']);
  });

  it('Given no field or no frontmatter When parsing Then returns empty', () => {
    assert.deepEqual(parseDependencies('---\nname: a\n---\n'), []);
    assert.deepEqual(parseDependencies('dependencies:\n  - b'), []);
  });

  it('Given the field in the body only When parsing Then ignores it', () => {
    assert.deepEqual(parseDependencies('---\nname: a\n---\ndependencies:\n  - b\n'), []);
  });
});

describe('resolveReference', () => {
  it('Given bare name with custom and official When resolving Then custom wins', () => {
    const all = [skill('x'), skill('x', [], 'custom')];
    assert.equal(resolveReference('x', all)?.bucket, 'custom');
    assert.equal(resolveReference('productivity/x', all)?.bucket, 'productivity');
  });
});

describe('resolveDependencyClosure', () => {
  it('Given a chain a->b->c When closing a Then adds b and c', () => {
    const all = [skill('a', ['b']), skill('b', ['c']), skill('c')];
    const r = resolveDependencyClosure([all[0]!], all);
    assert.deepEqual(
      r.added.map((s) => s.name),
      ['b', 'c'],
    );
  });

  it('Given a cycle a<->b When closing Then terminates', () => {
    const all = [skill('a', ['b']), skill('b', ['a'])];
    const r = resolveDependencyClosure([all[0]!], all);
    assert.deepEqual(
      r.skills.map((s) => s.name),
      ['a', 'b'],
    );
  });

  it('Given an unknown reference When closing Then reports missing', () => {
    const all = [skill('a', ['ghost'])];
    const r = resolveDependencyClosure([all[0]!], all);
    assert.equal(r.missing[0]?.ref, 'ghost');
  });
});

describe('resolveDependents', () => {
  it('Given a->b->c When asking dependents of c Then returns b and a', () => {
    const all = [skill('a', ['b']), skill('b', ['c']), skill('c'), skill('d')];
    const r = resolveDependents([all[2]!], all);
    assert.deepEqual(r.map((s) => s.name).sort(), ['a', 'b']);
  });
});

describe('dependency cascade', () => {
  const a = skill('a', ['b']);
  const b = skill('b', ['c']);
  const c = skill('c');

  it('Given a->b->c When selecting a Then cascade selects b and c; deselecting c drops a and b', () => {
    const cascade = buildDependencyCascade(buildInteractiveSkillEntries([a, b, c], new Set()));
    assert.deepEqual(cascade.onSelect('a').sort(), ['b', 'c']);
    assert.deepEqual(cascade.onDeselect('c').sort(), ['a', 'b']);
  });

  it('Given dependency already installed When expanding Then it is not added again', () => {
    const r = expandWithDependencies([a], [a, b, c], new Set(['b']));
    assert.deepEqual(
      r.added.map((s) => s.name),
      ['c'],
    );
  });
});

describe('findInstalledDependents', () => {
  const info = (name: string, dependencies: string[] = []): SkillInfo => ({
    name,
    bucket: 'productivity',
    storePath: `/store/${name}`,
    description: name,
    dependencies,
  });
  const inst = (name: string, target: 'claude' | 'cursor' = 'claude'): InstalledSkill => ({
    name,
    bucket: 'productivity',
    target,
    targetPath: `/p/.${target}/skills`,
    symlinkPath: `/p/.${target}/skills/${name}`,
  });

  it('Given a->b installed on claude and only b on cursor When removing b on claude Then only a on claude goes', () => {
    const available = [info('a', ['b']), info('b')];
    const installed = [inst('a'), inst('b'), inst('b', 'cursor')];
    const result = findInstalledDependents([inst('b')], installed, available);
    assert.deepEqual(
      result.map((s) => s.symlinkPath),
      ['/p/.claude/skills/a'],
    );
  });
});

describe('findMissingDependencies', () => {
  const inst = (name: string, target: 'claude' | 'cursor' = 'claude'): InstalledSkill => ({
    name,
    bucket: 'productivity',
    target,
    targetPath: `/p/.${target}/skills`,
    symlinkPath: `/p/.${target}/skills/${name}`,
  });

  it('Given a->b->c with only a installed on claude When checking Then b and c are missing there', () => {
    const available = [skill('a', ['b']), skill('b', ['c']), skill('c')];
    const r = findMissingDependencies([inst('a')], available);
    assert.deepEqual(r.map((m) => m.skill.name).sort(), ['b', 'c']);
    assert.equal(r[0]!.target, 'claude');
  });

  it('Given b already installed When checking Then only c is missing', () => {
    const available = [skill('a', ['b']), skill('b', ['c']), skill('c')];
    const r = findMissingDependencies([inst('a'), inst('b')], available);
    assert.deepEqual(
      r.map((m) => m.skill.name),
      ['c'],
    );
  });

  it('Given deps satisfied on cursor only When checking claude install Then still missing on claude', () => {
    const available = [skill('a', ['b']), skill('b')];
    const r = findMissingDependencies([inst('a'), inst('b', 'cursor')], available);
    assert.deepEqual(
      r.map((m) => m.target),
      ['claude'],
    );
  });
});
