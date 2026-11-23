# -*- coding: utf-8 -*-
"""生成《数据质量与口径说明书》Word 文档
数据来源：task1-data/output、contracts、shared/metrics 下的检查结果与映射表，保证文档数字与代码产物一致
"""
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "task1-data" / "output"
DOCS = ROOT / "task1-data" / "docs"
DOCS.mkdir(parents=True, exist_ok=True)
DOC_PATH = DOCS / "数据质量与口径说明书.docx"

DARK = RGBColor(0x1F, 0x3A, 0x5F)
GRAY = RGBColor(0x66, 0x66, 0x66)
FIG = ROOT / "task1-data" / "figures"

doc = Document()

# ---------------------------------------------------------------- 页面与样式
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.4)
sec.left_margin = sec.right_margin = Cm(2.2)

normal = doc.styles["Normal"]
normal.font.name = "宋体"
normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
normal.paragraph_format.line_spacing = 1.4
normal.paragraph_format.space_after = Pt(4)

for name, size in [("Heading 1", 15), ("Heading 2", 12.5), ("Heading 3", 11)]:
    st = doc.styles[name]
    st.font.name = "微软雅黑"
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = DARK
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    st.paragraph_format.space_before = Pt(12 if name == "Heading 1" else 8)
    st.paragraph_format.space_after = Pt(6)


def set_run(run, size=10.5, bold=False, color=None, font="宋体"):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)


def para(text="", size=10.5, bold=False, color=None, align=None, indent=True,
         space_after=4, font="宋体"):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.74)
    r = p.add_run(text)
    set_run(r, size, bold, color, font)
    return p


def bullet(text, size=10.5):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.74)
    p.paragraph_format.first_line_indent = Cm(-0.0)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("· " + text)
    set_run(r, size)
    return p


def caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    set_run(r, 9, bold=True, color=GRAY)


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def add_table(df, widths, font=8.5, header_font=8.5, cap=None, align_left_cols=()):
    if cap:
        caption(cap)
    t = doc.add_table(rows=1, cols=len(df.columns))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    t._tbl.tblPr.append(layout)
    hdr = t.rows[0].cells
    for i, col in enumerate(df.columns):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        set_run(p.add_run(str(col)), header_font, bold=True)
        shade(hdr[i], "E4ECF6")
    for _, row in df.iterrows():
        cells = t.add_row().cells
        for i, col in enumerate(df.columns):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i in align_left_cols else WD_ALIGN_PARAGRAPH.CENTER
            set_run(p.add_run("" if pd.isna(row[col]) else str(row[col])), font)
    for r in t.rows:
        for i, w in enumerate(widths):
            r.cells[i].width = Cm(w)
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_figure(fname, cap, width=15.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(FIG / fname), width=Cm(width))
    caption(cap)


def add_page_number():
    footer = doc.sections[0].footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    run._element.addnext(fld)


add_page_number()

# ---------------------------------------------------------------- 封面信息
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(24)
set_run(p.add_run("数据质量与口径说明书"), 24, bold=True, color=DARK, font="微软雅黑")

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(18)
set_run(p.add_run("「数说奥运 · 1896–2024」夏季奥运会可视分析挑战赛｜任务一"), 11, color=GRAY, font="微软雅黑")

info = pd.DataFrame({
    "项目": ["对应任务", "数据文件", "数据规模", "代码", "产物", "版本日期"],
    "说明": [
        "任务一（必做）：数据体检与口径定义",
        "olympics_dataset.csv（UTF-8，未修改原始文件）",
        "252,565 行 × 11 列，约 26 MB",
        "src/01_audit.py、src/01b_extra.py、src/02_clean.py",
        "task1-data/output 中间产物 + contracts 契约 + shared/metrics 共享指标",
        "2026-11-23",
    ],
})
add_table(info, [3.0, 13.4], font=9.5, header_font=9.5, align_left_cols=(1,))

