import type { InteractiveSkillEntry } from '../commands/skills/install-selection.js';
import type { InstalledSkill, SkillInfo } from '../types.js';

/**
 * Reads the `dependencies` field from a SKILL.md frontmatter.
 * Accepts a block list (`- name`) or an inline list (`[a, b]`).
 * Each entry is `name` or `bucket/name`.
 */
export function parseDependencies(skillMd: string): string[] {
  const front = skillMd.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!front) return [];
  const lines = front[1]!.split(/\r?\n/);
  const start = lines.findIndex((l) => /^dependencies:/.test(l));
  if (start === -1) return [];

  const clean = (v: string): string =>
    v
      .replace(/\s+#.*$/, '')
      .trim()
      .replace(/^['"]|['"]$/g, '');
  const inline = lines[start]!.slice('dependencies:'.length).trim();

  let raw: string[] = [];
  if (inline.startsWith('[')) {
    raw = inline.replace(/^\[|\]$/g, '').split(',');
  } else if (inline === '') {
    for (const line of lines.slice(start + 1)) {
      const item = line.match(/^\s+-\s+(.+)$/);
      if (item) raw.push(item[1]!);
      else if (line.trim() !== '' && !/^\s*#/.test(line)) break;
    }
  }
  return raw.map(clean).filter(Boolean);
}

/** Resolves a dependency reference against the available skills (custom wins on bare names). */
export function resolveReference(ref: string, skills: SkillInfo[]): SkillInfo | undefined {
  const slash = ref.indexOf('/');
  if (slash !== -1) {
    const bucket = ref.slice(0, slash);
    const name = ref.slice(slash + 1);
    return skills.find((s) => s.bucket === bucket && s.name === name);
  }
  const matches = skills.filter((s) => s.name === ref);
  return matches.find((s) => s.bucket === 'custom') ?? matches[0];
}

const keyOf = (s: SkillInfo): string => `${s.bucket}/${s.name}`;

export interface DependencyClosure {
  /** Roots first, then transitive dependencies in discovery order. */
  skills: SkillInfo[];
  /** Dependencies pulled in that were not among the roots. */
  added: SkillInfo[];
  /** Declared references that match no available skill. */
  missing: Array<{ from: SkillInfo; ref: string }>;
}

/** Transitive closure of dependencies; cycle-safe. */
export function resolveDependencyClosure(
  roots: SkillInfo[],
  available: SkillInfo[],
): DependencyClosure {
  const seen = new Map<string, SkillInfo>();
  const missing: DependencyClosure['missing'] = [];
  for (const root of roots) seen.set(keyOf(root), root);

  const queue = [...roots];
  while (queue.length) {
    const current = queue.shift()!;
    for (const ref of current.dependencies ?? []) {
      const dep = resolveReference(ref, available);
      if (!dep) {
        missing.push({ from: current, ref });
        continue;
      }
      if (seen.has(keyOf(dep))) continue;
      seen.set(keyOf(dep), dep);
      queue.push(dep);
    }
  }
  const rootKeys = new Set(roots.map(keyOf));
  const skills = [...seen.values()];
  return { skills, added: skills.filter((s) => !rootKeys.has(keyOf(s))), missing };
}

/** Skills among `candidates` that depend (directly or transitively) on any of `roots`. */
export function resolveDependents(roots: SkillInfo[], candidates: SkillInfo[]): SkillInfo[] {
  const targets = new Set(roots.map(keyOf));
  const dependents = new Map<string, SkillInfo>();
  let grew = true;
  while (grew) {
    grew = false;
    for (const candidate of candidates) {
      const key = keyOf(candidate);
      if (targets.has(key) || dependents.has(key)) continue;
      const hit = (candidate.dependencies ?? []).some((ref) => {
        const dep = resolveReference(ref, candidates.concat(roots));
        return dep ? targets.has(keyOf(dep)) || dependents.has(keyOf(dep)) : false;
      });
      if (hit) {
        dependents.set(key, candidate);
        grew = true;
      }
    }
  }
  return [...dependents.values()];
}

/** Entry representative used to read dependencies (official preferred, like the list row). */
function entryInfo(entry: InteractiveSkillEntry): SkillInfo | undefined {
  return entry.official ?? entry.custom;
}

/**
 * Multiselect cascade over entry names: selecting a skill also selects its
 * transitive dependencies; deselecting one also deselects everything that
 * depends on it (directly or not). Dependencies absent from `entries`
 * (e.g. already installed) are ignored.
 */
export function buildDependencyCascade(entries: InteractiveSkillEntry[]): {
  onSelect: (name: string) => string[];
  onDeselect: (name: string) => string[];
} {
  const infos = entries.map(entryInfo).filter((i): i is SkillInfo => Boolean(i));
  const byName = new Map(infos.map((i) => [i.name, i]));
  return {
    onSelect: (name: string): string[] => {
      const root = byName.get(name);
      if (!root) return [];
      return resolveDependencyClosure([root], infos).added.map((s) => s.name);
    },
    onDeselect: (name: string): string[] => {
      const root = byName.get(name);
      if (!root) return [];
      return resolveDependents([root], infos).map((s) => s.name);
    },
  };
}

export interface ExpandedSelection {
  skills: SkillInfo[];
  added: SkillInfo[];
  missing: Array<{ from: SkillInfo; ref: string }>;
}

/**
 * Adds transitive dependencies of `selected`, skipping names already
 * installed on the target. `available` should include custom variants.
 */
export function expandWithDependencies(
  selected: SkillInfo[],
  available: SkillInfo[],
  installedNames: Set<string> = new Set(),
): ExpandedSelection {
  const closure = resolveDependencyClosure(selected, available);
  const added = closure.added.filter((s) => !installedNames.has(s.name));
  const missing = closure.missing.filter((m) => !installedNames.has(m.ref.split('/').pop()!));
  return { skills: [...selected, ...added], added, missing };
}

/**
 * Installed skills (same target) that depend, directly or transitively, on any
 * of `selected` and are not already in it. Dependencies come from `available`.
 */
export function findInstalledDependents(
  selected: InstalledSkill[],
  installed: InstalledSkill[],
  available: SkillInfo[],
): InstalledSkill[] {
  const info = new Map(available.map((s) => [`${s.bucket}/${s.name}`, s]));
  const infoOf = (sk: InstalledSkill): SkillInfo | undefined => info.get(`${sk.bucket}/${sk.name}`);
  const selectedPaths = new Set(selected.map((s) => s.symlinkPath));
  const result = new Map<string, InstalledSkill>();

  for (const target of new Set(selected.map((s) => s.target))) {
    const sameTarget = installed.filter((s) => s.target === target);
    const roots = selected
      .filter((s) => s.target === target)
      .map(infoOf)
      .filter((i): i is SkillInfo => Boolean(i));
    const candidates = sameTarget.map(infoOf).filter((i): i is SkillInfo => Boolean(i));
    const keys = new Set(resolveDependents(roots, candidates).map((i) => `${i.bucket}/${i.name}`));
    for (const sk of sameTarget) {
      if (keys.has(`${sk.bucket}/${sk.name}`) && !selectedPaths.has(sk.symlinkPath)) {
        result.set(sk.symlinkPath, sk);
      }
    }
  }
  return [...result.values()];
}

export interface MissingDependency {
  skill: SkillInfo;
  target: InstalledSkill['target'];
  targetPath: string;
  /** Installed skill that (transitively) pulled this dependency in. */
  requiredBy: string;
}

/**
 * Dependencies (transitive) of the installed skills that are not installed on
 * the same target yet. Matches installed skills to `available` by
 * `bucket/name`, falling back to the bare name.
 */
export function findMissingDependencies(
  installed: InstalledSkill[],
  available: SkillInfo[],
): MissingDependency[] {
  const result: MissingDependency[] = [];
  for (const target of new Set(installed.map((s) => s.target))) {
    const onTarget = installed.filter((s) => s.target === target);
    const installedNames = new Set(onTarget.map((s) => s.name));
    const roots = onTarget
      .map(
        (sk) =>
          available.find((a) => a.bucket === sk.bucket && a.name === sk.name) ??
          available.find((a) => a.name === sk.name),
      )
      .filter((i): i is SkillInfo => Boolean(i));
    for (const dep of resolveDependencyClosure(roots, available).added) {
      if (installedNames.has(dep.name)) continue;
      const requiredBy = roots.find((r) =>
        resolveDependencyClosure([r], available).added.includes(dep),
      );
      result.push({
        skill: dep,
        target,
        targetPath: onTarget[0]!.targetPath,
        requiredBy: requiredBy ? `${requiredBy.bucket}/${requiredBy.name}` : '?',
      });
    }
  }
  return result;
}
