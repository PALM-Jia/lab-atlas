# 两源重采集与旧版对照

分母为同一主页快照的 144 篇论文。旧版基于多源采用结果，新版仅采用主页和 OpenAlex。OpenAlex 实时更新也会造成差异，不能把全部增减归因于删去其他来源。

| 信息 | 旧版 | 新版 | 新增到位 | 失去到位 |
| --- | ---: | ---: | ---: | ---: |
| OpenAlex 身份 | 118 | 115 | 0 | 3 |
| 作者名单 | 138 | 137 | 0 | 1 |
| 年份 | 138 | 137 | 0 | 1 |
| 发表情况 | 138 | 137 | 0 | 1 |
| 摘要 | 114 | 100 | 0 | 14 |
| 被引数 | 122 | 115 | 0 | 7 |
| 非空参考名单 | 79 | 80 | 1 | 0 |
| 取得被引名单（含明确为空） | 118 | 115 | 0 | 3 |

| 名单详情匹配 | 旧版 | 新版 |
| --- | ---: | ---: |
| 引用文献 | 2449 / 3593（68.16%） | 3181 / 3626（87.73%） |
| 被引记录 | 2077 / 2077（100.00%） | 2048 / 2048（100.00%） |

这里的匹配率只针对 OpenAlex 已返回的名单 ID，不是对论文原始 PDF 的完整参考文献收集率。

## 逐步验收

| 步骤／字段 | 成功 | 可解释未完成 | 成功率 | 归宿覆盖率 |
| --- | ---: | ---: | ---: | ---: |
| 身份核对 | 115 | 29 | 79.86% | 100.00% |
| 摘要 | 100 | 44 | 69.44% | 100.00% |
| 数据库关键词 | 115 | 29 | 79.86% | 100.00% |
| 数据库主题 | 115 | 29 | 79.86% | 100.00% |
| 被引数 | 115 | 29 | 79.86% | 100.00% |
| 引用名单查询 | 115 | 29 | 79.86% | 100.00% |
| 被引名单查询 | 115 | 29 | 79.86% | 100.00% |
| 外部详情 | 3602 | 318 | 91.89% | 100.00% |

空列表算查询完成，不代表内容到位；非空名单数量单独在上表汇报。每个外部ID都执行补全；网络候选只保留至少连接2篇不同实验室论文的外部文献，再按连接数排序取最多1600篇。连接数依据完整直接引用／被引关系，在top-K与页面筛选之前计算；不会沿外部文献继续扩展。

新版取得 3602 个不同外部记录，图节点选择 707 个；旧图 1529 个，交集 703 个。

## 身份未确定项

仅列未完成项；成功项的逐篇详情保留在机器数据中。

### Noise Separation guided Candidate Label Reconstruction for Noisy Partial Label Learning

`lab-5403cb1aad23`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Noise+Separation+guided+Candidate+Label+Reconstruction+for+Noisy+Partial+Label+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Noise+Separation+guided+Candidate+Label+Reconstruction+for+Noisy+Partial+Label+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Noise+Separation+guided+Candidate+Label+Reconstruction+for+Noisy+Partial+Label&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Separation+guided+Candidate+Label+Reconstruction+for+Noisy+Partial+Label+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Semantic Noise Reduction via Teacher-Guided Dual-Path Audio-Visual Representation Learning（https://openalex.org/W7153201386）；标题 47.4%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Towards improved particle reconstruction for single-molecule localization microscopy using geometric deep learning（https://openalex.org/W7202248467）；标题 45.8%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Neural network architecture search for extreme classification and in a partially labeled learning context（https://openalex.org/W4392288063）；标题 45.0%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。

### Unsupervised Long-tailed Learning for Foundation Model

