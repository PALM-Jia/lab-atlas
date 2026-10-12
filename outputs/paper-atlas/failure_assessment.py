"""Separate observed failed paths from judged causes and remaining collection gaps."""
import collections,json
from pathlib import Path
LABELS={'justified':'当前失败有充分依据','pipeline_gap':'采集流程未完成','pending':'原因待核实','excluded':'用户排除'}

def assess_failures(report,data,work):
 nodes={p['id']:p for p in data['nodes']}
 identity={r['id']:r for r in report['steps']['02_match']['items']}
 old_audit_path=Path(work)/'external-lookup-audit.json'
 old_audit=json.loads(old_audit_path.read_text(encoding='utf8'))if old_audit_path.exists()else{}
 def identity_assessment(reason):
  if reason in ('public_page_verified_no_openalex_match','official_listing_no_openalex_match'):
   return 'pipeline_gap','官方论文页面或目录已找到；当前身份成功条件只接受 OpenAlex ID，其他数据库标题匹配尚未执行。','补查 Semantic Scholar 标题匹配及 DBLP/OpenReview 标识；分别记录公开身份与 OpenAlex 收录状态。'
  if reason=='public_candidate_page_access_blocked':
   return 'justified','OpenReview 对该候选的查询返回 403 人机验证要求，该请求被外部访问限制阻挡。','使用已找到的会议来源和 Semantic Scholar 标题查询补采，保留 OpenReview 403 记录。'
  if reason=='title_variant_collides_with_another_lab_paper':
   return 'justified','State/TRB 条目与 Speed/TITS 条目将共用同一 OpenAlex ID；拒绝自动合并有题目、场所及 ID 冲突证据。','核对 TRB 原始记录与 TITS 正式版是否存在明确的版本对应关系。'
  if reason=='possible_renamed_paper_without_version_identity':
   return 'pending','已找到 Uniform 标题候选；原始条目为 Homeomorphic，未找到连接两种题目的版本历史。','查候选的版本记录、作者公开论文页及项目记录，核对是否为同一论文。'
  if reason=='no_public_locator_for_future_year':
   return 'pending','实验室列表标注 2027；当前搜索未找到独立记录。发表年份尚不足以确认公开日期或收录延迟。','核对 ICDE 公开录用目录、作者页面及预印本发布时间。'
  return 'pending','OpenAlex 标题/作者文献集合、Crossref 和网页检索未确认身份；尚未核实公开日期、DOI 有无或数据库收录延迟。','补查 Semantic Scholar 标题匹配、会议公开目录及作者论文页面，记录具体响应。'
 for key,step in report['steps'].items():
  tally=collections.Counter()
  for r in step['items']:
   if r['status']!='failure':continue
   p=nodes.get(r['id']);reason=r['reason'];stage=key
   status='pending';judgment='已记录该步骤的返回结果，失败根因尚未核实。';next_action='核对原始来源与替代查询入口。'
   if key=='02_match':status,judgment,next_action=identity_assessment(reason)
   elif reason=='manual_series_not_provided_by_user':
    status='excluded';judgment='用户明确不提供人工研究系列，此步骤按范围排除。';next_action='保留排除状态。'
   elif key=='03_api_requests'and r.get('provider')=='OpenReview'and reason=='http_403':
    status='justified';judgment='响应明确为 ChallengeRequiredError，访问限制已核实。';next_action='使用已公开会议页面补采该论文信息。'
   elif key=='08_content_vector':
    if reason=='no_supported_public_identifier':
     status='pipeline_gap';judgment='当前程序只用 DOI/arXiv ID 请求向量；Semantic Scholar 标题匹配入口尚未执行，缺标识就停止是程序限制。';next_action='先按标题查找 Semantic Scholar paperId，再按 paperId 获取 SPECTER2。'
    elif reason=='vector_missing_or_invalid':
     status='justified';judgment='Semantic Scholar 已返回论文记录，但 SPECTER2 向量为空或未通过维数/数值检查；当前方案不运行本地嵌入模型。';next_action='保留该模型向量缺失状态，其他关系层继续构建。'
    elif reason=='title_identity_mismatch':
     status='pipeline_gap';judgment='拒用标题不符的响应正确；当前流程尚未通过标题匹配或版本标识寻找正确记录。';next_action='核对 DOI/arXiv 与 Semantic Scholar 记录，改用已确认 paperId 查询。'
    elif reason=='semantic_scholar_no_record':
     status='pending';judgment='指定标识查询返回 null；尚未区分标识别名问题、版本问题和未收录。';next_action='按标题查询并核对作者、年份及 externalIds。'
   elif key=='05_external_metadata':
    old=old_audit.get(r['id'])
    if old and old.get('reason')=='external_id_http_404':
     r['prior_lookup_evidence']=old['lookup_evidence'];judgment='较早的单独 ID 查询已返回 404；ID 是否删除或合并尚未核实。';next_action='核对 OpenAlex ID 合并/重定向和引用来源中的原始标识。'
    else:
     status='pipeline_gap';judgment='批量返回中缺少该 ID，本轮尚未完成该 ID 的单独查询。';next_action='逐 ID 查询，记录 HTTP 状态及重定向目标。'
   elif key=='12_frontend_checks':
    status='justified';judgment='浏览器工具拒绝原标签页协议；页面验证被工具 URL 策略阻挡。';next_action='保留未完成的浏览器验证状态。'
   elif p and not p.get('openalex') and key!='09_research_series':
    upstream=identity.get(p['id'],{}).get('reason',p.get('match_reason'))
    status,judgment,next_action=identity_assessment(upstream)
    judgment='上游身份步骤：'+judgment
   elif key.startswith('04_'):
    if key=='04_references':
     status='pipeline_gap';judgment='OpenAlex 的 referenced_works 返回空列表；尚未查询 Semantic Scholar references。';next_action='在已确认的 Semantic Scholar 记录上获取 references。'
    elif key=='04_abstract':
     status='pipeline_gap';judgment='已尝试的 OpenAlex/Semantic Scholar 路径未补到摘要；出版页面摘要提取及标题回退尚未完成。';next_action='核对出版页摘要与 Semantic Scholar 标题匹配结果。'
    else:judgment='OpenAlex 已返回对应空字段；出版来源是否缺字段或抓取遗漏尚未核对。';next_action='核对出版记录对应字段及作者公开信息。'
   elif reason=='database_returned_empty_relation_field':
    judgment='对应 OpenAlex 关系输入为空；来源缺字段还是元数据抽取遗漏尚未核对。';next_action='补查该字段的其他公开来源。'
   r['failure_assessment']={'status':status,'label':LABELS[status],'failed_stage':stage,'judgment':judgment,'next_action':next_action}
   tally[status]+=1
  step['cause_assessment']={'failure_total':sum(tally.values()),'counts':dict(tally),'justified_rate':round(100*tally['justified']/sum(tally.values()),4)if tally else 0}
 report['failure_interpretation']={'path_accounting':'success + recorded failed paths = all items','reasonability':'justified, pipeline_gap, pending, excluded are separate; path accounting does not certify reasonability','labels':LABELS}
 return report
