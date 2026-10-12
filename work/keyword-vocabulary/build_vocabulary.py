import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent
papers = json.loads((ROOT / 'lab-papers.json').read_text(encoding='utf-8-sig'))
terms = []

def ev(i, quote=None, reason='直接研究该问题或将该方法用于所提出的方案。'):
    p = papers[i]
    field = 'abstract' if quote is not None else 'title'
    quote = quote if quote is not None else p['title']
    assert quote in (p.get(field) or ''), (i, quote)
    return dict(source_type='paper', source_id=p['id'], field=field,
                exact_quote=quote, role_reason_zh=reason)

def add(slug, en, zh, dim, definition, evidence, aliases=(), parent=None):
    terms.append(dict(id=slug, canonical_en=en, canonical_zh=zh,
                      primary_dimension=dim, definition_zh=definition,
                      aliases=list(aliases), parent_id=parent, evidence=evidence))

T='research_task'; M='method'; S='research_setting'; O='application_object'

# Research tasks; coverage uses stable IDs rather than list positions.
add('deep-clustering','Deep clustering','深度聚类',T,
    '利用可学习的神经表示和/或聚类头获得数据划分；仅在固定预训练特征上运行传统聚类不自动计入。',
    [ev(3,'To tackle this critical issue, we pioneer the development of a calibrated deep clustering framework.'),
     ev(103,'To address this, we propose a mini-cluster guided long-tailed deep clustering method, termed MiniClustering.')])
add('ensemble-clustering','Ensemble clustering','集成聚类',T,
    '融合多个已有聚类结果以求共识划分；不同于多个分类器的监督集成，也不同于为用户产生多个不同划分。',
    [ev(17,'Partial clustering ensemble integrates multiple incomplete base clusterings to generate a consensus one.'),
     ev(6,'This paper examines the generalization performance of ensemble clustering, focusing on generalization error, excess risk and consistency.')],['Clustering ensemble','Consensus clustering'])
add('subspace-clustering','Subspace clustering','子空间聚类',T,
    '按样本所属潜在子空间进行分组，通常利用自表达关系；一般的降维后聚类不充分。',
    [ev(46,'In this letter, we propose a novel semi-supervised subspace clustering method, which is able to simultaneously augment the initial supervisory information and construct a discriminative affinity matrix.'),
     ev(50,'Then, we perform self-expressiveness on the constructed attribute and structure matrices to learn their affinity graphs separately.')])
add('multi-label-learning','Multi-label learning','多标记学习',T,
    '学习为单个实例预测可同时成立的多个相关标记，含完整或弱监督下的多标记分类与识别；不同于单标记多分类及归一化标记描述度预测。',
    [ev(41,'Comparative studies over twelve benchmark data sets validate the effectiveness of the proposed algorithm in multi-label classification.'),
     ev(34,'Multi-label ensemble can achieve superior performance on multi-label learning problems by integrating a number of base classifiers.')],['Multi-label classification','Multi-label recognition','多标签学习','多标记分类','多标签分类'])
add('label-distribution-learning','Label distribution learning','标记分布学习',T,
    '预测各标签对实例的相对描述程度（标签分布）；浓度分布扩展可按此核心任务覆盖，但不把浓度分布学习当同义词。',
    [ev(39,'Label distribution learning (LDL) trains a model to predict the relevance of a set of labels (called label distribution (LD)) to an instance.'),
     ev(117,'Moreover, we propose a novel model by probabilistic methods and neural networks to learn label distributions and background concentrations from existing LDL datasets.')],['Label Distribution Learning','标签分布学习'])
add('label-enhancement','Label enhancement','标记增强',T,
    '从逻辑标签恢复或构建更细致的标签分布；不把一般的数据增强、候选标签删除或负标签扩充视为此任务。',
    [ev(128,'To solve the above problems, we propose a novel method to learn an LDL model directly from the logical label, which unifies LE and LDL into a joint model, and avoids the drawbacks of the previous LE methods.'),ev(31)],['标签增强'])
add('dimensionality-reduction','Dimensionality reduction','降维',T,
    '研究显式的低维映射或嵌入并以维度压缩为目标；仅存在隐藏层或特征向量不充分。',
    [ev(134,'After the alternating procedure, SDLPP maps the original data to a pre-specified low-dimensional feature space.'),
     ev(71,'Our DENMF solution simultaneously finds the low-dimensional representations and assignment matrix via joint optimization for better classification.')])
add('image-segmentation','Image segmentation','图像分割',T,
    '对图像像素划分区域或赋予像素级类别，包括语义、实例与超像素分割；物体检测不等价。',
    [ev(28,'In this paper, we propose a generalist-specialist-like framework for underwater image semantic segmentation called Underwater Semantic Segment Anything (UWSSA).'),
     ev(60,'Superpixel segmentation aims at dividing the input image into some representative regions containing pixels with similar and consistent intrinsic properties, without any prior knowledge about the shape and size of each superpixel.')])
add('data-imputation-recovery','Data imputation and recovery','数据补全与恢复',T,
    '估计缺失观测或从污染观测恢复原始数值；输出为待恢复数据，不含仅改进分类鲁棒性。',
    [ev(25,'To further enhance robustness against corrupted data, the model is extended to a robust variant by integrating an anomaly-tolerant module based on the l1 norm, capable of simultaneously eliminating anomalous observations and imputing missing values.'),
     ev(37,'In this paper, we leverage both intra-view and inter-view correlations for multiple traffic variable data simultaneous recovery.')])
add('hallucination-mitigation','Hallucination mitigation','幻觉抑制',T,
    '减少生成内容与给定证据不一致的现象；本语料主要是视觉语言模型，不自动扩展为单独的幻觉检测任务。',
    [ev(98,'Motivated by this observation, we propose a novel hallucination mitigation method that enhances visual evidence based on Inter-Layer Visual Attention Discrepancy (ILVAD).'),
     ev(111,'Building on these insights, we propose Steering LVLMs via SAE Latent Directions (SSL), a plug-and-play method based on SAE-derived latent directions to mitigate hallucinations in LVLMs.')],['Hallucination reduction'])
add('model-merging','Model merging','模型合并',T,
    '在参数或参数更新空间合并多个已训练模型以保留其能力；不同于预测投票或学生蒸馏。',
    [ev(88,'Based on this observation, we propose ResMerge, a residual-based spectral merging framework for RL experts.'),ev(79)])
add('multimodal-retrieval','Multimodal retrieval','多模态检索',T,
    '将不同模态的查询与候选映射至可比较的检索空间；一般多模态分类或融合不充分。',
    [ev(90,'Universal multimodal embedding (UME) maps heterogeneous inputs into a shared retrieval space with a single model.'),
     ev(90,'PLUME is especially well suited to retrieval settings where relevant evidence is dense, structurally complex, and difficult to organize through verbalized intermediate rationales, such as video and visual document retrieval.')])