`lab-bb2d463fb71a`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Unsupervised+Long-tailed+Learning+for+Foundation+Model&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Unsupervised+Long-tailed+Learning+for+Foundation+Model&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Unsupervised+Long+tailed+Learning+for+Foundation+Model&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Unsupervised Post-Training of Foundation Models: A Survey（https://openalex.org/W7204476104）；标题 74.2%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：A Survey of Deep Active Learning for Foundation Models（https://openalex.org/W4388296405）；标题 68.1%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Unsupervised Long-Tailed Adaptation of Vision-Language Models（https://openalex.org/W7220923077）；标题 66.7%；作者交集 0；拒绝：title_similarity_below_rule,substantive_title_word_substitution。

### PEEK: Partial Label Learning Empowered by External Knowledge

`lab-088383584e44`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=PEEK%3A+Partial+Label+Learning+Empowered+by+External+Knowledge&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=PEEK%3A+Partial+Label+Learning+Empowered+by+External+Knowledge&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Partial+Label+Learning+Empowered+by+External+Knowledge&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Research Frontiers in Machine Learning & Knowledge Extraction（https://openalex.org/W7117764744）；标题 47.6%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：CAMA: Enhancing Mathematical Reasoning in Large Language Models with Causal Knowledge（https://openalex.org/W7138862905）；标题 46.0%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：AI applications to medical images: From machine learning to deep learning（https://openalex.org/W3135096391）；标题 42.1%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。

### Attribute Distribution Modeling and Semantic-Visual Alignment for Generative Zero-shot Learning

`lab-1ba64af37485`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Attribute+Distribution+Modeling+and+Semantic-Visual+Alignment+for+Generative+Zero-shot+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Attribute+Distribution+Modeling+and+Semantic-Visual+Alignment+for+Generative+Zero-shot+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Attribute+Distribution+Modeling+and+Semantic+Visual+Alignment+for+Generative+Zero+shot+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Attribute+Distribution+Modeling+and+Semantic+Visual+Alignment+for+Generative+Zero&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Modeling+and+Semantic+Visual+Alignment+for+Generative+Zero+shot+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Learning Adaptive and Visually Aligned Conditions for Generative Zero-Shot Learning（https://openalex.org/W7134273068）；标题 66.2%；作者交集 0；拒绝：title_similarity_below_rule,substantive_title_word_substitution。
- 候选：Learning Discriminative Projection With Visual Semantic Alignment for Generalized Zero Shot Learning（https://openalex.org/W3083772902）；标题 65.9%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Bi-Directional Distribution Alignment for Transductive Zero-Shot Learning（https://openalex.org/W4386071542）；标题 63.1%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。

### Hub for Outliers, Spokes for Inliers: Homeomorphic Latent Space Construction for Dual-Mismatched Semi-Supervised Learning

`lab-a07279b34373`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Hub+for+Outliers%2C+Spokes+for+Inliers%3A+Homeomorphic+Latent+Space+Construction+for+Dual-Mismatched+Semi-Supervised+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Hub+for+Outliers%2C+Spokes+for+Inliers%3A+Homeomorphic+Latent+Space+Construction+for+Dual-Mismatched+Semi-Supervised+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Homeomorphic+Latent+Space+Construction+for+Dual-Mismatched+Semi-Supervised+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Homeomorphic+Latent+Space+Construction+for+Dual+Mismatched+Semi+Supervised+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations

### Beyond Low-Rank: A Region-Aware Imputation Method for Traffic Data Recovery

`lab-3af81cff7068`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Beyond+Low-Rank%3A+A+Region-Aware+Imputation+Method+for+Traffic+Data+Recovery&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Beyond+Low-Rank%3A+A+Region-Aware+Imputation+Method+for+Traffic+Data+Recovery&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=A+Region-Aware+Imputation+Method+for+Traffic+Data+Recovery&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=A+Region+Aware+Imputation+Method+for+Traffic+Data+Recovery&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Low-Rank Adaptation Redux for Large Models（https://openalex.org/W7155530850）；标题 52.5%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Multilinear Kernel Regression and Imputation via Manifold Learning（https://openalex.org/W4401607314）；标题 42.6%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Mechanistic and Data-Adaptive Bayesian Methods for Scientific Inference（https://openalex.org/W4378345697）；标题 41.3%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。