# ---------------------------------------------------------------- 一、摘要
doc.add_heading("一、摘要", level=1)
para(
    "本说明书对 252,565 行、11 列的 1896–2024 年夏季奥运会数据完成体检与口径定义。"
    "数据无缺失值，但 68.4% 的奖牌行来自团体项目与并列造成的同小项多行：38,818 枚奖牌行在“小项口径”下压缩为 17,452 枚。"
    "Sport 的 76 个原始取值归一为 57 个大类；2020 年起 Event 泛化共 6,488 行（2020 年 20.1%、2024 年 23.1%）。"
    "除赛题列出的六类问题外，本次新发现 2024 年有 3 个小项缺少金牌记录（女子公路自行车、男子山地自行车越野、男子 800 米自由泳），"
    "据此可逐项解释美国 39/40、德国 11/12 与官方金牌数的差异，而荷兰 15/15、中国 40/40 完全一致。主口径采用“运动员行口径＋剔除 1906”，小项口径作为对照，全部检查与清洗均可由代码复现。"
)

# ---------------------------------------------------------------- 二、总体情况
doc.add_heading("二、数据总体情况", level=1)
doc.add_heading("2.1 规模与覆盖", level=2)

snap = pd.DataFrame({
    "指标": ["参赛记录", "字段", "届次", "主办城市", "NOC", "Team", "Sport", "Event", "奖牌行", "无奖牌行", "缺失值"],
    "数值": [
        "252,565 行", "11 列", "31 个年份（30 届官方 + 1906 届间）",
        "23 个（1956 年同时有墨尔本、斯德哥尔摩）", "234 个（157 个曾获奖，77 个从未获奖）",
        "1,193 个", "76 个原始取值 → 归一 57 个大类", "1,041 个",
        "38,818 行（金 13,002 / 银 12,746 / 铜 13,070）", "213,747 行（84.6%）", "0",
    ],
})
add_table(snap, [4.0, 12.4], cap="表 1  数据快照（核对口径：全部行，含 1906）", align_left_cols=(1,))

df = pd.read_csv(OUT / "olympics_clean.csv", low_memory=False)
sel_years = [1896, 1900, 1908, 1932, 1956, 1980, 1984, 2000, 2016, 2020, 2024]
rows = []
for y in sel_years:
    d = df[df["Year"] == y]
    rows.append({
        "届次": y,
        "行数": f"{len(d):,}",
        "NOC 数": d["NOC"].nunique(),
        "女性行占比": f"{(d['Sex'] == 'F').mean() * 100:.1f}%",
        "奖牌行": int(d["is_medal"].sum()),
        "归一 Sport 数": d["sport_norm"].nunique(),
    })
add_table(pd.DataFrame(rows), [2.0, 2.4, 2.0, 2.8, 2.4, 3.0],
          cap="表 2  代表性届次规模（选摘，完整 31 届见 task1-data/output/olympics_clean.csv）")

para(
    "表 2 显示两个结构性事实：其一，参赛规模从 1896 年 380 行扩张到 2024 年 14,892 行，NOC 从 12 个增至 206 个；"
    "其二，女性行占比从 0% 升至 49.1%。这两条曲线在任务二 C 视角中直接使用，此处仅用于确认数据的时间覆盖完整、无断代。"
)

# ---------------------------------------------------------------- 三、问题复核
doc.add_heading("三、数据质量问题复核", level=1)
doc.add_heading("3.1 赛题所列六类问题", level=2)

issues = pd.DataFrame({
    "编号": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"],
    "问题": ["奖牌两套口径", "体育大类名称漂移", "小项命名泛化", "姓名与 ID 不可靠", "历史特殊记录", "团体项目与并列奖牌"],
    "复核结果": [
        "38,818 奖牌行；5,176 组“同届×同小项×同色”多行，涉及 26,542 行（68.4%）；2024 美国 131 金行、荷兰 67 金行",
        "76 个原始取值；2020 起新增/改写 24 个；89 行逗号拼接（全部 2024、全部无奖牌）；归一后 57 类",
        "泛化行 6,488（2.6%），2020 年占 20.1%、2024 年占 23.1%；泛化奖牌行 1,473",
        "player_id 235,903 个（1.071 行/ID）；52,544 个姓名对应多个 ID；12,883 个 ID 对应多个姓名；14,059 行姓名含括号；同名最大跨度 120 年",
        "1906 年 1,733 行/458 奖牌（1.18%）；1956 斯德哥尔摩 298 行；EOR 79 行/1 奖牌；ROC 561 行/149 奖牌；AIN 46 行/6 奖牌",
        "重复组 5,176；34 个小项只颁发一种奖牌（1908 男子 400 米仅 1 金）；金/银/铜数量不等",
    ],
    "本说明书处理": [
        "同时输出运动员行口径与小项口径（第四章）",
        "按 4 类规则归一，输出映射表（第五章）",
        "fine / coarse 两级粒度 + 事件键（第六章）",
        "不构建个体 ID，回避个体排名（3.2-N2）",
        "逐项制定规则（第七章）",
        "不补齐；口径差异显式化（第四章）",
    ],
})
add_table(issues, [1.1, 3.1, 7.4, 4.8], font=8, cap="表 3  赛题 2.4 六类问题的复核结果")

