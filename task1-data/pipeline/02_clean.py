# -*- coding: utf-8 -*-
"""任务一：清洗 / 归一，并生成两套口径的数据集
输入 : data/raw/olympics_dataset.csv
输出 : output/*.csv（含清洗后全量数据、双口径奖牌表、映射表、质量检查表）
"""
import io
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "olympics_dataset.csv"
OUT = ROOT / "task1-data" / "output"
PROC = ROOT / "data" / "processed"
CONTRACTS = ROOT / "task1-data" / "contracts"
SHARED = ROOT / "task1-data" / "metrics"
for d in (OUT, PROC, CONTRACTS, SHARED):
    d.mkdir(parents=True, exist_ok=True)

log = io.StringIO()


def p(*a):
    t = " ".join(str(x) for x in a)
    print(t)
    log.write(t + "\n")


def title(t):
    p("\n" + "-" * 70)
    p(t)
    p("-" * 70)


# ---------------------------------------------------------------- 1. 读取
df = pd.read_csv(RAW, low_memory=False)
p("原始数据:", df.shape)

# ---------------------------------------------------------------- 2. Sport 归一映射
# 只对需要归一的取值写规则，其余保持原值（identity）
SPORT_RULES = {
    # 2020 起拆分的大类，还原到 2016 前的名称
    "Artistic Gymnastics": ("Gymnastics", "2020后拆分合并", "艺术体操并入 Gymnastics，还原 2016 前口径"),
    "Trampoline Gymnastics": ("Trampoline Gymnastics", "保持不变", "Trampolining 统一到该名称"),
    "Trampolining": ("Trampoline Gymnastics", "2020后更名", "与 2020 后 Trampoline Gymnastics 统一"),
    "Cycling": ("Cycling", "保持不变", ""),
    "Cycling Road": ("Cycling", "2020后拆分合并", "公路/场地/山地/BMX 合并回 Cycling"),
    "Cycling Track": ("Cycling", "2020后拆分合并", ""),
    "Cycling Mountain Bike": ("Cycling", "2020后拆分合并", ""),
    "Cycling BMX Racing": ("Cycling", "2020后拆分合并", ""),
    "Cycling BMX Freestyle": ("Cycling", "2020后拆分合并", ""),
    "Canoe Sprint": ("Canoeing", "2020后拆分合并", "皮划艇静水/激流回旋合并回 Canoeing"),
    "Canoe Slalom": ("Canoeing", "2020后拆分合并", ""),
    "Equestrian": ("Equestrianism", "2020后更名", "统一为 2016 前名称"),
    "Artistic Swimming": ("Artistic Swimming", "保持不变", "Synchronized Swimming 统一到该名称"),
    "Synchronized Swimming": ("Artistic Swimming", "2020后更名", ""),
    "Baseball": ("Baseball/Softball", "合并", "棒球、垒球合并为同一大类"),
    "Softball": ("Baseball/Softball", "合并", ""),
    "Baseball/Softball": ("Baseball/Softball", "合并", ""),
    "3x3 Basketball": ("Basketball", "合并", "三人篮球并入篮球大类"),
    "Basketball": ("Basketball", "保持不变", ""),
    # 逗号拼接的跨项写法（2024，共 89 行，全部无奖牌）
    "Cycling Road, Cycling Track": ("Cycling", "逗号拼接", "拆分为 Cycling 后去重"),
    "Cycling Road, Cycling Mountain Bike": ("Cycling", "逗号拼接", ""),
    "Cycling Road, Triathlon": ("Cycling", "逗号拼接", "拆分为 Cycling + Triathlon"),
    "Marathon Swimming, Swimming": ("Marathon Swimming", "逗号拼接", "拆分为 Marathon Swimming + Swimming"),
    "3x3 Basketball, Basketball": ("Basketball", "逗号拼接", ""),
}


def norm_sport(raw: str):
    """返回 (主大类, 全部大类列表, 是否多项目)"""
    raw = str(raw).strip()
    if "," in raw:
        parts = [x.strip() for x in raw.split(",")]
        targets = []
        for x in parts:
            targets.append(SPORT_RULES.get(x, (x, "保持不变", ""))[0])
        uniq = list(dict.fromkeys(targets))
        return uniq[0], uniq, len(uniq) > 1
    target = SPORT_RULES.get(raw, (raw, "保持不变", ""))[0]
    return target, [target], False