add('value-preference-alignment','Value and preference alignment','价值与偏好对齐',T,
    '使模型输出遵循人类或教师所表达的价值、偏好与行为排序；不同于跨模态特征对齐。',
    [ev(99,'To resolve this, we propose CUMA (Cultural Mixture of Adapters), a framework that frames alignment as a conditional capacity separation problem.'),
     ev(96,"Without human-labeled preferences or a reward model, our method distills the teacher's preference-optimization capability from black-box generations into a locally trainable student.")])
add('adversarial-robustness','Adversarial robustness','对抗鲁棒性',T,
    '研究模型在刻意构造的攻击或对抗扰动下保持正确行为的能力；一般噪声鲁棒性及相似度/不相似度的竞争关系不充分。',
    [ev(135,'In this paper, we propose a new proactive defense method based on a two-stage training procedure in order to enhance the adversarial robustness of DNNs.'),
     ev(124,'In this paper, we investigate the adversarial robustness of DNN models on such complex classification tasks.')])
add('dataset-distillation','Dataset distillation','数据集蒸馏',T,
    '将训练数据压缩为保留训练效用的小型代表数据集；不同于模型输出或能力的知识蒸馏。当前依据仅为标题，不推断具体算法。',
    [ev(92,reason='标题明确研究多模态数据集蒸馏，摘要缺失，仅保留题名层面的任务。')])
add('person-reidentification','Person re-identification','行人重识别',T,
    '跨摄像头或场景检索同一身份的行人；不同于通用图像分类或行人检测。',
    [ev(48,'Extensive experiments on three large scale unsupervised and unsupervised domain adaptive (UDA) person re-ID benchmarks validate the effectiveness of$CASTOR$and its wide compatibility with the state-of-the-art clustering-based methods.')],['Person re-ID','Person reidentification'])
add('multi-objective-optimization','Multi-objective optimization','多目标优化',T,
    '以多个相互制约的目标求解帕累托解集；模型中出现多个损失项或联合训练不充分。',
    [ev(142,'In this paper, we propose an adaptive method to periodically regenerate the weight vectors for decomposition-based multi-objective algorithms according to the geometry of the estimated Pareto front.')])
add('confidence-calibration','Confidence calibration','置信度校准',T,
    '使预测置信度或权重与正确概率相符；仅选取高置信样本、校正分布或使用校准一词不充分。',
    [ev(3,'Specifically, we propose a novel dual head (calibration head and clustering head) deep clustering model that can effectively calibrate the estimated confidence and the actual accuracy.'),
     ev(122,"To obtain the optimal weighting function from PML dataset during the training, a transferable calibrator is designed, which takes the histogram of positive samples' confidences as input, and outputs the optimal curriculum weighting for training.")],['Prediction calibration'])

# Reusable methods and the domain-adaptation setting.
add('low-rank-modeling','Low-rank modeling','低秩建模',M,
    '显式利用矩阵或张量低秩约束、分解或近似表示相关结构；仅作为被批评的旧假设不充分，LoRA的参数化也不自动等同于数据低秩建模。',
    [ev(1,'Specifically, we explicitly impose a symmetric low-rank constraint and a structured sparse low-rank constraint on the frontal and horizontal slices of the tensor to characterize the intra-view and inter-view relationships, respectively.'),
     ev(38,'Then, with the enhanced traffic state low-rankness in the oblique matrix, a low-rank matrix completion method is tailored to explicitly capture spatiotemporal traffic propagation characteristics and precisely reconstruct traffic states.')])
add('nonnegative-matrix-factorization','Nonnegative matrix factorization','非负矩阵分解',M,
    '以非负因子分解矩阵，含对称非负矩阵分解；一般低秩分解或仅非负约束不充分。',
    [ev(0,'Inspired by ensemble clustering that aims to seek a better clustering result from a set of clustering results, we propose self-supervised SNMF (S3NMF), which is capable of boosting clustering performance progressively by taking advantage of the sensitivity to initialization characteristic of SNMF, without relying on any additional information.'),
     ev(61,'In this paper, we propose a nonnegative matrix factorization (NMF) based classification method leveraging both positive and negative label information, which is termed as positive and negative label-driven NMF (PNLD-NMF).')],['Non-negative matrix factorization'])
add('graph-structure-learning','Graph structure learning','图结构学习',M,
    '学习或修正样本间的边、邻接或亲和矩阵；使用固定图或只学习节点嵌入不充分。',
    [ev(42,'In order to address this issue, we propose a novel clustering network called Embedding-Induced Graph Refinement Clustering Network (EGRC-Net), which effectively utilizes the learned embedding to adaptively refine the initial graph and enhance the clustering performance.'),
     ev(113,'In this paper, we propose a novel graph construction model that is tailored to PLL.')])
add('graph-manifold-regularization','Graph and manifold regularization','图与流形正则化',M,
    '用邻域、图拉普拉斯或超图等结构对学习结果施加几何一致性约束；图神经网络或图构造本身不等价。',
    [ev(15,'Furthermore, we employ graph regularization to align the topological structures of the input and output spaces, ensuring accurate reconstruction of the true label distribution matrix.'),
     ev(51,'By taking advantage of the local manifold structure, a Laplacian graph is constructed from the superpixels to ensure that a typical pixel should be similar to its neighbors within the same superpixel.')])
add('graph-neural-networks','Graph neural networks','图神经网络',M,
    '使用图卷积或图上的可学习消息传递来获取表示；非神经图优化不计入。',
    [ev(24,'To address these challenges, we first propose a structural-spectral graph convolutional operator (SSGCO) tailored for graph-structured HSI superpixels to improve their representation quality through the co-extraction of spatial and spectral features.'),
     ev(42,'To begin, we leverage both semantic and topological information by employing a vanilla auto-encoder and a graph convolution network, respectively, to learn a latent feature representation.')])
add('contrastive-learning','Contrastive learning','对比学习',M,
    '通过视图、样本或中心间的吸引与区分目标学习表示；普通距离正则、竞争分类器不自动计入。',
    [ev(36,'Then sample-level alignment and clustering-center-level contrast are performed for better intra-class similarity and inter-class dissimilarity of superpixel embeddings.'),
     ev(120,'The proposed method makes innovations to mixup representations in contrastive learning to enhance deep clustering in long-tailed scenarios.')])
