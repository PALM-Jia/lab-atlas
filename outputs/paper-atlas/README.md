# 静态发布目录

三个主页面：index.html（网络与时间脉络）、retrieval.html（检索汇总）、workflow.html（处理流程）。workflow-map.html 和 keyword-missing.html 保留旧地址跳转。

页面可直接打开；只依赖本目录的浏览器资源。数据 JS 从仓库 data/ 导出，不在此目录维护事实 JSON、采集脚本、模型或运行报告。

在仓库根目录执行 python scripts/build/build_atlas.py 重建；使用 --check 只读检查。完整维护说明见仓库根目录 README。
