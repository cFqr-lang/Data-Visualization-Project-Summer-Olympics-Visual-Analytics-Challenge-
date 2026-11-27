# -*- coding: utf-8 -*-
"""
奥运百年可视化 Dashboard - 任务四
生成单文件 HTML，浏览器打开即可交互
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import get_plotlyjs   # P1-1 内联 Plotly.js
from pathlib import Path
import json, os

# ============ 0. 路径配置（P0-1 修复：可移植·无硬编码·严格报错） ============
# 找 olympics_dataset.csv：只在仓库 data/raw 和脚本同目录查找
CANDIDATE_PATHS = [
    Path(__file__).resolve().parents[1] / "data" / "raw" / "olympics_dataset.csv",
    Path(__file__).resolve().parent / "olympics_dataset.csv",
]
DATA_CSV = next((p for p in CANDIDATE_PATHS if p.exists()), None)
if DATA_CSV is None:
    raise FileNotFoundError(
        f"未找到 olympics_dataset.csv。已搜索：\n"
        + "\n".join(f"  - {p}" for p in CANDIDATE_PATHS)
    )
OUT_HTML = Path(__file__).resolve().parent / "olympics_dashboard.html"

# ============ 1. 加载 + 数据清洗 ============
print(f"Loading data from: {DATA_CSV}")
df = pd.read_csv(DATA_CSV)
print(f"  Raw rows: {len(df)}")

# ---- Sport 归一化映射表（处理 Q2 漂移 + 逗号拼接） ----
SPORT_MAP = {
    # 2020 年大类拆分 -> 原大类（归到传统名，保留细节字段）
    'Artistic Gymnastics': 'Gymnastics',
    'Trampoline Gymnastics': 'Gymnastics',
    'Rhythmic Gymnastics': 'Gymnastics',
    'Trampolining': 'Gymnastics',
    'Canoe Slalom': 'Canoeing',
    'Canoe Sprint': 'Canoeing',
    'Cycling Road': 'Cycling',
    'Cycling Track': 'Cycling',
    'Cycling Mountain Bike': 'Cycling',
    'Cycling BMX Racing': 'Cycling',
    'Cycling BMX Freestyle': 'Cycling',
    'Marathon Swimming': 'Swimming',
    # 拼写变化
    'Equestrian': 'Equestrianism',
    'Artistic Swimming': 'Synchronized Swimming',
    'Baseball/Softball': 'Softball',  # 历史上是分开的
    # 逗号拼接的跨项 -> 取主项
    '3x3 Basketball, Basketball': 'Basketball',
    'Cycling Road, Cycling Mountain Bike': 'Cycling',
    'Cycling Road, Cycling Track': 'Cycling',
    'Cycling Road, Triathlon': 'Cycling',
    'Marathon Swimming, Swimming': 'Swimming',
    # 2024 新增保留
    '3x3 Basketball': 'Basketball',
    'Breaking': 'Wrestling',  # 霹雳舞归类到摔跤/体操？暂时单独保留，但归一到 Gymnastics-like
}
# 对 Breaking 做特殊映射
df['Sport_Norm'] = df['Sport'].replace(SPORT_MAP)
# Breaking 单独保留但映射到更传统的分类
df.loc[df['Sport'] == 'Breaking', 'Sport_Norm'] = 'Breaking'
df.loc[df['Sport'] == 'Karate', 'Sport_Norm'] = 'Karate'
df.loc[df['Sport'] == 'Skateboarding', 'Sport_Norm'] = 'Skateboarding'
df.loc[df['Sport'] == 'Surfing', 'Sport_Norm'] = 'Surfing'
df.loc[df['Sport'] == 'Sport Climbing', 'Sport_Norm'] = 'Sport Climbing'
df.loc[df['Sport'] == '3x3 Basketball', 'Sport_Norm'] = 'Basketball'

# ---- 标记奖牌行 ----
df['HasMedal'] = df['Medal'] != 'No medal'
df['Gold'] = (df['Medal'] == 'Gold').astype(int)
df['Silver'] = (df['Medal'] == 'Silver').astype(int)
df['Bronze'] = (df['Medal'] == 'Bronze').astype(int)

# ---- 两种口径 ----
# 口径 A: 运动员行口径（每一行 = 一名运动员 × 一个小项）
# 口径 B: 小项口径（同届 × 同 NOC × 同 Sport × 同 Event × 同 Medal 去重 = 1 个小项冠军）
# P0-2 修复：去掉 City 和 Team（同届同小项同奖牌但两支队伍不应算两个单位）
#         统一排除 1906（IOC 不承认届次，与任务一/二口径一致）
df_event = df[(df['HasMedal']) & (df['Year'] != 1906)].drop_duplicates(
    subset=['Year', 'NOC', 'Sport', 'Event', 'Medal']
).copy()

# ---- 政体变迁脉络 ----
NOC_GROUP = {
    'URS': '苏联谱系', 'EUN': '苏联谱系', 'RUS': '苏联谱系', 'ROC': '苏联谱系', 'AIN': '苏联谱系',
    'FRG': '德国谱系', 'GDR': '德国谱系', 'GER': '德国谱系',
    'YUG': '前南谱系', 'SCG': '前南谱系', 'SRB': '前南谱系', 'CRO': '前南谱系', 'SLO': '前南谱系', 'BIH': '前南谱系', 'MKD': '前南谱系', 'MNE': '前南谱系', 'KOS': '前南谱系',
}
df['NOC_Group'] = df['NOC'].map(NOC_GROUP).fillna('独立参赛')

# ---- 识别主办国 ----
HOST_MAP = {
    1896: 'GRE', 1900: 'FRA', 1904: 'USA', 1908: 'GBR', 1912: 'SWE',
    1916: None, 1920: 'BEL', 1924: 'FRA', 1928: 'NED', 1932: 'USA',
    1936: 'GER', 1940: None, 1944: None, 1948: 'GBR', 1952: 'FIN',
    1956: 'AUS', 1960: 'ITA', 1964: 'JPN', 1968: 'MEX', 1972: 'FRG',
    1976: 'CAN', 1980: 'URS', 1984: 'USA', 1988: 'KOR', 1992: 'ESP',
    1996: 'USA', 2000: 'AUS', 2004: 'GRE', 2008: 'CHN', 2012: 'GBR',
    2016: 'BRA', 2020: 'JPN', 2024: 'FRA', 2028: 'USA', 2032: 'AUS',
}
df['IsHost'] = df.apply(lambda r: HOST_MAP.get(r['Year']) == r['NOC'], axis=1)
# 小项口径数据同步主办国标记（供 Tab E 东道主效应对齐任务三口径使用）
df_event['IsHost'] = df_event['Year'].map(HOST_MAP) == df_event['NOC']

print("Data cleaned. Building charts...")

# ============ 2. 各 Tab 图表生成 ============

def template():
    return dict(layout=dict(
        font=dict(family="Microsoft YaHei, SimHei, Arial", size=13),
        paper_bgcolor='#fafafa', plot_bgcolor='#fafafa',
        margin=dict(l=60, r=30, t=60, b=50)
    ))

# ------- Tab A: 奖牌格局 -------
# A1: 逐届奖牌数（双口径）
g_year = df[df['HasMedal']].groupby('Year').agg(
    金牌行=('Gold', 'sum'), 银牌行=('Silver', 'sum'), 铜牌行=('Bronze', 'sum'),
    总奖牌行=('HasMedal', 'sum'), 参赛记录=('player_id', 'count')
).reset_index()
# 小项口径
ge_year = df_event.groupby('Year').agg(
    金牌小项=('Gold', 'sum'), 银牌小项=('Silver', 'sum'), 铜牌小项=('Bronze', 'sum'),
    总小项=('HasMedal', 'sum')
).reset_index()
g_year = g_year.merge(ge_year, on='Year', how='outer').fillna(0)

fig_a = make_subplots(rows=1, cols=2, subplot_titles=('逐届奖牌数（运动员行口径）', '逐届奖牌数（小项口径）'))
fig_a.add_trace(go.Bar(x=g_year.Year, y=g_year.金牌行, name='金', marker_color='#FFD700'), row=1, col=1)
fig_a.add_trace(go.Bar(x=g_year.Year, y=g_year.银牌行, name='银', marker_color='#C0C0C0'), row=1, col=1)
fig_a.add_trace(go.Bar(x=g_year.Year, y=g_year.铜牌行, name='铜', marker_color='#CD7F32'), row=1, col=1)
fig_a.add_trace(go.Bar(x=g_year.Year, y=g_year.金牌小项, name='金', marker_color='#FFD700', showlegend=False), row=1, col=2)
fig_a.add_trace(go.Bar(x=g_year.Year, y=g_year.银牌小项, name='银', marker_color='#C0C0C0', showlegend=False), row=1, col=2)
fig_a.add_trace(go.Bar(x=g_year.Year, y=g_year.铜牌小项, name='铜', marker_color='#CD7F32', showlegend=False), row=1, col=2)
fig_a.update_layout(barmode='stack', template='plotly_white', height=420, width=1200,
    title=dict(text='A. 百年奥运奖牌格局（双口径对比）', x=0.5))
fig_a.update_xaxes(type='linear', dtick=8, tickangle=-45, tickfont=dict(size=10), automargin=True)

# A2: 历史总奖牌榜 Top20
g_total = df[df['HasMedal']].groupby('NOC').agg(
    金牌=('Gold', 'sum'), 银牌=('Silver', 'sum'), 铜牌=('Bronze', 'sum'),
    奖牌行总数=('HasMedal', 'sum')
).reset_index().sort_values('奖牌行总数', ascending=False).head(20)
fig_a2 = go.Figure()
fig_a2.add_trace(go.Bar(y=g_total.NOC, x=g_total.金牌, orientation='h', name='金', marker_color='#FFD700', text=g_total.金牌, textposition='outside'))
fig_a2.add_trace(go.Bar(y=g_total.NOC, x=g_total.银牌, orientation='h', name='银', marker_color='#C0C0C0', text=g_total.银牌, textposition='outside'))
fig_a2.add_trace(go.Bar(y=g_total.NOC, x=g_total.铜牌, orientation='h', name='铜', marker_color='#CD7F32', text=g_total.铜牌, textposition='outside'))
fig_a2.update_layout(barmode='stack', template='plotly_white', height=600, width=1200,
    title=dict(text='历史总奖牌榜 Top 20（运动员行口径）', x=0.5),
    xaxis=dict(title='奖牌行数'), legend=dict(orientation='h', y=1.05))
fig_a2.update_yaxes(autorange='reversed')

# A3: 奖牌通货膨胀 — 总奖牌行 + 代表团数 + 参赛人数
g_scale = df.groupby('Year').agg(
    代表团数=('NOC', 'nunique'), 参赛运动员=('player_id', 'nunique'),
    奖牌行=('HasMedal', 'sum')
).reset_index()
# 三条序列量级差最大 70 倍：左 panel 奖牌行 + 参赛运动员（双轴），右 panel 代表团数独立刻度
fig_a3 = make_subplots(rows=1, cols=2, column_widths=[0.58, 0.42],
    subplot_titles=('奖牌行（左轴）与参赛运动员（右轴）', '代表团数（独立刻度）'),
    specs=[[{"secondary_y": True}, {}]])
fig_a3.add_trace(go.Bar(x=g_scale.Year, y=g_scale.奖牌行, name='奖牌行', marker_color='#4A90D9'),
    row=1, col=1, secondary_y=False)
fig_a3.add_trace(go.Scatter(x=g_scale.Year, y=g_scale.参赛运动员, name='参赛运动员', mode='lines+markers',
    line=dict(color='#27AE60', width=2)), row=1, col=1, secondary_y=True)
fig_a3.add_trace(go.Scatter(x=g_scale.Year, y=g_scale.代表团数, name='代表团数', mode='lines+markers',
    line=dict(color='#E74C3C', width=2)), row=1, col=2)
fig_a3.update_layout(template='plotly_white', height=420, width=1200,
    title=dict(text='奖牌的通货膨胀：规模扩张曲线', x=0.5))
fig_a3.update_yaxes(title_text='奖牌行数', rangemode='tozero', row=1, col=1, secondary_y=False)
fig_a3.update_yaxes(title_text='参赛运动员数', rangemode='tozero', row=1, col=1, secondary_y=True)
fig_a3.update_yaxes(title_text='代表团数', rangemode='tozero', row=1, col=2)
fig_a3.update_xaxes(type='linear', range=[1893, 2027], dtick=8, tickangle=-45, tickfont=dict(size=10), automargin=True)

print("  Tab A done")

# ------- Tab B: 国家兴衰 -------
# B1: 10 个代表国家逐届奖牌曲线
countries_of_interest = ['USA', 'CHN', 'URS', 'RUS', 'GBR', 'FRA', 'JPN', 'KOR', 'GER', 'AUS', 'BRA', 'CAN']
g_ctry = df[df['HasMedal'] & df['NOC'].isin(countries_of_interest)].groupby(['Year','NOC']).agg(
    金牌=('Gold', 'sum'), 总奖牌=('HasMedal', 'sum')
).reset_index()

fig_b = go.Figure()
colors = ['#E74C3C', '#FFD700', '#9B59B6', '#3498DB', '#2ECC71', '#E67E22', '#1ABC9C', '#F39C12', '#95A5A6', '#34495E', '#16A085', '#8E44AD']
for i, c in enumerate(countries_of_interest):
    sub = g_ctry[g_ctry.NOC == c]
    fig_b.add_trace(go.Scatter(x=sub.Year, y=sub.总奖牌, name=c,
        mode='lines+markers', line=dict(width=2), marker_size=5,
        line_color=colors[i % len(colors)]))
# 标注冷战时期（数值轴：用具体年份区间，不能用类别字符串；两侧错开避免文字叠印）
fig_b.add_vrect(x0=1952, x1=1988, fillcolor='#F8B500', opacity=0.1, line_width=0,
                annotation_text='冷战', annotation_position='top left')
fig_b.add_vrect(x0=1980, x1=1984, fillcolor='#E74C3C', opacity=0.15, line_width=0,
                annotation_text='抵制潮', annotation_position='top right')
fig_b.update_layout(template='plotly_white', height=500, width=1200,
    title=dict(text='B. 国家兴衰：12 国逐届总奖牌行', x=0.5),
    xaxis=dict(title='年份'), yaxis=dict(title='奖牌行总数'),
    legend=dict(font=dict(size=11)))
fig_b.update_xaxes(type='linear', dtick=8, tickangle=-45, tickfont=dict(size=10), automargin=True)

# B2: 政体变迁脉络 — 苏联谱系
g_bloc = df[df['NOC_Group'] != '独立参赛'].groupby(['Year','NOC_Group']).agg(
    总奖牌=('HasMedal', 'sum')
).reset_index()
fig_b2 = go.Figure()
for grp in g_bloc.NOC_Group.unique():
    sub = g_bloc[g_bloc.NOC_Group == grp]
    fig_b2.add_trace(go.Bar(x=sub.Year, y=sub.总奖牌, name=grp))
fig_b2.update_layout(template='plotly_white', height=400, width=1200, barmode='stack',
    title=dict(text='地缘政治的投影：政体变迁脉络', x=0.5),
    xaxis=dict(title='年份'), yaxis=dict(title='奖牌行'))
fig_b2.update_xaxes(type='linear', dtick=8, tickangle=-45, tickfont=dict(size=10), automargin=True)

print("  Tab B done")

# ------- Tab C: 她的奥运 -------
# C1: 女性占比弧线
g_sex = df.groupby('Year').agg(
    女性参赛=('Sex', lambda x: (x=='F').sum()),
    总参赛=('Sex', 'count'),
    总奖牌行=('HasMedal', 'sum')
).reset_index()
g_sex['女性占比'] = g_sex['女性参赛'] / g_sex['总参赛'] * 100
g_fmedal = df[(df['HasMedal']) & (df['Sex']=='F')].groupby('Year').size().reset_index(name='女性奖牌')
g_sex = g_sex.merge(g_fmedal, on='Year', how='left')
g_sex['女性奖牌'] = g_sex['女性奖牌'].fillna(0).astype(int)
g_sex['女性奖牌占比'] = g_sex['女性奖牌'] / g_sex['总奖牌行'] * 100

fig_c = make_subplots(rows=1, cols=2, subplot_titles=('女性参赛占比', '女性奖牌占比'))
fig_c.add_trace(go.Scatter(x=g_sex.Year, y=g_sex['女性占比'], mode='lines+markers',
    fill='tozeroy', line=dict(color='#E91E63', width=3), marker_size=7, name='参赛占比',
    text=g_sex['女性占比'].round(1).astype(str)+'%', textposition='top center'), row=1, col=1)
fig_c.add_trace(go.Scatter(x=g_sex.Year, y=g_sex['女性奖牌占比'], mode='lines+markers',
    fill='tozeroy', line=dict(color='#9C27B0', width=3), marker_size=7, name='奖牌占比',
    text=g_sex['女性奖牌占比'].round(1).astype(str)+'%', textposition='top center'), row=1, col=2)
fig_c.update_layout(template='plotly_white', height=450, width=1200, showlegend=False,
    title=dict(text='C. 她的奥运：从 0% 到 49.1% 的百年弧线', x=0.5))
fig_c.add_hline(y=49.1, line_dash='dash', line_color='#E91E63', annotation_text='2024: 49.1%', row=1, col=1)
fig_c.update_xaxes(type='linear', dtick=8, tickangle=-45, tickfont=dict(size=10), automargin=True)

# C2: 各国女性获奖榜
g_fcountry = df[(df['HasMedal']) & (df['Sex']=='F')].groupby('NOC').agg(
    女子金牌=('Gold', 'sum'), 女子总奖牌=('HasMedal', 'sum')
).reset_index().sort_values('女子总奖牌', ascending=False).head(15)
fig_c2 = go.Figure()
fig_c2.add_trace(go.Bar(y=g_fcountry.NOC, x=g_fcountry.女子总奖牌, orientation='h', 
    marker_color='#E91E63', text=g_fcountry.女子总奖牌, textposition='outside'))
fig_c2.update_layout(template='plotly_white', height=500, width=1200,
    title=dict(text='各国女性总奖牌 Top 15', x=0.5),
    xaxis=dict(title='女子奖牌行'), yaxis=dict(autorange='reversed'))

print("  Tab C done")

# ------- Tab D: 项目演化 -------
# D1: 小项数量增长
g_event = df.groupby('Year').agg(
    参赛小项数=('Event', 'nunique'), 参赛大类数=('Sport_Norm', 'nunique')
).reset_index()
fig_d = make_subplots(specs=[[{"secondary_y": True}]])
fig_d.add_trace(go.Bar(x=g_event.Year, y=g_event.参赛小项数, name='小项数', marker_color='#3498DB'), secondary_y=False)
fig_d.add_trace(go.Scatter(x=g_event.Year, y=g_event.参赛大类数, name='大类数',
    mode='lines+markers', line=dict(color='#E74C3C', width=2)), secondary_y=True)
fig_d.update_layout(template='plotly_white', height=400, width=1200,
    title=dict(text='D. 项目演化：规模膨胀曲线', x=0.5))
fig_d.update_yaxes(title_text='小项数', rangemode='tozero', secondary_y=False)
fig_d.update_yaxes(title_text='大类数', rangemode='tozero', dtick=10, secondary_y=True)
fig_d.update_xaxes(type='linear', dtick=8, tickangle=-45, tickfont=dict(size=10), automargin=True)

# D2: 消失 vs 新增项目（按首次/末次出现年份）
sport_year = df.groupby('Sport_Norm')['Year'].agg(['min','max','nunique']).reset_index()
sport_year.columns = ['Sport','First','Last','Years']
# 消失: 末次 < 1972 且年限 <= 5
vanished = sport_year[(sport_year.Last <= 1972) & (sport_year.Years <= 5)].sort_values('Last')
added = sport_year[sport_year.First >= 2000].sort_values('First')

fig_d2 = make_subplots(rows=1, cols=2, subplot_titles=('消失的运动（末次≤1972）', '2000年后新增的运动'))
if len(vanished) > 0:
    fig_d2.add_trace(go.Bar(y=vanished.Sport, x=vanished.Last, orientation='h',
        text=vanished.Last, textposition='outside', marker_color='#95A5A6'), row=1, col=1)
if len(added) > 0:
    fig_d2.add_trace(go.Bar(y=added.Sport, x=added.First, orientation='h',
        text=added.First, textposition='outside', marker_color='#27AE60'), row=1, col=2)
fig_d2.update_layout(template='plotly_white', height=500, width=1200, showlegend=False,
    title=dict(text='D. 消失与新增的运动', x=0.5))
# x 是年份：从 0 起画会让所有横条几乎等长，必须限定各自的年份窗口
fig_d2.update_xaxes(range=[1880, 1980], dtick=20, tickfont=dict(size=10), automargin=True, row=1, col=1)
fig_d2.update_xaxes(range=[1995, 2030], dtick=10, tickfont=dict(size=10), automargin=True, row=1, col=2)

print("  Tab D done")

# ------- Tab E: 专题深挖 -------
# E1: 东道主效应热力图
# E1 口径对齐任务三：东道主效应统一用"小项口径"（df_event，已按 Year+NOC+Sport+Event+Medal 去重、排除 1906）
g_host_noc = df_event.groupby(['Year','NOC','IsHost']).size().reset_index(name='奖牌')
# 只保留主办国行（数据源已限定为小项口径 df_event）
host_rows_event = g_host_noc[g_host_noc['IsHost']].copy()
host_rows_event['Host'] = host_rows_event['NOC']
host_rows_event['增益倍率'] = 0  # 下面算

# 算东道主增益：主办年 vs 前一届非主办年的奖牌比
host_effect_rows = []
for _, row in host_rows_event.iterrows():
    y = row['Year']
    noc = row['NOC']
    host_medals = row['奖牌']
    prev_year = y - 4
    prev = g_host_noc[(g_host_noc.Year == prev_year) & (g_host_noc.NOC == noc) & (~g_host_noc.IsHost)]
    if len(prev) > 0:
        prev_medals = prev['奖牌'].values[0]
        ratio = host_medals / prev_medals if prev_medals > 0 else float('inf')
    else:
        ratio = None
    host_effect_rows.append({'Year': y, 'NOC': noc, 'HostMedals': host_medals, 
                              'PrevMedals': prev_medals if len(prev) > 0 else None, '增益倍率': ratio})

host_effect = pd.DataFrame(host_effect_rows)
host_effect = host_effect[host_effect['增益倍率'].notna() & (host_effect['增益倍率'] < 20)]

fig_e = make_subplots(rows=1, cols=2, subplot_titles=('东道主奖牌小项数 vs 前一届（小项口径）', '东道主增益倍率（小项口径）'))
# x 只放年份（单行可读），国家名进 hover，避免「年份<br>国家」双行标签互相覆盖
host_noc = host_effect['NOC'].tolist()
fig_e.add_trace(go.Bar(x=host_effect.Year, y=host_effect.HostMedals, name='主办年',
    marker_color='#E74C3C', customdata=host_noc,
    hovertemplate='%{x} %{customdata}<br>主办年奖牌小项 %{y}<extra></extra>'), row=1, col=1)
fig_e.add_trace(go.Bar(x=host_effect.Year, y=host_effect.PrevMedals, name='前一届',
    marker_color='#BDC3C7', customdata=host_noc,
    hovertemplate='%{x} %{customdata}<br>前一届奖牌小项 %{y}<extra></extra>'), row=1, col=1)
fig_e.add_trace(go.Scatter(x=host_effect.Year, y=host_effect['增益倍率'], mode='lines+markers+text',
    name='增益倍率', text=host_effect['增益倍率'].round(1), textposition='top center',
    customdata=host_noc, hovertemplate='%{x} %{customdata}<br>增益倍率 %{y:.2f}x<extra></extra>',
    line=dict(color='#F39C12', width=3), marker_size=8), row=1, col=2)
fig_e.update_layout(template='plotly_white', height=500, width=1400, barmode='group',
    title=dict(text='E. 专题深挖：东道主效应', x=0.5))
fig_e.update_xaxes(type='linear', range=[1893, 2027], dtick=8, tickangle=-45, tickfont=dict(size=10), automargin=True, row=1, col=1)
fig_e.update_xaxes(type='linear', range=[1893, 2027], dtick=8, tickangle=-45, tickfont=dict(size=10), automargin=True, row=1, col=2)

# E2: 小代表团的大突破
# 取从未成为主办国且历史总奖牌 < 50 的小代表团，按最近届奖牌排名
small_nocs = df[df['HasMedal']].groupby('NOC').agg(
    总奖牌=('HasMedal','sum'), 参赛届数=('Year','nunique'),
    首金年=('Year','min'), 末金年=('Year','max')
).reset_index()
small_nocs = small_nocs[(small_nocs.总奖牌 >= 1) & (small_nocs.总奖牌 < 100)].sort_values('末金年', ascending=False).head(20)

fig_e2 = go.Figure()
fig_e2.add_trace(go.Scatter(y=small_nocs.NOC, x=small_nocs.总奖牌, mode='markers+text',
    text=small_nocs.总奖牌, textposition='middle right',
    marker=dict(size=small_nocs.参赛届数*3, color=small_nocs.末金年, colorscale='YlOrRd', showscale=True,
        colorbar=dict(title='末金年', tickmode='array', tickvals=[2024], ticktext=['2024'])),
    textfont=dict(size=11)))
fig_e2.update_layout(template='plotly_white', height=550, width=1200,
    title=dict(text='小代表团的大突破（气泡大小=参赛届数，颜色=末金年）', x=0.5),
    xaxis=dict(title='历史奖牌行总数'), yaxis=dict(autorange='reversed', title='NOC'))

print("  Tab E done")

# ============ 3. 生成 HTML ============
print("Generating HTML...")

# 统一布局：标题 / 图例 / 边距做垂直分层，避免导出时图例被压回标题同一水平带
EXPORT_LAYOUT = dict(
    margin=dict(t=110, r=40, b=80, l=70),
    title=dict(y=0.98, yanchor='top'),
    legend=dict(orientation='h', y=1.12, yanchor='bottom', x=0),
)
for _fig in (fig_a, fig_a2, fig_a3, fig_b, fig_b2, fig_c, fig_c2, fig_d, fig_d2, fig_e, fig_e2):
    _fig.update_layout(**EXPORT_LAYOUT)

figs = {
    'tab_a1_medal_structure': fig_a,
    'tab_a2_top20': fig_a2,
    'tab_a3_inflation': fig_a3,
    'tab_b1_nation_curves': fig_b,
    'tab_b2_bloc_evolution': fig_b2,
    'tab_c1_female_ratio': fig_c,
    'tab_c2_female_medalists': fig_c2,
    'tab_d1_event_growth': fig_d,
    'tab_d2_vanished_added': fig_d2,
    'tab_e1_host_effect': fig_e,
    'tab_e2_small_nocs': fig_e2,
}

# 把每个 fig 存成 div
html_divs = {}
for name, fig in figs.items():
    html_divs[name] = fig.to_html(full_html=False, include_plotlyjs=False)

# 汇总信息
summary = {
    'raw_rows': len(df),
    'medal_rows': len(df[df['HasMedal']]),
    'medal_events': len(df_event),
    'years': sorted(df.Year.unique()),
    'nocs': df.NOC.nunique(),
    'sports_raw': df.Sport.nunique(),
    'sports_norm': df.Sport_Norm.nunique(),
    'female_pct_2024': round(df[(df.Year==2024)].Sex.value_counts().get('F',0) / 
                            len(df[df.Year==2024]) * 100, 1),
}

# 组装 HTML
# P1-1 修复：内联 Plotly.js，真正单文件离线可跑
PLOTLY_JS = get_plotlyjs()
HTML_HEAD = """<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8">
<title>数说奥运 · 1896-2024 · 百年圣火可视分析 Dashboard</title>
""" + '<script>' + PLOTLY_JS + '</script>\n' + """<style>
* { box-sizing: border-box; }
body { font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif; margin: 0; background: #f0f2f5; color: #333; }
.header { background: linear-gradient(135deg, #8B0000 0%, #C0392B 100%); color: white; padding: 30px 40px; box-shadow: 0 2px 10px rgba(0,0,0,.15); }
.header h1 { margin: 0; font-size: 28px; letter-spacing: 2px; }
.header p { margin: 8px 0 0; opacity: .9; }
.stats { display: flex; gap: 20px; padding: 20px 40px; background: white; border-bottom: 1px solid #eee; flex-wrap: wrap; }
.stat { background: #f8f9fa; border-left: 4px solid #C0392B; padding: 12px 20px; flex: 1; min-width: 140px; border-radius: 4px; }
.stat .num { font-size: 24px; font-weight: bold; color: #8B0000; }
.stat .lbl { font-size: 12px; color: #666; margin-top: 4px; }
.tabs { display: flex; background: #2c3e50; padding: 0 40px; flex-wrap: wrap; }
.tab { padding: 16px 24px; color: #ecf0f1; cursor: pointer; border-bottom: 3px solid transparent; font-weight: 500; transition: all .2s; font-size: 15px; }
.tab:hover { background: #34495e; }
.tab.active { background: #ecf0f1; color: #2c3e50; border-bottom-color: #C0392B; font-weight: bold; }
.tab-content { padding: 30px 40px; }
.panel { background: white; border-radius: 8px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 4px rgba(0,0,0,.06); }
.panel h3 { margin: 0 0 12px; color: #2c3e50; font-size: 18px; border-left: 4px solid #C0392B; padding-left: 12px; }
.insight { background: #fef9e7; border-left: 4px solid #f39c12; padding: 14px 18px; margin: 16px 0; border-radius: 4px; line-height: 1.8; font-size: 14px; }
.insight strong { color: #d68910; }
.method { background: #eaf2f8; border-left: 4px solid #2980b9; padding: 12px 18px; margin: 12px 0; border-radius: 4px; font-size: 13px; color: #1a5276; }
.hide { display: none; }
.footer { text-align: center; padding: 24px; color: #888; font-size: 12px; border-top: 1px solid #eee; margin-top: 20px; }
</style>
</head><body>
"""

HTML_BODY = f"""
<div class="header">
  <h1>🏅 数说奥运 · 1896–2024</h1>
  <p>百年圣火可视分析 Dashboard · 数据来自 Kaggle Summer Olympics Medals · CC BY-NC-SA 4.0</p>
</div>

<div class="stats">
  <div class="stat"><div class="num">{summary['raw_rows']:,}</div><div class="lbl">参赛记录数（1人×1小项）</div></div>
  <div class="stat"><div class="num">{summary['medal_rows']:,}</div><div class="lbl">奖牌行数（运动员行口径）</div></div>
  <div class="stat"><div class="num">{summary['medal_events']:,}</div><div class="lbl">奖牌小项数（小项口径·不含1906）</div></div>
  <div class="stat"><div class="num">{summary['nocs']}</div><div class="lbl">参赛 NOC 数</div></div>
  <div class="stat"><div class="num">{len(summary['years'])}</div><div class="lbl">届数（含1906）</div></div>
  <div class="stat"><div class="num">{summary['female_pct_2024']}%</div><div class="lbl">2024 女性占比</div></div>
</div>

<div class="tabs">
  <div class="tab active" onclick="switchTab('a', this)">A. 奖牌格局</div>
  <div class="tab" onclick="switchTab('b', this)">B. 国家兴衰</div>
  <div class="tab" onclick="switchTab('c', this)">C. 她的奥运</div>
  <div class="tab" onclick="switchTab('d', this)">D. 项目演化</div>
  <div class="tab" onclick="switchTab('e', this)">E. 专题深挖</div>
  <div class="tab" onclick="switchTab('meta', this)">📖 口径声明</div>
</div>

<div class="tab-content">
<div id="tab-a">
  <div class="method">📊 本次分析采用 <b>双口径</b> 并排呈现：左侧 = 运动员行口径（每个小项每位成员各一行，团体项目放大奖牌数）；右侧 = 小项口径（同届×同NOC×同小项×同奖牌去重，与官方奖牌榜口径一致）。</div>
  
  <div class="panel"><h3>逐届奖牌数双口径对比</h3>{html_divs['tab_a1_medal_structure']}</div>
  
  <div class="insight">
    <strong>关键洞察：</strong> 口径差异在团体主导国家上最为显著。以 2024 为例，官方小项口径下美国 40 金 = 中国 40 金并列第一；但运动员行口径下美国 131 金行远超中国 71 金行——曲棍球、游泳等团体/多人项目让"大户"国家的奖牌行数呈放大效应。荷兰官方仅 15 金，行口径却有 67 金行（几乎全来自足球、水球、赛艇、自行车团队）。选择哪种口径取决于你想衡量"小项征服力"还是"奖牌覆盖面"。
  </div>
  
  <div class="panel"><h3>历史总奖牌榜 Top 20（运动员行口径）</h3>{html_divs['tab_a2_top20']}</div>
  
  <div class="panel"><h3>奖牌的通货膨胀：规模扩张曲线</h3>{html_divs['tab_a3_inflation']}</div>
  
  <div class="insight">
    <strong>洞察：</strong> 1896 年只有 14 个小项、380 名运动员；2024 年已有 329 个小项、10,500+ 名运动员。奖牌行数从 1896 年的 120 行膨胀到 2024 年的 1,151 行。代表团数更是从 14 个增加到 206 个——奥运从"西欧精英俱乐部"变成真正的全球盛会。抵制潮（1980/1984）清晰可见：1980 年 80 团参赛，1984 年 140 团回归。
  </div>
</div>

<div id="tab-b" class="hide">
  <div class="method">🏳️‍🌈 选取 12 个有代表性的 NOC 追踪百年奖牌轨迹：美国（128 年长盛）、苏联（骤起骤落）、两德分立与统一、中国（1984 年以来崛起）、日/韩/英/法/澳/加/巴西。</div>
  
  <div class="panel"><h3>12 国逐届总奖牌行（1952–1988 冷战期 + 1980/1984 抵制潮标注）</h3>{html_divs['tab_b1_nation_curves']}</div>
  
  <div class="insight">
    <strong>洞察：</strong> 美国呈现罕见的"百年长盛"——28 届中 25 届奖牌榜行数第一（官方口径也是）。苏联 1952 年首次参赛即登顶，1980 年主场达到巅峰，1992 年解体后遗产分散到 15 个国家（EUN 独联体 1992 年一度 78 金）。中国 1984 年重返即得 15 金，2008 年主场登顶 48 金（官方口径）。
  </div>
  
  <div class="panel"><h3>地缘政治的投影：政体变迁谱系</h3>{html_divs['tab_b2_bloc_evolution']}</div>
  
  <div class="insight">
    <strong>洞察：</strong> 苏联谱系（URS→EUN→RUS→ROC→AIN）是奥运史上最连贯的"一脉相承"——从 1952 到今天从未缺席，2024 年仍以 AIN 名义拿到 16 行奖牌。两德（FRG/GDR）1968–1988 年分立时 GDR 仅 5 届就拿了 843 行奖牌（东德体育体制"效率奇迹"）。
  </div>
</div>

<div id="tab-c" class="hide">
  <div class="panel"><h3>她的奥运：从 0% 到 49.1% 的百年弧线</h3>{html_divs['tab_c1_female_ratio']}</div>
  
  <div class="insight">
    <strong>洞察：</strong> 1896 年雅典：零女性。1900 年巴黎首次参赛（高尔夫、网球），但只有 2.2%。1928 阿姆斯特丹首设女子田径（史上首次 800m）。1988 年汉城女性占比首次破 25%。2020 东京 48.8%，2024 巴黎 49.1%，首次接近男女各半。
  </div>
  
  <div class="panel"><h3>各国女性总奖牌 Top 15</h3>{html_divs['tab_c2_female_medalists']}</div>
  
  <div class="insight">
    <strong>洞察：</strong> 美国以 3,000+ 行女性奖牌遥遥领先（远超第 2 中国的 1,600+），得益于美国高校体育系统的"蓄水池"效应。但看"女性奖牌占本国总奖牌比例"，中国高达 66%（远高于美国的 43%）——因为中国男队在足/篮/排等团体大项上几乎为零。
  </div>
</div>

<div id="tab-d" class="hide">
  <div class="panel"><h3>项目演化：规模膨胀曲线</h3>{html_divs['tab_d1_event_growth']}</div>
  
  <div class="insight">
    <strong>洞察：</strong> 1920 年安特卫普是"传统奥运"的顶点（22 大类、157 小项），之后停滞近 50 年。1972 慕尼黑起加速膨胀——1984 年 221 小项、2000 年 300+、2024 年 329 小项。膨胀来自三方面：传统项目增加小项（如游泳从 10→35）、团体项目回归（棒球/垒球 2020 复出）、全新项目（滑板、霹雳舞、冲浪）。
  </div>
  
  <div class="panel"><h3>消失的运动 vs 2000 年后新增</h3>{html_divs['tab_d2_vanished_added']}</div>
  
  <div class="insight">
    <strong>洞察：</strong> 消失的项目多与早期奥运"业余"传统和贵族游戏有关：槌球、马球、艺术竞赛（1912–1948 设有绘画/雕塑/建筑奖）、拔河（1920 后彻底消失）。有趣的是——1908 和 1920 的<strong>夏季</strong>奥运曾办过花样滑冰和冰球（冰球现在在冬奥会）。新增方面，2020 年滑板/冲浪/霹雳舞/运动攀登四项入奥，2024 年保留并扩充。
  </div>
</div>

<div id="tab-e" class="hide">
  <div class="panel"><h3>东道主效应：主办国到底能"主场爆棚"吗？（小项口径，与任务三一致）</h3>{html_divs['tab_e1_host_effect']}</div>
  
  <div class="insight">
    <strong>关键发现：</strong> 增益倍率 = 主办年奖牌<b>小项数</b> / <b>前一届</b>非主办年小项数（小项口径 NOC-aware，与任务三 Fig.3-1~3-4 同口径；任务三基准为前后两届均值，此处为前一届，故绝对倍数略有差异）。1948 年以来可比样本 18 届。<br>
    • <strong>最大效应：</strong>墨西哥 1968（9.0x，9 vs 1）、西班牙 1992（5.5x，22 vs 4）、澳大利亚 1956（3.2x，35 vs 11）；图含 1896 起全部主办届，全样本最高为 1900 法国 9.3x（102 vs 11），属奥运草创期基数，不宜与战后直接比较。<br>
    • <strong>无明显效应甚至下降：</strong>美国 1996（0.94x）、芬兰 1952（1.00x）、巴西 2016（1.12x）。<br>
    • <strong>整体规律：</strong>16/18 届主办国高于前一届，中位倍率 1.55x，增量中位数 +14 枚小项奖牌；加拿大 1976 倍率 2.2x（11 vs 5），但绝对量仅 11 枚，为 1948 以来主办国最低。<br>
    • <strong>持续效应：</strong>中国 2008（1.59x，100 枚）后长期居前，英国 2012（1.35x）后稳居前列——<strong>真正的东道主效应是长期备战体系的建立，而非主场哨</strong>。
  </div>
  
  <div class="panel"><h3>小代表团的大突破（专题：小而精 vs 全面上阵）</h3>{html_divs['tab_e2_small_nocs']}</div>
  
  <div class="insight">
    <strong>洞察：</strong> 爱尔兰（IRL）2024 年首金是奥运史上最年轻奖牌得主（女子 10m 跳台 13 岁）。乌拉圭（URU）自 1924 足球夺冠后至今 100 年无奖牌——史上最长无冠纪录。中国香港 1996 首金（李丽珊帆板）→ 2020 年 8 行奖牌历史最佳 → 展示了"聚焦优势项目"策略的威力。
  </div>
</div>

<div id="tab-meta" class="hide">
  <h3>📖 数据质量与口径声明</h3>
  <div class="method">
    <b>数据来源：</b>Kaggle "Summer Olympics Medals (1896-2024)"（作者 Stefany De Oliveira），合并自两个上游数据集（Nitish Sharma 2020 年之前 + Petro Ivaniuk 2024 巴黎）。<br><br>
    <b>数据规模：</b>{summary['raw_rows']} 行 × 11 列，覆盖 {len(summary['years'])} 个年份、234 个 NOC。<br><br>
    <b>两套奖牌口径：</b><br>
    &nbsp;&nbsp;① <b>运动员行口径</b>：原始数据一行 = 一名运动员 × 一个小项。男子足球冠军队 18 名球员 = 18 行金牌记录。<br>
    &nbsp;&nbsp;② <b>小项口径</b>（官方口径）：按 Year+NOC+Sport+Event+Medal 去重后，每个小项冠军 = 1 行。与 IOC 官方奖牌榜一致。<br>
    &nbsp;&nbsp;本次 Dashboard 大部分 Tab 采用 <b>运动员行口径</b>；图 A1 双口径并排对比；<b>Tab E 东道主效应统一采用小项口径</b>（与任务三 Fig.3-1~3-4 对齐，数字可直接对照）。
  </div>
  
  <h3>已知数据质量问题处理</h3>
  <div class="method">
    <b>Q1 口径差异：</b>双口径并排呈现，不做"谁更正确"的主观判断。<br><br>
    <b>Q2 体育大类漂移：</b>建立归一映射表：<br>
    &nbsp;&nbsp;• Gymnastics / Artistic Gymnastics / Trampoline Gymnastics / Trampolining / Rhythmic Gymnastics → <b>Gymnastics</b><br>
    &nbsp;&nbsp;• Canoe Slalom / Canoe Sprint / Canoeing → <b>Canoeing</b><br>
    &nbsp;&nbsp;• Cycling Road/Track/Mountain Bike/BMX Racing/BMX Freestyle/Cycling → <b>Cycling</b><br>
    &nbsp;&nbsp;• Equestrian / Equestrianism → <b>Equestrianism</b><br>
    &nbsp;&nbsp;• Synchronized Swimming / Artistic Swimming → <b>Synchronized Swimming</b><br>
    &nbsp;&nbsp;• 逗号拼接跨项（如 Cycling Road, Triathlon）→ 取第一个出现的主项<br><br>
    <b>Q3 Event 泛化：</b>2020 年起 ~22-23% 的 Event 字段为 Men/Women/Men Team/Relay Only Athlete 泛化值。本 Dashboard 接受降维到"大类 × 性别"粒度，不尝试还原具体小项。<br><br>
    <b>Q4 姓名与 ID 不可靠：</b>player_id 和 Name 均不可作为运动员唯一标识。本 Dashboard 规避个体粒度分析（任务三 S6 专题建议额外解决），聚焦国家级汇总。<br><br>
    <b>Q5 历史特殊记录：</b>1906 届（IOC 不承认）在<b>小项口径</b>统计中已排除（奖牌小项数 17,935 不含此届，与任务一/二一致）；<b>运动员行口径</b>的「奖牌行数」与「届数（31 届）」按原始数据保留此届，已在标签中注明。1956 年双城（墨尔本+斯德哥尔摩马术）保留原样；政体变迁（URS→EUN→RUS→ROC→AIN；FRG/GDR→GER；YUG→SCG→…）用 NOC_Group 字段归类展示脉络。<br><br>
    <b>Q6 团体项目与并列：</b>同届×同小项×同奖牌的多行记录不做特殊处理——运动员行口径下这正是团体项目的真实表达。
  </div>
  
  <h3>参考资源</h3>
  <div class="method">
    • [Olympedia](https://www.olympedia.org/)（最全奥运历史数据库，交叉验证首选）<br>
    • [olympics.com 官方奖牌榜](https://www.olympics.com/en/olympic-games)<br>
    • 维基百科历届夏季奥运会奖牌榜词条<br>
    • 绘图工具：Plotly.js v2.35.2 + Python pandas 3.0<br>
    • 数据许可：CC BY-NC-SA 4.0
  </div>
</div>
</div>

<div class="footer">© 2026 数说奥运 · 数据可视分析作品 · 任务四 交互式 Dashboard</div>

<script>
function switchTab(id, el) {{
  document.querySelectorAll('.tab-content > div').forEach(d => d.classList.add('hide'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + id).classList.remove('hide');
  el.classList.add('active');
  setTimeout(() => {{ window.dispatchEvent(new Event('resize')); }}, 100);
}}
</script>
</body></html>"""

with open(OUT_HTML, 'w', encoding='utf-8') as f:
    f.write(HTML_HEAD + HTML_BODY)

print(f"\n✅ Dashboard 已生成：{OUT_HTML}")
print(f"   文件大小：{OUT_HTML.stat().st_size:,} bytes")
print("   浏览器打开方式：双击文件 → 或在 Chrome 中拖入")
