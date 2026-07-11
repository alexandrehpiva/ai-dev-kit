import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { cancel, confirm, intro, isCancel, outro, spinner, text } from '../utils/ui.js';

import { configExists, getConfigDir, writeConfig } from './config.js';
import { cloneStore, isGitRepo } from './store.js';

export function silentInit(storePath: string): void {
  const configDir = getConfigDir();
  fs.mkdirSync(configDir, { recursive: true });
  writeConfig({ storePath, configDir });
  console.log(`✓ ai-dev-kit configurado: store em ${storePath}`);
}

const DEFAULT_STORE_PATH = path.join(os.homedir(), '.config', 'ai-dev-kit', 'framework');

export async function runInitWizardIfNeeded(): Promise<void> {
  if (configExists()) return;
  await runInitWizard();
}

export async function runInitWizard(): Promise<void> {
  intro('ai-dev-kit — configuração inicial');

  const configDir = getConfigDir();
  console.log(`\nDiretório de config: ${configDir}`);
  console.log(
    'Para alterar, defina a variável de ambiente AI_DEV_KIT_HOME antes de rodar o CLI.\n',
  );

  const storePath = await text({
    message: 'Caminho onde o ai-dev-kit será clonado:',
    placeholder: DEFAULT_STORE_PATH,
    initialValue: DEFAULT_STORE_PATH,
    validate(value) {
      if (!value.trim()) return 'Informe um caminho válido.';
    },
  });

  if (isCancel(storePath)) {
    cancel('Configuração cancelada.');
    process.exit(1);
  }

  const resolvedStore = path.resolve(storePath as string);

  if (!fs.existsSync(resolvedStore)) {
    const shouldClone = await confirm({
      message: `${resolvedStore} não existe. Clonar o repositório agora?`,
      initialValue: true,
    });

    if (isCancel(shouldClone) || !shouldClone) {
      cancel('Configure o store manualmente e rode o CLI novamente.');
      process.exit(1);
    }

    const s = spinner();
    s.start('Clonando ai-dev-kit...');
    try {
      await cloneStore(resolvedStore);
      s.stop('Repositório clonado com sucesso.');
    } catch (err) {
      s.stop('Erro ao clonar o repositório.');
      throw err;
    }
  } else if (!isGitRepo(resolvedStore)) {
    console.log(
      `\nAviso: ${resolvedStore} existe mas não parece um repositório git. Verifique o caminho.\n`,
    );
  }

  fs.mkdirSync(configDir, { recursive: true });
  writeConfig({ storePath: resolvedStore, configDir });

  outro(`Config salvo em ${path.join(configDir, 'config.json')}`);
}
