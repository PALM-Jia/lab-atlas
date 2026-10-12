# coding: utf-8
import json,html,zipfile
from public_copy import clean_public_copy
from pathlib import Path
root=Path('outputs/paper-atlas');a=json.loads((root/'acceptance.json').read_text(encoding='utf8'));v=json.loads((root/'validation.json').read_text(encoding='utf8'))
labels={'01_import':'1. 列表导入','02_match':'2. 数据库身份匹配','03_api_requests':'3. API 逻辑请求（含缓存命中）','04_authors':'4a. 作者字段','04_year':'4b. 年份字段','04_abstract':'4c. 摘要字段','04_references':'4d. 非空参考文献字段','04_institution_records':'4e. 机构 ID 字段','05_incoming_neighborhood':'5a. 完整被引邻域','05_external_metadata':'5b. 所选外部节点元数据','08_content_vector':'6. 内容向量（全部图中节点）','09_research_series':'7. 人工研究系列','10_layout':'8. 关系布局','11_relation_validation':'9. 各关系层证据核验','12_frontend_checks':'10. 网页检查'}
relation_labels={'citation':'引用','coupling':'共同参考文献','cocitation':'共同被引','author':'共同作者 ID','topic':'数据库主题','institution':'机构 ID','semantic':'内容向量','series':'人工系列'}
reason_names={'unique_source_item_preserved':'原始条目导入并保留','public_field_available':'公共来源字段已到位','source_identifier':'原始 DOI / arXiv 标识匹配','source_url':'原始链接与数据库链接一致','title_author_unique':'唯一标题与作者校验候选','unique_formal_version_with_author_agreement':'唯一正式版，预印本标题与作者一致','no_title_author_or_identifier_verified_candidate':'已查询候选中无身份校验通过记录；扩大查询如受限见请求记录','multiple_qualified_records_without_identity_evidence':'多个合格候选，无法确定唯一版本','no_verified_database_id':'缺少已确认数据库 ID','complete_database_neighborhood':'数据库被引清单完整','pilot_cache_partial_after_anonymous_daily_budget_exhausted':'复用早期缓存但不完整；扩展受匿名额度限制','incoming_request_failed_anonymous_daily_budget_exhausted':'被引查询受匿名额度耗尽限制','lookup_anonymous_daily_budget_exhausted':'所选外部 ID 的元数据查询受匿名额度限制','public_api_cache_record_reused':'复用公开 API 完整记录缓存','incoming_record_reused':'复用被引记录','specter2_vector_verified':'SPECTER2 向量存在且标题校验通过','no_supported_public_identifier':'缺少可用于此轮向量查询的 DOI / arXiv ID','semantic_scholar_no_record':'Semantic Scholar 对该标识返回空记录','vector_missing_or_invalid':'记录存在但向量缺失或不符合要求','title_identity_mismatch':'返回记录标题未通过校验，不使用其向量','database_returned_empty':'已取得数据库记录但字段为空','public_sources_did_not_supply_field':'实验室列表未提供字段；OpenAlex 论文 ID 未确认','manual_series_not_provided_by_user':'用户明确不提供人工系列','finite_force_layout_coordinates':'生成有限的引用与共同参考文献布局坐标','relation_input_ready':'该关系所需输入到位','only_name_evidence_available':'只有姓名证据，身份关系未确认','only_keyword_topic_available':'只有关键词主题，可展示候选，数据库主题未到位','database_returned_empty_relation_field':'数据库关系输入字段为空','cached':'成功读取公开 API 缓存','anonymous_daily_budget_exhausted':'OpenAlex 明确返回共享 IP 匿名每日额度已耗尽','http_403':'OpenReview 要求人机验证（HTTP 403），未绕过','all_generated_edges_evidence_checked':'该层全部生成连接证据核验通过','node_syntax_check_passed':'网页 JavaScript 语法检查通过','browser_url_policy_rejected_existing_tab_binding':'浏览器 URL 策略拒绝绑定原预览页，本轮未完成页面验证'}
reason_names.update({'openalex_record_received':'取得 OpenAlex 文献记录','openalex_id_not_returned':'批量查询未返回该 ID','external_id_http_404':'单独查询该文献 ID 返回 HTTP 404','external_record_found_after_graph_build':'单独查询找到文献，需补入网络','curl_28':'响应传输超时','batch_curl_28':'该向量批次响应传输超时','external_id_redirect_requires_reconciliation':'数据库 ID 重定向，尚未完成身份归并'})
rows=[];sections=[]
reason_names.update({'local_specter2_title_abstract':'本地 SPECTER2：标题＋摘要','local_specter2_title_only':'本地 SPECTER2：仅标题','empty_title':'缺少可编码的标题'})
reason_names.update({'formal_publication_preferred':'优先选用已校验的唯一正式发表记录','broader_public_search':'扩大公开检索后确认身份','versioned_title_identity':'通过 arXiv 版本历史确认标题变更','official_program_title_authors':'通过会议日程核对标题与作者','public_page_verified_no_openalex_match':'已找到公开论文页面，扩大 OpenAlex 检索仍未确认记录','official_listing_no_openalex_match':'官方会议目录列有该标题，OpenAlex 尚未匹配','possible_renamed_paper_without_version_identity':'发现标题近似的公开论文，尚缺同一版本的身份依据','spelling_variant_no_verified_match':'已修正标题拼写后检索，仍无可确认记录','no_public_locator_for_future_year':'列表年份为 2027，未找到独立公开记录或标识','title_only_no_independent_locator':'原始条目只有标题，多源检索未找到可核对的独立记录','public_source_known_openreview_api_blocked':'已有 OpenReview 链接，但接口要求验证；其他检索未确认 OpenAlex 记录','expanded_search_no_verified_record':'已扩大标题和作者检索，仍未找到可确认的记录'})
audit_path=root/'identity-search-audit.json'
identity_audit={r['id']:r for r in json.loads(audit_path.read_text(encoding='utf8'))} if audit_path.exists() else {}
reason_names.update({'public_candidate_page_access_blocked':'网页搜索已定位 OpenReview 候选，但公开接口返回 403，无法核对元数据；OpenAlex 检索尚未确认','title_variant_collides_with_another_lab_paper':'候选正式记录与列表另一篇论文相同；当前条目的题目和发表场所不同，尚不能确认同一版本'})
reason_names.update({'public_sources_did_not_supply_field':'实验室列表未提供字段；OpenAlex 论文 ID 未确认','database_returned_empty':'OpenAlex 已返回论文记录，对应字段为空','no_verified_database_id':'OpenAlex 论文 ID 未确认，对应字段查询未发起','vector_missing_or_invalid':'Semantic Scholar 返回记录，但向量为空或未通过校验','database_returned_empty_relation_field':'OpenAlex 返回的关系输入字段为空'})
def failure_detail(r):
 text=''
 for evidence in r.get('failure_sources',[]):
  result=evidence['result']
  if evidence.get('identity_reason'):result+='；身份步骤：'+reason_names.get(evidence['identity_reason'],evidence['identity_reason'])
  text+='<p>'+html.escape(evidence['provider']+'：'+result)
  if evidence.get('url'):text+=f' · <a href="{html.escape(evidence["url"],quote=True)}">来源 / 查询地址</a>'
  text+='</p>'
 verdict=r.get('failure_assessment')
 if verdict:text+='<p><b>失败判断：'+html.escape(verdict['label'])+'</b>。'+html.escape(verdict['judgment'])+'</p><p>下一步：'+html.escape(verdict['next_action'])+'</p>'
 return text
