"""Export accepted vocabulary labels; never fall back to database keywords."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).with_name('apply-reviewed-keywords.py')), run_name='__main__')
