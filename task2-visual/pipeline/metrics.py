"""口径聚合与指标计算。纯函数，输入 list[Record]，输出可直接序列化的结构。"""

from __future__ import annotations

from collections import Counter, defaultdict

from .common import GENERIC_EVENTS, MEDAL_ORDER, Record

CALIBERS = ("athlete_row", "conservative_event", "loose_event")

CALIBER_LABEL = {
    "athlete_row": "运动员行口径（团体项目按人计行）",
    "conservative_event": "保守小项口径（团体项目每国每小项每色计 1 枚，2020+ 取下界）",
    "loose_event": "宽松小项口径（2020+ 泛化小项取上界）",
}


def _unit_key(rec: Record) -> tuple:
    """去重单元：泛化小项按 Sport×Sex 归组，具体小项按 (Sport, Event)。"""
    if rec.generic:
        unit = (rec.sport_key, rec.sex)
    else:
        unit = (rec.sport_key, rec.event)
    return (rec.year, rec.noc, rec.medal, unit)


def _empty() -> dict:
    return {"gold": 0, "silver": 0, "bronze": 0}


def aggregate_medals(records: list[Record], caliber: str = "conservative_event") -> dict:
    """返回 {(year, noc): {gold, silver, bronze}}。"""
    if caliber not in CALIBERS:
        raise ValueError(f"未知口径：{caliber}")

    out: dict = defaultdict(_empty)
    if caliber == "athlete_row":
        for rec in records:
            if rec.medal in MEDAL_ORDER:
                out[(rec.year, rec.noc)][rec.medal.lower()] += 1
        return dict(out)

    seen: set = set()
    generic_extra: Counter = Counter()
    for rec in records:
        if rec.medal not in MEDAL_ORDER:
            continue
        key = _unit_key(rec)
        if rec.generic:
            generic_extra[key] += 1
        if key in seen:
            continue
        seen.add(key)
        out[(rec.year, rec.noc)][rec.medal.lower()] += 1

    if caliber == "loose_event":
        for key, rows in generic_extra.items():
            year, noc = key[0], key[1]
            out[(year, noc)][key[2].lower()] += rows - 1

    return dict(out)


def medal_rows_by_year(records: list[Record]) -> dict[int, dict]:
    out: dict = defaultdict(_empty)
    for rec in records:
        if rec.medal in MEDAL_ORDER:
            out[rec.year][rec.medal.lower()] += 1
    return dict(out)


def participation_by_year(records: list[Record]) -> dict[int, dict]:
    """每届：参赛行数、去重运动员数、代表团数、女/男行数。"""
    rows: dict = defaultdict(int)
    female: dict = defaultdict(int)
    players: dict = defaultdict(set)
    nocs: dict = defaultdict(set)
    for rec in records:
        rows[rec.year] += 1
        if rec.sex == "F":
            female[rec.year] += 1
        players[rec.year].add(rec.player_id)
        nocs[rec.year].add(rec.noc)
    return {
        year: {
            "rows": rows[year],
            "athletes": len(players[year]),
            "female_rows": female[year],
            "male_rows": rows[year] - female[year],
            "female_share": round(female[year] / rows[year], 4) if rows[year] else 0.0,
            "delegations": len(nocs[year]),
        }
        for year in sorted(rows)
    }


def event_series_by_year(records: list[Record]) -> dict[int, dict]:
    """小项数代理：具体小项逐项计数，泛化小项按 Sport×Sex 计 1。"""
    specific: dict = defaultdict(set)
    generic: dict = defaultdict(set)
    women: dict = defaultdict(set)
    men: dict = defaultdict(set)
    mixed: dict = defaultdict(set)
    for rec in records:
        if rec.generic:
            unit = (rec.sport_key, rec.sex)
            generic[rec.year].add(unit)
        else:
            unit = (rec.sport_key, rec.event)
            specific[rec.year].add(unit)
        name = rec.event
        if "mixed" in name:
            mixed[rec.year].add(unit)
        elif "women" in name or rec.sex == "F":
            women[rec.year].add(unit)
        else:
            men[rec.year].add(unit)
    years = sorted(set(specific) | set(generic))
    return {
        year: {
            "specific": len(specific[year]),
            "generic": len(generic[year]),
            "proxy_total": len(specific[year]) + len(generic[year]),
            "women": len(women[year]),
            "men": len(men[year]),
            "mixed": len(mixed[year]),
        }
        for year in years
    }


def country_gender(records: list[Record], years: set[int]) -> dict[str, dict]:
    """（女/男）参赛与奖牌行，混合项目单列。"""
    out: dict = defaultdict(lambda: {
        "rows": 0, "female_rows": 0, "male_rows": 0,
        "medal_rows": 0, "female_medals": 0, "male_medals": 0, "mixed_medals": 0,
    })
    for rec in records:
        if rec.year not in years:
            continue
        bucket = out[rec.noc]
        bucket["rows"] += 1
        if rec.sex == "F":
            bucket["female_rows"] += 1
        else:
            bucket["male_rows"] += 1
        if rec.medal not in MEDAL_ORDER:
            continue
        bucket["medal_rows"] += 1
        if "mixed" in rec.event:
            bucket["mixed_medals"] += 1
        elif rec.sex == "F":
            bucket["female_medals"] += 1
        else:
            bucket["male_medals"] += 1
    return dict(out)


def sport_lifeline(records: list[Record]) -> list[dict]:
    """项目生命线：首次/最近出现、参赛届数、保守小项口径奖牌数。"""
    first: dict = {}
    last: dict = {}
    editions: dict = defaultdict(set)
    medal_units: dict = defaultdict(set)
    for rec in records:
        sport = rec.sport_key
        first[sport] = min(first.get(sport, rec.year), rec.year)
        last[sport] = max(last.get(sport, rec.year), rec.year)
        editions[sport].add(rec.year)
        if rec.medal in MEDAL_ORDER:
            medal_units[sport].add(_unit_key(rec))
    max_year = max(last.values()) if last else 0
    rows = []
    for sport in sorted(first):
        rows.append({
            "sport": sport,
            "first": first[sport],
            "last": last[sport],
            "editions": len(editions[sport]),
            "medals": len(medal_units[sport]),
            "status": "active" if last[sport] >= max_year else "retired",
        })
    rows.sort(key=lambda r: (r["first"], r["sport"]))
    return rows


def medals_by_noc_sport(records: list[Record]) -> dict:
    """保守小项口径下，各 NOC × Sport 的去重奖牌数。{(noc, sport): count}"""
    seen: set = set()
    out: Counter = Counter()
    for rec in records:
        if rec.medal not in MEDAL_ORDER:
            continue
        key = _unit_key(rec)
        if key in seen:
            continue
        seen.add(key)
        out[(rec.noc, rec.sport_key)] += 1
    return dict(out)


def event_medals_by_year_sport(records: list[Record]) -> dict:
    """保守小项口径下，每届各 Sport 的去重奖牌数。{(year, sport): count}"""
    seen: set = set()
    out: Counter = Counter()
    for rec in records:
        if rec.medal not in MEDAL_ORDER:
            continue
        key = _unit_key(rec)
        if key in seen:
            continue
        seen.add(key)
        out[(rec.year, rec.sport_key)] += 1
    return dict(out)


def latest_medal_year(records: list[Record]) -> int:
    return max((rec.year for rec in records if rec.medal in MEDAL_ORDER), default=0)
