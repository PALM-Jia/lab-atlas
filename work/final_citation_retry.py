from pathlib import Path
exec(Path('work/crosscheck_citations.py').read_text(encoding='utf8').split('rows = {')[0],globals())
r=json.loads((SITE/'citation-comparison.json').read_text(encoding='utf8'));rows={p['id']:p for p in r['rows']}
pending=[(p,identifier(p)) for p in data['nodes'] if identifier(p) and rows[p['id']]['semantic_scholar'].get('reason')=='HTTP 429']
fields='title,authors,citationCount,externalIds,year'
if pending:
 result,event=request('https://api.semanticscholar.org/graph/v1/paper/batch?fields='+fields,{'ids':[i for p,i in pending]})
 for n,(p,i) in enumerate(pending):
  if isinstance(result,list):
   v=s2_record(p,result[n],i);v['previous_attempt']=rows[p['id']]['semantic_scholar'];rows[p['id']]['semantic_scholar']=v
 print('Last identifier retry',len(pending),event['status'],flush=True)
for p in data['nodes']:
 if not p['lab'] or rows[p['id']]['semantic_scholar'].get('reason')!='HTTP 429':continue
 query=p['title'].split(':')[0]
 u='https://api.semanticscholar.org/graph/v1/paper/search/bulk?'+urllib.parse.urlencode({'query':query,'fields':fields})
 v,e=request(u);valid=[s2_record(p,c,'title search/bulk: '+u) for c in (v or {}).get('data',[])];valid=[x for x in valid if x['status']=='success']
 if len(valid)==1:
  valid[0]['previous_attempt']=rows[p['id']]['semantic_scholar'];rows[p['id']]['semantic_scholar']=valid[0]
 else:
  rows[p['id']]['semantic_scholar']['additional_attempt']={'url':u,'status':e['status'],'reason':e.get('reason','No unique identity-validated candidate')}
 print('Last title retry',p['id'],rows[p['id']]['semantic_scholar']['status'],flush=True)
r['rows']=list(rows.values());r['requests'].extend(events);r['collected_at']=dt.datetime.now(dt.timezone.utc).isoformat()
(SITE/'citation-comparison.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
