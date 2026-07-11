import { readConfig, writeConfig } from '../../core/config.js';
import { runInitWizardIfNeeded } from '../../core/init.js';
import { SUPPORTED_LOCALES } from '../../core/store.js';
import { intro, outro } from '../../utils/ui.js';

export async function configSetLocale(locale: string): Promise<void> {
  await runInitWizardIfNeeded();

  intro('ai-dev-kit config set-locale');

  if (!SUPPORTED_LOCALES.includes(locale as (typeof SUPPORTED_LOCALES)[number])) {
    console.error(`Locale inválido: "${locale}". Suportados: ${SUPPORTED_LOCALES.join(', ')}`);
    process.exit(1);
  }

  const config = readConfig();
  const previous = config.locale ?? 'pt-BR';
  config.locale = locale;
  writeConfig(config);

  console.log(`  ✓ Locale global: ${previous} → ${locale}`);
  console.log('  Skills com locale "default" serão atualizadas no próximo "ai-dev-kit update".');

  outro('');
}
