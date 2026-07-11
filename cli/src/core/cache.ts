import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

import type { CacheEntry, SkillCache } from '../types.js';

import { getCacheDir } from './config.js';
import { getCurrentCommit, getSkillsRoot } from './store.js';

const CACHE_FILE = 'skills-cache.json';
const SNAPSHOT_DIR = 'skills-snapshot';

function getCachePath(): string {
  return path.join(getCacheDir(), CACHE_FILE);
}

export function getSnapshotDir(): string {
  return path.join(getCacheDir(), SNAPSHOT_DIR);
}

/** Absolute path to a single skill's snapshot folder, keyed by `<bucket>/<name>`. */
export function getSnapshotSkillPath(skillRelativePath: string): string {
  return path.join(getSnapshotDir(), skillRelativePath);
}

function hashFile(filePath: string): string {
  const content = fs.readFileSync(filePath);
  return crypto.createHash('sha256').update(content).digest('hex');
}

function collectEntries(baseDir: string, relDir = ''): CacheEntry[] {
  const entries: CacheEntry[] = [];
  const dir = path.join(baseDir, relDir);

  for (const name of fs.readdirSync(dir)) {
    if (name.startsWith('.')) continue;
    const fullPath = path.join(dir, name);
    const relPath = relDir ? `${relDir}/${name}` : name;

    if (fs.statSync(fullPath).isDirectory()) {
      entries.push(...collectEntries(baseDir, relPath));
    } else {
      entries.push({
        relativePath: relPath,
        hash: hashFile(fullPath),
        updatedAt: new Date().toISOString(),
      });
    }
  }

  return entries;
}

export async function buildCache(storePath: string): Promise<SkillCache> {
  const skillsRoot = getSkillsRoot(storePath);
  const commit = await getCurrentCommit(storePath);
  const entries = fs.existsSync(skillsRoot) ? collectEntries(skillsRoot) : [];

  return {
    storeCommit: commit,
    updatedAt: new Date().toISOString(),
    entries,
  };
}

export function readCache(): SkillCache | null {
  const p = getCachePath();
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf-8')) as SkillCache;
}

export function writeCache(cache: SkillCache): void {
  fs.mkdirSync(getCacheDir(), { recursive: true });
  fs.writeFileSync(getCachePath(), JSON.stringify(cache, null, 2));
}

/**
 * Refresh the file-copy snapshot of the store's skills tree. The snapshot is
 * what `update` diffs the live store against to produce a human-readable
 * per-file summary, so it must mirror the store at the moment of the last
 * install/update.
 */
export function writeSnapshot(storePath: string): void {
  const skillsRoot = getSkillsRoot(storePath);
  const dest = getSnapshotDir();
  fs.rmSync(dest, { recursive: true, force: true });
  if (fs.existsSync(skillsRoot)) {
    fs.cpSync(skillsRoot, dest, { recursive: true });
  }
}

export function clearCache(): void {
  const p = getCachePath();
  if (fs.existsSync(p)) fs.unlinkSync(p);
  fs.rmSync(getSnapshotDir(), { recursive: true, force: true });
}

export interface SkillDiff {
  skillRelativePath: string;
  changedFiles: string[];
  isNew: boolean;
  isRemoved: boolean;
}

export function diffCacheVsStore(oldCache: SkillCache | null, newCache: SkillCache): SkillDiff[] {
  if (!oldCache) return [];

  const oldByPath = new Map(oldCache.entries.map((e) => [e.relativePath, e.hash]));
  const newByPath = new Map(newCache.entries.map((e) => [e.relativePath, e.hash]));

  const changedBySkill = new Map<string, Set<string>>();

  const recordChange = (relPath: string): void => {
    const parts = relPath.split('/');
    // Skip dotfiles/dotdirs at any path level (bucket or skill name).
    if (parts.some((p) => p.startsWith('.'))) return;
    const skillKey = parts.slice(0, 2).join('/');
    const fileRel = parts.slice(2).join('/') || relPath;
    const existing = changedBySkill.get(skillKey) ?? new Set<string>();
    existing.add(fileRel);
    changedBySkill.set(skillKey, existing);
  };

  // Union of old + new paths catches added, modified AND removed files/skills.
  const allPaths = new Set<string>([...oldByPath.keys(), ...newByPath.keys()]);
  for (const relPath of allPaths) {
    if (oldByPath.get(relPath) !== newByPath.get(relPath)) recordChange(relPath);
  }

  const diffs: SkillDiff[] = [];
  for (const [skillKey, files] of changedBySkill) {
    const isNew = !oldByPath.has(`${skillKey}/SKILL.md`) && newByPath.has(`${skillKey}/SKILL.md`);
    // A skill is removed only if it has no flat SKILL.md AND no locale subfolder SKILL.md.
    const isRemoved =
      !newByPath.has(`${skillKey}/SKILL.md`) &&
      !['pt-BR', 'en-US'].some((loc) => newByPath.has(`${skillKey}/${loc}/SKILL.md`));
    diffs.push({ skillRelativePath: skillKey, changedFiles: [...files], isNew, isRemoved });
  }

  return diffs;
}
