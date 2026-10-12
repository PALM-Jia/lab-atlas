本次补齐128份摘要，当前1464/1673篇有摘要（实验室126/144，外部1338/1529）。关键词pilot抽取实验室与外部各5篇，共8篇有摘要、2篇仅标题；固定49词与共同指令，以40次fresh独立上下文标注。实际模型ID为gpt-6.1-sol（Sol）与gpt-6-luna（Luna），两个队列并行进行，每模型每篇重复两次。两次失败CLI探测不计入正式结果。

按Astra匿名盲审的final必选集与可选集计算micro指标：精确率＝可接受已选/全部已选；召回率＝已覆盖必选/全部必选机会。可选项不选不算漏标。下表的明确错标与漏标按关键词机会计数；无明确问题按结果份数计数。集合推导的40份FP/FN与逐份盲审结论完全一致；同一多选及其证据问题只计一次。

| 实际模型 | 精确率 | 召回率 | 明确错标 | 漏标 | 无明确问题 | 两次集合一致 | 平均集合重合率（Jaccard） |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-6-luna | 95.8% (23/24) | 84.6% (22/26) | 1 | 4 | 15/20 | 8/10 | 91.7% |
| gpt-6.1-sol | 100.0% (25/25) | 96.2% (25/26) | 0 | 1 | 19/20 | 9/10 | 95.0% |

逐篇所选中文标签（①②为同模型的两次独立输出；“两次”表示集合相同）：

| 样本与标题 | Sol | Luna | 明确问题 |
|---|---|---|---|
| S01 · 外部 · 标题＋摘要<br>Multilabel Ranking with Inconsistent Rankers | ①弱监督学习；②标签相关性建模、弱监督学习 | ①多标记学习、弱监督学习；②弱监督学习 | Sol1：漏选标签相关性建模；Luna1：漏选标签相关性建模；Luna2：漏选标签相关性建模 |
| S02 · 实验室 · 标题＋摘要<br>Discriminative Low-Rank Representation for HSI Clustering | 两次：高光谱图像、低秩建模 | 两次：高光谱图像、低秩建模 | 无明确问题 |
| S03 · 外部 · 标题＋摘要<br>Ambiguously Labeled Learning Using Dictionaries | 两次：偏标记学习、弱监督学习 | 两次：偏标记学习、弱监督学习 | 无明确问题 |
| S04 · 外部 · 仅标题<br>ML-KNN: A lazy learning approach to multi-label learning | 两次：多标记学习 | 两次：多标记学习 | 无明确问题 |
| S05 · 外部 · 标题＋摘要<br>Nonnegative Spectral Clustering with Discriminative Regularization | 两次：空集 | 两次：空集 | 无明确问题 |
| S06 · 实验室 · 仅标题<br>Nonnegative Matrix Factorization with Mixed Hypergraph Regularization for Community Detection | 两次：图与流形正则化、非负矩阵分解 | ①图与流形正则化、低秩建模、非负矩阵分解；②图与流形正则化、非负矩阵分解 | Luna1：多选低秩建模 |
| S07 · 实验室 · 标题＋摘要<br>Ensemble Clustering via Co-Association Matrix Self-Enhancement | 两次：集成聚类、图结构学习 | 两次：集成聚类 | Luna1：漏选图结构学习；Luna2：漏选图结构学习 |
| S08 · 实验室 · 标题＋摘要<br>Applying Exponential Family Distribution to Generalized Extreme Learning Machine | 两次：空集 | 两次：空集 | 无明确问题 |
| S09 · 实验室 · 标题＋摘要<br>SAGENet: Sub-cluster Aggregation Guided Enhancement for Imbalanced Attributed Graph Clustering | 两次：类别不平衡学习、深度聚类 | 两次：类别不平衡学习、深度聚类 | 无明确问题 |
| S10 · 外部 · 标题＋摘要<br>Distributed Optimization and Statistical Learning via the Alternating Direction Method of Multipliers | 两次：空集 | 两次：空集 | 无明确问题 |

关键判断：S01的共同偏好分布实质建模标签间排序，不能只依词面漏掉标签相关性建模；S07增强样本共关联矩阵实质修正亲和结构，需识别图结构学习。S06仅标题的非负矩阵分解不自动支持低秩建模，Luna一次因此多选。S01多标记排序与偏好分布、S03迭代置信度训练、S09图神经网络与伪标签机制存在定义或文本边界，Astra按可选项处理，未强行计错。

参考集修订：S01在final新增弱监督学习为必选。原文以主观不一致的多人排序替代单一客观标签排序，且方法专门处理这一条件，符合不精确监督的定义；初审把较窄的噪声标签要求误用于弱监督。修订依据原文与词表，未依据匿名结果投票。reference-initial.json及其原SHA256保留，final记录完整修订；其余必选/可选未变。

空标签不是自动失败：词表可能没有该研究方向。S05的谱聚类、S08的ELM和S10的ADMM均被本次盲审接受为空集，不能因此视作模型未理解论文。40份结构与连续原文引文校验通过，也不等于全部语义标签正确。

这些数字只描述本10篇与Astra盲审判断，不构成全量准确率。样本没有大模型类论文，无法据此验证完整49词。建议先澄清多标记排序/偏好分布、迭代训练信号等词表边界，并补强“标签间排序”“亲和矩阵修正”的关键漏标示例；仅有NMF名称时继续要求明确低秩证据。随后增加大模型类及边界样本复核，再决定是否全量标注；本报告不自动启动全量，也不作成本或速度结论。

复现：运行quality-statistics.py；它先核对冻结输入与40原结果SHA256、initial参考指纹，再逐份对照Astra结论，写metrics.json与本报告。原始标注、production及参考文件不修改。
