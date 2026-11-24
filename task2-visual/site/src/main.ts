import './styles.css';
import type {
  A1Payload, A2Payload, B1Payload, B2Payload, C1Payload, C2Payload, D1Payload, D2Payload,
  FigureMeta, IndexPayload, MetaPayload, X1Payload, X2Payload,
} from './types';
import { renderA1 } from './charts/a1';
import { renderA2 } from './charts/a2';
import { renderB1 } from './charts/b1';
import { renderB2 } from './charts/b2';
import { renderC1 } from './charts/c1';
import { renderC2 } from './charts/c2';
import { renderD1 } from './charts/d1';
import { renderD2 } from './charts/d2';
import { renderX1 } from './charts/x1';
import { renderX2 } from './charts/x2';

const fmt = new Intl.NumberFormat('zh-CN');

const INLINE_DATA = (window as unknown as { __OLYMPICS_DATA__?: Record<string, unknown> })
  .__OLYMPICS_DATA__;

async function getJSON<T>(path: string): Promise<T> {
  if (INLINE_DATA && path in INLINE_DATA) return INLINE_DATA[path] as T;
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  return (await res.json()) as T;
}

const app = document.getElementById('app');
if (!app) throw new Error('#app 缺失');

app.innerHTML = `
  <div class="shell">
    <header class="hero">
      <p class="hero__eyebrow">数说奥运 1896–2024 · 任务二</p>
      <h1 class="hero__title">百年奥运，是一部扩张史，<br />也是一部集中史</h1>
      <p class="hero__lead">
        同一场比赛，换一种奖牌口径，榜首与名次就会改写。这里沿四组追问展开：奖牌格局如何膨胀，
        国家如何崛起与坠落，女性如何从 0 走到 49.1%，项目如何生灭更替。
      </p>
      <div class="badges" id="badges"></div>
    </header>

    <section class="figure" id="fig-A1">
      <div class="figure__head">
        <span class="figure__id">Fig.2-1 · A1</span>
        <h2 class="figure__title">奖牌榜是口径的函数</h2>
      </div>
      <p class="figure__sub" id="a1-sub"></p>
      <div class="figure__grid">
        <div class="panel">
          <div class="panel__cap">
            <span>历史累计奖牌 Top 20</span>
            <span>保守小项口径 · 不含 1906</span>
          </div>
          <div class="chart" id="chart-a1-bar"></div>
        </div>
        <div class="panel">
          <div class="panel__cap">
            <span>Top 10 在四种口径下的排名</span>
            <span>排序：金 &gt; 银 &gt; 铜</span>
          </div>
          <div class="chart" id="chart-a1-slope"></div>
        </div>
      </div>
      <ul class="notes" id="a1-notes"></ul>
    </section>

    <section class="figure" id="fig-A2">
      <div class="figure__head">
        <span class="figure__id">Fig.2-2 · A2</span>
        <h2 class="figure__title">奖牌在膨胀，榜单头部却长期稳定</h2>
      </div>
      <p class="figure__sub" id="a2-sub"></p>
      <div class="figure__grid figure__grid--even">
        <div class="panel">
          <div class="panel__cap">
            <span>奖牌与规模膨胀指数</span>
            <span>1896 = 100</span>
          </div>
          <div class="chart chart--mid" id="chart-a2-index"></div>
        </div>
        <div class="panel">
          <div class="panel__cap">
            <span>逐届奖牌 Top 10</span>
            <span>时间轴自动播放，可拖动</span>
          </div>
          <div class="chart chart--mid" id="chart-a2-race"></div>
        </div>
      </div>
      <ul class="notes" id="a2-notes"></ul>
    </section>

    <section class="figure" id="fig-B1">
      <div class="figure__head">
        <span class="figure__id">Fig.2-3 · B1</span>
        <h2 class="figure__title">四种国家模式并存：长盛、骤起骤落、分立统一、后发崛起</h2>
      </div>
      <p class="figure__sub" id="b1-sub"></p>
      <div class="panel">
        <div class="panel__cap">
          <span>九国九面板 · 实线总奖牌 / 虚线金牌</span>
          <span>政体按 NOC 原样呈现，谱系只在注释层连接</span>
        </div>
        <div class="chart chart--tall" id="chart-b1"></div>
      </div>
      <ul class="notes" id="b1-notes"></ul>
    </section>

    <section class="figure" id="fig-B2">
      <div class="figure__head">
        <span class="figure__id">Fig.2-7 · B2</span>
        <h2 class="figure__title">参赛规模与奖牌非线性，小国站在效率前沿</h2>
      </div>
      <p class="figure__sub" id="b2-sub"></p>
      <div class="panel">
        <div class="panel__cap">
          <span>场均参赛人数 × 场均奖牌 · 双 log · 点大小 = 参赛届数</span>
          <span>金色 = 效率 ≥ 0.12 枚/百人 · 仅赛题数据</span>
        </div>
        <div class="chart chart--mid" id="chart-b2"></div>
      </div>
      <ul class="notes" id="b2-notes"></ul>
    </section>

    <section class="figure" id="fig-X1">
      <div class="figure__head">
        <span class="figure__id">Fig.2-9 · X1</span>
        <h2 class="figure__title">传统优势写在项目里：国家 × 项目 lift</h2>
      </div>
      <p class="figure__sub" id="x1-sub"></p>
      <div class="panel">
        <div class="panel__cap">
          <span>Top 12 NOC × Top 10 项目 · lift 热力图</span>
          <span>lift = 1 与全局结构一致 · 金色为相对专长</span>
        </div>
        <div class="chart chart--mid" id="chart-x1"></div>
      </div>
      <ul class="notes" id="x1-notes"></ul>
    </section>

    <section class="figure" id="fig-C1">
      <div class="figure__head">
        <span class="figure__id">Fig.2-4 · C1</span>
        <h2 class="figure__title">女性从 0 走到 49.1%，走的是三次跃迁而非直线</h2>
      </div>
      <p class="figure__sub" id="c1-sub"></p>
      <div class="panel">
        <div class="panel__cap">
          <span>上：男女参赛记录堆叠面积 · 下：女性占比与里程碑</span>
          <span>运动员行口径 · 全部参赛记录</span>
        </div>
        <div class="chart chart--mid" id="chart-c1"></div>
      </div>
      <div class="milestones" id="c1-milestones"></div>
      <ul class="notes" id="c1-notes"></ul>
    </section>

    <section class="figure" id="fig-C2">
      <div class="figure__head">
        <span class="figure__id">Fig.2-5 · C2</span>
        <h2 class="figure__title">女性参赛占比高，不等于女性奖牌占比高</h2>
      </div>
      <p class="figure__sub" id="c2-sub"></p>
      <div class="panel">
        <div class="panel__cap">
          <span>女性参赛占比 × 女性奖牌占比 · 点大小 = 参赛记录数</span>
          <span class="c2-controls" id="c2-controls"></span>
        </div>
        <div class="chart chart--mid" id="chart-c2"></div>
      </div>
      <ul class="notes" id="c2-notes"></ul>
    </section>

    <section class="figure" id="fig-X2">
      <div class="figure__head">
        <span class="figure__id">Fig.2-10 · X2</span>
        <h2 class="figure__title">性别差集中在少数项目，多数项目已接近 50:50</h2>
      </div>
      <p class="figure__sub" id="x2-sub"></p>
      <div class="panel">
        <div class="panel__cap">
          <span>2024 各项目女性 / 男性参赛占比 · 连线为差距</span>
          <span>橙色线 = 差距 ≥ 4 pp · 虚线为 50:50</span>
        </div>
        <div class="chart chart--taller" id="chart-x2"></div>
      </div>
      <ul class="notes" id="x2-notes"></ul>
    </section>

    <section class="figure" id="fig-D1">
      <div class="figure__head">
        <span class="figure__id">Fig.2-6 · D1</span>
        <h2 class="figure__title">核心项目稳定，边缘项目不断轮换</h2>
      </div>
      <p class="figure__sub" id="d1-sub"></p>
      <div class="panel">
        <div class="panel__cap">
          <span>每届小项数</span>
          <span>2020+ 为 Sport×Sex 代理 · 官方 339 / 329 校准</span>
        </div>
        <div class="chart chart--low" id="chart-d1-count"></div>
      </div>
      <div class="panel panel--spaced">
        <div class="panel__cap">
          <span>项目生命线 · 首次出现 → 最近出现</span>
          <span>绿色仍在 · 橙色已退出 · 滚轮缩放年份</span>
        </div>
        <div class="chart chart--taller" id="chart-d1-life"></div>
      </div>
      <div class="chips" id="d1-highlights"></div>
      <ul class="notes" id="d1-notes"></ul>
    </section>

    <section class="figure" id="fig-D2">
      <div class="figure__head">
        <span class="figure__id">Fig.2-8 · D2</span>
        <h2 class="figure__title">核心大类份额稳定，新兴类在边缘上升</h2>
      </div>
      <p class="figure__sub" id="d2-sub"></p>
      <div class="panel">
        <div class="panel__cap">
          <span>项目结构变迁 · themeRiver（6–8 类 + Other）</span>
          <span>宽度 = 当届保守小项奖牌数</span>
        </div>
        <div class="chart chart--mid" id="chart-d2"></div>
      </div>
      <ul class="notes" id="d2-notes"></ul>
    </section>

    <section class="figure" id="fig-interface">
      <div class="figure__head">
        <span class="figure__id">接口</span>
        <h2 class="figure__title">十图资产与全队复用</h2>
      </div>
      <p class="figure__sub">
        管线输出固定 JSON 结构（<code>meta</code> + 数据段），任务三可直接引用指标，
        任务四可直接复用图表组件与离线包。10 幅图均已登记到
        <code>contracts/figure_registry.csv</code>。
      </p>
      <div class="pending" id="assets"></div>
    </section>

    <footer id="footer"></footer>
  </div>
`;