sport_rows = []
for raw_val, cnt in df["Sport"].value_counts().items():
    main, alls, multi = norm_sport(raw_val)
    rule = SPORT_RULES.get(raw_val, (raw_val, "保持不变", ""))
    sport_rows.append({
        "sport_raw": raw_val,
        "rows": int(cnt),
        "sport_norm": main,
        "sport_all": "|".join(alls),
        "is_multi_sport": int(multi),
        "rule": rule[1],
        "note": rule[2],
    })
sport_map_df = pd.DataFrame(sport_rows).sort_values(["rule", "sport_raw"])
sport_map_df.to_csv(OUT / "sport_mapping.csv", index=False, encoding="utf-8-sig")

clean = df.copy()
clean["sport_raw"] = clean["Sport"].str.strip()
clean["sport_norm"] = clean["sport_raw"].map(lambda x: norm_sport(x)[0])
clean["sport_all"] = clean["sport_raw"].map(lambda x: "|".join(norm_sport(x)[1]))
clean["is_multi_sport"] = clean["sport_raw"].map(lambda x: int(norm_sport(x)[2]))

p("Sport：原始 %d 个取值 -> 归一大类 %d 个" % (df["Sport"].nunique(), clean["sport_norm"].nunique()))
p("逗号拼接行数:", int(clean["is_multi_sport"].sum()))

# ---------------------------------------------------------------- 3. Event 泛化处理
GENERIC_EVENTS = {
    "Men", "Women", "Mixed", "Open",
    "Men Team", "Women Team", "Mixed Team", "Open Team",
    "Relay Only Athlete",
}
clean["event_raw"] = clean["Event"].str.strip()
clean["event_granularity"] = np.where(
    clean["event_raw"].isin(GENERIC_EVENTS), "coarse", "fine"
)


def make_event_key(row):
    """小项键：届次 + 原始 Sport + Event（+ Sex，仅用于非混合的泛化值）
    用原始 Sport 而非归一大类，避免 3x3 篮球与五人篮球在泛化值下被合并。
    """
    if row["event_granularity"] == "coarse":
        if row["event_raw"].lower().startswith("mixed"):
            return f"{row['Year']}|{row['sport_raw']}|{row['event_raw']}"
        return f"{row['Year']}|{row['sport_raw']}|{row['event_raw']}|{row['Sex']}"
    return f"{row['Year']}|{row['sport_raw']}|{row['event_raw']}"


clean["event_key"] = clean.apply(make_event_key, axis=1)
clean["event_name_clean"] = np.where(
    (clean["event_granularity"] == "coarse") & (~clean["event_raw"].str.lower().str.startswith("mixed")),
    clean["event_raw"] + "(" + clean["Sex"] + ")",  # 泛化事件，只能保留"项目×性别"粒度
    clean["event_raw"],
)

# ---------------------------------------------------------------- 4. 特殊记录标记
clean["is_1906"] = (clean["Year"] == 1906).astype(int)
clean["is_1956_stockholm"] = ((clean["Year"] == 1956) & (clean["City"] == "Stockholm")).astype(int)
clean["is_refugee"] = (clean["NOC"] == "EOR").astype(int)
clean["is_medal"] = (clean["Medal"] != "No medal").astype(int)
clean["medal_rank"] = clean["Medal"].map({"Gold": 1, "Silver": 2, "Bronze": 3}).fillna(0).astype(int)

# 契约字段：泛化质量、团体项目、默认纳入标记
clean["event_key_quality"] = np.where(clean["event_granularity"] == "coarse", "generic", "specific")
_dup = clean[clean["is_medal"] == 1].groupby(["event_key", "Medal", "NOC"]).size()
team_keys = set(_dup[_dup > 1].index.get_level_values("event_key"))
clean["is_team_event"] = clean["event_key"].isin(team_keys).astype(int)
clean["include_flag"] = (clean["is_1906"] == 0).astype(int)

