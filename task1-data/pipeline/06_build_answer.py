# -*- coding: utf-8 -*-
"""把任务一压缩填写进答卷模板第 Ⅰ 节，输出 docs/数说奥运_答卷_任务一填写版.docx"""
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
TPL = ROOT / "task1-data" / "template" / "数说奥运_答卷模板.docx"
OUT = ROOT / "task1-data" / "submission" / "数说奥运_答卷_任务一填写版.docx"
OUT.parent.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "task1-data" / "figures"
OUTDIR = ROOT / "task1-data" / "output"

NAVY = RGBColor(0x1F, 0x3A, 0x5F)
GRAY = RGBColor(0x66, 0x66, 0x66)

doc = Document(TPL)

# 找到第 Ⅱ 节标题作为插入锚点
anchor = None
for p in doc.paragraphs:
    if p.text.strip().startswith("Ⅱ"):
        anchor = p
        break
if anchor is None:
    raise SystemExit("未找到第 Ⅱ 节标题")

# 删除答题区域与 Ⅱ 之间的空段落
started = False
for p in list(doc.paragraphs):
    if p.text.strip() == "（下面是答题区域）":
        started = True
        continue
    if started and p is anchor:
        break
    if started and p.text.strip() == "" and p._p.getprevious() is not None:
        p._p.getparent().remove(p._p)

sec = doc.sections[0]
usable = (sec.page_width - sec.left_margin - sec.right_margin) / 360000  # cm


def set_run(run, size=10.5, bold=False, color=None, font="宋体"):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)


def space_after(p, pt):
    p.paragraph_format.space_after = Pt(pt)


def heading(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    set_run(p.add_run(text), 11, bold=True, color=NAVY, font="微软雅黑")
    anchor._p.addprevious(p._p)


def para(text, size=10.5, indent=True, after=3):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.74)
    space_after(p, after)
    set_run(p.add_run(text), size)
    anchor._p.addprevious(p._p)


def bullet(text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.74)
    space_after(p, 2)
    set_run(p.add_run("· " + text), 10.5)
    anchor._p.addprevious(p._p)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def table(df, widths, font=8.5, cap=None):
    if cap:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(2)
        set_run(p.add_run(cap), 8.5, bold=True, color=GRAY)
        anchor._p.addprevious(p._p)
    t = doc.add_table(rows=1, cols=len(df.columns))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    t._tbl.tblPr.append(layout)
    hdr = t.rows[0].cells
    for i, c in enumerate(df.columns):
        hdr[i].text = ""
        pp = hdr[i].paragraphs[0]
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        space_after(pp, 0)
        set_run(pp.add_run(str(c)), font, bold=True)
        shade(hdr[i], "E4ECF6")
    for _, row in df.iterrows():
        cells = t.add_row().cells
        for i, c in enumerate(df.columns):
            cells[i].text = ""
            pp = cells[i].paragraphs[0]
            pp.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == len(df.columns) - 1 else WD_ALIGN_PARAGRAPH.CENTER
            space_after(pp, 0)
            set_run(pp.add_run("" if pd.isna(row[c]) else str(row[c])), font)
    scale = usable / sum(widths)
    for r in t.rows:
        for i, w in enumerate(widths):
            r.cells[i].width = Cm(w * scale)
    anchor._p.addprevious(t._tbl)


def figure(fname, cap, width_ratio=0.94):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(str(FIG / fname), width=Cm(usable * width_ratio))
    anchor._p.addprevious(p._p)
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    space_after(c, 6)
    set_run(c.add_run(cap), 8.5, bold=True, color=GRAY)
    anchor._p.addprevious(c._p)


# ---------------------------------------------------------------- 正文
heading("1  奖牌统计口径：双口径并行")

