import path from 'node:path';

import { runInitWizard, silentInit } from '../core/init.js';

interface InitOptions {
  storePath?: string;
  yes?: boolean;
}

export async function initCommand(options: InitOptions): Promise<void> {
  if (options.storePath && options.yes) {
    silentInit(path.resolve(options.storePath));
    return;
  }
  await runInitWizard();
}
