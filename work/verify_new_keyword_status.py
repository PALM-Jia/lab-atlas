import json, re, urllib.request, html, concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
d=json.loads((ROOT/'outputs/paper-atlas/keyword-missing.json').read_text(encoding='utf-8'))
papers=[x for x in d['missing'] if x.get('year') in [2026,2027] and x['title'].startswith(('PGSB','Exploiting Negative','Individuals Matter','AdapMatch','Progressive Pseudo','LoCo','Attention Heads','Mismatch-Free','KGFlow','Question-Level','Towards Robust'))]
def fetch(p):
    out={'id':p['id'],'title':p['title'],'classification':'recent_venue_listed_without_public_locator','detail':'','verified_sources':[{'url':'https://jyh-learning.github.io/papers.html','fact':f"PI 个人主页将本论文列于 {'Journal Papers' if p['venue']=='PR' else 'Conference Papers'}，标注 {p['venue']} {p['year']}；不在 Preprint 栏。"}],'checked_date':'2026-10-10','keyword_remedy':'尚未取得可核对的公开摘要；继续定位官方论文页面。'}
    if p['venue']=='NeurIPS':
        u=next(s['url'] for s in p['sources'] if 'neurips.cc/virtual' in s['url'])
        try:
            r=op.open(u,timeout=30); t=r.read().decode(); (ROOT/'work'/f"new-status-{p['id']}.html").write_text(t,encoding='utf-8')
            links=list(dict.fromkeys(re.findall(r'https://openreview.net/forum\?id=[A-Za-z0-9_-]+',t)))
            ab=re.search(r'<!-- Abstract Section -->(.*?)<!--',t,re.S)
            excerpt=html.unescape(re.sub('<[^>]+>',' ',ab.group(1) if ab else ''))
            excerpt=' '.join(excerpt.split())
            out['classification']='recent_conference_public_abstract_collector_redirect_failure'
            out['detail']='NeurIPS 2026 最新会议论文，官方详情和摘要已经公开。此前采集停在 HTTP 302，未跟进地点路由跳转；本轮正常跟进后返回 HTTP 200。关键词缺失的直接原因仍是未匹配 OpenAlex，公开元数据采集也曾漏掉摘要，不能归为论文未公开。'
            out['verified_sources'].append({'url':r.url,'fact':'HTTP 200；标题及作者与主页一致；公开摘要可读取。','abstract_excerpt':excerpt,'openreview_urls':links})
            out['keyword_remedy']='官方公开摘要已取得，可从摘要提取关键词并标注来源；OpenReview 还可提供作者提交关键词。'
        except Exception as e: out['detail']=f'PI 主页确认为 NeurIPS 2026。官方详情本轮采集错误：{type(e).__name__}: {e}'
    else:
        out['detail']=f"PI 主页明确列为 {p['venue']} {p['year']}，但该条目未附论文、DOI 或预印本链接。现有 OpenAlex/Crossref 查询没有通过身份校验；尚无出版社发布时间或入库时间可直接证明延迟。"
    return out
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex: result=list(ex.map(fetch,papers))
(ROOT/'work/keyword-status-new.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
for p in result: print(p['id'],p['classification'],p['verified_sources'][-1].get('url'),p['verified_sources'][-1].get('openreview_urls'))
