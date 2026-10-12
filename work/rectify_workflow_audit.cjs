const fs=require('node:fs'),vm=require('node:vm');const dir='outputs/paper-atlas/';
let html=fs.readFileSync(dir+'workflow.html','utf8');
html=html.replace('<div class="intro"><h1>从论文清单到关系与特征</h1></div>','<div class="intro"><h1>论文信息处理流程</h1><span class="design-label">流程设计</span></div>');
html=html.replace('<small>阶段规则；实际到位情况见检索汇总。横轴为处理阶段，不代表耗时</small>','');
html=html.replace('<div class="chart-key">','<div class="chart-toolbar"><div class="chart-key">');
html=html.replace('</div><div id="lifecycle-scroll"','</div><button id="clear" class="quiet" hidden>取消高亮</button><span id="selection-caption" class="sr-only" aria-live="polite"></span></div><nav id="stage-navigation" aria-label="横向定位处理阶段" hidden></nav><div id="lifecycle-scroll"');
html=html.replace(/<div class="map-actions">[\s\S]*?<\/div>\s*/,'');
fs.writeFileSync(dir+'workflow.html',html);
const css=`/* Workflow uses the shared Atlas controls and palette. */
*{box-sizing:border-box}
body{margin:0;height:100dvh;overflow:hidden;display:flex;flex-direction:column;background:var(--bg);color:var(--text);font-size:14px;line-height:1.6}
button{font:inherit}a{color:var(--accent);text-decoration:none}h1,h2,p{margin:0}
main{flex:1;min-height:0;overflow:auto;padding:14px 18px 24px;width:100%;max-width:1880px;margin:0 auto}
.intro{display:flex;align-items:center;gap:12px;margin-bottom:10px}h1{font-size:20px;line-height:1.4;font-weight:600}.design-label{font-size:12px;color:var(--muted)}
.chart-toolbar{display:flex;align-items:center;gap:14px;margin-bottom:8px;min-height:26px}.chart-key{display:flex;align-items:center;flex-wrap:wrap;gap:8px 18px;color:var(--muted);font-size:12px}.chart-key>span{display:flex;align-items:center;gap:7px}.chart-toolbar #clear{margin-left:auto;flex-shrink:0}
.key-source{display:inline-block;width:21px;height:14px;border:1px solid #8c7abc;border-radius:3px;background:#f5f3fa}.key-line{width:26px;border-top:2px solid #7c879e}.key-line.optional{border-top-style:dashed}.key-process{display:inline-block;width:24px;height:14px;border:1px solid #aaa3bd;border-radius:9px;background:#eeebf6}
#stage-navigation{display:flex;align-items:center;gap:4px;margin:0 0 8px;padding:0;font-size:12px}#stage-navigation .stage-jump{border:1px solid var(--line);border-radius:var(--control-radius);padding:4px 8px;color:var(--text);background:var(--paper);font-size:12px;line-height:1.4;white-space:nowrap}#stage-navigation .stage-jump:hover{background:var(--soft);border-color:#cfc8e2;color:var(--accent)}.scroll-hint{color:var(--muted);font-size:12px;margin-left:6px}
.chart-scroll{overflow-x:auto;overflow-y:hidden;border:1px solid var(--line);border-radius:var(--control-radius);background:var(--paper);overscroll-behavior-x:contain}.chart-scroll:focus-visible{outline:1px solid var(--accent);outline-offset:2px}
#lifecycle-board{position:relative}.lifecycle-header{height:76px;position:relative;pointer-events:none}.stage-header{position:absolute;top:0;height:76px;padding:10px 4px;text-align:center;pointer-events:auto;border:0;border-bottom:1px solid var(--line);background:transparent;color:var(--text);line-height:1.5}.stage-header strong{display:block;font-size:13px;font-weight:600}.stage-header small{display:block;margin-top:5px;font-size:12px;color:var(--muted)}.stage-header:hover,.stage-header[aria-pressed=true]{background:var(--soft);color:var(--accent)}
.flow-row{position:absolute;left:0;width:100%;border:0;border-bottom:1px solid #e7eaf0;background:var(--paper);text-align:left;padding:0}.flow-row:nth-child(even){background:#fcfcfe}.flow-column{position:absolute;border-left:1px solid #edf0f4;pointer-events:none}.flow-group-label{position:absolute;left:12px;top:16px;width:118px;padding:0;border:0;background:transparent;color:var(--track);font-size:13px;text-align:left;font-weight:600;z-index:3}.flow-group-label:hover{text-decoration:underline;text-underline-offset:3px}
.flow-node{position:absolute;transform:translateX(-50%);display:flex;align-items:center;justify-content:center;padding:0 9px;font-size:12px;line-height:20px;white-space:pre;text-align:center;z-index:2}.flow-node.life-event,.flow-node.life-settle{border:1px solid var(--track);border-radius:var(--control-radius);color:var(--track);background:color-mix(in srgb,var(--track) 8%,white);font-weight:500}.flow-process{font-weight:600;border:1px solid #aaa3bd;border-radius:14px;background:#eeebf6;color:#544d69}.flow-node.dimmed{opacity:.3}.flow-node[aria-pressed=true]{box-shadow:0 0 0 1px var(--track)}
.flow-paths{position:absolute;inset:0;pointer-events:none;overflow:visible}.flow-ink{opacity:.65;pointer-events:none}.flow-visible{fill:none;stroke-width:1.5;stroke-linejoin:round;stroke-linecap:round;pointer-events:none}.flow-ink .query{stroke-dasharray:5 4;stroke-opacity:1}.flow-paths>.flow-hit{fill:none;stroke:transparent;stroke-width:9;stroke-opacity:1;pointer-events:stroke;cursor:help}
#inspector{max-width:1000px;margin-top:18px}.explanation-prose{padding:0;margin:0}.explanation-section{padding:14px 0}.explanation-section+.explanation-section{border-top:1px solid var(--line)}.explanation-section h2{font-size:16px;font-weight:600;line-height:1.5;margin-bottom:8px}.explanation-section p{font-size:14px;line-height:1.8;text-wrap:pretty}.explanation-section p+p{margin-top:8px}.explanation-section a{text-decoration:underline;text-underline-offset:3px}
.workflow-tooltip{position:fixed;z-index:30;width:380px;max-width:calc(100vw - 24px);padding:11px 13px;border:1px solid var(--line);border-radius:var(--control-radius);background:var(--paper);box-shadow:0 5px 22px #2932471a;font-size:13px;line-height:1.65;color:var(--text);pointer-events:none}.workflow-tooltip p+p{margin-top:7px}
.sr-only{position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip-path:inset(50%);white-space:nowrap;border:0}
@media(max-width:850px){main{padding:12px}.intro{gap:10px}h1{font-size:18px}.chart-key{gap:7px 14px}.chart-toolbar{align-items:start;flex-wrap:wrap}.chart-toolbar #clear{margin-left:0}#stage-navigation{gap:3px;flex-wrap:wrap}#stage-navigation .stage-jump{padding:4px 6px}.scroll-hint{width:100%;margin:3px 0 0}.stage-jump .jump-detail{display:none}.atlas-header .atlas-brand small{display:none}.explanation-section{padding:14px 0}}
@media print{body{height:auto;overflow:visible}main{overflow:visible;max-width:none}.atlas-header,#stage-navigation,.chart-toolbar #clear{display:none}.chart-scroll{overflow:visible}.workflow-tooltip{display:none!important}}
`;
fs.writeFileSync(dir+'workflow.css',css);
let js=fs.readFileSync(dir+'workflow.js','utf8');
js=js.replace("$('lifecycle-board').innerHTML=flow.html;",`$('lifecycle-board').innerHTML=flow.html;
// Stage shortcuts expose offscreen columns without changing vertical position.
const scroll=$('lifecycle-scroll'),nav=$('stage-navigation');
const jumpLabels=['清单','核对','详情','引用','特征'];
nav.innerHTML=data.stages.map((s,i)=>\`<button type="button" class="stage-jump" data-scroll-stage="\${i}" aria-label="横向定位到\${esc(s.title||s.label)}">\${esc(s.n||['①','②','③','④','⑤'][i])}\${jumpLabels[i]}</button>\`).join('')+'<span class="scroll-hint">横向浏览，或点击定位阶段</span>';
nav.onclick=e=>{const b=e.target.closest('[data-scroll-stage]');if(!b)return;const i=Number(b.dataset.scrollStage);scroll.scrollTo({left:i===0?0:flow.columns[i].left-flow.columns[0].left,behavior:'instant'});hideTip();};
const updateNavigation=()=>nav.hidden=scroll.scrollWidth<=scroll.clientWidth+1;
new ResizeObserver(updateNavigation).observe(scroll);updateNavigation();`);
js=js.replace("$('selection-caption').textContent=kind==='info'", "$('clear').hidden=kind==='all';\n $('selection-caption').textContent=kind==='info'");
// The explicit link is supplied by trusted explanatory content, not arbitrary text.
js=js.replace("esc(p)}</p>","esc(p).replace('【检索汇总】','<a href=\"retrieval.html\">检索汇总</a>')}</p>");
fs.writeFileSync(dir+'workflow.js',js);
const sections=[
{id:'queries',title:'身份核对与详情采集',paragraphs:[
 '流程设计把两种查询分开：先用主页标题、署名和发表情况，在 OpenAlex 与 Semantic Scholar 核对身份及版本；疑问再查原始发布页。随后按确认标识精确采集详情，以 OpenAlex 为主，其他来源按字段补缺。身份核对产生的摘要等附带详情不传入第二次查询。',
 '当前采集脚本主要在 OpenAlex 匹配身份，并复用选中记录的详情；Semantic Scholar 补充公开信息与语义向量。图中的查询分离和本地向量生成是后续调整方案。实际采用值、来源及缺失情况见【检索汇总】。']},
{id:'adoption',title:'版本与来源差异',paragraphs:[
 '同一工作可对应多个标题和标识，确认版本联系后优先采用正式版。NeurIPS 与 Neural Information Processing Systems 等缩写和全称归并；“预印”与数据库年份分别描述发表状态和年份，保留两者的来源表述。作者同名结合单位及合作证据区分，人员分类使用实验室确认的名册。',
 '核对依据与获取结果随条目记录。来源字段为空、请求失败、名单分页未完成分别说明，方便判断应补查哪个来源。']},
{id:'citations',title:'被引数与两份引用记录',paragraphs:[
 'A 引用 B：B 属于 A 的“引用文献”，A 属于 B 的“被引记录”。被引数是数据库报告的统计值；取得的被引记录数是本次查到的名单长度；匹配详情数是名单中找到对应论文信息的数量。三者分别统计，补全名单不会改写被引数。']},
{id:'external',title:'采集范围与网络显示范围',paragraphs:[
 '两份引用记录合并外部标识并去重，只采集一层外部论文。得到的信息分别补回引用文献和被引记录，未匹配条目保留原标识及原因；同一外部论文可供多条关系共用。',
 '当前每篇实验室论文最多采集 600 条被引记录，外部网络节点上限为 1600。记录的采集范围与网络显示范围分别限制，因此检索汇总中的记录可能多于图中显示的邻居。网络不绘制外部文献之间的引用边。']},
{id:'features',title:'关键词、主题与研究方向',paragraphs:[
 '论文关键词和分数来自文献库；数据库主题是 OpenAlex 的分类结果；研究方向标签由本站按标题、摘要匹配文本规则得到。三者含义与分数不同，分别用于关键词画像、主题关联和研究方向筛选。现有语义关联读取 Semantic Scholar 的 SPECTER2 向量；图中的本地生成路径使用论文自身标题及可用摘要。']},
{id:'profiles',title:'作者画像如何计分',paragraphs:[
 '关键词分数是加权论文覆盖率：该作者有关键词的署名论文中，包含这个词的论文贡献占多少。每篇论文可包含多个词，各词分数不必合计为 100%。研究方向画像则先在每篇论文的多个标签间均分贡献，再汇总为作者的研究方向占比。',
 '默认一作权重为 1，其他署名为 0.2；“全部署名”模式等权，“只计一作”模式也纳入导师 Yuheng Jia 一作、学生二作的论文。画像按当前筛选内的实验室论文计算，外部文献不贡献作者画像。']}
];
fs.writeFileSync(dir+'workflow-explanations.js','// Supplemental explanations distinguish process design from implementation.\nwindow.WORKFLOW_EXPLANATIONS = '+JSON.stringify(sections,null,2)+';\n');
// Tighten the hover copy and distinguish vector generation from existing vectors.
const c={window:{}};vm.createContext(c);vm.runInContext(fs.readFileSync(dir+'workflow-guide.js','utf8'),c);
const g=c.window.WORKFLOW_GUIDE;
g.stages.import.tooltip=['实验室主页定义论文清单范围。读取标题、署名、发表情况和链接，作为后续核对的原始依据。'];
g.stages.locate.tooltip=['流程设计通过 OpenAlex 与 Semantic Scholar 多源核对标题、署名和版本；疑问再查原始发布页。确定论文身份、基本信息和查询标识，复杂歧义才由 AI 辅助核对。'];
g.stages.collect.tooltip=['流程设计按确认的标识采集摘要、关键词、主题、被引数及两份引用记录。OpenAlex 为主，其他来源按字段补缺；不使用身份核对中附带的详情。'];
g.stages.external.tooltip=['从引用文献和被引记录提取外部标识，去重采集一层外部论文。核对版本并补充详情，输出外部文献信息和两份补全记录；被引数仍采用来源统计。'];
g.stages.features.tooltip=['研究方向标签由标题与摘要的文本规则生成，作者画像按实验室署名论文聚合。现有语义向量来自 Semantic Scholar；图中的本地向量生成是规划路径。'];
fs.writeFileSync(dir+'workflow-guide.js','window.WORKFLOW_GUIDE = '+JSON.stringify(g,null,2)+';\n');
let f=fs.readFileSync(dir+'workflow-flow-data.js','utf8');
f=f.replace("label:'生成文献特征',description:'对实验室和外部论文分别使用其自身标题与可用摘要，生成研究方向标签和语义向量。标题为必需输入，摘要可选；外部论文用自己的文本。记录实际输入、规则与模型。'","label:'生成文献特征',description:'各论文用自身标题和可用摘要生成研究方向标签。图中的本地向量生成是规划路径；现有向量直接读取 Semantic Scholar。'");
f=f.replace("label:'聚合作者画像',description:'按实验室论文署名聚合关键词及研究方向标签。一作权重 1，其他署名 0.2；导师 Yuheng Jia 一作时按第二作者计一作。两种画像独立生成，分别保留支撑论文。'","label:'聚合作者画像',description:'关键词画像计算加权论文覆盖率；研究方向画像按每篇论文的多标签均分贡献后聚合。默认一作权重 1、其他署名 0.2；“只计一作”模式也纳入导师一作、学生二作。'");
f=f.replace('按固定模型从各论文自己的标题与可用摘要生成，保留输入及模型版本。当前网络向量来自 Semantic Scholar；此处说明本地生成路径。','现有网络读取 Semantic Scholar 的 SPECTER2 向量。此节点表示规划中的本地生成结果，输入为论文自身标题和可用摘要。');
f=f.replace('按署名权重聚合实验室论文关键词与分数；缺关键词的论文不贡献该画像。','每个关键词的分数是有关键词的署名论文中，包含该词的加权论文覆盖率。来源关键词分数不参与累计。');
f=f.replace('按署名权重聚合实验室论文研究方向标签；不使用外部文献署名。','每篇论文在自身多个研究方向标签间均分贡献，再按署名权重聚合为作者占比。');
f=f.replace('按署名贡献权重聚合论文关键词及分数，形成关键词画像。','按署名贡献权重计算关键词的论文覆盖率，形成关键词画像。');
fs.writeFileSync(dir+'workflow-flow-data.js',f);
// Keep snapshot limits in prose synchronized whenever the site is packaged.
let py=fs.readFileSync('work/package_atlas.py','utf8');
if(!py.includes('workflow-explanations.js'))py=py.replace("with ZipFile",`# Sync explanatory limits from the same data snapshot used by the graph.
import json, re
payload=(root/'data.js').read_text(encoding='utf8')
limits=json.loads(payload.split('=',1)[1].strip().rstrip(';'))['meta']['limits']
prose_path=root/'workflow-explanations.js'
prose=prose_path.read_text(encoding='utf8')
prose=re.sub(r'每篇实验室论文最多采集 \\d+ 条被引记录', f"每篇实验室论文最多采集 {limits['citing_per_seed']} 条被引记录", prose)
prose=re.sub(r'外部网络节点上限为 \\d+', f"外部网络节点上限为 {limits['external_nodes']}", prose)
prose_path.write_text(prose,encoding='utf8')
with ZipFile`);
fs.writeFileSync('work/package_atlas.py',py);