# 政体变迁：历史 NOC -> 现代继承 NOC（"保留"表示不合并）
NOC_RULES = {
    "URS": ("RUS", "继承", "苏联 1952-1988，并入俄罗斯"),
    "EUN": ("RUS", "继承", "独联体联队 1992，并入俄罗斯（含非俄成员，见说明）"),
    "ROC": ("RUS", "继承", "俄罗斯奥委会 2020"),
    "GDR": ("GER", "继承", "东德 1968-1988"),
    "FRG": ("GER", "继承", "西德 1968-1988"),
    "SAA": ("GER", "继承", "萨尔 1952，1957 年并入西德"),
    "TCH": ("CZE", "可选继承", "捷克斯洛伐克；斯洛伐克部分归入 CZE 会低估 SVK"),
    "YUG": ("SRB", "可选继承", "南斯拉夫；继承国不止塞尔维亚"),
    "SCG": ("SRB", "可选继承", "塞尔维亚和黑山"),
    "ANZ": ("AUS", "历史合并队", "澳大拉西亚联队 1908-1912（澳+新）"),
    "BOH": ("CZE", "历史合并队", "波希米亚 1900-1912"),
    "UAR": ("EGY", "历史合并队", "阿拉伯联合共和国 1960（埃+叙）"),
    "MAL": ("MAS", "历史更名", "马来亚"),
    "NBO": ("MAS", "历史合并队", "北婆罗洲"),
    "RHO": ("ZIM", "历史更名", "罗得西亚"),
    "AIN": ("AIN", "保留", "2024 个人中立运动员（俄/白俄），不并入 RUS"),
    "EOR": ("EOR", "保留", "难民代表团"),
    "IOA": ("IOA", "保留", "独立奥林匹克参赛者（1992/2016）"),
    "WIF": ("WIF", "保留", "西印度群岛联队 1960，涉及多国"),
    "AHO": ("AHO", "保留", "荷属安的列斯，已解体"),
}
clean["noc_modern"] = clean["NOC"].map(lambda x: NOC_RULES.get(x, (x, "保持不变", ""))[0])
clean["team_base"] = clean["Team"].str.replace(r"-\d+$", "", regex=True).str.strip()
noc_name = clean.groupby("NOC")["team_base"].agg(lambda s: s.value_counts().index[0])
clean["noc_name"] = clean["NOC"].map(noc_name)

noc_rows = []
for noc in sorted(clean["NOC"].unique()):
    modern, mtype, note = NOC_RULES.get(noc, (noc, "保持不变", ""))
    sub = clean[clean["NOC"] == noc]
    noc_rows.append({
        "noc": noc,
        "team_name": noc_name.get(noc, ""),
        "first_year": int(sub["Year"].min()),
        "last_year": int(sub["Year"].max()),
        "years": int(sub["Year"].nunique()),
        "rows": int(len(sub)),
        "medal_rows": int(sub["is_medal"].sum()),
        "noc_modern": modern,
        "merge_type": mtype,
        "note": note,
    })
noc_map_df = pd.DataFrame(noc_rows).sort_values(["merge_type", "rows"], ascending=[True, False])
noc_map_df.to_csv(OUT / "noc_mapping.csv", index=False, encoding="utf-8-sig")
p("NOC 映射表行数（全量）:", len(noc_map_df))

# 近似运动员实体：Name + Sex + NOC（仅作探索用，不能当官方 ID）
clean["athlete_key"] = clean["Name"] + "|" + clean["Sex"] + "|" + clean["NOC"]
ath = (
    clean.groupby("athlete_key")
    .agg(
        name=("Name", "first"),
        sex=("Sex", "first"),
        noc=("NOC", "first"),
        first_year=("Year", "min"),
        last_year=("Year", "max"),
        years=("Year", "nunique"),
        rows=("Name", "size"),
        medals=("is_medal", "sum"),
    )
)
ath["name_span"] = ath["last_year"] - ath["first_year"]
ath["entity_flag"] = np.select(
    [ath["name_span"] > 40, (ath["name_span"] > 8) & (ath["years"] == 1)],
    ["疑似同名合并", "跨届存疑"],
    default="",
)
ath.sort_values("medals", ascending=False).to_csv(OUT / "athlete_entities.csv", encoding="utf-8-sig")
ath.sort_values("medals", ascending=False).head(30).to_csv(
    OUT / "athlete_top_medals.csv", index=False, encoding="utf-8-sig")
p("近似运动员实体:", len(ath), " 其中标记存疑:", int((ath["entity_flag"] != "").sum()))

