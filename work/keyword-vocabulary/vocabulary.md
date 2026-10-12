# 实验室关键词词表（第一阶段）

共49词（新版）。来源为144篇当前实验室内部论文：113篇有实质摘要、31篇仅按标题判断（30篇空摘要，1篇摘要栏误填作者/会议信息）。另参照资料包内主页研究文字；论文实质证据优先。

统一规则：只收文章实质研究的问题、采用的方法、处理的对象与学习设定；背景提及不匹配。维度与粒度分开，同义词不混入上下位或相关概念。聚类任务按所求划分类型区分，方法按可复用实现机制区分。同篇可涉及多维。每词有内部论文的精确连续原文证据，表内只列代表性论文，不声称穷举。标题证据只支持明确写出的内容。

本阶段未给全部文献打标签。coverage-review.json的144条记录是逐篇覆盖检查，候选词不等于最终标签；遗漏的小方向有明确记录。

主页处理：已阅读贾育衡个人主页完整研究兴趣句及PALM介绍。个人自述用于核对半监督、大模型与可信学习语境；PALM广义介绍仅为背景。没有仅因主页提及而加入智能体、AI4Science或幻觉检测，也没有把幻觉抑制改名为检测。

## 研究任务（18词）

|序号|英文 / 中文|定义与判定边界|代表性内部论文|
|---|---|---|---|
|1|Deep clustering / 深度聚类|利用可学习的神经表示和/或聚类头获得数据划分；仅在固定预训练特征上运行传统聚类不自动计入。|Towards Calibrated Deep Clustering Network；Mini-cluster Guided Long-tailed Deep Clustering|
|2|Ensemble clustering / 集成聚类|融合多个已有聚类结果以求共识划分；不同于多个分类器的监督集成，也不同于为用户产生多个不同划分。|Reliable Co-occurrence Guided Partial Clustering Ensemble；Generalization Performance of Ensemble Clustering: From Theory to Algorithm|
|3|Subspace clustering / 子空间聚类|按样本所属潜在子空间进行分组，通常利用自表达关系；一般的降维后聚类不充分。|Semi-Supervised Subspace Clustering via Tensor Low-Rank Representation；Adaptive Attribute and Structure Subspace Clustering Network|
|4|Multi-label learning / 多标记学习|学习为单个实例预测可同时成立的多个相关标记，含完整或弱监督下的多标记分类与识别；不同于单标记多分类及归一化标记描述度预测。|Multi-label Classification with High-rank and High-order Label Correlations；AME-LSIFT: Attention-Aware Multi-Label Ensemble with Label Subset-SpecIfic FeaTures|
|5|Label distribution learning / 标记分布学习|预测各标签对实例的相对描述程度（标签分布）；浓度分布扩展可按此核心任务覆盖，但不把浓度分布学习当同义词。|Inaccurate Label Distribution Learning；Concentration Distribution Learning from Label Distributions|
|6|Label enhancement / 标记增强|从逻辑标签恢复或构建更细致的标签分布；不把一般的数据增强、候选标签删除或负标签扩充视为此任务。|Label Distribution Learning from Logical Label；Progressive Label Enhancement|
|7|Dimensionality reduction / 降维|研究显式的低维映射或嵌入并以维度压缩为目标；仅存在隐藏层或特征向量不充分。|Semantic Dissimilarity Guided Locality Preserving Projections for Partial Label Dimensionality Reduction；Simultaneous Dimensionality Reduction and Classification via Dual Embedding Regularized Nonnegative Matrix Factorization|
|8|Image segmentation / 图像分割|对图像像素划分区域或赋予像素级类别，包括语义、实例与超像素分割；物体检测不等价。|Large Model Guided Semantic Segment Anything for Underwater Consumer Electronics；Superpixel Segmentation Based on Spatially Constrained Subspace Clustering|
|9|Data imputation and recovery / 数据补全与恢复|估计缺失观测或从污染观测恢复原始数值；输出为待恢复数据，不含仅改进分类鲁棒性。|Adaptive and robust low-rank tensor completion for missing and corrupted traffic data recovery；An Integrated Intra-view and Inter-view Framework for Multiple Traffic Variable Data Simultaneous Recovery|
|10|Hallucination mitigation / 幻觉抑制|减少生成内容与给定证据不一致的现象；本语料主要是视觉语言模型，不自动扩展为单独的幻觉检测任务。|Finding the Correct Visual Evidence Without Forgetting: Mitigating Hallucination in LVLMs via Inter-Layer Visual Attention Discrepancy；Steering LVLMs via Sparse Autoencoder for Hallucination Mitigation|
|11|Model merging / 模型合并|在参数或参数更新空间合并多个已训练模型以保留其能力；不同于预测投票或学生蒸馏。|ResMerge: Residual-based Spectral Merging of Large Language Models；PGSB: Pretrained-Guided Shared Basis for LoRA Model Merging|
|12|Multimodal retrieval / 多模态检索|将不同模态的查询与候选映射至可比较的检索空间；一般多模态分类或融合不充分。|PLUME: Latent Reasoning Based Universal Multimodal Embedding|
|13|Value and preference alignment / 价值与偏好对齐|使模型输出遵循人类或教师所表达的价值、偏好与行为排序；不同于跨模态特征对齐。|CuMA: Aligning LLMs with Sparse Cultural Values via Demographic-Aware Mixture of Adapters；Positive–Unlabeled Reinforcement Learning Distillation for On-Premise Small Models|
|14|Adversarial robustness / 对抗鲁棒性|研究模型在刻意构造的攻击或对抗扰动下保持正确行为的能力；一般噪声鲁棒性及相似度/不相似度的竞争关系不充分。|Improving the Adversarial Robustness of Deep Neural Networks via Efficient Two Stage Training；On the Adversarial Robustness of Hierarchical Classification|
|15|Dataset distillation / 数据集蒸馏|将训练数据压缩为保留训练效用的小型代表数据集；不同于模型输出或能力的知识蒸馏。当前依据仅为标题，不推断具体算法。|Fragmented Text Is Insufficient for Image Representation: Fine-Grained Correspondence in Multimodal Dataset Distillation|
|16|Person re-identification / 行人重识别|跨摄像头或场景检索同一身份的行人；不同于通用图像分类或行人检测。|Pseudo Label Rectification With Joint Camera Shift Adaptation and Outlier Progressive Recycling for Unsupervised Person Re-Identification|
|17|Multi-objective optimization / 多目标优化|以多个相互制约的目标求解帕累托解集；模型中出现多个损失项或联合训练不充分。|Adaptive Weights Generation for Decomposition-based Multi-objective Optimization Using Gaussian Process Regression|
|18|Confidence calibration / 置信度校准|使预测置信度或权重与正确概率相符；仅选取高置信样本、校正分布或使用校准一词不充分。|Towards Calibrated Deep Clustering Network；Calibrated Disambiguation for Partial Multi-Label Learning|

