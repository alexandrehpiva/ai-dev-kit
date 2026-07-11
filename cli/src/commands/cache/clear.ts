import { clearCache } from '../../core/cache.js';
import { runInitWizardIfNeeded } from '../../core/init.js';
import { intro, outro } from '../../utils/ui.js';

export async function cacheClear(): Promise<void> {
  await runInitWizardIfNeeded();
  intro('ai-dev-kit cache clear');
  clearCache();
  console.log('Cache limpo.');
  outro('');
}
