from pathlib import Path
p=Path('work/check_author_semantic_current.cjs');s=p.read_text(encoding='utf8');s=s.replace("el('search').value='semi-supervised';el('search').oninput({target:el('search')});",'');p.write_text(s,encoding='utf8')
