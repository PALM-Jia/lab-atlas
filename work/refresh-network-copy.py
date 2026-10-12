# -*- coding: utf-8 -*-
"""Apply concise current wording to network UI and the retired keyword route."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'outputs/paper-atlas'
path = out / 'app.js'
text = path.read_text(encoding='utf-8')
text = text.replace('<div class="detail-meta" style="margin-top:22px">关联 · ${esc(kinds[e.kind] || e.kind)}</div><h2 class="detail-title">连接的依据</h2><div class="detail-meta">', '<div class="detail-meta" style="margin-top:22px">')
text = text.replace('<div class="detail-meta" style="margin-top:22px">作者</div><h2 class="detail-title">', '<h2 class="detail-title">')
text = text.replace('href="retrieval.html" target="_blank" rel="noopener">关键词标注结果', 'href="retrieval.html?field=keywords" target="_blank" rel="noopener">查看关键词依据')
path.write_text(text, encoding='utf-8')
path = out / 'retrieval.js'
text = path.read_text(encoding='utf-8')
addition = " if(state.view!=='authors'&&Object.hasOwn(names,params.get('field')))state.field=params.get('field');\n"
if addition not in text:
    position = text.index(' const esc=v=>')
    text = text[:position] + addition + text[position:]
path.write_text(text, encoding='utf-8')
path = out / 'keyword-missing.html'
backup = root / 'work/keyword-integration/backups/keyword-missing.html'
if not backup.exists():
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_bytes(path.read_bytes())
path.write_text('''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>关键词 · Lab Atlas</title><link rel="stylesheet" href="theme.css"><style>body{margin:0;background:#f6f7fa;color:#243044;font:16px/1.6 system-ui,sans-serif}main{max-width:900px;margin:auto;padding:28px}h1{font-size:22px}a{color:#4772cf;text-decoration:none}a:hover{text-decoration:underline}</style></head><body><main><a href="index.html">Lab Atlas</a><h1>关键词</h1><p>论文关键词、原文依据及未采用原因见检索汇总。</p><a href="retrieval.html?field=keywords">查看关键词依据 ↗</a></main></body></html>''', encoding='utf-8')
print('Network copy and keyword entry updated.')
