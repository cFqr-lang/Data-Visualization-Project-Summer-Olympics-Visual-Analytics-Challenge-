/** 报告图资产导出页：?chart=A1&renderer=canvas|svg&theme=print|dark */
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import { barOption, slopeOption } from './charts/a1';
import { indexOption, raceOption } from './charts/a2';
import { buildOption as b1Option } from './charts/b1';
import { buildOption as b2Option } from './charts/b2';
import { buildOption as c1Option } from './charts/c1';
import { buildOption as c2Option } from './charts/c2';
import { countOption, lifelineOption } from './charts/d1';
import { buildOption as d2Option } from './charts/d2';
import type {
  A1Payload, A2Payload, B1Payload, B2Payload, C1Payload, C2Payload, D1Payload, D2Payload,
} from './types';

interface PanelCfg {
  x: number;
  y: number;
  w: number;
  h: number;
  build: (payload: any) => EChartsOption;
}

interface ChartCfg {
  file: string;
  panels: PanelCfg[];
}

const CHARTS: Record<string, ChartCfg> = {
  A1: {
    file: 'fig-A1.json',
    panels: [
      { x: 0, y: 0, w: 900, h: 620, build: (payload: A1Payload) => barOption(payload) },
      { x: 920, y: 0, w: 520, h: 620, build: (payload: A1Payload) => slopeOption(payload) },
    ],
  },
  A2: {
    file: 'fig-A2.json',
    panels: [
      { x: 0, y: 0, w: 720, h: 480, build: (payload: A2Payload) => indexOption(payload) },
      { x: 740, y: 0, w: 720, h: 480, build: (payload: A2Payload) => raceOption(payload) },
    ],
  },
  B1: {
    file: 'fig-B1.json',
    panels: [{ x: 0, y: 0, w: 1180, h: 820, build: (payload: B1Payload) => b1Option(payload) }],
  },
  B2: {
    file: 'fig-B2.json',
    panels: [{ x: 0, y: 0, w: 1000, h: 560, build: (payload: B2Payload) => b2Option(payload) }],
  },
  C1: {
    file: 'fig-C1.json',
    panels: [{ x: 0, y: 0, w: 1000, h: 560, build: (payload: C1Payload) => c1Option(payload) }],
  },
  C2: {
    file: 'fig-C2.json',
    panels: [{ x: 0, y: 0, w: 1000, h: 600, build: (payload: C2Payload) => c2Option(payload.views[0]) }],
  },
  D1: {
    file: 'fig-D1.json',
    panels: [
      { x: 0, y: 0, w: 1000, h: 220, build: (payload: D1Payload) => countOption(payload) },
      { x: 0, y: 240, w: 1000, h: 940, build: (payload: D1Payload) => lifelineOption(payload) },
    ],
  },
  D2: {
    file: 'fig-D2.json',
    panels: [{ x: 0, y: 0, w: 1000, h: 560, build: (payload: D2Payload) => d2Option(payload) }],
  },
};

const COLOR_MAP: Record<string, string> = {
  '#e6efe9': '#12211C',
  '#8aa79a': '#5F6F68',
  '#1e3a2f': '#D9D4C7',
  '#16281f': '#E5E0D2',
  '#0f201a': '#FFFFFF',
  '#08130f': '#FBFAF6',
};

function remap(node: any): any {
  if (typeof node === 'string') return COLOR_MAP[node] ?? node;
  if (Array.isArray(node)) return node.map(remap);
  if (node && typeof node === 'object') {
    const out: Record<string, any> = {};
    Object.entries(node).forEach(([key, value]) => {
      out[key] = typeof value === 'function' ? value : remap(value);
    });
    return out;
  }
  return node;
}

function query(name: string, fallback: string): string {
  return new URLSearchParams(location.search).get(name) ?? fallback;
}