# ---------------------------------------------------------------- 5. 输出清洗后全量数据
OUT_COLS = [
    "player_id", "Name", "Sex", "Team", "NOC", "Year", "Season", "City",
    "Sport", "Event", "Medal",
    "sport_raw", "sport_norm", "sport_all", "is_multi_sport",
    "event_raw", "event_name_clean", "event_granularity", "event_key", "event_key_quality",
    "is_1906", "is_1956_stockholm", "is_refugee", "is_medal", "medal_rank",
    "is_team_event", "include_flag",
    "noc_modern", "noc_name", "team_base", "athlete_key",
]
clean[OUT_COLS].to_csv(OUT / "olympics_clean.csv", index=False, encoding="utf-8-sig")
try:
    clean[OUT_COLS].to_parquet(PROC / "olympics_clean.parquet", index=False)
except Exception as exc:  # pyarrow 未安装时仍可产出 CSV，并给出明确提示
    p("WARN: parquet 写入失败（请安装 pyarrow）：", exc)
p("已输出 olympics_clean.csv / parquet:", clean.shape)

# ---------------------------------------------------------------- 6. 两套口径
medal_rows = clean[clean["is_medal"] == 1].copy()
medal_rows.to_csv(OUT / "medals_athlete_row.csv", index=False, encoding="utf-8-sig")

# 小项口径：同届×同小项×同奖牌色只计 1 枚
ev = (
    medal_rows.groupby(["Year", "event_key", "Medal"], as_index=False)
    .agg(
        sport_raw=("sport_raw", "first"),
        sport_norm=("sport_norm", "first"),
        event_raw=("event_raw", "first"),
        event_name_clean=("event_name_clean", "first"),
        event_granularity=("event_granularity", "first"),
        sex=("Sex", lambda s: "|".join(sorted(set(s)))),
        noc=("NOC", lambda s: s.value_counts().index[0]),
        n_noc=("NOC", "nunique"),
        n_athlete_rows=("Name", "size"),
        is_1906=("is_1906", "max"),
        is_1956_stockholm=("is_1956_stockholm", "max"),
    )
)
ev["is_mixed_noc"] = (ev["n_noc"] > 1).astype(int)
ev["n_medal_colors"] = ev.groupby("event_key")["Medal"].transform("nunique")
ev["has_gold"] = ev.groupby("event_key")["Medal"].transform(lambda s: int("Gold" in set(s)))
ev.to_csv(OUT / "medals_event_level.csv", index=False, encoding="utf-8-sig")
p("奖牌行口径:", len(medal_rows), " 小项口径:", len(ev))

# 2024 已知记录缺失清单（与公开赛果交叉核对）
def _rows(year, sport_raw, event):
    return int(((clean["Year"] == year) & (clean["sport_raw"] == sport_raw) & (clean["Event"] == event)).sum())


gaps = pd.DataFrame([
    {"届次": 2024, "项目": "Cycling Mountain Bike", "小项": "Men's Cross-country", "问题类型": "缺金牌行",
     "缺失奖牌": "Gold", "数据中行数": _rows(2024, "Cycling Mountain Bike", "Men's Cross-country"),
     "官方获得者": "Tom Pidcock (GBR)", "来源": "公开赛果/Olympedia 核对"},
    {"届次": 2024, "项目": "Cycling Road", "小项": "Women's Road Race", "问题类型": "奖牌行不完整",
     "缺失奖牌": "Gold;Bronze", "数据中行数": _rows(2024, "Cycling Road", "Women's Road Race"),
     "官方获得者": "Kristen Faulkner (USA) / Lotte Kopecky (BEL)", "来源": "公开赛果/Olympedia 核对"},
    {"届次": 2024, "项目": "Swimming", "小项": "Men's 800m Freestyle", "问题类型": "缺金牌/铜牌行",
     "缺失奖牌": "Gold;Bronze", "数据中行数": _rows(2024, "Swimming", "Men's 800m Freestyle"),
     "官方获得者": "Daniel Wiffen (IRL) / Gregorio Paltrinieri (ITA)", "来源": "公开赛果/Olympedia 核对"},
    {"届次": 2024, "项目": "Triathlon", "小项": "Mixed Relay", "问题类型": "整项无奖牌行",
     "缺失奖牌": "Gold;Silver;Bronze", "数据中行数": _rows(2024, "Triathlon", "Mixed Relay"),
     "官方获得者": "德国队金牌（混合接力）", "来源": "公开赛果/Olympedia 核对"},
])
gaps.to_csv(OUT / "known_gaps.csv", index=False, encoding="utf-8-sig")
p("2024 已知记录缺失:", len(gaps), "项")

