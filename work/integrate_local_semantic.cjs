const fs=require('node:fs');const p='outputs/paper-atlas/pipeline.py';let s=fs.readFileSync(p,'utf8');
s=s.replace('No private submissions, manual series, full-text downloads or local models.','No private submissions, manual series or full-text downloads. Semantic features use a bounded local model.');
s=s.replace('def embeddings(nodes,api,ledger):','def api_embeddings(nodes,api,ledger):');
const wrapper=`def embeddings(nodes,api,ledger):
    from semantic_features import generate_embeddings
    rows,meta=generate_embeddings(nodes)
    for row in rows:
        detail={k:v for k,v in row.items() if k not in ('id','title','status','reason')}
        ledger.add('08_content_vector',row,row['status']=='success',row['reason'],**detail)
    ledger.checkpoint()
    return meta


`;
s=s.replace('def graph(nodes,citing_sets):',wrapper+'def graph(nodes,citing_sets):');
const start=s.indexOf('    vectors=[p for p in nodes if p.get(\'embedding\')]');const end=s.indexOf('    retained=edges',start);if(start<0||end<start)throw Error('graph block');
s=s.slice(0,start)+"    from semantic_features import semantic_edges\n    edges.extend(semantic_edges(nodes))\n"+s.slice(end);
s=s.replace('    embeddings(nodes,api,ledger)\n','    semantic_meta=embeddings(nodes,api,ledger)\n');
s=s.replace("    data={'meta':meta,", "    meta['semantic']=semantic_meta\n    data={'meta':meta,");
fs.writeFileSync(p,s);
const q='work/refresh_paper_semantic.py';s=fs.readFileSync(q,'utf8');s=s.replace("d=json.loads((root/'data.json').read_text(encoding='utf-8'));vectors={}","d=json.loads((root/'data.json').read_text(encoding='utf-8'));vectors={}\nif d.get('meta',{}).get('semantic',{}).get('method')=='local':\n from generate_local_semantic import run\n run()\n raise SystemExit(0)");fs.writeFileSync(q,s);
const v='work/validate_pipeline.py';s=fs.readFileSync(v,'utf8');s=s.replace("            assert v['source_ids']==[a['semantic_paper_id'],b['semantic_paper_id']]", "            keys=[a['semantic_vector_key'],b['semantic_vector_key']] if v.get('source')=='local' else [a['semantic_paper_id'],b['semantic_paper_id']]\n            assert v['source_ids']==keys");
const first=s.indexOf("for path in Path('work/api-cache').glob('*.json'):");const last=s.indexOf("semantic=[e for e in edges",first);if(first<0||last<first)throw Error('validator block');
const legacy=s.slice(first,last);const local=`if d['meta'].get('semantic',{}).get('method')=='local':
    import sys
    sys.path.insert(0,str(root))
    from semantic_features import input_text,read_vector
    for p in nodes.values():
        if p['semantic_status']!='available':continue
        text,info,key=input_text(p)
        assert key==p['semantic_vector_key'] and info['sha256']==p['semantic_input']['sha256']
        record=read_vector(Path('work/semantic-vector-cache'),key)
        assert record and record['input']==p['semantic_input']
        vectors[key]=np.array(record['vector'],dtype=np.float64)
    available=[p for p in nodes.values() if p['semantic_status']=='available']
    lab_count=sum(p['lab'] for p in available)
    assert sum(e['kind']=='semantic' for e in edges)==lab_count*(len(available)-lab_count)+lab_count*(lab_count-1)//2
else:
`;
s=s.slice(0,first)+local+legacy.split('\n').filter((line,i,a)=>i<a.length-1||line).map(line=>'    '+line).join('\n')+'\n'+s.slice(last);
fs.writeFileSync(v,s);
