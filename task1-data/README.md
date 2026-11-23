# task1-data · 数据体检与口径定义

任务一交付：数据体检、双口径、Sport 归一、Event 泛化处理、特殊记录规则、11 项质量检查。

## 产物与仓库位置

| 仓库位置 | 内容 |
| --- | --- |
| `data/processed/olympics_clean.parquet` | 清洗后全量数据（252,565 行 × 31 列，不入库） |
| `contracts/caliber_spec.md` | 口径说明书 v1.1（冻结） |
| `contracts/sport_map.csv` | 76 项 Sport 归一映射 |
| `contracts/noc_map.csv` | 234 个 NOC 全量映射（20 条特殊规则） |
| `contracts/known_gaps.csv` | 2024 年 4 项已知记录缺失 |
| `contracts/quality_checks.csv` | 11 项质量检查结果 |
| `shared/metrics/*.csv` | 报告统一底表（奖牌榜、逐届、参与度、项目覆盖） |
| `task1-data/output/` | 中间产物（CSV、日志，不入库） |
| `task1-data/figures/` | 5 张诊断图（说明书用） |
| `task1-data/docs/数据质量与口径说明书.docx` | 任务一说明书（16 表 + 5 图） |
| `task1-data/submission/数说奥运_答卷_任务一填写版.docx` | 答卷模板第 Ⅰ 节填写版 |
| `task1-data/template/数说奥运_答卷模板.docx` | 官方答卷模板（复现用） |
| `task1-data/quality/checks/` | 质量检查可复现脚本与说明 |

## 冻结字段

| 字段 | 说明 |
| --- | --- |
| `sport_norm` | 2020 年前后大类漂移归一后的体育大类（57 类） |
| `event_key` | 小项唯一键：`届次|原始 Sport|Event`，泛化值追加 Sex（Mixed 除外） |
| `event_key_quality` | `specific` / `generic`，标记 2020+ 泛化 |
| `is_team_event` | 是否团体项目（同小项同牌同 NOC 多行） |
| `is_1906` | 是否 1906 届间奥运会 |
| `include_flag` | 是否纳入默认分析（`is_1906 == 0`） |

其余字段见 `contracts/caliber_spec.md` 第 2 节。

## 运行

```bash
python task1-data/pipeline/01_audit.py
python task1-data/pipeline/01b_extra.py
python task1-data/pipeline/02_clean.py
python task1-data/pipeline/03_figures.py
python task1-data/pipeline/04_validate.py
python task1-data/pipeline/05_build_spec.py
python task1-data/pipeline/06_build_answer.py
```

原始数据放 `data/raw/olympics_dataset.csv`，只读；重复运行结果一致。`04_validate.py` 共 18 项断言，全部 PASS 才退出 0。

## 口径速览

- 运动员行口径：38,818 枚（金 13,002 / 银 12,746 / 铜 13,070），剔除 1906 为 38,360。
- 小项口径：17,452 枚，剔除 1906 为 17,233；2024 年为 328 个有奖牌记录小项、325 个有金牌小项。
- 2024 官方锚点：美国 40、中国 40、荷兰 15；本数据小项口径为 39 / 40 / 15，美国差 1 由女子公路赛金牌行缺失解释。

## 变更

口径变更必须更新 `contracts/caliber_spec.md`，并在 `contracts/` 中说明受影响图表，再通知任务二、三、四。