add('pseudo-label-self-training','Pseudo-labeling and self-training','伪标签与自训练',M,
    '将模型对未标注或弱标注样本的预测作为后续训练信号，并可筛选、加权或迭代更新；仅输出预测标签不充分。',
    [ev(7,'To tackle this challenge, we propose a Controllable Pseudo-label Generation (CPG) framework, expanding the labeled dataset with the progressively identified reliable pseudo-labels from the unlabeled dataset and training the model on the updated labeled dataset with a known distribution, making it unaffected by the unlabeled data distribution.'),
     ev(3,'Then, the clustering head dynamically selects reliable high-confidence samples estimated by the calibration head for pseudo-label self-training.')])
add('sparse-representation','Sparse representation','稀疏表示',M,
    '以少量字典原子、基向量或潜在特征表达样本；单独对噪声矩阵加稀疏惩罚或参数剪枝不充分。',
    [ev(66,'In this letter, we propose a new sparse representation (SR)-based method for hyperspectral image (HSI) classification, namely SR with incremental dictionaries (SRID).'),
     ev(111,'In this work, we leverage sparse autoencoders (SAEs) to identify semantic directions closely associated with faithfulness or hallucination, extracting more precise and disentangled hallucination-related representations.')])
add('bayesian-inference','Bayesian inference','贝叶斯推断',M,
    '通过先验与概率模型进行后验估计或近似推断；仅提及贝叶斯最优分类器或概率输出不充分。',
    [ev(69,'In this paper, we introduce a closed-form sparse Bayesian kernel Poisson regression (SBKPR) model for count data regression problems based on the sparse Bayesian learning (SBL) approach.'),
     ev(141,'Since EFD results in inference intractable problem in Bayesian analysis, in this paper, Laplace approximation is adopted to solve this problem, which is a common approach in Bayesian inference.')])
add('label-correlation-modeling','Label correlation modeling','标签相关性建模',M,
    '显式建模标签间共现、依赖、排序或局部相关结构；样本间相似度及只使用多标签数据不充分。',
    [ev(41,'To this end, we propose a simple yet effective method to depict the high-order label correlations explicitly, and at the same time maintain the high-rank of the label matrix.'),
     ev(101,'It introduces consensus correlation, capturing agreement among other clients and serving as a global teacher to correct biased local estimates.')])
add('parameter-efficient-fine-tuning','Parameter-efficient fine-tuning','参数高效微调',M,
    '只训练少量增量参数或选定参数以适配预训练模型，包括低秩适配、适配器和连续提示；不能仅凭模型名称或推理加速认定。',
    [ev(102,'To overcome these limitations, we propose FlexLoRA, an entropy-guided flexible low-rank adaptation framework that (i) evaluates matrix importance via spectral energy entropy, (ii) supports rank pruning and expansion under a global budget, and (iii) employs zero-impact initialization for newly added singular directions to ensure stability.'),
     ev(80,'Second, we learn category-wise continuous semantic centers via prompt learning to produce the final clustering assignments.','采用可学习连续提示产生语义中心；作为参数高效适配的具体形式，不将连续提示和LoRA视为同义词。')],['Parameter efficient fine tuning'])
add('latent-reasoning','Latent reasoning','潜在空间推理',M,
    '以连续潜在状态执行中间推理过程；普通隐层表示、链式文本推理或只提到潜变量不充分。',
    [ev(90,'We propose PLUME, a latent reasoning framework that advances UME by replacing verbalized CoT with a short autoregressive rollout of continuous latent states.')])
add('knowledge-distillation','Knowledge distillation','知识蒸馏',M,
    '将教师模型的输出、表示或优化能力迁移至学生模型；数据集蒸馏和模型参数合并不等价。',
    [ev(96,"Without human-labeled preferences or a reward model, our method distills the teacher's preference-optimization capability from black-box generations into a locally trainable student.")],['Model distillation'])
add('domain-adaptation','Domain adaptation','域适应',S,
    '源域与目标域分布不同，通过适配将知识迁移至目标域；需明确跨域对象及适配过程，单纯类别长尾或标注/未标注类别比例失配不充分。',
    [ev(62,'In this letter, we propose a novel transfer learning approach, which simultaneously exploits the intra-domain differentiation and inter-domain correlation to comprehensively solve the drawbacks many existing transfer learning methods suffer from, i.e., they either are unable to handle the negative samples or have strict assumptions on the distribution.'),
     ev(48,'Extensive experiments on three large scale unsupervised and unsupervised domain adaptive (UDA) person re-ID benchmarks validate the effectiveness of$CASTOR$and its wide compatibility with the state-of-the-art clustering-based methods.')])
add('pairwise-constraint-propagation','Pairwise constraint propagation','成对约束传播',M,
    '扩展must-link/cannot-link监督关系，含只传播不相似关系的情形；普通节点标签传播或直接使用已知成对约束不等价。',
    [ev(2,'Specifically, we propagate MLs and CLs with two separated variables, called similarity and dissimilarity matrices, under the guidance of the graph structure constructed from data samples.'),
     ev(64,'Furthermore, we innovatively propose to propagate the cannot-link constraints (i.e., dissimilarity) to refine the dissimilarity regularizer to be more informative.')])
add('classifier-ensemble','Classifier ensemble','分类器集成',M,
    '结合多个分类器的预测或按样本分配专家以完成分类；聚类共识任务、模型权重合并不等价。',
    [ev(34,'It utilizes$c$-means clustering to produce Label Subset-specIfic FeaTures (LSIFT), constructs a neural network based model for each label subset, and integrates the base models with a dynamic and automatic attention-aware mechanism.'),
     ev(129,'Then, we propose a classifier weight estimation module to automatically estimate the shot belongingness (head class or tail class) of the samples and allocate the weights for the head classifier and tail classifier when making prediction.')],['Ensemble classification'])

# Supervision and data conditions, deliberately distinct from methods.
add('partial-label-learning','Partial label learning','偏标记学习',S,
    '每个实例给出候选标签集合，标准设定下仅一个为真；允许研究其带噪或半监督扩展，不与多标签同时为真混同。',
    [ev(4,'Partial label learning is a weakly supervised learning problem in which an instance is annotated with a set of candidate labels, among which only one is the correct label.'),ev(113)],['偏标签学习'])
add('semi-supervised-learning','Semi-supervised learning','半监督学习',S,
    '结合有限监督信息与未标注样本，或以有限成对约束指导全部样本学习；纯自监督、无监督及仅小规模有标签训练不充分。',
    [ev(97,'Semi-supervised learning faces significant challenges in realistic scenarios where labeled data is scarce and unlabeled data follows unknown, arbitrary distributions.'),
     ev(32,'Semi-supervised symmetric non-negative matrix factorization (SNMF) utilizes the available supervisory information (usually in the form of pairwise constraints) to improve the clustering ability of SNMF.')],['Semisupervised learning'])
