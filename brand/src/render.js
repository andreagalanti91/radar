// Genera i PNG del brand da brand/src/brand.html e brand/icon.svg.  Uso: node brand/src/render.js
const { chromium } = require("playwright");
const path = require("path");
const SRC = "file://" + path.join(__dirname, "brand.html");
const OUT = path.join(__dirname, "..");
// [vista, file, larghezza, altezza, deviceScaleFactor]
const JOBS = [
  ["banner", "banner.png", 1280, 640, 1],
  ["social", "social-preview.png", 1280, 640, 1],
  ["logoLight", "logo-light.png", 1200, 400, 1],
  ["logoDark", "logo-dark.png", 1200, 400, 1],
  ["board", "brand-board.png", 1600, 1000, 1],
  ["varianti", "src/varianti.png", 1500, 610, 1],
  ["icon", "icon-1024.png", 1024, 1024, 1],
  ["icon", "icon-512.png", 1024, 1024, .5],
  ["icon", "icon-192.png", 1024, 1024, .1875],
  ["icon", "apple-touch-icon.png", 1024, 1024, 180 / 1024],
];
(async () => {
  const b = await chromium.launch();
  for (const [view, file, w, h, dpr] of JOBS) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: dpr });
    await p.goto(`${SRC}#${view}`);
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(300);
    await p.screenshot({ path: path.join(OUT, file), clip: { x: 0, y: 0, width: w, height: h }, omitBackground: true });
    await p.close(); console.log(file);
  }
  // favicon: icon.svg (segno al 72%, correzione ottica per 16-32 px) con angoli arrotondati e trasparenza
  const p = await b.newPage({ viewport: { width: 32, height: 32 } });
  await p.goto("file://" + path.join(OUT, "icon.svg"));
  await p.waitForTimeout(200);
  await p.screenshot({ path: path.join(OUT, "favicon-32.png"), omitBackground: true });
  console.log("favicon-32.png");
  await b.close();
})();
