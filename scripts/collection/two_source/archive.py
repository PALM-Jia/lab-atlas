"""Freeze v1.0 data before collecting anything. No deletes or legacy reads by collector."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / '_legacy/v1.0'


def run():
    target = TARGET / 'data'
    previous = TARGET / 'manifest.json'
    if previous.exists():
        manifest = json.loads(previous.read_text(encoding='utf-8'))
    else:
        manifest = {'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                    'policy': 'Immutable copy; original release remains operational until explicit adoption.', 'files': []}
        for src in sorted((ROOT / 'data').rglob('*')):
            if not src.is_file():
                continue
            relative = src.relative_to(ROOT / 'data')
            dest = target / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            manifest['files'].append({'path': relative.as_posix(), 'bytes': src.stat().st_size,
                                      'sha256': hashlib.sha256(src.read_bytes()).hexdigest()})
        TARGET.mkdir(parents=True, exist_ok=True)
        previous.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    for row in manifest['files']:
        dest = target / row['path']
        assert dest.stat().st_size == row['bytes']
        assert hashlib.sha256(dest.read_bytes()).hexdigest() == row['sha256'], row['path']
    print(json.dumps({'archive': str(TARGET), 'files': len(manifest['files']),
                      'bytes': sum(r['bytes'] for r in manifest['files']), 'verified': True}))


if __name__ == '__main__':
    run()
