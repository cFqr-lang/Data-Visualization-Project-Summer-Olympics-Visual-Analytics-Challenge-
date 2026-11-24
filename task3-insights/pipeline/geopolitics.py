"""任务三 · S3 地缘政治的投影（数据管线，不含渲染）。

输出 `data/geopolitics_data.json`；渲染由 `task3-insights/site/render.mjs` 完成。
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


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    records = _common.load_records(include_1906=False)
    agg = _metrics.aggregate_medals(records, "conservative_event")
    agg_row = _metrics.aggregate_medals(records, "athlete_row")

    deleg = defaultdict(set)
    for r in records:
        deleg[r.year].add(r.noc)
    years = sorted(deleg)

    def series(noc):
        return {y: _total(agg, (y, noc)) for y in years if (y, noc) in agg}

    gdr_rows = sum(_total(agg_row, (y, "GDR")) for y in years)
    frg_rows = sum(_total(agg_row, (y, "FRG")) for y in years)
    gdr_cons = sum(series("GDR").values())
    frg_cons = sum(series("FRG").values())

    out = {
        "meta": {
            "chartSet": "Fig3-5..3-7", "topic": "S3 geopolitics",
            "caliber": "conservative_event",
            "caliber_label": _metrics.CALIBER_LABEL["conservative_event"],
            "includes_1906": False, "data_version": "v1.0",
            "source": _common.raw_fingerprint(),
            "generated_at": date.today().isoformat(),
        },
        "years": years,
        "delegations": {y: len(deleg[y]) for y in years},
        "usa": series("USA"),
        "urs_lineage": {
            "URS": series("URS"), "EUN": series("EUN"), "RUS": series("RUS"),
            "ROC": series("ROC"), "AIN": series("AIN"),
        },
        "germany": {"GER": series("GER"), "FRG": series("FRG"), "GDR": series("GDR")},
        "gdr_stats": {"gdr_rows": gdr_rows, "gdr_cons": gdr_cons,
                      "frg_rows": frg_rows, "frg_cons": frg_cons},
    }
    (DATA_DIR / "geopolitics_data.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("deleg 1976/1980/1984/1988 =", len(deleg[1976]), len(deleg[1980]),
          len(deleg[1984]), len(deleg[1988]))
    print("URS peak 1980 =", series("URS").get(1980), "; URS 1988 =", series("URS").get(1988))
    print("EUN 1992 =", series("EUN").get(1992), "; RUS 1996 =", series("RUS").get(1996),
          "; ROC 2020 =", series("ROC").get(2020), "; AIN 2024 =", series("AIN").get(2024))
    print("GDR cons/rows =", gdr_cons, gdr_rows, "; FRG cons/rows =", frg_cons, frg_rows)
    print("OK ->", T3_DIR)


if __name__ == "__main__":
    main()
