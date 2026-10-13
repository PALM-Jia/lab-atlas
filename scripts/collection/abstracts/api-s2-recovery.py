import json,time,importlib.util,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'work/abstract-backfill'
OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('backfill',Path(__file__).resolve().parent/'api-backfill.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest={p['id']:p for p in json.loads((OUT/'api-manifest.json').read_text(encoding='utf8'))}
todo=[manifest[p['id']]for p in json.loads((OUT/'merged-abstracts.json').read_text(encoding='utf8'))['results']if p['status']!='success']
run=m.Run();pairs=[];rows=[]
for p in todo:
    ident=p.get('semantic_scholar')or('DOI:'+p['doi']if p.get('doi')else'ARXIV:'+p['arxiv'][0]if p['arxiv']else None)
    if ident:pairs.append((p,ident))
    else:rows.append({'id':p['id'],'title':p['title'],'status':'not_queried','abstract':None,'attempts':[{'provider':'Semantic Scholar','http':None,'status':'not_queried','reason':'no_supported_identifier'}],'candidates':[],'reason':'no_supported_identifier'})
for i in range(0,len(pairs),50):
    group=pairs[i:i+50];url='https://api.semanticscholar.org/graph/v1/paper/batch?fields=paperId,title,abstract,year,externalIds';d,e=run.request('Semantic Scholar',url,{'ids':[x[1]for x in group]})
    for j,(p,ident)in enumerate(group):
        row=run.rows[p['id']];row['attempts'].append({**e,'identifier':ident,'recovery_after_cooldown_seconds_at_least':120});w=d[j]if isinstance(d,list)and j<len(d)else None
        if w:run.candidate(p,w,'Semantic Scholar',url,e.get('http'))
        if row['status']!='success':row.update(status='no_abstract'if d is not None else e['status'],reason='record_has_no_acceptable_abstract'if w else'no_matching_record'if d is not None else e['reason'])
        rows.append(row)
    if run.blocked:
        for p,ident in pairs[i+50:]:rows.append({'id':p['id'],'title':p['title'],'status':'not_queried','abstract':None,'attempts':[{'provider':'Semantic Scholar','path':url,'identifier':ident,'http':None,'status':'not_queried','reason':'source_blocked_after_recovery_probe_'+str(run.blocked)}],'candidates':[],'reason':'source_blocked_after_recovery_probe'})
        break
    if i+50<len(pairs):time.sleep(6)
result={'summary':dict(collections.Counter(x['status']for x in rows)),'calls':run.calls,'blocked':run.blocked,'results':rows}
(OUT/'api-s2-recovery-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items()if k!='results'}),flush=True)
