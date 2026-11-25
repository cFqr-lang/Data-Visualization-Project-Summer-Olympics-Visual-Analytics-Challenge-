/** 构建离线单文件包：读取 dist 与 public/data，内联 JS/CSS/JSON。
 *  用法：npm run build:offline
 */
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../..');
const dist = resolve(root, 'site/dist');
const dataDir = resolve(root, 'site/public/data');
const outDir = resolve(root, 'offline');

async function collectData() {
  const map = {};
  // data 目录下的所有顶层 JSON（meta.json、index.json 等），新增文件不会被漏掉
  const tops = await readdir(dataDir);
  for (const file of tops.filter((name) => name.endsWith('.json'))) {
    const raw = await readFile(resolve(dataDir, file), 'utf8');
    map[`./data/${file}`] = JSON.parse(raw);
  }
  const figures = await readdir(resolve(dataDir, 'figures'));
  for (const file of figures.filter((name) => name.endsWith('.json'))) {
    const raw = await readFile(resolve(dataDir, 'figures', file), 'utf8');
    map[`./data/figures/${file}`] = JSON.parse(raw);
  }
  return map;
}

async function main() {
  const html = await readFile(resolve(dist, 'index.html'), 'utf8');
  const scriptTag = /<script[^>]*src="([^"]+\.js)"[^>]*><\/script>/.exec(html);
  const styleTag = /<link[^>]*href="([^"]+\.css)"[^>]*>/.exec(html);
  if (!scriptTag || !styleTag) throw new Error('dist/index.html 未找到 JS/CSS 入口');

  const js = await readFile(resolve(dist, scriptTag[1].replace('./', '')), 'utf8');
  const css = await readFile(resolve(dist, styleTag[1].replace('./', '')), 'utf8');
  const data = await collectData();

  let out = html.replace(styleTag[0], () => `<style>${css}</style>`);
  const dataJson = JSON.stringify(data).replace(/<\/script/gi, '<\\/script');
  out = out.replace(
    scriptTag[0],
    () => `<script>window.__OLYMPICS_DATA__=${dataJson};</script>\n<script type="module">${js}</script>`
  );

  await mkdir(outDir, { recursive: true });
  const target = resolve(outDir, 'olympics-story.offline.html');
  await writeFile(target, out, 'utf8');
  const mb = Buffer.byteLength(out) / 1024 / 1024;
  console.log(`[OK] ${target} ${mb.toFixed(2)} MB`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
