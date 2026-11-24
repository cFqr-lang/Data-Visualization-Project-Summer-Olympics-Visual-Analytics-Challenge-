# task3-insights · 任务三：专题深挖

负责人：任务三成员。本期完成三个专题：**S1 东道主效应**、**S3 地缘政治的投影**、**S5 奖牌的通货膨胀**。
图表统一使用 **Apache ECharts**（与任务二一致），数据管线只产出聚合 JSON，渲染与导出由 `site/render.mjs` 完成。

## 结论一句话

- **S1**：主场加成真实、显著但是一场脉冲——主办届指数冲到基准的 163%，下一届即回落至 112%；机制主要是“多派人参赛”（中位规模 +60%）而非“单位投入夺牌更多”（中位效率 -10%）。
- **S3**：奖牌榜是地缘政治的投影——苏联一脉从 195 枚跌到 5 枚，两德分立并互相缺席对方主场，东德 5 届 409 枚是效率奇迹。
- **S5**：奖牌通胀是扩容型而非宽松型——总量 8.6 倍但每千条参赛记录奖牌只剩 22%，获奖国家 10→92，头部份额被稀释。

## 交付物

- `pipeline/host_effect.py` / `geopolitics.py` / `inflation.py`：三个专题的数据管线（复用任务二口径，只产出 JSON/CSV）；
- `data/*.json` 与 `data/host_effect_summary.csv`：测算底表与 ECharts 可复用聚合数据；
- `site/render.mjs`：ECharts 渲染脚本（SSR 出 SVG + Edge 出 PNG@4x）；
- `exports/Fig3-1 … Fig3-10.png / .svg`：报告用图资产（浅色印刷主题）；
- `report/findings.md`（S1）、`findings_s3.md`、`findings_s5.md`：摘要、口径方法、每图图注与 ≥100 字解读、结论与局限。

## 复现

```bash
python task3-insights/pipeline/host_effect.py   # S1 → data/host_effect_data.json
python task3-insights/pipeline/geopolitics.py   # S3 → data/geopolitics_data.json
python task3-insights/pipeline/inflation.py     # S5 → data/inflation_data.json

cd task3-insights/site
pnpm install                                   # 或 npm install
node render.mjs                                # 生成 exports/ 的 PNG@4x 与 SVG
```

依赖：任务二的 `data/raw/olympics_dataset.csv` 已就位，`task2-visual/pipeline/common.py`、`metrics.py` 可导入；渲染需要 Node ≥20 与本地 Edge（`render.mjs` 内 `EDGE` 路径可调）。

## 口径

- 主口径 `conservative_event`，对照 `athlete_row`，1906 排除——与任务二完全一致；
- 基准 = 主办届前后各两届奖牌均值（对称窗口，吸收线性趋势）；
- 零分布 = 全部非东道国（届次 × 国家）的对称波动，n=6,970。

## 契约登记

- 主张：`contracts/claim_registry.csv`（T3-S1-C1…C4、T3-S3-C1…C3、T3-S5-C1…C3）；
- 线索：`contracts/anomaly_leads.csv` 新增 S1/S3/S5 线索共 7 条，`status = verified`；
- 图资产：`contracts/figure_registry.csv` 与 `contracts/figure_caliber_matrix.csv` 已回填 Fig.3-1…Fig.3-10。
