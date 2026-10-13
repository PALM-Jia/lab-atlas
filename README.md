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
| `scripts/` | 构建、特征处理、候选采集、关键词执行和检查工具 |
| `work/` | 缓存、模型环境、运行目录、候选结果和历史归档；不提交 Git |

采用结果只在 `data/` 修改。浏览器 `.js` 数据由构建导出，不手工改；前端逻辑和样式仍在发布目录维护。`data/atlas/data.json` 的 `edges` 是完整关系来源，已删除重复的 `relations-full.json`。

## 日常使用

在仓库根目录执行：

```powershell
python scripts/build/build_atlas.py
python scripts/build/build_atlas.py --check
```

第一条从本地采用结果生成页面数据；第二条只读检查页面依赖、投影一致性和论文集合。构建不读取查询缓存，不请求数据库，不调用 AI，不重新计算向量。

需要重新应用已采用的关键词和领域映射时，使用 `--refresh`。它核对标注原文、更新派生字段后构建；不会重新标注。需要单独重建一个发布目录时，使用 `--output work/rebuild-preview`，随后可直接打开该目录的页面。

## 收集与采用的边界

五个阶段的语义以 `data/workflow/contract.json` 为准。该协议描述信息如何形成；当前构建读取历史采集、核对后保留的结果，不要求重新走一遍外部查询。

`scripts/collection/build_retrieval_dashboard.cjs` 及 `sync-retrieval-candidate.py` 从显式来源重新整理检索候选，写入 `work/retrieval-candidate/`。候选和现有采用结果分别保留，运行候选生成不会覆盖采用的版本、人员、来源观察值或当前网页。

`scripts/collection/abstracts/` 的摘要工具只在运行目录保存请求和候选；外部查询需要显式执行。`scripts/features/generate_local_semantic.py` 才会更新向量和语义关系，需要已安装的模型环境，普通构建不调用它。关键词 API 执行、机械校验和合并工具位于 `scripts/keywords/`，接受独立准备并冻结的运行目录，当前已关闭的标注不再复核。

## 检查与历史

`scripts/checks/README.md` 列出真实网络规则、作者权重、署名过滤、模糊搜索、向量溯源、流程路径和浏览器检查。浏览器运行检查使用已有 Playwright 与 Chromium，不安装新前端依赖。

整理前状态保存在提交 `d2fbd46`（前序检查点 `f9bcab9`）。旧脚本和页面保留在本机 `work/archive/`，迁移位置见 `data/maintenance/archive-map.json`；原先提交过的文件也可从检查点恢复。查询缓存和模型环境未删除。完整 AI 运行碎片已移出 Git 跟踪，采用结果、逐篇输入、引用原文和排除决定仍在 `data/keywords/`。
