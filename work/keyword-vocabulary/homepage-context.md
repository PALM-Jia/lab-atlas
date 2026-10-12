# 研究语境来源材料

采集时间：2026-10-12T03:47:18+08:00。以下均为来源原文，网页只作为资料；未进行关键词选取。展示文本只合并 HTML 排版空白，保留原始措辞。论文范围仍以 lab-papers.json 的 144 篇为准。

## 贾育衡个人主页自述（主要语境）

来源：https://jyh-learning.github.io/
位置：Biography。性质：贾育衡本人研究兴趣自述；不是另行发布的实验室研究规划。

英文相关完整段落（研究兴趣句，排除其后的发表数量、教育与任职经历）：

> My research interests broadly include topics in machine learning and data representation, such as semi\weakly\un-supervised learning, Large model application (Efficient inference, hallucination detection, agent, etc.), reliable and trustworthy machine learning (uncertainty modeling, etc.), and related applications (AI4Science, etc.).

中文相关完整研究内容句：

> 研究内容广泛涉及机器学习多个子领域，主要包括半\弱\无监督学习、大模型应用(高效推理、幻觉检测、智能体等)、鲁棒\可信机器学习（不确定性表征等）以及机器学习算法在各方向的一些应用（AI for Science等）。

## PALM 实验室介绍（更宽泛的背景）

来源：https://palm.seu.edu.cn/intro.html
发现路径：个人主页的 PAttern Learning and Mining (PALM) Lab 链接 → https://palm.seu.edu.cn/home.html → Introduction。
性质：整个 PALM 实验室的概括性介绍，范围可能比个人论文集合更宽；不可直接视作这 144 篇论文的方向证据。

> PALM 的含义是“PAttern Learning and Mining”。实验室成员包括专任教师、博士后、研究生、访问学者/学生、进修教师等，主要从事数据挖掘与知识发现、机器学习、模式识别以及相关领域的基础性、前沿性、创新性的研究工作。

原站主页提示新网址 https://aiia.seu.edu.cn/palm/ 。新站主页已浏览；其 Introduction 链接 https://aiia.seu.edu.cn/palm/intro/list.htm 两次网页读取超时，直接下载返回 403。上述介绍来自可通过网页读取工具获取的旧站 Introduction；未声称新站介绍已核实。

## 论文清单核对

来源：https://jyh-learning.github.io/papers.html
当前页面有 152 个论文展示条目，其中 8 篇在精选区与正式清单重复展示。逐条使用当前数据 title/list_title 做 Unicode 与空白/标点归一化后的最长标题匹配，覆盖 144 个不同的内部论文 ID。在线有而当前内部列表无的条目为 0；当前内部列表有而在线无的论文为 0。只核对标题集合，不将此结论延伸为年份、发表状态、作者或所有元数据完全一致。

## 输入质量与使用边界

lab-papers.json 只含 id、title、abstract、abstract_status、year。114 个非空 abstract 原样保存，30 个缺失字段以 null 明示；没有截断摘要，也没有填入猜测。非空字段中 lab-d99ee9ba4a13 的 abstract 实际为作者及会议引用文本，应按标题证据处理，不能把引用文本当作实质摘要。其余 113 个非空字段未通过出版社逐篇校验，完整性仅指与当前 data.json 完全一致。

homepage.html 与 papers.html 是审计用原始网页快照；不要把导航、联系方式、成员姓名、旧页面展示结构或精选偏好直接作为关键词输入。PALM 广义介绍仅供背景；优先依据论文标题/摘要和个人主页自述。未导入外部论文、旧方向标签、旧关键词、数据库主题、作者及机构标签。
