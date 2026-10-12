import os,urllib.parse,importlib.util
for name in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY']:
 v=os.getenv(name)
 if v:
  u=urllib.parse.urlsplit(v);print(name,u.scheme,u.hostname,u.port)
print('socks',bool(importlib.util.find_spec('socks')))