### Hyerspectral Image Clustering with Local Sparse Subspace guided Super-Graph Construction

`lab-8ef4decb9b26`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Hyerspectral+Image+Clustering+with+Local+Sparse+Subspace+guided+Super-Graph+Construction&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Hyerspectral+Image+Clustering+with+Local+Sparse+Subspace+guided+Super-Graph+Construction&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Hyperspectral+Image+Clustering+with+Local+Sparse+Subspace+guided+Super-Graph+Construction&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Hyperspectral+Image+Clustering+with+Local+Sparse+Subspace+guided+Super+Graph+Construction&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Hyperspectral+Image+Clustering+with+Local+Sparse+Subspace+guided+Super+Graph&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Image+Clustering+with+Local+Sparse+Subspace+guided+Super+Graph+Construction&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations

### Adaptive Graph Feedback Clustering Network

`lab-7af4622bbcc3`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Adaptive+Graph+Feedback+Clustering+Network&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Adaptive+Graph+Feedback+Clustering+Network&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Federated Graph-Level Clustering Network（https://openalex.org/W4409363832）；标题 70.3%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Attribute-Missing Graph Clustering Network（https://openalex.org/W4393159789）；标题 68.4%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Adaptive dynamical networks（https://openalex.org/W4386426569）；标题 57.1%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。

### Towards Robust Models: Mitigating Adversarial Shifts in Feature Statistics with Uncertainty-Aware Reconstruction

`lab-9ddc9ff7ce0c`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Towards+Robust+Models%3A+Mitigating+Adversarial+Shifts+in+Feature+Statistics+with+Uncertainty-Aware+Reconstruction&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Towards+Robust+Models%3A+Mitigating+Adversarial+Shifts+in+Feature+Statistics+with+Uncertainty-Aware+Reconstruction&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Mitigating+Adversarial+Shifts+in+Feature+Statistics+with+Uncertainty-Aware+Reconstruction&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Mitigating+Adversarial+Shifts+in+Feature+Statistics+with+Uncertainty+Aware+Reconstruction&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Conditional Generative Adversarial Networks for Subsurface Scenario-Based Uncertainty（https://openalex.org/W4415001200）；标题 46.6%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Towards Robust Uncertainty-Aware Incomplete Multi-View Classification（https://openalex.org/W4403589299）；标题 46.0%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Toward Robust Video Event Detection and Retrieval Under Adversarial Constraints（https://openalex.org/W2561670236）；标题 45.0%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。

### Graph-based Clustering Revisited: A Relaxation of Kernel k-Means Perspective

`lab-cb0529713b81`：ambiguous — multiple_verified_candidates_without_unique_version

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Graph-based+Clustering+Revisited%3A+A+Relaxation+of+Kernel+k-Means+Perspective&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Graph-based+Clustering+Revisited%3A+A+Relaxation+of+Kernel+k-Means+Perspective&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=A+Relaxation+of+Kernel+k-Means+Perspective&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=A+Relaxation+of+Kernel+k+Means+Perspective&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Graph-based Clustering Revisited: A Relaxation of Kernel $k$-Means Perspective（https://openalex.org/W4415251433）；标题 100.0%；作者交集 3；拒绝：。
- 候选：Graph-based Clustering Revisited:A Relaxation of Kernel k-Means Perspective（https://openalex.org/W7204219493）；标题 100.0%；作者交集 3；拒绝：。
- 候选：Graph-based methods for unsupervised and semi-supervised data analysis（https://openalex.org/W2591281590）；标题 47.6%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。

### Similarity and Dissimilarity Guided Co-association Matrix Construction for Ensemble Clustering

