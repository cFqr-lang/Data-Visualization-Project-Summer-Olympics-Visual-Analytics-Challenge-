"""任务三 · S5 奖牌的通货膨胀（数据管线，不含渲染）。

输出 `data/inflation_data.json`；渲染由 `task3-insights/site/render.mjs` 完成。
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from collections import defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
T3_DIR = REPO_ROOT / "task3-insights"
DATA_DIR = T3_DIR / "data"

PIPELINE = REPO_ROOT / "task2-visual" / "pipeline"
_pkg = types.ModuleType("t2pipeline")
_pkg.__path__ = [str(PIPELINE)]
sys.modules["t2pipeline"] = _pkg


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "t2pipeline"
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_common = _load("t2pipeline.common", PIPELINE / "common.py")
_metrics = _load("t2pipeline.metrics", PIPELINE / "metrics.py")


def _total(agg, key) -> int:
    d = agg.get(key, {})
    return int(d.get("gold", 0) + d.get("silver", 0) + d.get("bronze", 0))


def conservative_by_sex(records):
    seen = set()
    out = defaultdict(int)
    for rec in records:
        if rec.medal not in _metrics.MEDAL_ORDER:
            continue
        key = _metrics._unit_key(rec)
        if key in seen:
            continue
        seen.add(key)
        if "mixed" in rec.event:
            s = "mixed"
        elif rec.sex == "F":
            s = "women"
        else:
            s = "men"
        out[(rec.year, s)] += 1
    return dict(out)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    records = _common.load_records(include_1906=False)
    agg = _metrics.aggregate_medals(records, "conservative_event")

    by_year: dict = defaultdict(lambda: {"nocs": set(), "rows": 0, "players": set()})
    for rec in records:
        b = by_year[rec.year]
        b["nocs"].add(rec.noc)
        b["rows"] += 1
        b["players"].add(rec.player_id)
    years = sorted(by_year)

    totals = {y: sum(_total(agg, (y, n)) for n in by_year[y]["nocs"]) for y in years}
    deleg = {y: len(by_year[y]["nocs"]) for y in years}
    rows = {y: by_year[y]["rows"] for y in years}
    players = {y: len(by_year[y]["players"]) for y in years}
    per_1000 = {y: round(totals[y] / rows[y] * 1000, 2) for y in years}
    per_deleg = {y: round(totals[y] / deleg[y], 3) for y in years}

    medal_nocs = {y: sum(1 for n in by_year[y]["nocs"] if _total(agg, (y, n)) > 0) for y in years}
    nocs_sorted = {y: sorted((_total(agg, (y, n)) for n in by_year[y]["nocs"]), reverse=True)
                   for y in years}
    top5_share = {y: round(sum(nocs_sorted[y][:5]) / totals[y], 4) for y in years}
    top10_share = {y: round(sum(nocs_sorted[y][:10]) / totals[y], 4) for y in years}

    sex = conservative_by_sex(records)
    sex_by_year = {y: {"men": sex.get((y, "men"), 0), "women": sex.get((y, "women"), 0),
                       "mixed": sex.get((y, "mixed"), 0)} for y in years}

    lifeline = {s["sport"]: s["first"] for s in _metrics.sport_lifeline(records)}
    by_sport = _metrics.event_medals_by_year_sport(records)
    bands = [("1896 核心", lambda f: f == 1896),
             ("1900–1924", lambda f: 1900 <= f <= 1924),
             ("1928–1948", lambda f: 1928 <= f <= 1948),
             ("1952–1976", lambda f: 1952 <= f <= 1976),
             ("1984–2024 新增", lambda f: f >= 1984)]
    vintage = defaultdict(lambda: defaultdict(int))
    for (y, sport), cnt in by_sport.items():
        f = lifeline.get(sport, y)
        band = next((name for name, fn in bands if fn(f)), "其他")
        vintage[y][band] += cnt
    vintage_by_year = {y: dict(vintage[y]) for y in years}
    band_order = [b[0] for b in bands] + ["其他"]

    out = {
        "meta": {
            "chartSet": "Fig3-8..3-10", "topic": "S5 medal inflation",
            "caliber": "conservative_event",
            "caliber_label": _metrics.CALIBER_LABEL["conservative_event"],
            "includes_1906": False, "data_version": "v1.0",
            "source": _common.raw_fingerprint(),
            "generated_at": date.today().isoformat(),
        },
        "years": years,
        "totals": totals, "delegations": deleg, "rows": rows, "players": players,
        "per_1000_rows": per_1000, "per_delegation": per_deleg,
        "medal_nocs": medal_nocs, "top5_share": top5_share, "top10_share": top10_share,
        "sex_by_year": sex_by_year,
        "vintage_by_year": vintage_by_year, "band_order": band_order,
    }
    (DATA_DIR / "inflation_data.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("totals 1896->2024:", totals[1896], "->", totals[2024],
          "= %.2fx" % (totals[2024] / totals[1896]))
    print("per1000 1896->2024:", per_1000[1896], "->", per_1000[2024])
    print("per_deleg 1896->2024:", per_deleg[1896], "->", per_deleg[2024])
    print("medal_nocs 1896->2024:", medal_nocs[1896], "->", medal_nocs[2024])
    print("top5 share 1896->2024: %.3f -> %.3f" % (top5_share[1896], top5_share[2024]))
    print("top10 share 1896->2024: %.3f -> %.3f" % (top10_share[1896], top10_share[2024]))
    s = sex_by_year[2024]
    print("2024 sex split women/men/mixed:", s["women"], s["men"], s["mixed"],
          "women share %.3f" % (s["women"] / (s["women"] + s["men"] + s["mixed"])))
    print("OK ->", T3_DIR)


if __name__ == "__main__":
    main()
