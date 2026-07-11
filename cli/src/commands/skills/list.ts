import { readConfig } from '../../core/config.js';
import { runInitWizardIfNeeded } from '../../core/init.js';
import { listAvailableSkills } from '../../core/store.js';
import { intro, outro } from '../../utils/ui.js';

export async function listSkills(): Promise<void> {
  await runInitWizardIfNeeded();

  intro('ai-dev-kit skills list');

  const { storePath } = readConfig();
  const skills = listAvailableSkills(storePath, { suppressCustomDuplicates: false });

  if (!skills.length) {
    console.log('Nenhuma skill encontrada no store.');
    outro('');
    return;
  }

  const buckets = [...new Set(skills.map((s) => s.bucket))];

  for (const bucket of buckets) {
    console.log(`\n  ${bucket}/`);
    for (const skill of skills.filter((s) => s.bucket === bucket)) {
      const fullName = `${bucket}/${skill.name}`;
      console.log(`    ${fullName.padEnd(40)} ${skill.description.slice(0, 55)}`);
    }
  }

  console.log(`\n  Total: ${skills.length} skill(s) em ${buckets.length} bucket(s)`);
  outro('');
}
