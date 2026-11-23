# 百年圣火 · 夏季奥运会可视分析

> 「数说奥运 · 1896–2024」夏季奥运会可视分析挑战赛 · 团队协作仓库

本仓库承载四个任务的代码、数据契约、图表资产与文档。原始数据不入库，图表统一使用 Apache ECharts 实现。

## 团队分工

| 任务 | 内容 | 负责人 | 主要目录 |
| --- | --- | --- | --- |
| 任务一 | 数据体检与口径定义 | 待填 | `task1-data/` |
| 任务二 | 百年奥运全景 | 待填 | `task2-visual/` |
| 任务三 | 专题深挖 | 待填 | `task3-insights/` |
| 任务四 | 开放创作（加分） | 待填 | `task4-bonus/` |
| 统筹 | 报告总装、海报、视频、提交 | 待填 | `docs/`、`poster/` |

GitHub 用户名、仓库角色与分支保护规则见 [docs/team-permissions.md](docs/team-permissions.md)。

## 仓库结构

```text
.
├─ docs/                     赛题、任务二方案、团队权限
├─ contracts/                口径、图表矩阵、异常线索、图号登记
├─ data/
│  ├─ raw/                   原始 CSV（不入库）
│  └─ processed/             清洗后数据（不入库，走 Release/网盘）
├─ shared/
│  └─ metrics/               全队共用的聚合指标表
├─ task1-data/               任务一：清洗、体检、口径
├─ task2-visual/             任务二：ECharts 站点、管线、图表资产
│  ├─ pipeline/              Python 预聚合
│  ├─ site/                  Vite + TypeScript + ECharts
│  ├─ exports/               PNG / SVG 图资产
│  ├─ report/                图注与解读
│  ├─ video/                 视频分镜
│  └─ poster/                海报主图
├─ task3-insights/           任务三：专题深挖
├─ task4-bonus/              任务四：Dashboard / 预测 / 数据新闻
├─ scripts/                  仓库配置与校验脚本
└─ .github/                  CODEOWNERS、PR / Issue 模板
```

> [docs/任务二方案.md](docs/任务二方案.md) 中的 `olympics-story/` 对应本仓库的 `task2-visual/`。

## 快速开始

### 1. 获取数据

赛题原始数据不随仓库提交。请从赛题指定渠道获取 `olympics_dataset.csv`，放到：

```text
data/raw/olympics_dataset.csv
```

该路径已被 `.gitignore` 忽略，不会被误提交。

### 1.1 任务一：体检与口径（已交付）

任务一是自包含目录：代码、契约、指标底表、说明书与答卷都在 `task1-data/`。运行方式、产物清单与口径速览见 [task1-data/README.md](task1-data/README.md)。

- 清洗数据：`data/processed/olympics_clean.parquet`（不入库，走 Release/网盘）
- 口径说明书：`task1-data/contracts/caliber_spec.md`（v1.1，冻结）
- 共享指标：`task1-data/metrics/`
- 2024 缺口清单：`task1-data/contracts/known_gaps.csv`

### 2. Python 环境

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r task1-data/requirements.txt
```

依赖文件由任务一提供；任务二管线只读取 `data/processed/` 下的清洗产物。

### 3. 任务二站点

```bash
cd task2-visual/site
npm install
npm run dev
```

### 4. 生成图表数据与报告图

```bash
python -m task2-visual.pipeline.build --caliber conservative_event --exclude-1906
npm run --prefix task2-visual/site export:figures
```

具体命令以 `task2-visual/README.md` 为准。

## 协作流程

- `main` 为保护分支，禁止直接推送；所有改动走 Pull Request，至少 1 人审批。
- 分支命名：`feat/t1-*`、`feat/t2-*`、`feat/t3-*`、`feat/t4-*`、`fix/*`、`docs/*`。
- 口径变更必须由任务一确认，并在 `task1-data/contracts/` 更新说明与受影响图表清单。
- 图表冻结后，任何人不得擅自改口径；如需变更，回到任务一走变更流程。
- 原始数据、清洗后大文件、视频原片、`.env` 和密钥不得提交。
- 提交前检查 `git status`，确认没有把 `data/raw/olympics_dataset.csv` 加入暂存区。

## 数据与许可

- 数据来源：Kaggle *Summer Olympics Medals (1896–2024)* 及其上游数据集。
- 数据许可：CC BY-NC-SA 4.0（署名—非商业性—相同方式共享）。
- 本仓库作品仅用于参赛，不得用于商业用途。
- 与 IOC 官方奖牌榜对比时，必须注明统计口径。

## 文档索引

- [赛题介绍](docs/赛题介绍.md)
- [任务二方案](docs/任务二方案.md)
- [团队权限与分支保护](docs/team-permissions.md)
- [协作文档说明](contracts/README.md)
- [海报参考模板](docs/海报参考模板.md)
