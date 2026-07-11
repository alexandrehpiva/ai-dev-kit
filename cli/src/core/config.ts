import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import type { GlobalConfig, ProjectsRegistry } from '../types.js';

const DEFAULT_CONFIG_DIR = path.join(os.homedir(), '.config', 'ai-dev-kit');

export function getConfigDir(): string {
  return process.env.AI_DEV_KIT_HOME ?? DEFAULT_CONFIG_DIR;
}

export function getConfigPath(): string {
  return path.join(getConfigDir(), 'config.json');
}

export function getProjectsPath(): string {
  return path.join(getConfigDir(), 'projects.json');
}

export function getCacheDir(): string {
  return path.join(getConfigDir(), 'cache');
}

export function configExists(): boolean {
  return fs.existsSync(getConfigPath());
}

export function readConfig(): GlobalConfig {
  const raw = fs.readFileSync(getConfigPath(), 'utf-8');
  return JSON.parse(raw) as GlobalConfig;
}

export function getLocale(): string {
  return readConfig().locale ?? 'pt-BR';
}

export function writeConfig(config: GlobalConfig): void {
  fs.mkdirSync(getConfigDir(), { recursive: true });
  fs.writeFileSync(getConfigPath(), JSON.stringify(config, null, 2));
}

export function readProjects(): ProjectsRegistry {
  const p = getProjectsPath();
  if (!fs.existsSync(p)) return { projects: [] };
  return JSON.parse(fs.readFileSync(p, 'utf-8')) as ProjectsRegistry;
}

export function writeProjects(registry: ProjectsRegistry): void {
  fs.mkdirSync(getConfigDir(), { recursive: true });
  fs.writeFileSync(getProjectsPath(), JSON.stringify(registry, null, 2));
}
