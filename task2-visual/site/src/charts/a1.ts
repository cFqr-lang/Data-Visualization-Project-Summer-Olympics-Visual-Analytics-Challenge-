import * as echarts from 'echarts';
import type { BarSeriesOption, EChartsOption } from 'echarts';
import type { A1Payload } from '../types';
import { GOLD, INK, LINE, SILVER, TEXT } from '../theme';

const SHORT_LABEL: Record<string, string> = {
  athlete_row_1906: '行口径\n含 1906',
  athlete_row: '行口径\n不含 1906',
  conservative_event: '保守小项\n不含 1906',
  loose_event: '宽松小项\n不含 1906',
};

const NOC_COLOR: Record<string, string> = {
  USA: '#4fd1a5', URS: '#6fa8ff', GBR: '#c77dff', GER: '#f2cc8f',
  FRA: '#e07a5f', ITA: '#8ab17d', CHN: '#ff9f1c', AUS: '#9ad1d4',
  HUN: '#b7c2c8', SWE: '#7d8cff', JPN: '#ef7a8b', KOR: '#a3d977',
};

function colorOf(noc: string, index: number): string {
  return NOC_COLOR[noc] ?? ['#4fd1a5', '#d8a838', '#6fa8ff', '#e07a5f'][index % 4];
}

export function barOption(payload: A1Payload): EChartsOption {
  const items = [...payload.totals_top20].reverse();
  const nocs = items.map((item) => item.noc);
  const lookup = new Map(items.map((item) => [item.noc, item]));

  const stack = (
    name: string, key: 'gold' | 'silver' | 'bronze', color: string
  ): BarSeriesOption => ({
    name,
    type: 'bar',
    stack: 'medal',
    barWidth: '60%',
    itemStyle: { color },
    emphasis: { focus: 'series' },
    data: items.map((item) => item[key]),
  });

  const bronze = stack('铜牌', 'bronze', '#b1743f');
  bronze.label = {
    show: true,
    position: 'right',
    color: TEXT,
    fontSize: 11,
    formatter: (params: any) => {
      const row = lookup.get(nocs[params.dataIndex]);
      return row ? String(row.total) : '';
    },
  };

  return {
    backgroundColor: 'transparent',
    animationDuration: 700,
    grid: { left: 52, right: 62, top: 44, bottom: 30 },
    legend: {
      top: 0, right: 4, itemWidth: 10, itemHeight: 10,
      textStyle: { color: INK, fontSize: 11 },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(95,111,104,0.07)' } },
      backgroundColor: '#FFFFFF',
      borderColor: LINE,
      textStyle: { color: TEXT, fontSize: 12 },
      formatter: (params: any) => {
        const list = params as { name: string; dataIndex: number; marker: string }[];
        const row = lookup.get(list[0].name);
        if (!row) return '';
        return [
          `<strong>${row.noc}</strong>`,
          `金牌 ${row.gold} · 银牌 ${row.silver} · 铜牌 ${row.bronze}`,
          `去重奖牌 <strong>${row.total}</strong>（排名 ${row.rank}）`,
          `运动员行 ${row.athlete_medal_rows}（团体膨胀 +${row.diff}）`,
        ].join('<br/>');
      },
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: INK, fontSize: 11 },
      splitLine: { lineStyle: { color: LINE, type: 'dashed' } },
      axisLine: { show: false },
    },
    yAxis: {
      type: 'category',
      data: nocs,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: LINE } },
      axisLabel: { color: TEXT, fontSize: 12 },
    },
    series: [stack('金牌', 'gold', GOLD), stack('银牌', 'silver', SILVER), bronze],
  };
}

export function slopeOption(payload: A1Payload): EChartsOption {
  const defs = payload.definitions;
  const xLabels = defs.map((def) => SHORT_LABEL[def.id] ?? def.label);
  const lookups = defs.map(
    (def) => new Map(def.ranking.map((row) => [row.noc, row.rank]))
  );
  const candidates = payload.totals_top20.slice(0, 12).map((row) => row.noc);
  const nocs = candidates.filter((noc) => lookups.every((map) => map.has(noc)));

  const series = nocs.map((noc, index) => {
    const color = colorOf(noc, index);
    const strong = noc === 'CHN';
    return {
      name: noc,
      type: 'line' as const,
      data: lookups.map((map) => map.get(noc) ?? null),
      symbol: 'circle',
      symbolSize: strong ? 9 : 7,
      lineStyle: { width: strong ? 3 : 1.6, color },
      itemStyle: { color },
      z: strong ? 10 : 2,
      label: {
        show: true,
        position: 'top' as const,
        color: INK,
        fontSize: 10,
        formatter: (params: any) => (params.value ? String(params.value) : ''),
      },
      endLabel: {
        show: true,
        formatter: '{a}',
        color,
        fontSize: 11,
        distance: 6,
      },
      emphasis: { focus: 'series' as const },
    };
  });

  const maxRank = nocs.length
    ? Math.max(...nocs.map((noc) => Math.max(...lookups.map((map) => map.get(noc) ?? 0))))
    : 12;

  return {
    backgroundColor: 'transparent',
    animationDuration: 800,
    grid: { left: 46, right: 58, top: 34, bottom: 62 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: LINE,
      textStyle: { color: TEXT, fontSize: 12 },
      formatter: (params: any) => {
        const list = params as { seriesName: string; value: number | null; marker: string }[];
        return list
          .filter((item) => item.value)
          .sort((a, b) => (a.value ?? 99) - (b.value ?? 99))
          .map((item) => `${item.marker}${item.seriesName} 第 ${item.value} 位`)
          .join('<br/>');
      },
    },
    xAxis: {
      type: 'category',
      data: xLabels,
      boundaryGap: true,
      axisLine: { lineStyle: { color: LINE } },
      axisTick: { show: false },
      axisLabel: { color: INK, fontSize: 11, lineHeight: 15, interval: 0 },
    },
    yAxis: {
      type: 'value',
      inverse: true,
      min: 1,
      max: maxRank,
      interval: 1,
      name: '排名',
      nameTextStyle: { color: INK, fontSize: 11, padding: [0, 0, 0, -28] },
      axisLabel: { color: INK, fontSize: 11, formatter: '{value}' },
      splitLine: { lineStyle: { color: LINE, type: 'dashed' } },
      axisLine: { show: false },
    },
    series,
  };
}

export function renderA1(barEl: HTMLElement, slopeEl: HTMLElement, payload: A1Payload) {
  const bar = echarts.init(barEl, undefined, { renderer: 'canvas' });
  const slope = echarts.init(slopeEl, undefined, { renderer: 'canvas' });
  bar.setOption(barOption(payload));
  slope.setOption(slopeOption(payload));

  const observer = new ResizeObserver(() => {
    bar.resize();
    slope.resize();
  });
  observer.observe(barEl);
  observer.observe(slopeEl);
  return { bar, slope };
}
