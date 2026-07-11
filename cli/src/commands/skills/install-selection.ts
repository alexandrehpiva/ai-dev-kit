import type { InstalledSkill, SkillInfo, Target } from '../../types.js';

function terminalColumns(fallback = 80): number {
  const cols = process.stdout.columns;
  return typeof cols === 'number' && cols > 20 ? cols : fallback;
}

function fitTerminal(text: string, maxWidth: number): string {
  if (maxWidth < 4) return text.slice(0, Math.max(0, maxWidth));
  if (text.length <= maxWidth) return text;
  return `${text.slice(0, maxWidth - 1)}…`;
}

export type VariantChoice = 'official' | 'custom';

export interface InteractiveSkillEntry {
  name: string;
  official?: SkillInfo;
  custom?: SkillInfo;
}

export interface MultiselectOption {
  value: string;
  label: string;
  hint: string;
  separator?: boolean;
}

/** Names already present on this target with a usable symlink (valid|replaced). */
export function collectInstalledNamesForTarget(
  installed: InstalledSkill[],
  target: Target,
  statusOf: (skill: InstalledSkill) => 'valid' | 'replaced' | 'broken' | 'missing',
): Set<string> {
  const names = new Set<string>();
  for (const skill of installed) {
    if (skill.target !== target) continue;
    const status = statusOf(skill);
    if (status === 'valid' || status === 'replaced') {
      names.add(skill.name);
    }
  }
  return names;
}

export function groupSkillsByName(skills: SkillInfo[]): Map<string, SkillInfo[]> {
  const map = new Map<string, SkillInfo[]>();
  for (const skill of skills) {
    const list = map.get(skill.name) ?? [];
    list.push(skill);
    map.set(skill.name, list);
  }
  return map;
}

function shortHint(skill: SkillInfo): string {
  if (skill.localeHint) return skill.localeHint;
  // Prefer short fragment; terminal fit happens again in ui.formatOptionName.
  return skill.description.replace(/\s+/g, ' ').trim().slice(0, 40);
}

function variantHint(defaultVariant: VariantChoice): string {
  return defaultVariant === 'custom' ? 'custom+oficial' : 'oficial+custom';
}

/**
 * Default variant for a name that has both official and custom.
 * Prefers the bucket already installed on this target; otherwise custom.
 */
export function resolveDefaultVariant(
  official: SkillInfo | undefined,
  custom: SkillInfo | undefined,
  installedForName: InstalledSkill | undefined,
): VariantChoice {
  if (official && custom && installedForName) {
    if (installedForName.bucket === 'custom') return 'custom';
    return 'official';
  }
  if (custom) return 'custom';
  return 'official';
}

/**
 * Build interactive entries: one per name, collisions sit with the official
 * bucket, custom-only skills go in the custom section. Skips installed names.
 */
export function buildInteractiveSkillEntries(
  allSkills: SkillInfo[],
  installedNames: Set<string>,
): InteractiveSkillEntry[] {
  const byName = groupSkillsByName(allSkills);
  const entries: InteractiveSkillEntry[] = [];
  const seen = new Set<string>();

  const officialSkills = allSkills.filter((s) => s.bucket !== 'custom');
  for (const skill of officialSkills) {
    if (installedNames.has(skill.name) || seen.has(skill.name)) continue;
    seen.add(skill.name);
    const variants = byName.get(skill.name) ?? [];
    entries.push({
      name: skill.name,
      official: skill,
      custom: variants.find((v) => v.bucket === 'custom'),
    });
  }

  const customSkills = allSkills.filter((s) => s.bucket === 'custom');
  for (const skill of customSkills) {
    if (installedNames.has(skill.name) || seen.has(skill.name)) continue;
    seen.add(skill.name);
    entries.push({
      name: skill.name,
      custom: skill,
    });
  }

  return entries;
}

export function toMultiselectOptions(
  entries: InteractiveSkillEntry[],
  installedByName: Map<string, InstalledSkill> = new Map(),
): MultiselectOption[] {
  const officialEntries = entries.filter((e) => e.official);
  const customOnly = entries.filter((e) => !e.official && e.custom);
  const sepWidth = Math.min(40, Math.max(20, terminalColumns() - 10));

  const options: MultiselectOption[] = officialEntries.map((entry) => {
    const hasVariant = Boolean(entry.official && entry.custom);
    const defaultVariant = resolveDefaultVariant(
      entry.official,
      entry.custom,
      installedByName.get(entry.name),
    );
    return {
      value: entry.name,
      label: `${entry.official!.bucket}/${entry.name}`,
      hint: hasVariant ? variantHint(defaultVariant) : shortHint(entry.official!),
    };
  });

  if (customOnly.length > 0) {
    options.push({
      value: '__sep__custom__',
      label: fitTerminal('── Custom Skills ──', sepWidth),
      hint: '',
      separator: true,
    });
    for (const entry of customOnly) {
      options.push({
        value: entry.name,
        label: `custom/${entry.name}`,
        hint: shortHint(entry.custom!),
      });
    }
  }

  return options;
}

export function pickSkillForVariant(
  entry: InteractiveSkillEntry,
  choice: VariantChoice,
): SkillInfo {
  if (choice === 'custom') {
    if (!entry.custom) {
      throw new Error(`No custom variant for ${entry.name}`);
    }
    return entry.custom;
  }
  if (!entry.official) {
    throw new Error(`No official variant for ${entry.name}`);
  }
  return entry.official;
}

export function resolveSkillFromEntry(entry: InteractiveSkillEntry): SkillInfo {
  if (entry.official && entry.custom) {
    throw new Error(`Ambiguous entry ${entry.name}; resolve variant first`);
  }
  const skill = entry.official ?? entry.custom;
  if (!skill) {
    throw new Error(`Empty entry ${entry.name}`);
  }
  return skill;
}
