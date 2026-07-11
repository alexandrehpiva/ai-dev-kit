import { execSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { configExists, getConfigDir, readConfig, readProjects } from '../core/config.js';
import { checkSymlinkStatus, removeSymlink } from '../core/symlinks.js';
import { confirm, intro, isCancel, log, outro } from '../utils/ui.js';

function removeBinary(): void {
  const binDir = path.join(os.homedir(), '.local', 'bin');
  const candidates = [path.join(binDir, 'ai-dev-kit'), path.join(binDir, 'aidk')];
  for (const name of ['ai-dev-kit', 'aidk']) {
    try {
      const fromWhich = execSync(`which ${name}`, { encoding: 'utf-8' }).trim();
      if (fromWhich && !candidates.includes(fromWhich)) candidates.push(fromWhich);
    } catch {
      /* not in PATH */
    }
  }

  let removed = false;
  for (const binPath of candidates) {
    if (fs.existsSync(binPath)) {
      fs.unlinkSync(binPath);
      log(`  Binário removido: ${binPath}`);
      removed = true;
    }
  }
  if (!removed) {
    log('  Binário não encontrado — nada a remover.');
  }
}

interface UninstallOptions {
  yes?: boolean;
}

export async function uninstall(options: UninstallOptions): Promise<void> {
  intro('ai-dev-kit uninstall');

  if (!configExists()) {
    log('Nenhuma configuração local encontrada.');
    const proceed = options.yes
      ? true
      : await confirm({
          message: 'Remover apenas o binário global?',
          initialValue: true,
        });
    if (isCancel(proceed) || !proceed) {
      outro('Cancelado.');
      return;
    }
    removeBinary();
    outro('Binário removido.');
    return;
  }

  const configDir = getConfigDir();
  const registry = readProjects();
  const totalSkills = registry.projects.reduce((acc, p) => acc + p.skills.length, 0);

  let storePath: string | undefined;
  try {
    storePath = readConfig().storePath;
  } catch {
    storePath = undefined;
  }

  log('\nIsto irá:');
  log(
    `  • remover symlinks de skills de ${registry.projects.length} projeto(s) (${totalSkills} skill[s])`,
  );
  log(`  • apagar toda a configuração local em ${configDir}`);
  log('    (config.json, projects.json, cache e snapshot)');
  log('  • edições locais — skills cujo symlink virou arquivo real — são preservadas');
  log('');

  const proceed = options.yes
    ? true
    : await confirm({
        message: 'Confirma a desinstalação completa? Esta ação é irreversível.',
        initialValue: false,
      });

  if (isCancel(proceed) || !proceed) {
    outro('Desinstalação cancelada.');
    return;
  }

  // 1. Remove skill symlinks across all registered projects, preserving local edits
  let removed = 0;
  let preserved = 0;
  for (const project of registry.projects) {
    for (const skill of project.skills) {
      const { status } = checkSymlinkStatus(skill);
      if (status === 'replaced') {
        preserved++;
        log(`  — preservada (edição local): ${skill.name} em ${project.path}`);
        continue;
      }
      removeSymlink(skill.symlinkPath);
      removed++;
    }
  }

  log(`\n  ${removed} symlink(s) removido(s)${preserved ? `, ${preserved} preservada(s)` : ''}.`);

  // 2. Delete the entire local config directory (includes cache, snapshot and,
  //    when using the default layout, the cloned framework store)
  fs.rmSync(configDir, { recursive: true, force: true });
  log(`  Configuração local apagada: ${configDir}`);

  if (storePath && !storePath.startsWith(configDir)) {
    log(`\n  Nota: o store em ${storePath} está fora da config e NÃO foi removido.`);
  }

  // 3. Remove the global binary link
  removeBinary();

  outro('Desinstalação concluída.');
}
