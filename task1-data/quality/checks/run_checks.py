# -*- coding: utf-8 -*-
"""任务一质量检查的最小复现脚本（6 项核心检查）
完整 11 项见 task1-data/contracts/quality_checks.csv 与 pipeline/02_clean.py；交付断言见 pipeline/04_validate.py。
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw" / "olympics_dataset.csv"

df = pd.read_csv(RAW, low_memory=False)
medal = df[df["Medal"] != "No medal"]
ok = True


def check(name, cond, detail):
    global ok
    ok = ok and bool(cond)
    print(("PASS" if cond else "FAIL"), "|", name, "|", detail)


def highlight(name, detail):
    print("INFO", "|", name, "|", detail)


check("结构完整", df.shape == (252565, 11), f"{df.shape[0]} 行 × {df.shape[1]} 列")
check("缺失值为 0", int(df.isna().sum().sum()) == 0, str(int(df.isna().sum().sum())))
check("奖牌行 38,818", len(medal) == 38818, f"{len(medal)} 行")
check("金/银/铜守恒",
      [int((medal["Medal"] == m).sum()) for m in ["Gold", "Silver", "Bronze"]] == [13002, 12746, 13070],
      "13,002 / 12,746 / 13,070")

dup = medal.groupby(["Year", "Event", "Medal"]).size()
dup = dup[dup > 1]
highlight("团体/并列重复", f"{len(dup)} 组、{int(dup.sum())} 行（{dup.sum() / len(medal) * 100:.1f}%）")

generic = r"^(Men|Women|Mixed|Open|Men Team|Women Team|Mixed Team|Open Team|Relay Only Athlete)$"
gen = df[df["Event"].str.strip().str.match(generic, na=False)]
rate20 = (gen[gen["Year"] == 2020].shape[0] / (df["Year"] == 2020).sum() * 100) if (df["Year"] == 2020).sum() else 0
rate24 = (gen[gen["Year"] == 2024].shape[0] / (df["Year"] == 2024).sum() * 100) if (df["Year"] == 2024).sum() else 0
check("Event 泛化规模", len(gen) == 6488, f"{len(gen)} 行；2020 {rate20:.1f}%、2024 {rate24:.1f}%")

non_ascii = int(df["Name"].str.contains(r"[^\x00-\x7F]", na=False).sum())
highlight("姓名编码", f"非 ASCII {non_ascii} 行；player_id {df['player_id'].nunique():,} 个，"
                      f"平均 {len(df) / df['player_id'].nunique():.3f} 行/ID")

print("\n核心检查全部通过" if ok else "\n存在未通过项")
sys.exit(0 if ok else 1)
