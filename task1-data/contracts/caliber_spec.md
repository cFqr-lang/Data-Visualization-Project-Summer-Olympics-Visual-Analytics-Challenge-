# 口径说明书（caliber_spec）

| 项目 | 内容 |
| --- | --- |
| 版本 | v1.2（冻结） |
| 日期 | 2026-11-24 |
| 负责人 | 任务一 |
| 数据 | `olympics_dataset.csv`，252,565 行 × 11 列 |
| 适用范围 | 任务二、任务三、任务四全部图表与正文数字 |
| 状态 | 冻结；如需变更，提交“口径变更单”并列出受影响图表 |

> 本文件是跨任务唯一口径依据。任务二、任务三不得自行重定义小项或奖牌口径；图表标题、图注、正文数字必须与本文件一致。

## 1. 数据总体

| 指标 | 数值 |
| --- | --- |
| 参赛记录 | 252,565 行（一行 = 一名运动员 × 一届 × 一个小项） |
| 字段 | 11 列；缺失值 0；Season 恒为 Summer |
| 届次 | 31 个年份（30 届官方 + 1906 届间奥运会） |
| 主办城市 | 23 个；1956 年同时有墨尔本与斯德哥尔摩 |
| NOC | 234 个（157 个曾获奖，77 个从未获奖） |
| Team | 1,193 个；2,795 行带 `-数字` 分队后缀，43 行混合队 |
| Sport | 76 个原始取值 → 57 个归一后大类 |
| Event | 1,041 个原始取值，其中 6,488 行为泛化值 |
| 奖牌行 | 38,818 行（金 13,002 / 银 12,746 / 铜 13,070） |

## 2. 清洗数据契约（`data/processed/olympics_clean.parquet`）

### 2.1 冻结字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `sport_norm` | string | 2020 年前后大类漂移归一后的体育大类，共 57 类 |
| `event_key` | string | 小项唯一键：`届次|原始 Sport|Event`；泛化值追加性别（Mixed 除外） |
| `event_key_quality` | string | `specific` / `generic`；`generic` 即 2020+ 泛化小项 |
| `is_team_event` | int | 是否团体项目：同届同小项同奖牌同 NOC 超过 1 行即为 1 |
| `is_1906` | int | 是否 1906 届间奥运会 |
| `include_flag` | int | 是否纳入默认分析：`is_1906 == 0` 时为 1 |
| `is_medal` | int | 是否奖牌行（Gold/Silver/Bronze） |
| `medal_rank` | int | 金 1、银 2、铜 3、无奖牌 0 |
| `noc_modern` | string | 政体继承口径的现代 NOC；默认分析**不使用** |
| `athlete_key` | string | 近似运动员实体：`Name|Sex|NOC`；仅供探索，不是官方 ID |

### 2.2 辅助字段

`sport_raw`、`sport_all`、`is_multi_sport`、`event_raw`、`event_name_clean`、`event_granularity`、`is_1956_stockholm`、`is_refugee`、`noc_name`、`team_base`。

### 2.3 派生说明

- `event_key_quality` 与 `event_granularity` 一一对应：`generic` ↔ `coarse`，`specific` ↔ `fine`。
- `is_team_event` 由数据本身推断，不用项目名单硬编码；接力、足球、篮球、赛艇等会被正确标记，个别重复录入可能误判。
- `include_flag = 1` 是默认分析集；`1906` 只用于敏感性分析。

## 3. 奖牌口径

### 3.1 口径 A：运动员行口径

**定义**：每条 `Medal ∈ {Gold, Silver, Bronze}` 的记录计 1 枚，团体项目每位成员各计 1 枚。

**结果**：含 1906 为 38,818 枚；`include_flag == 1` 为 38,360 枚。

**适用**：参赛人数、获奖人数、女性参与、团体项目贡献。

**禁止**：不得用于历史总奖牌榜或与官方数字直接对比。2024 年美国为 131 个金牌行、荷兰 67 个，官方为 40、15。

### 3.2 口径 B：小项口径（strict / NOC-aware 两版）

**strict 版**：以 `Year + event_key + Medal` 为唯一键去重，同届同小项同颜色只计 1 枚；双铜牌与并列压成 1 枚。含 1906 为 17,452 枚，剔除 1906 为 17,233 枚；2024 年为 969 个奖牌单位。保留作“每色计 1”的敏感性分析，不单独作为历史总榜。

**NOC-aware 版（推荐总榜）**：键为 `Year + event_key + Medal + NOC`，每个获奖 NOC 各计 1 枚。含 1906 为 18,159 枚，剔除 1906 为 17,935 枚；2024 年为 1,027 个奖牌单位、325 金。适用于历史总榜、逐届榜、与官方及任务二对接。

**两版共有**：2024 年 328 个有奖牌记录的小项、325 个有金牌记录；美国 39、中国 40、荷兰 15（官方 40 / 40 / 15）。

