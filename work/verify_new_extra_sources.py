import urllib.request,re,json,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
data=json.loads((ROOT/'work/keyword-status-new.json').read_text(encoding='utf-8'))
def check(p):
    links=p['verified_sources'][-1].get('openreview_urls',[])
    if links:
        u='https://api2.openreview.net/notes?id='+links[0].split('id=')[-1]
        try:
            r=op.open(u,timeout=20); j=json.load(r); content=j['notes'][0]['content']; kws=content.get('keywords',{}); kws=kws.get('value') if isinstance(kws,dict) else kws
            p['verified_sources'].append({'url':u,'fact':'OpenReview API 返回 HTTP 200','keywords':kws})
        except urllib.error.HTTPError as e: p['verified_sources'].append({'url':u,'fact':f'OpenReview API 返回 HTTP {e.code}，本轮未取得作者填写关键词。'})
        except Exception as e: p['verified_sources'].append({'url':u,'fact':str(e)})
    return p
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex: data=list(ex.map(check,data))
(ROOT/'work/keyword-status-new.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
for u in ['https://bdsc.szu.edu.cn/en/TEAM1.htm','https://kitschnada.github.io/','https://aclanthology.org/events/emnlp-2026/']:
    try:
        r=op.open(u,timeout=20);t=r.read().decode();print(u,r.status,r.url)
        if 'TEAM' in u:
            for m in re.finditer('Zhu Tiantian',t): print(t[m.start()-250:m.end()+250])
        elif 'kitschnada' in u: print(re.findall(r'href="([^\"]+)"',t)[-25:])
    except Exception as e: print(u,type(e).__name__,str(e))
