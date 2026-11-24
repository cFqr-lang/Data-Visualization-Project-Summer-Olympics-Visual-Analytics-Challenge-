"""任务三 · S3 地缘政治的投影：抵制潮、苏联谱系、两德分立。

复用任务二口径（保守小项主口径，运动员行为对照；1906 排除）。
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


def main() -> None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    records = _common.load_records(include_1906=False)
    agg = _metrics.aggregate_medals(records, "conservative_event")
    agg_row = _metrics.aggregate_medals(records, "athlete_row")

    # 每届代表团数与参赛行数
    deleg = defaultdict(set)
    for r in records:
        deleg[r.year].add(r.noc)
    years = sorted(deleg)

    # 政体系列（保守小项）
    def series(noc):
        return {y: _total(agg, (y, noc)) for y in years if (y, noc) in agg}

    out = {
        "years": years,
        "delegations": {y: len(deleg[y]) for y in years},
        "usa": series("USA"),
        "urs_lineage": {
            "URS": series("URS"),
            "EUN": series("EUN"),
            "RUS": series("RUS"),
            "ROC": series("ROC"),
            "AIN": series("AIN"),
        },
        "germany": {
            "GER": series("GER"),
            "FRG": series("FRG"),
            "GDR": series("GDR"),
        },
    }
    # GDR / FRG 行口径总数
    gdr_rows = sum(_total(agg_row, (y, "GDR")) for y in years)
    frg_rows = sum(_total(agg_row, (y, "FRG")) for y in years)
    gdr_cons = sum(series("GDR").values())
    frg_cons = sum(series("FRG").values())
    out["gdr_stats"] = {"gdr_rows": gdr_rows, "gdr_cons": gdr_cons,
                        "frg_rows": frg_rows, "frg_cons": frg_cons}

    (DATA_DIR / "geopolitics_data.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    fig_boycott(years, deleg, series)
    fig_lineage(years, out["urs_lineage"])
    fig_germany(years, out["germany"], gdr_cons, gdr_rows)
    _summarize(years, deleg, series, gdr_cons, gdr_rows, frg_cons, frg_rows)
    print("OK ->", T3_DIR)


def fig_boycott(years, deleg, series):
    """S3-1 抵制潮：代表团数的两次塌陷 + 美苏两强的缺席缺口。"""
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5.0))
    ax = axes[0]
    dl = [len(deleg[y]) for y in years]
    ax.plot(years, dl, color=PRINT["slate"], lw=1.8, marker="o", ms=3.5)
    ax.fill_between(years, dl, color=PRINT["slate"], alpha=0.08)
    for y, note in [(1976, "非洲抵制\n92 团"), (1980, "美阵营抵制\n80 团"),
                    (1984, "苏阵营缺席\n140 团")]:
        ax.annotate(note, (y, len(deleg[y])), xytext=(0, -34),
                    textcoords="offset points", ha="center", fontsize=8,
                    color=PRINT["text"])
    ax.set_ylabel("代表团数")
    ax.set_xlabel("届次（年份）")
    ax.text(0.0, 1.04, "A", transform=ax.transAxes, fontsize=11, fontweight="bold")
    finalize(fig, ax, "抵制潮在数据里的塌陷", badge("代表团数"), source())

    ax2 = axes[1]
    for noc, color, lab in [("USA", PRINT["slate"], "美国"), ("URS", PRINT["flame"], "苏联")]:
        ys = sorted(series(noc))
        vals = [series(noc)[y] for y in ys]
        ax2.plot(ys, vals, color=color, lw=1.8, marker="o", ms=3.5, label=lab)
        # 缺席届标 0 与缺口
        if noc == "USA" and 1980 not in series(noc):
            ax2.plot([1980], [0], color=color, marker="x", ms=8, mew=1.8)
            ax2.annotate("美国缺席 1980", (1980, 0), xytext=(8, 18),
                         textcoords="offset points", fontsize=8, color=color)
        if noc == "URS" and 1984 not in series(noc):
            ax2.plot([1984], [0], color=color, marker="x", ms=8, mew=1.8)
            ax2.annotate("苏联缺席 1984", (1984, 0), xytext=(8, 18),
                         textcoords="offset points", fontsize=8, color=color)
    ax2.set_ylabel("奖牌数（保守小项口径）")
    ax2.set_xlabel("届次（年份）")
    ax2.set_xlim(1948, 1992)
    ax2.legend(fontsize=8, frameon=False)
    ax2.text(0.0, 1.04, "B", transform=ax2.transAxes, fontsize=11, fontweight="bold")
    finalize(fig, ax2, "冷战把领奖台切成两个阵营", badge("保守小项"), source())
    fig.savefig(EXPORTS / "Fig3-5_geopolitics-boycott_4x.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig_lineage(years, lineage):
    """S3-2 苏联谱系 URS→EUN→RUS→ROC→AIN 的一脉兴衰。"""
    fig, ax = plt.subplots(figsize=(10.2, 5.2))
    colors = {"URS": PRINT["flame"], "EUN": PRINT["gold"], "RUS": PRINT["slate"],
              "ROC": PRINT["mint"], "AIN": PRINT["violet"]}
    labels = {"URS": "苏联 URS", "EUN": "独联体 EUN", "RUS": "俄罗斯 RUS",
              "ROC": "ROC 2020", "AIN": "中立个人 AIN"}
    for entity in ["URS", "EUN", "RUS", "ROC", "AIN"]:
        ys = sorted(y for y in lineage[entity] if not (entity == "RUS" and y < 1992))
        vals = [lineage[entity][y] for y in ys]
        ax.bar([str(y) for y in ys], vals, color=colors[entity], alpha=0.88,
               width=0.72, label=labels[entity])
    ax.set_ylabel("奖牌数（保守小项口径）")
    ax.set_xlabel("届次")
    ax.legend(fontsize=8.5, frameon=False, ncol=2)
    ax.annotate("1980 莫斯科：抵制削弱竞争，见顶 195 枚",
                xy=("1980", 195), xytext=("1980", 202), ha="center", fontsize=8,
                color=PRINT["text"])
    ax.annotate("2024 巴黎：仅 5 枚，不及 1980 巅峰的 3%", xy=("2024", 5),
                xytext=("2016", 55), fontsize=8, color=PRINT["violet"],
                arrowprops=dict(arrowstyle="->", color=PRINT["violet"], lw=0.8))
    finalize(fig, ax, "一脉苏联：从 195 枚到 5 枚的政治兴衰",
              badge("保守小项 · 政体按 NOC 原样，谱系仅注释连接"), source())
    fig.savefig(EXPORTS / "Fig3-6_ussr-lineage_4x.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig_germany(years, germany, gdr_cons, gdr_rows):
    """S3-3 两德分立、互抵制的缺席与统一。"""
    fig, ax = plt.subplots(figsize=(10.2, 5.2))
    ger = germany["GER"]
    pre = sorted(y for y in ger if y <= 1964)
    post = sorted(y for y in ger if y >= 1992)
    ax.plot(pre, [ger[y] for y in pre], color=PRINT["slate"], lw=1.6,
            marker="o", ms=3, label="德国 GER（统一）")
    ax.plot(post, [ger[y] for y in post], color=PRINT["slate"], lw=1.6, marker="o", ms=3)
    for noc, color, lab in [("FRG", PRINT["mint"], "西德 FRG"), ("GDR", PRINT["flame"], "东德 GDR")]:
        ys = sorted(germany[noc])
        vals = [germany[noc][y] for y in ys]
        ax.plot(ys, vals, color=color, lw=1.8, marker="s", ms=4, label=lab)
    # 抵制缺口
    ax.plot([1980], [0], color=PRINT["mint"], marker="x", ms=9, mew=1.8)
    ax.annotate("FRG 缺席 1980", (1980, 0), xytext=(4, 20), textcoords="offset points",
                fontsize=8, color=PRINT["mint"])
    ax.plot([1984], [0], color=PRINT["flame"], marker="x", ms=9, mew=1.8)
    ax.annotate("GDR 缺席 1984", (1984, 0), xytext=(4, 20), textcoords="offset points",
                fontsize=8, color=PRINT["flame"])
    ax.set_ylabel("奖牌数（保守小项口径）")
    ax.set_xlabel("届次（年份）")
    ax.set_xlim(1950, 2026)
    ax.legend(fontsize=8.5, frameon=False)
    ax.text(0.03, 0.95, f"东德效率奇迹：仅 5 届\n保守小项 {gdr_cons} 枚 / 运动员行 {gdr_rows} 行",
            transform=ax.transAxes, ha="left", va="top", fontsize=8.5,
            color=PRINT["text"], bbox=dict(boxstyle="round,pad=0.4", fc=PRINT["panel"],
            ec=PRINT["grid"], lw=0.8))
    finalize(fig, ax, "两德：分立、互相抵制缺席、再统一",
              badge("保守小项 · 1956–1964 统一队记为 GER"), source())
    fig.savefig(EXPORTS / "Fig3-7_germany-split_4x.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _summarize(years, deleg, series, gdr_cons, gdr_rows, frg_cons, frg_rows):
    print("deleg 1976/1980/1984/1988 =", len(deleg[1976]), len(deleg[1980]),
          len(deleg[1984]), len(deleg[1988]))
    print("URS peak 1980 =", series("URS").get(1980), "; URS 1988 =", series("URS").get(1988))
    print("EUN 1992 =", series("EUN").get(1992), "; RUS 1996 =", series("RUS").get(1996),
          "; ROC 2020 =", series("ROC").get(2020), "; AIN 2024 =", series("AIN").get(2024))
    print("GDR cons/rows =", gdr_cons, gdr_rows, "; FRG cons/rows =", frg_cons, frg_rows)


if __name__ == "__main__":
    main()
