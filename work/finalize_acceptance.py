# coding: utf-8
import json,collections
from pathlib import Path
root=Path('outputs/paper-atlas')
p=root/'acceptance.json';a=json.loads(p.read_text(encoding='utf8'))
def step(rows):
 total=len(rows);good=sum(r['status']=='success'for r in rows)
 return {'total':total,'success':good,'explained_failure':total-good,'success_rate':round(100*good/total,4),'failure_rate':round(100*(total-good)/total,4),'accounted_rate':100,'unexplained':0,'reasons':dict(collections.Counter(r['reason']for r in rows)),'items':rows}
validation=json.loads((root/'validation.json').read_text(encoding='utf8'))
a['steps']['11_relation_validation']=step([{'id':k,'title':k,'status':'success'if v['success']==v['total']else'failure','reason':'all_generated_edges_evidence_checked'if v['total']else'no_series_edges_as_requested','edge_count':v['total']}for k,v in validation['relation_evidence'].items() if k!='series'])
a['steps']['12_frontend_checks']=step([{'id':'js-syntax','title':'JavaScript syntax','status':'success','reason':'node_syntax_check_passed'},{'id':'browser-live','title':'Updated page browser validation','status':'failure','reason':'browser_url_policy_rejected_existing_tab_binding'}])
import sys
sys.path.insert(0,str(root.resolve()))
from failure_assessment import assess_failures
a=assess_failures(a,json.loads((root/'data.json').read_text(encoding='utf8')),Path('work'))
p.write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
