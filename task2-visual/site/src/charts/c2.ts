import * as echarts from 'echarts';
import type { EChartsOption, ScatterSeriesOption } from 'echarts';
import type { C2Payload, C2View } from '../types';
import { ACCENT, AXIS_LABEL, FLAME, INK, LINE, SPLIT_LINE, TEXT, TOOLTIP } from '../theme';

const FOCUS = new Set(['USA', 'CHN', 'NED', 'JAM', 'IND', 'AUS', 'GBR', 'JPN', 'FRA', 'KOR', 'ROU']);

function scatterData(view: C2View): NonNullable<ScatterSeriesOption['data']> {
  return view.points
    .filter((point) => point.female_medal_share !== null)
    .map((point) => {
      const x = Number((point.female_share * 100).toFixed(1));
      const y = Number(((point.female_medal_share ?? 0) * 100).toFixed(1));
      const above = y >= x;
      return {
        value: [x, y, point.rows],
        noc: point.noc,
        itemStyle: { color: above ? ACCENT : FLAME, opacity: 0.82 },
        label: FOCUS.has(point.noc)
          ? { show: true, formatter: point.noc, position: 'top' as const, color: TEXT, fontSize: 10 }
          : { show: false },
      };
    });
}

export function buildOption(view: C2View): EChartsOption {
  const data = scatterData(view);

  const series: ScatterSeriesOption = {
    name: view.label,
    type: 'scatter',
    symbolSize: (value: number[]) => Math.max(7, Math.min(30, Math.sqrt(value[2]) * 0.95)),
    data,
    emphasis: {
      focus: 'self',
      itemStyle: { borderColor: '#12211C', borderWidth: 1.5 },
    },
    markLine: {
      silent: true,
      symbol: 'none',
      lineStyle: { color: INK, type: 'dashed', width: 1.2, opacity: 0.8 },
      label: {
        show: true,
        position: 'end',
        formatter: 'y = x',
        color: INK,
        fontSize: 10,
      },
      data: [[{ coord: [0, 0] }, { coord: [100, 100] }]],
    },
    markArea: {
      silent: true,
      data: [
        [
          {
            name: '高参与 · 高产出',
            xAxis: 50,
            yAxis: 50,
            itemStyle: { color: 'rgba(79,209,165,0.055)' },
            label: { position: 'insideTopLeft', color: '#2E9E78', fontSize: 10 },
          },
          { xAxis: 100, yAxis: 100 },
        ],
        [
          {
            name: '低参与 · 高产出',
            xAxis: 0,
            yAxis: 50,
            itemStyle: { color: 'rgba(216,168,56,0.05)' },
            label: { position: 'insideTopLeft', color: '#8F6B14', fontSize: 10 },
          },
          { xAxis: 50, yAxis: 100 },
        ],
        [
          {
            name: '高参与 · 低产出',
            xAxis: 50,
            yAxis: 0,
            itemStyle: { color: 'rgba(224,122,95,0.06)' },
            label: { position: 'insideBottomLeft', color: '#B45538', fontSize: 10 },
          },
          { xAxis: 100, yAxis: 50 },
        ],
        [
          {
            name: '低参与 · 低产出',
            xAxis: 0,
            yAxis: 0,
            itemStyle: { color: 'rgba(95,111,104,0.03)' },
            label: { position: 'insideBottomLeft', color: 'rgba(95,111,104,0.8)', fontSize: 10 },
          },
          { xAxis: 50, yAxis: 50 },
        ],
      ],
    },
  };

  return {
    backgroundColor: 'transparent',
    animationDuration: 700,
    grid: { left: 58, right: 28, top: 28, bottom: 54 },
    tooltip: {
      ...TOOLTIP,
      formatter: (params: any) => {
        const item = params as { data: { noc: string; value: [number, number, number] } };
        const [x, y, rows] = item.data.value;
        const point = view.points.find((row) => row.noc === item.data.noc);
        if (!point) return '';
        const delta = y - x;
        const sign = delta >= 0 ? '+' : '';
        return [
          `<strong>${point.noc}</strong> · ${view.label}`,
          `女性参赛占比 ${x.toFixed(1)}%`,
          `女性奖牌占比 ${y.toFixed(1)}%（偏离 ${sign}${delta.toFixed(1)}pp）`,
          `参赛记录 ${point.rows.toLocaleString('zh-CN')} 行`,
          `女 ${point.female_medals} · 男 ${point.male_medals} · 混合 ${point.mixed_medals} 枚奖牌`,
        ].join('<br/>');
      },
    },
    xAxis: {
      type: 'value',
      min: 0,
      max: 100,
      name: '女性参赛记录占比（%）',
      nameLocation: 'middle',
      nameGap: 32,
      nameTextStyle: { color: INK, fontSize: 11 },
      axisLabel: { ...AXIS_LABEL, formatter: '{value}%' },
      splitLine: SPLIT_LINE,
      axisLine: { lineStyle: { color: LINE } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      name: '女性奖牌占比（%）',
      nameTextStyle: { color: INK, fontSize: 11, padding: [0, 0, 4, 0] },
      axisLabel: { ...AXIS_LABEL, formatter: '{value}%' },
      splitLine: SPLIT_LINE,
      axisLine: { show: false },
    },
    series: [series],
  };
}

export function renderC2(el: HTMLElement, payload: C2Payload) {
  const chart = echarts.init(el);
  let current = payload.views[0];

  chart.setOption(buildOption(current));

  const setView = (id: string) => {
    const view = payload.views.find((item) => item.id === id);
    if (!view) return;
    current = view;
    chart.setOption(buildOption(view), true);
  };

  const observer = new ResizeObserver(() => chart.resize());
  observer.observe(el);

  return { chart, setView, getView: () => current };
}