doc.add_heading("3.2 本次新发现（赛题 2.4 未列）", level=2)
para("N1（最重要）· 2024 年奖牌记录不完整。", bold=True, space_after=2)
para(
    "对 2024 年每个小项检查奖牌色集合，发现有 3 个小项只有银/铜而无金牌行：女子公路自行车赛（仅银牌正确，金牌 Kristen Faulkner（USA）、"
    "铜牌 Lotte Kopecky（BEL）在数据中均为 No medal）、男子山地自行车越野（缺金牌，官方为英国选手）、男子 800 米自由泳（缺金牌与铜牌）。"
    "这不是口径问题，而是源数据缺行，直接导致美国 2024 金牌少于官方、相关国家金牌榜的细微偏差（见附录 A）。"
    "完整的 4 项缺口（含铁人三项混合接力整项缺失）已整理为 contracts/known_gaps.csv，任务二、三可直接引用。"
)
para("N2 · 姓名被系统性剥离变音符号。", bold=True, space_after=2)
para(
    "全部 252,565 行的 Name 均不含非 ASCII 字符（0 行），说明不是个别录入错误，而是源数据的编码处理：Nándor Kovács→Nndor Kovcs、"
    "József Nagy→Jzsef Nagy、Blaž Las-torres→Bla Las-torres。同时存在姓名顺序与介词残留（如 van Julie、le Kimberley），"
    "与赛题所述“截断、顺序颠倒、括号残留”一致。"
)
para("N3 · 逗号拼接的 89 行不污染奖牌榜。", bold=True, space_after=2)
para(
    "89 行 Sport 为逗号拼接（如 Cycling Road, Triathlon），全部集中在 2024 年，且全部为 No medal。它不影响任何奖牌统计，"
    "但会让“参赛人数/项目数”重复计数；归一后仍有 54 行为真正的跨项记录，需用 sport_all 字段展开处理。"
)
para("N4 · Team 不能用于国家统计。", bold=True, space_after=2)
para(
    "Team 有 1,193 个取值，其中 2,795 行带 -1/-2/-3 分队后缀（如 China-1、China-2），另有 43 行混合队（如 Denmark/Sweden）。"
    "同一 NOC 可对应多个 Team（NOC=CHN 有 China、China-1、China-2、China-3），因此国家归属一律使用 NOC。"
)
para("N5 · 泛化问题比赛题描述更集中。", bold=True, space_after=2)
para(
    "赛题称 2020/2024 两届约 22–23% 的 Event 泛化；复核结果为 2020 年 20.1%、2024 年 23.1%，两年合计 6,488 行，仅占全量 2.6%。"
    "这说明该问题不是“历史数据普遍脏”，而是最近两届数据源切换的局部断层，处理时应按届次分层，而不是全局清洗。"
)

# ---------------------------------------------------------------- 四、口径
doc.add_heading("四、统计口径定义", level=1)
doc.add_heading("4.1 分析总体与基本约定", level=2)
bullet("范围：Season 恒为 Summer；主口径剔除 1906 年届间奥运会，并保留 is_1906 标记做敏感性对比。")
bullet("1956 年：墨尔本为主办城市，斯德哥尔摩 298 行马术记录并入该届，用 is_1956_stockholm 标注分场。")
bullet("国家归属：一律使用 NOC；Team 仅用于展示。政体继承关系见第七章。")
bullet("记录粒度：一行 = 一名运动员 × 一届 × 一个小项；团体项目每位成员各占一行。")
bullet("年份：沿用官方届次，2020 东京虽然 2021 年举办，仍记为 2020。")

