import json,urllib.request,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
d=json.loads((ROOT/'work/keyword-status-new.json').read_text(encoding='utf-8'))
for p in d:
    if p['classification']=='recent_conference_public_abstract_collector_redirect_failure':
        p['detail']='主页列为 NeurIPS 2026；官方详情已公开标题、作者和摘要，正常跟进地点跳转后 HTTP 200。缺 OpenAlex 身份匹配；此前摘要采集停在 HTTP 302。'
        p['keyword_remedy']='用官方摘要提取关键词并标注来源；OpenReview API 本轮 HTTP 403，未取得作者填写关键词。'
    else:
        venue='ICDE 2027' if p['title'].startswith('Mismatch') else 'Findings EMNLP 2026' if p['title'].startswith('KGFlow') else 'ACM MM 2026' if p['title'].startswith('Question') else 'Pattern Recognition 2026'
        p['detail']=f'主页列为 {venue}；该条无 DOI、论文或预印本链接；精确标题网页检索只取得 PI 主页记录。当前缺 OpenAlex 身份匹配和官方论文定位。'
        p['keyword_remedy']='定位出版社或会议摘要页后提取关键词。'
    if p['title'].startswith('PGSB'):
        p['verified_sources'].append({'url':'https://kitschnada.github.io/','fact':'检索到同名刘穆清、东南大学背景且研究 LoRA 的主页，但当前页面只链接 FlexLoRA，未列 PGSB；未将同名主页作为本论文身份凭据。'})
    if p['title'].startswith('KGFlow'):
        u='https://bdsc.szu.edu.cn/en/info/1219/1847.htm'
        try:
            r=op.open(u,timeout=20);t=r.read().decode();(ROOT/'work/new-status-tiantiang-zhu.html').write_text(t,encoding='utf-8')
            p['verified_sources'].append({'url':r.url,'fact':'深圳大学教师朱田恬主页 HTTP 200；页面未检出 KGFlow 标题，未提供本论文链接。','keyword_found':'KGFlow' in t})
        except Exception as e:p['verified_sources'].append({'url':u,'fact':str(e)})
        p['verified_sources'].append({'url':'https://aclanthology.org/events/emnlp-2026/','fact':'ACL Anthology EMNLP 2026 事件路径本轮 HTTP 404；未取得该论文摘要。'})
(ROOT/'work/keyword-status-new.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('saved',len(d),'records')
