from pathlib import Path
p=Path('work/crosscheck_citations.py')
s=p.read_text(encoding='utf8')
head=s.split('rows = {')[0]
function=s.split('def crossref(p):')[1].split('\nlab = ')[0]
exec(head,globals())
exec('def crossref(p):'+function,globals())
with futures.ThreadPoolExecutor(max_workers=2) as pool:
 for i,(pid,r) in enumerate(pool.map(crossref,[p for p in data['nodes'] if p['lab']])):
  if i%20==0: print(i+1,r['status'],flush=True)
(ROOT/'work/crossref-prefetch-requests.json').write_text(json.dumps(events),encoding='utf8')
