import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { D1Payload } from '../types';
import { ACCENT, AXIS_LABEL, FLAME, INK, LINE, SPLIT_LINE, TEXT, TOOLTIP } from '../theme';

export function countOption(payload: D1Payload): EChartsOption {
  const rows = payload.event_counts;
  const years = rows.map((item) => String(item.year));
  const official = rows
    .filter((item) => item.official !== null)
    .map((item) => ({
      value: [String(item.year), item.official as number],
      label: { position: item.year <= 2020 ? ('left' as const) : ('bottom' as const) },
    }));
  const max = Math.max(...rows.map((item) => item.proxy), 400);

  return {
    backgroundColor: 'transparent',
    animationDuration: 700,
    grid: { left: 52, right: 28, top: 36, bottom: 30 },
    legend: {
      top: 0, right: 0, itemWidth: 12, itemHeight: 8,
      textStyle: { color: INK, fontSize: 11 },
    },
    tooltip: {
      ...TOOLTIP,
      trigger: 'axis',
      formatter: (params: any) => {
        const list = params as { seriesName: string; value: number; axisValue: string }[];
        if (!list.length) return '';
        const year = Number(list[0].axisValue);
        const row = rows.find((item) => item.year === year);
        if (!row) return '';
        return [
          `<strong>${year}</strong>`,
          `Sport×Sex 代理小项数 <strong>${row.proxy}</strong>`,
          row.official ? `官方小项数 ${row.official}` : '官方值未单列',
        ].join('<br/>');
      },
    },
    xAxis: {
      type: 'category',
      data: years,
      boundaryGap: false,
      axisLine: { lineStyle: { color: LINE } },
      axisTick: { show: false },
      axisLabel: { ...AXIS_LABEL, interval: 4 },
    },
    yAxis: {
      type: 'value',
      max,
      name: '小项数',
      nameTextStyle: { color: INK, fontSize: 10 },
      axisLabel: AXIS_LABEL,
      splitLine: SPLIT_LINE,
      axisLine: { show: false },
    },
    series: [
      {
        name: 'Sport×Sex 代理',
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2.2, color: ACCENT },
        itemStyle: { color: ACCENT },
        areaStyle: { color: 'rgba(79,209,165,0.14)' },
        markArea: {
          silent: true,
          itemStyle: { color: 'rgba(224,122,95,0.08)' },
          label: { show: false },
          data: [[{ name: '2020+ 代理估计', xAxis: '2020' }, { xAxis: '2024' }]],
        },
        data: rows.map((item) => item.proxy),
      },
      {
        name: '官方小项数',
        type: 'scatter',
        symbolSize: 9,
        itemStyle: { color: FLAME },
        label: {
          show: true,
          position: 'top',
          color: TEXT,
          fontSize: 10,
          formatter: (params: any) => String(params.value[1]),
        },
        data: official,
      },
    ],
  };
}

export function lifelineOption(payload: D1Payload): EChartsOption {
  const ordered = [...payload.sports];
  const names = ordered.map((item) => item.sport);
  const data = ordered.map((item, index) => ({
    value: [index, item.first, item.last],
    itemStyle: { color: item.status === 'active' ? ACCENT : FLAME },
  }));

  return {
    backgroundColor: 'transparent',
    animationDuration: 800,
    grid: { left: 164, right: 36, top: 24, bottom: 58 },
    tooltip: {
      ...TOOLTIP,
      trigger: 'item',
      formatter: (params: any) => {
        const item = ordered[params.dataIndex];
        if (!item) return '';
        const status = item.status === 'active' ? '仍在奥运' : '已退出';
        return [
          `<strong>${item.sport}</strong> · ${status}`,
          `首次 ${item.first} · 最近 ${item.last}`,
          `参赛 ${item.editions} 届 · 奖牌 ${item.medals} 枚`,
        ].join('<br/>');
      },
    },
    xAxis: {
      type: 'value',
      min: 1896,
      max: 2024,
      name: '年份',
      nameTextStyle: { color: INK, fontSize: 10 },
      axisLabel: { ...AXIS_LABEL, formatter: '{value}' },
      splitLine: SPLIT_LINE,
      axisLine: { lineStyle: { color: LINE } },
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: names,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: LINE } },
      axisLabel: { color: TEXT, fontSize: 9, interval: 0, width: 148, overflow: 'truncate' },
    },
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'weakFilter' },
      { type: 'slider', xAxisIndex: 0, bottom: 8, height: 16, borderColor: LINE, fillerColor: 'rgba(79,209,165,0.12)', textStyle: { color: INK, fontSize: 9 } },
    ],
    series: [
      {
        type: 'custom',
        renderItem: (params: any, api: any) => {
          const index = api.value(0) as number;
          const start = api.coord([api.value(1), index]);
          const end = api.coord([api.value(2), index]);
          const rowHeight = api.size([0, 1])[1] * 0.56;
          // dataZoom 放大后 start 会落到坐标系之外，钳制在绘图区内，避免条形压住纵轴标签
          const gridLeft = params.coordSys.x as number;
          const gridRight = gridLeft + (params.coordSys.width as number);
          const x0 = Math.min(Math.max(start[0], gridLeft), gridRight);
          const x1 = Math.min(Math.max(end[0], gridLeft), gridRight);
          return {
            type: 'rect',
            shape: {
              x: x0,
              y: start[1] - rowHeight / 2,
              width: Math.max(x1 - x0, x1 > x0 ? 3 : 0),
              height: rowHeight,
              r: 2,
            },
            style: {
              fill: api.visual('color'),
              opacity: 0.9,
            },
          };
        },
        encode: { x: [1, 2], y: 0 },
        clip: true,
        data,
      },
    ],
  };
}

export function renderD1(countEl: HTMLElement, lifeEl: HTMLElement, payload: D1Payload) {
  const countChart = echarts.init(countEl);
  const lifeChart = echarts.init(lifeEl);
  countChart.setOption(countOption(payload));
  lifeChart.setOption(lifelineOption(payload));

  const observer = new ResizeObserver(() => {
    countChart.resize();
    lifeChart.resize();
  });
  observer.observe(countEl);
  observer.observe(lifeEl);

  return { countChart, lifeChart };
}
