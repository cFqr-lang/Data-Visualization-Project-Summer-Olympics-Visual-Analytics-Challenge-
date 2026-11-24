"""任务三 · S5 奖牌的通货膨胀：总量扩张、结构性来源与头部稀释。

复用任务二口径（保守小项主口径；1906 排除）。
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from collections import defaultdict
from pathlib import Path

import numpy as np

from style import PRINT, badge, finalize, source
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[2]
T3_DIR = REPO_ROOT / "task3-insights"
EXPORTS = T3_DIR / "exports"
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
    EXPORTS.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    records = _common.load_records(include_1906=False)
    agg = _metrics.aggregate_medals(records, "conservative_event")

    # 每届总量、代表团、参赛行、去重运动员
    by_year: dict = defaultdict(lambda: {"nocs": set(), "rows": 0, "players": set(),
                                          "medals": 0})
    for rec in records:
        b = by_year[rec.year]
        b["nocs"].add(rec.noc)
        b["rows"] += 1
        b["players"].add(rec.player_id)
    years = sorted(by_year)
    for y in years:
        by_year[y]["medals"] = sum(_total(agg, (y, n)) for n in by_year[y]["nocs"])

    totals = {y: by_year[y]["medals"] for y in years}
    deleg = {y: len(by_year[y]["nocs"]) for y in years}
    rows = {y: by_year[y]["rows"] for y in years}
    players = {y: len(by_year[y]["players"]) for y in years}

    per_1000 = {y: totals[y] / rows[y] * 1000 for y in years}
    per_deleg = {y: totals[y] / deleg[y] for y in years}

    # 每届获奖 NOC 数与头部集中度
    medal_nocs = {y: sum(1 for n in by_year[y]["nocs"] if _total(agg, (y, n)) > 0) for y in years}
    nocs_sorted = {y: sorted((_total(agg, (y, n)) for n in by_year[y]["nocs"]), reverse=True)
                   for y in years}
    top5_share = {y: sum(nocs_sorted[y][:5]) / totals[y] for y in years}
    top10_share = {y: sum(nocs_sorted[y][:10]) / totals[y] for y in years}

    # 结构性：按性别与按项目代际
    sex = conservative_by_sex(records)
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

    out = {
        "meta": {"topic": "S5 medal inflation", "caliber": "conservative_event",
                 "includes_1906": False, "data_version": "v1.0-fallback"},
        "years": years,
        "totals": totals, "delegations": deleg, "rows": rows, "players": players,
        "per_1000_rows": per_1000, "per_delegation": per_deleg,
        "medal_nocs": medal_nocs, "top5_share": top5_share, "top10_share": top10_share,
        "sex": {f"{y}|{s}": c for (y, s), c in sex.items()},
        "vintage": {str(y): dict(vintage[y]) for y in years},
    }
    (DATA_DIR / "inflation_data.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    fig_unit(years, totals, per_1000, per_deleg)
    fig_structure(years, sex, vintage, bands)
    fig_dilution(years, medal_nocs, top5_share, top10_share)
    _summarize(years, totals, deleg, rows, per_1000, per_deleg, medal_nocs,
               top5_share, top10_share, sex, vintage)
    print("OK ->", T3_DIR)


def fig_unit(years, totals, per_1000, per_deleg):
    """S5-1 总量涨、单位量跌：奖牌膨胀的另一面。"""
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.9))
    ax = axes[0]
    ax.bar(years, [totals[y] for y in years], color=PRINT["gold"], alpha=0.85, width=3.2)
    ax.set_ylabel("奖牌总数（保守小项口径）")
    ax.set_xlabel("届次（年份）")
    ax.text(0.0, 1.04, "A", transform=ax.transAxes, fontsize=11, fontweight="bold")
    finalize(fig, ax, "奖牌总量百年涨 8.6 倍", badge("保守小项"), source())

    ax2 = axes[1]
    base_p = per_1000[years[0]]
    base_d = per_deleg[years[0]]
    ax2.plot(years, [per_1000[y] / base_p * 100 for y in years],
             color=PRINT["flame"], lw=2, marker="o", ms=3, label="每千条参赛记录奖牌")
    ax2.plot(years, [per_deleg[y] / base_d * 100 for y in years],
             color=PRINT["slate"], lw=2, marker="s", ms=3, label="每代表团奖牌")
    ax2.axhline(100, color=PRINT["muted"], lw=0.8, ls="--")
    ax2.set_ylabel("指数（1896=100）")
    ax2.set_xlabel("届次（年份）")
    ax2.legend(fontsize=8.5, frameon=False)
    ax2.annotate("每千条参赛记录\n缩水至 1896 年的 22%", (2016, 28), fontsize=8,
                 color=PRINT["flame"])
    ax2.text(0.0, 1.04, "B", transform=ax2.transAxes, fontsize=11, fontweight="bold")
    finalize(fig, ax2, "单位参赛的奖牌反而在缩水", badge("保守小项"), source())
    fig.savefig(EXPORTS / "Fig3-8_inflation-unit_4x.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig_structure(years, sex, vintage, bands):
    """S5-2 增长的结构性来源：按性别与按项目代际。"""
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.9))
    ax = axes[0]
    cats = [("men", "男子", PRINT["slate"]), ("women", "女子", PRINT["flame"]),
            ("mixed", "混合", PRINT["mint"])]
    bottoms = np.zeros(len(years))
    for key, lab, color in cats:
        vals = np.array([sex.get((y, key), 0) for y in years], dtype=float)
        ax.bar(years, vals, bottom=bottoms, color=color, width=3.2, label=lab, alpha=0.88)
        bottoms += vals
    ax.set_ylabel("奖牌数（保守小项口径）")
    ax.set_xlabel("届次（年份）")
    ax.legend(fontsize=8.5, frameon=False, loc="upper left")
    ax.text(0.0, 1.04, "A", transform=ax.transAxes, fontsize=11, fontweight="bold")
    finalize(fig, ax, "奖牌池的性别结构：女子从 0 到近半数", badge("保守小项"), source())

    ax2 = axes[1]
    names = [b[0] for b in bands]
    palette = [PRINT["slate"], PRINT["mint"], PRINT["gold"], PRINT["flame"], PRINT["violet"]]
    bottoms2 = np.zeros(len(years))
    for name, color in zip(names, palette):
        vals = np.array([vintage[y].get(name, 0) for y in years], dtype=float)
        ax2.bar(years, vals, bottom=bottoms2, color=color, width=3.2, label=name, alpha=0.86)
        bottoms2 += vals
    ax2.set_xlabel("届次（年份）")
    ax2.legend(fontsize=7.8, frameon=False, loc="upper left", ncol=2)
    ax2.text(0.0, 1.04, "B", transform=ax2.transAxes, fontsize=11, fontweight="bold")
    finalize(fig, ax2, "奖牌池的代际构成：新增项目层层堆叠",
              badge("保守小项 · 按项目首次出现的年代分组"), source())
    fig.savefig(EXPORTS / "Fig3-9_inflation-structure_4x.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig_dilution(years, medal_nocs, top5_share, top10_share):
    """S5-3 更多国家分蛋糕：获奖 NOC 数上升、头部份额下降。"""
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    ax.plot(years, [medal_nocs[y] for y in years], color=PRINT["mint"], lw=2,
            marker="o", ms=3, label="获奖 NOC 数（左轴）")
    ax.set_ylabel("获奖国家/地区数")
    ax2 = ax.twinx()
    ax2.plot(years, [top5_share[y] * 100 for y in years], color=PRINT["flame"],
             lw=1.6, ls="--", label="Top5 奖牌份额（右轴）")
    ax2.plot(years, [top10_share[y] * 100 for y in years], color=PRINT["slate"],
             lw=1.6, ls=":", label="Top10 奖牌份额（右轴）")
    ax2.set_ylabel("头部份额（%）")
    ax2.grid(False)
    lines = [ax.get_lines()[0], ax2.get_lines()[0], ax2.get_lines()[1]]
    ax.legend(lines, [l.get_label() for l in lines], fontsize=8.5, frameon=False,
              loc="center right")
    ax.set_xlabel("届次（年份）")
    finalize(fig, ax, "膨胀的受益者是更多国家，而不是少数强国",
              badge("保守小项"), source())
    fig.savefig(EXPORTS / "Fig3-10_inflation-dilution_4x.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _summarize(years, totals, deleg, rows, per_1000, per_deleg, medal_nocs,
               top5_share, top10_share, sex, vintage):
    print("totals 1896->2024:", totals[1896], "->", totals[2024],
          "= %.2fx" % (totals[2024] / totals[1896]))
    print("deleg 1896->2024:", deleg[1896], "->", deleg[2024],
          "= %.2fx" % (deleg[2024] / deleg[1896]))
    print("rows 1896->2024:", rows[1896], "->", rows[2024],
          "= %.2fx" % (rows[2024] / rows[1896]))
    print("per1000 1896->2024:", round(per_1000[1896], 1), "->", round(per_1000[2024], 1))
    print("per_deleg 1896->2024:", round(per_deleg[1896], 2), "->", round(per_deleg[2024], 2))
    print("medal_nocs 1896->2024:", medal_nocs[1896], "->", medal_nocs[2024])
    print("top5 share 1896->2024: %.3f -> %.3f" % (top5_share[1896], top5_share[2024]))
    print("top10 share 1896->2024: %.3f -> %.3f" % (top10_share[1896], top10_share[2024]))
    w = sex.get((2024, "women"), 0); m = sex.get((2024, "men"), 0); x = sex.get((2024, "mixed"), 0)
    print("2024 sex split women/men/mixed:", w, m, x, "women share %.3f" % (w / (w + m + x)))


if __name__ == "__main__":
    main()