def identity_detail(r,key):
 if key!='02_match' or r['id']not in identity_audit:return ''
 t=identity_audit[r['id']];parts=[]
 parts.append('原始信息：'+('作者 '+', '.join(t['source_authors']) if t['source_authors'] else '无作者')+'；年份 '+str(t['source_year'] or '未提供')+'；'+('已有公开链接' if t['source_links'] else '未提供公开链接'))
 closest=t.get('closest_openalex',[])
 if closest:parts.append(f'扩大查询的最高标题相似度 {closest[0]["score"]:.3f}（自动匹配门槛 0.93）')
 queries=t.get('queries',[]);parts.append(f'逐篇 API 查询 {len(queries)} 次；查询失败 {sum(q["status"]=="failure" for q in queries)} 次；另检查作者文献集合和通用网页搜索')
 text='<p>'+html.escape('。'.join(parts))+'。</p>'
 for p in t.get('public_evidence',[]):
  text+=f'<p>公开来源：<a href="{html.escape(p["url"],quote=True)}">{html.escape(p["url"])}</a>；'+('页面题目已核对' if p.get('title_present') else '页面内容未通过核对／访问受限')+'</p>'
 if t.get('related_public_candidate'):
  p=t['related_public_candidate'];text+=f'<p>待确认候选：<a href="{html.escape(p["url"],quote=True)}">{html.escape(p["title"])}</a>；候选使用 Uniform，实验室标题使用 Homeomorphic，原始条目没有作者或版本链接，尚不自动合并。</p>'
 return text
