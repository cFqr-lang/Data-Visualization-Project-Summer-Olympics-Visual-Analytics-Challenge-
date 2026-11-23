# contracts · 跨任务契约

本目录存放四个任务共同依赖的契约文件。任何改动都可能影响他人，修改前请先开 Issue 或在 PR 中说明。

## 文件与归属

| 文件 | 内容 | 负责人 | 说明 |
| --- | --- | --- | --- |
| `caliber_spec.md` | 口径说明书（v1.1 已交付） | 任务一 | 奖牌口径、1906、政体谱系、Event 泛化处理 |
| `sport_map.csv` | 体育大类归一映射（76 项） | 任务一 | 2020 前后 Sport 漂移的归一规则 |
| `noc_map.csv` | NOC 全量映射（234 项） | 任务一 | 历史政体、难民队、独立参赛者的处理规则 |
| `known_gaps.csv` | 2024 年已知记录缺失（4 项） | 任务一 | 涉及 2024 的图表必须引用 |
| `quality_checks.csv` | 数据质量检查（11 项） | 任务一 | 检查结果与处理决定 |
| `figure_caliber_matrix.csv` | 图表-口径矩阵 | 任务二 | 每幅图的口径、分母、是否含 1906 |
| `figure_registry.csv` | 图号与图资产登记 | 任务二 | 报告、海报、站点引用同一图号 |
| `anomaly_leads.csv` | 异常线索与假设 | 任务二 | 任务三选题的结构化菜单 |
| `claim_registry.csv` | 结论主张登记（待创建） | 任务二 + 任务三 | 防止同一结论两处重复主张 |

## 规则

1. 任务二只消费任务一的 `caliber_spec.md` 与 `event_key`，不自行重定义小项。
2. 任何口径变更必须由任务一确认，并在 `figure_caliber_matrix.csv` 中更新受影响图表。
3. 每幅图的 JSON `meta` 必须与本目录的矩阵一致；不一致时构建失败。
4. `anomaly_leads.csv` 的每条线索必须能由 `evidence_query` 复现。
5. 报告正文的数字只能引用 `shared/metrics/` 下的统一底表。
6. 修改他人负责的文件前，先在 PR 中说明理由并请求对应负责人 review。

## 关联文档

- [任务二方案](../docs/任务二方案.md)
- [团队权限](../docs/team-permissions.md)
- [赛题介绍](../docs/赛题介绍.md)
