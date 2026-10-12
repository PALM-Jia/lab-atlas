import json,re,hashlib,importlib.util,collections
from difflib import SequenceMatcher
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
spec=importlib.util.spec_from_file_location('pages',OUT/'api-pages.py');pages=importlib.util.module_from_spec(spec);spec.loader.exec_module(pages)
api=json.loads((OUT/'api-results.json').read_text(encoding='utf8'))
lab=json.loads((OUT/'lab-results.json').read_text(encoding='utf8'))
pub=json.loads((OUT/'api-publication-results.json').read_text(encoding='utf8'))
recovery=json.loads((OUT/'api-s2-recovery-results.json').read_text(encoding='utf8'))if(OUT/'api-s2-recovery-results.json').exists()else{'results':[]}
recoverymap={x['id']:x for x in recovery['results']}
format_review=json.loads((OUT/'api-format-review-results.json').read_text(encoding='utf8'))if(OUT/'api-format-review-results.json').exists()else{'results':[]}
formatmap={x['id']:x for x in format_review['results']}
# Reparse only saved official pages after selector corrections, without new requests.
for row in lab['results']:
    if row['status']=='success':continue
    for attempt in row['attempts']:
        if not attempt.get('file'):continue
        path=OUT/attempt['file']
        if not path.exists():continue
        try:w=pages.extract(path.read_text(encoding='utf8'),attempt['url'])
        except Exception:continue
        if w and w.get('abstract')and pages.norm(w.get('title')or'')==pages.norm(row['title'])and len(w['abstract'].split())>=25:
            row['candidates'].append({**w,'source_url':attempt['url'],'accepted':True,'reason':'exact_title_on_official_publication_page'})
            row.update(status='success',abstract=w['abstract'],source_url=attempt['url'],reason='exact_title_on_official_publication_page');break
lab['summary']=dict(collections.Counter(x['status']for x in lab['results']))
(OUT/'lab-results.json').write_text(json.dumps(lab,ensure_ascii=False,indent=2),encoding='utf8')
labmap={x['id']:x for x in lab['results']};pubmap={x['id']:x for x in pub['results']};merged=[];accepted={}
def extractor(url):
    if 'springer.com' in url:return 'publisher_abstract_section_Abs1-content'
    if 'nature.com' in url:return 'publisher_abstract_section'
    if '/virtual/'in url:return 'conference_abstract-text-inner'
    if 'neurips.cc/paper_files'in url:return 'proceedings_paper-abstract'
    if'aclanthology.org'in url:return 'acl-abstract'
    if'thecvf.com'in url:return 'cvf_abstract'
    if'api.crossref'in url:return 'metadata_abstract_jats_stripped'
    if'arxiv.org'in url:return 'arxiv_blockquote_abstract'
    return 'api_original_abstract_or_inverted_index'
