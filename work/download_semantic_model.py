import json,subprocess,hashlib
from pathlib import Path
root=Path('work/semantic-models');root.mkdir(parents=True,exist_ok=True)
for name,wanted in [('specter2_base',['config.json','pytorch_model.bin','special_tokens_map.json','tokenizer.json','tokenizer_config.json','vocab.txt']),('specter2',['adapter_config.json','pytorch_adapter.bin'])]:
 meta=json.loads(Path('work',name+'-manifest.json').read_text(encoding='utf8'));repo=root/name;repo.mkdir(exist_ok=True)
 (repo/'revision.json').write_text(json.dumps({'id':meta['id'],'revision':meta['sha']}),encoding='utf8')
 for record in meta['siblings']:
  name=record['rfilename']
  if name not in wanted:continue
  target=repo/name
  if target.exists() and target.stat().st_size==record['size']:continue
  temp=repo/(name+'.partial');route='resolve' if name.endswith('.bin') else 'raw';url=f"https://huggingface.co/{meta['id']}/{route}/{meta['sha']}/{name}"
  print('Downloading',meta['id'],name,record['size'],flush=True)
  subprocess.run(['curl.exe','--silent','--show-error','--fail','--location','--tls-max','1.2','--retry','3','--retry-all-errors','--max-time','600','--proxy','http://127.0.0.1:10809',url,'--output',str(temp)],check=True)
  assert temp.stat().st_size==record['size'],name+' wrong download size'
  if record.get('lfs',{}).get('sha256'):assert hashlib.sha256(temp.read_bytes()).hexdigest()==record['lfs']['sha256']
  if record.get('blobId') and not record.get('lfs'):
   raw=temp.read_bytes();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==record['blobId']
  temp.replace(target)
 print('Ready',meta['id'],meta['sha'],flush=True)