add('class-imbalance','Class-imbalanced learning','类别不平衡学习',S,
    '显式处理类别或簇的样本量、各标签描述度总量的不均衡，包含长尾分布；must-link与cannot-link数量不均衡不等同于类别不平衡。',
    [ev(103,'To address this, we propose a mini-cluster guided long-tailed deep clustering method, termed MiniClustering.'),
     ev(129,'However, in real-world applications, the distribution of the classes is imbalanced or long-tailed, leading to the long-tailed partial label learning problem.')],['Class imbalance','Class-imbalance learning'])
add('noisy-label-learning','Noisy-label learning','噪声标签学习',S,
    '训练监督中存在错误类别、候选集遗漏真标签或不准确的标签分布，并以此为研究条件；普通偏标记候选歧义、伪标签错误或输入数据污染不自动计入。',
    [ev(4,'However, in practice the correct label is not always in the candidate label set, leading to the noisy partial label learning (NPLL) problem.'),
     ev(43,'First, we assume that the inaccurate label distribution consists of the ground-truth label distribution and instance-dependent noise.')],['Learning with noisy labels'])
add('multi-view-learning','Multi-view learning','多视图学习',S,
    '同一对象有多个互补特征视图或观测变量，并显式联合利用视图间关系；数据增强生成两个视图不自动计入此数据设定。',
    [ev(1,'This paper explores the problem of multi-view spectral clustering (MVSC) based on tensor low-rank modeling.'),
     ev(37,'To explore the inter-view relationships, a multi-view subspace consistency learning module is developed to bridge connections and activate complementarities among multi-view traffic data.')])
add('federated-learning','Federated learning','联邦学习',S,
    '多个客户端保留本地原始数据、以模型更新或统计信息协作训练；普通分布式计算不充分。',
    [ev(101,'Federated Multi-Label Learning is a distributed paradigm where multiple clients possess heterogeneous multi-label data and perform collaborative learning under privacy constraints without sharing raw data.'),
     ev(95,'To address this trust dilemma, we propose FedQual, a quality-aware Fed-LDL framework with two coupled mechanisms: (i) quality-adaptive client training guided by a global semantic anchor that calibrates low-quality clients while preserving high-quality autonomy, and (ii) reliability-aware server aggregation that reweights client contributions by effective reliable information rather than raw sample size.')])
add('zero-shot-learning','Zero-shot learning','零样本学习',S,
    '依靠语义或属性等辅助信息识别训练时无标注样本的未见类别；与开放词表相关但非同义，不能由使用大模型直接推断。',
    [ev(10,'By jointly modeling semantic diversity and visual structural consistency, AAVS provides more effective generation conditions for unseen classes to generate visual features.')],['Zero shot learning'])
add('open-vocabulary-recognition','Open-vocabulary recognition','开放词表识别',S,
    '识别类别可通过词语指定而不局限于固定训练标签表；不等同于开放集拒识或零样本学习，当前论文仅支持标题层面的多标签识别设定。',
    [ev(85,reason='标题直接声明开放词表多标签识别；不根据标题推断具体实现。')])

# Application/model objects. These are objects, never supervision labels.
add('hyperspectral-images','Hyperspectral images','高光谱图像',O,
    '处理具有密集光谱波段的图像，包括其分类、聚类、表示与解混；一般遥感或RGB图像不充分。',
    [ev(5,'To tackle this issue, we propose a novel model for irregular tensor low-rank representation tailored to efficiently model irregular 3D cubes.'),ev(24)],['Hyperspectral imagery','Hyperspectral image'])
add('traffic-data','Traffic data','交通数据',O,
    '道路交通速度、流量、轨迹或时空交通状态等实际数据对象；论文仅提及智能交通应用背景不充分。',
    [ev(38,'In this study, we propose an efficient and robust low-rank model for precise spatiotemporal traffic speed state estimation (TSE) using low-penetration vehicle trajectory data.'),ev(37)])
add('underwater-images','Underwater images','水下图像',O,
    '直接研究水下采集图像的感知问题及成像退化；一般海洋背景或消费电子场景提及不充分。',
    [ev(20,'To solve this problem, we propose the Vision Transformer Underwater-Adapter (ViT-UWA), the first detail-focused and adapted ViT backbone for underwater dense prediction tasks, without requiring task-specific pretraining.'),ev(28)],['Underwater imagery'])
add('large-language-models','Large language models','大语言模型',O,
    '将大规模预训练语言模型作为要适配、合并、对齐或分析的对象；基因组基础模型和普通小型分类网络不自动计入。',
    [ev(99,'As Large Language Models (LLMs) serve a global audience, alignment must transition from enforcing universal consensus to respecting cultural pluralism.'),ev(88)])
add('vision-language-models','Vision-language models','视觉语言模型',O,
    '联合处理视觉与语言的模型，覆盖CLIP类图文表征模型及视觉语言大模型；须为论文的研究对象或主要组件，单独ViT或一般多模态任务不充分。仅有VLM或CLIP证据不能推定其为视觉语言大模型。',
    [ev(80,'Language-Assisted Image Clustering (LAIC) augments the input images with additional texts with the help of vision-language models (VLMs) to promote clustering performance.'),
     ev(111,'Building on these insights, we propose Steering LVLMs via SAE Latent Directions (SSL), a plug-and-play method based on SAE-derived latent directions to mitigate hallucinations in LVLMs.')],['Visual-language models'])

add('weakly-supervised-learning','Weakly supervised learning','弱监督学习',S,
    '以不完整、不精确、粗粒度或不准确的监督信号替代充分准确的实例级真值，并将该监督条件作为实质研究问题；可包含有限标注、候选歧义、标签缺失或错误、包级与比例监督。纯无监督、自监督以及仅有输入噪声不自动计入。各具体设定互不等价，也不是本词的同义词。',
    [ev(4,'Partial label learning is a weakly supervised learning problem in which an instance is annotated with a set of candidate labels, among which only one is the correct label.'),
     ev(109,'Learning from Label Proportions (LLP) is a weakly-supervised paradigm that uses bag-level label proportions to train instance-level classifiers, offering a practical alternative to costly instance-level annotation.'),
     ev(125,'This paper addresses the problem of partial multi-label learning (PML), a challenging weakly supervised learning framework, where each sample is associated with a candidate label set comprising both ground-true labels and noisy labels.')],['Weakly-supervised learning'])