**与任务二的接口**：任务二保守口径为 2,757，NOC-aware 表为 2,756，差 1 来自任务二额外做了 Sport 归并；引用总量时须注明。

**已知偏差**：

- 2024 年铁人三项混合接力整项无奖牌行；
- 2020 年游泳 `Relay Only Athlete` 只能支撑“项目×性别”粒度。

### 3.3 口径选择矩阵

| 场景 | 口径 | 是否含 1906 |
| --- | --- | --- |
| 历史总奖牌榜 / 逐届奖牌榜 | 小项口径（NOC-aware） | 否（脚注做敏感性） |
| 参赛人数 / 获奖人数 / 女性参与 | 运动员行口径 | 否 |
| 团体项目贡献 / 运动员故事 | 运动员行口径 | 否 |
| 2020 前后连续对比 | 小项口径，项目层用 `sport_norm` | 否 |
| 与官方数字对话 | 小项口径（NOC-aware）+ `known_gaps.csv` | 否 |

## 4. 体育大类归一

映射文件：`task1-data/contracts/sport_map.csv`（76 行）。

| 规则 | 示例 |
| --- | --- |
| 拆分合并 | Artistic Gymnastics→Gymnastics；Cycling Road/Track/MTB/BMX→Cycling；Canoe Sprint/Slalom→Canoeing |
| 更名统一 | Synchronized/Artistic Swimming→Artistic Swimming；Equestrian→Equestrianism；Trampolining→Trampoline Gymnastics |
| 同类合并 | Baseball/Softball→Baseball/Softball；3x3 Basketball→Basketball |
| 逗号拆分 | 89 行逗号拼接按逗号拆开；`sport_all` 保存全部项目，主项目取第一个 |

- 76 个原始取值 → 57 个大类，20 个原始取值被改写。
- 89 行逗号拼接全部在 2024 年、全部无奖牌；其中 54 行为真正跨项。
- 2020/2024 原始取值 46/50 个，归一后 40/39 个；新增项目（滑板、冲浪、霹雳舞等）属真实新增，不合并。

## 5. Event 泛化处理

- 泛化值：`Men`、`Women`、`Men Team`、`Women Team`、`Mixed Team`、`Open`、`Relay Only Athlete`。
- 规模：6,488 行（2.6%），2020 年占该届 20.1%，2024 年占 23.1%；含奖牌行 1,473 行。
- 处理：不改写原文；`event_key_quality = generic`；`event_key` 对非 Mixed 泛化值追加 `Sex`。
- 使用限制：跨 2020 的连续序列一律在 `sport_norm` 层；小项层只用 `event_key_quality == 'specific'`，或明确标注“项目×性别”粒度。

## 6. 特殊记录

| 对象 | 数据量 | 默认处理 | 备选 |
| --- | --- | --- | --- |
| 1906 届间奥运会 | 1,733 行 / 458 奖牌 | `include_flag = 0`，主口径剔除 | 敏感性分析纳入（奖牌行 +458，约 +1.18%） |
| 1956 斯德哥尔摩 | 298 行马术 | 并入 1956 墨尔本，`is_1956_stockholm = 1` | — |
| URS / EUN / ROC | 4,622 / 650 / 561 行 | 保留历史 NOC | `noc_modern = RUS`（需在图注声明） |
| GDR / FRG / SAA | 2,104 / 2,558 / 93 行 | 保留历史 NOC | `noc_modern = GER` |
| TCH / YUG / SCG | 3,369 / 2,046 / 300 行 | 保留历史 NOC（继承国会低估其他共和国） | 可选 `CZE` / `SRB` |
| AIN / EOR / IOA | 46 / 79 / 93 行 | 保留独立，EOR 单列 | 不并入任何国家 |

规则文件：`task1-data/contracts/noc_map.csv`（234 行全量，含 `merge_type` 与 `note`）。

## 7. 2024 年已知记录缺失

`task1-data/contracts/known_gaps.csv`：

| 小项 | 缺失 | 官方获得者 |
| --- | --- | --- |
| 女子公路自行车赛 | 金牌、铜牌行 | Kristen Faulkner (USA) / Lotte Kopecky (BEL) |
| 男子山地自行车越野 | 金牌行 | Tom Pidcock (GBR) |
| 男子 800 米自由泳 | 金牌、铜牌行 | Daniel Wiffen (IRL) / Gregorio Paltrinieri (ITA) |
| 铁人三项混合接力 | 整项无奖牌行 | 德国队金牌 |

因此：2024 年小项口径 328/329 个小项、325 个有金牌；美国 39/40、德国 11/12、中国 40/40、荷兰 15/15。**任何涉及 2024 的图表必须标注该缺口，不得把缺失当成 0。**

## 8. 质量检查摘要

完整 11 项见 `task1-data/contracts/quality_checks.csv`；可复现代码见 `task1-data/pipeline/`，交付前断言见 `04_validate.py`。

