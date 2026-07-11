import { readConfig, readProjects, writeProjects } from '../../core/config.js';
import { runInitWizardIfNeeded } from '../../core/init.js';
import { removeSymlink } from '../../core/symlinks.js';
import type { InstalledSkill } from '../../types.js';
import { cancel, intro, isCancel, multiselect, outro, spinner } from '../../utils/ui.js';

import {
  buildUninstallMultiselectOptions,
  resolveUninstallSelection,
} from './uninstall-selection.js';

interface UninstallSkillsOptions {
  /** Comma-separated skill names or bucket/name selectors (non-interactive). */
  skills?: string;
  /** When set with --skills, only remove entries for this target. */
  target?: string;
  /** Remove every skill installed in the current project (non-interactive). */
  all?: boolean;
}

function matchInstalled(
  installed: InstalledSkill[],
  selector: string,
  targetFilter?: string,
): InstalledSkill[] {
  const slashIdx = selector.indexOf('/');
  let matches: InstalledSkill[];

  if (slashIdx !== -1) {
    const bucket = selector.slice(0, slashIdx);
    const name = selector.slice(slashIdx + 1);
    matches = installed.filter((s) => s.bucket === bucket && s.name === name);
  } else {
    matches = installed.filter((s) => s.name === selector);
  }

  if (targetFilter) {
    matches = matches.filter((s) => s.target === targetFilter);
  }

  return matches;
}

export async function uninstallSkills(options: UninstallSkillsOptions = {}): Promise<void> {
  await runInitWizardIfNeeded();

  intro('ai-dev-kit skills uninstall');

  readConfig(); // ensure config exists

  const projectPath = process.cwd();
  const registry = readProjects();
  const project = registry.projects.find((p) => p.path === projectPath);

  if (!project || !project.skills.length) {
    console.log('Nenhuma skill instalada neste projeto.');
    outro('');
    return;
  }

  let toRemove: InstalledSkill[];

  if (options.all) {
    if (options.skills || options.target) {
      console.error('--all não combina com --skills nem --target.');
      process.exit(1);
    }
    toRemove = [...project.skills];
  } else if (options.skills) {
    const selectors = options.skills
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    if (!selectors.length) {
      console.error('--skills requer ao menos um nome (ou bucket/nome).');
      process.exit(1);
    }

    const collected: InstalledSkill[] = [];
    for (const selector of selectors) {
      const matches = matchInstalled(project.skills, selector, options.target);
      if (!matches.length) {
        const hint = options.target ? ` (target=${options.target})` : '';
        console.error(`Skill instalada não encontrada: ${selector}${hint}`);
        process.exit(1);
      }
      collected.push(...matches);
    }

    // Deduplicate by symlinkPath (same skill may match twice via name + bucket/name)
    const seen = new Set<string>();
    toRemove = collected.filter((s) => {
      if (seen.has(s.symlinkPath)) return false;
      seen.add(s.symlinkPath);
      return true;
    });
  } else {
    if (options.target) {
      console.error('--target só pode ser usado junto com --skills.');
      process.exit(1);
    }

    const selected = await multiselect({
      message: 'Selecione as skills para remover:',
      options: buildUninstallMultiselectOptions(project.skills),
      required: true,
    });

    if (isCancel(selected)) {
      cancel('Cancelado.');
      process.exit(1);
    }

    const allPaths = project.skills.map((s) => s.symlinkPath);
    const selectedPaths = new Set(resolveUninstallSelection(selected as string[], allPaths));
    toRemove = project.skills.filter((sk) => selectedPaths.has(sk.symlinkPath));
  }

  const s = spinner();
  s.start('Removendo symlinks...');

  const removePaths = new Set(toRemove.map((sk) => sk.symlinkPath));
  for (const skill of toRemove) {
    removeSymlink(skill.symlinkPath);
  }

  project.skills = project.skills.filter((sk) => !removePaths.has(sk.symlinkPath));

  if (!project.skills.length) {
    registry.projects = registry.projects.filter((p) => p.path !== projectPath);
  }

  writeProjects(registry);

  s.stop(`${toRemove.length} skill(s) removida(s).`);
  outro('');
}