para(
    "数据粒度为“一名运动员 × 一届 × 一个小项”，团体项目一枚奖牌对应多行，因此必须先定义口径。本队并行使用两套："
    "① 运动员行口径——每条 Gold/Silver/Bronze 记录计 1 枚，团体项目每位成员各计 1 枚，共 38,818 枚（金 13,002 / 银 12,746 / 铜 13,070；剔除 1906 为 38,360）；"
    "② 小项口径——以“届次 × 原始项目 × 小项名”为键，同色只计 1 枚，共 17,452 枚；其中 NOC-aware 版本（键再加 NOC，双铜牌与并列各计 1）共 18,159 枚，剔除 1906 为 17,935 枚，推荐作为历史总榜。"
)
para(
    "2024 年两套口径的差距见表 1：美国 131 个金牌行对应 39 枚，荷兰 67 行对应 15 枚；小项口径下中国 40、荷兰 15 与官方完全一致，美国 39 与官方的差 1 可由源数据缺行解释（见第 6 节）。"
    "因此历史总奖牌榜、逐届奖牌榜一律用小项口径的 NOC-aware 表；参赛人数、获奖人数、团体项目贡献用运动员行口径。所有图表标题均注明所用口径与是否含 1906。"
)

t1 = pd.DataFrame({
    "NOC": ["USA", "CHN", "NED", "FRA", "GBR", "AUS", "JPN"],
    "运动员行金牌": [131, 71, 67, 53, 39, 33, 27],
    "小项口径金牌": [39, 40, 15, 16, 13, 18, 20],
    "官方金牌（锚点）": [40, 40, 15, "—", "—", "—", "—"],
})
table(t1, [3.2, 3.6, 3.6, 3.6], cap="表 1  2024 年双口径金牌对比（官方仅取赛题给定锚点）")
figure("fig1_caliber_2024.png", "图 1  2024 年双口径金牌对比")

heading("2  体育大类归一：76 个原始取值 → 57 个大类")

para(
    "2020 年起数据源切换导致 Sport 拆细与更名，直接按 Sport 统计会出现“项目在 2020 年消失”的假象。本队建立 76 行映射表（output/sport_mapping.csv），规则四类："
    "拆分合并（Artistic Gymnastics→Gymnastics，Cycling Road/Track/MTB/BMX→Cycling，Canoe Sprint/Slalom→Canoeing）；"
    "更名统一（Synchronized/Artistic Swimming→Artistic Swimming，Equestrian→Equestrianism，Trampolining→Trampoline Gymnastics）；"
    "同类合并（Baseball/Softball→棒垒球，3x3 Basketball→Basketball）；逗号拆分（89 行，全部 2024、全部无奖牌，用 sport_all 保存完整项目串）。"
)
para("归一后为 57 个大类，20 个原始取值被改写；2020/2024 的原始取值分别为 46/50 个，归一后为 40/39 个（新增项目如滑板、冲浪、霹雳舞属真实新增，不应合并）。")

t2 = pd.DataFrame({
    "原始 Sport": ["Artistic Gymnastics", "Cycling Road / Track / MTB / BMX", "Canoe Sprint / Slalom", "Synchronized Swimming", "Equestrian", "Trampolining", "Baseball / Softball", "3x3 Basketball"],
    "归一后": ["Gymnastics", "Cycling", "Canoeing", "Artistic Swimming", "Equestrianism", "Trampoline Gymnastics", "Baseball/Softball", "Basketball"],
})
table(t2, [6.2, 4.6], cap="表 2  Sport 归一规则示例（完整 76 行见映射表）")
figure("fig4_sport_drift.png", "图 2  Sport 口径漂移与归一效果", width_ratio=0.82)

heading("3  Event 泛化：6,488 行，按粒度分层处理")

para(
    "2020/2024 有 6,488 行（2.6%）的 Event 是 Men / Women / Men Team / Relay Only Athlete 等泛化值，其中 2020 年占该届 20.1%、2024 年占 23.1%，含奖牌行 1,473 行。"
    "本队不改写原文，新增 event_granularity（fine/coarse）与 event_key：fine 用“届次|原始项目|Event”；coarse 追加 Sex（Mixed 事件除外，避免拆散混合团体）。"
    "跨 2020 的连续分析一律在归一 Sport 层进行；需要小项层时只用 fine 子集，或明确标注粒度降级为“项目×性别”。"
)
figure("fig5_generic_event.png", "图 3  Event 泛化行占比（2016 为 0，2020/2024 跃升至 20% 以上）", width_ratio=0.72)

heading("4  特殊记录处理规则")

