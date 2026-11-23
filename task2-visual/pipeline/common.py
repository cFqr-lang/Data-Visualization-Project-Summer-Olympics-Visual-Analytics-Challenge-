"""公共常量与原始数据加载（仅标准库）。

对外接口（供任务一/三/四接入时保持稳定）：
- `load_records()` -> list[Record]
- `Record` 字段：year, noc, sex, sport_key, event, generic, medal, player_id
"""

from __future__ import annotations

import csv
import hashlib
from collections import namedtuple
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = REPO_ROOT / "data" / "raw" / "olympics_dataset.csv"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
OUT_DATA_DIR = REPO_ROOT / "task2-visual" / "site" / "public" / "data"
OUT_FIG_DIR = OUT_DATA_DIR / "figures"
SHARED_METRICS_DIR = REPO_ROOT / "shared" / "metrics"

DATA_VERSION = "v1.0-fallback"
EXCLUDED_YEAR = 1906
MEDAL_ORDER = ("Gold", "Silver", "Bronze")

# Event 为泛化值的白名单（2020+ 无法还原到具体小项）
GENERIC_EVENTS = frozenset(
    {"men", "women", "men team", "women team", "mixed team", "open team",
     "relay only athlete", "team"}
)

# Sport 标签归并：2020 起数据由「大类」切换为「细分项目」，为画通 128 年生命线
# 统一回大类；键一律小写匹配。归并只影响展示分组，不改变小项去重。
SPORT_ALIASES = {
    "artistic gymnastics": "Gymnastics",
    "cycling": "Cycling",
    "cycling road": "Cycling",
    "cycling track": "Cycling",
    "cycling bmx racing": "Cycling",
    "cycling bmx freestyle": "Cycling",
    "cycling mountain bike": "Cycling",
    "cycling road, cycling track": "Cycling",
    "cycling road, cycling mountain bike": "Cycling",
    "cycling road, triathlon": "Cycling",
    "canoe slalom": "Canoeing",
    "canoe sprint": "Canoeing",
    "equestrianism": "Equestrian",
    "marathon swimming": "Swimming",
    "marathon swimming, swimming": "Swimming",
    "trampolining": "Trampoline Gymnastics",
    "synchronized swimming": "Artistic Swimming",
    "baseball": "Baseball/Softball",
    "softball": "Baseball/Softball",
    "3x3 basketball, basketball": "3x3 Basketball",
}


Record = namedtuple(
    "Record", "year noc sex sport_key event generic medal player_id"
)


def _squash(text: str) -> str:
    return " ".join((text or "").strip().split())


def sport_key(raw_sport: str) -> str:
    name = _squash(raw_sport)
    return SPORT_ALIASES.get(name.lower(), name)


def event_key(raw_event: str) -> str:
    return _squash(raw_event).lower()


def is_generic_event(raw_event: str) -> bool:
    return event_key(raw_event) in GENERIC_EVENTS


def raw_fingerprint() -> dict:
    """原始文件指纹，写入每份 JSON 的 meta，便于对账。"""
    digest = hashlib.sha256()
    size = 0
    with RAW_CSV.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
            size += len(chunk)
    return {"file": str(RAW_CSV.relative_to(REPO_ROOT)).replace("\\", "/"),
            "bytes": size, "sha256": digest.hexdigest()[:16]}


def load_records(include_1906: bool = False) -> list[Record]:
    """读取原始 CSV。

    任务一的 `data/processed/athletes_normalized.csv` 若存在则优先消费其
    `event_key` 列；当前未就绪，回退为自算键，并在 meta 中标记
    `event_key_source = task2_fallback`。
    """
    if not RAW_CSV.exists():
        raise SystemExit(f"原始数据缺失：{RAW_CSV}")

    records: list[Record] = []
    with RAW_CSV.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            year = int(row["Year"])
            if not include_1906 and year == EXCLUDED_YEAR:
                continue
            records.append(
                Record(
                    year=year,
                    noc=row["NOC"].strip(),
                    sex=row["Sex"].strip(),
                    sport_key=sport_key(row["Sport"]),
                    event=event_key(row["Event"]),
                    generic=is_generic_event(row["Event"]),
                    medal=row["Medal"].strip(),
                    player_id=row["player_id"].strip(),
                )
            )
    return records


def event_key_source() -> str:
    return "task1_normalized" if (PROCESSED_DIR / "athletes_normalized.csv").exists() else "task2_fallback"
