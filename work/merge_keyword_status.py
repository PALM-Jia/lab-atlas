"""Publish per-paper homepage/official-page checks as repeatable report evidence."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATLAS = ROOT / 'outputs/paper-atlas'
records = []
for name in ('iclr', 'new', 'preprint', 'root'):
    records += json.loads((ROOT / f'work/keyword-status-{name}.json').read_text(encoding='utf-8'))
assert len(records) == len({r['id'] for r in records}) == 28
nodes = {n['id']: n for n in json.loads((ATLAS / 'data.json').read_text(encoding='utf-8'))['nodes']}
for r in records:
    p = nodes[r['id']]
    c = r['classification']
    if c in ('2025_formal_conference', '2026_new_formal_conference'):
        r['classification'] = 'formal_proceedings'
        r['status_label'] = f"{p['venue']} {p['year']} · 正式论文集已公开"
        r['detail'] = f"贾育衡个人主页列为 {p['venue']} {p['year']} 会议论文；官方论文集页面已核对标题、作者和完整摘要。"
        r['keyword_remedy'] = '直接从官方摘要提取关键词，并标注为摘要提取；也可从正文补采作者关键词。'
    elif c == 'recent_conference_public_abstract_collector_redirect_failure':
        r['classification'] = 'formal_proceedings'
        r['status_label'] = 'NeurIPS 2026 · 官方摘要已公开'
    elif c == 'recent_venue_listed_without_public_locator':
        r['classification'] = 'recent_venue_without_locator'
        r['status_label'] = f"{p['venue']} {p['year']} · 主页已列，缺论文链接"
    elif c.startswith('主页'):
        r['classification'] = 'preprint_title_only'
        r['status_label'] = '主页标为 Preprint · 原条目只有标题'
    elif r['id'] == 'lab-cafae06c3f4f':
        r['classification'] = 'conference_journal_version_link'
        r['status_label'] = 'TRB 2024 · 作者主页已支持会议—期刊关联'
        r['detail'] = '贾育衡主页列 State/TRB 2024；第一作者 Yang He 主页把同一 State 题名同时列为 TRB、WTC 和 TITS 2024，代码仓明确期刊正式题名为 Speed。原采集因候选 ID 与期刊条目重复而拒绝，漏核对了这条版本关联。期刊公开 HTML 已列4个作者关键词。'
    elif r['id'] == 'lab-60280e69a6e3':
        r['classification'] = 'conference_without_fulltext'
        r['status_label'] = 'TRB 2024 · 作者主页已确认，缺会议正文链接'
        r['detail'] = '贾育衡主页及第一作者胡里阳的北京工业大学教师主页均列 TRB 2024；该条目未附 DOI 或正文链接。另篇 TITS 2024 题名、作者列表不同，主页没有版本对应声明。'
        r['keyword_remedy'] = '补采 TRB 会议稿或作者公开稿的关键词；目前可用标题提取，并标注来源。'
    elif c == '2026_formal_with_preprint':
        r['classification'] = 'formal_with_preprint'
        r['status_label'] = 'ICML 2026 · 已公开会议页，另有 arXiv 版本'
    elif c == '2026_formal_conference':
        r['classification'] = 'formal_proceedings'
        r['status_label'] = ('ICML 2026 · 官方摘要已公开' if 'One Coin' in r['title'] else 'CVPR Findings 2026 · 已公开正式论文')
    assert r.get('verified_sources') and r.get('status_label')
(ATLAS / 'keyword-status-review.json').write_text(json.dumps({'checked_date': '2026-10-10', 'items': records}, ensure_ascii=False, indent=2), encoding='utf-8')
print('Published homepage/official-page status checks:', len(records))
