# Andy的国家队资金看板 (ETF Fund Flow Dashboard)

全功能重点 ETF 资金流向及国家队信号观测看板，支持盘中分钟分时走势、20大重点ETF放量案例对照、单日表现排名、申赎放量信号以及近一个月各宽基ETF日度净流入热力矩阵。

---

## 核心特性

- **零依赖与开箱即用**：全功能页面完全自包含，双击即可直接在浏览器打开浏览全部图表。
- **官方行情自主直连**：浏览器原生跨域直连腾讯财经与官方金融数据源，盘中自动获取最新现价与成交额。
- **历史走势对比**：支持选择 2026 年以来任意历史交易日，叠加累计成交额曲线进行直观比对。
- **GitHub Pages 即刻上线**：仓库代码可直接在 GitHub Settings -> Pages 中开启，免费生成全球可访问的在线看板。

---

## 项目结构

```
├── index.html          # 主入口文件（自包含所有图表、离线数据与实时直连引擎）
├── standalone.html     # 本地离线快照版（仅基准数据，无实时）
├── data.js             # 历史基准数据与 20 大 ETF 案例走势
├── cumdays.json        # 2026 全年 200+ 交易日分钟累计走势数据集
├── app.js              # 核心计算与 ECharts 图表渲染引擎（standalone 版使用）
├── echarts.min.js      # ECharts 6.0 离线运行时
├── style.css           # 响应式布局与资金流红绿配色样式表
└── server.py           # 本地可选 Python 运行服务（仅监听 127.0.0.1）
```

### 数据更新机制

`data.js` 与 `cumdays.json` 由本地工具链（`tools/fetch_netflow.py`、`tools/build_cum.py` 等，未随本仓库公开）每个交易日重建后提交。决策卡的 20 日均额基准与日内同时点分布均从这两个文件的真源计算，不使用硬编码数值。

---

## 运行与部署

### 1. 本地免环境直接运行
直接双击打开 `index.html`（或 `etf_board_full.html`）即可在浏览器中查看完整看板，支持盘中自动实时刷新。

### 2. GitHub Pages 在线访问
在 GitHub 仓库中，进入 `Settings` -> `Pages` -> `Build and deployment`，选择 `Branch: main` / `root` 保存，即可获得专属的在线访问链接。
