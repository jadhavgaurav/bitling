import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';

const run = promisify(execFile);
test('the actual desktop attack renderer produces cyan atomic breath', async () => {
  const html = await readFile('apps/macos/web/bitling.html', 'utf8');
  const style = html.slice(html.indexOf("id: 'kaiju'")).match(/style: '([^']+)'/)[1];
  const overlay = await readFile('apps/macos/Sources/Overlay.swift', 'utf8');
  const directory = await mkdtemp(join(tmpdir(), 'bitling-native-test-'));
  try {
    const probe = `
let testWidth = 320, testHeight = 100
let testContext = CGContext(data: nil, width: testWidth, height: testHeight,
    bitsPerComponent: 8, bytesPerRow: testWidth * 4, space: CGColorSpaceCreateDeviceRGB(),
    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
NSGraphicsContext.current = NSGraphicsContext(cgContext: testContext, flipped: false)
let testView = OverlayView(frame: NSRect(x: 0, y: 0, width: testWidth, height: testHeight))
testView.beams = [Beam(from: CGPoint(x: 20, y: 50), to: CGPoint(x: 300, y: 50), life: 0.2, style: "${style}")]
testView.draw(testView.bounds)
let testPixels = testContext.data!.assumingMemoryBound(to: UInt8.self)
var cyanPixels = 0
for index in stride(from: 0, to: testWidth * testHeight * 4, by: 4) {
    if testPixels[index] < 160 && testPixels[index + 1] > 150 && testPixels[index + 2] > 180 { cyanPixels += 1 }
}
print(cyanPixels)
`;
    const sourcePath = join(directory, 'main.swift');
    const executable = join(directory, 'native-probe');
    await writeFile(sourcePath, overlay + probe);
    await run('swiftc', ['-swift-version', '5', '-framework', 'Cocoa', sourcePath, '-o', executable]);
    const { stdout } = await run(executable);
    assert.ok(Number(stdout.trim()) > 500, `native ${style} attack has no substantial cyan core: ${stdout}`);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
