"""任务三 · S1 东道主效应（Host Advantage Effect）专题深挖。

复用任务二口径（`task2-visual/pipeline/metrics.py`）：
  - 主口径：conservative_event（保守小项，同一届、同一 NOC、同一小项、同一奖牌颜色只计 1 次，2020+ 泛化小项取下界）
  - 对照口径：athlete_row（运动员行，团体项目按人计行）
  - 1906 届次默认排除

输出（全部写到 `task3-insights/`）：
  - data/host_effect_summary.csv   逐东道主的效应测算底表
  - data/host_effect_data.json     ECharts 可复用的聚合数据
  - exports/Fig3-1 ... Fig3-4.png  报告用静态图（浅色印刷主题）
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
T3_DIR = REPO_ROOT / "task3-insights"
EXPORTS = T3_DIR / "exports"
DATA_DIR = T3_DIR / "data"

# ---------------------------------------------------------------- 口径复用


PIPELINE = REPO_ROOT / "task2-visual" / "pipeline"
_pkg = types.ModuleType("t2pipeline")
_pkg.__path__ = [str(PIPELINE)]
sys.modules["t2pipeline"] = _pkg


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "t2pipeline"
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_common = _load_module("t2pipeline.common", PIPELINE / "common.py")
_metrics = _load_module("t2pipeline.metrics", PIPELINE / "metrics.py")

CALIBER_LABEL = _metrics.CALIBER_LABEL


# ---------------------------------------------------------------- 视觉系统（对齐任务二印刷浅色主题）

PRINT = {
    "bg": "#FBFAF6",
    "panel": "#FFFFFF",
    "grid": "#D9D4C7",
    "text": "#12211C",
    "muted": "#5F6F68",
    "flame": "#C24E2A",
    "gold": "#B8891F",
    "silver": "#7D878A",
    "bronze": "#A05F38",
    "mint": "#2E7D68",
    "slate": "#4A6A82",
}

plt.rcParams.update(
    {
        "font.family": "Microsoft YaHei",
        "axes.unicode_minus": False,
        "figure.facecolor": PRINT["bg"],
        "axes.facecolor": PRINT["bg"],
        "axes.edgecolor": PRINT["grid"],
        "axes.labelcolor": PRINT["text"],
        "text.color": PRINT["text"],
        "xtick.color": PRINT["muted"],
        "ytick.color": PRINT["muted"],
        "grid.color": PRINT["grid"],
        "grid.linewidth": 0.8,
        "grid.alpha": 0.7,
        "axes.grid": True,
        "axes.axisbelow": True,
        "savefig.facecolor": PRINT["bg"],
    }
)


def _badge(caliber: str) -> str:
    return f"{CALIBER_LABEL[caliber]} · 不含 1906"


def _source() -> str:
    return "数据 v1.0 · 保守小项口径 · 不含 1906 · 2026-11-24 生成"


# ---------------------------------------------------------------- 东道主与基准

# 现代夏季奥运会东道主（1948 以后；1956 墨尔本为 AUS，斯德哥尔摩马术分场见备注）
HOSTS = [
    (1948, "GBR", "London", ""),
    (1952, "FIN", "Helsinki", ""),
    (1956, "AUS", "Melbourne", "马术分场在斯德哥尔摩"),
    (1960, "ITA", "Rome", ""),
    (1964, "JPN", "Tokyo", ""),
    (1968, "MEX", "Mexico City", ""),
    (1972, "FRG", "Munich", "西德主办"),
    (1976, "CAN", "Montreal", ""),
    (1980, "URS", "Moscow", "美国等抵制，缺席致竞争减弱"),
    (1984, "USA", "Los Angeles", "苏联/东德等抵制，缺席致竞争减弱"),
    (1988, "KOR", "Seoul", ""),
    (1992, "ESP", "Barcelona", ""),
    (1996, "USA", "Atlanta", ""),
    (2000, "AUS", "Sydney", ""),
    (2004, "GRE", "Athens", ""),
    (2008, "CHN", "Beijing", ""),
    (2012, "GBR", "London", ""),
    (2016, "BRA", "Rio de Janeiro", "主场奖牌不升反降的反例"),
    (2020, "JPN", "Tokyo", "因疫情于 2021 年举办，年份记为 2020"),
    (2024, "FRA", "Paris", "无 T+1，基准取 T-1/T-2"),
]

YEARS = [1896, 1900, 1904, 1908, 1912, 1920, 1924, 1928, 1932, 1936,
         1948, 1952, 1956, 1960, 1964, 1968, 1972, 1976, 1980, 1984,
         1988, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]


def _window(years: list[int], idx: int, span: int = 2) -> list[int]:
    """T 前后各 span 届（不含 T），供基准估计；返回存在数据的年份列表。"""
    out = []
    for d in range(1, span + 1):
        if idx - d >= 0:
            out.append(years[idx - d])
    for d in range(1, span + 1):
        if idx + d < len(years):
            out.append(years[idx + d])
    return out


def _total(agg: dict, key) -> int:
    d = agg.get(key, {})
    return int(d.get("gold", 0) + d.get("silver", 0) + d.get("bronze", 0))


def main() -> None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    records = _common.load_records(include_1906=False)
    agg_cons = _metrics.aggregate_medals(records, "conservative_event")
    agg_row = _metrics.aggregate_medals(records, "athlete_row")

    # 参与规模（参赛记录行数，口径：athlete_row）
    part: dict = defaultdict(int)
    for rec in records:
        part[(rec.year, rec.noc)] += 1

    idx_map = {y: i for i, y in enumerate(YEARS)}

    # ---- 东道主效应测算 ----
    rows = []
    for year, noc, city, note in HOSTS:
        idx = idx_map[year]
        w = _window(YEARS, idx, span=2)
        base_cons = np.mean([_total(agg_cons, (t, noc)) for t in w]) if w else np.nan
        base_row = np.mean([_total(agg_row, (t, noc)) for t in w]) if w else np.nan
        base_part = np.mean([part[(t, noc)] for t in w]) if w else np.nan

        host_cons = _total(agg_cons, (year, noc))
        host_row = _total(agg_row, (year, noc))
        host_part = part[(year, noc)]

        prev_cons = _total(agg_cons, (YEARS[idx - 1], noc)) if idx - 1 >= 0 else np.nan
        next_cons = _total(agg_cons, (YEARS[idx + 1], noc)) if idx + 1 < len(YEARS) else np.nan

        conv_host = host_cons / host_part if host_part else np.nan
        conv_base = base_cons / base_part if base_part else np.nan

        rows.append(
            {
                "year": year,
                "noc": noc,
                "city": city,
                "note": note,
                "base_cons": round(base_cons, 2) if np.isfinite(base_cons) else None,
                "host_cons": host_cons,
                "prev_cons": int(prev_cons) if np.isfinite(prev_cons) else None,
                "next_cons": int(next_cons) if np.isfinite(next_cons) else None,
                "uplift_cons": round(host_cons - base_cons, 2) if np.isfinite(base_cons) else None,
                "lift_ratio_cons": round(host_cons / base_cons, 3) if base_cons else None,
                "base_row": round(base_row, 2) if np.isfinite(base_row) else None,
                "host_row": host_row,
                "uplift_row": round(host_row - base_row, 2) if np.isfinite(base_row) else None,
                "base_part": round(base_part, 2) if np.isfinite(base_part) else None,
                "host_part": host_part,
                "part_ratio": round(host_part / base_part, 3) if base_part else None,
                "conv_ratio": round(conv_host / conv_base, 3) if conv_base else None,
            }
        )

    # ---- 全样本逐年“对称波动”作为零分布（剔除东道主届） ----
    host_keys = {(y, n) for y, n, _, _ in HOSTS}
    null_ups = []
    for noc in {rec.noc for rec in records}:
        series = {t: _total(agg_cons, (t, noc)) for t in YEARS}
        for t in YEARS:
            if (t, noc) in host_keys:
                continue
            idx = idx_map[t]
            w = _window(YEARS, idx, span=2)
            vals = [series[x] for x in w if x in series]
            if len(vals) >= 2:
                null_ups.append(series[t] - np.mean(vals))
    null_ups = np.asarray(null_ups, dtype=float)

    host_ups = np.asarray([r["uplift_cons"] for r in rows if r["uplift_cons"] is not None])
    pct = {
        r["year"]: float((null_ups < r["uplift_cons"]).mean()) if r["uplift_cons"] is not None else None
        for r in rows
    }
    for r in rows:
        r["uplift_percentile"] = round(pct[r["year"]], 3) if pct[r["year"]] is not None else None

    # ---- 写底表与 JSON ----
    _write_csv(rows)
    _write_json(rows, null_ups)

    # ---- 四幅报告图 ----
    fig1(rows)
    fig2(rows, agg_cons, idx_map)
    fig3(rows)
    fig4(rows, null_ups)
    _summarize(rows, agg_cons, idx_map, null_ups)
    print("OK ->", T3_DIR)


def _summarize(rows: list[dict], agg_cons: dict, idx_map: dict, null_ups: np.ndarray) -> None:
    """打印关键结论数字，便于报告引用与人工复核。"""
    ups = np.array([r["uplift_cons"] for r in rows if r["uplift_cons"] is not None])
    pos = int((ups > 0).sum())
    # 持久性：T-2..T+2 的奖牌指数（相对 ±2 基准）中位数
    offsets = [-2, -1, 0, 1, 2]
    cols = {off: [] for off in offsets}
    for r in rows:
        idx = idx_map[r["year"]]
        vals = []
        for off in offsets:
            t = YEARS[idx + off] if 0 <= idx + off < len(YEARS) else None
            vals.append(_total(agg_cons, (t, r["noc"])) if t is not None else np.nan)
        base = np.nanmean([v for k, v in enumerate(vals) if k in (0, 1, 3, 4) and np.isfinite(v)])
        if not np.isfinite(base) or base == 0:
            continue
        for off, v in zip(offsets, vals):
            if np.isfinite(v):
                cols[off].append(v / base * 100)
    pers = {off: round(float(np.median(cols[off])), 1) for off in offsets}
    part_ratios = np.array([r["part_ratio"] for r in rows if r["part_ratio"] is not None and r["base_cons"] and r["base_cons"] >= 5])
    conv_ratios = np.array([r["conv_ratio"] for r in rows if r["conv_ratio"] is not None and r["base_cons"] and r["base_cons"] >= 5])
    print("uplift mean/median = %.2f / %.2f; positive %d/20" % (ups.mean(), np.median(ups), pos))
    print("null mean/sd = %.2f / %.2f (n=%d)" % (null_ups.mean(), null_ups.std(), len(null_ups)))
    print("persistence median index T-2..T+2 =", pers)
    print("median part_ratio = %.3f; median conv_ratio = %.3f" % (np.median(part_ratios), np.median(conv_ratios)))


def _write_csv(rows: list[dict]) -> None:
    import csv

    cols = [
        "year", "noc", "city", "note", "base_cons", "host_cons", "prev_cons",
        "next_cons", "uplift_cons", "lift_ratio_cons", "uplift_percentile",
        "base_row", "host_row", "uplift_row", "base_part", "host_part",
        "part_ratio", "conv_ratio",
    ]
    with (DATA_DIR / "host_effect_summary.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r[c] for c in cols})


def _write_json(rows: list[dict], null_ups: np.ndarray) -> None:
    payload = {
        "meta": {
            "chartSet": "Fig3-1..3-4",
            "topic": "S1 host advantage effect",
            "caliber": "conservative_event",
            "caliber_label": CALIBER_LABEL["conservative_event"],
            "includes_1906": False,
            "data_version": "v1.0-fallback",
            "event_key_source": _common.event_key_source(),
            "source": _common.raw_fingerprint(),
            "generated_at": "2026-11-24",
        },
        "hosts": rows,
        "null": {
            "n": int(len(null_ups)),
            "mean": float(null_ups.mean()),
            "sd": float(null_ups.std()),
            "median": float(np.median(null_ups)),
        },
    }
    (DATA_DIR / "host_effect_data.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------- 图

def _finalize(fig, ax, title, subtitle, source):
    ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=12)
    if subtitle:
        ax.text(0, 1.035, subtitle, transform=ax.transAxes, fontsize=9, color=PRINT["muted"])
    fig.text(0.01, 0.005, source, fontsize=7.5, color=PRINT["muted"])
    fig.tight_layout(rect=(0, 0.02, 1, 1))


def fig1(rows: list[dict]) -> None:
    """Fig3-1 主场脉冲：T 相对前后届基准的奖牌增量（双口径并置）。"""
    ordered = sorted(
        [r for r in rows if r["uplift_cons"] is not None],
        key=lambda r: r["uplift_cons"],
    )
    labels = [f"{r['noc']} {r['year']}" for r in ordered]
    y = np.arange(len(ordered))

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 8.2), sharey=True)
    fig.subplots_adjust(wspace=0.06)

    for ax, key, title in (
        (axes[0], "uplift_cons", "奖牌增量（保守小项口径）"),
        (axes[1], "uplift_row", "奖牌增量（运动员行口径）"),
    ):
        vals = np.array([r[key] for r in ordered], dtype=float)
        colors = [PRINT["flame"] if v >= 0 else PRINT["slate"] for v in vals]
        ax.barh(y, vals, color=colors, alpha=0.82, height=0.62)
        ax.axvline(0, color=PRINT["text"], lw=0.8)
        lo = min(0.0, float(vals.min()))
        hi = max(0.0, float(vals.max()))
        span = hi - lo if hi > lo else 1.0
        ax.set_xlim(lo - 0.08 * span, hi + 0.20 * span)
        for yi, v in zip(y, vals):
            ax.text(v + (0.01 * span if v >= 0 else -0.01 * span), yi,
                    f"{v:+.1f}", va="center", fontsize=7.2,
                    ha="left" if v >= 0 else "right", color=PRINT["text"])
        ax.set_title(title, fontsize=11, fontweight="bold", loc="left")
        ax.set_xlabel("较前后各两届均值多出的奖牌数", fontsize=9)
        ax.grid(axis="x", lw=0.6)
        ax.set_ylim(-0.6, len(ordered) - 0.4)

    axes[0].set_yticks(y)
    axes[0].set_yticklabels(labels, fontsize=8.5)
    axes[1].tick_params(labelleft=False)

    # 抵制届与反例标记（紧贴条形，避免箭头干扰）
    pos = {(r["noc"], r["year"]): i for i, r in enumerate(ordered)}
    vals0 = [r["uplift_cons"] for r in ordered]
    for key, tag in ((("URS", 1980), "抵制届"), (("USA", 1984), "抵制届"), (("BRA", 2016), "反例")):
        if key not in pos:
            continue
        v = vals0[pos[key]]
        axes[0].text(v + (0.8 if v >= 0 else -0.8), pos[key],
                     tag, va="center", ha="left" if v >= 0 else "right",
                     fontsize=7.2, color=PRINT["muted"])
    _finalize(fig, axes[0], "东道主效应是一场脉冲：主办那一届的奖牌数显著高于前后基准",
              _badge("conservative_event"), _source())
    fig.savefig(EXPORTS / "Fig3-1_host-pulse_4x.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig2(rows: list[dict], agg_cons: dict, idx_map: dict) -> None:
    """Fig3-2 加成能持续吗：以东道主届为 100 的奖牌指数，T-2..T+2 回落轨迹。"""
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    offsets = [-2, -1, 0, 1, 2]
    series_all = []
    for r in rows:
        idx = idx_map[r["year"]]
        vals = []
        for off in offsets:
            t = YEARS[idx + off] if 0 <= idx + off < len(YEARS) else None
            vals.append(_total(agg_cons, (t, r["noc"])) if t is not None else np.nan)
        base = np.nanmean([v for k, v in enumerate(vals) if k in (0, 1, 3, 4) and np.isfinite(v)])
        if not np.isfinite(base) or base == 0:
            continue
        idx_series = np.array(vals) / base * 100
        series_all.append(idx_series)
        ax.plot(offsets, idx_series, color=PRINT["grid"], lw=1.1, alpha=0.85, zorder=1)

    arr = np.array(series_all)
    med = np.nanmedian(arr, axis=0)
    ax.plot(offsets, med, color=PRINT["flame"], lw=3, marker="o", zorder=5,
            label="东道主中位数")

    # 重点国家
    highlight = {"CHN": PRINT["gold"], "GBR": PRINT["mint"], "JPN": PRINT["slate"],
                 "KOR": PRINT["bronze"], "BRA": PRINT["muted"], "FRA": "#7B5EA7"}
    for r in rows:
        if r["noc"] not in highlight:
            continue
        idx = idx_map[r["year"]]
        vals = []
        for off in offsets:
            t = YEARS[idx + off] if 0 <= idx + off < len(YEARS) else None
            vals.append(_total(agg_cons, (t, r["noc"])) if t is not None else np.nan)
        base = np.nanmean([v for k, v in enumerate(vals) if k in (0, 1, 3, 4) and np.isfinite(v)])
        if not np.isfinite(base) or base == 0:
            continue
        s = np.array(vals) / base * 100
        ax.plot(offsets, s, color=highlight[r["noc"]], lw=1.8, marker="s",
                markersize=4, label=f"{r['noc']} {r['year']}", zorder=4)

    ax.axhline(100, color=PRINT["muted"], lw=0.8, ls="--")
    ax.axvline(0, color=PRINT["gold"], lw=1.0, ls=":")
    ax.set_xticks(offsets)
    ax.set_xticklabels(["T-2", "T-1", "主办届 T", "T+1", "T+2"])
    ax.set_ylabel("奖牌指数（前后各两届均值为 100）")
    ax.legend(fontsize=8, frameon=False, loc="upper right", ncol=2)
    _finalize(fig, ax, "主场加成是脉冲而非台阶：T+1 即快速回落，到 T+2 基本回到基线",
              _badge("conservative_event") + " · 灰线为全部现代东道主", _source())
    fig.savefig(EXPORTS / "Fig3-2_persistence_4x.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig3(rows: list[dict]) -> None:
    """Fig3-3 加成来自哪里：参赛扩容（x）与夺牌效率（y）的分解。"""
    # 剔除基线过小（<5 枚）的东道主，避免比值不稳定；MEX 1968 基准仅 1.25 枚
    valid = [r for r in rows if r["base_cons"] and r["base_cons"] >= 5
             and r["part_ratio"] is not None and r["conv_ratio"] is not None
             and r["part_ratio"] and r["conv_ratio"]]
    x = np.array([r["part_ratio"] for r in valid])
    y = np.array([r["conv_ratio"] for r in valid])

    fig, ax = plt.subplots(figsize=(8.6, 6.6))
    ax.scatter(x, y, s=46, color=PRINT["slate"], alpha=0.8, zorder=3)
    ax.axhline(1, color=PRINT["muted"], lw=0.8, ls="--")
    ax.axvline(1, color=PRINT["muted"], lw=0.8, ls="--")

    labels = {"CHN", "GBR", "JPN", "KOR", "AUS", "ESP", "BRA", "URS", "USA", "FRA"}
    for r in valid:
        if r["noc"] in labels:
            ax.annotate(f"{r['noc']} {r['year']}", (r["part_ratio"], r["conv_ratio"]),
                        textcoords="offset points", xytext=(6, 5), fontsize=8,
                        color=PRINT["text"])

    ax.set_xlabel("参赛规模比（主办届 ÷ 前后基准）")
    ax.set_ylabel("夺牌效率比（每千条参赛记录的奖牌数，主办届 ÷ 前后基准）")
    ax.set_xlim(0.82, max(x) * 1.10)
    ax.set_ylim(0.62, max(y) * 1.10)
    ax.text(0.99, 0.98, "扩容 + 提效", transform=ax.transAxes, ha="right", va="top",
            fontsize=8.5, color=PRINT["muted"])
    ax.text(0.99, 0.03, "扩容 + 降效", transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8.5, color=PRINT["muted"])
    ax.text(0.01, 0.98, "收缩 + 提效", transform=ax.transAxes, ha="left", va="top",
            fontsize=8.5, color=PRINT["muted"])
    _finalize(fig, ax, "主场加成的最大来源是“多派人参赛”，而不是“单位投入夺牌更多”",
              "X>1 表示参赛规模扩张；Y>1 表示每千条参赛记录奖牌数上升 · 剔除基线 <5 枚的 MEX 1968", _source())
    fig.savefig(EXPORTS / "Fig3-3_decomposition_4x.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig4(rows: list[dict], null_ups: np.ndarray) -> None:
    """Fig3-4 主场加成有多大：东道主增量在全部国家逐年波动的分布中的位置。"""
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    lo, hi = -10.0, 38.0  # 截断显示主区间，极端尾值在脚注说明
    bins = np.linspace(lo, hi, 48)
    ax.hist(null_ups, bins=bins, color=PRINT["grid"], edgecolor=PRINT["muted"],
            lw=0.3, zorder=1)
    ax.axvline(0, color=PRINT["muted"], lw=0.8, ls="--")
    ax.set_xlim(lo, hi)
    ax.set_xlabel("较前后各两届均值的奖牌增量（保守小项口径）")
    ax.set_ylabel("国家 × 届次数")

    ups = np.array([r["uplift_cons"] for r in rows if r["uplift_cons"] is not None])
    for v in ups:
        if lo <= v <= hi:
            ax.axvline(v, color=PRINT["flame"], lw=0.9, alpha=0.55, zorder=3)

    # 关键东道主标注（错峰高度，避免重叠）
    top = ax.get_ylim()[1]
    key = [("CHN", 2008), ("FRA", 2024), ("FRG", 1972), ("AUS", 1956),
           ("BRA", 2016), ("CAN", 1976)]
    fracs = [1.0, 0.82, 0.64, 0.46, 0.28, 0.12]
    by_key = {(r["noc"], r["year"]): r for r in rows}
    for (noc, yr), fr in zip(key, fracs):
        r = by_key.get((noc, yr))
        if not r or r["uplift_cons"] is None or not (lo <= r["uplift_cons"] <= hi):
            continue
        ax.annotate(f"{noc} {yr}", (r["uplift_cons"], top * fr), xytext=(0, 6),
                    textcoords="offset points", ha="center", fontsize=7.5,
                    color=PRINT["text"], zorder=6)

    # 超出显示区间的抵制届，以右缘数值标出
    for noc, yr, fr in (("URS", 1980, 0.92), ("USA", 1984, 0.72)):
        r = by_key.get((noc, yr))
        if r and r["uplift_cons"] > hi:
            ax.annotate(f"{noc} {yr} +{r['uplift_cons']:.0f} →", (hi, top * fr),
                        xytext=(-4, 6), textcoords="offset points", ha="right",
                        fontsize=7.5, color=PRINT["flame"])

    sd = ups.mean() / null_ups.std()
    ax.text(0.03, 0.97, f"东道主平均增量 +{ups.mean():.1f} 枚\n≈ {sd:.1f} 个标准差（vs 非东道国波动）",
            transform=ax.transAxes, ha="left", va="top", fontsize=9,
            color=PRINT["text"], bbox=dict(boxstyle="round,pad=0.4", fc=PRINT["panel"],
            ec=PRINT["grid"], lw=0.8))
    _finalize(fig, ax, "主场加成的分布位置：显著高于一般国家，但不是“必然中奖”",
              "灰色为全部非东道国（届次 × 国家）的对称波动分布；红色竖线为现代东道主增量 · 横轴截断于 [-10, 38]，极端值（最大 184.5）未显示", _source())
    fig.savefig(EXPORTS / "Fig3-4_effect-size_4x.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