doc.add_heading("4.2 口径 A：运动员行口径（主口径）", level=2)
para(
    "定义：每一条 Medal ∈ {Gold, Silver, Bronze} 的记录计 1 枚奖牌，团体项目每名成员各计 1 枚。"
)
para("结果：含 1906 为 38,818 枚；剔除 1906 为 38,360 枚。")
para(
    "适用：参赛与获奖人数、团体项目贡献、运动员层面的“谁拿到了奖牌”。"
    "失真：团体项目被放大——2024 年美国 131 个金牌行、荷兰 67 个金牌行，而官方分别为 40 金、15 金。"
)
para("该口径不用于任何“历史总奖牌榜”的对外表述；若要和官方数字对话，必须切换到口径 B。")

doc.add_heading("4.3 口径 B：小项口径（对照口径）", level=2)
para(
    "定义：以“届次 + 归一 Sport + 事件键 + 奖牌色”为唯一键去重，同一小项的同一颜色只计 1 枚。"
    "事件键的构造：fine 事件直接用 Event 原文；coarse（泛化）事件追加 Sex，避免男女合并。"
)
para(
    "结果：含 1906 共 17,452 枚。2024 年得到 328 个有奖牌记录的小项（官方 329），其中 325 个有金牌记录，合计 969 枚奖牌；"
    "美国 39 金、中国 40 金、荷兰 15 金（官方锚点为 40 / 40 / 15）。"
)
para(
    "已知偏差：同色并列与拳击/柔道/摔跤/跆拳道的“双铜牌”按 1 枚计，因此总奖牌数不能直接与官方比较；"
    "2024 年铁人三项混合接力整项无奖牌记录，另有 3 个小项缺金牌行。"
)

cmp24 = pd.read_csv(OUT / "caliber_2024_compare.csv")
cmp24 = cmp24.rename(columns={"运动员行金牌": "运动员行金牌", "小项口径金牌": "小项口径金牌", "官方金牌(仅锚点)": "官方金牌（锚点）"})
cmp24["官方金牌（锚点）"] = cmp24["官方金牌（锚点）"].fillna("—")
add_table(cmp24, [2.4, 4.0, 4.0, 4.0], cap="表 4  2024 年双口径金牌对比（官方数字仅取赛题给定的三个锚点）")
add_figure("fig1_caliber_2024.png", "图 1  2024 年双口径金牌对比：小项口径已能复原美国 40、中国 40、荷兰 15")

doc.add_heading("4.4 双口径的分年差异", level=2)
cal = pd.read_csv(OUT / "caliber_by_year.csv")
pick = [1896, 1900, 1904, 1908, 1920, 1952, 1980, 1996, 2008, 2016, 2020, 2024]
show = cal[cal["Year"].isin(pick)].copy()
show.columns = ["届次", "运动员行口径", "小项口径", "差异", "膨胀率"]
add_table(show, [2.2, 3.6, 3.2, 2.6, 2.8],
          cap="表 5  双口径分年差异（膨胀率 =（行口径−小项口径）/ 小项口径；完整 31 届见 shared/metrics/caliber_by_year.csv）")
para(
    "膨胀率不是常数：1896 年只有 23.3%（几乎没有团体项目），1900 年达到 136.9%，2020 年 141.0%，2024 年 135.4%。"
    "这意味着“用运动员行口径画历史总奖牌榜”会把近几届放大 2.3–2.4 倍，且越晚近放大越严重，属于典型的口径陷阱。"
)
add_figure("fig2_inflation.png", "图 2  双口径膨胀率随届次变化（1896–2024）")
add_figure("fig3_sport_ratio.png", "图 3  团体项目是“行数虚高”的主要来源（剔除 1906）", width=14.5)

doc.add_heading("4.5 口径使用规则", level=2)
rules = pd.DataFrame({
    "分析场景": ["历史总奖牌榜、逐届奖牌榜", "参赛人数、获奖人数、女性参与", "团体项目贡献、运动员故事", "2020 前后的连续对比", "与官方数字对话"],
    "推荐口径": ["小项口径", "运动员行口径", "运动员行口径", "小项口径（项目层用归一 Sport）", "小项口径 + 差异清单"],
    "原因": [
        "与官方奖牌榜同粒度，可跨届比较",
        "每个运动员一行，天然对应“人”",
        "团体项目每位成员都真实获得奖牌",
        "Sport 已归一，Event 需避免泛化断层",
        "官方为小项口径；数据缺行须显式说明",
    ],
})
add_table(rules, [5.6, 5.4, 5.4], cap="表 6  不同分析场景下的口径选择")

