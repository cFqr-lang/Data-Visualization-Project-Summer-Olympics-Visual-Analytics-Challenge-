# -*- coding: utf-8 -*-
"""任务一：数据体检（只读脚本，不修改原始数据）
运行后会在 output/ 下生成 audit_log.txt
"""
import io
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "olympics_dataset.csv"
OUT = ROOT / "task1-data" / "output"
OUT.mkdir(parents=True, exist_ok=True)

buf = io.StringIO()


def p(*args):
    text = " ".join(str(a) for a in args)
    print(text)
    buf.write(text + "\n")


def title(t):
    p("\n" + "=" * 78)
    p(t)
    p("=" * 78)


df = pd.read_csv(RAW, low_memory=False)

title("A. 基本概况")
p("shape:", df.shape)
p("columns:", list(df.columns))
p("\n各列缺失值:")
p(df.isna().sum().to_string())
p("\n各列唯一值数量:")
p(df.nunique().to_string())
p("\nMedal 分布:")
p(df["Medal"].value_counts().to_string())
p("\nSex 分布:")
p(df["Sex"].value_counts().to_string())
p("\nSeason 分布:")
p(df["Season"].value_counts().to_string())
p("\nYear 取值（共 %d 个）:" % df["Year"].nunique(), sorted(df["Year"].unique().tolist()))
p("\n每届行数 / 奖牌行数 / 参赛 NOC 数:")
g = df.groupby("Year").agg(
    行数=("Name", "size"),
    奖牌行=("Medal", lambda s: (s != "No medal").sum()),
    NOC数=("NOC", "nunique"),
    女性行占比=("Sex", lambda s: round((s == "F").mean() * 100, 1)),
)
p(g.to_string())

title("B. 特殊届次与城市")
p("1906 行数:", (df["Year"] == 1906).sum())
p("1906 奖牌行数:", ((df["Year"] == 1906) & (df["Medal"] != "No medal")).sum())
p("\n同一届出现多个 City 的年份:")
city = df.groupby("Year")["City"].unique()
for y, c in city.items():
    if len(c) > 1:
        p(" ", y, list(c), " 该年行数:", (df["Year"] == y).sum())
p("\n2020 / 2024 行数:", (df["Year"] == 2020).sum(), (df["Year"] == 2024).sum())
p("2020 年份字段对应的实际举办城市:", df.loc[df["Year"] == 2020, "City"].unique())

title("C. Sport 口径")
sports = df["Sport"].value_counts()
p("Sport 唯一值:", df["Sport"].nunique())
p("\nSport 全部取值及行数:")
p(sports.to_string())

sport_years = df.groupby("Sport")["Year"].agg(["min", "max", "nunique"])
p("\n只在 2020 及以后出现的 Sport:")
p(sport_years[sport_years["min"] >= 2020].to_string())
p("\n只在 2016 及以前出现的 Sport（且 2020 后消失）:")
p(sport_years[sport_years["max"] <= 2016].to_string())

comma = df[df["Sport"].str.contains(",", na=False)]
p("\nSport 含逗号的行数:", len(comma))
p("其中奖牌行:", (comma["Medal"] != "No medal").sum())
p("逗号拼接取值示例:")
p(comma["Sport"].value_counts().head(20).to_string())
p("逗号拼接所在年份分布:")
p(comma.groupby("Year").size().to_string())

title("D. Event 泛化")
p("Event 唯一值:", df["Event"].nunique())
general_pat = r"^(Men|Women|Mixed|Open|Men Team|Women Team|Mixed Team|Open Team|Relay Only Athlete)$"
gen = df[df["Event"].str.strip().str.match(general_pat, na=False)]
p("泛化 Event 行数:", len(gen), " 占比: %.2f%%" % (len(gen) / len(df) * 100))
p("泛化 Event 按年份:")
p(gen.groupby("Year").size().to_string())
p("\n泛化 Event 的取值分布:")
p(gen["Event"].value_counts().to_string())
p("\n2020/2024 年 Event 取值 Top20:")
p(df.loc[df["Year"].isin([2020, 2024]), "Event"].value_counts().head(20).to_string())

title("E. 代表团与队伍")
p("NOC 唯一值:", df["NOC"].nunique())
noc_medal = df.loc[df["Medal"] != "No medal", "NOC"].nunique()
p("获得过奖牌的 NOC:", noc_medal)
p("从未获奖的 NOC:", df["NOC"].nunique() - noc_medal)
p("Team 唯一值:", df["Team"].nunique())
p("Team 含 '-数字' 后缀的行数:", df["Team"].str.contains(r"-\d+$", regex=True, na=False).sum())
p("Team 含 '/' 的行数（混合队）:", df["Team"].str.contains("/", na=False).sum())
p("混合队示例:")
p(df.loc[df["Team"].str.contains("/", na=False), "Team"].value_counts().head(10).to_string())
p("\n奖牌行数 Top15 NOC:")
p(df.loc[df["Medal"] != "No medal", "NOC"].value_counts().head(15).to_string())