## 采用方法（15词）

|序号|英文 / 中文|定义与判定边界|代表性内部论文|
|---|---|---|---|
|19|Low-rank modeling / 低秩建模|显式利用矩阵或张量低秩约束、分解或近似表示相关结构；仅作为被批评的旧假设不充分，LoRA的参数化也不自动等同于数据低秩建模。|Multi-View Spectral Clustering Tailored Tensor Low-Rank Representation；Efficient and Robust Freeway Traffic Speed Estimation under Oblique Grid using Vehicle Trajectory Data|
|20|Nonnegative matrix factorization / 非负矩阵分解|以非负因子分解矩阵，含对称非负矩阵分解；一般低秩分解或仅非负约束不充分。|Self-supervised Symmetric Nonnegative Matrix Factorization；Positive and Negative Label-Driven Nonnegative Matrix Factorization|
|21|Graph structure learning / 图结构学习|学习或修正样本间的边、邻接或亲和矩阵；使用固定图或只学习节点嵌入不充分。|EGRC-Net: Embedding-induced Graph Refinement Clustering Network；Partial Label Learning Tailored Graph Construction|
|22|Graph and manifold regularization / 图与流形正则化|用邻域、图拉普拉斯或超图等结构对学习结果施加几何一致性约束；图神经网络或图构造本身不等价。|Inaccurate Label Distribution Learning with Dependency Noise；Local Low-Rank Approximation With Superpixel-Guided Locality Preserving Graph for Hyperspectral Image Classification|
|23|Graph neural networks / 图神经网络|使用图卷积或图上的可学习消息传递来获取表示；非神经图优化不计入。|Structural-Spectral Graph Convolution with Evidential Edge Learning for Hyperspectral Image Clustering；EGRC-Net: Embedding-induced Graph Refinement Clustering Network|
|24|Contrastive learning / 对比学习|通过视图、样本或中心间的吸引与区分目标学习表示；普通距离正则、竞争分类器不自动计入。|Superpixel Graph Contrastive Clustering with Semantic-Invariant Augmentations for Hyperspectral Images；ConMix: Contrastive Mixup at Representation Level for Long-tailed Deep Clustering|
|25|Pseudo-labeling and self-training / 伪标签与自训练|将模型对未标注或弱标注样本的预测作为后续训练信号，并可筛选、加权或迭代更新；仅输出预测标签不充分。|Keep It on a Leash: Controllable Pseudo-label Generation Towards Realistic Long-Tailed Semi-Supervised Learning；Towards Calibrated Deep Clustering Network|
|26|Sparse representation / 稀疏表示|以少量字典原子、基向量或潜在特征表达样本；单独对噪声矩阵加稀疏惩罚或参数剪枝不充分。|Hyperspectral Image Classification via Sparse Representation With Incremental Dictionaries；Steering LVLMs via Sparse Autoencoder for Hallucination Mitigation|
|27|Bayesian inference / 贝叶斯推断|通过先验与概率模型进行后验估计或近似推断；仅提及贝叶斯最优分类器或概率输出不充分。|Sparse Bayesian Learning-Based Kernel Poisson Regression；Generalized Relevance Vector Machine|
|28|Label correlation modeling / 标签相关性建模|显式建模标签间共现、依赖、排序或局部相关结构；样本间相似度及只使用多标签数据不充分。|Multi-label Classification with High-rank and High-order Label Correlations；FedHarmony: Harmonizing Heterogeneous Label Correlations in Federated Multi-Label Learning|
|29|Parameter-efficient fine-tuning / 参数高效微调|只训练少量增量参数或选定参数以适配预训练模型，包括低秩适配、适配器和连续提示；不能仅凭模型名称或推理加速认定。|FlexLoRA: Entropy-Guided Flexible Low-Rank Adaptation；Language-Assisted Image Clustering Guided by Discriminative Relational Signals and Adaptive Semantic Centers|
|30|Latent reasoning / 潜在空间推理|以连续潜在状态执行中间推理过程；普通隐层表示、链式文本推理或只提到潜变量不充分。|PLUME: Latent Reasoning Based Universal Multimodal Embedding|
|31|Knowledge distillation / 知识蒸馏|将教师模型的输出、表示或优化能力迁移至学生模型；数据集蒸馏和模型参数合并不等价。|Positive–Unlabeled Reinforcement Learning Distillation for On-Premise Small Models|
|32|Pairwise constraint propagation / 成对约束传播|扩展must-link/cannot-link监督关系，含只传播不相似关系的情形；普通节点标签传播或直接使用已知成对约束不等价。|Pairwise Constraint Propagation with Dual Adversarial Manifold Regularization；Constrained Clustering With Dissimilarity Propagation-Guided Graph-Laplacian PCA|
|33|Classifier ensemble / 分类器集成|结合多个分类器的预测或按样本分配专家以完成分类；聚类共识任务、模型权重合并不等价。|AME-LSIFT: Attention-Aware Multi-Label Ensemble with Label Subset-SpecIfic FeaTures；Long-tailed Partial Label Learning by Head Classifier and Tail Classifier Cooperation|

