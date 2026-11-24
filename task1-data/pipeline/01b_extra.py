# -*- coding: utf-8 -*-
"""补充体检：为口径定义取数"""
import io
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "olympics_dataset.csv"
OUT = ROOT / "task1-data" / "output"

buf = io.StringIO()


def p(*a):
    t = " ".join(str(x) for x in a)
    print(t)
    buf.write(t + "\n")


df = pd.read_csv(RAW, low_memory=False)
medal = df[df["Medal"] != "No medal"].copy()

p("== 1. 泛化 Event 的奖牌行 ==")
gen_pat = r"^(Men|Women|Mixed|Open|Men Team|Women Team|Mixed Team|Open Team|Relay Only Athlete)$"
gen = df[df["Event"].str.strip().str.match(gen_pat, na=False)]
p("泛化行:", len(gen), "其中奖牌行:", (gen['Medal'] != 'No medal').sum())
p(gen[gen['Medal'] != 'No medal'].groupby('Year').size().to_string())
p("\n泛化 Event 所在 Sport Top15:")
p(gen['Sport'].value_counts().head(15).to_string())
p("\n泛化 Event 的奖牌行按 Sport Top10:")
p(gen[gen['Medal'] != 'No medal']['Sport'].value_counts().head(10).to_string())

p("\n== 2. 2024 小项口径（Key = Sport + Event） ==")
g24 = medal[(medal["Year"] == 2024) & (medal["Medal"] == "Gold")]
p("运动员行口径金牌行:", len(g24))
p("按(Sport,Event)去重后的金牌小项数:", g24.drop_duplicates(["Sport", "Event"]).shape[0])
p("\n按(Sport,Event)去重后的金牌榜 Top15:")
p(g24.drop_duplicates(["Sport", "Event"])["NOC"].value_counts().head(15).to_string())
p("\n按(Sport,Event)去重后的总奖牌榜 Top10:")
m24 = medal[medal["Year"] == 2024]
p(m24.drop_duplicates(["Sport", "Event", "Medal"])["NOC"].value_counts().head(10).to_string())

p("\n仅用 Event 去重（错误做法）金牌数:", g24.drop_duplicates(["Event"]).shape[0])
p("仅用 Event 去重金牌 Top5:")
p(g24.drop_duplicates(["Event"])["NOC"].value_counts().head(5).to_string())

p("\n== 3. 2016 / 2020 / 2024 泛化情况 ==")
for y in (2016, 2020, 2024):
    d = df[df["Year"] == y]
    g = d[d["Event"].str.match(gen_pat, na=False)]
    p(f"{y}: 行数 {len(d)}, 泛化行 {len(g)} ({len(g)/len(d)*100:.1f}%), 泛化奖牌行 {(g['Medal']!='No medal').sum()}, Event 唯一值 {d['Event'].nunique()}, Sport 唯一值 {d['Sport'].nunique()}")

p("\n== 4. 特殊记录 ==")
p("1956 年各城市行数:")
p(df[df["Year"] == 1956].groupby("City").size().to_string())
p("\n1956 Stockholm 的 Sport:")
p(df[(df["Year"] == 1956) & (df["City"] == "Stockholm")]["Sport"].value_counts().to_string())
p("\nEOR 记录:", (df["NOC"] == "EOR").sum(), " 奖牌:", ((df["NOC"] == "EOR") & (df["Medal"] != "No medal")).sum())
p(df[df["NOC"] == "EOR"].to_string())
p("\nROC 记录:", (df["NOC"] == "ROC").sum(), " 奖牌:", ((df["NOC"] == "ROC") & (df["Medal"] != "No medal")).sum())
p("AIN 记录:", (df["NOC"] == "AIN").sum(), " 奖牌:", ((df["NOC"] == "AIN") & (df["Medal"] != "No medal")).sum())
p("1906 参赛 NOC 数:", df.loc[df["Year"] == 1906, "NOC"].nunique())
p("1906 奖牌 NOC:", df.loc[(df["Year"] == 1906) & (df["Medal"] != "No medal"), "NOC"].nunique())

p("\n== 5. NOC 全量清单（年份范围 / 奖牌行） ==")
noc = df.groupby("NOC").agg(
    首次=("Year", "min"), 末次=("Year", "max"), 届数=("Year", "nunique"),
    行数=("Name", "size"),
    奖牌行=("Medal", lambda s: (s != "No medal").sum()),
).sort_values("奖牌行", ascending=False)
p(noc.to_string())

p("\n== 6. 奖牌为 No medal 的队伍/个人项目对比 ==")
p("奖牌行为 0 的 NOC 数:", (noc["奖牌行"] == 0).sum())
p("\n== 7. 姓名 ASCII 检查 ==")
p("含非 ASCII:", df["Name"].str.contains(r"[^\x00-\x7F]", na=False).sum())
p("含数字:", df["Name"].str.contains(r"\d", na=False).sum())
p("含 '.' :", df["Name"].str.contains(r"\.", na=False).sum())
p("姓名长度分布:")
p(df["Name"].str.len().describe().to_string())

p("\n== 8. 1906 与 1956 对奖牌总量影响 ==")
p("总奖牌行:", len(medal))
p("剔除1906后:", len(medal[medal["Year"] != 1906]))
p("1906 奖牌分布:")
p(medal[medal["Year"] == 1906]["Medal"].value_counts().to_string())

p("\n== 9. 同一年同小项不同 NOC 的金牌（混合队/并列） ==")
gold = medal[medal["Medal"] == "Gold"]
mix = gold.groupby(["Year", "Event"])["NOC"].nunique()
p("金牌对应多个 NOC 的 (年,小项) 数:", (mix > 1).sum())
p(mix[mix > 1].head(10).to_string())

p("\n== 10. 性别在 2024 的参赛/奖牌 ==")
d24 = df[df["Year"] == 2024]
p("女性行占比: %.2f%%" % ((d24["Sex"] == "F").mean() * 100))
m24f = m24[m24["Sex"] == "F"]
p("女性奖牌行占比: %.2f%%" % (len(m24f) / len(m24) * 100))

(OUT / "audit_extra.txt").write_text(buf.getvalue(), encoding="utf-8")
print("\nsaved", OUT / "audit_extra.txt")