# ---------------------------------------------------------------- 五、Sport 归一
doc.add_heading("五、体育大类归一映射", level=1)
doc.add_heading("5.1 四类归一规则", level=2)
bullet("拆分合并：2020 起被拆细的大类还原到 2016 前的名称——Artistic Gymnastics→Gymnastics；Cycling Road/Track/Mountain Bike/BMX→Cycling；Canoe Sprint/Slalom→Canoeing。")
bullet("更名统一：Synchronized Swimming / Artistic Swimming→Artistic Swimming；Equestrian→Equestrianism；Trampolining / Trampoline Gymnastics→Trampoline Gymnastics。")
bullet("同类合并：Baseball + Softball + Baseball/Softball→Baseball/Softball；3x3 Basketball→Basketball。")
bullet("逗号拆分：89 行逗号拼接按逗号拆开，逐个映射后用 sport_all 保存完整项目串，主项目取第一个。")

para(
    "归一后有 57 个大类，共 20 个原始取值发生变更。未列出的取值保持原样，所有规则都可在 contracts/sport_map.csv 中逐行核查。"
)

smap = pd.read_csv(OUT / "sport_mapping.csv")
changed = smap[smap["rule"] != "保持不变"][["sport_raw", "sport_norm", "rows", "rule", "note"]].copy()
changed.columns = ["原始 Sport", "归一后", "行数", "规则", "说明"]
changed["说明"] = changed["说明"].fillna("")
add_table(changed, [5.6, 3.2, 1.6, 2.6, 3.4], font=8, cap="表 7  Sport 归一变更明细（20 项；完整 76 项见 contracts/sport_map.csv）", align_left_cols=(0, 4))

doc.add_heading("5.2 逗号拼接与跨项记录", level=2)
para(
    "89 行逗号拼接全部出现在 2024 年，全部为 No medal，因此不影响奖牌榜。归一时按逗号拆分：如 “Cycling Road, Triathlon” 拆为 Cycling 与 Triathlon，"
    "主项目取第一个（Cycling），并用 sport_all=“Cycling|Triathlon”、is_multi_sport=1 标记。若按 Sport 统计参赛人数，必须用 sport_all 展开，否则这 54 行跨项记录会被少算一个项目。"
)

doc.add_heading("5.3 归一效果", level=2)
para(
    "以 Gymnastics 为例：若不归一，2016 年及以前的 26,707 行在 Gymnastics，2020/2024 则被拆到 Artistic Gymnastics；归一后恢复为单一序列，"
    "可直接做“Gymnastics 百年参赛与奖牌曲线”。同理，Cycling 的 9 个原始写法合并为一个序列，避免了“项目在 2020 年突然消失”的假象。"
)
add_figure("fig4_sport_drift.png", "图 4  Sport 口径漂移与归一效果（2016 / 2020 / 2024）", width=13.5)

# ---------------------------------------------------------------- 六、Event
doc.add_heading("六、2020 年起 Event 泛化的处理策略", level=1)
doc.add_heading("6.1 规模与分布", level=2)
gen_tbl = pd.DataFrame({
    "泛化值": ["Men", "Women", "Men Team", "Women Team", "Mixed Team", "Relay Only Athlete", "合计"],
    "行数": [1634, 1539, 1425, 1317, 416, 157, 6488],
    "2020": ["739 行（占该届 20.1%）", "", "", "", "", "", ""],
    "2024": ["", "", "", "", "", "", "3445 行（占该届 23.1%）"],
})
gen_tbl = gen_tbl[["泛化值", "行数"]]
add_table(gen_tbl, [6.0, 3.0], cap="表 8  泛化 Event 的取值分布（2020 年 3,043 行、2024 年 3,445 行）")
add_figure("fig5_generic_event.png", "图 5  Event 泛化行占比：2016 年为 0，2020/2024 年跃升至 20% 以上", width=12.5)
para(
    "泛化集中在团体项目：Football、Hockey、Handball、Rugby Sevens、Volleyball、Basketball、Water Polo 的“Men/Women/Men Team”占了大头；"
    "Judo 的 Mixed Team 与 Swimming 的 Relay Only Athlete 是两类特殊情形——前者本身就是一个真实小项，后者则把多个接力小项压成一个值。"
)

