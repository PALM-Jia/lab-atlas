# coding: utf-8
from pathlib import Path
import json
root=Path('outputs/paper-atlas')
changes={
 '未提供人工研究系列，按要求不自动推断。':'研究系列未添加。',
 '当前筛选未观测到这类连接。节点仍可查看；数据缺失不等于不存在关系。':'当前筛选暂无此类连接。',
 '暂缺摘要，保留条目。不会仅凭标题生成已验证的内容关联。':'暂无摘要。',
 '<p class="detail-note">被引数量为数据库计数；未找到记录不能解释为没有引用。</p>':'',
 '这是一条候选关联，请结合上方证据判断；尚未经人工确认。':'候选关联',
 '时间视图不自动推断继承关系。研究系列需要人工确认，目前未添加。':'研究系列未添加。',
 '本页为相关文献网络切片，不能用于判断全球中心性。':'',
 '位置依据引用关系计算，不代表精确学术距离。':'布局依据引用与共同参考文献。',
 '坐标由引用与共同参考文献关系迭代计算；视觉距离不是精确相似度。':'坐标由引用与共同参考文献关系迭代计算。',
 '关键词规则推断的共享主题；不是引用证据':'关键词规则推断的共享主题',
 '实验室人工确认的同系列论文；不自动判断扩展方向':'实验室人工确认的同系列论文',
 '主题标签为规则推断，默认不将其连线当成已验证关系。':'主题标签采用关键词规则推断。',
 '共同被引基于已采集引用论文；缺失不等于零。':'共同被引基于已采集引用论文。',
 '预置坐标按主题分区，仅帮助浏览，不表示精确学术距离。':'预置坐标按主题分区。',
 'Uniform 候选与 Homeomorphic 原始标题是否对应仍待核实，不能直接合并。':'Uniform 候选与 Homeomorphic 原始标题是否对应仍待核实。',
 '访问失败不等于论文身份无法确认。':'',
 '布局距离不是精确相似度。':'布局依据引用和共同参考文献计算。',
 '论文节点大小区分来源，不表示被引量。':'论文节点大小区分来源。',
 '不代表原因合理或验收完成。':'原因判断另行核查。',
 '缺 DOI 不足以解释身份检索失败。':'无 DOI 时继续执行标题检索。',
 '仅凭年份不能作此判断。':'逐篇核对公开日期和查询响应。',
 '用户明确不提供人工系列，不自动推断':'用户明确不提供人工系列',
 '接口逻辑请求包含缓存读取与因明确额度限制终止的请求，不等于实际网络请求次数。':'逻辑请求按接口任务统计，实际网络请求按执行日志统计。',
}
files=[root/'app.js',root/'index.html',root/'README.md',root/'pipeline.py',root/'collect.py',Path('work/make_report.py')]
for p in files:
 s=p.read_text(encoding='utf-8-sig')
 for before,after in changes.items():s=s.replace(before,after)
 if p.name=='app.js':s=s.replace('<span>被引数量</span>','<span>数据库被引数</span>')
 p.write_text(s,encoding='utf8')
# Update owned display text; scientific titles, abstracts and source snapshots stay untouched.
def clean(value):
 if isinstance(value,str):
  for before,after in changes.items():value=value.replace(before,after)
  return value
 if isinstance(value,list):return [clean(x) for x in value]
 if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
 return value
p=root/'data.json';data=json.loads(p.read_text(encoding='utf8'))
data['meta']=clean(data['meta'])
for edge in data['edges']:
 if 'evidence' in edge:edge['evidence']=clean(edge['evidence'])
p.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8')
(root/'data.js').write_text('window.ATLAS_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
p=root/'relations-full.json';relations=json.loads(p.read_text(encoding='utf8'))
p.write_text(json.dumps(clean(relations),ensure_ascii=False,separators=(',',':')),encoding='utf8')
print('Display copy and generators updated.')
