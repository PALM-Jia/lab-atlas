from pathlib import Path
p=Path('outputs/paper-atlas/workflow-data.js')
s=p.read_text(encoding='utf-8')
needle="stages:['collect','external','adopt','output']},\n ]"
s=s.replace(needle,"stages:['collect','external','adopt','output']},\n  {id:'output',label:'检索汇总',color:'#89909c',fields:'各论文字段及其来源原值、采集时间、采用理由和获取状态的汇总视图',collect:'读取其他信息项附带的记录，不单独采集一份来源证据。',fixed:'按条目输出字段结果和缺失状态，不要求所有字段齐全。',used:'显示字段到位情况，并分别报告被引总数、取得的施引条目数、其中已匹配详情的条目数。',stages:['output']}\n ]")
s=s.replace("['summary','counts',6,", "['summary',null,6,")
s=s.replace("].map(([id,info,stage,label,detail,definition])=>({id,info,stage,label,detail,definition}));", "].map(([id,info,stage,label,detail,definition])=>({id,info,stage,label,detail,definition,...(id==='summary'?{track:'output'}:{})}));")
p.write_text(s,encoding='utf-8')
