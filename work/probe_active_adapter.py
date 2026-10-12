from adapters import AutoAdapterModel
from transformers import AutoTokenizer
import torch
m=AutoAdapterModel.from_pretrained('work/semantic-models/specter2_base',local_files_only=True)
a=m.load_adapter('work/semantic-models/specter2',load_as='proximity',set_active=True)
print('loaded',a,'active',repr(m.active_adapters),'flatten',repr(m.active_adapters.flatten()) if m.active_adapters else None)
m.set_active_adapters('proximity');m.eval();torch.set_num_threads(4)
t=AutoTokenizer.from_pretrained('work/semantic-models/specter2_base',local_files_only=True);x=t(['Title[SEP]A short abstract.'],return_tensors='pt',return_token_type_ids=False)
with torch.inference_mode():
 y=m(**x).last_hidden_state[:,0,:]
 m.set_active_adapters(None);z=m(**x).last_hidden_state[:,0,:]
print('adapter_changes_embedding',torch.max(torch.abs(y-z)).item())
assert torch.max(torch.abs(y-z)).item()>.001
