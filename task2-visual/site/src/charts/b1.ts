import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { B1Payload } from '../types';
import { AXIS_LABEL, INK, LINE, SPLIT_LINE, TEXT, TOOLTIP, nocColor } from '../theme';

const COLS = ['3%', '35.2%', '67.4%'];
const ROWS = ['4%', '37%', '70%'];
const TITLE_ROWS = ['0.5%', '33.5%', '66.5%'];
const WIDTH = '29%';
const HEIGHT = '22%';

export function buildOption(payload: B1Payload): EChartsOption {
  const grids: Record<string, unknown>[] = [];
  const xAxes: Record<string, unknown>[] = [];
  const yAxes: Record<string, unknown>[] = [];
  const titles: Record<string, unknown>[] = [];
  const series: Record<string, unknown>[] = [];

  payload.panels.forEach((panel, index) => {
    const col = index % 3;
    const row = Math.floor(index / 3);

    grids.push({
      left: COLS[col],
      top: ROWS[row],
      width: WIDTH,
      height: HEIGHT,
      containLabel: false,
    });
    titles.push({
      text: panel.label,
      left: COLS[col],
      top: TITLE_ROWS[row],
      textStyle: { color: TEXT, fontSize: 12, fontWeight: 600 },
    });
    xAxes.push({
      type: 'value',
      gridIndex: index,
      min: 1896,
      max: 2024,
      axisLine: { lineStyle: { color: LINE } },
      axisTick: { show: false },
      axisLabel: {
        ...AXIS_LABEL,
        fontSize: 9,
        show: row === 2,
        formatter: (value: number) =>
          [1896, 1936, 1980, 2024].includes(value) ? String(value) : '',
      },
      splitLine: { show: false },
    });
    yAxes.push({
      type: 'value',
      gridIndex: index,
      axisLabel: { ...AXIS_LABEL, fontSize: 9, show: col === 0 },
      splitLine: SPLIT_LINE,
      axisLine: { show: false },
    });

    panel.series.forEach((line) => {
      const color = nocColor(line.noc);
      series.push({
        name: line.noc,
        type: 'line',
        xAxisIndex: index,
        yAxisIndex: index,
        showSymbol: false,
        connectNulls: false,
        smooth: false,
        lineStyle: { width: 2, color },
        itemStyle: { color },
        emphasis: { focus: 'series' as const },
        data: line.points.map((point) => [point.year, point.total]),
      });
      series.push({
        name: `${line.noc}·金`,
        type: 'line',
        xAxisIndex: index,
        yAxisIndex: index,
        showSymbol: false,
        connectNulls: false,
        smooth: false,
        lineStyle: { width: 1.1, color, type: 'dashed' as const, opacity: 0.85 },
        itemStyle: { color },
        emphasis: { disabled: true },
        data: line.points.map((point) => [point.year, point.gold]),
      });
    });
  });

  return {
    backgroundColor: 'transparent',
    animationDuration: 700,
    title: titles as any,
    grid: grids as any,
    xAxis: xAxes as any,
    yAxis: yAxes as any,
    axisPointer: {
      link: [{ xAxisIndex: 'all' }],
      label: { backgroundColor: '#0f201a', color: TEXT },
    },
    tooltip: {
      ...TOOLTIP,
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: INK, width: 1 } },
      formatter: (params: any) => {
        const list = params as { seriesName: string; value: [number, number]; color: string; dataIndex: number }[];
        if (!list.length) return '';
        const visible = list.filter((item) => item.value && item.value[1] > 0);
        if (!visible.length) return '';
        const year = visible[0].value[0];
        return [
          `<strong>${year}</strong>`,
          ...visible.map((item) => `${item.seriesName} ${item.value[1]}`),
        ].join('<br/>');
      },
    },
    series: series as any,
  };
}

export function renderB1(el: HTMLElement, payload: B1Payload) {
  const chart = echarts.init(el);
  chart.setOption(buildOption(payload));
  const observer = new ResizeObserver(() => chart.resize());
  observer.observe(el);
  return chart;
}