doc.add_heading("6.2 三层处理策略", level=2)
bullet("保留原文：Event 不改写，另建 event_raw 与 event_granularity（fine / coarse），保证可回溯。")
bullet("事件键分级：fine 事件用“届次|归一 Sport|Event”做键；coarse 事件追加 Sex，得到“项目×性别”键，避免男女混合。")
bullet("分析降级：跨 2020 的连续序列一律在 Sport 层做；必须到小项层时，只用 fine 子集，或明确标注 coarse 的粒度限制。")

doc.add_heading("6.3 影响量化（2024）", level=2)
para(
    "按上述键去重，2024 年得到 328 个有奖牌记录的小项、325 个有金牌记录。官方为 329 个小项，差异可逐项解释："
)
recon = pd.DataFrame({
    "项目": ["奖牌小项数", "有金牌记录的小项", "美国金牌", "中国金牌", "荷兰金牌", "德国金牌"],
    "本数据": ["328", "325", "39", "40", "15", "11"],
    "官方": ["329", "329", "40", "40", "15", "12"],
    "差异原因": [
        "铁人三项混合接力整项无奖牌记录（只有 2 条 No medal）",
        "另有 3 个小项缺金牌行：女子公路自行车、男子山地越野、男子 800 米自由泳",
        "女子公路赛金牌行缺失（Faulkner 记为 No medal）",
        "完全一致",
        "完全一致",
        "混合接力金牌行缺失（整项无奖牌记录）",
    ],
})
add_table(recon, [4.2, 2.0, 1.8, 8.4], font=8.5, cap="表 9  2024 年小项口径与官方数字的逐项归因", align_left_cols=(3,))

# ---------------------------------------------------------------- 七、特殊记录
doc.add_heading("七、特殊记录处理规则", level=1)
special = pd.DataFrame({
    "对象": ["1906 届间奥运会", "1956 双城", "URS / EUN / ROC", "GDR / FRG / SAA", "TCH", "YUG / SCG", "ANZ / BOH / UAR / MAL / NBO / RHO", "AIN / EOR / IOA / WIF / AHO"],
    "数据量": ["1,733 行 / 458 奖牌", "298 行（全部马术）", "4,622 + 650 + 561 行", "2,104 + 2,558 + 93 行", "3,369 行", "2,046 + 300 行", "86 / 153 / 123 / 45 / 2 / 12 行", "46 / 79 / 93 / 20 / 74 行"],
    "处理规则": [
        "主口径剔除；保留 is_1906 做敏感性（纳入后奖牌行 +458，约 +1.18%）",
        "并入 1956 墨尔本，is_1956_stockholm 标注分场，不单列届次",
        "继承口径并入 RUS 谱系；历史口径保留原 NOC，两列并存",
        "继承口径并入 GER；历史口径保留原 NOC",
        "可选并入 CZE；因斯洛伐克部分会低估 SVK，默认不合并，仅提供 noc_modern 备选",
        "可选并入 SRB；因继承国不止塞尔维亚，默认不合并",
        "按继承关系分别并入 AUS / CZE / EGY / MAS / MAS / ZIM",
        "保留独立，不并入任何国家；EOR 单列并在任务二、三中单独展示",
    ],
    "代码字段": ["is_1906", "is_1956_stockholm", "noc_modern", "noc_modern", "noc_modern", "noc_modern", "noc_modern", "noc_modern"],
})
add_table(special, [4.4, 3.2, 6.6, 2.4], font=8, cap="表 10  特殊记录处理规则（完整 234 条 NOC 规则见 contracts/noc_map.csv）", align_left_cols=(0, 2))
para(
    "关于 1906：主口径剔除，是因为 IOC 现行口径不承认该届；但纳入与否并不改变任何前十名国家的排序（458 枚奖牌分散在 18 个 NOC），"
    "因此敏感性分析只影响总量，不影响结构性结论。"
)
para(
    "关于政体：noc_modern 只改变“国家谱系”分析（任务二 B、任务三 S3），不改变奖牌行本身。默认关闭继承合并，"
    "是为了避免把苏联的 2,063 枚奖牌直接算到俄罗斯头上这类争议；一旦采用继承口径，必须在图表标题与注释中写明。"
)

