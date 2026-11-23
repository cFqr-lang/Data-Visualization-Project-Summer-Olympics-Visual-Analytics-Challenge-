/** 深色站点统一视觉 token 与 ECharts 片段。 */
export const INK = '#8aa79a';
export const LINE = '#1e3a2f';
export const LINE_SOFT = '#16281f';
export const TEXT = '#e6efe9';
export const GOLD = '#d8a838';
export const SILVER = '#b7c2c8';
export const BRONZE = '#b1743f';
export const ACCENT = '#4fd1a5';
export const FLAME = '#e07a5f';
export const PANEL = '#0f201a';

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
  extraCssText: 'box-shadow:0 8px 24px rgba(0,0,0,.35);border-radius:8px;',
} as const;

export const AXIS_LABEL = { color: INK, fontSize: 11 } as const;

export const SPLIT_LINE = { lineStyle: { color: LINE, type: 'dashed' as const } };

export const SOURCE_NOTE = '数据 v1.0-fallback · 仅使用赛题数据集 · 图表 Apache ECharts';