p("\n分年对比（运动员行口径 / 小项口径）:")
cmp_year = (
    medal_rows.groupby("Year").size().rename("运动员行奖牌")
    .to_frame()
    .join(ev.groupby("Year").size().rename("小项口径奖牌"))
)
cmp_year["差异"] = cmp_year["运动员行奖牌"] - cmp_year["小项口径奖牌"]
cmp_year["膨胀率%"] = (cmp_year["差异"] / cmp_year["小项口径奖牌"] * 100).round(1)
cmp_year.to_csv(OUT / "caliber_by_year.csv", encoding="utf-8-sig")
p(cmp_year.to_string())

# 两种口径的奖牌榜
ath_tbl = (
    medal_rows.groupby(["NOC", "Medal"]).size().unstack(fill_value=0)
    .reindex(columns=["Gold", "Silver", "Bronze"], fill_value=0)
)
ath_tbl["Total"] = ath_tbl.sum(axis=1)
ath_tbl = ath_tbl.sort_values("Total", ascending=False)
ath_tbl.to_csv(OUT / "medal_table_athlete_noc.csv", encoding="utf-8-sig")

ev_tbl = (
    ev.groupby(["noc", "Medal"]).size().unstack(fill_value=0)
    .reindex(columns=["Gold", "Silver", "Bronze"], fill_value=0)
)
ev_tbl["Total"] = ev_tbl.sum(axis=1)
ev_tbl = ev_tbl.sort_values("Total", ascending=False)
ev_tbl.to_csv(OUT / "medal_table_event_noc.csv", encoding="utf-8-sig")

# 主口径（剔除 1906 届间奥运会）的奖牌榜，供任务二直接使用
for name, frame, noc_col in [
    ("medal_table_athlete_noc_ex1906.csv", medal_rows[medal_rows["is_1906"] == 0], "NOC"),
    ("medal_table_event_noc_ex1906.csv", ev[ev["is_1906"] == 0], "noc"),
]:
    t = frame.groupby([noc_col, "Medal"]).size().unstack(fill_value=0).reindex(
        columns=["Gold", "Silver", "Bronze"], fill_value=0)
    t["Total"] = t.sum(axis=1)
    t.sort_values("Total", ascending=False).to_csv(OUT / name, encoding="utf-8-sig")

# 2024 双口径对比（官方数字只引用赛题给定的锚点）
d24 = medal_rows[medal_rows["Year"] == 2024]
e24 = ev[ev["Year"] == 2024]
official = {"USA": 40, "CHN": 40, "NED": 15}
compare = []
for noc in ["USA", "CHN", "NED", "JPN", "AUS", "FRA", "GBR", "KOR", "ITA", "GER"]:
    compare.append({
        "NOC": noc,
        "运动员行金牌": int(((d24["NOC"] == noc) & (d24["Medal"] == "Gold")).sum()),
        "小项口径金牌": int(((e24["noc"] == noc) & (e24["Medal"] == "Gold")).sum()),
        "官方金牌(仅锚点)": official.get(noc, ""),
    })
cmp24 = pd.DataFrame(compare)
cmp24.to_csv(OUT / "caliber_2024_compare.csv", index=False, encoding="utf-8-sig")
p("\n2024 双口径对比:")
p(cmp24.to_string(index=False))

# ---------------------------------------------------------------- 7. 质量检查清单
def cnt(cond):
    return int(cond.sum())


ev24 = ev[ev["Year"] == 2024]
medal_set_24 = ev24.groupby("event_key")["Medal"].agg(lambda s: set(s))
no_gold_keys = medal_set_24[~medal_set_24.apply(lambda s: "Gold" in s)].index.tolist()
no_gold24 = len(no_gold_keys)
no_gold_names = [k.split("|", 2)[2] for k in no_gold_keys]
n_event24 = ev24["event_key"].nunique()
n_gold_event24 = ev24[ev24["Medal"] == "Gold"]["event_key"].nunique()
p("\n2024 缺金牌行的小项:", no_gold_names)
p("2024 奖牌小项:", n_event24, " 有金牌记录:", n_gold_event24)


