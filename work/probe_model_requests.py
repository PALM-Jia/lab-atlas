import requests
s=requests.Session();s.trust_env=False;s.proxies={'http':'http://127.0.0.1:10809','https':'http://127.0.0.1:10809'}
u='https://huggingface.co/allenai/specter2_base/raw/3447645e1def9117997203454fa4495937bfbd83/special_tokens_map.json'
r=s.get(u,timeout=25);r.raise_for_status();print(r.status_code,len(r.content));open('work/semantic-models/specter2_base/special_tokens_map.json','wb').write(r.content)
