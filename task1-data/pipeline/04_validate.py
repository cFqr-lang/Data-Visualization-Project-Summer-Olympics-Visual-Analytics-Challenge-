# -*- coding: utf-8 -*-
"""任务一交付前的自动校验：逐项断言，全部通过才返回 0"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "olympics_dataset.csv"
OUT = ROOT / "task1-data" / "output"
PROC = ROOT / "data" / "processed"
CONTRACTS = ROOT / "task1-data" / "contracts"

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS" if cond else "FAIL"), "|", name, "|", detail)


raw = pd.read_csv(RAW, low_memory=False)
clean = pd.read_csv(OUT / "olympics_clean.csv", low_memory=False)
rows = pd.read_csv(OUT / "medals_athlete_row.csv", low_memory=False)
ev = pd.read_csv(OUT / "medals_event_level.csv", low_memory=False)
ev_tbl = pd.read_csv(OUT / "medal_table_event_noc_ex1906.csv", index_col=0)
ev_noc_tbl = pd.read_csv(OUT / "medal_table_event_noc_aware_ex1906.csv", index_col=0)
noc_map = pd.read_csv(OUT / "noc_mapping.csv")
ath = pd.read_csv(OUT / "athlete_top_medals.csv")

check("原始数据行列为 252,565 × 11", raw.shape == (252565, 11), str(raw.shape))
check("原始数据无缺失值", int(raw.isna().sum().sum()) == 0, str(int(raw.isna().sum().sum())))
check("奖牌行 38,818", len(rows) == 38818, str(len(rows)))
check("金/银/铜 13,002 / 12,746 / 13,070",
      [int((rows["Medal"] == m).sum()) for m in ["Gold", "Silver", "Bronze"]] == [13002, 12746, 13070])
check("清洗后行数不变（只增列）", len(clean) == 252565, str(len(clean)))
check("清洗后列数 31", clean.shape[1] == 31, str(clean.shape[1]))
check("契约字段 event_key_quality 取值合法",
      set(clean["event_key_quality"].unique()) <= {"specific", "generic"})
check("include_flag 与 is_1906 互补",
      int(clean["include_flag"].sum()) == int((clean["is_1906"] == 0).sum()))
check("归一后 Sport 57 类", clean["sport_norm"].nunique() == 57, str(clean["sport_norm"].nunique()))
check("小项口径 17,452 枚", len(ev) == 17452, str(len(ev)))
check("2024 有奖牌记录小项 328 个", ev.loc[ev["Year"] == 2024, "event_key"].nunique() == 328)
check("2024 有金牌记录小项 325 个",
      ev.loc[(ev["Year"] == 2024) & (ev["Medal"] == "Gold"), "event_key"].nunique() == 325)
check("2024 已知缺失 4 项", len(pd.read_csv(OUT / "known_gaps.csv")) == 4)
check("NOC 映射覆盖全部 234 个 NOC", len(noc_map) == 234)
check("1906 奖牌行 458", int(((clean["Year"] == 1906) & (clean["is_medal"] == 1)).sum()) == 458)
check("2024 女性行占比 49.1%", abs((clean.loc[clean["Year"] == 2024, "Sex"] == "F").mean() * 100 - 49.1) < 0.05)
check("小项口径奖牌榜总数与明细一致",
      int(ev_tbl["Total"].sum()) == int(ev[ev["is_1906"] == 0].shape[0]))
check("近似实体奖牌榜首为 Michael Ii（28 枚）",
      ath.iloc[0]["name"] == "Michael Ii" and int(ath.iloc[0]["medals"]) == 28,
      f"{ath.iloc[0]['name']} / {int(ath.iloc[0]['medals'])}")

_dup = rows.groupby(["Year", "event_key", "Medal"]).size()
check("Q3 重复组 5,188 组 / 26,554 行（含 1906）",
      int((_dup > 1).sum()) == 5188 and int(_dup[_dup > 1].sum()) == 26554,
      f"{int((_dup > 1).sum())} 组 / {int(_dup[_dup > 1].sum())} 行")
_na24 = rows[rows["Year"] == 2024].drop_duplicates(["Year", "event_key", "Medal", "NOC"])
check("NOC-aware 小项口径 17,935（剔除 1906）、2024 年 1,027 单位 / 325 金",
      int(ev_noc_tbl["Total"].sum()) == 17935 and len(_na24) == 1027
      and int((_na24["Medal"] == "Gold").sum()) == 325,
      f"{int(ev_noc_tbl['Total'].sum())} / {len(_na24)} 单位 / {int((_na24['Medal'] == 'Gold').sum())} 金")
_usa24 = int(((ev["Year"] == 2024) & (ev["Medal"] == "Gold") & (ev["noc"] == "USA")).sum())
check("2024 美国小项口径金牌 39（官方 40，差 1 为女子公路赛金牌行缺失）",
      _usa24 == 39, f"本数据 {_usa24} / 官方 40")

failed = [r for r in results if not r[1]]
print(f"\n{len(results) - len(failed)}/{len(results)} 项通过")
sys.exit(1 if failed else 0)
