import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { describe, it } from 'node:test';

import {
  cleanCliDist,
  defaultBinDir,
  distIndexPath,
  ensureCliBinLinks,
  looksLikeKitCliEntrypoint,
  reconcileStaleCliBins,
  resolveCliPackageDir,
  updateCliFromStore,
} from './cli-self-update.ts';

function makeTempDir(prefix: string): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

describe('resolveCliPackageDir', () => {
  it('Given store with cli/package.json named ai-dev-kit When resolving Then returns cli dir', () => {
    // Given
    const store = makeTempDir('aidk-store-');
    const cliDir = path.join(store, 'cli');
    fs.mkdirSync(cliDir);
    fs.writeFileSync(path.join(cliDir, 'package.json'), JSON.stringify({ name: 'ai-dev-kit' }));

    // When / Then
    assert.equal(resolveCliPackageDir(store), cliDir);
  });

  it('Given wrong package name When resolving Then returns null', () => {
    // Given
    const store = makeTempDir('aidk-store-');
    const cliDir = path.join(store, 'cli');
    fs.mkdirSync(cliDir);
    fs.writeFileSync(path.join(cliDir, 'package.json'), JSON.stringify({ name: 'other' }));

    // When / Then
    assert.equal(resolveCliPackageDir(store), null);
  });
});

describe('cleanCliDist', () => {
  it('Given orphan js in dist When cleaning Then removes dist tree only', () => {
    // Given
    const cliDir = makeTempDir('aidk-cli-');
    const dist = path.join(cliDir, 'dist');
    fs.mkdirSync(dist);
    fs.writeFileSync(path.join(dist, 'orphan.js'), 'old');
    fs.writeFileSync(path.join(cliDir, 'package.json'), '{}');

    // When
    const cleaned = cleanCliDist(cliDir);

    // Then
    assert.equal(cleaned, true);
    assert.equal(fs.existsSync(dist), false);
    assert.ok(fs.existsSync(path.join(cliDir, 'package.json')));
  });
});

describe('looksLikeKitCliEntrypoint', () => {
  it('Given path ending in cli/dist/index.js When checking Then true', () => {
    assert.equal(looksLikeKitCliEntrypoint('/Users/x/Projects/ai-dev-kit/cli/dist/index.js'), true);
  });

  it('Given unrelated binary When checking Then false', () => {
    assert.equal(looksLikeKitCliEntrypoint('/usr/local/bin/aidk'), false);
  });
});

describe('ensureCliBinLinks', () => {
  it('Given dist index When linking Then creates ai-dev-kit and aidk symlinks', () => {
    // Given
    const root = makeTempDir('aidk-bin-');
    const distDir = path.join(root, 'cli', 'dist');
    const binDir = path.join(root, 'bin');
    fs.mkdirSync(distDir, { recursive: true });
    const distIndex = path.join(distDir, 'index.js');
    fs.writeFileSync(distIndex, '#!/usr/bin/env node\n');

    // When
    const result = ensureCliBinLinks(distIndex, binDir);

    // Then
    assert.equal(result.linked.length, 2);
    assert.equal(fs.realpathSync(path.join(binDir, 'ai-dev-kit')), fs.realpathSync(distIndex));
    assert.equal(fs.realpathSync(path.join(binDir, 'aidk')), fs.realpathSync(distIndex));
  });

  it('Given existing correct symlink When linking Then skips', () => {
    // Given
    const root = makeTempDir('aidk-bin-');
    const distIndex = path.join(root, 'index.js');
    const binDir = path.join(root, 'bin');
    fs.writeFileSync(distIndex, 'ok');
    fs.mkdirSync(binDir);
    fs.symlinkSync(distIndex, path.join(binDir, 'ai-dev-kit'));
    fs.symlinkSync(distIndex, path.join(binDir, 'aidk'));

    // When
    const result = ensureCliBinLinks(distIndex, binDir);

    // Then
    assert.equal(result.skipped.length, 2);
    assert.equal(result.linked.length, 0);
  });
});

