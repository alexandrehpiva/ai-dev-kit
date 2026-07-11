import { getLocale, readConfig, readProjects, writeProjects } from '../../core/config.js';
import { runInitWizardIfNeeded } from '../../core/init.js';
import { SUPPORTED_LOCALES, listAvailableSkills } from '../../core/store.js';
import { checkSymlinkStatus, createSymlink, getTargetDir } from '../../core/symlinks.js';
import { cancel, intro, isCancel, outro, select } from '../../utils/ui.js';

interface SetLocaleOptions {
  locale?: string;
}

export async function skillsSetLocale(
  skillSelector: string | undefined,
  options: SetLocaleOptions,
): Promise<void> {
  await runInitWizardIfNeeded();

  intro('ai-dev-kit skills set-locale');

  const { storePath } = readConfig();
  const globalLocale = getLocale();
  const registry = readProjects();
  const projectPath = process.cwd();
  const project = registry.projects.find((p) => p.path === projectPath);

  if (!project || !project.skills.length) {
    console.log('Nenhuma skill instalada neste projeto.');
    outro('');
    return;
  }

  // Resolve which skill to target
  let skillName = skillSelector;
  if (!skillName) {
    const selected = await select({
      message: 'Selecione a skill para definir o locale:',
      options: project.skills.map((sk) => ({
        value: sk.name,
        label: sk.name,
        hint: `locale atual: ${sk.locale ?? 'default'} (${globalLocale})`,
      })),
    });
    if (isCancel(selected)) {
      cancel('Cancelado.');
      process.exit(1);
    }
    skillName = selected as string;
  }

  const installed = project.skills.find((sk) => sk.name === skillName);
  if (!installed) {
    console.error(`Skill "${skillName}" não encontrada no projeto.`);
    process.exit(1);
  }

  // Determine which locales are available for this skill in the store
  const allSkillsAllLocales = SUPPORTED_LOCALES.flatMap((loc) =>
    listAvailableSkills(storePath, { suppressCustomDuplicates: false, locale: loc }).filter(
      (s) => s.name === skillName && s.resolvedLocale === loc,
    ),
  );

  const availableLocales = [...new Set(allSkillsAllLocales.map((s) => s.resolvedLocale!))];

  if (!availableLocales.length) {
    console.error(
      `Skill "${skillName}" não possui versão locale no store (é flat/locale-agnostic).`,
    );
    outro('');
    return;
  }

  // Resolve target locale
  let targetLocale: string;

  if (options.locale) {
    if (!SUPPORTED_LOCALES.includes(options.locale as (typeof SUPPORTED_LOCALES)[number])) {
      console.error(
        `Locale inválido: "${options.locale}". Suportados: ${SUPPORTED_LOCALES.join(', ')}`,
      );
      process.exit(1);
    }
    if (!availableLocales.includes(options.locale)) {
      console.error(
        `Locale "${options.locale}" não disponível para "${skillName}". Disponíveis: ${availableLocales.join(', ')}`,
      );
      process.exit(1);
    }
    targetLocale = options.locale;
  } else {
    const localeOptions = [
      { value: 'default', label: 'default', hint: `segue locale global (${globalLocale})` },
      ...availableLocales.map((loc) => ({ value: loc, label: loc, hint: '' })),
    ];
    const selected = await select({
      message: `Locale para "${skillName}":`,
      options: localeOptions,
    });
    if (isCancel(selected)) {
      cancel('Cancelado.');
      process.exit(1);
    }
    targetLocale = selected as string;
  }

  // Re-link symlink to the resolved locale path
  const resolvedLocale = targetLocale === 'default' ? globalLocale : targetLocale;
  const storeSkill = listAvailableSkills(storePath, {
    suppressCustomDuplicates: false,
    locale: resolvedLocale,
  }).find((s) => s.name === skillName);

  if (!storeSkill) {
    console.error(`Skill "${skillName}" não encontrada no store para locale "${resolvedLocale}".`);
    process.exit(1);
  }

  const { status } = checkSymlinkStatus(installed);
  if (status === 'missing') {
    console.error(`Symlink de "${skillName}" não encontrado. Reinstale a skill.`);
    process.exit(1);
  }

  const targetDir = getTargetDir(projectPath, installed.target, installed.targetPath);
  const updated = createSymlink(
    storeSkill,
    targetDir,
    installed.target,
    installed.targetPath,
    targetLocale,
  );

  const idx = project.skills.findIndex((sk) => sk.name === skillName);
  if (idx !== -1) project.skills[idx] = updated;

  writeProjects(registry);

  const displayLocale = targetLocale === 'default' ? `default (${resolvedLocale})` : targetLocale;
  console.log(`  ✓ ${String(skillName).padEnd(28)} locale → ${displayLocale}`);

  outro('Rode "ai-dev-kit update" para sincronizar se necessário.');
}
