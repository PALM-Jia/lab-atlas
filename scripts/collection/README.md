# 候选采集与整理

外部收集和本地采用是两个操作。这里的工具只输出运行候选，不直接改写采用数据或浏览器投影。

```powershell
node scripts/collection/build_retrieval_dashboard.cjs
python scripts/collection/sync-retrieval-candidate.py
```

这两条仅从 `data/atlas`、`data/people` 和 `data/sources` 整理本地结果，输出 `work/retrieval-candidate`。书目信息来自显式保存的 `data/sources/bibliography.json`，不再扫描请求缓存。同步使用同一套关键词、字段状态和文案处理代码。

`abstracts/api-backfill.py` 按已核对身份补取摘要，默认只查看缓存，`--online` 才访问 OpenAlex/Semantic Scholar；发布页、S2恢复与合并工具在同一目录，结果进入 `work/abstract-backfill`。部分入口会访问外部来源，须按实际补缺任务选择，普通网页构建不会调用。

旧 `pipeline.py` 是早期采集与布局的一体实现，含已退役关系和不完整的语义刷新接线，已归档；不再作为正式入口。这里保留候选整理和摘要工具，未来新增采集按流程协议交接证据，不恢复该旧入口。
