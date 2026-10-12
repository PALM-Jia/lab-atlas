from pathlib import Path
p=Path('outputs/paper-atlas/semantic_features.py');s=p.read_text(encoding='utf8').replace("model.active_adapters.flatten()!=['proximity']", "set(model.active_adapters.flatten())!={'proximity'}");p.write_text(s,encoding='utf8')
