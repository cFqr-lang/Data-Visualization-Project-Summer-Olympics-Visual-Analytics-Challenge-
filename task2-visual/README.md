# task2-visual · 任务二：百年奥运全景

负责人：任务二成员。完整设计见 [docs/任务二方案.md](../docs/任务二方案.md)。

## 交付物

- `pipeline/`：Python 预聚合，输出图表 JSON 与 `shared/metrics/`；
- `site/`：Vite + TypeScript + Apache ECharts 数据故事站（8 图，含 B2 / D2）；
- `exports/`：8 幅 PNG@4x 与 SVG，命名见 `contracts/figure_registry.csv`；
- `offline/olympics-story.offline.html`：单文件离线包（约 1.1 MB，无网络可打开）；
- `report/`：图注、≥100 字解读、复现命令；
- `video/`：90 秒视频分镜；
- `poster/`：3 张海报主图 + 主标题数据。

## 图表优先级

- P0：A1 双口径总榜、A2 逐届演变、B1 九国矩阵、C1 女性双弧线、C2 参与≠产出、D1 项目生命线；
- P1：B2 国家效率前沿、D2 项目结构变迁；
- P2：X1 国家×项目矩阵、X2 项目性别差哑铃。

## 常用命令

```bash
python -m pipeline.build            # 生成图表 JSON + 底表，并自动自检
python -m pipeline.build --check-only
cd site && npm install && npm run dev
npm run build                       # tsc + vite
npm run export:figures              # 需先运行 dev；导出 8 幅 PNG@4x + SVG
npm run build:offline               # 生成 offline/olympics-story.offline.html
npm run export:figures -- A2 D1     # 只重导指定图
```

## 数据接口（供任务三 / 任务四复用）

| 路径 | 内容 |
| --- | --- |
| `site/public/data/meta.json` | 数据版本、自检结果、总量、口径字典 |
| `site/public/data/index.json` | 图号 → JSON 路径清单 |
| `site/public/data/figures/fig-*.json` | 每图 `meta` + 数据段 |
| `shared/metrics/metrics_master.csv` | 全队唯一数字底表 |

每份 `fig-*.json` 的 `meta` 字段固定：`figure_id`、`chart_id`、`title`、`caliber`、`caliber_label`、`denominator`、`includes_1906`、`data_version`、`generated_at`、`source`、`event_key_source`、`notes`。

数据段按图：A1 `totals_top20` / `definitions` / `rank_changes`；A2 `series` / `bar_race` / `snapshots`；B1 `panels`；B2 `points`；C1 `series` / `milestones`；C2 `views`；D1 `sports` / `event_counts` / `highlights`；D2 `categories` / `river` / `totals`。

底表列：`metric, scope, year, noc, value, unit, caliber, includes_1906, data_version, notes`。
报告正文数字请先查底表，避免各图表口径打架。

### 与任务一的口径衔接

当前 `event_key` 由任务二按 `(Sport, Event)` 自算，`meta.event_key_source = task2_fallback`。
任务一交付 `data/processed/athletes_normalized.csv` 后，只需替换 `pipeline/common.py::load_records`，输出结构不变。
任务一未就绪时，本目录不定义也不改写口径，只做回退适配。

### 前端复用

`site/src/types.ts` 是上述 JSON 的 TypeScript 类型，可直接 import；图表组件在 `site/src/charts/`，均只依赖 `echarts`。
每个组件同时导出纯函数 `buildOption(payload)`（A1 为 `barOption` / `slopeOption`），任务四可在自己的主题下复用同一份 option。

### 导出与离线

- `site/export.html?chart=A1&renderer=canvas|svg&theme=print|dark` 是单图导出页；`scripts/export-figures.mjs` 用本机 Edge + puppeteer-core 批量截图与取 SVG，浅色主题由 `src/export.ts` 做色值重映射。
- `scripts/build-offline.mjs` 把 `dist` 的 JS/CSS 与 `public/data` 全部 JSON 内联，`main.ts` 优先读 `window.__OLYMPICS_DATA__`，因此 `file://` 直接打开可用。

## 约束

- 所有图表必须使用 Apache ECharts；
- 每幅图必须声明口径、分母、是否含 1906；
- 站点深色主题，PDF/海报使用浅色主题；
- 不提交原始数据与大体积导出中间产物。
