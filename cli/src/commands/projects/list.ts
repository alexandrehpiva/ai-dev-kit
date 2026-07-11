import { readProjects } from '../../core/config.js';
import { runInitWizardIfNeeded } from '../../core/init.js';
import { checkSymlinkStatus } from '../../core/symlinks.js';
import { intro, outro } from '../../utils/ui.js';

export async function projectsList(): Promise<void> {
  await runInitWizardIfNeeded();
  intro('ai-dev-kit projects list');

  const registry = readProjects();

  if (!registry.projects.length) {
    console.log('Nenhum projeto rastreado.');
    outro('');
    return;
  }

  for (const project of registry.projects) {
    console.log(`\n  ${project.path}`);
    console.log(`  instalado em: ${project.installedAt}`);

    for (const skill of project.skills) {
      const { status } = checkSymlinkStatus(skill);
      const icon = status === 'valid' ? '✓' : status === 'replaced' ? '⚠' : '✗';
      const hint =
        status === 'valid'
          ? ''
          : status === 'replaced'
            ? ' (arquivo real — possível edição local)'
            : status === 'broken'
              ? ' (symlink quebrado)'
              : ' (não encontrado)';
      console.log(`    ${icon} ${skill.name.padEnd(28)} [${skill.target}]${hint}`);
    }
  }

  outro('');
}
