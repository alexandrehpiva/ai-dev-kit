import fs from 'node:fs';
import path from 'node:path';

import { simpleGit } from 'simple-git';

import type { SkillInfo } from '../types.js';

export const SUPPORTED_LOCALES = ['pt-BR', 'en-US'] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export function getSkillsRoot(storePath: string): string {
  return path.join(storePath, 'skills');
}

export function listAvailableSkills(
  storePath: string,
  options: { suppressCustomDuplicates?: boolean; locale?: string } = {},
): SkillInfo[] {
  const { suppressCustomDuplicates = true, locale = 'pt-BR' } = options;
  const skillsRoot = getSkillsRoot(storePath);
  if (!fs.existsSync(skillsRoot)) return [];

  const skills: SkillInfo[] = [];

  for (const bucket of fs.readdirSync(skillsRoot)) {
    if (bucket.startsWith('.')) continue;
    const bucketPath = path.join(skillsRoot, bucket);
    if (!fs.statSync(bucketPath).isDirectory()) continue;

    for (const skillName of fs.readdirSync(bucketPath)) {
      if (skillName.startsWith('.')) continue;
      const skillPath = path.join(bucketPath, skillName);
      if (!fs.statSync(skillPath).isDirectory()) continue;

      // Detect locale-aware structure: any supported locale subfolder with SKILL.md
      const localeAware = SUPPORTED_LOCALES.some((loc) =>
        fs.existsSync(path.join(skillPath, loc, 'SKILL.md')),
      );

      if (localeAware) {
        const preferredPath = path.join(skillPath, locale, 'SKILL.md');
        if (fs.existsSync(preferredPath)) {
          const resolvedPath = path.join(skillPath, locale);
          const description = extractDescription(preferredPath);
          skills.push({
            name: skillName,
            bucket,
            storePath: resolvedPath,
            description,
            resolvedLocale: locale,
          });
        } else {
          // Fallback: find first available locale
          const fallbackLocale = SUPPORTED_LOCALES.find((loc) =>
            fs.existsSync(path.join(skillPath, loc, 'SKILL.md')),
          );
          if (!fallbackLocale) continue;
          const resolvedPath = path.join(skillPath, fallbackLocale);
          const description = extractDescription(path.join(resolvedPath, 'SKILL.md'));
          skills.push({
            name: skillName,
            bucket,
            storePath: resolvedPath,
            description,
            resolvedLocale: fallbackLocale,
            localeHint: `${fallbackLocale} only`,
          });
        }
      } else {
        // Flat (locale-agnostic): always shown regardless of user locale
        const skillMdPath = path.join(skillPath, 'SKILL.md');
        if (!fs.existsSync(skillMdPath)) continue;
        const description = extractDescription(skillMdPath);
        skills.push({ name: skillName, bucket, storePath: skillPath, description });
      }
    }
  }

  if (!suppressCustomDuplicates) return skills;

  // Custom skills take precedence: if a custom skill shares a name with an
  // official one, the official is suppressed and a notice is printed.
  const customNames = new Set(skills.filter((s) => s.bucket === 'custom').map((s) => s.name));
  if (customNames.size === 0) return skills;

  return skills.filter((s) => {
    if (s.bucket !== 'custom' && customNames.has(s.name)) {
      console.log(`ℹ  custom/${s.name} substitui ${s.bucket}/${s.name}`);
      return false;
    }
    return true;
  });
}

function extractDescription(skillMdPath: string): string {
  const content = fs.readFileSync(skillMdPath, 'utf-8');
  const match = content.match(/^description:\s*[>|]?\s*\n?([\s\S]*?)(?=\n\w|\n---)/m);
  if (match) {
    return match[1].replace(/^\s+/gm, '').replace(/\n/g, ' ').trim().slice(0, 100);
  }
  const inlineMatch = content.match(/^description:\s*(.+)$/m);
  if (inlineMatch) return inlineMatch[1].trim().slice(0, 100);
  return '(sem descrição)';
}

export async function gitPull(storePath: string): Promise<string> {
  const git = simpleGit(storePath);
  const result = await git.pull();
  return result.summary.changes > 0
    ? `${result.summary.changes} arquivo(s) atualizado(s)`
    : 'já atualizado';
}

export async function cloneStore(storePath: string): Promise<void> {
  const REPO_URL = 'git@github.com:alexandrehpiva/ai-dev-kit.git';
  const parent = path.dirname(storePath);
  fs.mkdirSync(parent, { recursive: true });
  const git = simpleGit(parent);
  await git.clone(REPO_URL, storePath);
}

export async function getCurrentCommit(storePath: string): Promise<string> {
  const git = simpleGit(storePath);
  const log = await git.log({ maxCount: 1 });
  return log.latest?.hash ?? 'unknown';
}

export function isGitRepo(storePath: string): boolean {
  return fs.existsSync(path.join(storePath, '.git'));
}
