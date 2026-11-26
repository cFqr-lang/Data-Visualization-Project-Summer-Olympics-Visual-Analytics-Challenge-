"""为 Fig.4-1 ~ Fig.4-11 各生成一个内联 plotly.js 的独立 HTML，供 export_figures.js 导出 PNG/SVG。

用法（在仓库根目录执行）：
    python task4-bonus/tools/export_figures.py
    node   task4-bonus/tools/export_figures.js

依赖：pandas / numpy / plotly（见 task4-bonus/requirements.txt）。
CSV 查找规则与 build_dashboard.py 相同：仓库 data/raw/ 或脚本同目录。
"""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK_DIR = HERE.parent
OUT = HERE / "_figs"

FIGS = [
    ("Fig4-1_A1_dual-caliber", "fig_a", 1200, 420),
    ("Fig4-2_A2_top20", "fig_a2", 1200, 600),
    ("Fig4-3_A3_inflation", "fig_a3", 1200, 420),
    ("Fig4-4_B1_twelve-nations", "fig_b", 1200, 500),
    ("Fig4-5_B2_bloc-evolution", "fig_b2", 1200, 400),
    ("Fig4-6_C1_female-ratio", "fig_c", 1200, 450),
    ("Fig4-7_C2_female-top15", "fig_c2", 1200, 500),
    ("Fig4-8_D1_event-growth", "fig_d", 1200, 400),
    ("Fig4-9_D2_vanished-added", "fig_d2", 1200, 500),
    ("Fig4-10_E1_host-pulse", "fig_e", 1400, 500),
    ("Fig4-11_E2_small-nocs", "fig_e2", 1200, 550),
]


def main():
    sys.argv = ["build_dashboard.py"]
    ns = runpy.run_path(str(TASK_DIR / "build_dashboard.py"))

    OUT.mkdir(exist_ok=True)
    for name, var, _w, _h in FIGS:
        fig = ns[var]
        html = fig.to_html(include_plotlyjs="inline", full_html=True,
                           config={"displayModeBar": False})
        (OUT / f"{name}.html").write_text(html, encoding="utf-8")
        print(f"  {name}.html")
    print(f"完成：{len(FIGS)} 个 HTML -> {OUT}")
    print("下一步：node task4-bonus/tools/export_figures.js")


if __name__ == "__main__":
    main()
