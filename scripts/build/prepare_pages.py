"""Preserve old nested Pages URLs when publishing the static site at its root."""

import argparse
from pathlib import Path

PAGES = (
    "index.html",
    "retrieval.html",
    "workflow.html",
    "workflow-map.html",
    "keyword-missing.html",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    for page in PAGES:
        if not (output / page).is_file():
            raise SystemExit(f"Missing top-level page: {page}")
    legacy = output / "outputs" / "paper-atlas"
    legacy.mkdir(parents=True, exist_ok=True)
    for page in PAGES:
        target = "../../" + page
        (legacy / page).write_text(
            '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0;url={target}">'
            "<title>Lab Atlas</title>"
            f'<script>location.replace("{target}" + location.search + location.hash);</script>'
            f'</head><body><a href="{target}">打开 Lab Atlas</a></body></html>\n',
            encoding="utf-8",
        )
    (output / ".nojekyll").touch()


if __name__ == "__main__":
    main()
