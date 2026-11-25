// 由 report/report.html 生成 A4 PDF（含逐页溢出检测）
// 用法：cd task2-visual/site && node scripts/build-report-pdf.mjs
import puppeteer from 'puppeteer-core';

const EDGE = process.env.EDGE_PATH || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const SRC = 'file:///E:/资料/数据可视化课程/report/report.html';
const OUT_PDF = 'E:\\资料\\数据可视化课程\\report\\数说奥运_数据可视分析报告.pdf';

const browser = await puppeteer.launch({
  executablePath: EDGE,
  headless: true,
  args: ['--no-sandbox', '--disable-gpu'],
});
const page = await browser.newPage();
await page.setViewport({ width: 900, height: 1200, deviceScaleFactor: 1 });
await page.goto(SRC, { waitUntil: 'load', timeout: 30000 }).catch(() => {});
await new Promise((r) => setTimeout(r, 3000));

const info = await page.evaluate(() =>
  [...document.querySelectorAll('.page')].map((p) => ({
    n: p.dataset.page,
    over: p.scrollHeight - p.clientHeight,
  }))
);
const bad = info.filter((x) => x.over > 2);
console.log(`页面数: ${info.length}`);
console.log(bad.length ? `溢出页: ${JSON.stringify(bad)}` : '溢出: 无');

await page.pdf({
  path: OUT_PDF,
  printBackground: true,
  preferCSSPageSize: true,
  margin: { top: 0, right: 0, bottom: 0, left: 0 },
});
console.log(`PDF 已生成: ${OUT_PDF}`);
await browser.close();