async function boot(): Promise<void> {
  const chartId = query('chart', 'A1').toUpperCase();
  const renderer = query('renderer', 'canvas') === 'svg' ? 'svg' : 'canvas';
  const theme = query('theme', 'print');
  const cfg = CHARTS[chartId];
  if (!cfg) throw new Error(`未知图号：${chartId}`);

  const res = await fetch(`./data/figures/${cfg.file}`);
  const payload = await res.json();
  const print = theme === 'print';
  const bg = print ? '#FBFAF6' : '#08130f';
  const ink = print ? '#12211C' : '#e6efe9';
  const muted = print ? '#5F6F68' : '#8aa79a';

  const pad = 28;
  const top = 70;
  const footer = 38;
  const width = Math.max(...cfg.panels.map((panel) => panel.x + panel.w)) + pad * 2;
  const height = Math.max(...cfg.panels.map((panel) => panel.y + panel.h)) + top + footer;

  const stage = document.getElementById('stage') as HTMLElement;
  stage.style.width = `${width}px`;
  stage.style.height = `${height}px`;
  stage.style.background = bg;

  const title = document.createElement('div');
  title.style.cssText = [
    'position:absolute', 'left:28px', 'top:18px',
    `color:${ink}`, 'font-family:"Noto Serif SC","Songti SC",serif',
    'font-size:22px', 'font-weight:700', 'letter-spacing:.02em',
  ].join(';');
  title.textContent = `${payload.meta.figure_id} · ${payload.meta.title}`;
  stage.appendChild(title);

  const sub = document.createElement('div');
  sub.style.cssText = [
    'position:absolute', `right:28px`, 'top:28px',
    `color:${muted}`, 'font-family:Inter,"Microsoft YaHei",sans-serif',
    'font-size:11px', 'text-align:right',
  ].join(';');
  sub.textContent = `${payload.meta.caliber_label} · 不含 1906`;
  stage.appendChild(sub);

  const note = document.createElement('div');
  note.style.cssText = [
    'position:absolute', 'left:28px', `bottom:12px`,
    `color:${muted}`, 'font-family:Inter,"Microsoft YaHei",sans-serif',
    'font-size:10px',
  ].join(';');
  note.textContent =
    `来源 data/raw/olympics_dataset.csv · 数据 ${payload.meta.data_version} · 生成 ${payload.meta.generated_at.slice(0, 10)} · Apache ECharts`;
  stage.appendChild(note);

  const panelEls: HTMLElement[] = [];
  const positions: { x: number; y: number; w: number; h: number }[] = [];
  cfg.panels.forEach((panel, panelIndex) => {
    const el = document.createElement('div');
    el.className = 'panel';
    el.style.left = `${panel.x + pad}px`;
    el.style.top = `${panel.y + top}px`;
    el.style.width = `${panel.w}px`;
    el.style.height = `${panel.h}px`;
    stage.appendChild(el);
    panelEls.push(el);
    positions.push({ x: panel.x + pad, y: panel.y + top, w: panel.w, h: panel.h });

    const option = remap(panel.build(payload));
    if (chartId === 'A2' && panelIndex === 1) {
      const base = (option as any).baseOption;
      if (base?.timeline) {
        base.timeline.autoPlay = false;
        base.timeline.currentIndex = base.timeline.data.length - 1;
      }
    }
    option.backgroundColor = 'transparent';
    const chart = echarts.init(el, undefined, { renderer });
    chart.setOption(option);
  });

  (window as unknown as Record<string, unknown>).__exportSvg = (): string => {
    const inner = panelEls
      .map((el, index) => {
        const svg = el.querySelector('svg');
        if (!svg) return '';
        const pos = positions[index];
        return `<g transform="translate(${pos.x},${pos.y})">${svg.outerHTML}</g>`;
      })
      .join('');
    return [
      `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
      `<rect width="100%" height="100%" fill="${bg}"/>`,
      `<text x="28" y="40" fill="${ink}" font-size="22" font-family="Noto Serif SC, Songti SC, serif" font-weight="700">${payload.meta.figure_id} · ${payload.meta.title}</text>`,
      `<text x="28" y="${height - 14}" fill="${muted}" font-size="10" font-family="Inter, Microsoft YaHei, sans-serif">来源 data/raw/olympics_dataset.csv · 数据 ${payload.meta.data_version} · Apache ECharts</text>`,
      inner,
      '</svg>',
    ].join('');
  };

  (window as unknown as Record<string, unknown>).__exportWidth = width;
  (window as unknown as Record<string, unknown>).__exportHeight = height;

  await new Promise((resolve) => setTimeout(resolve, 1400));
  (window as unknown as Record<string, unknown>).__exportReady = true;
}

void boot().catch((error) => {
  document.body.insertAdjacentHTML('beforeend', `<pre style="color:#c00">${String(error)}</pre>`);
  (window as unknown as Record<string, unknown>).__exportError = String(error);
});
