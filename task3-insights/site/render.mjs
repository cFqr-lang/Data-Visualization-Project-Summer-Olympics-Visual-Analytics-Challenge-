/** 任务三 ECharts 渲染：读取 data/*.json，输出 exports/ 的 PNG@4x 与 SVG。 */
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import puppeteer from 'puppeteer-core';
import { init as echartsInit, use as echartsUse } from 'echarts/core';
import { BarChart, LineChart, ScatterChart } from 'echarts/charts';
import {
  GridComponent, TitleComponent, TooltipComponent, LegendComponent,
  MarkLineComponent, MarkPointComponent, GraphicComponent,
} from 'echarts/components';
import { SVGRenderer } from 'echarts/renderers';

echartsUse([
  BarChart, LineChart, ScatterChart,
  GridComponent, TitleComponent, TooltipComponent, LegendComponent,
  MarkLineComponent, MarkPointComponent, GraphicComponent,
  SVGRenderer,
]);

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '..');
const dataDir = resolve(root, 'data');
const outDir = resolve(root, 'exports');
const EDGE = process.env.EDGE_PATH
  ?? 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const ECHARTS_DIST = resolve(here, 'node_modules', 'echarts', 'dist', 'echarts.min.js');

const C = {
  bg: '#FBFAF6', grid: '#D9D4C7', text: '#12211C', muted: '#5F6F68',
  flame: '#C24E2A', gold: '#B8891F', silver: '#7D878A', bronze: '#A05F38',
  mint: '#2E7D68', slate: '#4A6A82', violet: '#7B5EA7',
};

const JSON_PATHS = {
  host: 'host_effect_data.json',
  geo: 'geopolitics_data.json',
  inf: 'inflation_data.json',
};

function load(name) {
  return JSON.parse(readFileSync(resolve(dataDir, name), 'utf8'));
}

function frame(title, subtitle, footnote) {
  return {
    backgroundColor: C.bg,
    title: {
      text: title, subtext: subtitle, left: 6, top: 4,
      textStyle: { color: C.text, fontSize: 20, fontWeight: 'bold', fontFamily: 'Microsoft YaHei' },
      subtextStyle: { color: C.muted, fontSize: 12, fontFamily: 'Microsoft YaHei' },
    },
    textStyle: { fontFamily: 'Microsoft YaHei', color: C.text },
    graphic: {
      elements: [{
        type: 'text', left: 6, bottom: 2,
        style: { text: footnote, fill: C.muted, fontSize: 10, fontFamily: 'Microsoft YaHei' },
      }],
    },
  };
}

const axisCommon = {
  axisLine: { lineStyle: { color: C.grid } },
  axisTick: { lineStyle: { color: C.grid } },
  axisLabel: { color: C.muted, fontSize: 11 },
  splitLine: { lineStyle: { color: C.grid } },
};

