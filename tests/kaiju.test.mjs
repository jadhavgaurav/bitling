import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const source = await readFile(new URL('../apps/macos/web/bitling.html', import.meta.url), 'utf8');
function footPose(phase) {
  const match = source.match(/  function kaijuFootPose\(phase\) \{[\s\S]*?\n  \}/);
  assert.ok(match, 'Godzilla needs an explicit stance/swing cycle to prevent foot skating');
  return vm.runInNewContext(`${match[0]}; kaijuFootPose(${phase});`);
}

test('a planted foot cancels forward travel throughout the stance', () => {
  const a = footPose(0.1), b = footPose(0.5);
  assert.equal(a.lift, 0);
  assert.equal(b.lift, 0);
  assert.ok(Math.abs((b.x - a.x) - 0.72 * (0.5 - 0.1) / 0.62) < 1e-9);
});
test('feet lift only on recovery and never both leave the floor', () => {
  for (let i = 0; i < 100; i++) {
    const a = footPose(i / 100), b = footPose(i / 100 + 0.5);
    assert.ok(a.lift >= 0 && a.lift <= 0.12);
    assert.ok(a.lift === 0 || b.lift === 0, 'at least one foot must bear the weight');
  }
  assert.ok(footPose(0.81).lift > 0.11);
});
test('the walk loop is continuous at lift-off and touchdown', () => {
  for (const phase of [0, 0.62, 1]) {
    const a = footPose(phase - 1e-7), b = footPose(phase + 1e-7);
    assert.ok(Math.abs(a.x - b.x) < 0.00001);
    assert.ok(Math.abs(a.lift - b.lift) < 0.00001);
  }
});
