# Lab Atlas

从实验室论文清单收集、核对信息，在静态网页展示论文、作者与外部文献的关联。页面可以直接打开，不在浏览器端调用数据库接口。

## 目录与唯一维护入口

| 目录 | 维护什么 |
| --- | --- |
| `outputs/paper-atlas/` | 网络、检索汇总、流程介绍三个页面，以及浏览器代码和生成的数据投影；两个旧地址保留跳转 |
| `data/atlas/` | 采用的论文、关系、字段证据、关键词、领域和生成记录 |
| `data/people/` | 去重人员、分类、名册和署名单位证据 |
| `data/keywords/` | 49项词表、实际输入文本、采用标注、排除决定和标注规范 |
| `data/vectors/` | 按模型版本和输入摘要散列定位的向量文件，不含模型权重 |
| `data/sources/` | 原主页、参考与被引名单、已保存书目信息、摘要提取来源和领域判定依据 |
| `data/workflow/` | 阶段协议、当前图表结构和补充解释；阶段标题从协议生成 |
| data/maintenance/ | 当前两源验收记录与维护说明 |
| `data/two-source/` | 两源流程协议、冻结结果与旧版对照；网络与检索页面由其导出采用数据 |
| `_legacy/v1.0/` | 原多源数据的校验归档，原数据仍由 v1.0 标签保留 |
| `scripts/` | 构建、特征处理、候选采集、关键词执行和检查工具 |
| `work/` | 缓存、模型环境、运行目录、候选结果和历史归档；不提交 Git |

采用结果只在 `data/` 修改。浏览器 `.js` 数据由构建导出，不手工改；前端逻辑和样式仍在发布目录维护。`data/atlas/data.json` 的 `edges` 是完整关系来源，已删除重复的 `relations-full.json`。

## 网页发布

GitHub Pages 使用 `.github/workflows/pages.yml`，将离线构建目录的内容直接发布到站点根路径，不发布整个仓库。

- 可视化：https://palm-jia.github.io/lab-atlas/
- 检索汇总：https://palm-jia.github.io/lab-atlas/retrieval.html
- 处理流程：https://palm-jia.github.io/lab-atlas/workflow.html

`outputs/paper-atlas/` 是源码维护目录，不是公开网址的一部分。原有深层 HTML 地址在发布时生成兼容跳转，保留查询参数和锚点。后续推送到 `master` 自动重新构建和发布。Pages 设置的 Source 应为 GitHub Actions。

本地预览发布结构：

```powershell
python -B scripts/build/build_atlas.py --output work/pages
python -B scripts/build/prepare_pages.py --output work/pages
python -m http.server 8000 --directory work/pages
```

## 日常使用

在仓库根目录执行：

```powershell
python -B scripts/collection/two_source/export_atlas.py --promote
python scripts/build/build_atlas.py
python scripts/build/build_atlas.py --check
```

第一条从冻结的两源快照生成采用数据；第二条从采用结果生成页面数据；第三条只读检查页面依赖、投影一致性和论文集合。导出和构建都不请求数据库、不调用 AI、不重新计算向量。

时间脉络使用正射投影，年份为竖直轴。论文从发表起在后续年度以粗枝线延续；选中节点后才显示跨论文关联，引用与共同作者用细实线，相似度用细虚线。选中论文时激活其全部可见年度节点，关联从最早的可见年度节点向上绘制，每条关系只出现一次；引用仅连接引用它的施引文献。点击节点或连线时，详情对应实际端点年度。年度节点大小按截至该年的累计被引数平方根映射，放大低被引与高被引的尺寸差异。实验室论文使用已采用的被引名单；外部文献仅使用已采集邻域中的引用。缺失名单保留为未知，不使用当前总被引数倒推历史。`data/atlas/citation-history.json` 是这些证据的年度派生汇总，普通离线构建自动更新，浏览器通过 `citation-history.js` 读取。

横向拖动旋转，纵向拖动调整俯仰，滚轮切换最上方年份。可见年数由底盘的投影厚度、俯仰角、缩放和画布可用高度共同确定；层间距自适应调整，避免年度切片过度重叠，没有固定年数上限。范围外的年份和连接不绘制、不参与点击；滚轮保持缩放不变。

滚动边界按整个可见年份窗口计算：底部到达最早年份或顶部到达最晚年份时保持原位。全部年份都能显示时停止滚动；触界后的滚轮位移清零，反向滚动立即响应。

需要重新应用已采用的关键词和领域映射时，使用 `--refresh`。它核对标注原文、更新派生字段后构建；不会重新标注。需要单独重建一个发布目录时，使用 `--output work/rebuild-preview`，随后可直接打开该目录的页面。

## 收集与采用的边界

两源重采集入口为 `scripts/collection/two_source/`，协议在 `data/two-source/protocol.json`。只用主页原始快照、用户实验室名单和 OpenAlex；完整说明见该入口 README。流程页的阶段、图表解释和正文从这份协议及两源冻结快照生成。`scripts/collection/two_source/export_atlas.py` 将冻结快照导出到 `data/atlas/` 与 `data/people/`，再由普通构建投影到网络和检索页面。`data/workflow/contract.json` 是只读生成结果，`map.json` 与 `diagram.json` 只维护图形布局。

统一执行入口：`python -B scripts/collection/two_source/run.py`。默认离线，串联采集、人员对应、向量、关键词复用、画像、校验、独立冻结和旧版对照。输入或代码变化时重跑对应缓存单元；失败停止冻结，未决任务单列，不调用AI模型。`--online`只允许补查本轮缓存缺少的OpenAlex请求，不替换网络页面数据。

五个阶段的执行边界与读者说明统一维护在 `data/two-source/protocol.json`。普通构建只导出已采用的本地数据和流程说明，不重新查询数据库、调用AI或生成向量。更新冻结快照后，先运行两源导出，再运行普通构建，页面才会切换到新的采用数据。

`scripts/collection/build_retrieval_dashboard.cjs` 及 `sync-retrieval-candidate.py` 从显式来源重新整理检索候选，写入 `work/retrieval-candidate/`。候选和现有采用结果分别保留，运行候选生成不会覆盖采用的版本、人员、来源观察值或当前网页。

`scripts/collection/abstracts/` 的摘要工具只在运行目录保存请求和候选；外部查询需要显式执行。`scripts/features/generate_local_semantic.py` 才会更新向量和语义关系，需要已安装的模型环境，普通构建不调用它。关键词 API 执行、机械校验和合并工具位于 `scripts/keywords/`，接受独立准备并冻结的运行目录，当前已关闭的标注不再复核。

## 检查与历史

`scripts/checks/README.md` 列出真实网络规则、作者权重、署名过滤、模糊搜索、向量溯源、流程路径和浏览器检查。浏览器运行检查使用已有 Playwright 与 Chromium，不安装新前端依赖。

整理前状态保存在提交 `d2fbd46`（前序检查点 `f9bcab9`）。旧脚本和页面不参与当前构建；原先提交过的文件可从 Git 历史恢复，旧版采用数据保存在 `_legacy/v1.0/`。当前验收记录位于 `data/two-source/snapshot/` 和 `data/two-source/results/`。查询缓存和模型环境保留在本机 `work/`，不提交 Git。


