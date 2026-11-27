# task4-bonus · 任务四：开放创作（加分）

负责人：任务四成员。

## 三种可选方向

| 方向 | 复用任务二的内容 | 新增内容 |
| --- | --- | --- |
| 交互 Dashboard | 站点底座、图表组件、JSON | `/explore` 路由、筛选与联动 |
| 2028 预测 | `fact_medal_event`、历史序列图壳 | `/forecast` 路由、模型、区间、回测 |
| 数据新闻 | 章节骨架、组件、文案模板 | 叙事网页或信息长图 |

## 约定

- 不另建第二个站点，统一在 `task2-visual/site/` 中加路由；
- 预测必须写清方法、假设、不确定性区间与验证方式；
- 口径与任务二一致，图表冻结后不得擅自修改；
- 新增数据契约放在 `contracts/`，并请任务二 review。

## 已交付：离线单文件交互 Dashboard

`build_dashboard.py` 读取 `data/raw/olympics_dataset.csv`，生成 `olympics_dashboard.html`
（4.9MB 单文件，内联 plotly.js，双击即可离线打开；6 个 Tab / 11 张图）。使用说明见 `DASHBOARD_README.md`。

路径规则（P0-1）：只在「仓库 `data/raw/`」与「脚本同目录」查找 CSV，找不到直接抛出
`FileNotFoundError` 并列出已搜索路径，不回退到任何本机绝对路径。

## 图资产：`exports/` 与契约表 Fig.4-1 ~ Fig.4-11

| 图号 | chart_id | 文件名 | 内容 |
| --- | --- | --- | --- |
| Fig.4-1 | A1 | `Fig4-1_A1_dual-caliber` | 逐届奖牌数双口径对比 |
| Fig.4-2 | A2 | `Fig4-2_A2_top20` | 历史总奖牌榜 Top20 |
| Fig.4-3 | A3 | `Fig4-3_A3_inflation` | 奖牌膨胀三轴扩张 |
| Fig.4-4 | B1 | `Fig4-4_B1_twelve-nations` | 12 国逐届轨迹 |
| Fig.4-5 | B2 | `Fig4-5_B2_bloc-evolution` | 政体变迁谱系 |
| Fig.4-6 | C1 | `Fig4-6_C1_female-ratio` | 女性参赛/奖牌占比双弧线 |
| Fig.4-7 | C2 | `Fig4-7_C2_female-top15` | 女性奖牌 Top15 |
| Fig.4-8 | D1 | `Fig4-8_D1_event-growth` | 项目演化规模 |
| Fig.4-9 | D2 | `Fig4-9_D2_vanished-added` | 消失 vs 新增项目 |
| Fig.4-10 | E1 | `Fig4-10_E1_host-pulse` | 东道主效应脉冲 |
| Fig.4-11 | E2 | `Fig4-11_E2_small-nocs` | 小代表团突破 |

- PNG：`exports/png/<文件名>_4x.png`（deviceScaleFactor=4，4800~5600px 宽）
- SVG：`exports/svg/<文件名>.svg`（矢量，`<svg class="main-svg">`）
- 登记：`contracts/figure_registry.csv` 与 `contracts/figure_caliber_matrix.csv` 的 11 行，`owner=task4`、`status=done`

### 复现导出（不使用 kaleido）

kaleido 的内置 chromium 在本机反复崩溃（`Network service crashed`），故改用
plotly.js 客户端渲染 + 浏览器无头导出：

```bash
python tools/export_figures.py     # 1. 为 11 张图各生成一个内联 plotly.js 的独立 HTML（tools/_figs/）
npm install puppeteer-core         # 2. 首次执行（需本机已安装 Edge 或 Chrome）
node tools/export_figures.js       # 3. 输出 exports/png/*_4x.png 与 exports/svg/*.svg
```

注意：`Plotly.toImage(format="svg")` 返回的 data URI 是 **URL-encoded**，需用
`decodeURIComponent` 解码；只有 PNG 的 data URI 是 base64。用 base64 解 SVG 会得到损坏文件。
