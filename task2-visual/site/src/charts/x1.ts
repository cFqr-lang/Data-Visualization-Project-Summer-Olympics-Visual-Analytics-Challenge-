import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { X1Payload } from '../types';
import { INK, LINE, TEXT, TOOLTIP } from '../theme';

export function buildOption(payload: X1Payload): EChartsOption {
  const nocs = payload.nocs.map((item) => item.noc);
  const sports = payload.sports.map((item) => item.sport);
  const xIndex = new Map(sports.map((sport, index) => [sport, index]));
  const yIndex = new Map(nocs.map((noc, index) => [noc, index]));

  const data = payload.cells.map((cell) => ({
    value: [xIndex.get(cell.sport) ?? 0, yIndex.get(cell.noc) ?? 0, cell.lift, cell.medals],
    noc: cell.noc,
    sport: cell.sport,
    medals: cell.medals,
    lift: cell.lift,
  }));

  return {
    backgroundColor: 'transparent',
    animationDuration: 600,
    grid: { left: 58, right: 26, top: 18, bottom: 104 },
    tooltip: {
      ...TOOLTIP,
      formatter: (params: any) => {
        const row = params.data as { noc: string; sport: string; medals: number; lift: number };
        return [
          `<strong>${row.noc} × ${row.sport}</strong>`,
          `保守小项奖牌 ${row.medals} 枚`,
          `lift <strong>${row.lift.toFixed(2)}</strong>`,
          row.lift > 1 ? '高于全局结构，属于相对专长' : '低于全局结构或未获奖牌',
        ].join('<br/>');
      },
    },
    xAxis: {
      type: 'category',
      data: sports,
      splitArea: { show: false },
      axisLine: { lineStyle: { color: LINE } },
      axisTick: { show: false },
      axisLabel: { color: INK, fontSize: 10, interval: 0, rotate: 32, margin: 10 },
    },
    yAxis: {
      type: 'category',
      data: nocs,
      inverse: true,
      splitArea: { show: false },
      axisLine: { lineStyle: { color: LINE } },
      axisTick: { show: false },
      axisLabel: { color: TEXT, fontSize: 11 },
    },
    visualMap: {
      min: 0,
      max: payload.max_lift,
      dimension: 2,
      orient: 'horizontal',
      left: 'center',
      bottom: 2,
      itemWidth: 12,
      itemHeight: 110,
      calculable: false,
      text: [`高 ${payload.max_lift}`, '低 0'],
      textStyle: { color: INK, fontSize: 10 },
      inRange: { color: ['#142a22', '#265a49', '#4fd1a5', '#d8a838'] },
    },
    series: [
      {
        name: 'lift',
        type: 'heatmap',
        data,
        itemStyle: { borderColor: '#08130f', borderWidth: 2, borderRadius: 3 },
        label: {
          show: true,
          color: '#12211C',
          fontSize: 10,
          fontWeight: 600,
          formatter: (params: any) => {
            const value = params.value as number[];
            return value[2] >= 1.5 ? value[2].toFixed(1) : '';
          },
        },
        emphasis: {
          itemStyle: { borderColor: '#e6efe9', borderWidth: 2 },
        },
      },
    ],
  };
}

export function renderX1(el: HTMLElement, payload: X1Payload) {
  const chart = echarts.init(el);
  chart.setOption(buildOption(payload));
  const observer = new ResizeObserver(() => chart.resize());
  observer.observe(el);
  return chart;
}
