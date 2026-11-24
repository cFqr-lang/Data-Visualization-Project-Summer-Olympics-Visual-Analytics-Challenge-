import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { D2Payload } from '../types';
import { INK, LINE, SPLIT_LINE, TEXT, TOOLTIP } from '../theme';

const COLOR: Record<string, string> = {
  Athletics: '#d8a838',
  Swimming: '#6fa8ff',
  Wrestling: '#c77dff',
  Gymnastics: '#4fd1a5',
  Boxing: '#e07a5f',
  Shooting: '#f2cc8f',
  Cycling: '#9ad1d4',
  Other: '#5c6f68',
};

export function buildOption(payload: D2Payload): EChartsOption {
  return {
    backgroundColor: 'transparent',
    animationDuration: 800,
    legend: {
      top: 0, right: 0, itemWidth: 12, itemHeight: 8,
      textStyle: { color: INK, fontSize: 11 },
      data: payload.categories,
    },
    tooltip: {
      ...TOOLTIP,
      trigger: 'item',
      formatter: (params: any) => {
        const [date, value, name] = params.data as [string, number, string];
        return `<strong>${name}</strong><br/>${date.slice(0, 4)} · 保守小项奖牌 ${value} 枚`;
      },
    },
    singleAxis: {
      type: 'time',
      top: 44,
      bottom: 44,
      left: 48,
      right: 28,
      axisLabel: { color: INK, fontSize: 10, formatter: '{yyyy}' },
      axisLine: { lineStyle: { color: LINE } },
      splitLine: SPLIT_LINE,
      axisPointer: { label: { backgroundColor: '#FFFFFF', color: TEXT } },
    },
    series: [
      {
        type: 'themeRiver',
        emphasis: { focus: 'series' as const },
        label: { show: false },
        itemStyle: {
          borderWidth: 0,
          color: (params: any) => COLOR[params.name] ?? '#5c6f68',
        },
        data: payload.river,
      },
    ],
  };
}

export function renderD2(el: HTMLElement, payload: D2Payload) {
  const chart = echarts.init(el);
  chart.setOption(buildOption(payload));
  const observer = new ResizeObserver(() => chart.resize());
  observer.observe(el);
  return chart;
}
