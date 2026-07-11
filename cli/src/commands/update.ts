import fs from 'node:fs';

import {
  buildCache,
  diffCacheVsStore,
  getSnapshotSkillPath,
  readCache,
  writeCache,
  writeSnapshot,
  type SkillDiff,
} from '../core/cache.js';
import { updateCliFromStore } from '../core/cli-self-update.js';
import { getLocale, readConfig, readProjects, writeProjects } from '../core/config.js';
import { runInitWizardIfNeeded } from '../core/init.js';
import { SUPPORTED_LOCALES, gitPull, isGitRepo, listAvailableSkills } from '../core/store.js';
import {
  checkSymlinkStatus,
  createSymlink,
  getTargetDir,
  removeSymlink,
} from '../core/symlinks.js';
import type { SkillInfo } from '../types.js';
import { skillDiffSummary } from '../utils/diff-summary.js';
import { fileLink } from '../utils/terminal-link.js';
import { confirm, intro, isCancel, log, outro, spinner } from '../utils/ui.js';

export interface UpdateOptions {
  /** Skip `git pull` — rebuild CLI/skills from the current store tree (rollback-friendly). */
  noPull?: boolean;
  /** Only rebuild/relink the CLI; do not sync project skill symlinks. */
  cliOnly?: boolean;
}

export default async function update(options: UpdateOptions = {}): Promise<void> {
  await runInitWizardIfNeeded();

  intro('ai-dev-kit update');

  const { storePath } = readConfig();

  if (!isGitRepo(storePath)) {
    log(`✗ O store não é um repositório git: ${storePath}`);
    log('  Verifique o caminho com o wizard (apague config.json) ou clone o framework lá.');
    outro('Nada a fazer.');
    return;
  }

  // 1. git pull (optional — skip for local rollback / rebuild-from-tree)
  if (options.noPull) {
    log('Store: git pull pulado (--no-pull)');
  } else {
    const s = spinner();
    s.start('Atualizando store (git pull)...');
    const pullSummary = await gitPull(storePath);
    s.stop(`Store: ${pullSummary}`);
  }

  // 2. Rebuild CLI from store/cli and refresh ~/.local/bin links (same as install.sh)
  const cliSpinner = spinner();
  cliSpinner.start('Atualizando CLI (pnpm install + build)...');
  try {
    const cliResult = await updateCliFromStore(storePath);
    if (cliResult.status === 'updated') {
      const ver = cliResult.version ? ` v${cliResult.version}` : '';
      const cleaned = cliResult.cleanedDist ? ' (dist limpo)' : '';
      cliSpinner.stop(`CLI${ver} reconstruída e bins atualizados${cleaned}`);
      if (cliResult.redirectedBins?.length) {
        for (const p of cliResult.redirectedBins) {
          log(`  ↳ bin antigo redirecionado: ${p}`);
        }
      }
      if (cliResult.leftAloneBins?.length) {
        for (const p of cliResult.leftAloneBins) {
          log(
            `  ⚠  "${p}" no PATH não parece CLI do kit — mantido intacto (skills/registry não afetados).`,
          );
        }
      }
    } else {
      cliSpinner.stop(`CLI: ${cliResult.reason ?? 'pulado'}`);
    }
  } catch (err) {
    cliSpinner.stop('Falha ao atualizar o CLI');
    const message = err instanceof Error ? err.message : String(err);
    log(`✗ ${message}`);
    log('  Corrija o build (pnpm no PATH, store/cli) e rode `aidk update` de novo.');
    outro('Update interrompido.');
    process.exit(1);
  }

  if (options.cliOnly) {
    outro('Update CLI concluído (--cli-only; skills não sincronizadas).');
    return;
  }

  // 3. Diff the freshly-pulled store against the cached baseline
  const oldCache = readCache();
  const newCache = await buildCache(storePath);
  const diffs = diffCacheVsStore(oldCache, newCache);

  // 4. Verify registered projects, dropping ones whose target no longer exists
  const registry = readProjects();
  const projectsToRemove = new Set<string>();

  for (const project of registry.projects) {
    if (!fs.existsSync(project.path)) {
      log(`\n⚠  As skills do repositório ${project.path} não foram encontradas.`);
      log('   Removendo rastreamento...');
      log(`   Para rastrear novamente: cd ${project.path} && ai-dev-kit skills install`);
      projectsToRemove.add(project.path);
      continue;
    }

    for (const skill of project.skills) {
      if (checkSymlinkStatus(skill).status !== 'missing') continue;
      const targetDir = getTargetDir(project.path, skill.target, skill.targetPath);
      if (!fs.existsSync(targetDir)) {
        log(`\n⚠  Pasta de skills não encontrada em ${project.path} (${targetDir}).`);
        log('   Removendo rastreamento...');
        log(`   Para rastrear novamente: cd ${project.path} && ai-dev-kit skills install`);
        projectsToRemove.add(project.path);
        break;
      }
    }
  }

  if (projectsToRemove.size) {
    registry.projects = registry.projects.filter((p) => !projectsToRemove.has(p.path));
  }

  // 5. Apply changed (still-existing) skills
  const locale = getLocale();
  const availableSkills = listAvailableSkills(storePath, { locale });
  const removedDiffs = diffs.filter((d) => d.isRemoved);
  const changedDiffs = diffs.filter((d) => !d.isRemoved);
  const migrationLogs: string[] = [];

  for (const diff of changedDiffs) {
    const [bucket, skillName] = diff.skillRelativePath.split('/');
    const storeSkill = availableSkills.find((sk) => sk.bucket === bucket && sk.name === skillName);
    if (!storeSkill) continue;

    for (const project of registry.projects) {
      const installed = project.skills.find((sk) => sk.name === skillName);
      if (!installed) continue;

      const { status } = checkSymlinkStatus(installed);
      const targetDir = getTargetDir(project.path, installed.target, installed.targetPath);

      // Detect flat→locale migration: old symlink pointed to skill root, new points to locale subfolder.
      const resolvedSkillLocale = storeSkill.resolvedLocale;
      const isMigration =
        resolvedSkillLocale !== undefined &&
        !SUPPORTED_LOCALES.some((loc) => installed.symlinkPath.endsWith(`/${loc}`));

      if (status === 'replaced') {
        log(`\n  Skill modificada localmente: ${skillName} (${project.path})`);
        log(`  ${fileLink('Abrir pasta', installed.symlinkPath)}`);
        const snapshot = getSnapshotSkillPath(diff.skillRelativePath);
        skillDiffSummary(storeSkill.storePath, snapshot).forEach((l) => log(l));

        const shouldReplace = await confirm({
          message: `Substituir "${skillName}" com a versão atualizada do framework?`,
          initialValue: false,
        });
        if (!isCancel(shouldReplace) && shouldReplace) {
          const updated = createSymlink(
            storeSkill,
            targetDir,
            installed.target,
            installed.targetPath,
            installed.locale,
          );
          const idx = project.skills.findIndex((sk) => sk.name === skillName);
          if (idx !== -1) project.skills[idx] = { ...updated, locale: installed.locale };
          log(`  ✓ ${skillName} atualizada`);
        } else {
          log(`  — ${skillName} mantida (versão local preservada)`);
        }
      } else {
        // valid or broken — relink to the current store path
        const updated = createSymlink(
          storeSkill,
          targetDir,
          installed.target,
          installed.targetPath,
          installed.locale,
        );
        const idx = project.skills.findIndex((sk) => sk.name === skillName);
        if (idx !== -1) project.skills[idx] = { ...updated, locale: installed.locale };

        if (isMigration) {
          const fallbackNote = storeSkill.localeHint ? ` (pt-BR ausente)` : '';
          migrationLogs.push(
            `  ✓ ${skillName.padEnd(28)} flat → ${resolvedSkillLocale}${fallbackNote}`,
          );
        }
      }
    }
  }

  if (migrationLogs.length) {
    log('\n  Skills migradas para estrutura locale:');
    migrationLogs.forEach((l) => log(l));
  }

  // 6. Handle skills removed from the framework
  if (removedDiffs.length) {
    log('\n  Skills descontinuadas no framework:');
    for (const diff of removedDiffs) {
      const rename = detectPossibleRename(diff, diffs, availableSkills);
      const renameNote = rename ? `  (possível rename → ${rename})` : '';
      log(`    - ${diff.skillRelativePath}${renameNote}`);
    }

    const keptDueToLocalEdit: string[] = [];
    const removable: string[] = []; // skill names safe to remove

    for (const diff of removedDiffs) {
      const skillName = diff.skillRelativePath.split('/')[1];
      let hasLocalEdit = false;
      for (const project of registry.projects) {
        const installed = project.skills.find((sk) => sk.name === skillName);
        if (installed && checkSymlinkStatus(installed).status === 'replaced') {
          hasLocalEdit = true;
          keptDueToLocalEdit.push(`${skillName} (${project.path})`);
        }
      }
      if (!hasLocalEdit) removable.push(skillName);
    }

    if (keptDueToLocalEdit.length) {
      log('\n  Descontinuadas com edição local — mantidas automaticamente:');
      keptDueToLocalEdit.forEach((entry) => log(`    ${entry}`));
    }

    if (removable.length) {
      const shouldRemove = await confirm({
        message: `Remover as ${removable.length} skill(s) descontinuada(s) dos projetos rastreados?`,
        initialValue: false,
      });
      if (!isCancel(shouldRemove) && shouldRemove) {
        for (const skillName of removable) {
          for (const project of registry.projects) {
            const installed = project.skills.find((sk) => sk.name === skillName);
            if (installed) {
              removeSymlink(installed.symlinkPath);
              project.skills = project.skills.filter((sk) => sk.name !== skillName);
            }
          }
        }
        log('  ✓ Skills descontinuadas removidas.');
      }
    }
  }

  // 7. Persist the new baseline (registry, hash cache and file snapshot)
  writeProjects(registry);
  writeCache(newCache);
  writeSnapshot(storePath);

  outro('Update concluído.');
}

