import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import test from 'node:test';
const run = promisify(execFile);

async function hasDotnet() {
  try { await run('dotnet', ['--version']); return true; } catch { return false; }
}

test('the Windows usage logic (parsers, colours, merge) passes its checks', async (t) => {
  if (!await hasDotnet()) { t.skip('the .NET SDK is not installed'); return; }
  const { stdout } = await run('dotnet', ['run', '--project', 'apps/windows/Bitling.Windows.Checks'], { timeout: 240000 });
  assert.match(stdout, /all checks passed/, stdout);
  assert.doesNotMatch(stdout, /FAIL/, stdout);
});

test('the Windows app, tray usage included, compiles', async (t) => {
  if (!await hasDotnet()) { t.skip('the .NET SDK is not installed'); return; }
  // EnableWindowsTargeting lets a Mac or Linux machine compile the Windows-only project.
  const { stdout } = await run('dotnet', ['build', 'apps/windows/Bitling.Windows/Bitling.Windows.csproj',
    '-p:EnableWindowsTargeting=true', '-v:q', '-nologo'], { timeout: 480000 });
  assert.match(stdout, /0 Error\(s\)/, stdout);
});
