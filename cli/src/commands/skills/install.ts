import path from 'node:path';

import { buildCache, readCache, writeCache, writeSnapshot } from '../../core/cache.js';
import { getLocale, readConfig, readProjects, writeProjects } from '../../core/config.js';
import { runInitWizardIfNeeded } from '../../core/init.js';
import { getCurrentCommit, listAvailableSkills } from '../../core/store.js';
import { createSymlink, getTargetDir } from '../../core/symlinks.js';
import type { Target } from '../../types.js';
import {
  cancel,
  confirm,
  intro,
  isCancel,
  multiselect,
  outro,
  select,
  spinner,
  text,
} from '../../utils/ui.js';

interface InstallOptions {
  target?: string;
  path?: string;
  skills?: string;
  bucket?: string;
  all?: boolean;
}

export async function installSkills(options: InstallOptions): Promise<void> {
  await runInitWizardIfNeeded();

  const config = readConfig();
  const { storePath } = config;

  // Check if store diverges from cache
  const cache = readCache();
  const currentCommit = await getCurrentCommit(storePath);
  if (cache && cache.storeCommit !== currentCommit) {
    intro('ai-dev-kit skills install');
    const shouldUpdate = await confirm({
      message:
        'O store local está desatualizado em relação ao cache. Deseja atualizar antes de instalar?',
    });
    if (isCancel(shouldUpdate)) {
      cancel('Cancelado.');
      process.exit(1);
    }
    if (shouldUpdate) {
      const { default: updateCmd } = await import('../update.js');
      await updateCmd();
    }
  } else {
    intro('ai-dev-kit skills install');
  }

  // Resolve target
  let target: Target;
  let customPath: string | undefined;

  if (options.target) {
    target = options.target as Target;
    if (target === 'custom') {
      if (!options.path) {
        console.error('--path é obrigatório quando --target custom');
        process.exit(1);
      }
      customPath = options.path;
    }
  } else {
    const selectedTarget = await select({
      message: 'Selecione o target para instalação das skills:',
      options: [
        { value: 'claude', label: 'Claude Code', hint: '.claude/skills/' },
        { value: 'cursor', label: 'Cursor', hint: '.cursor/skills/' },
        { value: 'custom', label: 'Custom', hint: 'caminho personalizado' },
      ],
    });
    if (isCancel(selectedTarget)) {
      cancel('Cancelado.');
      process.exit(1);
    }
    target = selectedTarget as Target;

    if (target === 'custom') {
      const defaultCustomPath = path.join(process.cwd(), '.ai', 'skills');
      const customPathInput = await text({
        message: 'Caminho para instalar as skills:',
        placeholder: defaultCustomPath,
        initialValue: defaultCustomPath,
        validate(v) {
          if (!v.trim()) return 'Informe um caminho.';
        },
      });
      if (isCancel(customPathInput)) {
        cancel('Cancelado.');
        process.exit(1);
      }
      customPath = customPathInput as string;
    }
  }

  // Resolve skills to install
  // allSkills: with suppression — used for flag-based paths (backward-compat)
  // allSkillsForDisplay: without suppression — used for interactive multiselect
  const locale = getLocale();
  const allSkills = listAvailableSkills(storePath, { locale });
  const allSkillsForDisplay = listAvailableSkills(storePath, {
    suppressCustomDuplicates: false,
    locale,
  });
  let skillsToInstall = allSkills;

  if (options.all) {
    // use all (suppressed list — custom takes precedence)
  } else if (options.bucket) {
    skillsToInstall = allSkills.filter((s) => s.bucket === options.bucket);
    if (!skillsToInstall.length) {
      console.error(`Bucket "${options.bucket}" não encontrado ou sem skills.`);
      process.exit(1);
    }
  } else if (options.skills) {
    const selectors = options.skills.split(',').map((s) => s.trim());
    skillsToInstall = selectors.flatMap((selector) => {
      // Supports both "name" and "bucket/name" formats.
      const slashIdx = selector.indexOf('/');
      if (slashIdx !== -1) {
        const bucket = selector.slice(0, slashIdx);
        const name = selector.slice(slashIdx + 1);
        const match = allSkillsForDisplay.find((s) => s.bucket === bucket && s.name === name);
        if (!match) {
          console.error(`Skill não encontrada: ${selector}`);
          process.exit(1);
        }
        return [match];
      }
      // Short name: warn if ambiguous (both custom and official exist), use custom.
      const matches = allSkillsForDisplay.filter((s) => s.name === selector);
      if (!matches.length) {
        console.error(`Skill não encontrada: ${selector}`);
        process.exit(1);
      }
      const custom = matches.find((s) => s.bucket === 'custom');
      if (custom && matches.length > 1) {
        console.log(
          `⚠  "${selector}" é ambíguo (custom e oficial disponíveis); usando custom/${selector}. Use bucket/${selector} para ser explícito.`,
        );
        return [custom];
      }
      return [matches[0]];
    });
  } else {
    const officialSkills = allSkillsForDisplay.filter((s) => s.bucket !== 'custom');
    const customSkills = allSkillsForDisplay.filter((s) => s.bucket === 'custom');

    const CUSTOM_SEP = '__sep__custom__';
    const skillKey = (s: { bucket: string; name: string }): string => `${s.bucket}/${s.name}`;
    const officialOptions = officialSkills.map((s) => ({
      value: skillKey(s),
      label: `${s.bucket}/${s.name}`,
      hint: s.localeHint
        ? `(${s.localeHint}) ${s.description.slice(0, 45)}`
        : s.description.slice(0, 60),
    }));
    const customOptions =
      customSkills.length > 0
        ? [
            { value: CUSTOM_SEP, label: '── Custom Skills ──────────────────', hint: '' },
            ...customSkills.map((s) => ({
              value: skillKey(s),
              label: `custom/${s.name}`,
              hint: s.description.slice(0, 60),
            })),
          ]
        : [];

    const selected = await multiselect({
      message: 'Selecione as skills para instalar:',
      options: [...officialOptions, ...customOptions],
      required: true,
    });
    if (isCancel(selected)) {
      cancel('Cancelado.');
      process.exit(1);
    }

    const selectedKeys = new Set((selected as string[]).filter((v) => v !== CUSTOM_SEP));
    skillsToInstall = allSkillsForDisplay.filter((s) => selectedKeys.has(skillKey(s)));
  }

  // Install
  const s = spinner();
  s.start('Criando symlinks...');

  const projectPath = process.cwd();
  const targetDir = getTargetDir(projectPath, target, customPath);
  const installedSkills = [];

  for (const skill of skillsToInstall) {
    const installed = createSymlink(skill, targetDir, target, customPath, 'default');
    installedSkills.push(installed);
  }

  // Register project — idempotent: remove all existing entries with the same
  // name@target key before pushing the new one, so repeated installs never
  // accumulate duplicates regardless of prior registry state.
  const registry = readProjects();
  const existing = registry.projects.find((p) => p.path === projectPath);
  if (existing) {
    const key = (sk: { name: string; target: string }): string => `${sk.name}@${sk.target}`;
    for (const sk of installedSkills) {
      existing.skills = existing.skills.filter((e) => key(e) !== key(sk));
      existing.skills.push(sk);
    }
  } else {
    registry.projects.push({
      path: projectPath,
      installedAt: new Date().toISOString(),
      skills: installedSkills,
    });
  }
  writeProjects(registry);

  // Refresh baseline (hash cache + file snapshot for future diffs)
  const newCache = await buildCache(storePath);
  writeCache(newCache);
  writeSnapshot(storePath);

  s.stop(`${installedSkills.length} skill(s) instalada(s) em ${targetDir}`);

  outro('Pronto! Use "ai-dev-kit update" para manter as skills atualizadas.');
}
