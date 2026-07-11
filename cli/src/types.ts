export type Target = 'claude' | 'cursor' | 'custom';

export interface GlobalConfig {
  storePath: string;
  configDir: string;
  locale?: string;
}

export interface InstalledSkill {
  name: string;
  bucket: string;
  target: Target;
  targetPath: string;
  symlinkPath: string;
  /** "default" follows config.locale; a specific value pins this skill. Absent = "default". */
  locale?: string;
}

export interface RegisteredProject {
  path: string;
  installedAt: string;
  skills: InstalledSkill[];
}

export interface ProjectsRegistry {
  projects: RegisteredProject[];
}

export interface CacheEntry {
  relativePath: string;
  hash: string;
  updatedAt: string;
}

export interface SkillCache {
  storeCommit: string;
  updatedAt: string;
  entries: CacheEntry[];
}

export interface SkillInfo {
  name: string;
  bucket: string;
  /** Absolute path to the skill folder in the store (locale subfolder when locale-aware) */
  storePath: string;
  description: string;
  /** Set when the user's locale is unavailable and a fallback locale was used, e.g. "pt-BR only" */
  localeHint?: string;
  /** The resolved locale for this skill entry, e.g. "pt-BR" or "en-US". Absent for flat skills. */
  resolvedLocale?: string;
}

export type SymlinkStatus = 'valid' | 'replaced' | 'broken' | 'missing';

export interface SkillSymlinkStatus {
  skill: InstalledSkill;
  status: SymlinkStatus;
}