add('large-vision-language-models','Large vision-language models','视觉语言大模型',O,
    '以大语言模型为语言生成或推理核心并接收视觉输入的视觉语言模型，研究其生成、推理、适配或内部表征；必须有LVLM或视觉输入的大型多模态语言模型证据。CLIP类图文对比编码器及仅称VLM的模型不自动计入。',
    [ev(98,'Large Vision-Language Models (LVLMs) have shown remarkable performance on a wide range of vision-language tasks.'),
     ev(111,'Building on these insights, we propose Steering LVLMs via SAE Latent Directions (SSL), a plug-and-play method based on SAE-derived latent directions to mitigate hallucinations in LVLMs.')],
    ['Large visual-language models'],parent='vision-language-models')

assert len(terms)==49, len(terms)
homepage_text = (ROOT/'homepage-context.md').read_text(encoding='utf-8-sig')
home_quote = 'semi\\weakly\\un-supervised learning'
assert home_quote in homepage_text
next(t for t in terms if t['id']=='semi-supervised-learning')['evidence'].append(dict(
    source_type='homepage', source_id='https://jyh-learning.github.io/',
    field='research_description', exact_quote=home_quote,
    role_reason_zh='个人主页自述帮助选定半监督学习术语；论文决定具体判定边界，不由此将所有弱监督与无监督设定合并。'))