for a in api['results']:
    variants=[x for x in[labmap.get(a['id']),formatmap.get(a['id']),pubmap.get(a['id']),recoverymap.get(a['id']),a]if x]
    good=[x for x in variants if x['status']=='success'and x.get('abstract')]
    candidates=[c for x in variants for c in x.get('candidates',[])]
    api_attempts=a['attempts']+(recoverymap.get(a['id'])or{}).get('attempts',[]);page_attempts=[e for x in[labmap.get(a['id']),formatmap.get(a['id']),pubmap.get(a['id'])]if x for e in x.get('attempts',[])]
    if a.get('doi','') and a['doi'].startswith('10.1016/') and not page_attempts and 'www.sciencedirect.com'in pub.get('blocked',{}):
        page_attempts.append({'url':'https://doi.org/'+a['doi'],'http':None,'status':'not_queried','reason':'Elsevier_DOI_route_not_followed_after_publisher_domain_http_403'})
    row={'id':a['id'],'title':a['title'],'lab':a['lab'],'target_reason':a['target_reason'],'status':'unresolved','abstract':None,'api_attempts':api_attempts,'publication_page_attempts':page_attempts,'candidates':candidates}
    if a['id']=='lab-d99ee9ba4a13':row['invalid_original']={'kind':'bibliographic_citation_in_abstract','text':next(p['abstract']for p in json.loads((ROOT/'outputs/paper-atlas/data.json').read_text(encoding='utf8'))['nodes']if p['id']==a['id']),'discarded':True}
    if a['lab'] and not a['landing_urls']:row['discovery_search']={'query':'"'+a['title']+'"','method':'exact_title_web_search','http':None,'reason':'official_sources_or_candidates_recorded_when_found'}
    if good:
        g=good[0];source=g.get('source_url')or g.get('source_path');archive=None
        for e in g.get('attempts',[]):
            if e.get('url')==source and e.get('file'):archive=e['file']
        if not archive and source and source.startswith('http'):
            expected=OUT/('api-page-'+hashlib.sha256(source.encode()).hexdigest()+'.html')
            if expected.exists():archive=expected.name
        if not archive and g.get('source')=='existing_cache':archive=g.get('source_path')
        if not archive:
            archive=next((e.get('response_file')for e in g.get('attempts',[])if e.get('path')==source and e.get('response_file')),None)
        row.update(status='success',abstract=g['abstract'],abstract_source=source,source_archive=archive,extractor=extractor(source or''),quality='source_abstract_verified_title_and_identifier',reason=g.get('reason'))
        accepted[a['id']]=row
    else:
        queried=[e for e in page_attempts if e.get('status')!='not_queried']
        blocking=[e for e in api_attempts+page_attempts if e.get('status')in('not_queried','query_failed')and ('http_4' in str(e.get('reason'))or'blocked' in str(e.get('reason')))]
        plausible=[c for c in candidates if SequenceMatcher(None,pages.norm(a['title']),pages.norm(c.get('title')or'')).ratio()>=.9 and c.get('reason')not in('bibliographic_citation_not_abstract','reference_list','html_or_access_page')]
        row['review_candidate_count']=len(plausible);row['rejected_unrelated_candidate_count']=len(candidates)-len(plausible)
        if plausible:row.update(status='candidate_requires_review',reason='similar_title_abstract_found_but_identity_or_version_not_verified')
        elif blocking:row.update(status='unresolved_access_limited',reason='one_or_more_source_routes_blocked_or_rate_limited')
        elif not queried:row.update(status='unresolved_pages_not_queried',reason='api_did_not_supply_accepted_abstract_and_no_supported_publication_page_was_queried')
        else:row.update(status='unresolved_after_page_attempt',reason='retrieved_pages_did_not_yield_verified_abstract; not_a_claim_that_no_abstract_exists')
        row['publication_page_status']='not_queried'if not queried else'queried_with_failure_or_block'if any(e.get('status')=='query_failed'for e in queried)else'retrieved_without_accepted_abstract'
        if not queried:row['publication_page_nonquery_reason']='publisher_domain_access_block'if blocking else'no_publication_url_or_identifier_in_target_metadata'if not a['landing_urls']else'available_identifiers_have_no_supported_publication_landing_url_in_cached_metadata'
    merged.append(row)
nodes=json.loads((ROOT/'outputs/paper-atlas/data.json').read_text(encoding='utf8'))['nodes'];allrows=[]
for p in nodes:
    g=accepted.get(p['id'])
    if g:abstract=g['abstract'];source={'url_or_cache':g['abstract_source'],'archive':g['source_archive'],'extractor':g['extractor']};quality=g['quality'];status='backfilled_verified'
    elif p.get('abstract')and p['id']!='lab-d99ee9ba4a13':abstract=p['abstract'];source=(p.get('metadata_sources')or{}).get('abstract')or p.get('source');quality='existing_abstract_not_individually_reverified';status='existing_unverified'
    else:abstract=None;source=None;quality='missing_or_unverified_candidate';status='missing'
    allrows.append({'id':p['id'],'title':p['title'],'abstract':abstract,'lab':p['lab'],'abstract_source':source,'quality':quality,'status':status})
summary={'targets':len(merged),'backfilled':len(accepted),'backfilled_lab':sum(r['lab']for r in accepted.values()),'backfilled_external':sum(not r['lab']for r in accepted.values()),'remaining':len(merged)-len(accepted),'remaining_lab':sum(r['lab']and r['status']!='success'for r in merged),'remaining_external':sum(not r['lab']and r['status']!='success'for r in merged),'target_statuses':dict(collections.Counter(r['status']for r in merged)),'all_papers':len(allrows),'all_with_abstract':sum(bool(r['abstract'])for r in allrows),'existing_abstracts_not_reverified':sum(r['status']=='existing_unverified'for r in allrows),'new_crossref_abstracts':sum('api.crossref'in str(r.get('abstract_source'))for r in accepted.values()),'production_data_modified':False,'keywords_generated':False,'network_or_vectors_recomputed':False}
assert len({r['id']for r in allrows})==len(allrows)==1673
assert len({r['id']for r in merged})==len(merged)==337
assert next(x for x in allrows if x['id']=='lab-d99ee9ba4a13')['status']=='backfilled_verified'
(OUT/'merged-abstracts.json').write_text(json.dumps({'summary':summary,'results':merged},ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'all-papers-with-abstracts.json').write_text(json.dumps({'summary':summary,'papers':allrows},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False),flush=True)