t3 = pd.DataFrame({
    "对象": ["1906 届间奥运会", "1956 双城", "URS / EUN / ROC", "GDR / FRG / SAA", "TCH / YUG / SCG", "AIN / EOR / IOA"],
    "数据量": ["1,733 行 / 458 奖牌", "298 行马术", "4,622 / 650 / 561 行", "2,104 / 2,558 / 93 行", "3,369 / 2,046 / 300 行", "46 / 79 / 93 行"],
    "处理规则": ["主口径剔除，is_1906 标记；纳入敏感性 +458 奖牌（+1.18%）", "并入 1956 墨尔本，is_1956_stockholm 标注分场", "默认保留原 NOC；noc_modern 提供并入 RUS 的继承口径", "默认保留原 NOC；继承口径并入 GER", "默认不合并（继承国会低估其他共和国），仅提供可选字段", "保留独立，EOR 单列"],
})
table(t3, [4.0, 4.2, 8.0], cap="表 3  特殊记录处理规则（完整 234 行 NOC 映射见 output/noc_mapping.csv）")
para("政体合并只在“国家兴衰”分析中启用，并在图表标题声明；默认口径保留历史 NOC，避免把苏联 2,063 枚奖牌直接算到俄罗斯等争议。")

heading("5  可复现的数据质量检查（共 11 项，选列 8 项）")

t4 = pd.DataFrame({
    "检查项": ["结构与缺失", "字段取值域", "团体/并列重复", "奖牌守恒", "Sport 漂移", "Event 泛化", "姓名 / player_id", "NOC / Team"],
    "结果": ["252,565 × 11；缺失 0；Season 恒为 Summer", "Sex 仅 M/F；Medal 仅 4 值；Year 31 个", "5,188 组同小项同色多行，涉及 26,554 行（68.4%；剔除 1906 为 5,140 组 / 26,267 行）", "金 13,002 / 银 12,746 / 铜 13,070；34 个小项仅 1 种奖牌", "76 → 57 类；2020 后 24 个新写法；89 行逗号拼接", "6,488 行（2.6%）；2020 20.1%、2024 23.1%", "235,903 个 ID（1.071 行/ID）；52,544 个姓名多 ID；14,059 行含括号；姓名 0 行非 ASCII", "234 NOC / 1,193 Team；2,795 行带 -数字 分队"],
    "处理决定": ["不插补，保留常量列", "保留原值，不推断", "双口径并行，差异显式化", "不补齐缺失银/铜", "按映射表统一，输出映射表", "标记 fine/coarse，事件键分级", "不建个体 ID，回避个体排名；另提供近似实体表", "国家一律用 NOC，Team 仅展示"],
})
table(t4, [3.4, 8.2, 4.8], font=8, cap="表 4  数据质量检查选摘（完整 11 项见 output/quality_checks.csv）")
para("全部检查由代码复现：task1-data/pipeline/01_audit.py、01b_extra.py、02_clean.py 取数，task1-data/pipeline/04_validate.py 做 21 项断言（含行数、奖牌数、映射覆盖、Q3 重复组、NOC-aware 小项口径、2024 小项数），当前 21/21 通过。", after=2)

heading("6  关键结论：2024 年的 4 处记录缺失")

para(
    "2024 年小项口径得到 328 个有奖牌记录的小项（官方 329），其中 325 个有金牌记录。差异不是统计错误，而是源数据缺行："
    "女子公路赛缺金牌行（Kristen Faulkner 被记为 No medal）、男子山地越野缺金牌行、男子 800 米自由泳缺金牌与铜牌行、铁人三项混合接力整项只有 2 条 No medal。"
    "据此美国 39/40、德国 11/12 可逐项解释，中国 40/40、荷兰 15/15 完全一致（表 5）。任务二、三凡涉及 2024 的图表均需引用该缺口清单（output/known_gaps.csv）。"
)

t5 = pd.DataFrame({
    "指标": ["有奖牌记录小项", "有金牌记录小项", "美国金牌", "中国金牌", "荷兰金牌", "德国金牌"],
    "本数据": [328, 325, 39, 40, 15, 11],
    "官方": [329, 329, 40, 40, 15, 12],
    "归因": ["铁人三项混合接力整项无奖牌行", "另有 3 个小项缺金牌行", "女子公路赛金牌行缺失", "一致", "一致", "混合接力金牌行缺失"],
})
table(t5, [3.6, 2.2, 2.0, 8.0], cap="表 5  2024 年小项口径与官方的逐项归因")

doc.save(OUT)
print("saved:", OUT)