# Each row was selected after reading that paper's complete supplied record.
# These are vocabulary coverage probes, not final paper annotations.
coverage_map = {
    0: ['nonnegative-matrix-factorization', 'graph-structure-learning'],
    1: ['low-rank-modeling', 'multi-view-learning'],
    2: ['graph-manifold-regularization', 'pairwise-constraint-propagation', 'semi-supervised-learning'],
    3: ['deep-clustering', 'confidence-calibration', 'pseudo-label-self-training'],
    4: ['partial-label-learning', 'noisy-label-learning'],
    5: ['low-rank-modeling', 'hyperspectral-images'],
    6: ['ensemble-clustering'],
    7: ['pseudo-label-self-training', 'semi-supervised-learning', 'class-imbalance'],
    8: ['class-imbalance'],
    9: ['partial-label-learning'],
    10: ['zero-shot-learning'],
    11: ['semi-supervised-learning'],
    12: ['data-imputation-recovery', 'traffic-data'],
    13: ['graph-structure-learning', 'sparse-representation', 'hyperspectral-images'],
    14: ['nonnegative-matrix-factorization', 'graph-structure-learning'],
    15: ['label-distribution-learning', 'graph-manifold-regularization', 'label-correlation-modeling', 'noisy-label-learning'],
    16: ['deep-clustering', 'graph-structure-learning'],
    17: ['ensemble-clustering', 'graph-structure-learning'],
    18: ['adversarial-robustness'],
    19: ['domain-adaptation'],
    20: ['image-segmentation', 'underwater-images'],
    21: ['low-rank-modeling', 'graph-structure-learning'],
    22: ['graph-manifold-regularization', 'multi-view-learning', 'hyperspectral-images'],
    23: ['adversarial-robustness'],
    24: ['deep-clustering', 'graph-structure-learning', 'graph-neural-networks', 'contrastive-learning', 'hyperspectral-images'],
    25: ['data-imputation-recovery', 'low-rank-modeling', 'traffic-data'],
    26: ['ensemble-clustering', 'graph-structure-learning'],
    27: ['label-distribution-learning', 'low-rank-modeling', 'label-correlation-modeling', 'class-imbalance', 'weakly-supervised-learning'],
    28: ['image-segmentation', 'underwater-images'],
    29: ['label-enhancement'],
    30: [],
    31: ['label-enhancement'],
    32: ['low-rank-modeling', 'nonnegative-matrix-factorization', 'pairwise-constraint-propagation', 'semi-supervised-learning'],
    33: ['low-rank-modeling', 'hyperspectral-images'],
    34: ['multi-label-learning', 'classifier-ensemble'],
    35: ['label-distribution-learning', 'label-correlation-modeling'],
    36: ['deep-clustering', 'graph-neural-networks', 'contrastive-learning', 'hyperspectral-images'],
    37: ['data-imputation-recovery', 'low-rank-modeling', 'multi-view-learning', 'traffic-data'],
    38: ['data-imputation-recovery', 'low-rank-modeling', 'traffic-data'],
    39: ['label-distribution-learning', 'low-rank-modeling', 'graph-manifold-regularization', 'label-correlation-modeling', 'noisy-label-learning'],
    40: ['pseudo-label-self-training', 'partial-label-learning', 'semi-supervised-learning', 'hyperspectral-images'],
    41: ['multi-label-learning', 'label-correlation-modeling'],
    42: ['deep-clustering', 'graph-structure-learning', 'graph-neural-networks'],
    43: ['label-distribution-learning', 'low-rank-modeling', 'noisy-label-learning'],
    44: ['data-imputation-recovery', 'low-rank-modeling', 'traffic-data'],
    45: ['ensemble-clustering', 'graph-structure-learning'],
    46: ['subspace-clustering', 'low-rank-modeling', 'graph-manifold-regularization', 'pairwise-constraint-propagation', 'semi-supervised-learning'],
    47: ['deep-clustering', 'graph-neural-networks', 'pseudo-label-self-training'],
    48: ['person-reidentification', 'pseudo-label-self-training', 'domain-adaptation'],
    49: ['sparse-representation', 'hyperspectral-images'],
    50: ['deep-clustering', 'subspace-clustering', 'graph-structure-learning'],
    51: ['low-rank-modeling', 'graph-manifold-regularization', 'hyperspectral-images'],
    52: ['dimensionality-reduction', 'graph-structure-learning', 'semi-supervised-learning'],
    53: ['image-segmentation', 'low-rank-modeling', 'hyperspectral-images'],
    54: ['low-rank-modeling', 'semi-supervised-learning'],
    55: ['low-rank-modeling', 'hyperspectral-images'],
    56: ['deep-clustering', 'subspace-clustering', 'graph-structure-learning'],
    57: ['low-rank-modeling', 'graph-structure-learning', 'graph-manifold-regularization', 'pairwise-constraint-propagation', 'semi-supervised-learning'],
    58: ['multi-label-learning', 'classifier-ensemble'],
    59: ['nonnegative-matrix-factorization', 'graph-structure-learning', 'pairwise-constraint-propagation', 'semi-supervised-learning'],
    60: ['subspace-clustering', 'image-segmentation', 'graph-manifold-regularization'],
    61: ['nonnegative-matrix-factorization'],
    62: ['pseudo-label-self-training', 'domain-adaptation'],
    63: ['low-rank-modeling', 'graph-structure-learning', 'graph-manifold-regularization', 'pairwise-constraint-propagation', 'semi-supervised-learning'],
    64: ['dimensionality-reduction', 'graph-manifold-regularization', 'pairwise-constraint-propagation', 'semi-supervised-learning'],
    65: ['graph-structure-learning'],
    66: ['pseudo-label-self-training', 'sparse-representation', 'hyperspectral-images'],
    67: [],
    68: ['nonnegative-matrix-factorization', 'semi-supervised-learning'],
    69: ['bayesian-inference'],
    70: ['image-segmentation'],
    71: ['dimensionality-reduction', 'nonnegative-matrix-factorization', 'graph-manifold-regularization', 'semi-supervised-learning'],
    72: ['pseudo-label-self-training', 'classifier-ensemble', 'semi-supervised-learning', 'hyperspectral-images'],
    73: ['semi-supervised-learning'],
    74: ['nonnegative-matrix-factorization', 'graph-structure-learning', 'pairwise-constraint-propagation', 'semi-supervised-learning'],
    75: ['nonnegative-matrix-factorization', 'graph-manifold-regularization'],
    76: [],
    77: [],
    78: ['weakly-supervised-learning'],
    79: ['model-merging'],
    80: ['deep-clustering', 'parameter-efficient-fine-tuning', 'vision-language-models'],
    81: ['multi-label-learning', 'weakly-supervised-learning'],
    82: ['deep-clustering', 'multi-view-learning'],
    83: ['partial-label-learning', 'semi-supervised-learning'],
    84: ['pseudo-label-self-training', 'vision-language-models'],
    85: ['multi-label-learning', 'open-vocabulary-recognition'],
    86: ['hallucination-mitigation', 'large-vision-language-models'],
    87: ['ensemble-clustering'],
    88: ['model-merging', 'large-language-models'],
    89: ['large-language-models'],
    90: ['multimodal-retrieval', 'latent-reasoning', 'large-vision-language-models'],
    91: [],
    92: ['dataset-distillation'],
    93: ['deep-clustering', 'graph-neural-networks', 'class-imbalance'],
    94: ['multi-label-learning', 'weakly-supervised-learning'],
    95: ['label-distribution-learning', 'noisy-label-learning', 'federated-learning'],
    96: ['value-preference-alignment', 'knowledge-distillation', 'weakly-supervised-learning'],
    97: ['pseudo-label-self-training', 'semi-supervised-learning'],
    98: ['hallucination-mitigation', 'large-vision-language-models'],
    99: ['value-preference-alignment', 'parameter-efficient-fine-tuning', 'large-language-models'],
    100: [],
    101: ['multi-label-learning', 'label-correlation-modeling', 'federated-learning'],
    102: ['parameter-efficient-fine-tuning'],
    103: ['deep-clustering', 'pseudo-label-self-training', 'class-imbalance'],
    104: ['deep-clustering', 'pseudo-label-self-training'],
    105: ['deep-clustering', 'pseudo-label-self-training', 'large-vision-language-models'],
    106: ['multi-label-learning', 'confidence-calibration', 'contrastive-learning', 'pseudo-label-self-training', 'semi-supervised-learning'],
    107: ['label-distribution-learning', 'data-imputation-recovery', 'low-rank-modeling', 'weakly-supervised-learning'],
    108: ['deep-clustering', 'pseudo-label-self-training'],
    109: ['contrastive-learning', 'pseudo-label-self-training', 'weakly-supervised-learning'],
    110: ['label-distribution-learning', 'pseudo-label-self-training', 'label-correlation-modeling', 'semi-supervised-learning'],
    111: ['hallucination-mitigation', 'sparse-representation', 'large-vision-language-models'],
    112: ['class-imbalance', 'noisy-label-learning'],
    113: ['graph-structure-learning', 'pairwise-constraint-propagation', 'partial-label-learning'],
    114: ['large-vision-language-models'],
    115: ['deep-clustering'],
    116: ['pseudo-label-self-training', 'classifier-ensemble', 'semi-supervised-learning', 'class-imbalance'],
    117: ['label-distribution-learning'],
    118: ['graph-structure-learning', 'pairwise-constraint-propagation', 'partial-label-learning', 'semi-supervised-learning'],
    119: ['multi-label-learning', 'label-distribution-learning', 'low-rank-modeling', 'label-correlation-modeling', 'noisy-label-learning'],
    120: ['deep-clustering', 'contrastive-learning', 'class-imbalance'],
    121: ['pseudo-label-self-training', 'weakly-supervised-learning'],
    122: ['multi-label-learning', 'confidence-calibration', 'weakly-supervised-learning'],
    123: ['partial-label-learning'],
    124: ['adversarial-robustness'],
    125: ['multi-label-learning', 'weakly-supervised-learning'],
    126: ['pseudo-label-self-training', 'partial-label-learning', 'semi-supervised-learning'],
    127: ['multi-label-learning', 'label-distribution-learning', 'low-rank-modeling', 'label-correlation-modeling'],
    128: ['label-distribution-learning', 'label-enhancement'],
    129: ['classifier-ensemble', 'partial-label-learning', 'class-imbalance'],
    130: ['traffic-data'],
    131: ['data-imputation-recovery', 'low-rank-modeling', 'traffic-data'],
    132: ['pairwise-constraint-propagation', 'partial-label-learning'],
    133: ['graph-manifold-regularization', 'partial-label-learning'],
    134: ['dimensionality-reduction', 'partial-label-learning'],
    135: ['adversarial-robustness'],
    136: ['deep-clustering', 'graph-neural-networks'],
    137: ['ensemble-clustering', 'low-rank-modeling'],
    138: ['pairwise-constraint-propagation', 'semi-supervised-learning'],
    139: ['dimensionality-reduction', 'graph-manifold-regularization', 'semi-supervised-learning'],
    140: ['multi-label-learning', 'label-correlation-modeling', 'classifier-ensemble'],
    141: ['bayesian-inference'],
    142: ['multi-objective-optimization'],
    143: [],
}
assert set(coverage_map)==set(range(144))