`lab-8a85b44117f4`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Similarity+and+Dissimilarity+Guided+Co-association+Matrix+Construction+for+Ensemble+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Similarity+and+Dissimilarity+Guided+Co-association+Matrix+Construction+for+Ensemble+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Similarity+and+Dissimilarity+Guided+Co+association+Matrix+Construction+for+Ensemble+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Similarity+and+Dissimilarity+Guided+Co+association+Matrix+Construction+for+Ensemble&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=and+Dissimilarity+Guided+Co+association+Matrix+Construction+for+Ensemble+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：A Family of Divergence Measures for Evaluating the Reconstruction Quality of Explainable Ensemble Trees（https://openalex.org/W7161850834）；标题 46.0%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Functional group classification using consensus clustering（https://openalex.org/W7160992807）；标题 45.3%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Optimized Python library for reconstruction of ensemble-based gene co-expression networks using multi-GPU（https://openalex.org/W4396832393）；标题 41.1%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。

### PGSB: Pretrained-Guided Shared Basis for LoRA Model Merging

`lab-dccd5bfa936b`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=PGSB%3A+Pretrained-Guided+Shared+Basis+for+LoRA+Model+Merging&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=PGSB%3A+Pretrained-Guided+Shared+Basis+for+LoRA+Model+Merging&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Pretrained-Guided+Shared+Basis+for+LoRA+Model+Merging&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Pretrained+Guided+Shared+Basis+for+LoRA+Model+Merging&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations

### Exploiting Negative Multi-Cluster Structure in Class-Wise Embeddings for Weakly Supervised Multi-Label Learning

`lab-e73ac884ede0`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Exploiting+Negative+Multi-Cluster+Structure+in+Class-Wise+Embeddings+for+Weakly+Supervised+Multi-Label+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Exploiting+Negative+Multi-Cluster+Structure+in+Class-Wise+Embeddings+for+Weakly+Supervised+Multi-Label+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Exploiting+Negative+Multi+Cluster+Structure+in+Class+Wise+Embeddings+for+Weakly+Supervised+Multi+Label+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Exploiting+Negative+Multi+Cluster+Structure+in+Class+Wise+Embeddings+for&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=in+Class+Wise+Embeddings+for+Weakly+Supervised+Multi+Label+Learning&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Bringing Clustering to MLL: Weakly-Supervised Clustering for Partial Multi-Label Learning（https://openalex.org/W7154183346）；标题 57.5%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Context-Based Semantic-Aware Alignment for Semi-Supervised Multi-Label Learning（https://openalex.org/W4405900660）；标题 56.6%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Fine-Grained Multi-label Sexism Classification Using a Semi-Supervised Multi-level Neural Approach（https://openalex.org/W3193949653）；标题 53.8%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。

### Individuals Matter: Improving Deep Multi-View Clustering via Explicit Single-View Enhancement

`lab-1025a6d4de24`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Individuals+Matter%3A+Improving+Deep+Multi-View+Clustering+via+Explicit+Single-View+Enhancement&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Individuals+Matter%3A+Improving+Deep+Multi-View+Clustering+via+Explicit+Single-View+Enhancement&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Improving+Deep+Multi-View+Clustering+via+Explicit+Single-View+Enhancement&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Improving+Deep+Multi+View+Clustering+via+Explicit+Single+View+Enhancement&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Prismatic: Interactive Multi-View Cluster Analysis of Concept Stocks（https://openalex.org/W4410087279）；标题 51.4%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Improved Multi-View Graph Clustering with Global Graph Refinement（https://openalex.org/W4414281963）；标题 50.7%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Geometric-driven Scalable Multi-view Subspace Clustering with View Rarity Analysis（https://openalex.org/W7204947551）；标题 45.8%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。

### AdapMatch: Adaptive Bias Decoupling for Semi-Supervised Partial Label Learning under Unknown Class Distributions

`lab-effcb20ed6d4`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=AdapMatch%3A+Adaptive+Bias+Decoupling+for+Semi-Supervised+Partial+Label+Learning+under+Unknown+Class+Distributions&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=AdapMatch%3A+Adaptive+Bias+Decoupling+for+Semi-Supervised+Partial+Label+Learning+under+Unknown+Class+Distributions&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Adaptive+Bias+Decoupling+for+Semi-Supervised+Partial+Label+Learning+under+Unknown+Class+Distributions&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Adaptive+Bias+Decoupling+for+Semi+Supervised+Partial+Label+Learning+under+Unknown+Class+Distributions&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Adaptive+Bias+Decoupling+for+Semi+Supervised+Partial+Label+Learning+under&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=for+Semi+Supervised+Partial+Label+Learning+under+Unknown+Class+Distributions&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations

