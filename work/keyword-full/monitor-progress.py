"""Refresh local progress summaries; no model calls or result edits."""
import json
from pathlib import Path
import tempfile
import os
import time
import validate

root = Path(__file__).resolve().parent
while True:
    try:
        report = validate.validate(root)
        destination = root / 'control' / 'validation-report.json'
        fd, temp = tempfile.mkstemp(dir=str(destination.parent), suffix='.tmp')
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(report, handle, ensure_ascii=False)
        os.replace(temp, str(destination))
    except Exception as error:
        print(type(error).__name__, flush=True)
    time.sleep(10)