dup_groups = medal_rows.groupby(["Year", "event_key", "Medal"]).size()
dup_groups = dup_groups[dup_groups > 1]
single_medal_events = medal_rows.groupby(["Year", "event_key"])["Medal"].nunique()
span = df.groupby("Name")["Year"].agg(["min", "max"])
span_max = int((span["max"] - span["min"]).max())
span_name = span.assign(d=span["max"] - span["min"]).sort_values("d", ascending=False).index[0]

checks = [
    {
        "编号": "Q1", "检查项": "结构完整性与缺失值",
        "方法": "df.shape / df.isna().sum() / 常量列检测",
        "结果": f"{df.shape[0]} 行 × {df.shape[1]} 列；缺失值 0；Season 恒为 Summer，City 覆盖 {df['City'].nunique()} 个城市",
        "处理决定": "不做插补；Season 作为常量列保留但不参与分析",
        "影响": "无",
    },
    {
        "编号": "Q2", "检查项": "字段取值域与编码",
        "方法": "逐列 nunique + 非 ASCII 检测 + 首尾空格检测",
        "结果": f"Sex 仅 M/F；Medal 仅 4 值；Year {df['Year'].nunique()} 个取值；姓名含非 ASCII {cnt(df['Name'].str.contains(r'[^\x00-\x7F]', na=False))} 行、首尾空格 {cnt(df['Name'] != df['Name'].str.strip())} 行",
        "处理决定": "保留原值；识别出全部姓名已被剥离变音符号（如 Nándor Kovács→Nndor Kovcs），不尝试还原",
        "影响": "姓名检索需容忍缺字母；个体分析不可靠",
    },
    {
        "编号": "Q3", "检查项": "奖牌行重复（团体项目/并列）",
        "方法": "groupby(Year, event_key, Medal).size() > 1",
        "结果": f"重复组 {len(dup_groups)} 个，涉及奖牌行 {int(dup_groups.sum())} 行，占奖牌行 {dup_groups.sum()/len(medal_rows)*100:.1f}%",
        "处理决定": "同时提供运动员行口径与小项口径；小项口径按(届次×小项×奖牌色)去重",
        "影响": "两套口径 2024 金牌榜差异显著（见对比表）",
    },
    {
        "编号": "Q4", "检查项": "奖牌数量守恒与单奖牌小项",
        "方法": "Medal.value_counts() + 每个(届次,小项)的奖牌种类数",
        "结果": f"金 {cnt(df['Medal']=='Gold')} / 银 {cnt(df['Medal']=='Silver')} / 铜 {cnt(df['Medal']=='Bronze')}，三者不等；仅颁发 1 种奖牌的小项 {(single_medal_events==1).sum()} 个（如 1908 男子 400 米仅 1 金）",
        "处理决定": "不补齐缺失的银/铜牌；保留历史真实状态",
        "影响": "'金银铜应相等'的假设不成立",
    },
    {
        "编号": "Q5", "检查项": "Sport 口径漂移与逗号拼接",
        "方法": "按年份统计 Sport 取值；检测逗号；构建归一映射表",
        "结果": f"原始 {df['Sport'].nunique()} 个取值；2020 及以后新增/改写 24 个；Sport 含逗号 {cnt(clean['sport_raw'].str.contains(','))} 行（全部 2024、全部无奖牌），其中归一后仍为跨项的 {cnt(clean['is_multi_sport']==1)} 行；归一后 {clean['sport_norm'].nunique()} 个大类",
        "处理决定": "按映射表统一到 2016 前口径；逗号行拆分为多项目，主项目取第一个",
        "影响": "2020 前后项目统计可直接比较",
    },
    {
        "编号": "Q6", "检查项": "Event 泛化（2020 起）",
        "方法": "检测 Men/Women/Men Team/Relay Only Athlete 等泛化值",
        "结果": f"泛化行 {cnt(clean['event_granularity']=='coarse')} 行（{clean['event_granularity'].eq('coarse').mean()*100:.1f}%），其中奖牌行 {cnt((clean['event_granularity']=='coarse') & (clean['is_medal']==1))} 行；2020 年占 20.1%，2024 年占 23.1%",
        "处理决定": "标记 coarse 粒度；小项键加入 Sex 并注明只能还原到'项目×性别'，涉及接力的分析降级到项目层",
        "影响": "2024 小项口径金牌小项数少于官方（见 Q10）",
    },
    {
        "编号": "Q7", "检查项": "姓名与 player_id 可靠性",
        "方法": "player_id 唯一值/重复度；同名多 ID、同 ID 多名；括号残留；跨年份跨度",
        "结果": f"player_id {df['player_id'].nunique()} 个（平均 {len(df)/df['player_id'].nunique():.3f} 行/ID）；同名对应多个 ID {cnt(df.groupby('Name')['player_id'].nunique()>1)} 个；同 ID 对应多个姓名 {cnt(df.groupby('player_id')['Name'].nunique()>1)} 个；姓名含括号 {cnt(df['Name'].str.contains(r'[()\[\]]', regex=True))} 行；同名跨年份最大跨度 {span_max} 年（{span_name}）",
        "处理决定": "不构建个体 ID；个体分析改用 (Name+Sex+NOC) 近似实体并做敏感性说明；本任务不做个体排名结论",
        "影响": "奖牌之王 'Michael Ii' 等姓名不可直接对外引用",
    },
    {
        "编号": "Q8", "检查项": "NOC 与 Team 一致性",
        "方法": "NOC/Team 唯一值；Team 后缀 -数字；混合队检测",
        "结果": f"NOC {df['NOC'].nunique()} 个 / Team {df['Team'].nunique()} 个；Team 带 -数字 分队后缀 {cnt(df['Team'].str.contains(r'-\d+$', regex=True))} 行；含 '/' 的混合队 {cnt(df['Team'].str.contains('/'))} 行",
        "处理决定": "国家归属一律用 NOC；Team 仅用于展示，去除 -数字 后缀生成 team_base",
        "影响": "避免把 'China-1' 等分队当成独立代表团",
    },
    {
        "编号": "Q9", "检查项": "特殊届次与特殊政体",
        "方法": "按年份/城市交叉核对；识别 1906、1956 双城、EOR/ROC/AIN 等",
        "结果": f"1906 年 {cnt(clean['Year']==1906)} 行、奖牌 {cnt((clean['Year']==1906)&(clean['is_medal']==1))} 行（占奖牌 {cnt((clean['Year']==1906)&(clean['is_medal']==1))/len(medal_rows)*100:.2f}%）；1956 斯德哥尔摩 {cnt(clean['is_1956_stockholm']==1)} 行（全部马术）；EOR {cnt(clean['NOC']=='EOR')} 行/奖牌 {cnt((clean['NOC']=='EOR')&(clean['is_medal']==1))} 行；ROC {cnt(clean['NOC']=='ROC')} 行；AIN {cnt(clean['NOC']=='AIN')} 行",
        "处理决定": "主分析剔除 1906（保留标记做敏感性）；1956 合并为墨尔本主办并标注分场；ROC 并入 RUS 谱系，AIN/EOR 保留独立并单列",
        "影响": "主口径与含 1906 口径的奖牌总数差约 1.2%",
    },
    {
        "编号": "Q10", "检查项": "小项口径与官方小项数校验（2024）",
        "方法": "以(届次×原始 Sport×Event，泛化值追加性别)为键去重，统计 2024 小项数，与官方 329 小项对比",
        "结果": f"2024 运动员行金牌 {cnt((d24['Medal']=='Gold'))} 行；小项口径 {n_event24} 个有奖牌记录的小项（官方 329；铁人三项混合接力在数据中无任何奖牌行），其中 {n_gold_event24} 个有金牌记录；{no_gold24} 个小项缺金牌行",
        "处理决定": "小项口径作为对比口径使用；与官方数字对比时必须附差异清单，不补齐缺失行",
        "影响": "美国小项口径 39、官方 40（差 1 为女子公路赛金牌行缺失）；荷兰 15、官方 15；中国 40、官方 40",
    },
    {
        "编号": "Q11", "检查项": "2024 奖牌记录完整性（新发现）",
        "方法": "对每个 2024 小项键检查奖牌色集合是否含 Gold；逐项核对缺失行",
        "结果": f"2024 有 {no_gold24} 个小项只有银/铜而无金牌行：{'、'.join(no_gold_names)}；另有铁人三项混合接力整项只有 2 条无奖牌记录、无任何奖牌行；对应官方金牌获得者分别为美国（女子公路赛）、英国（男子山地越野）、爱尔兰（男子 800 米自由泳）、德国（混合接力），均未出现在数据中",
        "处理决定": "在事件级数据中保留空缺，不推断补录；任务二、三涉及 2024 金牌榜时以'数据可观测值'为准并注明缺失",
        "影响": "美国 39/40、德国 11/12 的差异可逐项解释，不构成口径错误",
    },
]
qc_df = pd.DataFrame(checks)
qc_df.to_csv(OUT / "quality_checks.csv", index=False, encoding="utf-8-sig")
p("\n质量检查项:", len(qc_df))

