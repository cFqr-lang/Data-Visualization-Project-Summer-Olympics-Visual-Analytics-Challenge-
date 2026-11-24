"""任务三共享绘图样式（对齐任务二印刷浅色主题）。"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
    "violet": "#7B5EA7",
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


def badge(text: str) -> str:
    return f"{text} · 不含 1906"


def source() -> str:
    return "数据 v1.0 · 保守小项口径 · 不含 1906 · 2026-11-24 生成"


def finalize(fig, ax, title, subtitle, src, xlabel=None):
    ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=12)
    if subtitle:
        ax.text(0, 1.03, subtitle, transform=ax.transAxes, fontsize=9, color=PRINT["muted"])
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9)
    fig.text(0.01, 0.005, src, fontsize=7.5, color=PRINT["muted"])
    fig.tight_layout(rect=(0, 0.02, 1, 1))
