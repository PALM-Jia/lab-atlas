# coding: utf-8
from pathlib import Path
p=Path('outputs/paper-atlas/app.js');s=p.read_text(encoding='utf-8').replace("  const knownYears=D.nodes.map(p=>p.year).filter(Number.isFinite);\n  const yearBounds=knownYears.length?[Math.min(...knownYears),Math.max(...knownYears)]:[2026,2026];", "  const yearBounds=[2010,2027];")
s=s.replace('p.year<state.yearFrom||p.year>state.yearTo','Math.max(yearBounds[0],p.year)<state.yearFrom||p.year>state.yearTo')
s=s.replace('const years=visible.map(p=>p.year).filter(Number.isFinite);','const years=visible.map(p=>p.year).filter(Number.isFinite).map(y=>Math.max(yearBounds[0],y));')
s=s.replace('yearBounds:years.length?[Math.min(...years),Math.max(...years)]:yearBounds,reset:', 'yearBounds:years.length?[Math.min(...years),Math.max(...years)]:yearBounds,lowerYearBucket:2010,reset:')
s=s.replace("$('year-output').textContent=state.yearFrom===state.yearTo?String(state.yearFrom):`${state.yearFrom} — ${state.yearTo}`;", "const fromLabel=state.yearFrom===yearBounds[0]?'−∞':String(state.yearFrom);\n    $('year-output').textContent=state.yearFrom===state.yearTo?(state.yearFrom===yearBounds[0]?'≤2010':fromLabel):`${fromLabel} — ${state.yearTo}`;")
s=s.replace("$('year-from').setAttribute('aria-valuetext',`${state.yearFrom} 年`);", "$('year-from').setAttribute('aria-valuetext',state.yearFrom===yearBounds[0]?'负无穷，包含2010年及更早论文':`${state.yearFrom} 年`);")
s=s.replace("$('year-to').setAttribute('aria-valuetext',`${state.yearTo} 年`);", "$('year-to').setAttribute('aria-valuetext',state.yearTo===yearBounds[0]?'2010年及更早论文':`${state.yearTo} 年`);")
p.write_text(s,encoding='utf-8')
p=Path('outputs/paper-atlas/index.html');s=p.read_text(encoding='utf-8').replace('包含年份未知</label>','包含年份未知</label><p class="year-note">左端 −∞ 包含 2010 年及更早论文</p>');s=s.replace('<div id="detail-content">','<section id="relation-explanation" class="relation-explanation" aria-label="当前关联依据"></section><div id="detail-content">');p.write_text(s,encoding='utf-8')
p=Path('outputs/paper-atlas/panel-layout.css');s=p.read_text(encoding='utf-8')+'''\n.year-note { margin:4px 0 0; color:var(--muted); font-size:11px; line-height:1.5; }
.relation-explanation { margin-top:14px; padding:12px; background:var(--soft); border:1px solid var(--line); border-radius:8px; }
.relation-explanation h3 { margin:0 0 6px; font-size:15px; }
.relation-explanation p { margin:5px 0; font-size:13px; line-height:1.6; }
.relation-explanation .relation-stats { color:var(--muted); font-size:12px; }
''';p.write_text(s,encoding='utf-8')
