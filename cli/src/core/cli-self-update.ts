import { execSync, spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

export const CLI_PACKAGE_NAME = 'ai-dev-kit';
export const CLI_BIN_NAMES = ['ai-dev-kit', 'aidk'] as const;

export type RunCommand = (cwd: string, command: string, args: string[]) => Promise<void>;
export type DiscoverBinPaths = (names: readonly string[]) => string[];

export function defaultBinDir(homedir: string = os.homedir()): string {
  return path.join(homedir, '.local', 'bin');
}

/** Resolve `{store}/cli` when it is the ai-dev-kit package. */
export function resolveCliPackageDir(storePath: string): string | null {
  const cliDir = path.join(storePath, 'cli');
  const pkgPath = path.join(cliDir, 'package.json');
  if (!fs.existsSync(pkgPath)) return null;
  try {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8')) as { name?: string };
    if (pkg.name !== CLI_PACKAGE_NAME) return null;
  } catch {
    return null;
  }
  return cliDir;
}

export function readCliPackageVersion(cliDir: string): string | undefined {
  try {
    const pkg = JSON.parse(fs.readFileSync(path.join(cliDir, 'package.json'), 'utf-8')) as {
      version?: string;
    };
    return pkg.version;
  } catch {
    return undefined;
  }
}

export function distIndexPath(cliDir: string): string {
  return path.join(cliDir, 'dist', 'index.js');
}

/**
 * Wipe only `cli/dist` so deleted/renamed sources cannot leave orphan `.js`.
 * Never touches skills, registry, config, or node_modules.
 */
export function cleanCliDist(cliDir: string): boolean {
  const dist = path.join(cliDir, 'dist');
  if (!fs.existsSync(dist)) return false;
  fs.rmSync(dist, { recursive: true, force: true });
  return true;
}

/** True when resolved path looks like `{kit}/cli/dist/index.js` (aidk or legacy kits). */
export function looksLikeKitCliEntrypoint(resolvedPath: string): boolean {
  const parts = path.normalize(resolvedPath).split(path.sep).filter(Boolean);
  const n = parts.length;
  return n >= 3 && parts[n - 1] === 'index.js' && parts[n - 2] === 'dist' && parts[n - 3] === 'cli';
}

export function defaultDiscoverBinPaths(names: readonly string[]): string[] {
  const found: string[] = [];
  for (const name of names) {
    try {
      const fromWhich = execSync(`which ${name}`, { encoding: 'utf-8' }).trim();
      if (fromWhich) found.push(path.resolve(fromWhich));
    } catch {
      /* not in PATH */
    }
  }
  return found;
}

function forceSymlink(target: string, linkPath: string): void {
  try {
    fs.rmSync(linkPath, { recursive: true, force: true });
  } catch {
    /* missing */
  }
  fs.symlinkSync(target, linkPath);
}

/** Symlink ~/.local/bin/{ai-dev-kit,aidk} → cli/dist/index.js (same as install.sh). */
export function ensureCliBinLinks(
  distIndex: string,
  binDir: string,
): { linked: string[]; skipped: string[] } {
  if (!fs.existsSync(distIndex)) {
    throw new Error(`CLI dist not found: ${distIndex}`);
  }
  fs.mkdirSync(binDir, { recursive: true });
  fs.chmodSync(distIndex, 0o755);

  const desiredReal = fs.realpathSync(distIndex);
  const linked: string[] = [];
  const skipped: string[] = [];

  for (const name of CLI_BIN_NAMES) {
    const binPath = path.join(binDir, name);
    try {
      const st = fs.lstatSync(binPath);
      if (st.isSymbolicLink() || st.isFile()) {
        try {
          if (fs.realpathSync(binPath) === desiredReal) {
            skipped.push(binPath);
            continue;
          }
        } catch {
          // broken link — replace
        }
        forceSymlink(distIndex, binPath);
        linked.push(binPath);
        continue;
      }
      forceSymlink(distIndex, binPath);
      linked.push(binPath);
    } catch {
      forceSymlink(distIndex, binPath);
      linked.push(binPath);
    }
  }

  return { linked, skipped };
}

/**
 * Redirect extra PATH bins that still point at an old kit CLI entrypoint.
 * Leaves unknown `aidk`/`ai-dev-kit` files alone (no blind deletes).
 * Does not touch skill symlinks or project registries.
 */
export function reconcileStaleCliBins(
  distIndex: string,
  primaryBinDir: string,
  extraCandidates: string[],
): { redirected: string[]; leftAlone: string[]; alreadyCurrent: string[] } {
  const desiredReal = fs.realpathSync(distIndex);
  const primaryResolved = new Set(
    CLI_BIN_NAMES.map((name) => path.resolve(path.join(primaryBinDir, name))),
  );

  const redirected: string[] = [];
  const leftAlone: string[] = [];
  const alreadyCurrent: string[] = [];
  const seen = new Set<string>();

  for (const raw of extraCandidates) {
    const binPath = path.resolve(raw);
    if (seen.has(binPath) || primaryResolved.has(binPath)) continue;
    seen.add(binPath);

    let resolved: string;
    try {
      resolved = fs.realpathSync(binPath);
    } catch {
      // broken link to old CLI name — safe to retarget
      forceSymlink(distIndex, binPath);
      redirected.push(binPath);
      continue;
    }

    if (resolved === desiredReal) {
      alreadyCurrent.push(binPath);
      continue;
    }

    if (looksLikeKitCliEntrypoint(resolved)) {
      forceSymlink(distIndex, binPath);
      redirected.push(binPath);
      continue;
    }

    leftAlone.push(binPath);
  }

  return { redirected, leftAlone, alreadyCurrent };
}

export async function defaultRunCommand(
  cwd: string,
  command: string,
  args: string[],
): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const child = spawn(command, args, {
      cwd,
      stdio: 'inherit',
      env: process.env,
      shell: process.platform === 'win32',
    });
    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${command} ${args.join(' ')} exited with code ${code}`));
    });
  });
}

export interface CliSelfUpdateResult {
  status: 'updated' | 'skipped';
  cliDir?: string;
  version?: string;
  reason?: string;
  linked?: string[];
  cleanedDist?: boolean;
  redirectedBins?: string[];
  leftAloneBins?: string[];
}

/**
 * Rebuild the CLI from `{storePath}/cli` and refresh global bin links.
 *
 * Scope (intentional):
 * - Touches: `cli/dist`, `pnpm` install/build, `ai-dev-kit`/`aidk` bin links
 * - Never touches: skills symlinks, projects registry, skill store content, config.json
 */
export async function updateCliFromStore(
  storePath: string,
  options: {
    binDir?: string;
    runCommand?: RunCommand;
    discoverBinPaths?: DiscoverBinPaths;
  } = {},
): Promise<CliSelfUpdateResult> {
  const cliDir = resolveCliPackageDir(storePath);
  if (!cliDir) {
    return {
      status: 'skipped',
      reason: 'Store sem pacote cli/ai-dev-kit — CLI não atualizado automaticamente.',
    };
  }

  const run = options.runCommand ?? defaultRunCommand;
  const discover = options.discoverBinPaths ?? defaultDiscoverBinPaths;
  const binDir = options.binDir ?? defaultBinDir();

  await run(cliDir, 'pnpm', ['install']);
  const cleanedDist = cleanCliDist(cliDir);
  await run(cliDir, 'pnpm', ['run', 'build']);

  const distIndex = distIndexPath(cliDir);
  const { linked } = ensureCliBinLinks(distIndex, binDir);
  const { redirected, leftAlone } = reconcileStaleCliBins(
    distIndex,
    binDir,
    discover([...CLI_BIN_NAMES]),
  );

  return {
    status: 'updated',
    cliDir,
    version: readCliPackageVersion(cliDir),
    linked,
    cleanedDist,
    redirectedBins: redirected,
    leftAloneBins: leftAlone,
  };
}
