# Lab Atlas 文件边界

这里保存静态 Lab Atlas 的输入边界和校验结果。页面文件仍位于 `outputs/paper-atlas/`，本目录不复制大数据文件。

## 规范文件

- `workflow-contract.json`：五个处理阶段的输入、采用输出、证据和未决状态。它是流程说明的唯一规范来源。
- `validate_atlas_inputs.py`：只读校验器，检查固定输入文件、论文 ID 集合、关键词词表、研究领域和流程协议。
- `export_workflow_guide.py`：把流程协议投影成流程页使用的阶段说明；修改协议后先运行它，再做校验。
- `manifest.json`：最近一次校验的文件哈希、规模和结果。
- `release-manifest.json`：三个主页面及其本地依赖清单。

## 数据边界

`outputs/paper-atlas/data.json`、`retrieval-data.json`、`paper-keywords.json`、`paper-fields.json` 和 `network-evidence.js` 是当前事实输入。对应的 `.js` 文件是浏览器投影，不用于建立事实或统计。

`work/api-cache/`、`work/semantic-vector-cache/`、`work/abstract-backfill/` 等目录是采集缓存或运行产物，不属于静态页面发布输入，也不由只读构建检查扫描。

## 当前整理策略

先冻结边界、记录哈希并验证投影一致，再归档或删除旧页面、重复快照和缓存。任何删除动作都必须先完成页面依赖检查和数据重建验证。
