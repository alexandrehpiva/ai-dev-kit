import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { computeSelection, impliedBy, pullsIn, toggleItem } from './multiselect-selection.ts';

// a -> b -> c ; d independent ; index: a0 b1 c2 d3
const options = ['a', 'b', 'c', 'd'].map((value) => ({ value }));
const deps: Record<string, string[]> = { a: ['b', 'c'], b: ['c'], c: [], d: [] };
const cascade = { onSelect: (v: string) => deps[v] ?? [] };

describe('computeSelection', () => {
  it('Given a picked skill When computing Then its dependencies are implied, not explicit', () => {
    const s = computeSelection(options, new Set([0]), cascade);
    assert.deepEqual([...s.explicit], [0]);
    assert.deepEqual([...s.implied].sort(), [1, 2]);
    assert.deepEqual([...s.all].sort(), [0, 1, 2]);
  });

  it('Given a dependency also picked explicitly When computing Then it is explicit, not implied', () => {
    const s = computeSelection(options, new Set([0, 2]), cascade);
    assert.deepEqual([...s.implied], [1]);
  });

  it('Given nothing picked When computing Then nothing is implied', () => {
    assert.equal(computeSelection(options, new Set(), cascade).all.size, 0);
  });
});

describe('toggleItem', () => {
  it('Given an unpicked item When toggling Then it becomes explicit', () => {
    const state = computeSelection(options, new Set(), cascade);
    assert.deepEqual([...toggleItem(options, 3, state, cascade).explicit], [3]);
  });

  it('Given an explicit item When toggling Then dependencies it pulled in are released', () => {
    const state = computeSelection(options, new Set([0]), cascade);
    const next = toggleItem(options, 0, state, cascade);
    assert.equal(computeSelection(options, next.explicit, cascade).all.size, 0);
  });

  it('Given an implied-only item When toggling Then it stays and reports who requires it', () => {
    const state = computeSelection(options, new Set([0]), cascade);
    const result = toggleItem(options, 2, state, cascade);
    assert.deepEqual([...result.explicit], [0]);
    assert.deepEqual(result.blockedBy, [0]);
  });

  it('Given a dependency picked explicitly and its parent picked When unpicking it Then it stays implied', () => {
    const state = computeSelection(options, new Set([0, 2]), cascade);
    const next = toggleItem(options, 2, state, cascade);
    const after = computeSelection(options, next.explicit, cascade);
    assert.ok(after.implied.has(2));
  });

  it('Given a separator When toggling Then nothing changes', () => {
    const withSep = [...options, { value: 'sep', separator: true }];
    const state = computeSelection(withSep, new Set(), cascade);
    assert.equal(toggleItem(withSep, 4, state, cascade).explicit.size, 0);
  });
});

describe('hints', () => {
  it('Given a skill with dependencies When asking what it pulls in Then lists them', () => {
    assert.deepEqual(pullsIn(options, 0, cascade).sort(), [1, 2]);
  });

  it('Given an implied item When asking who requires it Then lists the explicit parents', () => {
    assert.deepEqual(impliedBy(options, 2, new Set([0, 1]), cascade).sort(), [0, 1]);
  });
});