describe('reconcileStaleCliBins', () => {
  it('Given extra PATH bin pointing at old kit When reconciling Then redirects to new dist', () => {
    // Given
    const root = makeTempDir('aidk-rec-');
    const oldDist = path.join(root, 'old-kit', 'cli', 'dist');
    const newDist = path.join(root, 'new-kit', 'cli', 'dist');
    const primaryBin = path.join(root, 'primary-bin');
    const otherBin = path.join(root, 'other-bin');
    fs.mkdirSync(oldDist, { recursive: true });
    fs.mkdirSync(newDist, { recursive: true });
    fs.mkdirSync(primaryBin);
    fs.mkdirSync(otherBin);
    fs.writeFileSync(path.join(oldDist, 'index.js'), 'old');
    const newIndex = path.join(newDist, 'index.js');
    fs.writeFileSync(newIndex, 'new');
    const stale = path.join(otherBin, 'aidk');
    fs.symlinkSync(path.join(oldDist, 'index.js'), stale);

    // When
    const result = reconcileStaleCliBins(newIndex, primaryBin, [stale]);

    // Then
    assert.deepEqual(result.redirected, [stale]);
    assert.equal(fs.realpathSync(stale), fs.realpathSync(newIndex));
  });

  it('Given unknown aidk file When reconciling Then leaves alone', () => {
    // Given
    const root = makeTempDir('aidk-leave-');
    const newIndex = path.join(root, 'cli', 'dist', 'index.js');
    fs.mkdirSync(path.dirname(newIndex), { recursive: true });
    fs.writeFileSync(newIndex, 'new');
    const primaryBin = path.join(root, 'primary');
    fs.mkdirSync(primaryBin);
    const weird = path.join(root, 'weird-aidk');
    fs.writeFileSync(weird, '#!/bin/sh\necho hi\n');

    // When
    const result = reconcileStaleCliBins(newIndex, primaryBin, [weird]);

    // Then
    assert.deepEqual(result.leftAlone, [weird]);
    assert.equal(fs.readFileSync(weird, 'utf-8').includes('echo hi'), true);
  });
});

describe('updateCliFromStore', () => {
  it('Given orphan dist and mock pnpm When updating Then cleans orphans builds and links', async () => {
    // Given
    const store = makeTempDir('aidk-upd-');
    const cliDir = path.join(store, 'cli');
    const binDir = path.join(store, 'home-bin');
    fs.mkdirSync(path.join(cliDir, 'dist'), { recursive: true });
    fs.writeFileSync(path.join(cliDir, 'dist', 'orphan.js'), 'stale');
    fs.writeFileSync(
      path.join(cliDir, 'package.json'),
      JSON.stringify({ name: 'ai-dev-kit', version: '0.1.3' }),
    );
    const calls: string[] = [];
    const runCommand = async (cwd: string, command: string, args: string[]): Promise<void> => {
      calls.push(`${cwd}|${command}|${args.join(' ')}`);
      if (args.includes('build')) {
        fs.mkdirSync(path.join(cliDir, 'dist'), { recursive: true });
        fs.writeFileSync(distIndexPath(cliDir), '#!/usr/bin/env node\n');
      }
    };

    // When
    const result = await updateCliFromStore(store, {
      binDir,
      runCommand,
      discoverBinPaths: () => [],
    });

    // Then
    assert.equal(result.status, 'updated');
    assert.equal(result.cleanedDist, true);
    assert.equal(result.version, '0.1.3');
    assert.equal(fs.existsSync(path.join(cliDir, 'dist', 'orphan.js')), false);
    assert.deepEqual(calls, [`${cliDir}|pnpm|install`, `${cliDir}|pnpm|run build`]);
    assert.ok(fs.existsSync(path.join(binDir, 'aidk')));
  });

  it('Given store without cli When updating Then skips', async () => {
    // Given
    const store = makeTempDir('aidk-skip-');

    // When
    const result = await updateCliFromStore(store);

    // Then
    assert.equal(result.status, 'skipped');
    assert.match(result.reason ?? '', /Store sem pacote/);
  });
});

describe('defaultBinDir', () => {
  it('Given homedir When resolving Then uses .local/bin', () => {
    assert.equal(defaultBinDir('/Users/alex'), path.join('/Users/alex', '.local', 'bin'));
  });
});