uncovered = {
 8:'标题明确无监督长尾基础模型学习；词表覆盖类别不平衡，但未单列无监督学习这一宽泛设定，且无法仅凭标题确认基础模型模态。',
 11:'标题可确认半监督设定；双重分布失配未独立成词，缺摘要不能细化失配类型。',
 19:'依用户要求删除剪接变异效应预测任务词；保留原有域适应候选，任务本身未覆盖。基因组基础模型未单列对象词，不等同于大语言模型。',
 30:'仅标题：城市建筑三维建模、无人机倾斜摄影与能耗仿真均未进入本轮49词；不能将其强配为高光谱或图像分割。',
 38:'交通数据恢复得到覆盖；交通状态估计未再单列为同维度细分任务。',
 54:'仅标题：半监督与低秩方法得到覆盖，未单列无参考图像质量评价任务。',
 67:'指数族输出建模与极限学习机为实质贡献，但本轮未单列；不能仅凭概率解释赋贝叶斯推断。',
 69:'贝叶斯推断已覆盖；计数数据回归未单列任务。',
 73:'半监督设定已覆盖；谱聚类未独立成词，不能强配为深度或子空间聚类。',
 75:'仅标题：方法得到覆盖，未单列社区发现任务。',
 76:'视频编码码率控制与合作博弈未收录；不能把多项优化目标直接当作帕累托多目标优化。',
 77:'生物网络相似性检索及随机森林回归未单列；不能因网络对象是图就将所用回归检索方法视为图神经网络。',
 81:'仅标题：明确的多标记任务与弱监督设定得到覆盖，弱监督具体类型和负多簇方法机制无法进一步确定。',
 89:'仅标题：大语言模型对象得到覆盖，医学问答及多图对齐未独立收录。',
 91:'仅标题：异步视频面试认知能力评估与问题级多模态融合未收录；不等同于多模态检索。',
 100:'仅标题：ViT注意力头交互分析未收录；单模态ViT不能直接归入视觉语言模型。',
 105:'神经聚类得到覆盖；用户语义驱动的多重聚类未单列，不能误用集成聚类。',
 114:'abstract字段仅为作者及会议信息，按标题审阅；只能确认视觉语言大模型幻觉分析主题，检测或抑制目标未决，不能归入幻觉抑制或推断头分歧具体方法。',
 117:'标签分布核心任务得到覆盖；绝对强度/背景浓度扩展未独立成词，也未当成LDL同义词。',
 130:'仅标题：交通对象得到覆盖，交通状态估计未单列；题名不足以推断低秩方法。',
 143:'图像边缘显著性检测及多尺度相位一致性方法未收录；不能把检测边缘强配为图像分割。'
}

coverage = []
for i,p in enumerate(papers):
    basis = 'title_only' if not p.get('abstract') or i==114 else 'title_and_abstract'
    coverage.append(dict(paper_id=p['id'], title=p['title'], reviewed=True,
        reviewed_fields=['title'] if basis=='title_only' else ['title','abstract'],
        evidence_basis=basis,
        candidate_keyword_ids=coverage_map[i],
        uncovered_reason=uncovered.get(i)))

excluded = [
 ('Splicing variant effect prediction','依用户要求删除独立任务词；该篇保留原有域适应候选，剪接变异效应预测任务本身未覆盖，不新增替代词。'),
 ('Artificial intelligence / Machine learning / Deep learning','不作为独立检索词：范围过宽，不能区分本文关心的问题。'),
 ('Unsupervised learning / Self-supervised learning','本轮未新增这两个上位设定；聚类任务及对比学习、伪标签等方法只覆盖部分实质方面，不宣称与它们等价或穷尽其范围。'),
 ('Partial multi-label learning','删除独立细分，以多标记学习与弱监督学习组合覆盖；不把偏多标记学习视为多标记学习的同义词。'),
 ('Complementary label learning / Incomplete-label supervision / Positive-unlabeled learning / Multiple-instance learning / Learning from label proportions','删除五个独立细分，以弱监督学习及有证据支持的任务、方法组合覆盖；互补、缺失、PU、包级和比例监督仍是不同条件，不互作同义词，粗词表不保留全部监督形式细节。'),
 ('Partial label learning / Noisy-label learning','保留独立词：候选集合中单一真标记的歧义与错误监督分别构成本语料反复研究的核心条件；新增弱监督上位词不要求移除有辨识度的密集方向。'),
 ('Hyperspectral unmixing','依用户要求删除独立任务词；高光谱图像已足够具体，相关论文由高光谱图像及实际方法覆盖，不声称对象词与解混任务同义。'),
 ('Multi-label classification','规范名改为Multi-label learning / 多标记学习，沿用原任务位置和证据，不另建重复词；分类、识别及多标签学习保留为该任务的通行同义表达。'),
 ('Large vision-language models','新增为视觉语言模型在研究对象维度的严格子项；明确LVLM或具有视觉输入的MLLM证据才使用子项，CLIP及一般VLM不自动升级。'),
 ('Long-tailed learning','按本轮粗粒度归入类别不平衡学习的严格子类型；不是别名，未另占词位。'),
 ('Tensor low-rank representation / Matrix low-rank approximation','低秩建模的具体形式，暂不另分词；不是彼此的同义词。'),
 ('Graph convolutional networks','图神经网络的子类型，未另占词位，不写入同义词。'),
 ('LoRA / Adapter tuning / Continuous prompt learning','参数高效微调的不同子类型，未各自拆词；保留对应实质论文证据，不写作互相同义，也不收入专属论文模型名。'),
 ('Superpixel segmentation / Semantic segmentation / Instance segmentation','在图像分割下合并覆盖的不同任务子类型，互不等价，未放入aliases。'),
 ('Distribution mismatch','域适应已单列；标注/未标注的类别分布失配不等于域适应，暂以半监督及类别不平衡覆盖已有方面，不能混为别名。'),
 ('Biological network similarity retrieval','内部论文有直接实质支持，但本轮未单列生物网络对象及网络相似性检索任务，coverage如实记录缺口。'),
 ('Cognitive ability assessment / Urban building modeling','各有内部论文标题直接支持，但缺摘要，本轮暂不增加特定应用词；已记录未覆盖，非判断为不相关。'),
 ('Medical question answering / Knowledge graph alignment','内部论文仅标题支持，待有摘要再细化任务与方法；大语言模型对象已保留。'),
 ('Rate control in video coding / Image quality assessment / Edge saliency detection / Count data regression','有对应内部记录，49词未完整保留所有历史任务；coverage逐篇明确，不能用相关任务代替。'),
 ('Vision Transformer attention-head interaction analysis','仅标题支持，不能以视觉语言模型替代；列为未覆盖分析方向。'),
 ('Uncertainty representation / Explainability / Efficient inference','相关表述不直接变成宽泛词；先保留有明确判定对象的校准、潜在推理、参数高效微调等。'),
 ('Agent / AI4Science / Hallucination detection','主页明确自述的兴趣；本语料未建立独立智能体或幻觉检测任务的直接论文支持，AI4Science亦过宽。不能由主页将其强加到正式词表。'),
]

