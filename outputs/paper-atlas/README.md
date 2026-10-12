# Lab Atlas 静态发布目录

这里是可直接从 file:// 打开的静态网站发布目录。它只放页面、浏览器脚本和页面需要的事实投影；采集脚本、缓存、模型和审计过程放在仓库根目录的 work/。

## 页面

- index.html：论文与作者网络、时间脉络。
- retrieval.html：论文身份、详情和来源证据汇总。
- workflow.html：从主页清单到特征与画像的处理流程。

workflow-map.html 和 keyword-missing.html 只作为旧链接的兼容入口。旧的论文索引、采集报告和探针页面已移到 work/archive/paper-atlas-legacy-2026-10-13/，不再作为发布页面维护。

## 事实输入与投影

事实输入由 work/atlas-inputs/workflow-contract.json 定义，当前固定为：

- data.json：节点、边及上游论文快照。
- retrieval-data.json：论文来源观察值、采用值和检索状态。
- paper-keywords.json：受控关键词和标注状态。
- paper-fields.json：研究领域投影。
- network-evidence.js：网络关系证据。

同名 .js 文件是浏览器加载投影，不作为重新统计事实的来源。relations-full.json 仍保留为网络关系的历史完整快照；它不被三个主页面直接加载。

## 检查

在仓库根目录运行 python work/build_atlas.py，会进行只读校验：固定输入文件、论文 ID 集合、关键词词表、研究领域、流程协议、页面依赖和流程页投影必须全部通过。需要显式更新本地生成投影时才使用 python work/build_atlas.py --refresh。

当前校验规模为 1,673 个论文节点，其中 144 个实验室论文节点和 1,529 个外部邻域节点；页面不在浏览器端发起数据库请求。
