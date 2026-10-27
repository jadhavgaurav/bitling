import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, mkdir, writeFile, rm, realpath } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';

const run = promisify(execFile);

const DRIVER = `import Foundation
let paths = Array(CommandLine.arguments.dropFirst())
UserDefaults.standard.set(paths, forKey: "gitRepoCache")
UserDefaults.standard.removeObject(forKey: "gitToday")
let watcher = GitWatcher()
watcher.primeFromCache()
watcher.seedToday()
let first = watcher.commitsToday
watcher.seedToday()
print("\\(first) \\(watcher.commitsToday)")
`;

// One commit is visible through several reflogs: the linked worktree's own log, and the main
// repository's scan of every worktree. The display counted it once per path (706 shown for 436
// real commits), so the count must follow commits, not events.
test('today\'s commit count counts each commit once, even across linked worktrees', async (t) => {
  try { await run('swiftc', ['--version']); } catch { return t.skip('swiftc is not installed'); }
  const directory = await realpath(await mkdtemp(join(tmpdir(), 'bitling-git-count-')));
  try {
    const main = join(directory, 'main'), linked = join(directory, 'linked');
    const git = (cwd, args, env = {}) => run('git', args, { cwd, env: { ...process.env, GIT_AUTHOR_NAME: 'T', GIT_AUTHOR_EMAIL: 't@t', GIT_COMMITTER_NAME: 'T', GIT_COMMITTER_EMAIL: 't@t', ...env } });
    await mkdir(main);
    await git(main, ['init', '-q', '-b', 'main']);
    const commit = async (cwd, name, env) => { await writeFile(join(cwd, name), name); await git(cwd, ['add', name]); await git(cwd, ['commit', '-q', '-m', name], env); };
    const twoDaysAgo = new Date(Date.now() - 2 * 864e5).toISOString();
    await commit(main, 'old', { GIT_COMMITTER_DATE: twoDaysAgo, GIT_AUTHOR_DATE: twoDaysAgo });
    await commit(main, 'a'); await commit(main, 'b'); await commit(main, 'c');
    await git(main, ['worktree', 'add', '-q', '-b', 'feature', linked]);
    await commit(linked, 'd'); await commit(linked, 'e');

    await writeFile(join(directory, 'main.swift'), DRIVER);
    const binary = join(directory, 'counter');
    await run('swiftc', ['-swift-version', '5', '-framework', 'Cocoa', 'apps/macos/Sources/GitWatcher.swift', join(directory, 'main.swift'), '-o', binary]);
    const { stdout } = await run(binary, [main, linked]);
    assert.equal(stdout.trim(), '5 5', 'three on main and two in the worktree, today only, once each, and reseeding adds nothing');
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