# ---------------------------------------------------------------- 八、质量检查
doc.add_heading("八、数据质量检查清单（11 项）", level=1)
para(
    "下表 11 项检查全部可复现：Q1–Q9 的取数代码在 task1-data/pipeline/01_audit.py 与 02_clean.py（国家清单等补充在 01b_extra.py），"
    "Q10–Q11 在 02_clean.py，结果汇总在 contracts/quality_checks.csv。每项都给出检查思路、结果与处理决定。"
)
qc = pd.read_csv(OUT / "quality_checks.csv")[["编号", "检查项", "方法", "结果", "处理决定"]]
add_table(qc, [1.1, 3.0, 3.6, 5.6, 3.3], font=7.5, header_font=8, cap="表 11  数据质量检查清单（逐项可复现）", align_left_cols=(1, 2, 3, 4))

# ---------------------------------------------------------------- 九、数据集
doc.add_heading("九、清洗后数据集说明", level=1)
doc.add_heading("9.1 输出文件", level=2)
files = pd.DataFrame({
    "文件": ["data/processed/olympics_clean.parquet", "task1-data/output/medals_athlete_row.csv", "task1-data/output/medals_event_level.csv", "shared/metrics/medal_table_athlete_noc.csv", "shared/metrics/medal_table_event_noc.csv", "shared/metrics/caliber_by_year.csv、caliber_2024_compare.csv", "contracts/sport_map.csv", "contracts/noc_map.csv", "task1-data/output/athlete_entities.csv、athlete_top_medals.csv", "contracts/known_gaps.csv", "contracts/quality_checks.csv"],
    "内容": ["全量清洗数据（252,565 行，31 列）", "奖牌行口径明细（38,818 行）", "小项口径明细（17,452 行，含 has_gold / 粒度标记）", "行口径奖牌榜（剔除 1906）", "小项口径奖牌榜（剔除 1906，推荐）", "双口径分年差异与 2024 对比", "76 项 Sport 归一映射", "234 个 NOC 全量映射（20 个特殊规则）", "近似运动员实体（Name+Sex+NOC）与奖牌 Top30", "2024 年 4 项已知记录缺失清单", "11 项检查结果"],
    "用途": ["后续所有分析的基础表", "运动员/团体层面的分析", "奖牌榜、跨届对比", "历史总榜（口径 A）", "历史总榜（口径 B，推荐）", "口径敏感性说明", "复现归一过程", "复现国家谱系/决定是否合并", "个体探索的近似方案（需声明）", "2024 图表必须标注的缺口", "质量结论索引"],
})
add_table(files, [6.4, 6.0, 4.0], font=7.8, cap="表 12  清洗产物清单（与仓库目录一致）", align_left_cols=(0, 1, 2))

doc.add_heading("9.2 新增字段", level=2)
fields = pd.DataFrame({
    "字段": ["sport_raw / sport_norm / sport_all", "is_multi_sport", "event_raw / event_name_clean", "event_granularity / event_key_quality", "event_key", "is_team_event", "is_1906 / include_flag", "is_1956_stockholm", "is_refugee", "is_medal / medal_rank", "noc_modern / noc_name", "team_base", "athlete_key"],
    "含义": ["原始项目名 / 归一后主大类 / 全部大类（| 分隔）", "是否逗号拼接的跨项记录", "Event 原文 / 展示用清洗名", "fine|coarse 与 specific|generic 一一对应", "去重与连接用的事件键", "是否团体项目（同小项同牌同 NOC 多行）", "是否 1906；是否纳入默认分析", "是否 1956 斯德哥尔摩马术分场", "是否难民代表团", "是否奖牌行 / 金 1 银 2 铜 3", "继承口径的现代 NOC / NOC 的常用队伍名", "去除 -数字 分队后缀的 Team", "近似运动员实体：Name|Sex|NOC（不可当官方 ID）"],
})
add_table(fields, [5.4, 11.0], font=8, cap="表 13  字段字典（含跨任务冻结字段）", align_left_cols=(0, 1))

doc.add_heading("9.3 行数与守恒校验", level=2)
bullet("全量行数保持 252,565，清洗只增列不删行（31 列），任何筛选都可逆。")
bullet("奖牌行 38,818 = 金 13,002 + 银 12,746 + 铜 13,070，与原始文件一致。")
bullet("小项口径 17,452；主口径（剔除 1906）奖牌行 38,360、小项 17,233。")
bullet("归一后 Sport 57 类；Event 1,041 个原始取值，其中 6,488 行为 coarse 粒度。")
bullet("交付前 04_validate.py 共 18 项断言全部通过。")