function buildCharts(d) {
  const charts = {};

  // ---------------- Fig3-1 主场脉冲（双口径） ----------------
  {
    const hosts = [...d.host.hosts].sort((a, b) => a.uplift_cons - b.uplift_cons);
    const labels = hosts.map((h) => `${h.noc} ${h.year}`);
    const mkBar = (vals) => vals.map((v) => ({
      value: v,
      itemStyle: { color: v >= 0 ? C.flame : C.slate },
      label: { show: true, position: v >= 0 ? 'right' : 'left', color: C.text, fontSize: 10 },
    }));
    charts['Fig3-1'] = {
      file: 'Fig3-1_host-pulse_4x.png', w: 1560, h: 900,
      option: {
        ...frame('东道主效应是一场脉冲：主办那一届的奖牌数显著高于前后基准',
          '1948 年以来 20 个现代东道主，按主场增量从低到高排列', '数据 v1.0 · 左：保守小项口径 · 右：运动员行口径 · 不含 1906'),
        grid: [
          { left: 100, width: '40%', top: 88, bottom: 44 },
          { left: '57%', right: 76, top: 88, bottom: 44 },
        ],
        xAxis: [
          { ...axisCommon, type: 'value', gridIndex: 0, name: '保守小项口径（枚）', nameTextStyle: { color: C.muted } },
          { ...axisCommon, type: 'value', gridIndex: 1, name: '运动员行口径（行）', nameTextStyle: { color: C.muted } },
        ],
        yAxis: [
          { ...axisCommon, type: 'category', gridIndex: 0, data: labels },
          { ...axisCommon, type: 'category', gridIndex: 1, data: labels, show: false },
        ],
        series: [
          { type: 'bar', xAxisIndex: 0, yAxisIndex: 0, barWidth: 12, data: mkBar(hosts.map((h) => h.uplift_cons)) },
          { type: 'bar', xAxisIndex: 1, yAxisIndex: 1, barWidth: 12, data: mkBar(hosts.map((h) => h.uplift_row)) },
        ],
      },
    };
  }

  // ---------------- Fig3-2 持续性 ----------------
  {
    const offs = ['-2', '-1', '0', '1', '2'];
    const offLabels = ['T-2', 'T-1', '主办届 T', 'T+1', 'T+2'];
    const series = d.host.hosts.map((h) => ({
      type: 'line', data: offs.map((o) => h.index[o]), symbol: 'none',
      lineStyle: { color: C.grid, width: 1.1 }, silent: true,
    }));
    const hi = { CHN: C.gold, GBR: C.mint, JPN: C.slate, KOR: C.bronze, BRA: C.muted, FRA: C.violet };
    for (const h of d.host.hosts) {
      if (hi[h.noc]) {
        series.push({
          type: 'line', name: `${h.noc} ${h.year}`, data: offs.map((o) => h.index[o]),
          symbol: 'circle', symbolSize: 5, lineStyle: { color: hi[h.noc], width: 2 },
        });
      }
    }
    series.push({
      type: 'line', name: '东道主中位数', data: offs.map((o) => d.host.persistence_median[o]),
      symbol: 'circle', symbolSize: 6, lineStyle: { color: C.flame, width: 3.5 },
      markLine: {
        silent: true, symbol: 'none',
        data: [
          { yAxis: 100, lineStyle: { color: C.muted, type: 'dashed' } },
          { xAxis: '主办届 T', lineStyle: { color: C.gold, type: 'dotted' } },
        ],
      },
    });
    charts['Fig3-2'] = {
      file: 'Fig3-2_persistence_4x.png', w: 1380, h: 760,
      option: {
        ...frame('主场加成是脉冲而非台阶：T+1 即快速回落', '奖牌指数以东道主前后各两届均值为 100', '数据 v1.0 · 保守小项口径 · 不含 1906 · 灰线为全部现代东道主'),
        tooltip: { trigger: 'axis' },
        legend: { top: 70, right: 12, textStyle: { color: C.muted, fontSize: 11 } },
        grid: { left: 60, right: 40, top: 100, bottom: 48 },
        xAxis: { ...axisCommon, type: 'category', data: offLabels },
        yAxis: { ...axisCommon, type: 'value', name: '奖牌指数', nameTextStyle: { color: C.muted } },
        series,
      },
    };
  }

  // ---------------- Fig3-3 来源分解 ----------------
  {
    const valid = d.host.hosts.filter((h) => h.base_cons >= 5 && h.part_ratio && h.conv_ratio);
    const key = new Set(['CHN', 'GBR', 'JPN', 'KOR', 'AUS', 'ESP', 'BRA', 'URS', 'USA', 'FRA']);
    charts['Fig3-3'] = {
      file: 'Fig3-3_decomposition_4x.png', w: 1180, h: 760,
      option: {
        ...frame('主场加成的最大来源是“多派人参赛”，而不是“单位投入夺牌更多”',
          'X>1 表示参赛规模扩张；Y>1 表示每千条参赛记录奖牌数上升 · 剔除基线 <5 枚的 MEX 1968',
          '数据 v1.0 · 保守小项口径 · 不含 1906'),
        tooltip: { trigger: 'item', formatter: '{b}' },
        grid: { left: 72, right: 36, top: 96, bottom: 52 },
        xAxis: { ...axisCommon, type: 'value', name: '参赛规模比（主办届 ÷ 前后基准）', min: 0.8, max: 2.6, nameTextStyle: { color: C.muted } },
        yAxis: { ...axisCommon, type: 'value', name: '夺牌效率比', min: 0.5, max: 2.0, nameTextStyle: { color: C.muted } },
        series: [{
          type: 'scatter', symbolSize: 12,
          data: valid.map((h) => ({
            value: [h.part_ratio, h.conv_ratio], name: `${h.noc} ${h.year}`,
            label: key.has(h.noc) ? { show: true, position: 'top', fontSize: 10, color: C.text } : {},
            itemStyle: { color: C.slate },
          })),
          markLine: {
            silent: true, symbol: 'none', lineStyle: { color: C.muted, type: 'dashed' },
            data: [{ xAxis: 1 }, { yAxis: 1 }],
          },
        }],
      },
    };
  }

  // ---------------- Fig3-4 效应量 ----------------
  {
    const centers = d.host.null_hist.centers;
    const counts = d.host.null_hist.counts;
    const ups = d.host.hosts.map((h) => h.uplift_cons);
    const inRange = d.host.hosts.filter((h) => h.uplift_cons >= -10 && h.uplift_cons <= 38);
    const keyLabel = { CHN: 'CHN 2008', FRA: 'FRA 2024', BRA: 'BRA 2016', CAN: 'CAN 1976' };
    const sd = d.host.null.sd;
    charts['Fig3-4'] = {
      file: 'Fig3-4_effect-size_4x.png', w: 1380, h: 720,
      option: {
        ...frame('主场加成的分布位置：显著高于一般国家，但不是“必然中奖”',
          `东道主平均增量 +${(d.host.hosts.reduce((s, h) => s + h.uplift_cons, 0) / d.host.hosts.length).toFixed(1)} 枚 ≈ ${(d.host.hosts.reduce((s, h) => s + h.uplift_cons, 0) / d.host.hosts.length / sd).toFixed(1)} 个标准差`,
          '数据 v1.0 · 保守小项口径 · 不含 1906 · 横轴截断于 [-10, 38]，极端值未显示'),
        grid: { left: 64, right: 40, top: 100, bottom: 48 },
        xAxis: { ...axisCommon, type: 'value', min: -10, max: 38, name: '较前后各两届均值的奖牌增量（保守小项口径）', nameTextStyle: { color: C.muted } },
        yAxis: { ...axisCommon, type: 'value', name: '国家 × 届次数', nameTextStyle: { color: C.muted } },
        series: [{
          type: 'bar', name: '非东道国波动', barMaxWidth: 8,
          data: centers.map((c, i) => [c, counts[i]]),
          itemStyle: { color: C.grid },
          markLine: {
            silent: true, symbol: 'none',
            data: [
              { xAxis: 0, lineStyle: { color: C.muted, type: 'dashed' } },
              ...inRange.map((h) => ({
                xAxis: h.uplift_cons,
                label: keyLabel[h.noc] ? { show: true, formatter: keyLabel[h.noc], fontSize: 10, color: C.text } : { show: false },
                lineStyle: { color: C.flame, width: 1.2 },
              })),
            ],
          },
        }],
        graphic: {
          elements: [
            { type: 'text', right: 10, top: 60, style: { text: 'URS 1980 +106 →  USA 1984 +99 →', fill: C.flame, fontSize: 11, fontFamily: 'Microsoft YaHei' } },
          ],
        },
      },
    };
  }

  // ---------------- Fig3-5 抵制潮 ----------------
  {
    const years = d.geo.years;
    const dl = years.map((y) => d.geo.delegations[y]);
    const cold = [1948, 1952, 1956, 1960, 1964, 1968, 1972, 1976, 1980, 1984, 1988, 1992];
    charts['Fig3-5'] = {
      file: 'Fig3-5_geopolitics-boycott_4x.png', w: 1560, h: 720,
      option: {
        ...frame('抵制潮在数据里的塌陷', 'A 每届代表团数 · B 冷战美苏两强奖牌', '数据 v1.0 · B 为保守小项口径 · 不含 1906'),
        grid: [
          { left: 70, width: '42%', top: 92, bottom: 46 },
          { left: '55%', right: 60, top: 92, bottom: 46 },
        ],
        xAxis: [
          { ...axisCommon, type: 'category', gridIndex: 0, data: years, name: '届次（年份）', nameTextStyle: { color: C.muted } },
          { ...axisCommon, type: 'category', gridIndex: 1, data: cold, name: '届次（年份）', nameTextStyle: { color: C.muted } },
        ],
        yAxis: [
          { ...axisCommon, type: 'value', gridIndex: 0, name: '代表团数', nameTextStyle: { color: C.muted } },
          { ...axisCommon, type: 'value', gridIndex: 1, name: '奖牌数', nameTextStyle: { color: C.muted } },
        ],
        series: [
          {
            type: 'line', xAxisIndex: 0, yAxisIndex: 0, name: '代表团数', data: dl,
            lineStyle: { color: C.slate }, itemStyle: { color: C.slate },
            markPoint: {
              symbolSize: 38, data: [
                { coord: ['1976', 92], value: '92', itemStyle: { color: C.silver } },
                { coord: ['1980', 80], value: '80', itemStyle: { color: C.silver } },
                { coord: ['1984', 140], value: '140', itemStyle: { color: C.silver } },
              ],
            },
          },
          {
            type: 'line', xAxisIndex: 1, yAxisIndex: 1, name: '美国',
            data: cold.map((y) => (d.geo.usa[y] != null ? d.geo.usa[y] : null)),
            lineStyle: { color: C.slate }, itemStyle: { color: C.slate },
          },
          {
            type: 'line', xAxisIndex: 1, yAxisIndex: 1, name: '苏联',
            data: cold.map((y) => (d.geo.urs_lineage.URS[y] != null ? d.geo.urs_lineage.URS[y] : null)),
            lineStyle: { color: C.flame }, itemStyle: { color: C.flame },
          },
        ],
        legend: { top: 64, right: 12, textStyle: { color: C.muted, fontSize: 11 } },
        graphic: {
          elements: [{
            type: 'text', left: 72, top: 64,
            style: { text: '1976 非洲抵制 92 · 1980 美阵营抵制 80 · 1984 苏阵营缺席 140', fill: C.muted, fontSize: 11, fontFamily: 'Microsoft YaHei' },
          }],
        },
      },
    };
  }

  // ---------------- Fig3-6 苏联谱系 ----------------
  {
    const allYears = Object.keys(d.geo.urs_lineage.URS).map(Number)
      .concat(Object.keys(d.geo.urs_lineage.EUN).map(Number))
      .concat(Object.keys(d.geo.urs_lineage.RUS).map(Number).filter((y) => y >= 1992))
      .concat(Object.keys(d.geo.urs_lineage.ROC).map(Number))
      .concat(Object.keys(d.geo.urs_lineage.AIN).map(Number));
    const xs = [...new Set(allYears)].sort((a, b) => a - b).map(String);
    const ents = [
      ['URS', '苏联 URS', C.flame], ['EUN', '独联体 EUN', C.gold],
      ['RUS', '俄罗斯 RUS', C.slate], ['ROC', 'ROC 2020', C.mint],
      ['AIN', '中立个人 AIN', C.violet],
    ];
    charts['Fig3-6'] = {
      file: 'Fig3-6_ussr-lineage_4x.png', w: 1380, h: 720,
      option: {
        ...frame('一脉苏联：从 195 枚到 5 枚的政治兴衰', '政体按 NOC 原样呈现，谱系仅注释连接', '数据 v1.0 · 保守小项口径 · 不含 1906'),
        tooltip: { trigger: 'axis' },
        legend: { top: 66, right: 12, textStyle: { color: C.muted, fontSize: 11 } },
        grid: { left: 60, right: 40, top: 100, bottom: 48 },
        xAxis: { ...axisCommon, type: 'category', data: xs, name: '届次', nameTextStyle: { color: C.muted } },
        yAxis: { ...axisCommon, type: 'value', name: '奖牌数（保守小项口径）', nameTextStyle: { color: C.muted } },
        series: ents.map(([code, label, color]) => ({
          type: 'bar', name: label, barMaxWidth: 22,
          data: xs.map((y) => (d.geo.urs_lineage[code][+y] != null ? d.geo.urs_lineage[code][+y] : null)),
          itemStyle: { color },
        })),
      },
    };
  }

  // ---------------- Fig3-7 两德 ----------------
  {
    const yrs = [];
    for (let y = 1952; y <= 2024; y += 4) yrs.push(y);
    const germany = d.geo.germany;
    const lineOf = (code, color) => ({
      type: 'line', name: { GER: '德国 GER', FRG: '西德 FRG', GDR: '东德 GDR' }[code],
      data: yrs.map((y) => (germany[code][y] != null ? [y, germany[code][y]] : null)),
      connectNulls: false, lineStyle: { color, width: 2 }, itemStyle: { color },
    });
    charts['Fig3-7'] = {
      file: 'Fig3-7_germany-split_4x.png', w: 1380, h: 720,
      option: {
        ...frame('两德：分立、互相抵制缺席、再统一',
          `东德效率奇迹：仅 5 届，保守小项 ${d.geo.gdr_stats.gdr_cons} 枚 / 运动员行 ${d.geo.gdr_stats.gdr_rows} 行`,
          '数据 v1.0 · 保守小项口径 · 不含 1906 · 1956–1964 统一队记为 GER'),
        tooltip: { trigger: 'axis' },
        legend: { top: 66, right: 12, textStyle: { color: C.muted, fontSize: 11 } },
        grid: { left: 60, right: 40, top: 100, bottom: 48 },
        xAxis: { ...axisCommon, type: 'value', min: 1950, max: 2026, name: '届次（年份）', nameTextStyle: { color: C.muted } },
        yAxis: { ...axisCommon, type: 'value', name: '奖牌数（保守小项口径）', nameTextStyle: { color: C.muted } },
        series: [
          {
            ...lineOf('GER', C.slate),
            markPoint: {
              symbolSize: 1, data: [
                { coord: [1980, 0], symbol: 'x', symbolSize: 12, itemStyle: { color: C.mint } },
                { coord: [1984, 0], symbol: 'x', symbolSize: 12, itemStyle: { color: C.flame } },
              ],
            },
          },
          lineOf('FRG', C.mint),
          lineOf('GDR', C.flame),
        ],
      },
    };
  }

  // ---------------- Fig3-8 总量与单位量 ----------------
  {
    const years = d.inf.years;
    const baseP = d.inf.per_1000_rows[1896];
    const baseD = d.inf.per_delegation[1896];
    charts['Fig3-8'] = {
      file: 'Fig3-8_inflation-unit_4x.png', w: 1560, h: 700,
      option: {
        ...frame('奖牌总量百年涨 8.6 倍，单位参赛的奖牌却在缩水',
          'A 每届奖牌总数 · B 单位量指数（1896=100）', '数据 v1.0 · 保守小项口径 · 不含 1906'),
        grid: [
          { left: 72, width: '42%', top: 92, bottom: 48 },
          { left: '55%', right: 62, top: 92, bottom: 48 },
        ],
        xAxis: [
          { ...axisCommon, type: 'category', gridIndex: 0, data: years, name: '届次（年份）', nameTextStyle: { color: C.muted } },
          { ...axisCommon, type: 'category', gridIndex: 1, data: years, name: '届次（年份）', nameTextStyle: { color: C.muted } },
        ],
        yAxis: [
          { ...axisCommon, type: 'value', gridIndex: 0, name: '奖牌总数', nameTextStyle: { color: C.muted } },
          { ...axisCommon, type: 'value', gridIndex: 1, name: '指数（1896=100）', nameTextStyle: { color: C.muted } },
        ],
        series: [
          { type: 'bar', xAxisIndex: 0, yAxisIndex: 0, name: '奖牌总数', data: years.map((y) => d.inf.totals[y]), itemStyle: { color: C.gold }, barMaxWidth: 18 },
          { type: 'line', xAxisIndex: 1, yAxisIndex: 1, name: '每千条参赛记录奖牌', data: years.map((y) => +(d.inf.per_1000_rows[y] / baseP * 100).toFixed(1)), lineStyle: { color: C.flame }, itemStyle: { color: C.flame } },
          { type: 'line', xAxisIndex: 1, yAxisIndex: 1, name: '每代表团奖牌', data: years.map((y) => +(d.inf.per_delegation[y] / baseD * 100).toFixed(1)), lineStyle: { color: C.slate }, itemStyle: { color: C.slate } },
        ],
        legend: { top: 66, right: 12, textStyle: { color: C.muted, fontSize: 11 } },
      },
    };
  }

  // ---------------- Fig3-9 结构性来源 ----------------
  {
    const years = d.inf.years;
    const sexCats = [['men', '男子', C.slate], ['women', '女子', C.flame], ['mixed', '混合', C.mint]];
    const bandColors = [C.slate, C.mint, C.gold, C.flame, C.violet, C.muted];
    charts['Fig3-9'] = {
      file: 'Fig3-9_inflation-structure_4x.png', w: 1600, h: 720,
      option: {
        ...frame('增长的结构性来源：女子项目与老项目内部扩容',
          'A 奖牌池的性别结构 · B 奖牌池的项目代际构成', '数据 v1.0 · 保守小项口径 · 不含 1906'),
        grid: [
          { left: 72, width: '42%', top: 92, bottom: 48 },
          { left: '55%', right: 70, top: 92, bottom: 48 },
        ],
        xAxis: [
          { ...axisCommon, type: 'category', gridIndex: 0, data: years, name: '届次（年份）', nameTextStyle: { color: C.muted } },
          { ...axisCommon, type: 'category', gridIndex: 1, data: years, name: '届次（年份）', nameTextStyle: { color: C.muted } },
        ],
        yAxis: [
          { ...axisCommon, type: 'value', gridIndex: 0, name: '奖牌数', nameTextStyle: { color: C.muted } },
          { ...axisCommon, type: 'value', gridIndex: 1, name: '奖牌数', nameTextStyle: { color: C.muted } },
        ],
        series: [
          ...sexCats.map(([k, name, color]) => ({
            type: 'bar', xAxisIndex: 0, yAxisIndex: 0, name, stack: 's',
            data: years.map((y) => d.inf.sex_by_year[y][k]), itemStyle: { color }, barMaxWidth: 18,
          })),
          ...d.inf.band_order.map((band, i) => ({
            type: 'bar', xAxisIndex: 1, yAxisIndex: 1, name: band, stack: 'v',
            data: years.map((y) => d.inf.vintage_by_year[y][band] || 0),
            itemStyle: { color: bandColors[i] }, barMaxWidth: 18,
          })),
        ],
        legend: { top: 64, left: '57%', textStyle: { color: C.muted, fontSize: 10 } },
      },
    };
  }

  // ---------------- Fig3-10 稀释 ----------------
  {
    const years = d.inf.years;
    charts['Fig3-10'] = {
      file: 'Fig3-10_inflation-dilution_4x.png', w: 1380, h: 720,
      option: {
        ...frame('膨胀的受益者是更多国家，而不是少数强国', '获奖 NOC 数上升，头部份额下降', '数据 v1.0 · 保守小项口径 · 不含 1906'),
        tooltip: { trigger: 'axis' },
        legend: { top: 66, right: 12, textStyle: { color: C.muted, fontSize: 11 } },
        grid: { left: 64, right: 70, top: 100, bottom: 48 },
        xAxis: { ...axisCommon, type: 'category', data: years, name: '届次（年份）', nameTextStyle: { color: C.muted } },
        yAxis: [
          { ...axisCommon, type: 'value', name: '获奖国家/地区数', nameTextStyle: { color: C.muted } },
          { ...axisCommon, type: 'value', name: '头部份额（%）', splitLine: { show: false }, nameTextStyle: { color: C.muted } },
        ],
        series: [
          { type: 'line', name: '获奖 NOC 数（左轴）', data: years.map((y) => d.inf.medal_nocs[y]), lineStyle: { color: C.mint }, itemStyle: { color: C.mint } },
          { type: 'line', yAxisIndex: 1, name: 'Top5 奖牌份额（右轴）', data: years.map((y) => +(d.inf.top5_share[y] * 100).toFixed(1)), lineStyle: { color: C.flame, type: 'dashed' }, itemStyle: { color: C.flame } },
          { type: 'line', yAxisIndex: 1, name: 'Top10 奖牌份额（右轴）', data: years.map((y) => +(d.inf.top10_share[y] * 100).toFixed(1)), lineStyle: { color: C.slate, type: 'dotted' }, itemStyle: { color: C.slate } },
        ],
      },
    };
  }

  return charts;
}

