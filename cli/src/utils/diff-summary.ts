import fs from 'node:fs';
import path from 'node:path';

import { diffLines } from 'diff';

/**
 * Returns one summary line per changed file: "+ 5 - 2  SKILL.md"
 * storePath: absolute path to the skill folder in the store (current state)
 * cachedSkillRoot: absolute path to the cached skill folder
 */
export function skillDiffSummary(storePath: string, cachedSkillRoot: string): string[] {
  const lines: string[] = [];

  if (!fs.existsSync(cachedSkillRoot)) return [];

  collectFiles(storePath).forEach((relFile) => {
    const storeFile = path.join(storePath, relFile);
    const cacheFile = path.join(cachedSkillRoot, relFile);

    const storeContent = fs.existsSync(storeFile) ? fs.readFileSync(storeFile, 'utf-8') : '';
    const cacheContent = fs.existsSync(cacheFile) ? fs.readFileSync(cacheFile, 'utf-8') : '';

    if (storeContent === cacheContent) return;

    const diff = diffLines(cacheContent, storeContent);
    const added = diff.filter((d) => d.added).reduce((a, d) => a + (d.count ?? 0), 0);
    const removed = diff.filter((d) => d.removed).reduce((a, d) => a + (d.count ?? 0), 0);

    lines.push(`  +${added} -${removed}  ${relFile}`);
  });

  return lines;
}

function collectFiles(dir: string, rel = ''): string[] {
  if (!fs.existsSync(dir)) return [];
  const results: string[] = [];
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    const relPath = rel ? `${rel}/${name}` : name;
    if (fs.statSync(full).isDirectory()) {
      results.push(...collectFiles(full, relPath));
    } else {
      results.push(relPath);
    }
  }
  return results;
}
