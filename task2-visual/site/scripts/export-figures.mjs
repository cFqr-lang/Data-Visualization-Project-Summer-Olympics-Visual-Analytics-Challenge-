/** 从运行中的 Vite 站点导出 10 幅图的 PNG@4x 与 SVG。
 *  用法：先 npm run dev，再 npm run export:figures
 */
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../..');
const base = process.env.EXPORT_BASE_URL ?? 'http://localhost:5273';

const EDGE = process.env.EDGE_PATH
  ?? 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

const FIGURES = [
  ['A1', 'Fig2-1_A1_dual-caliber'],
  ['A2', 'Fig2-2_A2_medal-race'],
  ['B1', 'Fig2-3_B1_nine-nations'],
  ['C1', 'Fig2-4_C1_women-arc'],
  ['C2', 'Fig2-5_C2_participation-output'],
  ['D1', 'Fig2-6_D1_sport-lifeline'],
  ['B2', 'Fig2-7_B2_efficiency-frontier'],
  ['D2', 'Fig2-8_D2_structure-river'],
  ['X1', 'Fig2-9_X1_strength-matrix'],
  ['X2', 'Fig2-10_X2_gender-gap'],
];

async function main() {
  const pngDir = resolve(root, 'exports/png');
  const svgDir = resolve(root, 'exports/svg');
  await mkdir(pngDir, { recursive: true });
  await mkdir(svgDir, { recursive: true });

  const only = process.argv.slice(2).map((item) => item.toUpperCase());
  const figures = only.length ? FIGURES.filter(([chart]) => only.includes(chart)) : FIGURES;

  const browser = await puppeteer.launch({
    executablePath: EDGE,
    headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--force-device-scale-factor=4'],
  });

  try {
    for (const [chart, name] of figures) {
      const page = await browser.newPage();
      await page.setViewport({ width: 1800, height: 1600, deviceScaleFactor: 4 });
      const url = `${base}/export.html?chart=${chart}&renderer=canvas&theme=print`;
      await page.goto(url, { waitUntil: 'networkidle0', timeout: 60000 });
      await page.waitForFunction('window.__exportReady === true', { timeout: 60000 });

      const stage = await page.$('#stage');
      if (!stage) throw new Error(`#stage 缺失：${chart}`);
      await stage.screenshot({ path: resolve(pngDir, `${name}_4x.png`) });

      await page.goto(`${base}/export.html?chart=${chart}&renderer=svg&theme=print`, {
        waitUntil: 'networkidle0',
        timeout: 60000,
      });
      await page.waitForFunction('window.__exportReady === true', { timeout: 60000 });
      const svg = await page.evaluate(() => window.__exportSvg());
      if (!svg) throw new Error(`SVG 生成失败：${chart}`);
      await writeFile(resolve(svgDir, `${name}.svg`), svg, 'utf8');

      const size = await page.evaluate(() => `${window.__exportWidth}x${window.__exportHeight}`);
      console.log(`[OK] ${chart} ${name} (${size})`);
      await page.close();
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
