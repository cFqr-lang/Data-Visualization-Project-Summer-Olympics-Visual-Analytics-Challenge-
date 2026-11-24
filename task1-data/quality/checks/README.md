# 数据质量检查（quality/checks）

任务一提供 11 项可复现检查；本目录提供一个最小复现脚本，完整结果在 `task1-data/contracts/quality_checks.csv`。

## 运行

```bash
python task1-data/quality/checks/run_checks.py
```

6 项核心检查（结构、缺失、奖牌守恒、重复组、Event 泛化、姓名编码）全部 PASS 才返回 0。

## 11 项检查与代码位置

| 编号 | 检查项 | 代码位置 | 结果 |
| --- | --- | --- | --- |
| Q1 | 结构与缺失值 | `pipeline/01_audit.py` | 252,565 × 11；缺失 0 |
| Q2 | 字段取值域/编码 | `pipeline/01_audit.py` | Sex 2 值、Medal 4 值；姓名 0 行非 ASCII |
| Q3 | 团体/并列重复 | `pipeline/01_audit.py` | 5,188 组、26,554 行（68.4%，含 1906；剔除 1906 为 5,140 组 / 26,267 行） |
| Q4 | 奖牌守恒 | `pipeline/01_audit.py` | 金 13,002 / 银 12,746 / 铜 13,070；34 个小项仅 1 种奖牌 |
| Q5 | Sport 漂移/逗号 | `pipeline/02_clean.py` | 76 → 57；89 行逗号拼接 |
| Q6 | Event 泛化 | `pipeline/02_clean.py` | 6,488 行（2.6%）；2020 20.1%、2024 23.1% |
| Q7 | 姓名/player_id | `pipeline/01_audit.py` | 235,903 个 ID（1.071 行/ID）；52,544 个姓名多 ID |
| Q8 | NOC/Team | `pipeline/01_audit.py` | 234 NOC / 1,193 Team；2,795 行分队后缀 |
| Q9 | 特殊届次/政体 | `pipeline/01b_extra.py`、`02_clean.py` | 1906 / 1956 / EOR / ROC / AIN 规则 |
| Q10 | 2024 小项数 | `pipeline/02_clean.py` | 328 个有奖牌记录、325 个有金牌 |
| Q11 | 2024 记录完整性 | `pipeline/02_clean.py` | 4 项缺失，见 `task1-data/contracts/known_gaps.csv` |

交付前断言：`python task1-data/pipeline/04_validate.py`（21 项，全部 PASS）。
