# coding: utf-8
from pathlib import Path
p=Path('outputs/paper-atlas/timeline-3d.js');s=p.read_text(encoding='utf-8');a=s.index('      const step =');b=s.index('      for (const year of',a);s=s[:a]+'''      const tickCount=Math.max(2,Math.min(5,Math.floor(width/150)));
      const ticks=new Set(Array.from({length:tickCount},(_,i)=>Math.round(min+span*i/(tickCount-1))));
'''+s[b:];s=s.replace("label({x:-560,y:340,z:285},'年份未知');", "label({x:-650,y:375,z:285},'年份未知');")
p.write_text(s,encoding='utf-8')
