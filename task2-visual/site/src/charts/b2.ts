import * as echarts from 'echarts';
import type { EChartsOption, ScatterSeriesOption } from 'echarts';
import type { B2Payload } from '../types';
import { ACCENT, AXIS_LABEL, GOLD, INK, LINE, SPLIT_LINE, TEXT, TOOLTIP } from '../theme';

const FOCUS = new Set([
  'USA', 'URS', 'CHN', 'GBR', 'AUS', 'NED', 'JAM', 'KEN', 'NZL', 'BAH', 'HKG', 'CUB',
]);

export function buildOption(payload: B2Payload): EChartsOption {
  const data = payload.points.map((point) => ({
    value: [point.avg_athletes, point.avg_medals, point.editions],
    noc: point.noc,
    itemStyle: {
      color: point.efficiency >= 0.12 ? GOLD : ACCENT,
      opacity: 0.82,
    },
    label: FOCUS.has(point.noc)
      ? { show: true, formatter: point.noc, position: 'top' as const, color: TEXT, fontSize: 10 }
      : { show: false },
  }));

  const series: ScatterSeriesOption = {
    name: '国家',
    type: 'scatter',
    symbolSize: (value: number[]) => Math.max(6, Math.min(26, 5 + value[2] * 0.55)),
    data,
    labelLayout: { hideOverlap: true },
    emphasis: {
      focus: 'self',
      itemStyle: { borderColor: '#12211C', borderWidth: 1.5 },
    },
  };

  return {
    backgroundColor: 'transparent',
    animationDuration: 700,
    grid: { left: 68, right: 28, top: 30, bottom: 58 },
    tooltip: {
      ...TOOLTIP,
      formatter: (params: any) => {
        const item = params as { data: { noc: string; value: [number, number, number] } };
        const point = payload.points.find((row) => row.noc === item.data.noc);
        if (!point) return '';
        return [
          `<strong>${point.noc}</strong> · 场均奖牌第 ${point.rank} 位`,
          `场均参赛 ${point.avg_athletes} 人 · 场均奖牌 ${point.avg_medals} 枚`,
          `参赛 ${point.editions} 届 · 累计 ${point.total_medals} 枚`,
          `效率 ${(point.efficiency * 100).toFixed(1)} 枚 / 百人`,
        ].join('<br/>');
      },
    },
    xAxis: {
      type: 'log',
      min: 2,
      max: 800,
      name: '场均参赛人数（去重运动员，log）',
      nameLocation: 'middle',
      nameGap: 34,
      nameTextStyle: { color: INK, fontSize: 11 },
      axisLabel: AXIS_LABEL,
      splitLine: SPLIT_LINE,
      axisLine: { lineStyle: { color: LINE } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'log',
      min: 0.2,
      max: 200,
      name: '场均奖牌（log）',
      nameTextStyle: { color: INK, fontSize: 11, padding: [0, 0, 4, 0] },
      axisLabel: AXIS_LABEL,
      splitLine: SPLIT_LINE,
      axisLine: { show: false },
    },
    series: [series],
  };
}

export function renderB2(el: HTMLElement, payload: B2Payload) {
  const chart = echarts.init(el);
  chart.setOption(buildOption(payload));
  const observer = new ResizeObserver(() => chart.resize());
  observer.observe(el);
  return chart;
}