## 研究对象（6词）

|序号|英文 / 中文|定义与判定边界|代表性内部论文|
|---|---|---|---|
|34|Hyperspectral images / 高光谱图像|处理具有密集光谱波段的图像，包括其分类、聚类、表示与解混；一般遥感或RGB图像不充分。|Irregular Tensor Low-Rank Representation for Hyperspectral Image Representation；Structural-Spectral Graph Convolution with Evidential Edge Learning for Hyperspectral Image Clustering|
|35|Traffic data / 交通数据|道路交通速度、流量、轨迹或时空交通状态等实际数据对象；论文仅提及智能交通应用背景不充分。|Efficient and Robust Freeway Traffic Speed Estimation under Oblique Grid using Vehicle Trajectory Data；An Integrated Intra-view and Inter-view Framework for Multiple Traffic Variable Data Simultaneous Recovery|
|36|Underwater images / 水下图像|直接研究水下采集图像的感知问题及成像退化；一般海洋背景或消费电子场景提及不充分。|ViT-UWA: Vision Transformer Underwater-Adapter for Dense Predictions Beneath the Water Surface；Large Model Guided Semantic Segment Anything for Underwater Consumer Electronics|
|37|Large language models / 大语言模型|将大规模预训练语言模型作为要适配、合并、对齐或分析的对象；基因组基础模型和普通小型分类网络不自动计入。|CuMA: Aligning LLMs with Sparse Cultural Values via Demographic-Aware Mixture of Adapters；ResMerge: Residual-based Spectral Merging of Large Language Models|
|38|Vision-language models / 视觉语言模型|联合处理视觉与语言的模型，覆盖CLIP类图文表征模型及视觉语言大模型；须为论文的研究对象或主要组件，单独ViT或一般多模态任务不充分。仅有VLM或CLIP证据不能推定其为视觉语言大模型。|Language-Assisted Image Clustering Guided by Discriminative Relational Signals and Adaptive Semantic Centers；Steering LVLMs via Sparse Autoencoder for Hallucination Mitigation|
|39|Large vision-language models / 视觉语言大模型|以大语言模型为语言生成或推理核心并接收视觉输入的视觉语言模型，研究其生成、推理、适配或内部表征；必须有LVLM或视觉输入的大型多模态语言模型证据。CLIP类图文对比编码器及仅称VLM的模型不自动计入。|Finding the Correct Visual Evidence Without Forgetting: Mitigating Hallucination in LVLMs via Inter-Layer Visual Attention Discrepancy；Steering LVLMs via Sparse Autoencoder for Hallucination Mitigation|