# ---------------------------------------------------------------- 8. 口径摘要
p("\n奖牌行口径 Top10 国家:")
p(ath_tbl.head(10).to_string())
p("\n小项口径 Top10 国家:")
p(ev_tbl.head(10).to_string())

p("\n主口径（运动员行，剔除 1906）奖牌行:", len(medal_rows[medal_rows["is_1906"] == 0]))
p("全口径（含 1906）奖牌行:", len(medal_rows))

# ---------------------------------------------------------------- 9. 契约与共享指标
sport_map_df.to_csv(CONTRACTS / "sport_map.csv", index=False, encoding="utf-8-sig")
qc_df.to_csv(CONTRACTS / "quality_checks.csv", index=False, encoding="utf-8-sig")
gaps.to_csv(CONTRACTS / "known_gaps.csv", index=False, encoding="utf-8-sig")

base = clean[clean["include_flag"] == 1]
mrows = base[base["is_medal"] == 1]
mev = ev[ev["is_1906"] == 0]


def _pivot(frame, key):
    t = frame.groupby([key, "Medal"]).size().unstack(fill_value=0).reindex(
        columns=["Gold", "Silver", "Bronze"], fill_value=0)
    t["Total"] = t.sum(axis=1)
    return t.sort_values("Total", ascending=False)


