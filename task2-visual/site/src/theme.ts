/** 「成绩册」浅色站点统一视觉 token 与 ECharts 片段。
 *  色板与导出图 print 主题一致：纸底 #FBFAF6 / 墨色 #12211C / 细线 #D9D4C7。
 */
export const INK = '#5F6F68';      // 轴标签、图例等次级文字
export const LINE = '#D9D4C7';     // 主细线（同站点 --line）
export const LINE_SOFT = '#E9E5DA';
export const TEXT = '#12211C';     // 主文字（同站点 --ink）
export const GOLD = '#d8a838';
export const SILVER = '#b7c2c8';
export const BRONZE = '#b1743f';
export const ACCENT = '#4fd1a5';
export const FLAME = '#e07a5f';
export const PANEL = '#FFFFFF';    // 提示框底

export const NOC_COLOR: Record<string, string> = {
  USA: '#4fd1a5', URS: '#6fa8ff', GBR: '#c77dff', GER: '#f2cc8f',
  FRA: '#e07a5f', ITA: '#8ab17d', CHN: '#ff9f1c', AUS: '#9ad1d4',
  HUN: '#b7c2c8', SWE: '#7d8cff', JPN: '#ef7a8b', KOR: '#a3d977',
  RUS: '#6fa8ff', EUN: '#8ecbff', ROC: '#7d8cff', AIN: '#9aa7ff',
  FRG: '#f2cc8f', GDR: '#d8a838', NED: '#ffb703', CAN: '#f4845f',
  CUB: '#c9ada7', BRA: '#8ecae6', NZL: '#b5e48c', KEN: '#f4a261',
  JAM: '#ffd166', IND: '#f2cc8f', ESP: '#e76f51', SUI: '#90be6d',
  DEN: '#a8dadc', NOR: '#cfe1b9', FIN: '#8ecae6', POL: '#ffafcc',
  TUR: '#cdb4db', IRI: '#f6bd60', UKR: '#90dbf4', GRE: '#f9c74f',
  ROU: '#f9844a', BUL: '#b8c0ff', CZE: '#a3d977', BEL: '#84a59d',
  ARG: '#82c0cc', MEX: '#f6bd60', RSA: '#b5e48c', ETH: '#f4a261',
  BAH: '#90dbf4', HKG: '#ffd166', POR: '#a8dadc', CRO: '#f28482',
};

const FALLBACK = [ACCENT, GOLD, '#6fa8ff', FLAME, '#c77dff', '#9ad1d4', '#f2cc8f', '#ef7a8b'];

export function nocColor(noc: string): string {
  if (NOC_COLOR[noc]) return NOC_COLOR[noc];
  let hash = 0;
  for (let i = 0; i < noc.length; i += 1) hash = (hash * 31 + noc.charCodeAt(i)) % 9973;
  return FALLBACK[hash % FALLBACK.length];
}

export const TOOLTIP = {
  backgroundColor: PANEL,
  borderColor: LINE,
  borderWidth: 1,
  textStyle: { color: TEXT, fontSize: 12 },
  extraCssText: 'box-shadow:0 4px 18px rgba(31,42,37,.10);border-radius:6px;',
} as const;

export const AXIS_LABEL = { color: INK, fontSize: 11 } as const;

export const SPLIT_LINE = { lineStyle: { color: LINE, type: 'dashed' as const } };

export const SOURCE_NOTE = '数据 v1.0-fallback · 仅使用赛题数据集 · 图表 Apache ECharts';
