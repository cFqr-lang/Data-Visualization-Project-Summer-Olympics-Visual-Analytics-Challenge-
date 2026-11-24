# -*- coding: utf-8 -*-
"""生成说明书用图（4–5 张），输出到 docs/figures/"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "task1-data" / "output"
FIG = ROOT / "task1-data" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200

NAVY, TEAL, AMBER, GRAY = "#1F3A5F", "#2E8B8B", "#D97706", "#9AA5B1"


def style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    ax.tick_params(colors="#444444", labelsize=9)
    ax.grid(axis="y", color="#E8EDF2", linewidth=0.8)
    ax.set_axisbelow(True)


clean = pd.read_csv(OUT / "olympics_clean.csv", low_memory=False)
rows = pd.read_csv(OUT / "medals_athlete_row.csv", low_memory=False)
ev = pd.read_csv(OUT / "medals_event_level.csv", low_memory=False)

# ---------------- 图 1：2024 双口径金牌 Top10
d24 = rows[(rows["Year"] == 2024) & (rows["Medal"] == "Gold")]
e24 = ev[(ev["Year"] == 2024) & (ev["Medal"] == "Gold")]
top = d24["NOC"].value_counts().head(10).index.tolist()
a = [int(((d24["NOC"] == n)).sum()) for n in top]
b = [int((e24["noc"] == n).sum()) for n in top]
order = np.argsort(a)
top = [top[i] for i in order]
a = [a[i] for i in order]
b = [b[i] for i in order]

fig, ax = plt.subplots(figsize=(7.6, 4.4))
y = np.arange(len(top))
h = 0.38
ax.barh(y + h / 2, a, height=h, color=NAVY, label="运动员行口径（每人每牌计 1）")
ax.barh(y - h / 2, b, height=h, color=TEAL, label="小项口径（每小项每色计 1）")
for i, (va, vb) in enumerate(zip(a, b)):
    ax.text(va + 1.5, i + h / 2, str(va), va="center", fontsize=8, color=NAVY)
    ax.text(vb + 1.5, i - h / 2, str(vb), va="center", fontsize=8, color=TEAL)
ax.set_yticks(y, top)
ax.set_xlabel("2024 巴黎奥运会金牌数", fontsize=9.5)
ax.set_title("同一个国家，两套金牌数：2024 年双口径对比", fontsize=12.5, color=NAVY, pad=12, loc="left")
ax.legend(frameon=False, fontsize=8.5, loc="lower right")
style(ax)
ax.text(0.99, 1.02, "官方锚点：美国 40、中国 40、荷兰 15（中国、荷兰已复原；美国 39，差 1）",
        transform=ax.transAxes, ha="right", fontsize=8, color="#666666")
fig.tight_layout()
fig.savefig(FIG / "fig1_caliber_2024.png", bbox_inches="tight")
plt.close(fig)

# ---------------- 图 2：双口径膨胀率随届次
cal = pd.read_csv(OUT / "caliber_by_year.csv")
fig, ax = plt.subplots(figsize=(8.2, 4.0))
ax.plot(cal["Year"], cal["膨胀率%"], color=NAVY, linewidth=2, marker="o", markersize=3)
ax.fill_between(cal["Year"], cal["膨胀率%"], color=NAVY, alpha=0.08)
for yv, off in [(1900, (0, 12)), (1920, (0, -20)), (2020, (-42, 12)), (2024, (14, -18))]:
    r = cal.loc[cal["Year"] == yv, "膨胀率%"].iloc[0]
    ax.annotate(f"{yv}：{r:.1f}%", (yv, r), textcoords="offset points", xytext=off,
                ha="center", fontsize=8, color=AMBER)
ax.set_ylim(0, 220)
ax.set_ylabel("膨胀率（%）", fontsize=9.5)
ax.set_xlabel("届次", fontsize=9.5)
ax.set_title("运动员行口径的“通货膨胀”：越晚近，虚高越严重", fontsize=12.5, color=NAVY, pad=12, loc="left")
style(ax)
fig.tight_layout()
fig.savefig(FIG / "fig2_inflation.png", bbox_inches="tight")
plt.close(fig)

# ---------------- 图 3：哪些项目最容易虚高
r = rows[rows["is_1906"] == 0].groupby("sport_norm").size().rename("row_medals")
e = ev[ev["is_1906"] == 0].groupby("sport_norm").size().rename("event_medals")
ratio = pd.concat([r, e], axis=1).dropna()
ratio = ratio[ratio["event_medals"] >= 100]
ratio["ratio"] = ratio["row_medals"] / ratio["event_medals"]
ratio = ratio.sort_values("ratio", ascending=False).head(10).sort_values("ratio")

fig, ax = plt.subplots(figsize=(7.6, 4.4))
bars = ax.barh(ratio.index, ratio["ratio"], color=TEAL, height=0.62)
for bar, (nm, row) in zip(bars, ratio.iterrows()):
    ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
            f"{row['ratio']:.1f}×", va="center", fontsize=8, color="#333333")
ax.set_xlabel("运动员行奖牌数 ÷ 小项口径奖牌数（剔除 1906）", fontsize=9)
ax.set_title("哪些项目最容易让奖牌“行数”虚高", fontsize=12.5, color=NAVY, pad=12, loc="left")
ax.axvline(1, color=GRAY, linewidth=1, linestyle="--")
style(ax)
fig.tight_layout()
fig.savefig(FIG / "fig3_sport_ratio.png", bbox_inches="tight")
plt.close(fig)

# ---------------- 图 4：Sport 口径漂移
years = [2016, 2020, 2024]
raw_n = [clean.loc[clean["Year"] == y, "sport_raw"].nunique() for y in years]
norm_n = [clean.loc[clean["Year"] == y, "sport_norm"].nunique() for y in years]
x = np.arange(len(years))
w = 0.34
fig, ax = plt.subplots(figsize=(6.6, 3.8))
b1 = ax.bar(x - w / 2, raw_n, width=w, color=GRAY, label="原始 Sport 取值数")
b2 = ax.bar(x + w / 2, norm_n, width=w, color=NAVY, label="归一后大类数")
for b in list(b1) + list(b2):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.6, str(int(b.get_height())),
            ha="center", fontsize=8.5, color="#333333")
ax.set_xticks(x, [str(y) for y in years])
ax.set_ylim(0, max(raw_n) + 8)
ax.set_ylabel("取值个数", fontsize=9.5)
ax.set_title("Sport 口径漂移：原始取值 34→50，归一后 34–40 类", fontsize=11.5, color=NAVY, pad=10, loc="left")
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
style(ax)
fig.tight_layout()
fig.savefig(FIG / "fig4_sport_drift.png", bbox_inches="tight")
plt.close(fig)

# ---------------- 图 5：Event 泛化占比
gen = []
for y in [2016, 2020, 2024]:
    d = clean[clean["Year"] == y]
    gen.append((d["event_granularity"] == "coarse").mean() * 100)
fig, ax = plt.subplots(figsize=(6.0, 3.6))
bars = ax.bar(["2016", "2020", "2024"], gen, color=[GRAY, AMBER, AMBER], width=0.5)
for b, v in zip(bars, gen):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.5, f"{v:.1f}%", ha="center", fontsize=9, color="#333333")
ax.set_ylim(0, 28)
ax.set_ylabel("泛化 Event 行占比（%）", fontsize=9)
ax.set_title("Event 泛化不是历史常态，而是最近两届的断层", fontsize=11.5, color=NAVY, pad=10, loc="left")
style(ax)
fig.tight_layout()
fig.savefig(FIG / "fig5_generic_event.png", bbox_inches="tight")
plt.close(fig)

print("figures saved:", sorted(p.name for p in FIG.glob("*.png")))