| 编号 | 检查 | 结果 | 处理 |
| --- | --- | --- | --- |
| Q1 | 结构与缺失 | 252,565 × 11；缺失 0 | 不插补 |
| Q2 | 取值域/编码 | Sex 2 值、Medal 4 值、Year 31 个；姓名 0 行非 ASCII | 保留原值，声明变音符号被剥离 |
| Q3 | 团体/并列重复 | 5,188 组、26,554 行（68.4%，含 1906；剔除 1906 为 5,140 组 / 26,267 行） | 双口径 |
| Q4 | 奖牌守恒 | 金 13,002 / 银 12,746 / 铜 13,070；34 个小项仅 1 种奖牌 | 不补齐 |
| Q5 | Sport 漂移 | 76→57；89 行逗号拼接 | 映射表 |
| Q6 | Event 泛化 | 6,488 行（2.6%） | `event_key_quality` 标记 |
| Q7 | 姓名/ID | 235,903 个 ID（1.071 行/ID）；52,544 个姓名多 ID | 不建个体 ID，提供近似实体 |
| Q8 | NOC/Team | 234 NOC / 1,193 Team；2,795 行分队后缀 | 国家一律 NOC |
| Q9 | 特殊届次/政体 | 1906 / 1956 / EOR / ROC / AIN | 第 6 节规则 |
| Q10 | 2024 小项数 | 328 个有奖牌记录、325 个有金牌 | 差异清单 |
| Q11 | 2024 记录完整性 | 4 项缺失 | `known_gaps.csv` |

## 9. 共享指标（`task1-data/metrics/`）

| 文件 | 内容 | 口径 |
| --- | --- | --- |
| `medal_table_event_noc_aware.csv` | 国家历史总奖牌榜（推荐） | 小项 NOC-aware，剔除 1906 |
| `medal_table_event_noc.csv` | 国家历史总奖牌榜（strict 版） | 小项每色计 1，剔除 1906；仅做敏感性对比 |
| `medal_table_athlete_noc.csv` | 国家历史总奖牌榜 | 运动员行，剔除 1906 |
| `medals_by_year_noc.csv` | 逐届国家奖牌（长表） | 小项，剔除 1906 |
| `participation_by_year.csv` | 逐届行数、运动员数、NOC 数、女性占比 | 行口径，剔除 1906 |
| `sport_coverage_by_year.csv` | 逐届项目参赛规模与小项数 | 行口径，剔除 1906 |
| `caliber_by_year.csv` | 双口径分年差异 | 全部 |
| `caliber_2024_compare.csv` | 2024 双口径与官方锚点 | 全部 |

报告正文的数字只能引用上述表，不得自行从原始行重算。

## 10. 使用约定（给任务二、三、四）

1. 统一过滤 `include_flag == 1`；1906 只做脚注或敏感性。
2. 国家用 `NOC`，绝不用 `Team`；项目用 `sport_norm`，不用原始 `Sport`。
3. 每幅图 `meta` 必须写：`caliber`、`denominator`、`includes_1906`、`event_key_quality`。
4. 2024 图表引用 `known_gaps.csv` 并标注缺口。
5. 不做个体排名；如必须做，使用 `athlete_key` 并声明“近似实体”。
6. strict 小项口径总奖牌 969 不与官方总数比较，只比金牌；历史总榜统一用 NOC-aware 表（2024 年为 1,027）。
7. 政体继承默认关闭；启用时在标题与图注声明。
8. 发现口径问题，开 Issue 并通知任务一，不得自行改数。
9. 历史总量与任务二对接用 `medal_table_event_noc_aware.csv`；`medal_table_event_noc.csv` 只做“每色计 1”的敏感性对比。

## 11. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| v1.0 | 2026-11-23 | 初版：双口径、Sport 归一、Event 泛化、特殊记录 |
| v1.1 | 2026-11-23 | 修正 3x3 篮球与五人篮球同键合并、混合团体按性别拆键；新增 2024 年 4 项缺失清单与 234 个 NOC 全量映射 |
| v1.2 | 2026-11-24 | 新增 NOC-aware 小项榜（含 1906 18,159 / 剔除 17,935）；图 1 注释修正为美国 39/40；Q3 统一为 5,188 组 / 26,554 行（剔除 1906 为 5,140 / 26,267）；Q5 表述与代码对齐；校验脚本扩至 21 项 |

## 12. 复现

```bash
python task1-data/pipeline/01_audit.py
python task1-data/pipeline/01b_extra.py
python task1-data/pipeline/02_clean.py
python task1-data/pipeline/03_figures.py
python task1-data/pipeline/04_validate.py
python task1-data/pipeline/05_build_spec.py
python task1-data/pipeline/06_build_answer.py
```

脚本编号：`01_audit`、`01b_extra`、`02_clean`、`03_figures`、`04_validate`、`05_build_spec`、`06_build_answer`。
