from pathlib import Path
p=Path('work/download_semantic_model.py');s=p.read_text(encoding='utf8');s=s.replace("'--retry','2','--max-time'","'--retry','3','--retry-all-errors','--max-time'");p.write_text(s,encoding='utf8')
