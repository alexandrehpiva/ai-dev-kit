/**
 * Selection model of the multiselect prompt.
 *
 * The user picks `explicit` items; the cascade (`onSelect`) pulls in linked ones (install: transitive
 * dependencies; uninstall: dependents). Linked items are never stored: they are derived from the
 * explicit set, so un-picking an item always takes back exactly what it had pulled in, and an item
 * that is still required by another picked item cannot be un-picked by accident.
 */

export type SelectionItem<T> = { value: T; separator?: boolean };

export type SelectionCascade<T> = { onSelect?: (value: T) => T[] };

export type SelectionState = {
  /** Indexes picked directly by the user. */
  explicit: Set<number>;
  /** Indexes marked only because another picked item pulled them in. */
  implied: Set<number>;
  /** explicit ∪ implied, the final selection. */
  all: Set<number>;
};

function linkedIndexes<T>(
  options: SelectionItem<T>[],
  index: number,
  cascade?: SelectionCascade<T>,
): number[] {
  const root = options[index];
  if (!root || root.separator) return [];
  const result: number[] = [];
  for (const value of cascade?.onSelect?.(root.value) ?? []) {
    const i = options.findIndex((o) => !o.separator && Object.is(o.value, value));
    if (i >= 0 && i !== index) result.push(i);
  }
  return result;
}

export function computeSelection<T>(
  options: SelectionItem<T>[],
  explicit: Set<number>,
  cascade?: SelectionCascade<T>,
): SelectionState {
  const implied = new Set<number>();
  for (const index of explicit) {
    for (const linked of linkedIndexes(options, index, cascade)) {
      if (!explicit.has(linked)) implied.add(linked);
    }
  }
  return { explicit, implied, all: new Set([...explicit, ...implied]) };
}

/** Items that `index` pulls in when picked (for the "Marca junto" hint). */
export function pullsIn<T>(
  options: SelectionItem<T>[],
  index: number,
  cascade?: SelectionCascade<T>,
): number[] {
  return linkedIndexes(options, index, cascade);
}

/** Explicit items responsible for `index` being implied (for the "Marcada por" hint). */
export function impliedBy<T>(
  options: SelectionItem<T>[],
  index: number,
  explicit: Set<number>,
  cascade?: SelectionCascade<T>,
): number[] {
  return [...explicit].filter((e) => linkedIndexes(options, e, cascade).includes(index));
}

export type ToggleResult = { explicit: Set<number>; blockedBy?: number[] };

/** Space on an item: pick/unpick explicitly; an implied-only item is blocked and reports who requires it. */
export function toggleItem<T>(
  options: SelectionItem<T>[],
  index: number,
  state: SelectionState,
  cascade?: SelectionCascade<T>,
): ToggleResult {
  if (index < 0 || options[index]?.separator) return { explicit: state.explicit };
  if (state.explicit.has(index)) {
    const next = new Set(state.explicit);
    next.delete(index);
    return { explicit: next };
  }
  if (state.implied.has(index)) {
    return {
      explicit: state.explicit,
      blockedBy: impliedBy(options, index, state.explicit, cascade),
    };
  }
  return { explicit: new Set(state.explicit).add(index) };
}
