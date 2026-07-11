import fs from 'node:fs';
import path from 'node:path';

import type {
  InstalledSkill,
  SkillInfo,
  SkillSymlinkStatus,
  SymlinkStatus,
  Target,
} from '../types.js';

export function getTargetDir(projectPath: string, target: Target, customPath?: string): string {
  if (target === 'claude') return path.join(projectPath, '.claude', 'skills');
  if (target === 'cursor') return path.join(projectPath, '.cursor', 'skills');
  if (target === 'custom' && customPath) return customPath;
  throw new Error('Custom target requires a path');
}

/** Remove a path whether it's a valid symlink, a broken symlink or a real file/dir. */
function removePathIfExists(p: string): void {
  try {
    fs.lstatSync(p); // lstat does not follow the link, so broken links are seen
    fs.rmSync(p, { recursive: true, force: true });
  } catch {
    // path doesn't exist — nothing to remove
  }
}

export function createSymlink(
  skill: SkillInfo,
  targetDir: string,
  target: Target,
  customPath?: string,
  locale?: string,
): InstalledSkill {
  fs.mkdirSync(targetDir, { recursive: true });

  const symlinkPath = path.join(targetDir, skill.name);
  removePathIfExists(symlinkPath);
  fs.symlinkSync(skill.storePath, symlinkPath, 'dir');

  return {
    name: skill.name,
    bucket: skill.bucket,
    target,
    targetPath: customPath ?? targetDir,
    symlinkPath,
    locale,
  };
}

export function removeSymlink(symlinkPath: string): void {
  removePathIfExists(symlinkPath);
}

export function checkSymlinkStatus(installed: InstalledSkill): SkillSymlinkStatus {
  const { symlinkPath } = installed;

  let status: SymlinkStatus;

  try {
    const lstat = fs.lstatSync(symlinkPath);
    if (lstat.isSymbolicLink()) {
      const linkTarget = fs.readlinkSync(symlinkPath);
      // readlink may return a relative path — resolve against the link's dir.
      const resolved = path.resolve(path.dirname(symlinkPath), linkTarget);
      status = fs.existsSync(resolved) ? 'valid' : 'broken';
    } else {
      status = 'replaced';
    }
  } catch {
    status = 'missing';
  }

  return { skill: installed, status };
}