## 学习设定（10词）

|序号|英文 / 中文|定义与判定边界|代表性内部论文|
|---|---|---|---|
|40|Domain adaptation / 域适应|源域与目标域分布不同，通过适配将知识迁移至目标域；需明确跨域对象及适配过程，单纯类别长尾或标注/未标注类别比例失配不充分。|Non-Negative Transfer Learning With Consistent Inter-Domain Distribution；Pseudo Label Rectification With Joint Camera Shift Adaptation and Outlier Progressive Recycling for Unsupervised Person Re-Identification|
|41|Partial label learning / 偏标记学习|每个实例给出候选标签集合，标准设定下仅一个为真；允许研究其带噪或半监督扩展，不与多标签同时为真混同。|Noise Separation guided Candidate Label Reconstruction for Noisy Partial Label Learning；Partial Label Learning Tailored Graph Construction|
|42|Semi-supervised learning / 半监督学习|结合有限监督信息与未标注样本，或以有限成对约束指导全部样本学习；纯自监督、无监督及仅小规模有标签训练不充分。|Beyond Distribution Estimation: Simplex Anchored Structural Inference Towards Universal Semi-supervised Learning；Semi-supervised Symmetric Non-negative Matrix Factorization with Low-Rank Tensor Representation|
|43|Class-imbalanced learning / 类别不平衡学习|显式处理类别或簇的样本量、各标签描述度总量的不均衡，包含长尾分布；must-link与cannot-link数量不均衡不等同于类别不平衡。|Mini-cluster Guided Long-tailed Deep Clustering；Long-tailed Partial Label Learning by Head Classifier and Tail Classifier Cooperation|
|44|Noisy-label learning / 噪声标签学习|训练监督中存在错误类别、候选集遗漏真标签或不准确的标签分布，并以此为研究条件；普通偏标记候选歧义、伪标签错误或输入数据污染不自动计入。|Noise Separation guided Candidate Label Reconstruction for Noisy Partial Label Learning；Instance-Dependent Inaccurate Label Distribution Learning|
|45|Multi-view learning / 多视图学习|同一对象有多个互补特征视图或观测变量，并显式联合利用视图间关系；数据增强生成两个视图不自动计入此数据设定。|Multi-View Spectral Clustering Tailored Tensor Low-Rank Representation；An Integrated Intra-view and Inter-view Framework for Multiple Traffic Variable Data Simultaneous Recovery|
|46|Federated learning / 联邦学习|多个客户端保留本地原始数据、以模型更新或统计信息协作训练；普通分布式计算不充分。|FedHarmony: Harmonizing Heterogeneous Label Correlations in Federated Multi-Label Learning；Trustworthy Federated Label Distribution Learning under Annotation Quality Disparity|
|47|Zero-shot learning / 零样本学习|依靠语义或属性等辅助信息识别训练时无标注样本的未见类别；与开放词表相关但非同义，不能由使用大模型直接推断。|Attribute Distribution Modeling and Semantic-Visual Alignment for Generative Zero-shot Learning|
|48|Open-vocabulary recognition / 开放词表识别|识别类别可通过词语指定而不局限于固定训练标签表；不等同于开放集拒识或零样本学习，当前论文仅支持标题层面的多标签识别设定。|LoCo: Selective Local Competition for Discriminative Open-Vocabulary Multi-Label Recognition|
|49|Weakly supervised learning / 弱监督学习|以不完整、不精确、粗粒度或不准确的监督信号替代充分准确的实例级真值，并将该监督条件作为实质研究问题；可包含有限标注、候选歧义、标签缺失或错误、包级与比例监督。纯无监督、自监督以及仅有输入噪声不自动计入。各具体设定互不等价，也不是本词的同义词。|Noise Separation guided Candidate Label Reconstruction for Noisy Partial Label Learning；Robust Label Proportions Learning；Noisy Label Removal for Partial Multi-Label Learning|

