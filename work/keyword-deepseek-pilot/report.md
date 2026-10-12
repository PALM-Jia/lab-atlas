DeepSeek V4.1 Flash对原10篇独立请求，API实际返回模型名均为deepseek-flash；thinking=enabled、reasoning_effort=high，初轮max_tokens=8192、并发10。旧Sol/Luna各有2×10份独立结果。

最终10/10通过结构和逐字连续原文引文检查。主比较表统一采用旧Astra final固定必选＋可选参照：精确率＝可接受已选/全部已选；召回率＝覆盖必选/必选机会（micro）。可选遗漏不算漏；结构有效不等于语义正确。

| 范围 | 模型/重复 | 有效/请求 | 精确率 | 召回率 | FP | FN |
|---|---|---:|---:|---:|---:|---:|
| 10篇 | deepseek-flash / 重复1 | 10/10 | 93.3% (14/15) | 92.3% (12/13) | 1 | 1 |
| 10篇 | gpt-6-luna / 两次汇总 | 20/20 | 95.8% (23/24) | 84.6% (22/26) | 1 | 4 |
| 10篇 | gpt-6-luna / 重复1 | 10/10 | 92.3% (12/13) | 84.6% (11/13) | 1 | 2 |
| 10篇 | gpt-6-luna / 重复2 | 10/10 | 100.0% (11/11) | 84.6% (11/13) | 0 | 2 |
| 10篇 | gpt-6.1-sol / 两次汇总 | 20/20 | 100.0% (25/25) | 96.2% (25/26) | 0 | 1 |
| 10篇 | gpt-6.1-sol / 重复1 | 10/10 | 100.0% (12/12) | 92.3% (12/13) | 0 | 1 |
| 10篇 | gpt-6.1-sol / 重复2 | 10/10 | 100.0% (13/13) | 100.0% (13/13) | 0 | 0 |

逐篇所选标签及相对固定参照差异（①②为旧模型重复；差异只列机械FP/FN）：

| 样本/标题                                                                                                     | DeepSeek            | Sol①；②                          | Luna①；②                              | 差异                                                               |
| --------------------------------------------------------------------------------------------------------- | ------------------- | ------------------------------- | ------------------------------------ | ---------------------------------------------------------------- |
| S01 Multilabel Ranking with Inconsistent Rankers                                                          | 标签相关性建模、多标记学习、弱监督学习 | ①弱监督学习；②标签相关性建模、弱监督学习           | ①多标记学习、弱监督学习；②弱监督学习                  | DeepSeek：FP/FN均为0；Sol1：漏选标签相关性建模；Luna1：漏选标签相关性建模；Luna2：漏选标签相关性建模 |
| S02 Discriminative Low-Rank Representation for HSI Clustering                                             | 高光谱图像、低秩建模          | ①高光谱图像、低秩建模；②高光谱图像、低秩建模         | ①高光谱图像、低秩建模；②高光谱图像、低秩建模              | DeepSeek：FP/FN均为0                                                |
| S03 Ambiguously Labeled Learning Using Dictionaries                                                       | 偏标记学习               | ①偏标记学习、弱监督学习；②偏标记学习、弱监督学习       | ①偏标记学习、弱监督学习；②偏标记学习、弱监督学习            | DeepSeek：漏选弱监督学习                                                 |
| S04 ML-KNN: A lazy learning approach to multi-label learning                                              | 多标记学习               | ①多标记学习；②多标记学习                   | ①多标记学习；②多标记学习                        | DeepSeek：FP/FN均为0                                                |
| S05 Nonnegative Spectral Clustering with Discriminative Regularization                                    | 空集                  | ①空集；②空集                         | ①空集；②空集                              | DeepSeek：FP/FN均为0                                                |
| S06 Nonnegative Matrix Factorization with Mixed Hypergraph Regularization for Community Detection         | 图与流形正则化、非负矩阵分解      | ①图与流形正则化、非负矩阵分解；②图与流形正则化、非负矩阵分解 | ①图与流形正则化、低秩建模、非负矩阵分解；②图与流形正则化、非负矩阵分解 | DeepSeek：FP/FN均为0；Luna1：多选低秩建模                                   |
| S07 Ensemble Clustering via Co-Association Matrix Self-Enhancement                                        | 集成聚类、图结构学习          | ①集成聚类、图结构学习；②集成聚类、图结构学习         | ①集成聚类；②集成聚类                          | DeepSeek：FP/FN均为0；Luna1：漏选图结构学习；Luna2：漏选图结构学习                    |
| S08 Applying Exponential Family Distribution to Generalized Extreme Learning Machine                      | 空集                  | ①空集；②空集                         | ①空集；②空集                              | DeepSeek：FP/FN均为0                                                |
| S09 SAGENet: Sub-cluster Aggregation Guided Enhancement for Imbalanced Attributed Graph Clustering        | 类别不平衡学习、深度聚类、图神经网络  | ①类别不平衡学习、深度聚类；②类别不平衡学习、深度聚类     | ①类别不平衡学习、深度聚类；②类别不平衡学习、深度聚类          | DeepSeek：FP/FN均为0                                                |
| S10 Distributed Optimization and Statistical Learning via the Alternating Direction Method of Multipliers | 稀疏表示                | ①空集；②空集                         | ①空集；②空集                              | DeepSeek：多选稀疏表示                                                  |

新增gpt-6.1-sol独立审阅（仅DeepSeek，单独参照，不替换主表旧Astra）：FP 0、FN 1（S03弱监督）；证据/理由问题3处：S01标签相关性引用既有方法的背景假设，S09图神经网络引用GCN背景，S09深度聚类理由额外推断本文使用GCN。15处quote均逐字连续合法。S03弃权误用未声明的父子关系，与漏标同根，不重复计数。

审阅分歧须保留：旧Astra把S10稀疏表示视为多选，新Sol初参照也为空，final因basis pursuit明确表示稀疏基系数，且本文实质综述ADMM应用，将其新增为必选。该修订与证据已留存，未改旧参照；因此主表仍报S10 FP，而新增审阅不报此FP。其他边界：S01弱监督由旧必选变新可选，S02图像分割、S06低秩、S09对比学习在新参照为可选；S03伪标签自训练由旧可选变新不接受。这些是两位审阅者的定义/文本边界差异，不按对DeepSeek有利的参照筛选分数。

初轮7/10成功生成标注，S01/S02/S03在8192预算下reasoning耗尽上限且无标注，作为技术失败保留，不能记成空标签或模型错标。仅对这3篇提高预算到32768技术重试，thinking/high不变，已完成7篇不重跑；总API尝试13次，每篇仅1份成功标注。

DeepSeek全部实际尝试usage（含技术失败）：prompt 110487、completion 74502（其中reasoning 72704）、total 184989 tokens。技术失败消耗total 50070 tokens。初轮并发整批墙钟54.778秒；全部尝试每请求3.095–66.157秒，均值35.372秒。最终单篇预算不同，不能作为统一耗时benchmark；无旧模型同口径时长，不作速度或成本比较。DeepSeek无第二次成功重复，不报重复一致性。

本10篇按同一旧Astra口径，DeepSeek漏标少于Luna（1/13与4/26必选机会），多选稀疏表示存在审阅分歧，另有3处证据/理由问题需复核。不能由这10篇外推完整49词的准确率。原始标签、旧参照与生产文件未修改。