def write(homepage_notes):
    counts = dict(Counter(t['primary_dimension'] for t in terms))
    metadata = dict(schema_version='1.1', stage='vocabulary_construction_only',
        keyword_count=len(terms), dimension_counts=counts,
        corpus=dict(paper_count=144, nonempty_abstract_count=114,
          substantive_abstract_count=113, title_only_count=31,
          invalid_abstract_paper_ids=[papers[114]['id']],
          truncated_abstract_paper_ids=[papers[110]['id']]),
        rules_zh=[
          '仅据受控目录中的实验室内部论文标题、摘要和主页相关文字构建；未读旧词表、生产分类、外部文献或记忆。',
          '词条要求是文章实质研究任务、采用方法、处理对象或学习设定；背景提及、引用、对比方法名称和泛泛未来展望不构成正向证据。',
          'primary_dimension与概念粒度分离；parent_id仅表达同维度的严格包含，其他相关性不充作父子或别名。',
          '聚类任务按希望得到的数据划分类型命名（如深度、子空间、集成聚类），方法按可复用的实现机制命名（如图神经网络、对比学习）；同篇可同时具有任务与方法词。',
          'aliases只存真正同义表达，不列上下位词、相关词或未消歧缩写；允许空列表。',
          '每词至少一篇内部论文直接支持；evidence仅为代表性例证，不是支撑论文穷举或逐篇最终标注。',
          'coverage-review只检查词表能否覆盖论文方向；candidate_keyword_ids不能作为最终标签发布，未产生人工置信度。',
          '31篇以标题为依据；其中1篇非空abstract实为文献引用。RankMatch摘要截断，使用现有实质部分，不补写。',
          '不要求每篇每个方面都落入当前词表；未覆盖方向明示，不能以背景泛词或误并概念追求100%覆盖。'
        ], homepage_notes=homepage_notes)
    (ROOT/'vocabulary.json').write_text(json.dumps(dict(metadata=metadata,keywords=terms),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    covout=dict(stage='vocabulary_coverage_review_not_final_annotation',
        paper_count=144, reviewed_count=len(coverage),
        papers_with_candidates=sum(bool(c['candidate_keyword_ids']) for c in coverage),
        papers_without_candidates=sum(not c['candidate_keyword_ids'] for c in coverage),
        warning_zh='candidate_keyword_ids仅为词表覆盖检查候选，不是第二阶段的论文最终标签；未覆盖原因也可能指出已有候选之外的缺失方面。',
        papers=coverage,
        excluded_or_merged_candidates=[dict(candidate=x,reason_zh=y) for x,y in excluded])
    (ROOT/'coverage-review.json').write_text(json.dumps(covout,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    dims=[(T,'研究任务'),(M,'采用方法'),(O,'研究对象'),(S,'学习设定')]
    md=['# 实验室关键词词表（第一阶段）','',
        f'共{len(terms)}词（新版）。来源为144篇当前实验室内部论文：113篇有实质摘要、31篇仅按标题判断（30篇空摘要，1篇摘要栏误填作者/会议信息）。另参照资料包内主页研究文字；论文实质证据优先。',
        '', '统一规则：只收文章实质研究的问题、采用的方法、处理的对象与学习设定；背景提及不匹配。维度与粒度分开，同义词不混入上下位或相关概念。聚类任务按所求划分类型区分，方法按可复用实现机制区分。同篇可涉及多维。每词有内部论文的精确连续原文证据，表内只列代表性论文，不声称穷举。标题证据只支持明确写出的内容。',
        '', '本阶段未给全部文献打标签。coverage-review.json的144条记录是逐篇覆盖检查，候选词不等于最终标签；遗漏的小方向有明确记录。',
        '', '主页处理：'+homepage_notes,'']
    display_no = 0
    for d,name in dims:
        md += ['## '+name+'（'+str(counts[d])+'词）','', '|序号|英文 / 中文|定义与判定边界|代表性内部论文|','|---|---|---|---|']
        for n,t in enumerate(terms,1):
            if t['primary_dimension']!=d: continue
            display_no += 1
            ids=list(dict.fromkeys(e['source_id'] for e in t['evidence'] if e['source_type']=='paper'))
            titles=[next(p['title'] for p in papers if p['id']==pid) for pid in ids]
            md.append(f"|{display_no}|{t['canonical_en']} / {t['canonical_zh']}|{t['definition_zh']}|"+'；'.join(titles)+'|')
        md.append('')
    md += ['## 新版取舍','',
        '|处理|词条与理由|','|---|---|',
        '|新增|弱监督学习承接监督信号不足或不可靠的粗粒度设定；视觉语言大模型单列为视觉语言模型子项，CLIP不自动计入。|',
        '|规范名称|多标记分类改为多标记学习，保留分类、识别等同义称呼，不重复建词。|',
        '|本次删项|依用户要求删除剪接变异效应预测，50词减为49词；该篇保留原有域适应候选，任务本身未覆盖。|',
        '|删除独立词|高光谱解混由高光谱对象及具体方法覆盖；偏多标记以多标记学习＋弱监督覆盖；互补标签、不完整标签、PU、多示例、标签比例收束到弱监督及对应任务/方法，不列作同义词。|',
        '|保留细分|偏标记与噪声标签在本组语料中反复作为核心研究条件，保持独立；半监督、类别不平衡、多视图、联邦、域适应、零样本、开放词表仍有独立检索价值。|','']
    md += ['## 合并与未覆盖边界','',
        '长尾作为类别不平衡的子类型、矩阵/张量低秩作为低秩建模的形式，均不冒充同义词。LoRA、连续提示学习合入参数高效微调的定义与证据；图卷积、不同分割任务也未重复占位。视觉语言大模型是视觉语言模型在研究对象维度的严格子项；其余词暂不显式设置父子关系。候选采用有证据支持的具体对象层级，父项不重复列入。',
        '', '未单列的实质方向包括剪接变异效应预测、生物网络相似性检索、视频编码码率控制、图像质量评价、边缘显著性检测及少数只有标题的新应用。它们仍是相关候选，不因本轮49词限制被判断为不相关；详见coverage-review.json逐篇缺口和候选处理理由。',
        '', '质量限制：Vision-aware Head Divergence一文仅使用标题；RankMatch摘要末尾截断，不推断缺失结论。未联网补充内容，未修改生产数据或页面。','']
    (ROOT/'vocabulary.md').write_text('\n'.join(md),encoding='utf-8')

if __name__=='__main__':
    write('已阅读贾育衡个人主页完整研究兴趣句及PALM介绍。个人自述用于核对半监督、大模型与可信学习语境；PALM广义介绍仅为背景。没有仅因主页提及而加入智能体、AI4Science或幻觉检测，也没有把幻觉抑制改名为检测。')
    print(json.dumps({'keywords':len(terms),'dimensions':dict(Counter(t['primary_dimension'] for t in terms)), 'papers':len(coverage)},ensure_ascii=False))
