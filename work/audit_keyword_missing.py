"""Audit keyword coverage against existing OpenAlex responses; never sends requests."""
import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit

ROOT = Path(__file__).resolve().parent.parent
ATLAS = ROOT / 'outputs/paper-atlas'
LEGACY = ROOT / 'work/archive/paper-atlas-legacy-2026-10-13'
LEGACY.mkdir(parents=True, exist_ok=True)


def load(name):
    return json.loads((ATLAS / name).read_text(encoding='utf8'))


def safe_url(url):
    parts = urlsplit(url or '')
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if k.lower() not in ('api_key', 'apikey', 'key', 'token')]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def main():
    data = load('data.json')
    audits = {r['id']: r for r in load('identity-search-audit.json')}
    matches = {r['id']: r for r in load('acceptance.json')['steps']['02_match']['items']}
    public = load('public-paper-metadata.json')
    records = defaultdict(list)
    for path in sorted((ROOT / 'work/api-cache').glob('*.json')):
        try:
            raw = json.loads(path.read_text(encoding='utf8'))
        except (ValueError, OSError):
            continue
        candidates = raw.get('results', [raw]) if isinstance(raw, dict) else raw if isinstance(raw, list) else []
        for record in candidates:
            if isinstance(record, dict) and str(record.get('id', '')).startswith('https://openalex.org/W'):
                records[record['id']].append((record, path.relative_to(ROOT).as_posix()))
    missing = []
    available = 0
    for paper in (p for p in data['nodes'] if p['lab']):
        cached = records.get(paper.get('openalex'), [])
        if any(r.get('keywords') for r, _ in cached):
            available += 1
            continue
        audit, match = audits.get(paper['id'], {}), matches[paper['id']]
        sources = []
        reason = audit.get('reason') or match.get('reason')
        assessment = match.get('failure_assessment') or {}
        if paper.get('openalex'):
            keyword_fields = [r.get('keywords', 'FIELD_MISSING') for r, _ in cached]
            field_empty = bool(cached) and all(k == [] for k in keyword_fields)
            reason = 'openalex_keywords_empty' if field_empty else 'keyword_field_not_cached'
            detail = ('OpenAlex 记录已取得，所有已存响应的 keywords 字段均为 []。' if field_empty
                      else '已匹配 OpenAlex 身份，但缓存未提供关键词字段。')
            best = max((r for r, _ in cached), key=len, default={})
            detail += f"记录含 {len(best.get('topics') or [])} 个主题；" + ('含摘要。' if best.get('abstract_inverted_index') else '摘要字段为空。')
            judgment = '关键词字段为空的具体数据库处理原因未记录。'
            remedy = '从论文原文关键词补采，或以标题、摘要提取关键词并标注来源。'
            sources.append({'source': 'OpenAlex work', 'url': 'https://api.openalex.org/works/' + paper['openalex'].rsplit('/', 1)[-1],
                            'result': 'keywords = []' if field_empty else 'keywords 字段未缓存',
                            'cache_paths': sorted({path for _, path in cached})})
        else:
            detail = '未确认 OpenAlex 论文 ID，未取得该论文的 keywords 字段。'
            if reason == 'public_page_verified_no_openalex_match':
                detail += '官方论文页面已核对标题和作者；OpenAlex 标题及作者文献集合查询未匹配。'
            elif reason == 'official_listing_no_openalex_match':
                detail += '已有身份审计中，NeurIPS 2026 官方目录已列出标题；论文详情请求返回 HTTP 302，采集程序未继续跳转。'
            elif reason == 'title_only_no_independent_locator':
                detail += '实验室列表仅有标题，无年份、作者或论文链接；标题查询未确认记录。'
            elif reason == 'spelling_variant_no_verified_match':
                detail += '原题含 Hyerspectral 拼写，身份审计已尝试标题变体，仍未确认记录。'
            elif reason == 'possible_renamed_paper_without_version_identity':
                detail += '找到 Uniform Latent Space 标题候选（arXiv:2610.07610），原题为 Homeomorphic Latent Space，缺少两题对应的版本证据。'
            elif reason == 'public_candidate_page_access_blocked':
                detail += '候选 OpenReview API 请求返回 HTTP 403，要求人机验证；未取得正文元数据。'
            elif reason == 'no_public_locator_for_future_year':
                detail += '实验室列表标注 2027 / ICDE；标题查询未确认公开记录，公开日期尚未核对。'
            elif reason == 'title_variant_collides_with_another_lab_paper':
                detail += 'State / TRB 条目候选为 Speed / TITS，且与另一个实验室条目共用 OpenAlex ID；身份归并被拒绝。'
            else:
                detail += 'OpenAlex 标题、作者文献集合和 Crossref 标题查询未取得身份校验通过的记录。'
            judgment = assessment.get('judgment', '身份匹配原因尚未核实。')
            remedy = assessment.get('next_action', '补查公开论文页面或其他数据库身份。')
            if paper['id'] in public:
                remedy = '官方页面已有摘要，可据此提取关键词并标注为摘要提取；或从论文原文补采作者关键词。'
            for event in audit.get('queries', []) + audit.get('author_corpus_queries', []):
                sources.append({'source': event.get('provider', '数据库查询'), 'url': safe_url(event.get('url')),
                                'result': '请求成功；无身份校验通过的匹配' if event.get('status') == 'success' else event.get('reason'),
                                'attempts': event.get('attempts', [])})
            for proof in audit.get('public_evidence', []):
                event = proof.get('event') or {}
                result = ('官方目录已核对标题' if proof.get('evidence_type') == 'official_title_listing'
                          else '已核对标题及作者' if proof.get('title_present')
                          else 'HTTP 403，人机验证' if event.get('reason') == 'http_403'
                          else 'HTTP 302，采集程序未继续跳转' if event.get('reason') == 'http_302'
                          else event.get('reason', '未完成身份核验'))
                sources.append({'source': event.get('provider', '公开论文页面'), 'url': safe_url(event.get('url') or proof.get('url')), 'result': result})
            for candidate in match.get('candidates', []):
                if reason == 'title_variant_collides_with_another_lab_paper':
                    sources.append({'source': '冲突候选：' + candidate['title'], 'url': candidate['id'], 'result': candidate.get('doi') or ''})
            related = audit.get('related_public_candidate')
            if related:
                sources.append({'source': '改题候选：' + related['title'], 'url': related['url'], 'result': '未找到原题与该题的版本对应证据'})
        missing.append({'id': paper['id'], 'title': paper['title'], 'year': paper.get('year'), 'venue': paper.get('venue'),
                        'openalex': paper.get('openalex'), 'reason': reason, 'detail': detail,
                        'assessment': judgment, 'next_action': remedy, 'sources': sources,
                        'evidence_files': ['data.json', 'acceptance.json'] + (['identity-search-audit.json'] if audit else [])
                                          + (['public-paper-metadata.json'] if paper['id'] in public else [])})
    review_path = ATLAS / 'keyword-status-review.json'
    review = json.loads(review_path.read_text(encoding='utf8')) if review_path.exists() else {}
    status_items = {r['id']: r for r in review.get('items', [])}
    for item in missing:
        status = status_items.get(item['id'])
        if not status:
            continue
        item['prior_pipeline_detail'] = item['detail']
        item['prior_pipeline_assessment'] = item['assessment']
        item['verified_status'] = status['classification']
        item['status_label'] = status['status_label']
        item['checked_date'] = status['checked_date']
        item['detail'] = status['detail']
        item['assessment'] = ('已匹配 OpenAlex，缓存 keywords 为空；官方发表状态与数据库字段缺失分别记录。'
                              if item['openalex'] else '当前关键词采集只接入已匹配 OpenAlex 的记录；已确认的个人主页及官方摘要尚未用于补采。')
        if status['classification'] == 'preprint_title_only':
            item['assessment'] = '原主页条目只有标题；缺作者、时间和公开原文标识，当前未接入 OpenAlex 关键词。'
        elif status['classification'] == 'recent_venue_without_locator':
            item['assessment'] = '主页有场所、年份和作者；缺正式论文页/DOI链接，OpenAlex身份尚未匹配。'
        elif status['classification'] == 'conference_without_fulltext':
            item['assessment'] = '会议发表状态已确认；会议稿关键词和摘要尚未取得。'
        elif status['classification'] == 'conference_journal_version_link':
            item['assessment'] = '已有版本关联和期刊关键词；采集程序仍未接入带版本来源的关键词补采。'
        item['next_action'] = status['keyword_remedy']
        item['verified_sources'] = status['verified_sources']
        item['sources'] = [{'source': '本轮主页/公开页核查', 'url': safe_url(s['url']), 'result': s['fact']}
                           for s in status['verified_sources']] + item['sources']
        item['evidence_files'].append('keyword-status-review.json')
    counts = Counter(r['reason'] for r in missing)
    result = {'summary': {'total': available + len(missing), 'available': available, 'missing': len(missing),
                           'available_rate': round(100 * available / (available + len(missing)), 1),
                           'identity_unmatched': sum(not r['openalex'] for r in missing),
                           'matched_empty_keywords': counts['openalex_keywords_empty'], 'reasons': dict(counts)},
              'scope': '现有 OpenAlex 关键词缓存；另按个人主页和官方公开页逐篇核查发表状态。', 'missing': missing}
    result['summary']['status_checked'] = sum('verified_status' in r for r in missing)
    result['summary']['status_categories'] = dict(Counter(r.get('verified_status', 'not_checked') for r in missing))
    categories = result['summary']['status_categories']
    published = sum(categories.get(k, 0) for k in ('formal_proceedings', 'formal_with_preprint', 'conference_journal_version_link', 'conference_without_fulltext'))
    status_summary = (f"状态核查：{published} 篇已有正式会议/期刊发表证据，"
                      f"{categories.get('preprint_title_only', 0)} 篇在主页标为 Preprint 且原条目只有标题，"
                      f"{categories.get('recent_venue_without_locator', 0)} 篇主页列为 2026/2027 会议或期刊条目但未附论文链接。")
    (ATLAS / 'keyword-missing.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    esc = html.escape
    cards = []
    for item in missing:
        links = ''.join(f'<li><a href="{esc(s["url"], quote=True)}" target="_blank" rel="noopener">{esc(s["source"])}</a>：{esc(str(s["result"]))}</li>' for s in item['sources'] if s.get('url'))
        paths = ''.join(f'<li><code>{esc(p)}</code></li>' for s in item['sources'] for p in s.get('cache_paths', []))
        files = ' · '.join(f'<a href="{esc(f)}">{esc(f)}</a>' for f in item['evidence_files'])
        status_label = item.get('status_label') or f'{item["year"] or "年份未提供"} · {item["venue"] or "场所未提供"}'
        cards.append(f'<article id="{esc(item["id"])}"><h2>{esc(item["title"])}</h2><div class="meta">{esc(status_label)}</div><p>{esc(item["detail"])}</p><p><b>关键词缺口：</b>{esc(item["assessment"])}</p><p><b>补采路径：</b>{esc(item["next_action"])}</p><section><h3>本轮核查来源与历史请求</h3><ul>{links}{paths}</ul><p class="files">审计文件：{files}</p></section></article>')
    page = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>缺关键词论文</title>
<style>body{{font:16px/1.65 system-ui,sans-serif;color:#243143;background:#f5f7fa;margin:0}}main{{max-width:1080px;margin:auto;padding:24px}}h1{{font-size:26px;margin:12px 0}}h2{{font-size:18px;margin:0}}p{{margin:8px 0}}a{{color:#2463a9;overflow-wrap:anywhere}}article{{background:white;border:1px solid #dde3ea;border-radius:8px;padding:16px 20px;margin:12px 0}}.meta,.files{{color:#627083;font-size:14px}}h3{{color:#2463a9}}code{{font-size:12px;overflow-wrap:anywhere}}li{{margin:5px 0}}nav{{display:flex;gap:18px;flex-wrap:wrap}}</style>
<main><nav><a href="index.html?view=authors&amp;authorRelation=keywords">作者网络</a><a href="acceptance-report.html">检索报告</a><a href="keyword-missing.json">审计数据</a></nav><h1>缺关键词论文</h1><p>144 篇实验室论文：116 篇已接入 OpenAlex keywords（80.6%），28 篇尚未接入。以下逐篇列出发表状态、当前关键词缺口及补采来源。</p><p>{esc(status_summary)}</p><p class="meta">2026-10-10 回查个人主页和官方公开页，已核对 {result['summary']['status_checked']} / 28 项。成功项只作汇总。</p>{''.join(cards)}</main></html>'''
    from public_copy import clean_public_copy
    (LEGACY / 'keyword-missing.html').write_text(clean_public_copy(page), encoding='utf8')
    print(json.dumps(result['summary'], ensure_ascii=False))
    print('Empty keywords:', [r['title'] for r in missing if r['reason'] == 'openalex_keywords_empty'])


if __name__ == '__main__':
    main()
