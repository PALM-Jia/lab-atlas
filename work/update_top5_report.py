from pathlib import Path
for p in [Path('work/make_report.py'),Path('outputs/paper-atlas/acceptance-report.html')]:
 s=p.read_text(encoding='utf8').replace('语义关联按当前筛选控制连接密度，优先让至少 95% 有足够候选的实验室论文具有两条连接。','网络按当前筛选为每个节点保留最强的 5 条关联，取两端选择的并集。');p.write_text(s,encoding='utf8')
