# 🏅 数说奥运 · 1896–2024 · 百年圣火可视分析 Dashboard

> 数据可视分析挑战赛 · 任务四（加分项）· 交互式 Dashboard

## 🎯 在线访问

**公网 URL**：https://37lpfxarig0m5duj2es.traesite.cn

## 🖥️ 本地运行

### 方式一：直接打开 HTML（零依赖，推荐）

```bash
# Windows: 双击文件 或 在 PowerShell 中
Start-Process olympics_dashboard.html

# macOS
open olympics_dashboard.html

# Linux
xdg-open olympics_dashboard.html
```

### 方式二：本地 HTTP Server（多人分享）

```bash
# Python 3
python -m http.server 8080
# 然后访问 http://localhost:8080/olympics_dashboard.html

# Node.js (需要全局安装 http-server)
npx http-server -p 8080
```

### 方式三：重新生成（更换数据后）

```bash
# 1. 安装依赖（如果没有）
pip install pandas numpy plotly

# 2. 修改 build_dashboard.py 第 11 行的数据路径
#    df = pd.read_csv(r'你的新数据.csv')

# 3. 运行生成
python build_dashboard.py

# 4. 自动在 workspace 目录生成 olympics_dashboard.html
```

## 📦 交付物清单

| 文件 | 说明 |
|------|------|
| `olympics_dashboard.html` | **主交付物** — 单 HTML，Plotly.js 交互式看板（117KB） |
| `build_dashboard.py` | 数据清洗 + 图表生成 + HTML 打包脚本 |
| `olympics_dataset.csv` | 原始数据（252,565 行 × 11 列，~26MB，CC BY-NC-SA 4.0） |
| `本 README` | 运行说明 |

## 🗂️ Dashboard 内容概览

| Tab | 主题 | 图表 | 深度洞察 |
|-----|------|------|---------|
| **A. 奖牌格局** | 双口径逐届对比、Top20 历史榜、规模膨胀 | 3 | 荷兰官方15金/行口径67金行、1980/1984 抵制潮清晰可见 |
| **B. 国家兴衰** | 12 国逐届奖牌轨迹、政体变迁谱系 | 2 | 美国百年长盛、苏联一脉相承到 AIN、两德 GDR 效率奇迹 |
| **C. 她的奥运** | 0%→49.1% 弧线、女性奖牌占比、Top15 | 2 | 中国女性奖牌占本国 66%（男队团体几乎为零） |
| **D. 项目演化** | 小项增长曲线、消失 vs 新增 | 2 | 艺术竞赛曾有绘画/雕塑奖、冰球曾是夏季项目 |
| **E. 专题深挖** | 东道主增益倍率、小代表团气泡图 | 2 | 中国 2008 年增益 4.9x 最大、加拿大 1976 尴尬减半 |
| **📖 口径声明** | 数据来源、Q1–Q6 处理规则 | — | Sport 归一映射表、双口径定义 |

## ⚙️ 技术栈

- **数据处理**：Python 3.12 + pandas 3.0 + numpy 2.3
- **可视化**：Plotly.js v2.35.2（CDN 引入，浏览器端渲染）
- **交付形式**：单 HTML 文件（零依赖，离线可运行）
- **部署**：Trae StaticWeb（公网可访问）

## 📝 口径声明

- **奖牌口径**：默认采用**运动员行口径**（原始数据一行 = 一名运动员 × 一个小项）。图 A1 提供双口径并排对比（运动员行 vs 小项去重）。
- **Sport 归一化**：2020 年起拆分的大类（Artistic/Tarampoline → Gymnastics、Canoe Sprint/Slalom → Canoeing、Cycling X5 → Cycling）已统一映射。
- **1906 届**：IOC 不承认但纳入本分析，口径一致。
- **政体变迁**：URS→EUN→RUS→ROC→AIN 归为"苏联谱系"；FRG/GDR→GER。

## 🔗 参考资源

- [Olympedia](https://www.olympedia.org/) — 最全奥运历史数据库
- [olympics.com 官方奖牌榜](https://www.olympics.com/en/olympic-games)
- Kaggle: [Summer Olympics Medals (1896-2024)](https://www.kaggle.com/datasets/stefanydeoliveira/summer-olympics-medals-1896-2024)
- 数据许可：CC BY-NC-SA 4.0
- AI 辅助：TRAE AI（代码生成、数据清洗逻辑、图表设计）

---

© 2026 数说奥运 · 数据可视分析作品 · 任务四 加分项交付