function renderSvg(chartId, option, w, h) {
  const chart = echartsInit(null, null, { renderer: 'svg', ssr: true, width: w, height: h });
  chart.setOption(option);
  const svg = chart.renderToSVGString();
  chart.dispose();
  return svg;
}

function buildHtml(chartId, option, w, h) {
  const echartsJs = readFileSync(ECHARTS_DIST, 'utf8');
  const payload = JSON.stringify(option).replace(/</g, '\\u003c');
  return `<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#FBFAF6}#stage{position:absolute;left:0;top:0}</style></head>
<body><div id="stage" style="width:${w}px;height:${h}px"></div>
<script>${echartsJs}</script>
<script>var c=echarts.init(document.getElementById('stage'));c.setOption(${payload});window.__ready=true;</script>
</body></html>`;
}

async function main() {
  mkdirSync(outDir, { recursive: true });
  const d = { host: load(JSON_PATHS.host), geo: load(JSON_PATHS.geo), inf: load(JSON_PATHS.inf) };
  const charts = buildCharts(d);

  // 1) SVG via SSR
  for (const [id, cfg] of Object.entries(charts)) {
    const svg = renderSvg(id, cfg.option, cfg.w, cfg.h);
    writeFileSync(resolve(outDir, cfg.file.replace('_4x.png', '.svg')), svg, 'utf8');
    console.log(`[SVG] ${id} ${cfg.file.replace('_4x.png', '.svg')}`);
  }

  // 2) PNG@4x via Edge（puppeteer-core，路径可用 EDGE_PATH 环境变量覆盖）
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  try {
    for (const [id, cfg] of Object.entries(charts)) {
      const page = await browser.newPage();
      await page.setViewport({ width: 1700, height: 1000, deviceScaleFactor: 4 });
      await page.setContent(buildHtml(id, cfg.option, cfg.w, cfg.h), { waitUntil: 'load' });
      await page.waitForFunction('window.__ready === true', { timeout: 30000 });
      await new Promise((r) => setTimeout(r, 250));
      const el = await page.$('#stage');
      if (!el) throw new Error(`#stage 缺失：${id}`);
      await el.screenshot({ path: resolve(outDir, cfg.file) });
      console.log(`[PNG] ${id} ${cfg.file}`);
      await page.close();
    }
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