## 新版取舍

|处理|词条与理由|
|---|---|
|新增|弱监督学习承接监督信号不足或不可靠的粗粒度设定；视觉语言大模型单列为视觉语言模型子项，CLIP不自动计入。|
|规范名称|多标记分类改为多标记学习，保留分类、识别等同义称呼，不重复建词。|
|本次删项|依用户要求删除剪接变异效应预测，50词减为49词；该篇保留原有域适应候选，任务本身未覆盖。|
|删除独立词|高光谱解混由高光谱对象及具体方法覆盖；偏多标记以多标记学习＋弱监督覆盖；互补标签、不完整标签、PU、多示例、标签比例收束到弱监督及对应任务/方法，不列作同义词。|
|保留细分|偏标记与噪声标签在本组语料中反复作为核心研究条件，保持独立；半监督、类别不平衡、多视图、联邦、域适应、零样本、开放词表仍有独立检索价值。|

## 合并与未覆盖边界

长尾作为类别不平衡的子类型、矩阵/张量低秩作为低秩建模的形式，均不冒充同义词。LoRA、连续提示学习合入参数高效微调的定义与证据；图卷积、不同分割任务也未重复占位。视觉语言大模型是视觉语言模型在研究对象维度的严格子项；其余词暂不显式设置父子关系。候选采用有证据支持的具体对象层级，父项不重复列入。

未单列的实质方向包括剪接变异效应预测、生物网络相似性检索、视频编码码率控制、图像质量评价、边缘显著性检测及少数只有标题的新应用。它们仍是相关候选，不因本轮49词限制被判断为不相关；详见coverage-review.json逐篇缺口和候选处理理由。

质量限制：Vision-aware Head Divergence一文仅使用标题；RankMatch摘要末尾截断，不推断缺失结论。未联网补充内容，未修改生产数据或页面。
