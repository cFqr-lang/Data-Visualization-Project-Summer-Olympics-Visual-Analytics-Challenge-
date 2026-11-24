import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { C1Payload } from '../types';
import { ACCENT, AXIS_LABEL, GOLD, INK, LINE, SPLIT_LINE, TEXT, TOOLTIP } from '../theme';

export function buildOption(payload: C1Payload): EChartsOption {
  const points = payload.series;
  const years = points.map((item) => String(item.year));
  const milestoneByYear = new Map(payload.milestones.map((item) => [item.year, item.text]));

  const markPoints = payload.milestones.map((item) => {
    const point = points.find((row) => row.year === item.year);
    return {
      name: item.text,
      coord: [String(item.year), Number(((point?.female_share ?? 0) * 100).toFixed(1))],
      value: item.text,
    };
  });

  return {
    backgroundColor: 'transparent',
    animationDuration: 800,
    legend: {
      top: 0, right: 0, itemWidth: 12, itemHeight: 8,
      textStyle: { color: INK, fontSize: 11 },
      data: ['男性参赛记录', '女性参赛记录', '女性占比'],
    },
    grid: [
      { left: 58, right: 66, top: 40, height: 206 },
      { left: 58, right: 66, top: 312, height: 132 },
    ],
    axisPointer: { link: [{ xAxisIndex: 'all' }], label: { backgroundColor: '#FFFFFF', color: TEXT } },
    tooltip: {
      ...TOOLTIP,
      trigger: 'axis',
      formatter: (params: any) => {
        const list = params as { seriesName: string; value: number; axisValue: string }[];
        if (!list.length) return '';
        const year = Number(list[0].axisValue);
        const row = points.find((item) => item.year === year);
        if (!row) return '';
        const milestone = milestoneByYear.get(year);
        return [
          `<strong>${year}</strong>${milestone ? ` · ${milestone}` : ''}`,
          `男性记录 ${row.male_rows.toLocaleString('zh-CN')} · 女性记录 ${row.female_rows.toLocaleString('zh-CN')}`,
          `女性占比 <strong>${(row.female_share * 100).toFixed(1)}%</strong>`,
          `有女性参赛的代表团 ${row.delegations_with_women} / ${row.delegations}`,
        ].join('<br/>');
      },
    },
    xAxis: [
      {
        type: 'category',
        gridIndex: 0,
        data: years,
        boundaryGap: false,
        axisLine: { lineStyle: { color: LINE } },
        axisTick: { show: false },
        axisLabel: { show: false },
      },
      {
        type: 'category',
        gridIndex: 1,
        data: years,
        boundaryGap: false,
        axisLine: { lineStyle: { color: LINE } },
        axisTick: { show: false },
        axisLabel: { ...AXIS_LABEL, interval: 4 },
      },
    ],
    yAxis: [
      {
        type: 'value',
        gridIndex: 0,
        name: '参赛记录（行）',
        nameTextStyle: { color: INK, fontSize: 10, padding: [0, 0, 4, 0] },
        axisLabel: { ...AXIS_LABEL, formatter: (value: number) => `${value / 1000}k` },
        splitLine: SPLIT_LINE,
        axisLine: { show: false },
      },
      {
        type: 'value',
        gridIndex: 1,
        name: '女性占比',
        min: 0,
        max: 50,
        nameTextStyle: { color: INK, fontSize: 10, padding: [0, 0, 4, 0] },
        axisLabel: { ...AXIS_LABEL, formatter: '{value}%' },
        splitLine: SPLIT_LINE,
        axisLine: { show: false },
      },
    ],
    series: [
      {
        name: '男性参赛记录',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        stack: 'rows',
        areaStyle: { color: 'rgba(111,168,255,0.28)' },
        lineStyle: { width: 1.6, color: '#6fa8ff' },
        itemStyle: { color: '#6fa8ff' },
        showSymbol: false,
        smooth: true,
        emphasis: { focus: 'series' },
        data: points.map((item) => item.male_rows),
      },
      {
        name: '女性参赛记录',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        stack: 'rows',
        areaStyle: { color: 'rgba(79,209,165,0.34)' },
        lineStyle: { width: 1.6, color: ACCENT },
        itemStyle: { color: ACCENT },
        showSymbol: false,
        smooth: true,
        emphasis: { focus: 'series' },
        data: points.map((item) => item.female_rows),
      },
      {
        name: '女性占比',
        type: 'line',
        xAxisIndex: 1,
        yAxisIndex: 1,
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 2.4, color: GOLD },
        itemStyle: { color: GOLD },
        areaStyle: { color: 'rgba(216,168,56,0.10)' },
        endLabel: {
          show: true, color: GOLD, fontSize: 11, distance: 4,
          formatter: '49.1%',
        },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: LINE, type: 'dashed', width: 1 },
          label: { show: false },
          data: payload.milestones.map((item) => ({ xAxis: String(item.year) })),
        },
        markPoint: {
          symbol: 'circle',
          symbolSize: 7,
          itemStyle: { color: GOLD, borderColor: '#FBFAF6', borderWidth: 1 },
          label: { show: false },
          data: markPoints,
        },
        data: points.map((item) => Number((item.female_share * 100).toFixed(1))),
      },
    ],
  };
}

export function renderC1(el: HTMLElement, payload: C1Payload) {
  const chart = echarts.init(el);
  chart.setOption(buildOption(payload));
  const observer = new ResizeObserver(() => chart.resize());
  observer.observe(el);
  return chart;
}
