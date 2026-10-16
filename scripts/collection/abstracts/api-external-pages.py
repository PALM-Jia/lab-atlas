import json, re, concurrent.futures, collections, urllib.parse, importlib.util, threading
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "work/abstract-backfill"
OUT.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location(
    "pages", Path(__file__).resolve().parent / "api-pages.py"
)
pages = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pages)
previous = (
    json.loads((OUT / "api-publication-results.json").read_text(encoding="utf8"))
    if (OUT / "api-publication-results.json").exists()
    else {}
)
done = {x["id"] for x in previous.get("results", [])}
targets = [
    x
    for x in json.loads((OUT / "api-results.json").read_text(encoding="utf8"))[
        "results"
    ]
    if x["status"] != "success" and x["id"] not in done
]
locations = collections.defaultdict(set)
for folder in ["api-cache", "citation-cache", "abstract-backfill"]:
    for f in (ROOT / "work" / folder).glob("*.json"):
        if folder == "abstract-backfill" and not f.name.startswith("api-response-"):
            continue
        try:
            d = json.loads(f.read_text(encoding="utf8"))
        except Exception:
            continue
        for w in (
            d
            if isinstance(d, list)
            else d.get("results", [d]) if isinstance(d, dict) else []
        ):
            if not isinstance(w, dict) or not str(w.get("id", "")).startswith(
                "https://openalex.org/"
            ):
                continue
            for loc in w.get("locations", []) + [w.get("primary_location") or {}]:
                if loc.get("landing_page_url"):
                    locations[w["id"]].add(loc["landing_page_url"])
blocked = previous.get("blocked", {})
lock = threading.Lock()
rows = previous.get("results", [])


def fetch(url):
    host = urllib.parse.urlparse(url).netloc
    if host in blocked:
        return None, {
            "url": url,
            "http": None,
            "status": "not_queried",
            "reason": "domain_blocked_after_" + blocked[host],
        }
    h, e = pages.fetch(url)
    if e.get("http") in (403, 429):
        blocked[host] = "http_" + str(e["http"])
    return h, e


def process(p):
    row = {
        "id": p["id"],
        "title": p["title"],
        "lab": p["lab"],
        "status": "unresolved",
        "attempts": [],
        "candidates": [],
        "abstract": None,
    }
    urls = []
    d = p.get("doi") or ""
    if d.startswith(("10.1007/", "10.1023/")):
        urls.append(
            "https://link.springer.com/"
            + ("chapter/" if re.search(r"/978", d) else "article/")
            + d
        )
    if d.startswith("10.1038/"):
        urls.append("https://www.nature.com/articles/" + d.split("/", 1)[1])
    urls += sorted(locations.get(p.get("openalex"), set()))
    for u in p["landing_urls"]:
        if "openalex.org" not in u:
            urls.append(u)
    urls = [
        u
        for u in dict.fromkeys(urls)
        if not any(
            x in u
            for x in [
                ".pdf",
                "doi.org",
                "pubmed.ncbi",
                "hdl.handle.net",
                "scopus.com",
                "europepmc.org",
                "ideas.repec.org",
            ]
        )
    ]
    # Only publisher/repository landing pages and public bibliographic DOI records.
    allowed = (
        "springer.com",
        "nature.com",
        "sciencedirect.com",
        "arxiv.org",
        "thecvf.com",
        "mlr.press",
        "aclanthology.org",
        "openreview.net",
        "ieeexplore.ieee.org",
        "papers.ssrn.com",
        "dl.acm.org",
        "onlinelibrary.wiley.com",
        "proceedings.neurips.cc",
        "papers.nips.cc",
    )
    urls = [
        u for u in urls if any(x in urllib.parse.urlparse(u).netloc for x in allowed)
    ]
    # Crossref is intentionally excluded from subsequent requests: original public pages are the fallback.
    for u in urls:
        h, e = fetch(u)
        row["attempts"].append(e)
        if not h:
            continue
        try:
            if "api.crossref.org" in u:
                w = json.loads(h).get("message", {})
                w = {
                    "title": (w.get("title") or [""])[0],
                    "abstract": BeautifulSoup(
                        w.get("abstract") or "", "html.parser"
                    ).get_text(" ", strip=True),
                    "doi": w.get("DOI"),
                }
            else:
                w = pages.extract(h, u)
        except Exception as ex:
            row["attempts"][-1]["parse_error"] = type(ex).__name__
            continue
        if not w or not w.get("abstract"):
            continue
        a = w["abstract"]
        accepted = (
            pages.norm(w.get("title") or "") == pages.norm(p["title"])
            and len(a.split()) >= 25
        )
        # Recorded, already verified publication title variants are valid for a matching DOI.
        if not accepted and w.get("doi") and w["doi"].lower() == d:
            accepted = (
                any(
                    pages.norm(v.get("title", "")) == pages.norm(w.get("title", ""))
                    for v in p.get("versions", [])
                )
                and len(a.split()) >= 25
            )
        row["candidates"].append(
            {
                **w,
                "source_url": u,
                "accepted": accepted,
                "reason": (
                    "title_and_publication_identifier_verified"
                    if accepted
                    else "title_or_abstract_quality_requires_review"
                ),
            }
        )
        if accepted:
            row.update(
                status="success",
                abstract=a,
                source_url=u,
                reason="title_and_publication_identifier_verified",
            )
            break
    if row["status"] != "success":
        row["reason"] = (
            "no_accepted_abstract_from_attempted_routes"
            if urls
            else "no_supported_public_landing_url_or_doi"
        )
    return row


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    for row in pool.map(process, targets):
        rows.append(row)
        if len(rows) % 15 == 0:
            print(
                len(rows),
                dict(collections.Counter(x["status"] for x in rows)),
                flush=True,
            )
            (OUT / "api-publication-results.json").write_text(
                json.dumps(
                    {
                        "summary": dict(collections.Counter(x["status"] for x in rows)),
                        "blocked": blocked,
                        "results": rows,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf8",
            )
(OUT / "api-publication-results.json").write_text(
    json.dumps(
        {
            "summary": dict(collections.Counter(x["status"] for x in rows)),
            "blocked": blocked,
            "results": rows,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf8",
)
print(
    "complete",
    len(rows),
    dict(collections.Counter(x["status"] for x in rows)),
    flush=True,
)
