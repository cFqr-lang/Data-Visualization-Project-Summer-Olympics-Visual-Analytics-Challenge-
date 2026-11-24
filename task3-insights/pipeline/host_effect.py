"""任务三 · S1 东道主效应（数据管线，不含渲染）。

复用任务二口径（`task2-visual/pipeline/metrics.py`），输出 ECharts 可用的
`data/host_effect_data.json` 与 `data/host_effect_summary.csv`。
渲染由 `task3-insights/site/render.mjs`（Apache ECharts）完成。
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import types
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np

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

CALIBER_LABEL = _metrics.CALIBER_LABEL

# 现代夏季奥运会东道主（1948 以后）
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
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    records = _common.load_records(include_1906=False)
    agg_cons = _metrics.aggregate_medals(records, "conservative_event")
    agg_row = _metrics.aggregate_medals(records, "athlete_row")

    part: dict = defaultdict(int)
    for rec in records:
        part[(rec.year, rec.noc)] += 1

    idx_map = {y: i for i, y in enumerate(YEARS)}

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

        # 持续性序列（T-2..T+2 的保守奖牌与指数）
        series, index = {}, {}
        for off in (-2, -1, 0, 1, 2):
            t = YEARS[idx + off] if 0 <= idx + off < len(YEARS) else None
            v = _total(agg_cons, (t, noc)) if t is not None else np.nan
            series[str(off)] = v if np.isfinite(v) else None
        base4 = np.nanmean([v for k, v in enumerate(list(series.values()))
                            if k in (0, 1, 3, 4) and v is not None])
        if np.isfinite(base4) and base4:
            for off in (-2, -1, 0, 1, 2):
                v = series[str(off)]
                index[str(off)] = round(v / base4 * 100, 2) if v is not None else None

        rows.append({
            "year": year, "noc": noc, "city": city, "note": note,
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
            "series": series,
            "index": index,
        })

    # 零分布 + 直方图
    host_keys = {(y, n) for y, n, _, _ in HOSTS}
    null_ups = []
    for noc in {rec.noc for rec in records}:
        series_noc = {t: _total(agg_cons, (t, noc)) for t in YEARS}
        for t in YEARS:
            if (t, noc) in host_keys:
                continue
            idx = idx_map[t]
            vals = [series_noc[x] for x in _window(YEARS, idx, span=2) if x in series_noc]
            if len(vals) >= 2:
                null_ups.append(series_noc[t] - np.mean(vals))
    null_ups = np.asarray(null_ups, dtype=float)

    pct = {
        r["year"]: float((null_ups < r["uplift_cons"]).mean()) if r["uplift_cons"] is not None else None
        for r in rows
    }
    for r in rows:
        r["uplift_percentile"] = round(pct[r["year"]], 3) if pct[r["year"]] is not None else None

    lo, hi = -10.0, 38.0
    edges = np.linspace(lo, hi, 48)
    counts, _ = np.histogram(null_ups, bins=edges)
    centers = ((edges[:-1] + edges[1:]) / 2).round(2).tolist()

    persistence_median = {}
    for off in (-2, -1, 0, 1, 2):
        vals = [r["index"][str(off)] for r in rows if r["index"].get(str(off)) is not None]
        persistence_median[str(off)] = round(float(np.median(vals)), 1) if vals else None

    _write_csv(rows)
    _write_json(rows, null_ups, counts.tolist(), centers, persistence_median)
    _summarize(rows, null_ups, persistence_median)
    print("OK ->", T3_DIR)


def _write_csv(rows: list[dict]) -> None:
    cols = ["year", "noc", "city", "note", "base_cons", "host_cons", "prev_cons",
            "next_cons", "uplift_cons", "lift_ratio_cons", "uplift_percentile",
            "base_row", "host_row", "uplift_row", "base_part", "host_part",
            "part_ratio", "conv_ratio"]
    with (DATA_DIR / "host_effect_summary.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r[c] for c in cols})


def _write_json(rows, null_ups, counts, centers, persistence_median) -> None:
    payload = {
        "meta": {
            "chartSet": "Fig3-1..3-4", "topic": "S1 host advantage effect",
            "caliber": "conservative_event",
            "caliber_label": CALIBER_LABEL["conservative_event"],
            "includes_1906": False, "data_version": "v1.0",
            "event_key_source": _common.event_key_source(),
            "source": _common.raw_fingerprint(),
            "generated_at": date.today().isoformat(),
        },
        "hosts": rows,
        "persistence_median": persistence_median,
        "null": {
            "n": int(len(null_ups)), "mean": float(null_ups.mean()),
            "sd": float(null_ups.std()), "median": float(np.median(null_ups)),
            "p99": float(np.percentile(null_ups, 99)),
        },
        "null_hist": {"edges": [-10.0, 38.0], "centers": centers, "counts": counts},
    }
    (DATA_DIR / "host_effect_data.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _summarize(rows, null_ups, persistence_median) -> None:
    ups = np.array([r["uplift_cons"] for r in rows if r["uplift_cons"] is not None])
    part_ratios = np.array([r["part_ratio"] for r in rows
                            if r["part_ratio"] is not None and r["base_cons"] and r["base_cons"] >= 5])
    conv_ratios = np.array([r["conv_ratio"] for r in rows
                            if r["conv_ratio"] is not None and r["base_cons"] and r["base_cons"] >= 5])
    print("uplift mean/median = %.2f / %.2f; positive %d/20"
          % (ups.mean(), np.median(ups), int((ups > 0).sum())))
    print("null mean/sd = %.2f / %.2f (n=%d)" % (null_ups.mean(), null_ups.std(), len(null_ups)))
    print("persistence median index T-2..T+2 =", persistence_median)
    print("median part_ratio = %.3f; median conv_ratio = %.3f"
          % (np.median(part_ratios), np.median(conv_ratios)))


if __name__ == "__main__":
    main()