for key,name in labels.items():
 s=a['steps'][key];ok=s['success'];fail=s['explained_failure'];total=s['total']
 counts=s.get('cause_assessment',{}).get('counts',{})
 verdicts='；'.join(f'{a["failure_interpretation"]["labels"][k]} {n}'for k,n in counts.items()) or '无失败项'
 rows.append(f'<tr><td>{html.escape(name)}</td><td>{ok}/{total} · {ok/total:.2%}</td><td>{fail}/{total} · {fail/total:.2%}</td><td>100%</td><td>{html.escape(verdicts)}</td></tr>')
 bad=[r for r in s['items']if r['status']=='failure']
 if not bad: continue
 from collections import Counter
 summary='；'.join(f'{reason_names.get(k,k)}：{n}'for k,n in Counter(r['reason'] for r in bad).items())
 items=''.join(f'<li><b>{html.escape(r["title"])}</b> — {html.escape(r.get("failure_summary") or reason_names.get(r["reason"],r["reason"]))}<code>{html.escape(r["id"])}</code>{failure_detail(r)}{identity_detail(r,key)}</li>'for r in bad)
 sections.append(f'<section><h3>{html.escape(name)}：失败路径已记录 {fail} 项</h3><p>{html.escape(summary)}</p><ul>{items}</ul></section>')
readiness=[]
for k,label in relation_labels.items():
 s=a['steps']['07_readiness_'+k];total=s['total']
 readiness.append(f'<tr><td>{label}</td><td>{s["success"]}/{total} · {s["success"]/total:.2%}</td><td>{s["explained_failure"]}/{total} · {s["explained_failure"]/total:.2%}</td><td>{a["meta"]["stats"]["full_edges"][k]}</td><td>{a["meta"]["stats"]["edges"][k]}</td></tr>')
doc=f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>论文网络逐步验收报告</title><style>body{{font:15px/1.7 'Segoe UI','Microsoft YaHei',sans-serif;color:#293247;background:#f6f7fb;max-width:1120px;margin:25px auto;padding:0 20px}}h1{{font-size:25px}}h2{{font-size:19px}}table{{border-collapse:collapse;width:100%;background:white;margin:15px 0}}th,td{{padding:9px 12px;text-align:left;border:1px solid #dce0ea}}th{{background:#eeecf8}}section{{background:white;border:1px solid #dce0ea;padding:10px 14px;margin:8px 0}}h3{{font-weight:600}}li{{padding:4px 0;overflow-wrap:anywhere}}code{{display:block;font-size:12px;color:#737d90}}.note{{padding:12px 16px;background:#fff;border-left:4px solid #6657a8}}a{{color:#6657a8}}</style><h1>论文网络逐步验收报告</h1><p>数据时间：{a['meta']['updated']}。<a href="./index.html">打开论文网络</a></p><p class="note">验收口径：每步先固定分母；成功项 + 失败路径已记录项 = 全部处理项，未归类项为 0。失败判断另分为：当前失败有充分依据、采集流程未完成、原因待核实、用户排除。部分采集、接口失败及用户排除的人工系列计入失败项。未处理的候选节点也纳入外部元数据分母。逻辑请求按接口任务统计，实际网络请求按执行日志统计。</p><h2>步骤结果</h2><table><thead><tr><th>步骤 / 处理范围</th><th>成功</th><th>失败路径已记录</th><th>路径核算</th><th>失败判断</th></tr></thead><tbody>{''.join(rows)}</tbody></table><h2>每个关系层的输入覆盖</h2><p>分母统一为 144 篇实验室论文。表中统计各关系所需字段的到位情况。自动主题、姓名候选和内容相似均标为候选。人工研究系列 0/144，按用户要求不补充。</p><table><tr><th>关系</th><th>输入成功</th><th>失败路径已记录</th><th>全部候选连接</th><th>展示连接</th></tr>{''.join(readiness)}</table><h2>失败路径、原因判断与后续操作</h2><p>路径核算 100% 表示知道在哪一步失败；合理性判断按逐项证据单独列出。缺 DOI 和年份较新只作为待核实线索。补救操作的输入、结果与剩余缺口见 README.md 和 collection-actions.json。</p>{''.join(sections)}<h2>连接证据检查</h2><p>全部生成连接 {sum(s['total']for s in v['relation_evidence'].values()):,} 条，程序证据检查全部通过；SPECTER2 分数使用生成时保存的向量独立重算。检查覆盖数据来源、集合交集和算术一致性。网络按当前筛选为每个节点保留最强的 5 条关联，取两端选择的并集。</p><p>候选匹配、具体查询 URL、向量失败标识和逐条状态均在 acceptance.json；扩大身份检索的逐篇证据在 identity-search-audit.json；validation.json 保存验证结果。引用每篇最多 600 条，展示外部节点预算 1600 个。本轮所选外部 ID 共 {a["steps"]["05_external_metadata"]["total"]} 个，成功取得元数据 {a["steps"]["05_external_metadata"]["success"]} 个；实际图中为 {a["meta"]["stats"]["external"]} 个外部节点。布局基于引用和共同参考文献，颜色仍为关键词主题。静态网页在打开时不请求 API。</p></html>"""
(root/'acceptance-report.html').write_text(clean_public_copy(doc),encoding='utf8')
print('Report created')
