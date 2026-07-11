#!/usr/bin/env node

import { Command } from 'commander';

import { cacheClear } from './commands/cache/clear.js';
import { configSetLocale } from './commands/config/set-locale.js';
import { initCommand } from './commands/init.js';
import { projectsList } from './commands/projects/list.js';
import { projectsRemove } from './commands/projects/remove.js';
import { installSkills } from './commands/skills/install.js';
import { listSkills } from './commands/skills/list.js';
import { skillsSetLocale } from './commands/skills/set-locale.js';
import { switchSkills } from './commands/skills/switch.js';
import { uninstallSkills } from './commands/skills/uninstall.js';
import { uninstall } from './commands/uninstall.js';
import update from './commands/update.js';

const program = new Command();

program
  .name('ai-dev-kit')
  .description('CLI for managing AI Dev Kit skills and resources')
  .version('0.1.5');

// --- init ---
program
  .command('init')
  .description('Configure the ai-dev-kit store path')
  .option('--store-path <path>', 'Absolute path to the ai-dev-kit repository')
  .option('--yes', 'Apply immediately without interactive wizard')
  .action(initCommand);

// --- skills ---
const skills = program.command('skills').description('Manage skills in the current project');

skills
  .command('install')
  .description('Install skills via symlinks in the current project')
  .option('--target <claude|cursor|custom>', 'Target agent (skips interactive prompt)')
  .option('--path <path>', 'Custom target path (required with --target custom)')
  .option('--skills <names>', 'Comma-separated skill names to install')
  .option('--bucket <name>', 'Install all skills from a bucket')
  .option('--all', 'Install all available skills')
  .action(installSkills);

skills.command('list').description('List all available skills in the store').action(listSkills);

skills
  .command('switch')
  .description('Switch installed skills between custom and official versions')
  .option(
    '--skills <names>',
    'Comma-separated skill names or bucket/name selectors (non-interactive)',
  )
  .action(switchSkills);

skills
  .command('set-locale [skill]')
  .description('Set the locale for a specific installed skill (default follows global locale)')
  .option('--locale <locale>', 'Locale to set (pt-BR, en-US, or "default")')
  .action(skillsSetLocale);

skills
  .command('uninstall')
  .description('Remove skill symlinks from the current project')
  .option(
    '--skills <names>',
    'Comma-separated skill names or bucket/name selectors (non-interactive)',
  )
  .option('--target <claude|cursor|custom>', 'Only remove entries for this target (with --skills)')
  .option('--all', 'Remove all skills installed in the current project')
  .action(uninstallSkills);

// --- update ---
program
  .command('update')
  .description('Pull store, rebuild CLI (pnpm), refresh bins, and update registered project skills')
  .option('--no-pull', 'Skip git pull; rebuild from the current store tree (rollback-friendly)')
  .option('--cli-only', 'Only rebuild/relink the CLI; skip skill symlink sync')
  .action(update);

// --- uninstall (the whole tool) ---
program
  .command('uninstall')
  .description('Remove all local config, caches and skill symlinks across tracked projects')
  .option('--yes', 'Skip the confirmation prompt')
  .action(uninstall);

// --- config ---
const config = program.command('config').description('Manage global CLI configuration');

config
  .command('set-locale <locale>')
  .description('Set the global default locale for skills (pt-BR or en-US)')
  .action(configSetLocale);

// --- cache ---
const cache = program.command('cache').description('Manage the local skills cache');

cache.command('clear').description('Clear the local skills comparison cache').action(cacheClear);

// --- projects ---
const projects = program.command('projects').description('Manage tracked projects');

projects
  .command('list')
  .description('List all tracked projects and their symlink statuses')
  .action(projectsList);

projects
  .command('remove')
  .description('Remove a project from tracking (does not touch symlinks)')
  .option('--path <path>', 'Project path to remove (skips interactive prompt)')
  .action(projectsRemove);

program.parseAsync().catch((err: unknown) => {
  const message = err instanceof Error ? err.message : String(err);
  console.error(`\n✗ ${message}`);
  process.exit(1);
});
