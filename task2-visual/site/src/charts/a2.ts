import * as echarts from 'echarts';
import type { BarSeriesOption, EChartsOption } from 'echarts';
import type { A2Payload, RaceRow } from '../types';
import {
  ACCENT, AXIS_LABEL, FLAME, GOLD, INK, LINE, SPLIT_LINE, TEXT, TOOLTIP, nocColor,
} from '../theme';

const INDEX_SERIES = [
  { key: 'medals' as const, name: '奖牌（去重）', color: GOLD },
  { key: 'delegations' as const, name: '代表团', color: ACCENT },
  { key: 'athletes' as const, name: '参赛人数', color: '#6fa8ff' },
  { key: 'events' as const, name: '小项（代理）', color: FLAME },
];

export function indexOption(payload: A2Payload): EChartsOption {
  const points = payload.series;
  const years = points.map((item) => String(item.year));

  return {
    backgroundColor: 'transparent',
    animationDuration: 800,
    grid: { left: 52, right: 76, top: 44, bottom: 40 },
    legend: {
      top: 0, right: 0, itemWidth: 12, itemHeight: 8,
      textStyle: { color: INK, fontSize: 11 },
    },
    tooltip: {
      ...TOOLTIP,
      trigger: 'axis',
      formatter: (params: any) => {
        const list = params as { seriesName: string; value: number; color: string; dataIndex: number }[];
        const row = points[list[0].dataIndex];
        return [
          `<strong>${row.year}</strong>`,
          ...list.map((item) => `${item.seriesName} 指数 <strong>${item.value}</strong>`),
          `奖牌 ${row.medal_events} · 代表团 ${row.delegations} · 参赛 ${row.athletes.toLocaleString('zh-CN')}`,
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
      name: '指数（1896 = 100）',
      nameTextStyle: { color: INK, fontSize: 11, padding: [0, 0, 4, 0] },
      axisLabel: AXIS_LABEL,
      splitLine: SPLIT_LINE,
      axisLine: { show: false },
    },
    series: INDEX_SERIES.map((meta, index) => ({
      name: meta.name,
      type: 'line' as const,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      showSymbol: false,
      lineStyle: { width: index === 0 ? 2.6 : 1.8, color: meta.color },
      itemStyle: { color: meta.color },
      emphasis: { focus: 'series' as const },
      endLabel: {
        show: meta.key === 'athletes' || meta.key === 'delegations',
        color: meta.color, fontSize: 10, distance: 4,
        formatter: '{a}',
      },
      data: points.map((item) => item.index[meta.key]),
    })),
  };
}

export function raceOption(payload: A2Payload): EChartsOption {
  const years = payload.bar_race.map((item) => String(item.year));
  const maxTotal = Math.max(
    ...payload.bar_race.flatMap((year) => year.top.map((row) => row.total)),
    10
  );
  const yMax = Math.ceil(maxTotal / 20) * 20;

  const options: EChartsOption[] = payload.bar_race.map(({ year, top }) => {
    const rows = [...top].sort((a, b) => a.total - b.total);
    const lookup = new Map(rows.map((row) => [row.noc, row]));
    const nocs = rows.map((row) => row.noc);

    const stack = (
      name: string, key: 'gold' | 'silver' | 'bronze', color: string
    ): BarSeriesOption => ({
      name,
      type: 'bar',
      stack: 'medal',
      barWidth: '58%',
      itemStyle: { color },
      emphasis: { focus: 'series' },
      data: rows.map((row) => row[key]),
    });

    const bronze = stack('铜牌', 'bronze', '#b1743f');
    bronze.label = {
      show: true,
      position: 'right',
      color: TEXT,
      fontSize: 10,
      formatter: (params: any) => {
        const row = lookup.get(nocs[params.dataIndex]);
        return row ? String(row.total) : '';
      },
    };

    return {
      title: {
        text: String(year),
        right: 12,
        top: 2,
        textStyle: { color: '#D9D4C7', fontSize: 42, fontWeight: 700 },
      },
      grid: { left: 56, right: 56, top: 52, bottom: 62 },
      xAxis: {
        type: 'value',
        max: yMax,
        axisLabel: { ...AXIS_LABEL, fontSize: 10 },
        splitLine: SPLIT_LINE,
        axisLine: { show: false },
      },
      yAxis: {
        type: 'category',
        data: nocs,
        axisTick: { show: false },
        axisLine: { lineStyle: { color: LINE } },
        axisLabel: { color: TEXT, fontSize: 11 },
      },
      series: [
        stack('金牌', 'gold', GOLD),
        stack('银牌', 'silver', '#b7c2c8'),
        bronze,
      ],
    } as EChartsOption;
  });

  return {
    backgroundColor: 'transparent',
    baseOption: {
      timeline: {
        axisType: 'category',
        autoPlay: true,
        loop: true,
        playInterval: 1000,
        currentIndex: years.length - 1,
        data: years,
        bottom: 4,
        height: 32,
        left: 24,
        right: 24,
        label: { color: INK, fontSize: 10 },
        lineStyle: { color: LINE },
        itemStyle: { color: ACCENT },
        checkpointStyle: { color: GOLD, borderColor: GOLD },
        controlStyle: { color: INK, borderColor: INK },
        progress: { lineStyle: { color: ACCENT }, itemStyle: { color: ACCENT } },
      },
      tooltip: {
        ...TOOLTIP,
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(95,111,104,0.07)' } },
        formatter: (params: any) => {
          const list = params as { seriesName: string; dataIndex: number; marker: string }[];
          const name = list[0].seriesName;
          const index = list[0].dataIndex;
          const race = payload.bar_race.find((item) => item.top.some((row) => row.noc === name));
          const row = race?.top.find((item) => item.noc === name);
          if (!row) return '';
          return [
            `<strong>${row.noc}</strong> · ${params[0].axisValue}`,
            `金 ${row.gold} · 银 ${row.silver} · 铜 ${row.bronze}`,
            `合计 <strong>${row.total}</strong>`,
          ].join('<br/>');
        },
      },
      legend: {
        top: 0, left: 12, itemWidth: 10, itemHeight: 8,
        textStyle: { color: INK, fontSize: 11 },
      },
    },
    options,
  };
}

export function renderA2(indexEl: HTMLElement, raceEl: HTMLElement, payload: A2Payload) {
  const indexChart = echarts.init(indexEl);
  const raceChart = echarts.init(raceEl);
  indexChart.setOption(indexOption(payload));
  raceChart.setOption(raceOption(payload));

  const observer = new ResizeObserver(() => {
    indexChart.resize();
    raceChart.resize();
  });
  observer.observe(indexEl);
  observer.observe(raceEl);

  return { indexChart, raceChart, colorOf: nocColor };
}
