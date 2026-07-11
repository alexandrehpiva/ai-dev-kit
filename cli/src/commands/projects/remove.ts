import { readProjects, writeProjects } from '../../core/config.js';
import { runInitWizardIfNeeded } from '../../core/init.js';
import { cancel, intro, isCancel, outro, select } from '../../utils/ui.js';

interface RemoveOptions {
  path?: string;
}

export async function projectsRemove(options: RemoveOptions): Promise<void> {
  await runInitWizardIfNeeded();
  intro('ai-dev-kit projects remove');

  const registry = readProjects();

  if (!registry.projects.length) {
    console.log('Nenhum projeto rastreado.');
    outro('');
    return;
  }

  let targetPath = options.path;

  if (!targetPath) {
    const selected = await select({
      message: 'Selecione o projeto para remover do rastreamento:',
      options: registry.projects.map((p) => ({
        value: p.path,
        label: p.path,
        hint: `${p.skills.length} skill(s)`,
      })),
    });
    if (isCancel(selected)) {
      cancel('Cancelado.');
      process.exit(1);
    }
    targetPath = selected as string;
  }

  registry.projects = registry.projects.filter((p) => p.path !== targetPath);
  writeProjects(registry);

  console.log(`Projeto removido do rastreamento: ${targetPath}`);
  console.log('Nota: os symlinks no projeto não foram alterados.');
  outro('');
}