/** Heuristic: a removed skill whose name closely matches a newly-added skill in the same bucket. */
function detectPossibleRename(
  removed: SkillDiff,
  allDiffs: SkillDiff[],
  available: SkillInfo[],
): string | undefined {
  const [bucket, name] = removed.skillRelativePath.split('/');
  const newSkillKeys = new Set(allDiffs.filter((d) => d.isNew).map((d) => d.skillRelativePath));
  const candidate = available.find(
    (sk) =>
      sk.bucket === bucket &&
      newSkillKeys.has(`${sk.bucket}/${sk.name}`) &&
      stringSimilarity(name, sk.name) > 0.6,
  );
  return candidate ? `${candidate.bucket}/${candidate.name}` : undefined;
}

function stringSimilarity(a: string, b: string): number {
  const longer = a.length >= b.length ? a : b;
  const shorter = a.length >= b.length ? b : a;
  if (!longer.length) return 1;
  return (longer.length - editDistance(longer, shorter)) / longer.length;
}

function editDistance(a: string, b: string): number {
  const dp = Array.from({ length: a.length + 1 }, (_, i) =>
    Array.from({ length: b.length + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0)),
  );
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      dp[i][j] =
        a[i - 1] === b[j - 1]
          ? dp[i - 1][j - 1]
          : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
    }
  }
  return dp[a.length][b.length];
}
