"""Attach concrete provider and field evidence to failed acceptance rows."""
import json, urllib.parse
from pathlib import Path

def enrich_report(report,data,work):
 nodes={p['id']:p for p in data['nodes']}
 vector_rows={r['id']:r for r in report['steps']['08_content_vector']['items']}
 sem={}
 for path in Path(work,'api-cache').glob('*.request'):
  try:
   ids=json.loads(path.read_text(encoding='utf8')).get('ids',[])
   records=json.loads(path.with_suffix('.json').read_text(encoding='utf8'))
   if isinstance(records,list) and len(ids)==len(records):sem.update(zip((i.lower()for i in ids),records))
  except (ValueError,OSError,AttributeError):pass
 field_names={'authors':'作者','year':'年份','abstract':'摘要','references':'参考文献','institution_records':'机构 ID'}
 oa_fields={'authors':'authorships','year':'publication_year','abstract':'abstract_inverted_index','references':'referenced_works','institution_records':'authorships[].institutions'}
 def s2_trace(pid,for_vector=False):
  v=vector_rows.get(pid,{})
  identifier=v.get('identifier')
  if not identifier:return {'provider':'Semantic Scholar','result':'未发起查询：条目没有 DOI 或 arXiv ID；当前查询入口仅支持这两类标识'}
  record=sem.get(identifier.lower())
  if v['reason']=='semantic_scholar_no_record':result=f'/paper/batch 对 {identifier} 返回 null'
  elif v['reason']=='title_identity_mismatch':result=f'/paper/batch 返回标题“{(record or {}).get("title","未保存")}”，未通过标题核对'
  elif v['reason'].startswith('batch_'):result=f'/paper/batch 查询 {identifier} 失败：{v["reason"][6:]}'
  elif not record:result=f'/paper/batch 对 {identifier} 返回 null'
  else:
   vec=(record.get('embedding')or{}).get('vector')
   result=f'记录 {record["paperId"]} 的 abstract 字段为空' if not record.get('abstract') else f'记录 {record["paperId"]} 已返回摘要'
   if for_vector and v['reason']=='vector_missing_or_invalid':result='记录已返回，embedding.vector 字段为空' if not vec else f'返回向量未通过校验：维数 {len(vec)}，要求 768 维、有限数值且非零'
  return {'provider':'Semantic Scholar','url':'https://api.semanticscholar.org/graph/v1/paper/batch','identifier':identifier,'result':result}
 for key,step in report['steps'].items():
  for r in step['items']:
   if r['status']!='failure':continue
   p=nodes.get(r['id']);traces=[]
   if key.startswith('04_'):
    field=key[3:];label=field_names[field]
    if p.get('openalex'):
     traces.append({'provider':'OpenAlex','url':'https://api.openalex.org/works/'+p['openalex'].split('/')[-1],'result':f'已取得该论文记录，{oa_fields[field]} 字段为空'})
     summary=f'OpenAlex 返回空的{label}字段'
    else:
     traces.append({'provider':'实验室论文列表','url':report['meta']['source'],'result':f'该条目未提供{label}' if field not in ('references','institution_records') else f'列表不提供{label}字段'})
     traces.append({'provider':'OpenAlex','result':f'论文 ID 尚未确认；{oa_fields[field]} 字段查询未发起','identity_reason':p.get('match_reason')})
     summary=f'实验室列表未提供{label}；OpenAlex 论文 ID 未确认'
     audit=p.get('identity_search_evidence',{})
     for evidence in audit.get('public_evidence',[]):
      event=evidence.get('event',{})
      if event.get('status')=='failure':result='请求失败：'+event.get('reason','未记录错误码')
      elif not evidence.get('title_present'):result='已收到 HTML，但解析内容没有论文题目和摘要'
      else:result=f'论文题目已核对，页面未提取到{label}'
      if field=='abstract':traces.append({'provider':urllib.parse.urlparse(evidence['url']).netloc,'url':evidence['url'],'result':result})
    if field=='abstract':traces.append(s2_trace(r['id']))
    r['failure_summary']=summary
   elif key=='08_content_vector':
    traces.append(s2_trace(r['id'],True));r['failure_summary']=traces[0]['result']
   elif key=='03_api_requests':
    provider=r['provider'];reason=r['reason']
    result='OpenReview 要求人机验证（HTTP 403），未绕过' if provider=='OpenReview'and reason=='http_403'else f'{provider} 请求失败：{reason}'
    traces.append({'provider':provider,'url':r['title'],'result':result});r['failure_summary']=result
   elif key in ('05_incoming_neighborhood',) and p and not p.get('openalex'):
    traces.append({'provider':'OpenAlex','result':'论文 ID 未确认，cites 被引查询未发起','identity_reason':p.get('match_reason')})
    r['failure_summary']='OpenAlex 论文 ID 未确认，被引列表查询未发起'
   elif key=='05_external_metadata':
    url=next((q['url']for q in report['requests']if q['provider']=='OpenAlex'and r['id']in urllib.parse.unquote(q['url']) and 'openalex_id' in q['url']),None)
    result='批量查询返回成功响应，但 results 中未返回该 ID' if r['reason']=='openalex_id_not_returned' else '单独查询该 ID 返回 HTTP 404' if r['reason']=='external_id_http_404' else '请求失败：'+r['reason']
    traces.append({'provider':'OpenAlex','url':url,'result':result});r['failure_summary']='OpenAlex '+result
   elif key=='12_frontend_checks':
    traces.append({'provider':'浏览器工具','result':'绑定原预览标签页被 URL 策略拒绝：页面协议不在允许的 HTTP/HTTPS 范围内'})
   if traces:r['failure_sources']=traces
 return report