### Progressive Pseudo-label Self-balancing Towards Unsupervised Vision-Language Models Adaptation

`lab-2110e10b1fd2`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Progressive+Pseudo-label+Self-balancing+Towards+Unsupervised+Vision-Language+Models+Adaptation&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Progressive+Pseudo-label+Self-balancing+Towards+Unsupervised+Vision-Language+Models+Adaptation&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Progressive+Pseudo+label+Self+balancing+Towards+Unsupervised+Vision+Language+Models+Adaptation&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Progressive+Pseudo+label+Self+balancing+Towards+Unsupervised+Vision+Language+Models&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Pseudo+label+Self+balancing+Towards+Unsupervised+Vision+Language+Models+Adaptation&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：SelfPrompt: Confidence-Aware Semi-Supervised Tuning for Robust Vision-Language Model Adaptation（https://openalex.org/W4406840674）；标题 58.7%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Robust Pseudo-label Learning with Neighbor Relation for Unsupervised Visible-Infrared Person Re-Identification（https://openalex.org/W4403791524）；标题 56.4%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：DPA: Dual Prototypes Alignment for Unsupervised Adaptation of Vision-Language Models（https://openalex.org/W4409263171）；标题 56.1%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。

### LoCo: Selective Local Competition for Discriminative Open-Vocabulary Multi-Label Recognition

`lab-5dda1e979492`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=LoCo%3A+Selective+Local+Competition+for+Discriminative+Open-Vocabulary+Multi-Label+Recognition&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=LoCo%3A+Selective+Local+Competition+for+Discriminative+Open-Vocabulary+Multi-Label+Recognition&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Selective+Local+Competition+for+Discriminative+Open-Vocabulary+Multi-Label+Recognition&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Selective+Local+Competition+for+Discriminative+Open+Vocabulary+Multi+Label+Recognition&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：ImageNet Large Scale Visual Recognition Challenge（https://openalex.org/W2546241758）；标题 33.6%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。
- 候选：A cross cultural study of disability in the United States and Brazil（https://openalex.org/W2137273641）；标题 31.9%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。
- 候选：Morphological processing in the brain: The good (inflection), the bad (derivation) and the ugly (compounding)（https://openalex.org/W2889294614）；标题 28.6%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。

### Attention Heads are Complementary Visual Units: Mitigating Hallucinations in LVLMs via Adaptive Visual Cues Focusing

`lab-deff0ac02cbd`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Attention+Heads+are+Complementary+Visual+Units%3A+Mitigating+Hallucinations+in+LVLMs+via+Adaptive+Visual+Cues+Focusing&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Attention+Heads+are+Complementary+Visual+Units%3A+Mitigating+Hallucinations+in+LVLMs+via+Adaptive+Visual+Cues+Focusing&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Mitigating+Hallucinations+in+LVLMs+via+Adaptive+Visual+Cues+Focusing&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：V-Loop: Visual Logical Loop Verification for Hallucination Detection in Medical Visual Question Answering（https://openalex.org/W7125785291）；标题 47.9%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Relaxing Anchor-Frame Dominance for Mitigating Hallucinations in Video Large Language Models（https://openalex.org/W7154451413）；标题 45.1%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Grounding or Guessing? Visual Signals for Detecting Hallucinations in Sign Language Translation（https://openalex.org/W4416056156）；标题 42.4%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。

### Mismatch-Free One-Step at Scale: Linear-Time Ensemble Clustering with Soft Balancing