function renderBadges(meta: MetaPayload): void {
  const counts = meta.counts;
  const badges = [
    ['参赛记录', fmt.format(Number(counts.rows))],
    ['NOC', String(counts.noc_count)],
    ['奖牌行', fmt.format(Number(counts.medals))],
    ['最后一届女性占比', `${(Number(counts.female_share_latest) * 100).toFixed(1)}%`],
    ['体育大类（归并后）', String(counts.sport_count)],
  ];
  const el = document.getElementById('badges');
  if (!el) return;
  el.innerHTML = badges
    .map(([label, value]) => `<span class="badge">${label} <strong>${value}</strong></span>`)
    .join('');
}

function metaLine(meta: FigureMeta): string {
  return (
    `口径：${meta.caliber_label}｜分母：${meta.denominator}｜` +
    `含 1906：${meta.includes_1906 ? '是' : '否'}｜数据 ${meta.data_version}`
  );
}

function setText(id: string, text: string): void {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setNotes(id: string, items: string[]): void {
  const el = document.getElementById(id);
  if (el) el.innerHTML = items.map((text) => `<li>${text}</li>`).join('');
}

function renderA1Section(a1: A1Payload): void {
  setText('a1-sub', metaLine(a1.meta));

  const changes = a1.rank_changes
    .filter((item) => item.delta !== 0)
    .slice(0, 4)
    .map((item) => {
      const arrow = item.delta > 0 ? '↑' : '↓';
      return `${item.noc}：行口径第 ${item.athlete_row_rank} → 保守小项第 ${item.conservative_rank}（${arrow}${Math.abs(item.delta)}）`;
    });
  setNotes('a1-notes', [...a1.meta.notes, ...changes]);

  renderA1(
    document.getElementById('chart-a1-bar') as HTMLElement,
    document.getElementById('chart-a1-slope') as HTMLElement,
    a1
  );
}

function renderA2Section(a2: A2Payload): void {
  setText('a2-sub', metaLine(a2.meta));
  setNotes('a2-notes', [
    ...a2.meta.notes,
    `停办届：${a2.missing_years.join(' / ')}，曲线上直接缺届而非 0`,
    `2024 年奖牌去重 ${fmt.format(a2.series[a2.series.length - 1].medal_events)} 枚，代表团 ${a2.series[a2.series.length - 1].delegations} 个`,
  ]);
  renderA2(
    document.getElementById('chart-a2-index') as HTMLElement,
    document.getElementById('chart-a2-race') as HTMLElement,
    a2
  );
}

function renderB1Section(b1: B1Payload): void {
  setText('b1-sub', metaLine(b1.meta));
  const panelNotes = b1.panels
    .filter((panel) => panel.notes.length)
    .map((panel) => `<strong>${panel.label}</strong>（${panel.nocs.join(' / ')}）：${panel.notes.join('；')}`);
  setNotes('b1-notes', [...b1.meta.notes, ...panelNotes]);
  renderB1(document.getElementById('chart-b1') as HTMLElement, b1);
}

function renderB2Section(b2: B2Payload): void {
  setText('b2-sub', metaLine(b2.meta));
  const top = b2.points.slice(0, 3);
  const efficient = [...b2.points].sort((a, b) => b.efficiency - a.efficiency).slice(0, 3);
  setNotes('b2-notes', [
    ...b2.meta.notes,
    `场均奖牌前三：${top.map((item) => `${item.noc} ${item.avg_medals}`).join(' · ')}`,
    `效率前三：${efficient.map((item) => `${item.noc} ${(item.efficiency * 100).toFixed(1)} 枚/百人`).join(' · ')}`,
  ]);
  renderB2(document.getElementById('chart-b2') as HTMLElement, b2);
}

function renderX1Section(x1: X1Payload): void {
  setText('x1-sub', metaLine(x1.meta));
  const top = [...x1.cells].sort((a, b) => b.lift - a.lift).slice(0, 3);
  const zeros = x1.cells.filter((cell) => cell.medals === 0);
  setNotes('x1-notes', [
    ...x1.meta.notes,
    `最高 lift：${top.map((cell) => `${cell.noc}×${cell.sport} ${cell.lift.toFixed(2)}`).join(' · ')}`,
    `零奖牌格：${zeros.map((cell) => `${cell.noc}×${cell.sport}`).join('、')}；强项覆盖并非可以无限横向复制`,
  ]);
  renderX1(document.getElementById('chart-x1') as HTMLElement, x1);
}

function renderC1Section(c1: C1Payload): void {
  setText('c1-sub', metaLine(c1.meta));
  setNotes('c1-notes', c1.meta.notes);

  const milestones = document.getElementById('c1-milestones');
  if (milestones) {
    milestones.innerHTML = c1.milestones
      .map((item) => `<span class="chip"><em>${item.year}</em>${item.text}</span>`)
      .join('');
  }
  renderC1(document.getElementById('chart-c1') as HTMLElement, c1);
}

function renderC2Section(c2: C2Payload): void {
  const view = c2.views[0];
  setText(
    'c2-sub',
    `${metaLine(c2.meta)}｜当前视图：${view.label}（${view.years.join(' / ')}）｜` +
      `保留记录数 ≥ ${view.min_rows} 且奖牌行 ≥ ${view.min_medals} 的国家`
  );
  setNotes('c2-notes', c2.meta.notes);

  const controls = document.getElementById('c2-controls');
  if (controls) {
    controls.innerHTML = c2.views
      .map(
        (item, index) =>
          `<button type="button" class="switch${index === 0 ? ' is-active' : ''}" data-view="${item.id}">${item.label}</button>`
      )
      .join('');
  }

  const c2Chart = renderC2(document.getElementById('chart-c2') as HTMLElement, c2);

  controls?.querySelectorAll<HTMLButtonElement>('[data-view]').forEach((button) => {
    button.addEventListener('click', () => {
      const id = button.dataset.view;
      if (!id) return;
      c2Chart.setView(id);
      const target = c2.views.find((item) => item.id === id);
      if (!target) return;
      controls.querySelectorAll('.switch').forEach((node) => node.classList.remove('is-active'));
      button.classList.add('is-active');
      setText(
        'c2-sub',
        `${metaLine(c2.meta)}｜当前视图：${target.label}（${target.years.join(' / ')}）｜` +
          `保留记录数 ≥ ${target.min_rows} 且奖牌行 ≥ ${target.min_medals} 的国家`
      );
    });
  });
}

function renderX2Section(x2: X2Payload): void {
  setText('x2-sub', metaLine(x2.meta));
  const outliers = x2.sports.filter((row) => Math.abs(row.gap_pp) >= 4);
  const near = x2.sports.filter((row) => Math.abs(row.gap_pp) < 4).length;
  setNotes('x2-notes', [
    ...x2.meta.notes,
    `差距 ≥ 4 pp 的项目：${outliers
      .map((row) => `${row.sport} ${row.gap_pp > 0 ? '+' : ''}${row.gap_pp.toFixed(1)}`)
      .join(' · ')}`,
    `${near} / ${x2.sports.length} 个项目落在 ±4 pp 内，性别差是局部问题而非普遍现象`,
  ]);
  renderX2(document.getElementById('chart-x2') as HTMLElement, x2);
}

function renderD1Section(d1: D1Payload): void {
  setText('d1-sub', metaLine(d1.meta));
  setNotes('d1-notes', d1.meta.notes);

  const highlights = document.getElementById('d1-highlights');
  if (highlights) {
    const retired = d1.highlights.retired
      .slice(0, 6)
      .map((item) => `<span class="chip chip--retired"><em>${item.first}–${item.last}</em>${item.sport}</span>`);
    const added = d1.highlights.added
      .slice(0, 6)
      .map((item) => `<span class="chip chip--added"><em>${item.first}</em>${item.sport}</span>`);
    highlights.innerHTML = [
      `<div class="chips__row"><span class="chips__label">已退出</span>${retired.join('')}</div>`,
      `<div class="chips__row"><span class="chips__label">新增</span>${added.join('')}</div>`,
    ].join('');
  }

  renderD1(
    document.getElementById('chart-d1-count') as HTMLElement,
    document.getElementById('chart-d1-life') as HTMLElement,
    d1
  );
}

function renderD2Section(d2: D2Payload): void {
  setText('d2-sub', metaLine(d2.meta));
  const top = d2.totals.slice(0, 3);
  setNotes('d2-notes', [
    ...d2.meta.notes,
    `历史累计前三：${top.map((item) => `${item.name} ${item.medals} 枚`).join(' · ')}`,
  ]);
  renderD2(document.getElementById('chart-d2') as HTMLElement, d2);
}

function renderAssets(index: IndexPayload): void {
  const el = document.getElementById('assets');
  if (!el) return;
  el.innerHTML = index.figures
    .map(
      (figure) => `
      <article class="pending__card">
        <span class="figure__id">${figure.figure_id} · ${figure.chart_id}</span>
        <h3>${figure.title} <span class="tag">已交付</span></h3>
        <p>${figure.caliber}<br />${figure.path}</p>
      </article>`
    )
    .join('');
}

function renderFooter(meta: MetaPayload, a1: A1Payload): void {
  const footer = document.getElementById('footer');
  if (!footer) return;
  const passed = meta.checks.filter((item) => item.pass).length;
  footer.innerHTML = [
    `数据 ${meta.data_version} · 生成 ${meta.generated_at}`,
    `自检 ${passed}/${meta.checks.length} 通过 · 事件键来源 ${a1.meta.event_key_source}`,
    `来源 ${a1.meta.source} · 图表 Apache ECharts · 口径以任务一 caliber_spec 为准`,
  ].join('<br />');
}

async function boot(): Promise<void> {
  try {
    const [meta, index, a1, a2, b1, b2, x1, c1, c2, x2, d1, d2] = await Promise.all([
      getJSON<MetaPayload>('./data/meta.json'),
      getJSON<IndexPayload>('./data/index.json'),
      getJSON<A1Payload>('./data/figures/fig-A1.json'),
      getJSON<A2Payload>('./data/figures/fig-A2.json'),
      getJSON<B1Payload>('./data/figures/fig-B1.json'),
      getJSON<B2Payload>('./data/figures/fig-B2.json'),
      getJSON<X1Payload>('./data/figures/fig-X1.json'),
      getJSON<C1Payload>('./data/figures/fig-C1.json'),
      getJSON<C2Payload>('./data/figures/fig-C2.json'),
      getJSON<X2Payload>('./data/figures/fig-X2.json'),
      getJSON<D1Payload>('./data/figures/fig-D1.json'),
      getJSON<D2Payload>('./data/figures/fig-D2.json'),
    ]);

    renderBadges(meta);
    renderA1Section(a1);
    renderA2Section(a2);
    renderB1Section(b1);
    renderB2Section(b2);
    renderX1Section(x1);
    renderC1Section(c1);
    renderC2Section(c2);
    renderX2Section(x2);
    renderD1Section(d1);
    renderD2Section(d2);
    renderAssets(index);
    renderFooter(meta, a1);
  } catch (error) {
    app!.insertAdjacentHTML(
      'beforeend',
      `<pre style="color:#e07a5f">数据加载失败：${String(error)}</pre>`
    );
  }
}

void boot();
