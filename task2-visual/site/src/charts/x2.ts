import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { X2Payload } from '../types';
import { ACCENT, AXIS_LABEL, FLAME, INK, LINE, SPLIT_LINE, TOOLTIP } from '../theme';

const MALE = '#6fa8ff';
const GAP_LINE = 'rgba(95,111,104,0.45)';

export function buildOption(payload: X2Payload): EChartsOption {
  const rows = payload.sports;
  const sports = rows.map((row) => row.sport);

  const female = rows.map((row, index) => {
    const pct = Number((row.female_share * 100).toFixed(1));
    const single = row.female_share >= 0.999 || row.male_share >= 0.999;
    const notable = !single && Math.abs(row.gap_pp) >= 4;
    const label = single
      ? (row.female_share > 0.5 ? '女子专属' : '男子专属')
      : `${row.gap_pp > 0 ? '+' : ''}${row.gap_pp.toFixed(1)} pp`;
    return {
      value: [pct, row.sport],
      sport: row.sport,
      itemStyle: { color: ACCENT },
      label: {
        show: single || notable,
        // 最顶行的单性别项目标签改到点下方，避免溢出到图例区
        position: single && index === 0 ? ('bottom' as const) : ('top' as const),
        // 单性别点固定在 100% 处，向左让出文字宽度，防止越出画布
        offset: single ? [-30, index === 0 ? 4 : -4] : [0, -10],
        distance: 6,
        fontSize: 10,
        color: FLAME,
        backgroundColor: 'rgba(251,250,246,0.92)',
        padding: [2, 3],
        borderRadius: 2,
        formatter: label,
      },
    };
  });

  const male = rows.map((row) => {
    const pct = Number((row.male_share * 100).toFixed(1));
    return {
      value: [pct, row.sport],
      sport: row.sport,
      itemStyle: { color: MALE },
    };
  });

  const lines = rows.map((row, index) => ({
    coords: [
      [Number((row.female_share * 100).toFixed(1)), index],
      [Number((row.male_share * 100).toFixed(1)), index],
    ],
    lineStyle: {
      color: Math.abs(row.gap_pp) >= 4 ? 'rgba(224,122,95,0.75)' : GAP_LINE,
      width: Math.abs(row.gap_pp) >= 4 ? 2.2 : 1.6,
    },
  }));

  return {
    backgroundColor: 'transparent',
    animationDuration: 700,
    legend: {
      top: 0,
      right: 4,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: INK, fontSize: 11 },
      data: ['女性', '男性'],
    },
    grid: { left: 132, right: 58, top: 36, bottom: 34 },
    tooltip: {
      ...TOOLTIP,
      trigger: 'item',
      formatter: (params: any) => {
        const sport = params.data?.sport as string | undefined;
        const row = rows.find((item) => item.sport === sport);
        if (!row) return '';
        const medal = row.female_medal_share === null
          ? '无奖牌行'
          : `${(row.female_medal_share * 100).toFixed(1)}%`;
        const gap = row.gap_pp > 0 ? `+${row.gap_pp.toFixed(1)}` : row.gap_pp.toFixed(1);
        return [
          `<strong>${row.sport}</strong> · 差距 ${gap} pp`,
          `女性 ${row.female_athletes} 人（${(row.female_share * 100).toFixed(1)}%）`,
          `男性 ${row.male_athletes} 人（${(row.male_share * 100).toFixed(1)}%）`,
          `女性奖牌行占比 ${medal}`,
        ].join('<br/>');
      },
    },
    xAxis: {
      type: 'value',
      min: 0,
      max: 100,
      interval: 25,
      axisLabel: { ...AXIS_LABEL, formatter: '{value}%' },
      splitLine: SPLIT_LINE,
      axisLine: { show: false },
    },
    yAxis: {
      type: 'category',
      data: sports,
      inverse: true,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: LINE } },
      axisLabel: { color: INK, fontSize: 10, interval: 0 },
    },
    series: [
      {
        name: '差距',
        type: 'lines',
        coordinateSystem: 'cartesian2d',
        polyline: false,
        silent: true,
        z: 1,
        data: lines,
        lineStyle: { opacity: 1 },
      },
      {
        name: '女性',
        type: 'scatter',
        symbolSize: 9,
        z: 3,
        data: female,
        emphasis: { itemStyle: { borderColor: '#12211C', borderWidth: 1.5 } },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: INK, type: 'dashed', width: 1.2, opacity: 0.7 },
          label: { show: true, position: 'end', formatter: '50:50', color: INK, fontSize: 10 },
          data: [{ xAxis: 50 }],
        },
      },
      {
        name: '男性',
        type: 'scatter',
        symbolSize: 9,
        z: 3,
        data: male,
        emphasis: { itemStyle: { borderColor: '#12211C', borderWidth: 1.5 } },
      },
    ],
  };
}

export function renderX2(el: HTMLElement, payload: X2Payload) {
  const chart = echarts.init(el);
  chart.setOption(buildOption(payload));
  const observer = new ResizeObserver(() => chart.resize());
  observer.observe(el);
  return chart;
}
