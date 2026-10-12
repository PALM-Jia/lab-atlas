import argparse, concurrent.futures, datetime, hashlib, json, pathlib, shutil, subprocess, time

BASE = pathlib.Path(__file__).resolve().parent.parent
NODE = pathlib.Path('C:/Program Files/nodejs/node.exe')
CLI = pathlib.Path('C:/Program Files/nodejs/node_global/node_modules/@openai/codex/bin/codex.js')

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def run(row):
    rid = row['run_id']
    work = BASE / 'isolated' / rid
    work.mkdir(parents=True, exist_ok=True)
    logs = BASE / 'execution-logs'
    logs.mkdir(exist_ok=True)
    result = BASE / row['output_path']
    temp = logs / (rid + '.raw-output.json')
    if result.exists() or temp.exists():
        raise RuntimeError('Refusing to overwrite ' + rid)
    instructions = (BASE / 'annotation-instructions.txt').read_text(encoding='utf-8-sig')
    vocab = (BASE / 'vocabulary-for-annotation.json').read_text(encoding='utf-8-sig')
    sample = (BASE / 'inputs' / (row['sample_id'] + '.json')).read_text(encoding='utf-8-sig')
    prompt = ('独立完成一次论文关键词标注。当前上下文已提供全部允许材料；不读取文件，不调用任何工具、代理或网络，不查找外部资料。不需要写文件。直接返回遵循schema的JSON对象，不加Markdown。下方共同指令中的文件读取和结果写入由控制端完成，你只依据下方完整材料判断。\n\n共同指令：\n' + instructions + '\n\n完整固定词表（49词）：\n' + vocab + '\n\n唯一论文样本：\n' + sample)
    args = [str(NODE), str(CLI), 'exec', '--ephemeral', '--ignore-user-config', '--sandbox', 'read-only', '--skip-git-repo-check', '--model', row['model'], '-c', 'model_reasoning_effort="medium"', '--output-schema', str(BASE / 'annotation-output.schema.json'), '-o', str(temp), '--json', '-']
    meta = {'run_id': rid, 'sample_id': row['sample_id'], 'requested_model': row['model'], 'reasoning_effort': 'medium', 'arguments': args, 'cwd': str(work), 'started_at': now(), 'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(), 'prompt_characters': len(prompt)}
    (logs / (rid + '.prompt.txt')).write_text(prompt, encoding='utf-8')
    start = time.monotonic()
    with (logs / (rid + '.jsonl')).open('wb') as out, (logs / (rid + '.stderr.txt')).open('wb') as err:
        process = subprocess.run(args, input=prompt.encode('utf-8'), stdout=out, stderr=err, cwd=work, timeout=900, shell=False)
    meta.update(exit_code=process.returncode, finished_at=now(), elapsed_seconds=round(time.monotonic()-start, 3))
    events = []
    for line in (logs / (rid + '.jsonl')).read_text(encoding='utf-8').splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    items = [event.get('item', {}) for event in events if event.get('type') == 'item.completed']
    meta['completed_item_types'] = [item.get('type') for item in items]
    meta['tool_item_count'] = sum(item.get('type') in ('command_execution', 'mcp_tool_call', 'web_search', 'file_change', 'tool_call') for item in items)
    meta['errors'] = [event for event in events if event.get('type') in ('error', 'turn.failed')]
    meta['output_exists'] = temp.exists()
    if process.returncode == 0 and temp.exists():
        raw = temp.read_bytes()
        try:
            parsed = json.loads(raw)
            meta['json_valid'] = True
            meta['reported_sample_id'] = parsed.get('sample_id')
        except Exception as error:
            meta['json_valid'] = False
            meta['parse_error'] = str(error)
        shutil.copyfile(temp, result)
        meta['output_sha256'] = hashlib.sha256(raw).hexdigest()
    (logs / (rid + '.metadata.json')).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(meta, ensure_ascii=False), flush=True)
    return meta

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['probe', 'remaining'])
    opts = parser.parse_args()
    rows = json.loads((BASE / 'control/run-map.json').read_text(encoding='utf-8-sig'))['runs']
    if opts.mode == 'probe':
        rows = [r for r in rows if r['run_id'] in ('run002', 'run004')]
    else:
        rows = [r for r in rows if not (BASE / r['output_path']).exists()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2 if opts.mode == 'probe' else 4) as pool:
        list(pool.map(run, rows))
