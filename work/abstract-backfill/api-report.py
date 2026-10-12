import json,collections,urllib.parse
from pathlib import Path
OUT=Path(__file__).resolve().parent
d=json.loads((OUT/'merged-abstracts.json').read_text(encoding='utf8'));s=d['summary'];manifest={x['id']:x for x in json.loads((OUT/'api-manifest.json').read_text(encoding='utf8'))}
labels={'candidate_requires_review':'身份或版本待核对','unresolved_pages_not_queried':'未查到可用原页入口','unresolved_after_page_attempt':'页面未提取到合格摘要','unresolved_access_limited':'访问受限或接口限流'}
review={
'lab-a07279b34373':'原列表 Homeomorphic 与 arXiv Uniform 标题不同，列表无作者或公开标识交叉证明；保留候选。',
'lab-cafae06c3f4f':'Traffic State 与候选 Traffic Speed 标题、作者清单有差异；存在既有身份冲突提示，保留候选。',
'W4301861531':'目标为1989年Springer书籍 DOI 10.1007/978-1-4899-3242-6；候选 DOI 10.2307/2344614 属另一年份记录，不把同名摘要当作该书摘要。',
'W4399400619':'目标 SSRN 预印本 DOI 10.2139/ssrn.4854529，缓存候选为 IEEE 正式出版 DOI 10.1109/TCSVT.2024.3492814；没有版本摘要等同性证据。',
'W2008499862':'目标1998年 DOI 10.1007/978-1-4615-5563-6，候选 DOI 10.1007/978-3-0348-8280-4 且年份不同；同名并不足以核对版本。',
'W2069323107':'目标 IEEE DOI 10.1109/TASSP.1984.1164450 作者 L. R. Rabiner；候选 DOI 10.2307/2322374 是另一条同名记录，不能移用摘要。'}
failed=[x for x in d['results']if x['status']!='success']
lines=['# 摘要补缺结果','',f'本轮目标337篇，核对后补回{s["backfilled"]}篇：内部{s["backfilled_lab"]}篇、外部{s["backfilled_external"]}篇。剩余{s["remaining"]}篇：内部{s["remaining_lab"]}篇、外部{s["remaining_external"]}篇。',f'全量1673篇中现有{s["all_with_abstract"]}篇非空摘要；其中1336篇沿用原数据，明确标记“未逐篇重新核验”。','', '采用来源均保留原始响应/HTML、提取方式和身份核对理由；没有生成、翻译或拼接摘要。128篇按节点ID去重，不重复累计同篇多个来源。','', '本轮仅生成独立补缺结果和下一步输入；生产data.json、关系网络、向量和关键词均未修改。','', '| 剩余原因 | 篇数 |','|---|---:|']
for k,label in labels.items():lines.append(f'| {label} | {sum(x["status"]==k for x in failed)} |')
lines+=['','“页面未提取到合格摘要”不等同于论文没有摘要。域名访问被拒后不逐篇重复请求；Semantic Scholar 初次限流后冷却超过120秒再探测，前两批200仍无新摘要，第三批429即停止。OpenAlex批量正常查询但没有新增可接受摘要。','', '原数据 lab-d99ee9ba4a13 的摘要实际为作者和会议引用串；已拒绝，保留 invalid_original 审计字段，并替换为 ACL Anthology 官方完整摘要。首次缓存误判已在 api-results.json 中纠正。','', '最初19项候选经人工核查：10项是明显不同论文，已明确拒绝；3项通过目标DOI正确Springer章节页补回；剩余6项身份/版本证据不足。另有4篇旧ISBN章节在校正原页路径后补回。两篇同名Generalized Linear Models分别核对，未混用。','', 'Crossref曾作为短暂后备试查，遵照范围收窄已停止；最终采用的Crossref摘要为0。','', '输出：','', '- all-papers-with-abstracts.json：1673项，字段仅 id/title/abstract/lab/abstract_source/quality/status，未携带旧关键词。','- merged-abstracts.json：337项完整账本，含查询路径、HTTP状态、采用/拒绝候选、原文存档和剩余原因。','- failures.md：仅209项未成功记录，含具体路径失败/未查询原因。','- identity-review.md：最终6项身份/版本待核对说明。','']
(OUT/'summary.md').write_text('\n'.join(lines),encoding='utf8')
lines=['# 未补回摘要的记录','', '以下只列未成功项。HTTP失败、限流跳过、无可用原页入口，以及已取页面但未提取到合格摘要分别保留；不据此声称论文没有摘要。','', '| ID | 内外 | 标题 | DOI | 结果 | 具体原因/路径 |','|---|---|---|---|---|---|']
for r in failed:
    m=manifest[r['id']];details=[]
    if r['id']in review:details.append(review[r['id']])
    for e in r['publication_page_attempts']:
        u=e.get('url')or e.get('path')or'';status=e.get('http')if e.get('http')is not None else e.get('status');reason=e.get('reason')or('已返回页面，未提取到身份核对通过的摘要'if status==200 else e.get('status',''))
        details.append(f'{u} [{status}; {reason}]')
    if not r['publication_page_attempts']:
        details.append('未执行原页请求：原始条目无论文URL/DOI，精准标题检索未找到可核对原页。'if not m['landing_urls']else'未执行原页请求：仅有数据库/DOI标识，已有缓存未提供支持的出版页入口。')
    s2=[e for e in r['api_attempts']if e.get('provider')=='Semantic Scholar'];details.append('S2: '+('; '.join(dict.fromkeys(str(e.get('http'))+' '+e.get('status','')+' '+e.get('reason','')for e in s2))if s2 else'未执行，缺少支持标识'))
    vals=[r['id'],'内部'if r['lab']else'外部',r['title'],m.get('doi')or'—',labels[r['status']],'；'.join(details)]
    lines.append('| '+' | '.join(v.replace('|',' / ').replace('\n',' ')for v in vals)+' |')
(OUT/'failures.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
lines=['# 身份与版本核对','', '以下6项保留候选但不写入摘要。大小写、标点和同一DOI可证实的标题格式差异均已正常接受。','']
for r in failed:
    if r['status']=='candidate_requires_review':lines+=['- '+r['id']+' — '+r['title']+'：'+review.get(r['id'],r['reason'])]
(OUT/'identity-review.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print('reports saved',len(failed))
