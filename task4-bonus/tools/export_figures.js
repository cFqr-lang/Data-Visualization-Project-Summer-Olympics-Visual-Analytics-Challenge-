/**
 * 用法（在任意目录执行）：
 *   python task4-bonus/tools/export_figures.py   # 先生成 tools/_figs/*.html
 *   npm install puppeteer-core
 *   node   task4-bonus/tools/export_figures.js
 *
 * 依赖本机 Edge / Chrome（脚本自动探测常见安装路径）。
 * 输出：task4-bonus/exports/png/<name>_4x.png 与 task4-bonus/exports/svg/<name>.svg
 */
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

const HERE = __dirname;
const TASK_DIR = path.dirname(HERE);
const HTML_DIR = path.join(HERE, '_figs');
const PNG_DIR = path.join(TASK_DIR, 'exports', 'png');
const SVG_DIR = path.join(TASK_DIR, 'exports', 'svg');

const FIGS = [
  ['Fig4-1_A1_dual-caliber', 1200, 420],
  ['Fig4-2_A2_top20', 1200, 600],
  ['Fig4-3_A3_inflation', 1200, 420],
  ['Fig4-4_B1_twelve-nations', 1200, 500],
  ['Fig4-5_B2_bloc-evolution', 1200, 400],
  ['Fig4-6_C1_female-ratio', 1200, 450],
  ['Fig4-7_C2_female-top15', 1200, 500],
  ['Fig4-8_D1_event-growth', 1200, 400],
  ['Fig4-9_D2_vanished-added', 1200, 500],
  ['Fig4-10_E1_host-pulse', 1400, 500],
  ['Fig4-11_E2_small-nocs', 1200, 550],
];

const CANDIDATES = [
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  '/usr/bin/google-chrome',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
];

function findBrowser() {
  const hit = CANDIDATES.find((p) => fs.existsSync(p));
  if (!hit) throw new Error('未找到 Edge/Chrome，请手动设置 executablePath');
  return hit;
}

(async () => {
  fs.mkdirSync(PNG_DIR, { recursive: true });
  fs.mkdirSync(SVG_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: process.env.BROWSER_PATH || findBrowser(),
    headless: true,
    args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files'],
  });

  for (const [name, w, h] of FIGS) {
    const page = await browser.newPage();
    await page.setViewport({ width: w, height: h, deviceScaleFactor: 4 });
    const url = 'file:///' + path.join(HTML_DIR, name + '.html').replace(/\\/g, '/');
    await page.goto(url, { waitUntil: 'load', timeout: 90000 });
    await page.waitForSelector('.main-svg', { timeout: 90000 });
    await new Promise((r) => setTimeout(r, 1000));

    await page.screenshot({
      path: path.join(PNG_DIR, name + '_4x.png'),
      clip: { x: 0, y: 0, width: w, height: h },
    });

    const dataUrl = await page.evaluate(async (ww, hh) => {
      const gd = document.querySelector('.js-plotly-plot');
      return await Plotly.toImage(gd, { format: 'svg', width: ww, height: hh });
    }, w, h);

    // 注意：SVG 的 data URI 是 URL-encoded，PNG 才是 base64
    const payload = dataUrl.slice(dataUrl.indexOf(',') + 1);
    const svg = dataUrl.includes('base64')
      ? Buffer.from(payload, 'base64').toString('utf8')
      : decodeURIComponent(payload);
    if (!svg.includes('<svg')) throw new Error(`${name}: SVG 解码失败`);

    fs.writeFileSync(path.join(SVG_DIR, name + '.svg'), svg, 'utf8');
    console.log(`  ${name}: png + svg`);
    await page.close();
  }

  await browser.close();
  console.log(`完成：${FIGS.length} 张图 -> ${PNG_DIR} / ${SVG_DIR}`);
})().catch((e) => {
  console.error('导出失败：', e && e.stack ? e.stack : e);
  process.exit(1);
});
