# 两源文献采集

文献事实仅来自实验室主页原始快照、用户确认的实验室名单、OpenAlex。人员名单属于实验室输入；本地模型和受控词表属于派生方法。采集代码不读取旧采用数据、旧查询缓存、旧人员合并结果或旧关键词标注。独立的关键词派生步骤可以按完整输入和证据检查复用旧标注，不导入旧事实。

## 统一入口

```powershell
python -B scripts/collection/two_source/run.py
```

默认离线：执行“采集与特征输入准备 → 人员对应 → 本地向量 → 关键词复用 → 作者画像 → 强制校验 → 独立冻结与旧版对照”。需要查询本轮缓存中没有的OpenAlex响应时加`--online`；已有缓存仍复用，刷新数据库须另建`--run work/two-source/新运行名`。冻结结果通过`export_atlas.py`导出为采用数据，再由普通构建生成网络与检索页面。

采集1–4及特征输入准备目前作为一个缓存执行单元，变化后整体重放；人员、向量、关键词与画像分别按输入和代码指纹复用。输出被改动也会重算。无论是否复用，结束前重新校验来源响应、候选判定、关系、向量和派生结果。`automation-status.json`记录各步骤状态；失败停止冻结，下次可继续，不能将缓存命中称为重新采集。

五阶段的细分输入、输出、验收和异常出口在协议的`execution_steps`。不强行完成的任务集中到`review-queues.json`：论文身份、详情身份漂移、人员署名、关键词。`automation-acceptance.json`同时记录已完成与待处理，存在待处理时标为`validated_with_explicit_pending_tasks`。

人员对应写入`data/two-source/person-mappings.json`，每项包括`person_id/name/group/occurrence_ids/evidence`，可附`aliases`。只作用于显式列举的逐篇署名，不凭姓名或单位扩展到其他论文；名单分类必须一致。无身份锚点、已知同名冲突进入`02-person-review-queue.json`阻塞队列；已有OpenAlex ID或ORCID但同名家族仍有其他组件、或名单分类证据不足的记录进入`02-person-review-warnings.json`，不阻塞该条记录的身份画像。用户明确要求修复时，导出步骤可按论文 occurrence 对齐旧版已采用人员映射，并逐项保存旧版来源证据；其他旧事实不会导入。临时画像不是最终人员名单。

关键词旧标注仅在同论文ID、相同词表、完整标题摘要相同或仅NFKC/空白/大小写差异时复用，每条引文都须在当前文本中找到。文本变化、旧标注未通过、引文无效或新增论文全部进入`05-keyword-pending.jsonl`。成功空标注单独算已完成。模型任务默认不执行。

可用`--keyword-results 路径`导入已保存的固定任务JSONL。每行包含固定prompt要求的字段，以及`vocabulary_sha256/prompt_sha256/model/settings/raw_response/response_sha256`；响应散列以`pipeline.digest`计算，原始响应中的论文ID、输入指纹、词项和引文必须与采用结果相同。重复条目、旧输入、未知词项、无引文或缺模型记录均拒绝。人员审查prompt为`prompts/person-audit.txt`，仅输出建议，不能直接修改对应表。

作者画像以每篇论文的贡献计算：一作1，其他署名0.2；Yuheng Jia一作时第二作者按一作计。成功空标注计入分母，未标注不计入；人员对应或标注未完成时画像标为部分。画像保存全量实验室语料的贡献，页面接入后须按筛选重新聚合。

`data/two-source/protocol.json` 定义五阶段、查询顺序、采用规则、字段状态、AI 输入输出和可复现边界。每次运行复制协议、采集脚本、六份输入并保存散列。结果先写独立运行目录，不覆盖现有网页数据。

## 执行与重放

先运行 `archive.py`，逐文件保存并校验 `_legacy/v1.0/data/`。大体积副本留在本机；原文件也由 v1.0 Git 标签保留。

```powershell
python -B scripts/collection/two_source/archive.py
python -B scripts/collection/two_source/pipeline.py --iteration accepted --broad
python -B scripts/collection/two_source/validate.py work/two-source/current/iterations/accepted
python -B scripts/collection/two_source/pipeline.py --iteration replay --broad --offline
python -B scripts/collection/two_source/replay.py work/two-source/current/iterations/clean
```