`lab-6757df585f08`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Mismatch-Free+One-Step+at+Scale%3A+Linear-Time+Ensemble+Clustering+with+Soft+Balancing&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Mismatch-Free+One-Step+at+Scale%3A+Linear-Time+Ensemble+Clustering+with+Soft+Balancing&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Linear-Time+Ensemble+Clustering+with+Soft+Balancing&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Linear+Time+Ensemble+Clustering+with+Soft+Balancing&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：On the Response of Proteinoid Ensembles to Fibonacci Sequences（https://openalex.org/W4408157976）；标题 43.2%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：The ONETEP linear-scaling density functional theory program（https://openalex.org/W3021204671）；标题 40.7%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。
- 候选：NeoMutate: an ensemble machine learning framework for the prediction of somatic mutations in cancer（https://openalex.org/W2947555888）；标题 38.5%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。

### KGFlow: Enhancing Large Language Model Reasoning with Multi-Graph Alignment for Knowledge-Intensive Medical Question Answering

`lab-1a90fc2c3965`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=KGFlow%3A+Enhancing+Large+Language+Model+Reasoning+with+Multi-Graph+Alignment+for+Knowledge-Intensive+Medical+Question+Answering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=KGFlow%3A+Enhancing+Large+Language+Model+Reasoning+with+Multi-Graph+Alignment+for+Knowledge-Intensive+Medical+Question+Answering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Enhancing+Large+Language+Model+Reasoning+with+Multi-Graph+Alignment+for+Knowledge-Intensive+Medical+Question+Answering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Enhancing+Large+Language+Model+Reasoning+with+Multi+Graph+Alignment+for+Knowledge+Intensive+Medical+Question+Answering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Enhancing+Large+Language+Model+Reasoning+with+Multi+Graph+Alignment+for&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=with+Multi+Graph+Alignment+for+Knowledge+Intensive+Medical+Question+Answering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations

### Question-Level Multimodal Fusion for Cognitive Ability Assessment in Asynchronous Video Interviews

`lab-4dafc16e5fd8`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Question-Level+Multimodal+Fusion+for+Cognitive+Ability+Assessment+in+Asynchronous+Video+Interviews&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Question-Level+Multimodal+Fusion+for+Cognitive+Ability+Assessment+in+Asynchronous+Video+Interviews&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Question+Level+Multimodal+Fusion+for+Cognitive+Ability+Assessment+in+Asynchronous+Video+Interviews&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Question+Level+Multimodal+Fusion+for+Cognitive+Ability+Assessment+in+Asynchronous&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Multimodal+Fusion+for+Cognitive+Ability+Assessment+in+Asynchronous+Video+Interviews&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：EMMR: Emotion-Mediated Multimodal Reasoning for Personality Assessment in Asynchronous Video Interviews（https://openalex.org/W7202187509）；标题 77.5%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：AVI-Personality: A Trait-Activated Multimodal Dataset for Personality and Competency Assessment in Asynchronous Video Interviews（https://openalex.org/W7204464735）；标题 65.3%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Multi-Modal Method for Candidate Interview Assessment Based on Computer Vision and Large Language Models（https://openalex.org/W7146985806）；标题 49.7%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。

### One Coin Has Two Sides: Single Poistive Multi Label Learning from Salient Annotations

`lab-b4f457369e13`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=One+Coin+Has+Two+Sides%3A+Single+Poistive+Multi+Label+Learning+from+Salient+Annotations&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=One+Coin+Has+Two+Sides%3A+Single+Poistive+Multi+Label+Learning+from+Salient+Annotations&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=One+Coin+Has+Two+Sides%3A+Single+Positive+Multi+Label+Learning+from+Salient+Annotations&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Single+Positive+Multi+Label+Learning+from+Salient+Annotations&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations

### Mini-cluster Guided Long-tailed Deep Clustering

`lab-77b725acea33`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Mini-cluster+Guided+Long-tailed+Deep+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Mini-cluster+Guided+Long-tailed+Deep+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Mini+cluster+Guided+Long+tailed+Deep+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Inducing Neural Collapse in Deep Long-tailed Learning（https://openalex.org/W4322616360）；标题 57.5%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。
- 候选：Sampling for Large-Scale Clustering（https://openalex.org/W2907528359）；标题 55.6%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。
- 候选：A Systematic Review on Long-Tailed Learning（https://openalex.org/W4401307342）；标题 53.8%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。