title("F. 奖牌口径与团体项目")
medal = df[df["Medal"] != "No medal"]
p("奖牌行总数:", len(medal))
p(medal["Medal"].value_counts().to_string())
grp_all = df.groupby(["Year", "Event", "Medal"]).size()
p("\n(年×小项×奖牌) 重复组数（含 No medal 行）:", (grp_all > 1).sum())
p("涉及行数:", grp_all[grp_all > 1].sum())
grp_medal = medal.groupby(["Year", "Event", "Medal"]).size()
p("(年×小项×奖牌) 重复组数（仅奖牌行）:", (grp_medal > 1).sum())
p("涉及奖牌行数:", grp_medal[grp_medal > 1].sum())
p("重复组规模分布（仅奖牌行）:")
p(grp_medal[grp_medal > 1].value_counts().sort_index().head(15).to_string())

# 每个(年,小项)的奖牌种类数
kinds = medal.groupby(["Year", "Event"])["Medal"].nunique()
p("\n(年×小项) 只颁发 1 种奖牌的数量:", (kinds == 1).sum())
p("只颁发 1 种奖牌的明细（前 20）:")
p(kinds[kinds == 1].head(20).to_string())
p("\n1908 年 Athletics 400m 相关记录:")
p(df[(df["Year"] == 1908) & (df["Event"].str.contains("400", na=False))][
    ["Name", "NOC", "Event", "Medal"]
].to_string())

p("\n2024 年各国金牌行数 Top15（运动员行口径）:")
p(medal[(medal["Year"] == 2024) & (medal["Medal"] == "Gold")]["NOC"].value_counts().head(15).to_string())
p("\n2024 年各国金牌数 Top15（小项口径：同一年+同小项只计 1 金）:")
gold24 = medal[(medal["Year"] == 2024) & (medal["Medal"] == "Gold")]
p(gold24.drop_duplicates(["Event"])["NOC"].value_counts().head(15).to_string())

title("G. 运动员姓名与 ID")
p("player_id 唯一值:", df["player_id"].nunique())
p("平均每 ID 记录数: %.3f" % (len(df) / df["player_id"].nunique()))
id_names = df.groupby("player_id")["Name"].nunique()
p("对应多个姓名的 ID 数:", (id_names > 1).sum())
name_ids = df.groupby("Name")["player_id"].nunique()
p("对应多个 ID 的姓名数:", (name_ids > 1).sum())
p("\n奖牌最多的姓名 Top10:")
p(medal["Name"].value_counts().head(10).to_string())
p("\n同名跨年份跨度最大的姓名 Top10（疑似多人合并）:")
span = df.groupby("Name")["Year"].agg(["min", "max", "nunique"])
span["跨度"] = span["max"] - span["min"]
p(span.sort_values("跨度", ascending=False).head(10).to_string())
p("\n姓名含括号的行数:", df["Name"].str.contains(r"[()\[\]]", regex=True, na=False).sum())
p("姓名含非 ASCII 字符的行数:", df["Name"].str.contains(r"[^\x00-\x7F]", regex=True, na=False).sum())
p("姓名首尾空格行数:", (df["Name"] != df["Name"].str.strip()).sum())
p("姓名示例（含括号）:")
p(df.loc[df["Name"].str.contains(r"[()\[\]]", regex=True, na=False), "Name"].head(10).to_string())
p("\nMichael 相关姓名及记录数:")
p(df.loc[df["Name"].str.contains("Michael", na=False), "Name"].value_counts().head(10).to_string())
p("\nCharles Jr. 相关姓名及记录数:")
p(df.loc[df["Name"].str.contains("Charles", na=False), "Name"].value_counts().head(10).to_string())

title("H. 其他潜在问题")
p("Year 与 City 组合数:", df.groupby(["Year", "City"]).ngroups)
p("NOC 与 Team 组合数:", df.groupby(["NOC", "Team"]).ngroups)
p("同一 NOC 对应多个 Team 的示例（NOC=CHN）:")
p(df.loc[df["NOC"] == "CHN", "Team"].value_counts().head(10).to_string())
p("\n奖牌值为空或异常:", df["Medal"].isna().sum())
p("Sex 唯一值:", df["Sex"].unique().tolist())
p("Year 最小值/最大值:", df["Year"].min(), df["Year"].max())
p("\n奖牌行中 1906 年占比: %.2f%%" % ((medal["Year"] == 1906).mean() * 100))

p("\n审计完成。")

(OUT / "audit_log.txt").write_text(buf.getvalue(), encoding="utf-8")
print("\n已保存:", OUT / "audit_log.txt")
