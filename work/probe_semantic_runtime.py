import importlib.util,json,shutil
modules=['torch','transformers','adapters','numpy','huggingface_hub','safetensors','onnxruntime']
print(json.dumps({m:bool(importlib.util.find_spec(m)) for m in modules}))
print('free_gb',round(shutil.disk_usage('.').free/1024**3,1))
try:
 import torch
 print('torch',torch.__version__,'cuda',torch.cuda.is_available(),'threads',torch.get_num_threads())
except ImportError:pass