### Samples Are Not Equal: A Sample Selection Approach for Deep Clustering

`lab-918df170a3ad`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Samples+Are+Not+Equal%3A+A+Sample+Selection+Approach+for+Deep+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Samples+Are+Not+Equal%3A+A+Sample+Selection+Approach+for+Deep+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=A+Sample+Selection+Approach+for+Deep+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Synthetic Sample Selection for Generalized Zero-Shot Learning（https://openalex.org/W4385815555）；标题 47.8%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。
- 候选：Computerized stratified random site-selection approaches for design of a ground-water-quality sampling network（https://openalex.org/W2140714829）；标题 47.7%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。
- 候选：Weak Supervision and Clustering-Based Sample Selection for Clinical Named Entity Recognition（https://openalex.org/W4386798399）；标题 45.7%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。

### Learning from Sample Stability for Deep Clustering

`lab-82a7992c094e`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Learning+from+Sample+Stability+for+Deep+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Learning+from+Sample+Stability+for+Deep+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Learning to Discover Novel Visual Categories via Deep Transfer Clustering（https://openalex.org/W2990604239）；标题 55.6%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。
- 候选：Deep Learning for Short-Term Voltage Stability Assessment of Power Systems（https://openalex.org/W3129175333）；标题 53.7%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。
- 候选：Deep Learning-Based Dynamic Stable Cluster Head Selection in VANET（https://openalex.org/W3181874253）；标题 51.5%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。

### ConMix: Contrastive Mixup at Representation Level for Long-tailed Deep Clustering

`lab-bddb535117ca`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=ConMix%3A+Contrastive+Mixup+at+Representation+Level+for+Long-tailed+Deep+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=ConMix%3A+Contrastive+Mixup+at+Representation+Level+for+Long-tailed+Deep+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Contrastive+Mixup+at+Representation+Level+for+Long-tailed+Deep+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Contrastive+Mixup+at+Representation+Level+for+Long+tailed+Deep+Clustering&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：A Square Peg in a Square Hole: Meta-Expert for Long-Tailed Semi-Supervised Learning（https://openalex.org/W4416450637）；标题 47.8%；作者交集 1；拒绝：title_similarity_below_rule,substantive_title_word_substitution。
- 候选：OFBD: Object-Focused Background Debiasing for Long-Tailed Learning（https://openalex.org/W7214911135）；标题 40.9%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：You Can Trust Your Clustering Model: A Parameter-free Self-Boosting Plug-in for Deep Clustering（https://openalex.org/W4416786370）；标题 36.2%；作者交集 1；拒绝：title_similarity_below_rule,substantive_title_word_substitution。

### Complementary Label Learning with Positive Label Guessing and Negative Label Enhancement

`lab-2c640db3fd61`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Complementary+Label+Learning+with+Positive+Label+Guessing+and+Negative+Label+Enhancement&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Complementary+Label+Learning+with+Positive+Label+Guessing+and+Negative+Label+Enhancement&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Complementary+Label+Learning+with+Positive+Label+Guessing+and+Negative+Label&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Label+Learning+with+Positive+Label+Guessing+and+Negative+Label+Enhancement&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Enhancing Label Sharing Efficiency in Complementary-Label Learning with Label Augmentation（https://openalex.org/W4376653814）；标题 50.6%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Complementary-Label Learning: A Survey of Methods, an Open-Source Toolkit, and Fair Benchmarking Results（https://openalex.org/W7218852040）；标题 43.6%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Robust Data Programming with Precision-guided Labeling Functions（https://openalex.org/W3034712684）；标题 43.0%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。

### Efficient and Robust Freeway Traffic State Estimation under Oblique Grid using Vehicle Trajectory Data

