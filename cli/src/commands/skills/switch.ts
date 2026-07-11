import { readConfig, readProjects, writeProjects } from '../../core/config.js';
import { runInitWizardIfNeeded } from '../../core/init.js';
import { listAvailableSkills } from '../../core/store.js';
import { checkSymlinkStatus, createSymlink, getTargetDir } from '../../core/symlinks.js';
import type { InstalledSkill, SkillInfo } from '../../types.js';
import { cancel, intro, isCancel, multiselect, outro, spinner } from '../../utils/ui.js';

interface SwitchCandidate {
  installed: InstalledSkill;
  alternate: SkillInfo;
}

interface SwitchOptions {
  skills?: string;
}

export async function switchSkills(options: SwitchOptions): Promise<void> {
  await runInitWizardIfNeeded();

  intro('ai-dev-kit skills switch');

  const { storePath } = readConfig();
  const allSkills = listAvailableSkills(storePath, { suppressCustomDuplicates: false });
  const registry = readProjects();
  const projectPath = process.cwd();
  const project = registry.projects.find((p) => p.path === projectPath);

  if (!project || !project.skills.length) {
    console.log('Nenhuma skill instalada neste projeto.');
    outro('');
    return;
  }

  // Find installed skills that have an alternate version available in the store.
  const candidates: SwitchCandidate[] = [];

  for (const installed of project.skills) {
    const { status } = checkSymlinkStatus(installed);
    if (status === 'missing' || status === 'broken') continue;

    const alternate = allSkills.find(
      (s) => s.name === installed.name && s.bucket !== installed.bucket,
    );
    if (alternate) candidates.push({ installed, alternate });
  }

  if (!candidates.length) {
    console.log('Nenhuma skill instalada tem versão alternativa disponível.');
    outro('');
    return;
  }

  let toSwitch: SwitchCandidate[];

  if (options.skills) {
    // Non-interactive: resolve each selector against the candidates list.
    // Accepts "name" (short) or "bucket/name" (explicit target version).
    const selectors = options.skills.split(',').map((s) => s.trim());
    toSwitch = selectors.map((selector) => {
      const slashIdx = selector.indexOf('/');
      if (slashIdx !== -1) {
        // bucket/name — the user specified the desired destination bucket.
        const targetBucket = selector.slice(0, slashIdx);
        const name = selector.slice(slashIdx + 1);
        const candidate = candidates.find(
          (c) => c.installed.name === name && c.alternate.bucket === targetBucket,
        );
        if (!candidate) {
          console.error(`Skill não encontrada ou sem alternativa para trocar: ${selector}`);
          process.exit(1);
        }
        return candidate;
      }
      // Short name — single alternate assumed.
      const candidate = candidates.find((c) => c.installed.name === selector);
      if (!candidate) {
        console.error(`Skill não encontrada ou sem alternativa para trocar: ${selector}`);
        process.exit(1);
      }
      return candidate;
    });
  } else {
    const selected = await multiselect({
      message: 'Selecione as skills para trocar de versão:',
      options: candidates.map(({ installed, alternate }) => ({
        value: `${installed.bucket}/${installed.name}`,
        label: installed.name,
        hint: `${installed.bucket} → ${alternate.bucket}`,
      })),
      required: true,
    });

    if (isCancel(selected)) {
      cancel('Cancelado.');
      process.exit(1);
    }

    const selectedKeys = new Set(selected as string[]);
    toSwitch = candidates.filter((c) =>
      selectedKeys.has(`${c.installed.bucket}/${c.installed.name}`),
    );
  }

  const s = spinner();
  s.start('Trocando symlinks...');

  for (const { installed, alternate } of toSwitch) {
    const targetDir = getTargetDir(projectPath, installed.target, installed.targetPath);
    const updated = createSymlink(alternate, targetDir, installed.target, installed.targetPath);

    const idx = project.skills.findIndex((sk) => sk.name === installed.name);
    if (idx !== -1) project.skills[idx] = updated;
  }

  writeProjects(registry);

  s.stop(`${toSwitch.length} skill(s) trocada(s).`);

  for (const { installed, alternate } of toSwitch) {
    console.log(`  ✓ ${installed.name.padEnd(28)} ${installed.bucket} → ${alternate.bucket}`);
  }

  outro('');
}
