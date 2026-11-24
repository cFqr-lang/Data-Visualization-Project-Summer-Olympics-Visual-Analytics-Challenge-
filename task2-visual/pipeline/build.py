"""任务二数据管线入口。

用法（在 task2-visual/ 目录下）：
    python -m pipeline.build            # 生成全部图表 JSON + metrics_master.csv 并自检
    python -m pipeline.build --check-only
    python -m pipeline.build --include-1906
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime

from . import common
from .common import MEDAL_ORDER, OUT_DATA_DIR, OUT_FIG_DIR, SHARED_METRICS_DIR
from .metrics import (
    CALIBER_LABEL,
    aggregate_medals,
    country_gender,
    event_medals_by_year_sport,
    event_series_by_year,
    latest_medal_year,
    medal_rows_by_year,
    medals_by_noc_sport,
    participation_by_year,
    sport_lifeline,
)

# 九国矩阵：谱系只在注释层连接，主数据按 NOC 原样呈现
NATION_PANELS = [
    ("USA", "美国", ["USA"], ["1984 洛杉矶、1996 亚特兰大主场"]),
    ("URS", "苏联谱系", ["URS", "EUN", "RUS", "ROC", "AIN"],
     ["1988 苏联最后一届", "1992 独联体", "2020 ROC", "2024 AIN"]),
    ("GER", "德国谱系", ["GER", "FRG", "GDR"], ["1968-1988 两德分立", "1992 起统一"]),
    ("CHN", "中国", ["CHN"], ["1984 首次大规模参赛", "2008 北京主场"]),
    ("JPN", "日本", ["JPN"], ["1964 东京", "2020 东京"]),
    ("KOR", "韩国", ["KOR"], ["1988 汉城"]),
    ("GBR", "英国", ["GBR"], ["2012 伦敦"]),
    ("AUS", "澳大利亚", ["AUS"], ["2000 悉尼"]),
    ("HUN", "匈牙利", ["HUN"], ["早期奖牌强国"]),
]

MILESTONES = [
    (1900, "首批女性参赛"),
    (1928, "田径/体操向女子开放"),
    (1960, "罗马：女性规模扩张"),
    (1984, "洛杉矶：女子项目扩容"),
    (2012, "伦敦：所有项目设女子小项"),
    (2024, "巴黎：女性占比 49.1%"),
]

OFFICIAL_EVENT_COUNT = {2020: 339, 2024: 329}


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #
def _round(value, digits=4):
    return round(value, digits)


def _sort_key(item):
    return (item["gold"], item["silver"], item["bronze"])


def _rank_table(agg: dict, top: int | None = None) -> list[dict]:
    rows = []
    for (year, noc), colors in agg.items():
        rows.append({"year": year, "noc": noc, **colors,
                     "total": colors["gold"] + colors["silver"] + colors["bronze"]})
    rows.sort(key=_sort_key, reverse=True)
    return rows[:top] if top else rows


def _noc_totals(agg: dict) -> list[dict]:
    totals: dict = {}
    for (_year, noc), colors in agg.items():
        bucket = totals.setdefault(noc, {"gold": 0, "silver": 0, "bronze": 0})
        for color in bucket:
            bucket[color] += colors[color]
    rows = [{"noc": noc, **colors,
             "total": colors["gold"] + colors["silver"] + colors["bronze"]}
            for noc, colors in totals.items()]
    rows.sort(key=_sort_key, reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=False),
        encoding="utf-8",
    )


def _meta(figure_id, chart_id, title, caliber, denominator, includes_1906, notes):
    return {
        "figure_id": figure_id,
        "chart_id": chart_id,
        "title": title,
        "caliber": caliber,
        "caliber_label": CALIBER_LABEL.get(caliber, caliber),
        "denominator": denominator,
        "includes_1906": includes_1906,
        "data_version": common.DATA_VERSION,
        "generated_at": GENERATED_AT,
        "source": "data/raw/olympics_dataset.csv",
        "event_key_source": common.event_key_source(),
        "notes": notes,
    }


# --------------------------------------------------------------------------- #
# A1 双口径总榜 + 排名敏感性
# --------------------------------------------------------------------------- #
def build_a1(records):
    agg_cons = aggregate_medals(records, "conservative_event")
    agg_rows = aggregate_medals(records, "athlete_row")

    totals_rows = {row["noc"]: row for row in _noc_totals(agg_rows)}
    totals = []
    for row in _noc_totals(agg_cons)[:20]:
        row_rows = totals_rows.get(row["noc"], {})
        row["athlete_medal_rows"] = row_rows.get("total", 0)
        row["diff"] = row["athlete_medal_rows"] - row["total"]
        totals.append(row)

    records_with_1906 = ALL_RECORDS
    definitions = [
        ("athlete_row_1906", "运动员行口径 · 含 1906", "athlete_row", True),
        ("athlete_row", "运动员行口径 · 不含 1906", "athlete_row", False),
        ("conservative_event", "保守小项口径 · 不含 1906", "conservative_event", False),
        ("loose_event", "宽松小项口径 · 不含 1906", "loose_event", False),
    ]
    ranks_by_def = []
    union_nocs: list[str] = []
    for key, label, caliber, with_1906 in definitions:
        source = records_with_1906 if with_1906 else records
        ranked = _noc_totals(aggregate_medals(source, caliber))
        for item in ranked[:10]:
            if item["noc"] not in union_nocs:
                union_nocs.append(item["noc"])
        ranks_by_def.append({
            "id": key, "label": label, "caliber": caliber,
            "includes_1906": with_1906, "ranking": ranked[:12],
        })

    rank_lookup = {d["id"]: {r["noc"]: r["rank"] for r in d["ranking"]} for d in ranks_by_def}
    rank_changes = []
    for noc in union_nocs:
        before = rank_lookup["athlete_row"].get(noc)
        after = rank_lookup["conservative_event"].get(noc)
        if before is None or after is None:
            continue
        rank_changes.append({
            "noc": noc, "athlete_row_rank": before,
            "conservative_rank": after, "delta": before - after,
        })
    rank_changes.sort(key=lambda r: abs(r["delta"]), reverse=True)

    return {
        "meta": _meta(
            "Fig.2-1", "A1", "奖牌榜是口径的函数", "conservative_event+athlete_row",
            "NOC×届（历史累计）", False,
            ["主榜为保守小项口径；差额 = 运动员行奖牌 - 去重后奖牌，反映团体项目膨胀",
             "1906 届默认排除，仅在敏感性面板第一种定义中出现",
             "排名依据：金牌 > 银牌 > 铜牌"],
        ),
        "totals_top20": totals,
        "definitions": ranks_by_def,
        "rank_changes": rank_changes,
    }


# --------------------------------------------------------------------------- #
# A2 逐届演变 + 膨胀指数
# --------------------------------------------------------------------------- #
def build_a2(records, agg_cons):
    medal_year = medal_rows_by_year(records)
    part = participation_by_year(records)
    events = event_series_by_year(records)

    years = sorted(part)
    series = []
    for year in years:
        series.append({
            "year": year,
            "medal_events": 0,
            "medal_rows": sum(medal_year.get(year, {}).values()),
            "delegations": part[year]["delegations"],
            "athletes": part[year]["athletes"],
            "events_proxy": events.get(year, {}).get("proxy_total", 0),
            "events_official": OFFICIAL_EVENT_COUNT.get(year),
        })

    cons_year: dict = {}
    for (year, _noc), colors in agg_cons.items():
        cons_year[year] = cons_year.get(year, 0) + sum(colors.values())
    for item in series:
        item["medal_events"] = cons_year.get(item["year"], 0)

    base = series[0]
    for item in series:
        item["index"] = {
            "medals": _round(item["medal_events"] / base["medal_events"] * 100, 1),
            "delegations": _round(item["delegations"] / base["delegations"] * 100, 1),
            "athletes": _round(item["athletes"] / base["athletes"] * 100, 1),
            "events": _round(item["events_proxy"] / base["events_proxy"] * 100, 1),
        }

    by_year: dict = {}
    for row in _rank_table(agg_cons):
        by_year.setdefault(row["year"], []).append(row)
    bar_race = [{"year": year, "top": rows[:10]} for year, rows in sorted(by_year.items())]

    snapshot_years = [1896, 1960, 2000, 2024]
    snapshots = [
        {"year": year, "top": [r for r in by_year.get(year, [])][:8]}
        for year in snapshot_years
    ]

    return {
        "meta": _meta(
            "Fig.2-2", "A2", "奖牌在膨胀，榜单头部却长期稳定", "conservative_event",
            "每届", False,
            ["1916/1940/1944 停办，曲线上直接缺届而非 0",
             "1980/1984 抵制届不补零，留白",
             "2020+ 小项数为 Sport×Sex 代理值，另附官方 339/329 校准点"],
        ),
        "series": series,
        "bar_race": bar_race,
        "snapshots": snapshots,
        "missing_years": [1916, 1940, 1944],
    }


# --------------------------------------------------------------------------- #
# B1 九国命运矩阵
# --------------------------------------------------------------------------- #
def build_b1(records, agg_cons):
    panels = []
    for key, label, nocs, notes in NATION_PANELS:
        series = []
        for noc in nocs:
            points = []
            for year in sorted({r.year for r in records if r.noc == noc}):
                colors = agg_cons.get((year, noc), {"gold": 0, "silver": 0, "bronze": 0})
                points.append({
                    "year": year, "gold": colors["gold"],
                    "silver": colors["silver"], "bronze": colors["bronze"],
                    "total": sum(colors.values()),
                })
            if points:
                series.append({"noc": noc, "points": points})
        panels.append({"key": key, "label": label, "nocs": nocs,
                       "series": series, "notes": notes})

    return {
        "meta": _meta(
            "Fig.2-3", "B1", "四种国家模式并存：长盛、骤起骤落、分立统一、后发崛起",
            "conservative_event", "每届", False,
            ["政体按 NOC 原样呈现，谱系只在注释层连接，不在主数据合并",
             "某届无参赛记录的年份留空，不补 0"],
        ),
        "panels": panels,
    }


# --------------------------------------------------------------------------- #
# C1 她的奥运双弧线
# --------------------------------------------------------------------------- #
def build_c1(records):
    part = participation_by_year(records)
    events = event_series_by_year(records)

    women_per_year: dict = {}
    for rec in records:
        if rec.sex == "F":
            women_per_year.setdefault(rec.year, set()).add(rec.noc)
    women_per_year = {year: len(nocs) for year, nocs in women_per_year.items()}

    series = []
    for year, info in part.items():
        series.append({
            "year": year,
            "male_rows": info["male_rows"],
            "female_rows": info["female_rows"],
            "female_share": info["female_share"],
            "delegations": info["delegations"],
            "delegations_with_women": women_per_year.get(year, 0),
            "women_events": events.get(year, {}).get("women", 0),
            "men_events": events.get(year, {}).get("men", 0),
            "mixed_events": events.get(year, {}).get("mixed", 0),
        })

    return {
        "meta": _meta(
            "Fig.2-4", "C1", "女性从 0 走到 49.1%，但走的是三次跃迁而非直线",
            "athlete_row", "全部参赛记录", False,
            ["分母为运动员行；团体项目会抬高人数，代表层面女性参与见 delegations_with_women",
             "女子/混合小项 2020+ 为 Sport×Sex 估计值"],
        ),
        "series": series,
        "milestones": [{"year": y, "text": t} for y, t in MILESTONES],
    }


# --------------------------------------------------------------------------- #
# C2 参与 ≠ 产出
# --------------------------------------------------------------------------- #
def _c2_view(records, years, view_id, label, min_rows=20, min_medals=3):
    stats = country_gender(records, set(years))
    points = []
    for noc, bucket in stats.items():
        if bucket["rows"] < min_rows or bucket["medal_rows"] < min_medals:
            continue
        gender_medals = bucket["female_medals"] + bucket["male_medals"]
        points.append({
            "noc": noc,
            "rows": bucket["rows"],
            "female_share": _round(bucket["female_rows"] / bucket["rows"]),
            "female_medals": bucket["female_medals"],
            "male_medals": bucket["male_medals"],
            "mixed_medals": bucket["mixed_medals"],
            "female_medal_share": _round(bucket["female_medals"] / gender_medals) if gender_medals else None,
        })
    return {"id": view_id, "label": label, "years": list(years),
            "min_rows": min_rows, "min_medals": min_medals, "points": points}


def build_c2(records):
    years = sorted({r.year for r in records})
    last3 = years[-3:]
    views = [
        _c2_view(records, [years[-1]], f"{years[-1]}", f"{years[-1]} 单届"),
        _c2_view(records, last3, "last3", f"{last3[0]}–{last3[-1]} 三届合并"),
    ]
    return {
        "meta": _meta(
            "Fig.2-5", "C2", "女性参赛占比高，不等于女性奖牌占比高",
            "athlete_row", "该国该届全部记录", False,
            ["混合项目单列，不并入男女奖牌占比",
             "female_medal_share 为 None 表示该国无男女分项奖牌",
             "仅保留记录数 ≥ 20 且奖牌行 ≥ 3 的国家（否则占比无统计意义）"],
        ),
        "views": views,
    }


# --------------------------------------------------------------------------- #
# D1 项目生命线
# --------------------------------------------------------------------------- #
def build_d1(records):
    lifeline = sport_lifeline(records)
    events = event_series_by_year(records)
    max_year = max(events) if events else 0

    retired = [row for row in lifeline if row["status"] == "retired" and row["medals"] >= 2]
    retired.sort(key=lambda r: (-r["last"], -r["medals"]))
    added = [row for row in lifeline if row["first"] >= 1988]
    added.sort(key=lambda r: (r["first"], r["sport"]))

    counts = [{"year": year, "proxy": info["proxy_total"],
               "official": OFFICIAL_EVENT_COUNT.get(year)}
              for year, info in sorted(events.items())]

    return {
        "meta": _meta(
            "Fig.2-6", "D1", "核心项目稳定，边缘项目不断轮换",
            "conservative_event", "每届", False,
            ["项目归属按 Sport 归类，少量改名项目已归并",
             "1908/1920 夏奥中的花样滑冰、冰球按数据原样保留",
             f"小项数为估计值，最后一届 {max_year}；官方 2020=339、2024=329 仅作校准点"],
        ),
        "sports": lifeline,
        "event_counts": counts,
        "highlights": {"retired": retired[:12], "added": added},
    }


# --------------------------------------------------------------------------- #
# B2 国家效率前沿
# --------------------------------------------------------------------------- #
def build_b2(records, agg_cons):
    years_by_noc: dict = {}
    players: dict = {}
    for rec in records:
        years_by_noc.setdefault(rec.noc, set()).add(rec.year)
        players.setdefault(rec.noc, {}).setdefault(rec.year, set()).add(rec.player_id)

    medals: dict = {}
    for (_year, noc), colors in agg_cons.items():
        medals[noc] = medals.get(noc, 0) + sum(colors.values())

    points = []
    for noc, years in years_by_noc.items():
        editions = len(years)
        if editions < 5:
            continue
        total = medals.get(noc, 0)
        if total < 10:
            continue
        athletes = sum(len(players[noc][year]) for year in years)
        avg_athletes = athletes / editions
        avg_medals = total / editions
        points.append({
            "noc": noc,
            "editions": editions,
            "total_medals": total,
            "avg_athletes": _round(avg_athletes, 2),
            "avg_medals": _round(avg_medals, 2),
            "efficiency": _round(avg_medals / avg_athletes, 4) if avg_athletes else 0,
        })
    points.sort(key=lambda row: (-row["avg_medals"], -row["avg_athletes"]))
    for index, row in enumerate(points, start=1):
        row["rank"] = index

    return {
        "meta": _meta(
            "Fig.2-7", "B2", "参赛规模与奖牌非线性，小国站在效率前沿",
            "conservative_event", "场均参赛人数（去重运动员）", False,
            ["X 为该国每届平均去重运动员数，Y 为每届平均保守小项奖牌数，均为 log 轴",
             "点大小为参赛届数；仅保留参赛 ≥ 5 届且累计奖牌 ≥ 10 枚的 NOC",
             "不引入 GDP / 人口等外部数据，效率仅指奖牌 / 参赛人数"],
        ),
        "points": points,
    }


# --------------------------------------------------------------------------- #
# D2 项目结构变迁（themeRiver）
# --------------------------------------------------------------------------- #
D2_SPORTS = [
    "Athletics", "Swimming", "Wrestling", "Gymnastics",
    "Boxing", "Shooting", "Cycling",
]


def build_d2(records):
    by_sport = event_medals_by_year_sport(records)
    years = sorted({rec.year for rec in records})
    categories = D2_SPORTS + ["Other"]

    river = []
    totals = {name: 0 for name in categories}
    for year in years:
        for sport in D2_SPORTS:
            value = by_sport.get((year, sport), 0)
            river.append([f"{year}-01-01", value, sport])
            totals[sport] += value
        other = sum(
            value for (y, sport), value in by_sport.items()
            if y == year and sport not in D2_SPORTS
        )
        river.append([f"{year}-01-01", other, "Other"])
        totals["Other"] += other

    return {
        "meta": _meta(
            "Fig.2-8", "D2", "核心大类份额稳定，新兴类在边缘上升",
            "conservative_event", "份额", False,
            ["河流宽度为该届各 Sport 的保守小项奖牌数，6–8 类 + Other",
             "份额按当届总数归一，跨国膨胀被抵消",
             "2020+ 泛化小项取下界，绝对值可能低估"],
        ),
        "categories": categories,
        "river": river,
        "totals": [
            {"name": name, "medals": totals[name]}
            for name in sorted(totals, key=lambda key: -totals[key])
        ],
    }


# --------------------------------------------------------------------------- #
# X1 国家 × 项目优势矩阵（lift）
# --------------------------------------------------------------------------- #
def build_x1(records):
    counts = medals_by_noc_sport(records)
    noc_totals: dict = {}
    sport_totals: dict = {}
    for (noc, sport), value in counts.items():
        noc_totals[noc] = noc_totals.get(noc, 0) + value
        sport_totals[sport] = sport_totals.get(sport, 0) + value

    grand = sum(counts.values())
    nocs = sorted(noc_totals, key=lambda noc: (-noc_totals[noc], noc))[:12]
    sports = sorted(sport_totals, key=lambda sport: (-sport_totals[sport], sport))[:10]

    cells = []
    max_lift = 0.0
    for noc in nocs:
        for sport in sports:
            medals = counts.get((noc, sport), 0)
            expected = noc_totals[noc] * sport_totals[sport] / grand if grand else 0
            lift = medals / expected if expected else 0.0
            max_lift = max(max_lift, lift)
            cells.append({
                "noc": noc, "sport": sport, "medals": medals,
                "lift": _round(lift, 2),
            })

    return {
        "meta": _meta(
            "Fig.2-9", "X1", "传统优势写在项目里：国家 × 项目 lift",
            "conservative_event", "Top 12 NOC × Top 10 项目", False,
            ["lift = (该国该项目奖牌 / 该国全部奖牌) ÷ (该项目全部奖牌 / 全球奖牌)",
             "lift = 1 表示与全局结构一致，> 1 为相对专长，0 表示该项目无奖牌",
             "仅用赛题数据；Top 12 NOC 与 Top 10 项目均按保守小项奖牌数选取"],
        ),
        "nocs": [{"noc": noc, "medals": noc_totals[noc]} for noc in nocs],
        "sports": [{"sport": sport, "medals": sport_totals[sport]} for sport in sports],
        "cells": cells,
        "max_lift": _round(max_lift + 0.05, 1),
    }


# --------------------------------------------------------------------------- #
# X2 项目性别差哑铃
# --------------------------------------------------------------------------- #
def build_x2(records):
    latest = max(r.year for r in records)
    view = [r for r in records if r.year == latest]

    female: dict = {}
    male: dict = {}
    medal_rows: dict = {}
    female_medals: dict = {}
    for rec in view:
        target = female if rec.sex == "F" else male
        target.setdefault(rec.sport_key, set()).add(rec.player_id)
        if rec.medal in MEDAL_ORDER:
            medal_rows[rec.sport_key] = medal_rows.get(rec.sport_key, 0) + 1
            if rec.sex == "F":
                female_medals[rec.sport_key] = female_medals.get(rec.sport_key, 0) + 1

    sports = []
    for sport in set(female) | set(male):
        women = len(female.get(sport, ()))
        men = len(male.get(sport, ()))
        if women + men < 10:
            continue
        female_share = women / (women + men)
        total_medals = medal_rows.get(sport, 0)
        sports.append({
            "sport": sport,
            "female_athletes": women,
            "male_athletes": men,
            "athletes": women + men,
            "female_share": _round(female_share),
            "male_share": _round(1 - female_share),
            "gap_pp": _round((2 * female_share - 1) * 100, 1),
            "medal_rows": total_medals,
            "female_medal_share": (
                _round(female_medals.get(sport, 0) / total_medals)
                if total_medals else None
            ),
        })
    sports.sort(key=lambda row: (-row["female_share"], row["sport"]))
    for index, row in enumerate(sports, start=1):
        row["rank"] = index

    return {
        "meta": _meta(
            "Fig.2-10", "X2", "性别差集中在少数项目，多数项目已接近 50:50",
            "athlete_row", f"{latest} 去重运动员", False,
            [f"两端为 {latest} 各项目女性 / 男性去重参赛人数占比，连线长度 = 差距（百分点）",
             "仅保留男女合计 ≥ 10 人的项目；Artistic Swimming、Rhythmic Gymnastics 为女子专属，呈 100% / 0%",
             "女子奖牌占比按运动员行统计（含混合项目），只在 tooltip 中作产出参考，不参与排序",
             "2020+ 小项名不可还原，故本图用人均参赛结构而非小项数衡量性别差"],
        ),
        "year": latest,
        "sports": sports,
    }


# --------------------------------------------------------------------------- #
# 统一底表
# --------------------------------------------------------------------------- #
def write_metrics_master(records, agg_cons, agg_rows, actual, x1, x2):
    part = participation_by_year(records)
    events = event_series_by_year(records)
    cons_totals = _noc_totals(agg_cons)
    row_totals = {row["noc"]: row for row in _noc_totals(agg_rows)}
    cons_year: dict = {}
    for (year, _noc), colors in agg_cons.items():
        cons_year[year] = cons_year.get(year, 0) + sum(colors.values())
    medal_year = medal_rows_by_year(records)

    rows = []

    def add(metric, scope, value, unit, caliber, year="", noc="", notes=""):
        rows.append({
            "metric": metric, "scope": scope, "year": year, "noc": noc,
            "value": value, "unit": unit, "caliber": caliber,
            "includes_1906": False, "data_version": common.DATA_VERSION,
            "notes": notes,
        })

    for key in ("rows", "medals", "noc_count", "sport_count"):
        add(key, "全数据（含 1906）", actual[key], "count", "-", notes="自检项")

    for color in MEDAL_ORDER:
        add(f"{color.lower()}_rows", "全数据（含 1906）",
            actual[color.lower()], "rows", "athlete_row")

    for year, info in part.items():
        add("conservative_medals", "每届", cons_year.get(year, 0),
            "medals", "conservative_event", year=year)
        add("medal_rows", "每届", sum(medal_year.get(year, {}).values()),
            "rows", "athlete_row", year=year)
        add("delegations", "每届", info["delegations"], "count", "-", year=year)
        add("athletes", "每届", info["athletes"], "count", "-", year=year)
        add("female_share", "每届", info["female_share"], "ratio", "athlete_row", year=year)
        add("events_proxy", "每届", events.get(year, {}).get("proxy_total", 0),
            "count", "conservative_event", year=year, notes="2020+ 为估计值")

    for row in cons_totals:
        add("conservative_medals_total", "NOC 历史累计", row["total"],
            "medals", "conservative_event", noc=row["noc"], notes=f"rank={row['rank']}")
        add("gold_total", "NOC 历史累计", row["gold"],
            "medals", "conservative_event", noc=row["noc"])
        add("medal_rows_total", "NOC 历史累计",
            row_totals.get(row["noc"], {}).get("total", 0),
            "rows", "athlete_row", noc=row["noc"], notes="与 conservative 的差额即团体膨胀")

    for row in x1["cells"]:
        if row["medals"] <= 0:
            continue
        add("specialization_lift", "NOC×Sport", row["lift"], "lift",
            "conservative_event", noc=row["noc"],
            notes=f"sport={row['sport']}; medals={row['medals']}")

    for row in x2["sports"]:
        notes = f"sport={row['sport']}; female={row['female_athletes']}, male={row['male_athletes']}"
        add("female_participation_share", "Sport 2024", row["female_share"],
            "ratio", "athlete_row", year=x2["year"], notes=notes)
        add("male_participation_share", "Sport 2024", row["male_share"],
            "ratio", "athlete_row", year=x2["year"], notes=notes)
        add("gender_gap_pp", "Sport 2024", row["gap_pp"],
            "percentage_points", "athlete_row", year=x2["year"], notes=notes)
        if row["female_medal_share"] is not None:
            add("female_medal_share", "Sport 2024", row["female_medal_share"],
                "ratio", "athlete_row", year=x2["year"], notes=notes)

    path = SHARED_METRICS_DIR / "metrics_master.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path, len(rows)


# --------------------------------------------------------------------------- #
# 自检
# --------------------------------------------------------------------------- #
EXPECTED = {
    "rows": 252565, "medals": 38818, "gold": 13002, "silver": 12746,
    "bronze": 13070, "noc_count": 234, "rows_1906": 1733,
}


def run_checks():
    all_records = common.load_records(include_1906=True)
    view = [r for r in all_records if r.year != common.EXCLUDED_YEAR]
    medals = [r for r in all_records if r.medal in MEDAL_ORDER]
    latest = max(r.year for r in view)
    female_latest = [r for r in view if r.year == latest and r.sex == "F"]
    latest_rows = [r for r in view if r.year == latest]

    actual = {
        "rows": len(all_records),
        "medals": len(medals),
        "gold": sum(1 for r in medals if r.medal == "Gold"),
        "silver": sum(1 for r in medals if r.medal == "Silver"),
        "bronze": sum(1 for r in medals if r.medal == "Bronze"),
        "noc_count": len({r.noc for r in all_records}),
        "sport_count": len({r.sport_key for r in all_records}),
        "rows_1906": len(all_records) - len(view),
        "rows_excl_1906": len(view),
        "medals_excl_1906": sum(1 for r in view if r.medal in MEDAL_ORDER),
        "female_share_latest": round(len(female_latest) / len(latest_rows), 4),
        "latest_year": latest,
    }
    checks = []
    for key in ("rows", "medals", "gold", "silver", "bronze", "noc_count", "rows_1906"):
        checks.append({"check": key, "expected": EXPECTED[key],
                       "actual": actual[key], "pass": actual[key] == EXPECTED[key]})
    checks.append({
        "check": "female_share_latest", "expected": "0.45 ~ 0.52",
        "actual": actual["female_share_latest"],
        "pass": 0.45 <= actual["female_share_latest"] <= 0.52,
    })
    return actual, checks


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
GENERATED_AT = ""
ALL_RECORDS: list = []


def main(argv=None):
    global GENERATED_AT, ALL_RECORDS
    parser = argparse.ArgumentParser(description="任务二数据管线")
    parser.add_argument("--include-1906", action="store_true", help="主视图包含 1906 届")
    parser.add_argument("--check-only", action="store_true", help="只跑自检，不写文件")
    parser.add_argument("--no-check", action="store_true", help="跳过自检失败退出")
    args = parser.parse_args(argv)

    GENERATED_AT = datetime.now().astimezone().isoformat(timespec="seconds")
    actual, checks = run_checks()
    failed = [c for c in checks if not c["pass"]]
    for item in checks:
        flag = "PASS" if item["pass"] else "FAIL"
        print(f"[{flag}] {item['check']}: {item['actual']} (期望 {item['expected']})")
    if args.check_only:
        return 1 if failed else 0

    ALL_RECORDS = common.load_records(include_1906=True)
    records = [r for r in ALL_RECORDS if args.include_1906 or r.year != common.EXCLUDED_YEAR]
    agg_cons = aggregate_medals(records, "conservative_event")
    agg_rows = aggregate_medals(records, "athlete_row")

    x1 = build_x1(records)
    x2 = build_x2(records)
    figures = {
        "fig-A1.json": build_a1(records),
        "fig-A2.json": build_a2(records, agg_cons),
        "fig-B1.json": build_b1(records, agg_cons),
        "fig-C1.json": build_c1(records),
        "fig-C2.json": build_c2(records),
        "fig-D1.json": build_d1(records),
        "fig-B2.json": build_b2(records, agg_cons),
        "fig-D2.json": build_d2(records),
        "fig-X1.json": x1,
        "fig-X2.json": x2,
    }
    for name, payload in figures.items():
        _write_json(OUT_FIG_DIR / name, payload)

    meta = {
        "schema": "task2-figure-v1",
        "data_version": common.DATA_VERSION,
        "generated_at": GENERATED_AT,
        "source": common.raw_fingerprint(),
        "event_key_source": common.event_key_source(),
        "includes_1906": args.include_1906,
        "calibers": CALIBER_LABEL,
        "checks": checks,
        "counts": {**actual, "sports_after_alias": actual["sport_count"]},
        "figures": [
            {"figure_id": p["meta"]["figure_id"], "chart_id": p["meta"]["chart_id"],
             "title": p["meta"]["title"], "path": f"figures/{name}",
             "caliber": p["meta"]["caliber"]}
            for name, p in figures.items()
        ],
    }
    _write_json(OUT_DATA_DIR / "meta.json", meta)
    _write_json(OUT_DATA_DIR / "index.json", {
        "schema": "task2-figure-v1",
        "data_version": common.DATA_VERSION,
        "generated_at": GENERATED_AT,
        "figures": meta["figures"],
    })

    metrics_path, metric_rows = write_metrics_master(records, agg_cons, agg_rows, actual, x1, x2)
    print(f"\n写出 {len(figures)} 个图表 JSON → {OUT_FIG_DIR}")
    print(f"写出 {metric_rows} 行底表 → {metrics_path}")
    print(f"最后一届 {latest_medal_year(records)}；自检失败 {len(failed)} 项")
    return 1 if failed and not args.no_check else 0


if __name__ == "__main__":
    sys.exit(main())
