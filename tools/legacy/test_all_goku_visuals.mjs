import { chromium } from "playwright";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { readFile, mkdir } from "node:fs/promises";

const run = promisify(execFile);

async function main() {
  await mkdir("/tmp/goku_visual_checks", { recursive: true });
  await run("python3", ["Tools/make_pet_html.py", "web/bitling.html", "/tmp/goku_visual_checks/pet.html"]);
  let html = await readFile("/tmp/goku_visual_checks/pet.html", "utf8");

  html = html.replace(
    '  // ---------------------------------------------------------------- boot',
    `window.__gokuTest = { pet, state, draw, drawGoku, ctx, canvas, gokuState };
  // ---------------------------------------------------------------- boot`
  );

  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || "chrome" });
  const page = await browser.newPage({ viewport: { width: 400, height: 400 }, deviceScaleFactor: 2 });

  await page.addInitScript(() => {
    window.requestAnimationFrame = () => 0;
    window.__hostMessages = [];
    window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
    window.__petSavedState = JSON.stringify({ species: "goku", hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
  });

  await page.route("**/*", route => route.request().url() === "http://bitling.test/"
    ? route.fulfill({ contentType: "text/html", body: html }) : route.abort());

  await page.goto("http://bitling.test/");

  const forms = [
    { name: "0_kid", commits: 0 },
    { name: "1_base", commits: 3 },
    { name: "2_ssj", commits: 7 },
    { name: "3_ssj2", commits: 14 },
    { name: "4_ssj3", commits: 25 },
    { name: "5_ui", commits: 41 }
  ];

  const actions = [
    { name: "idle", patch: {} },
    { name: "kame_charge", patch: { zapCharge: 0.8, zapFull: 1, zapBoss: true, zapStyle: "kamehameha" } },
    { name: "kame_fire", patch: { zap: 0.2, zapBoss: true, zapStyle: "kamehameha" } },
    { name: "kiblast", patch: { zap: 0.15, zapBoss: false, zapStyle: "kiball" } }
  ];

  for (const f of forms) {
    for (const a of actions) {
      await page.evaluate(({ commits, patch }) => {
        window.petNative.gokuSimulate(commits);
        const api = window.__gokuTest;
        api.gokuState.transformFlash = 0;
        Object.assign(api.pet, { x: 200, y: 260, mode: "fly", grounded: false, facing: 1, walking: false, zapCharge: 0, zap: 0 }, patch);
        api.ctx.clearRect(0, 0, 400, 400);
        api.drawGoku();
      }, { commits: f.commits, patch: a.patch });

      await page.screenshot({ path: `/tmp/goku_visual_checks/${f.name}_${a.name}.png` });
      console.log(`Saved: ${f.name}_${a.name}.png`);
    }
  }

  await browser.close();
  console.log("All visual checks successfully captured!");
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
