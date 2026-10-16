"""Reusable publication-page fetching and extraction; no historical batch fixes."""

import json, re, subprocess, hashlib

from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]

OUT = ROOT / "work/abstract-backfill"

OUT.mkdir(parents=True, exist_ok=True)


def norm(s):
    return re.sub("[^a-z0-9]", "", s.lower())


def fetch(url):
    path = OUT / ("api-page-" + hashlib.sha256(url.encode()).hexdigest() + ".html")
    if path.exists():
        return path.read_text(encoding="utf8"), {
            "url": url,
            "http": 200,
            "status": "cached",
            "file": path.name,
        }
    try:
        r = subprocess.run(
            [
                "curl.exe",
                "-L",
                "--silent",
                "--show-error",
                "--max-time",
                "20",
                "--write-out",
                "\n%{http_code}",
                url,
            ],
            capture_output=True,
            timeout=24,
        )
        raw, _, code = r.stdout.rpartition(b"\n")
        status = int(code) if code.isdigit() else 0
        if not r.returncode and 200 <= status < 300:
            text = raw.decode("utf8", errors="replace")
            path.write_text(text, encoding="utf8")
            return text, {
                "url": url,
                "http": status,
                "status": "received",
                "file": path.name,
            }
        return None, {
            "url": url,
            "http": status,
            "status": "query_failed",
            "reason": "http_" + str(status) if status else "curl_" + str(r.returncode),
        }
    except Exception as e:
        return None, {
            "url": url,
            "http": None,
            "status": "query_failed",
            "reason": type(e).__name__,
        }


def extract(html, url):
    if "api2.openreview.net" in url or "api.openreview.net" in url:
        d = json.loads(html)
        ns = d.get("notes", [])
        if not ns:
            return None
        c = ns[0].get("content", {})
        v = lambda k: (
            c.get(k, {}).get("value") if isinstance(c.get(k), dict) else c.get(k)
        )
        return {
            "title": v("title"),
            "abstract": v("abstract"),
            "authors": v("authors"),
            "doi": None,
        }
    s = BeautifulSoup(html, "html.parser")

    def meta(*names):
        for name in names:
            v = s.find("meta", attrs={"name": name}) or s.find(
                "meta", attrs={"property": name}
            )
            if v:
                return v.get("content")

    title = meta("citation_title", "DC.Title", "dc.title", "og:title")
    a = None
    if (
        "neurips.cc/virtual" in url
        or "cvpr.thecvf.com/virtual" in url
        or "icml.cc/virtual" in url
    ):
        title = (
            (s.select_one(".event-title") or s.select_one(".maincardBody")).get_text(
                " ", strip=True
            )
            if (s.select_one(".event-title") or s.select_one(".maincardBody"))
            else title
        )
        el = (
            s.select_one(".abstract-text-inner")
            or s.select_one(".abstract")
            or s.select_one("#abstract")
            or s.select_one(".card-text")
        )
        a = el.get_text(" ", strip=True) if el else None
    elif "aclanthology.org" in url:
        el = s.select_one(".acl-abstract")
        a = el.get_text(" ", strip=True) if el else None
    elif "thecvf.com" in url:
        el = s.select_one("#abstract")
        a = el.get_text(" ", strip=True) if el else None
    elif "arxiv.org" in url:
        el = s.select_one("blockquote.abstract")
        a = el.get_text(" ", strip=True) if el else None
    elif "springer" in url:
        el = s.select_one("#Abs1-content") or s.select_one(
            ".c-article-section__content"
        )
        a = el.get_text(" ", strip=True) if el else None
    elif "sciencedirect.com" in url:
        el = s.select_one("#abstracts") or s.select_one(".abstract")
        a = el.get_text(" ", strip=True) if el else None
    elif "nips.cc" in url or "neurips.cc/paper_files" in url:
        title = (
            s.select_one(".paper-title").get_text(" ", strip=True)
            if s.select_one(".paper-title")
            else title
        )
        el = s.select_one(".paper-abstract")
        a = el.get_text(" ", strip=True) if el else None
    elif "nature.com" in url:
        el = s.select_one("#Abs1-content") or s.select_one("#abstract-content")
        a = el.get_text(" ", strip=True) if el else None
    elif "proceedings.mlr.press" in url:
        el = s.select_one("#abstract") or s.select_one(".abstract")
        a = el.get_text(" ", strip=True) if el else None
    authors = [
        v.get("content") for v in s.find_all("meta", attrs={"name": "citation_author"})
    ]
    return {
        "title": title,
        "abstract": re.sub(r"^Abstract\s*:?\s*", "", a).strip() if a else None,
        "authors": authors,
        "doi": meta("citation_doi", "dc.identifier"),
    }
