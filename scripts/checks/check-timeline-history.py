"""Synthetic adopted-evidence producer check; no query/cache/clock access."""

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
from build_atlas import citation_history

r = {
    "meta": {"snapshot": "fixed"},
    "bibliography": {"x": {"year": 2020}, "u": {"year": None}},
    "papers": [
        {
            "id": "a",
            "fields": {
                "citing": {"state": "ready", "ids": ["x", "x", "u"], "total": 2}
            },
        },
        {"id": "b", "fields": {"citing": {"state": "missing", "ids": [], "total": 0}}},
    ],
}
g = {
    "nodes": [
        {"id": "a", "lab": True},
        {"id": "b", "lab": True},
        {"id": "external", "year": 2010},
    ],
    "edges": [
        {"kind": "citation", "source": "a", "target": "external"},
        {"kind": "citation", "source": "a", "target": "external"},
    ],
}
h = citation_history(g, r)["papers"]
assert h["a"]["observedCount"] == 2 and h["a"]["unknownYearCount"] == 1
assert h["a"]["annual"] == [{"year": 2020, "count": 1, "cumulative": 1}]
assert h["b"]["databaseTotal"] is None and h["b"]["observedCount"] is None
assert h["a"]["snapshot"] == "fixed"
assert h["external"]["observedCount"] == 1 and h["external"]["databaseTotal"] is None
assert h["external"]["unknownYearCount"] == 1
print(
    "Citation history producer passed: repeated ids/edges deduplicated; unknown dates, unavailable totals and snapshot fallback retained."
)