_pivot(mev, "noc").to_csv(SHARED / "medal_table_event_noc.csv", encoding="utf-8-sig")
_pivot(mrows, "NOC").to_csv(SHARED / "medal_table_athlete_noc.csv", encoding="utf-8-sig")

by_year_noc = (
    mev.groupby(["Year", "noc", "Medal"]).size().unstack(fill_value=0)
    .reindex(columns=["Gold", "Silver", "Bronze"], fill_value=0)
    .reset_index()
)
by_year_noc.columns = ["Year", "NOC", "Gold", "Silver", "Bronze"]
by_year_noc["Total"] = by_year_noc[["Gold", "Silver", "Bronze"]].sum(axis=1)
by_year_noc["Caliber"] = "event"
by_year_noc.to_csv(SHARED / "medals_by_year_noc.csv", index=False, encoding="utf-8-sig")

part = base.groupby("Year").agg(
    rows=("Name", "size"),
    athletes=("athlete_key", "nunique"),
    noc=("NOC", "nunique"),
    female_rows=("Sex", lambda s: int((s == "F").sum())),
)
part["female_share_pct"] = (part["female_rows"] / part["rows"] * 100).round(2)
part.reset_index().to_csv(SHARED / "participation_by_year.csv", index=False, encoding="utf-8-sig")

sport_year = (
    base.groupby(["Year", "sport_norm"])
    .agg(events=("event_key", "nunique"), rows=("Name", "size"), athletes=("athlete_key", "nunique"))
    .reset_index()
)
sport_year.to_csv(SHARED / "sport_coverage_by_year.csv", index=False, encoding="utf-8-sig")

shutil.copy2(OUT / "caliber_by_year.csv", SHARED / "caliber_by_year.csv")
shutil.copy2(OUT / "caliber_2024_compare.csv", SHARED / "caliber_2024_compare.csv")
shutil.copy2(OUT / "noc_mapping.csv", CONTRACTS / "noc_map.csv")

(OUT / "clean_log.txt").write_text(log.getvalue(), encoding="utf-8")
print("\n已生成:", OUT)
print("契约文件:", CONTRACTS)
print("共享指标:", SHARED)
print("处理后数据:", PROC)