doc.add_heading("9.4 已知局限", level=2)
limits = pd.DataFrame({
    "局限": ["并列奖牌与双铜牌按 1 枚计", "2024 年 1 个小项整项缺失、3 个小项缺金牌行", "泛化 Event 无法完全还原", "姓名不能识别个体", "混合 NOC 事件按主 NOC 归属", "1906 是否纳入存在争议", "Sport 归一含主观判断", "未引入外部数据"],
    "影响": ["小项口径总奖牌数略低于官方，不能直接比总数", "美国 39/40、德国 11/12 偏低", "2020 的 Relay Only Athlete 等仍需降级到项目×性别", "不做个体排名与跨届运动员追踪", "1900 年丹麦/瑞典等混合队只计入主 NOC", "纳入会使奖牌总量 +1.18%", "Trampoline、Rugby、Baseball 等边界可讨论", "人口/GDP 等未合并，性别差异未做人口标准化"],
    "应对": ["只比金牌数，或另附并列清单", "与官方对比时引用表 9 的差异清单", "任务二 D 视角只用 fine 子集或 Sport 层", "任务三避开 S6，或声明近似实体", "在图表注释中说明归属规则", "主口径剔除，敏感性分析单独列示", "映射表全文公开，接受复核", "任务三如需再按 FAQ 声明来源"],
})
add_table(limits, [5.4, 6.2, 4.8], font=8, cap="表 14  已知局限与应对", align_left_cols=(0, 1, 2))

# ---------------------------------------------------------------- 十、复现
doc.add_heading("十、复现说明", level=1)
para("环境：Windows 10/11，Python 3.12.10，pandas 3.0.3，numpy，pyarrow，matplotlib；生成说明书另需 python-docx。")
para("运行顺序（在项目根目录执行）：")
for cmd in ["python task1-data/pipeline/01_audit.py", "python task1-data/pipeline/01b_extra.py",
            "python task1-data/pipeline/02_clean.py", "python task1-data/pipeline/03_figures.py",
            "python task1-data/pipeline/04_validate.py", "python task1-data/pipeline/05_build_spec.py"]:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.space_after = Pt(2)
    set_run(p.add_run(cmd), 9.5, font="Consolas")
para("原始数据放在 data/raw/olympics_dataset.csv，只读不改；清洗产物写 data/processed/，中间表写 task1-data/output/，契约写 contracts/，共享指标写 shared/metrics/。")
para("文件结构：task1-data/ 为任务一代码与文档，contracts/ 为跨任务契约，shared/metrics/ 为报告统一底表。")

# ---------------------------------------------------------------- 十一、参考
doc.add_heading("十一、参考资料", level=1)
bullet("赛题数据：Summer Olympics Medals (1896-2024)，Kaggle，作者 Stefany De Oliveira（CC BY-NC-SA 4.0）。")
bullet("上游数据：Olympics 124 years Dataset (till 2020)（Nitish Sharma）；Paris 2024 Olympic Summer Games（Petro Ivaniuk）。")
bullet("赛题文档：《数说奥运 · 1896–2024》赛题介绍与答卷模板。")
bullet("交叉验证：Olympedia（olympedia.org）、olympics.com 官方奖牌榜、维基百科历届奖牌榜词条。")

# ---------------------------------------------------------------- 附录
doc.add_heading("附录 A  2024 年差异归因明细", level=1)
appendix = pd.DataFrame({
    "指标": ["奖牌小项数", "有金牌记录的小项", "总奖牌数", "美国金牌", "中国金牌", "荷兰金牌", "德国金牌"],
    "本数据": ["328", "325", "969", "39", "40", "15", "11"],
    "官方/锚点": ["329", "329", "—", "40", "40", "15", "12"],
    "归因": [
        "铁人三项混合接力整项无奖牌记录（只有 2 条 No medal）",
        "另有女子公路赛、男子山地越野、男子 800 米自由泳缺金牌行",
        "双铜牌与并列按 1 枚计，官方总数口径不同，不作直接比较",
        "女子公路赛金牌行缺失（Faulkner 被记为 No medal）",
        "无差异，可验证小项口径的正确性",
        "无差异，可验证小项口径的正确性",
        "混合接力金牌行缺失（整项无奖牌记录）",
    ],
})
add_table(appendix, [3.8, 2.4, 2.8, 7.4], font=8.5, cap="表 A-1  2024 年小项口径与官方的逐项归因（官方总数不作比较）", align_left_cols=(3,))

doc.save(DOC_PATH)
print("saved:", DOC_PATH)