`lab-cafae06c3f4f`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Efficient+and+Robust+Freeway+Traffic+State+Estimation+under+Oblique+Grid+using+Vehicle+Trajectory+Data&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=Efficient+and+Robust+Freeway+Traffic+State+Estimation+under+Oblique+Grid+using+Vehicle+Trajectory+Data&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Efficient+and+Robust+Freeway+Traffic+State+Estimation+under+Oblique+Grid&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Traffic+State+Estimation+under+Oblique+Grid+using+Vehicle+Trajectory+Data&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Efficient and Robust Freeway Traffic Speed Estimation Under Oblique Grid Using Vehicle Trajectory Data（https://openalex.org/W4400525194）；标题 96.6%；作者交集 3；拒绝：substantive_title_word_substitution,different_publication_venue。
- 候选：Efficient and Safe Strategies for Intersection Management: A Review（https://openalex.org/W3158955455）；标题 44.9%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution,different_publication_venue。
- 候选：Traffic state estimation based on Eulerian and Lagrangian observations in a mesoscopic modeling framework（https://openalex.org/W2604574479）；标题 44.2%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution,different_publication_venue。

### When Missingness Meets Anomalies: A Tailored Low-rank Tensor Completion Approach for Traffic Data Recovery

`lab-60280e69a6e3`：unmatched — no_candidate_passed_identity_rules

实际查询：
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=When+Missingness+Meets+Anomalies%3A+A+Tailored+Low-rank+Tensor+Completion+Approach+for+Traffic+Data+Recovery&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search=When+Missingness+Meets+Anomalies%3A+A+Tailored+Low-rank+Tensor+Completion+Approach+for+Traffic+Data+Recovery&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=A+Tailored+Low-rank+Tensor+Completion+Approach+for+Traffic+Data+Recovery&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=A+Tailored+Low+rank+Tensor+Completion+Approach+for+Traffic+Data+Recovery&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=A+Tailored+Low+rank+Tensor+Completion+Approach+for+Traffic+Data&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- HTTP 200；response_received；https://api.openalex.org/works?per_page=50&search.title=Tailored+Low+rank+Tensor+Completion+Approach+for+Traffic+Data+Recovery&select=id%2Ctitle%2Cdoi%2Cids%2Ctype%2Cpublication_year%2Cauthorships%2Cprimary_location%2Clocations
- 候选：Applied Mathematics in Integrative Research: Quantitative and Computational Approaches（https://openalex.org/W4414828282）；标题 44.0%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：An Assessment of the Sustainability of Electricity Consumption among European Countries. A Multistage Network Data Envelopment Analysis（https://openalex.org/W7113584181）；标题 40.2%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,substantive_title_word_substitution。
- 候选：Leveraging Sparsity and Low Rank for Large-Scale Networks and Data Science（https://openalex.org/W2273844344）；标题 39.0%；作者交集 0；拒绝：title_similarity_below_rule,insufficient_author_corroboration,publication_year_outside_tolerance,substantive_title_word_substitution。

## 范围与剩余产出

身份与详情没有 AI 兜底，没有查询 Semantic Scholar、Crossref、Scholar 或论文发布页。人员名字与 OpenAlex 作者 ID 分开保存；无 ID 的署名只保持逐篇 occurrence，不按同名合并。人员分类需要带实验室证据的逐篇人员对应表，未确认项进入队列。

关键词任务是新文本与固定词表的独立派生步骤，不属于事实补缺。任务准备、已生成、空标注与失败分别记状态，不将旧标注当成新结果。网页尚未接入新版；当前页面仍读取旧发布快照。

## 自动执行结果

向量 851/851；关键词复用完成 696/851（81.8%），待标注 155。

关键词逐项结果：exact_input_reuse：662；format_only_reanchored：34；no_previous_input：4；previous_annotation_not_accepted：21；title_or_abstract_changed：130。

人员共 688 条逐篇署名；明确人员对应 681 条，待处理 2 条。当前 205 个临时人员键的画像均按实际依赖状态标记，不作为最终去重名单。

例行入口不请求AI模型。人员对应和剩余关键词有独立任务队列；带规则、代码、原始输入及响应指纹的候选结果通过校验后独立冻结。网络与检索页面仍使用旧发布快照。