在线运行从环境变量 `OPENALEX_API_KEY` 读取凭据，通过请求头发送，不写入 URL、协议、响应记录或报告。没有 key 时只能使用 OpenAlex 公共额度。网络响应保存在本次运行专用的 `responses/`，不从历史混合缓存补缺。

离线重放先校验输入及响应散列，按同一规则重新生成阶段结果。重放新协议不等于重现旧协议：旧输出的 `protocol.json`、`pipeline.py` 和请求依赖清单用于说明其版本；实际运行必须核对版本，不允许替换协议后宣称结果相同。

## 阶段边界

1. 原始 HTML 解析为主页清单。重复展示条目留 occurrence；原始段落、署名、发表信息、链接不被数据库值覆盖。
2. 标识符、标题限定搜索及完整标题搜索产生身份候选，只有身份字段被保留。排版差异可自动归一；实质题名变化必须有主页标识佐证。同作品的正式版优先需要完整署名证据兼容。未确定条目保留主页值。
3. 已确认 ID 重新精确查询详情。摘要、主题、关键词、被引数、引用及被引名单只在此阶段取得。被引查询总数优先，论文主记录计数保留观察值；名单长度不是总被引数。真正身份漂移进入单独 review queue，详情不改写阶段2身份。
4. 每个一层外部 ID 都补查详情；批量遗漏再逐 ID 查询。以数据库标识归一、重新划分内部/外部。完整名单与最多1600个网络节点分开；不递归扩展，不产生外部—外部引用边。

外部网络节点必须连接至少两篇不同实验室论文（`external.graph_min_lab_neighbors=2`）。按完整直接引用／被引名单去重计数，同一对论文的重复记录或相反方向只算一个邻居；在top-K、语义边和页面筛选之前执行。先筛选再按连接数排序应用1600预算，不用单连接论文补满。仅裁剪网络候选与相应特征输入，完整外部详情和两份名单均保留；不叠加年份或被引数门槛。
5. 冻结标题及可用摘要作为新特征输入。向量使用已固定本地SPECTER2权重；关键词用49词表复用或独立标定。旧标注必须通过完整输入和引文检查并记为复用；其余未执行任务为`not_generated`，不能把任务准备称为生成成功。

OpenAlex 标题限定查询与归一方式参考官方检索文档：https://help.openalex.org/api/searching/ 。详情字段定义：https://help.openalex.org/data/works/attributes/ 。返回的数据库关键词/主题不是受控词表标注。

## 人员与 AI

论文署名顺序、OpenAlex作者ID、署名单位置原值分别保存。同名无ID的作者只保留逐篇 occurrence，不跨论文合并。姓名和东南大学单位只能提出实验室名单候选；正式分类需要已确认的名单人员—作者ID对应，不能凭同名加单位确认。

身份AI审查默认关闭。固定任务见 `prompts/identity-audit.txt`：只能读取本轮证据，输出同意、规则需修改或证据不足；不能直接采用身份。真正规则修订后要重新执行对应阶段。

受控关键词是独立派生任务，默认不自动请求模型。固定任务见 `prompts/keywords.txt`：单篇标题、可用摘要、49词定义，输出关键词ID和连续原文证据。执行时必须另存模型、参数、输入、prompt和原始输出指纹；模型别名不保证未来权重不变，因此可复现指保存的响应重放及规则重算，不保证外部模型将来逐字重新生成。旧标注复用规则及结果分别记录，不能默默补缺。

## 验收、冻结、对照

`validate.py` 校验本轮协议/脚本/输入/所用响应，重算候选匹配，检查所有输入有归宿、引用关系完整、外部预算和特征输入指纹。成功加可解释未完成覆盖全部输入，但这个比例不等于正确率；逻辑规则另由合成边界测试和独立代码审计验证。

```powershell
work/semantic-runtime/Scripts/python.exe -B scripts/collection/two_source/features.py work/two-source/current/iterations/accepted
python -B scripts/collection/two_source/freeze.py work/two-source/current/iterations/accepted
python -B scripts/collection/two_source/report.py work/two-source/current/iterations/accepted
```

`freeze.py` 输出独立快照；统一入口先冻结候选，再保留原快照并更新`data/two-source/snapshot/`。`report.py`读取旧事实生成逐字段对比，`derived.py`只读取旧关键词输入、词表与采用标注做限定复用。`export_atlas.py`只读取冻结快照、固定词表和用户人员分类，写入新的采用数据；它不读取旧事实。完成导出后运行普通构建即可更新可视化、检索汇总和时间脉络。
