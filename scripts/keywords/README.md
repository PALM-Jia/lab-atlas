# 关键词运行工具

采用的词表、输入和结果在 `data/keywords`；普通构建不执行这里的 API 工具。

`run-deepseek.py` 逐篇请求、重试和续跑；`validate.py` 核对冻结文件、结构、原文证据和逐篇覆盖；`assemble-reviewed.py` 从运行结果生成候选合并文件。三者均支持 `--root` 指定独立准备并冻结的运行目录，默认是本机保留的 `work/keyword-full`。API 密钥从环境变量取得。

运行目录须包含词表、规范、输入批次、输出结构和冻结清单；历史试验准备器已归档，不能当作当前数据源。当前采用结果已关闭，不重新发起查询或复核。

机械校验的合成测试：`python -m unittest discover -s scripts/keywords/tests`。测试读取正式词表和结构规范，不依赖历史运行文件。
