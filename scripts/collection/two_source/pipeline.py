"""Isolated two-source collection. No imports of legacy adoption/collector modules."""

import argparse
import collections
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import time
import unicodedata
import urllib.parse
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "data/two-source/protocol.json"
API_ROOT = "https://api.openalex.org"
IDENTITY_FIELDS = (
    "id,title,doi,ids,type,publication_year,authorships,primary_location,locations"
)
DETAIL_FIELDS = (
    IDENTITY_FIELDS
    + ",abstract_inverted_index,cited_by_count,referenced_works,topics,keywords,counts_by_year"
)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def digest(value):
    data = (
        value
        if isinstance(value, bytes)
        else json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    )
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".partial")
    temp.write_bytes(
        (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    temp.replace(path)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip(" ,.;\n")


def norm(text):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", text or "").lower())


def search_text(text):
    """Normalize query typography, preserving the original homepage fields."""
    text = unicodedata.normalize("NFKC", text or "")
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = text.translate(
        str.maketrans(
            {
                "‐": "-",
                "‑": "-",
                "–": "-",
                "—": "-",
                "‘": "'",
                "’": "'",
                "“": '"',
                "”": '"',
            }
        )
    )
    return re.sub(r"\s+", " ", text).strip()


def spelling_text(text):
    text = search_text(text)
    for typo, corrected in [
        ("Poistive", "Positive"),
        ("Hyerspectral", "Hyperspectral"),
    ]:
        text = re.sub(r"\b" + typo + r"\b", corrected, text, flags=re.I)
    return text


def editorial_title_variant(text):
    # A specific duplicated verbal/noun phrase in the lab listing. It is only
    # eligible for identity acceptance with complete author/year/venue evidence.
    return re.sub(
        r"\bby\s+fusing\s+manifold\s+fusion\b",
        "by manifold fusion",
        spelling_text(text),
        flags=re.I,
    )


def author_norm(text):
    text = re.sub(
        r";\s*id_orcid\s+\d{4}-\d{4}-\d{4}-[\dX]{4}", "", text or "", flags=re.I
    )
    text = re.sub(r"\s*\(\d+\)$", "", text)
    if "," in text:
        last, first = text.split(",", 1)
        text = first.strip() + " " + last.strip()
    return norm(text)


def oid(value):
    return (value or "").rstrip("/").split("/")[-1]


def summary(rows, success_states=("ready", "empty")):
    counts = collections.Counter(r["state"] for r in rows)
    success = sum(counts[s] for s in success_states)
    total = len(rows)
    explained = sum(
        r["state"] not in success_states and bool(r.get("reason")) for r in rows
    )
    return {
        "total": total,
        "success": success,
        "explained_failure": explained,
        "unexplained": total - success - explained,
        "success_rate": round(success / total * 100, 2) if total else None,
        "explained_failure_rate": round(explained / total * 100, 2) if total else None,
        "accounted_rate": (
            round((success + explained) / total * 100, 2) if total else None
        ),
        "states": dict(counts),
    }


def parse_homepage(source, url):
    """The lab's malformed jemdoc paragraphs require nearest-p ownership."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(source, "html.parser")
    papers, occurrences, exclusions = {}, [], []
    for p in soup.select("#layout-content p"):
        heading = p.find_previous("h2")
        if not heading:
            continue
        section = clean(heading.get_text(" ", strip=True))
        if section not in (
            "The works that I personally like the most",
            "Preprint",
            "Journal Papers",
            "Conference Papers",
        ):
            continue
        text = clean(" ".join(str(s) for s in p.strings if s.find_parent("p") is p))
        if not text:
            continue
        index = len(occurrences) + len(exclusions)
        if len(text) < 12:
            exclusions.append(
                {
                    "index": index,
                    "raw": text,
                    "reason": "non_publication_short_paragraph",
                }
            )
            continue
        anchors = [a for a in p.find_all("a") if a.find_parent("p") is p]
        title_links = [
            a
            for a in anchors
            if clean(a.get_text(" ", strip=True)).lower() not in ("code", "pdf")
        ]
        venue_match = re.match(r"^\[([^]]+)\]", text)
        venue = venue_match.group(1) if venue_match else None
        names, title = [], None
        if section == "Preprint":
            title = text
        elif title_links:
            title = clean(title_links[0].get_text(" ", strip=True))
            pos = text.find(title)
            if pos >= 0:
                byline = re.sub(r"^\[[^]]+\]\s*", "", text[:pos])
                names = [
                    clean(x)
                    for x in re.sub(r"\band\s+", "", byline).split(",")
                    if clean(x)
                ]
        elif venue:
            body = re.sub(r"^\[[^]]+\]\s*", "", text)
            parts = body.split(",")
            start = next(
                (
                    i
                    for i, value in enumerate(parts)
                    if len(value.split()) > 5
                    or ":" in value
                    or re.search(
                        r"\b(Towards|Learning|Discovering|Generalization|Individuals|Samples|Attention|Exploiting|Mismatch|Progressive|Beyond|Reliable|Comprehensive|Question|Fragmented|Unsupervised|Robust|On the|Mini-cluster|Partial Label)\b",
                        value,
                    )
                ),
                None,
            )
            if start is not None:
                byline, remainder = ",".join(parts[:start]), ",".join(parts[start:])
                if "Yuheng Jia Towards Better" in remainder:
                    byline += "," + remainder.split("Towards Better")[0]
                    remainder = (
                        "Towards Better" + remainder.split("Towards Better", 1)[1]
                    )
                names = [clean(x) for x in byline.split(",") if clean(x)]
                title = re.split(
                    r",\s*(?:IEEE|EEE |International|The |Thirty|Twenty|Forty|34th|Pattern Recognition|Briefings|Journal of|Conference on|Empirical Methods|ACM |AAAI |Transportation Research|Intelligent Systems|Genetic and|Information Sciences|20\d{2})",
                    remainder,
                    maxsplit=1,
                )[0]
        title = clean(title)
        if len(title) < 8:
            exclusions.append(
                {"index": index, "raw": text, "reason": "could_not_parse_title"}
            )
            continue
        if (
            len(title) % 2 == 1
            and title[: len(title) // 2] == title[len(title) // 2 + 1 :]
        ):
            title = title[: len(title) // 2]
        key = norm(title)
        year_tokens = re.findall(r"\b(20\d{2}|19\d{2})\b", text)
        links = list(dict.fromkeys(a.get("href") for a in title_links if a.get("href")))
        item = {
            "id": "lab-" + hashlib.sha1(key.encode()).hexdigest()[:12],
            "title": title,
            "authors": names,
            "year": int(year_tokens[0]) if year_tokens else None,
            "venue": venue,
            "publication_status": (
                "preprint" if section == "Preprint" else "homepage_reported"
            ),
            "links": links,
            "raw": text,
            "section": section,
            "source": "lab_homepage",
            "source_url": url,
        }
        occurrences.append(
            {"index": index, "paper_id": item["id"], "section": section, "raw": text}
        )
        if key in papers:
            previous = papers[key]
            previous["links"] = list(dict.fromkeys(previous["links"] + links))
            # A journal/conference listing is more informative than a featured duplicate.
            if section in ("Journal Papers", "Conference Papers"):
                item["links"] = previous["links"]
                papers[key] = item
        else:
            papers[key] = item
    return {
        "papers": list(papers.values()),
        "occurrences": occurrences,
        "excluded": exclusions,
        "parse_summary": {
            "unique_papers": len(papers),
            "publication_occurrences": len(occurrences),
            "duplicates": len(occurrences) - len(papers),
            "excluded": len(exclusions),
        },
    }


class Client:
    def __init__(self, run_dir, config, offline=False):
        self.base = Path(run_dir) / "responses"
        self.base.mkdir(parents=True, exist_ok=True)
        self.config, self.offline = config, offline
        self.key = os.environ.get("OPENALEX_API_KEY")
        self.lock, self.last, self.calls = threading.Lock(), 0.0, 0
        self.blocked = None

    def request(self, path, params=None):
        assert path == "/works" or re.fullmatch(r"/works/W\d+", path), path
        params = {k: v for k, v in (params or {}).items() if v is not None}
        url = (
            API_ROOT
            + path
            + ("?" + urllib.parse.urlencode(sorted(params.items())) if params else "")
        )
        filename = self.base / (digest(url.encode()) + ".json")
        if filename.exists():
            envelope = read(filename)
            assert envelope["url"] == url
            assert envelope["sha256"] == digest(envelope.get("payload"))
            return envelope.get("payload") if envelope["state"] == "ready" else None, {
                k: v for k, v in envelope.items() if k != "payload"
            }
        if self.offline:
            return None, {
                "url": url,
                "state": "query_failed",
                "reason": "response_not_in_frozen_run",
                "http": None,
            }
        envelope = {
            "url": url,
            "received_at": now(),
            "attempts": [],
            "state": "query_failed",
            "reason": "",
            "http": None,
            "payload": None,
        }
        if self.blocked:
            envelope["reason"] = "not_requested_after_" + self.blocked
        else:
            for attempt in range(self.config["attempts"]):
                with self.lock:
                    delay = self.config["minimum_start_interval_seconds"] - (
                        time.monotonic() - self.last
                    )
                    if delay > 0:
                        time.sleep(delay)
                    self.last = time.monotonic()
                    self.calls += 1
                config = (
                    "header = " + json.dumps("Authorization: Bearer " + self.key)
                    if self.key
                    else ""
                )
                args = [
                    "curl.exe",
                    "--silent",
                    "--show-error",
                    "--max-time",
                    str(self.config["timeout_seconds"]),
                    "--config",
                    "-",
                    "--write-out",
                    "\n%{http_code}",
                    url,
                ]
                try:
                    result = subprocess.run(
                        args,
                        input=config.encode(),
                        capture_output=True,
                        timeout=self.config["timeout_seconds"] + 5,
                    )
                    body, _, code = result.stdout.rpartition(b"\n")
                    status = int(code) if code.isdigit() else 0
                    envelope["http"] = status
                    event = {"http": status, "curl_exit": result.returncode}
                    if result.returncode == 0 and 200 <= status < 300:
                        payload = json.loads(body)
                        if not isinstance(payload, dict) or (
                            "results" not in payload and "id" not in payload
                        ):
                            raise ValueError("invalid_openalex_record_shape")
                        envelope.update(
                            state="ready", reason="response_received", payload=payload
                        )
                        envelope["attempts"].append(event)
                        break
                    event["reason"] = (
                        "http_" + str(status)
                        if status
                        else "curl_" + str(result.returncode)
                    )
                    envelope["reason"] = event["reason"]
                    if status in (401, 403):
                        self.blocked = event["reason"]
                    if status == 429:
                        try:
                            error = json.loads(body)
                            if (
                                error.get("dailyRemainingUsd") == 0
                                or error.get("creditsRemaining") == 0
                            ):
                                self.blocked = "http_429_budget_exhausted"
                        except ValueError:
                            pass
                    envelope["attempts"].append(event)
                    if self.blocked or status in (400, 404):
                        break
                except (ValueError, subprocess.TimeoutExpired) as exc:
                    envelope["reason"] = (
                        str(exc) if isinstance(exc, ValueError) else "curl_timeout"
                    )
                    envelope["attempts"].append({"reason": envelope["reason"]})
                if attempt + 1 < self.config["attempts"]:
                    time.sleep(2**attempt)
        envelope["sha256"] = digest(envelope["payload"])
        save(filename, envelope)
        return envelope["payload"], {
            k: v for k, v in envelope.items() if k != "payload"
        }


def source_dois(paper):
    values = []
    for link in paper["links"]:
        m = re.search(
            r"(?:doi\.org/|/doi/(?:abs/|full/)?)(10\.\d{4,9}/[^?#]+)", link, re.I
        )
        if m:
            values.append(urllib.parse.unquote(m[1]).rstrip("/."))
        arxiv = re.search(
            r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?", link, re.I
        )
        if arxiv:
            values.append("10.48550/arxiv." + arxiv[1])
    return list(dict.fromkeys(values))


def identity_projection(work):
    return {k: work.get(k) for k in IDENTITY_FIELDS.split(",")}


def identity_signature(work):
    # Nested author/source objects contain mutable display metadata. Only the
    # bibliographic identity participates in the stage 2 -> 3 boundary check.
    return {
        "id": work.get("id"),
        "title": norm(work.get("title")),
        "doi": work.get("doi"),
        "authors": [
            (
                author_norm((a.get("author") or {}).get("display_name")),
                (a.get("author") or {}).get("id"),
            )
            for a in work.get("authorships") or []
        ],
        "year": work.get("publication_year"),
        "venue": canonical_venue(work_venue(work)),
        "formal": formal(work),
    }


def formal(work):
    loc = work.get("primary_location") or {}
    src = loc.get("source") or {}
    return bool(
        loc.get("version") == "publishedVersion"
        and (
            src.get("type") in ("journal", "conference")
            or (not src and loc.get("raw_source_name"))
        )
    )


def work_venue(work):
    location = work.get("primary_location") or {}
    return (
        (location.get("source") or {}).get("display_name")
        or location.get("raw_source_name")
        or None
    )


def canonical_venue(value):
    key = norm(value)
    aliases = {
        "pr": "patternrecognition",
        "tkde": "ieeetransactionsonknowledgeanddataengineering",
        "tits": "ieeetransactionsonintelligenttransportationsystems",
        "tcsvt": "ieeetransactionsoncircuitsandsystemsforvideotechnology",
        "tpami": "ieeetransactionsonpatternanalysisandmachineintelligence",
        "tnnls": "ieeetransactionsonneuralnetworksandlearningsystems",
        "trb": "transportationresearchboardannualmeeting",
        "neurips": "neuralinformationprocessingsystems",
        "nips": "neuralinformationprocessingsystems",
        "cvprfindings": "cvprfindings",
        "cvprf": "cvprfindings",
    }
    if "findings" in key and (
        "computervisionandpatternrecognition" in key or "cvpr" in key
    ):
        return "cvprfindings"
    return aliases.get(key, key)


def title_word_changes(a, b):
    # Joining hyphens (multi-view/multiview) and case is harmless; replacing substantive words is not.
    def tokens(text):
        text = re.sub(r"(?<=\w)[‐‑–—-](?=\w)", "", search_text(text).lower())
        return re.findall(r"[a-z0-9]+", text)

    changes = []
    left, right = tokens(a), tokens(b)
    for op, i, j, x, y in SequenceMatcher(None, left, right).get_opcodes():
        if op != "equal":
            changes.append(
                {"operation": op, "homepage": left[i:j], "candidate": right[x:y]}
            )
    return changes


def metrics(paper, work, config):
    a, b = norm(paper["title"]), norm(work.get("title"))
    similarity = SequenceMatcher(None, a, b).ratio()
    labnames = {author_norm(x) for x in paper["authors"]}
    oanames = {
        author_norm((x.get("author") or {}).get("display_name"))
        for x in work.get("authorships") or []
    }
    overlap = labnames & oanames
    direct = any(
        (work.get("doi") or "").lower().endswith(d.lower())
        or any(
            (loc.get("doi") or "").lower().endswith(d.lower())
            for loc in work.get("locations") or []
        )
        for d in source_dois(paper)
    )
    year_delta = (
        abs(paper["year"] - work["publication_year"])
        if paper.get("year") and work.get("publication_year")
        else None
    )
    authors_ok = len(overlap) >= 2 or (
        bool(overlap) and len(overlap) / max(1, len(labnames)) >= 0.5
    )
    mentor = "yuhengjia" in oanames
    if not labnames:
        authors_ok = mentor
    year_ok = year_delta is None or year_delta <= config["year_tolerance"]
    changes = title_word_changes(paper["title"], work.get("title") or "")
    # Formatting equivalence is handled by norm. Other title edits require a
    # source identifier: a high ratio cannot distinguish a genuinely new task.
    homevenue, candidatevenue = canonical_venue(paper.get("venue")), canonical_venue(
        work_venue(work)
    )
    venue_exact = bool(homevenue and homevenue == candidatevenue)
    spelling_equivalent = norm(spelling_text(paper["title"])) == norm(
        spelling_text(work.get("title"))
    )
    complete_authors = tuple(author_norm(x) for x in paper["authors"]) == tuple(
        author_norm((x.get("author") or {}).get("display_name"))
        for x in work.get("authorships") or []
    )
    editorial_equivalent = (
        a != b
        and norm(editorial_title_variant(paper["title"]))
        == norm(spelling_text(work.get("title")))
        and len(paper["authors"]) >= 3
        and complete_authors
        and year_delta == 0
        and venue_exact
        and formal(work)
    )
    meaningful_substitution = (
        a != b and not spelling_equivalent and not editorial_equivalent
    )
    venue_conflict = bool(
        formal(work)
        and homevenue
        and candidatevenue
        and homevenue
        in {
            "transportationresearchboardannualmeeting",
            "ieeetransactionsonintelligenttransportationsystems",
        }
        and homevenue != candidatevenue
    )
    missing_byline_supported = (
        not oanames and a == b and year_delta == 0 and venue_exact
    )
    accepted = (direct and (authors_ok or not labnames) and similarity >= 0.65) or (
        similarity >= config["title_similarity"] and authors_ok and year_ok
    )
    accepted = (
        (accepted or missing_byline_supported)
        and (direct or not meaningful_substitution)
        and (direct or not venue_conflict)
    )
    inappropriate_type = work.get("type") in (
        "other",
        "dataset",
        "paratext",
        "grant",
        "reference-entry",
    )
    accepted = accepted and not inappropriate_type
    reasons = []
    if not direct and similarity < config["title_similarity"]:
        reasons.append("title_similarity_below_rule")
    if not authors_ok and not missing_byline_supported:
        reasons.append("insufficient_author_corroboration")
    if not direct and not year_ok:
        reasons.append("publication_year_outside_tolerance")
    if meaningful_substitution and not direct:
        reasons.append("substantive_title_word_substitution")
    if venue_conflict and not direct:
        reasons.append("different_publication_venue")
    if inappropriate_type:
        reasons.append("record_type_is_not_a_paper")
    return {
        "accepted": accepted,
        "title_similarity": round(similarity, 6),
        "author_overlap": sorted(overlap),
        "homepage_author_count": len(labnames),
        "year_delta": year_delta,
        "direct_doi": direct,
        "formal": formal(work),
        "venue_exact": venue_exact,
        "title_word_changes": changes,
        "spelling_equivalent": spelling_equivalent,
        "editorial_equivalent": editorial_equivalent,
        "missing_byline_supported": missing_byline_supported,
        "reasons": reasons,
    }


def choose(paper, candidates, config):
    scored = [
        {"work": identity_projection(w), "metrics": metrics(paper, w, config)}
        for w in candidates
    ]
    eligible = [r for r in scored if r["metrics"]["accepted"]]
    if not eligible:
        return None, "unmatched", "no_candidate_passed_identity_rules", scored
    if len(eligible) == 1:
        return eligible[0]["work"], "ready", "unique_verified_candidate", scored
    direct = [r for r in eligible if r["metrics"]["direct_doi"]]
    if len(direct) == 1:
        return direct[0]["work"], "ready", "homepage_doi_identifies_version", scored
    # Publication preference is allowed only inside an exact-title/author-verified family.
    exact_family = len({norm(r["work"]["title"]) for r in eligible}) == 1
    names = [
        tuple(
            author_norm((a.get("author") or {}).get("display_name"))
            for a in r["work"].get("authorships") or []
        )
        for r in eligible
    ]
    author_family = bool(names[0]) and all(n == names[0] for n in names)
    # OpenAlex often assigns different author IDs across versions. Compatible
    # complete bylines establish a work family, never a person-ID merge.
    published = [r for r in eligible if r["metrics"]["formal"]]
    if exact_family and author_family and len(published) == 1:
        return (
            published[0]["work"],
            "ready",
            "published_version_of_same_title_author_family",
            scored,
        )
    return (
        None,
        "ambiguous",
        "multiple_verified_candidates_without_unique_version",
        scored,
    )


def title_queries(title, broad):
    normalized_title = search_text(title)
    queries = [normalized_title]
    if not broad:
        return queries
    repaired = spelling_text(normalized_title)
    if repaired != normalized_title:
        queries.append(repaired)
    editorial = editorial_title_variant(repaired)
    if editorial != repaired:
        queries.append(editorial)
    body = repaired.split(":", 1)[-1].strip()
    queries.append(body)
    normalized = re.sub(r"[-‐‑–—/]", " ", body)
    queries.append(normalized)
    words = re.findall(r"[A-Za-z0-9]+", normalized)
    if len(words) > 10:
        queries.extend([" ".join(words[:10]), " ".join(words[-10:])])
    return list(dict.fromkeys(q for q in queries if len(q) >= 8))


def resolve(paper, client, config, broad):
    candidates, attempts = {}, []
    for doi_value in source_dois(paper):
        data, event = client.request(
            "/works",
            {"filter": "doi:" + doi_value, "per_page": 15, "select": IDENTITY_FIELDS},
        )
        attempts.append(event)
        for w in (data or {}).get("results", []):
            candidates[w["id"]] = identity_projection(w)
    # Finish both primary routes before deciding. Variants are expansion only
    # when the primary pool has no verified identity; do not broaden gratuitously.
    normalized_title = search_text(paper["title"])
    search_plan = [("search.title", normalized_title), ("search", normalized_title)]
    variants = [("search.title", q) for q in title_queries(paper["title"], broad)[1:]]
    search_plan += variants
    for scope, query in search_plan:
        data, event = client.request(
            "/works",
            {scope: query, "per_page": config["per_query"], "select": IDENTITY_FIELDS},
        )
        attempts.append(event)
        for w in (data or {}).get("results", []):
            candidates[w["id"]] = identity_projection(w)
        selected, state, reason, scored = choose(
            paper, list(candidates.values()), config
        )
        if (
            scope == "search"
            and selected
            and (
                formal(selected)
                or any(
                    c["metrics"]["direct_doi"]
                    for c in scored
                    if c["work"]["id"] == selected["id"]
                )
            )
        ):
            break
        if (
            (scope, query) in variants
            and selected
            and (
                formal(selected)
                or any(
                    c["metrics"]["direct_doi"]
                    for c in scored
                    if c["work"]["id"] == selected["id"]
                )
            )
        ):
            break
    selected, state, reason, scored = choose(paper, list(candidates.values()), config)
    if not candidates and attempts and all(a["state"] != "ready" for a in attempts):
        state, reason = "query_failed", "all_identity_queries_failed"
    final = (
        {
            "title": selected["title"],
            "authors": [
                a["author"]["display_name"] for a in selected.get("authorships") or []
            ]
            or paper["authors"],
            "year": selected.get("publication_year"),
            "venue": work_venue(selected) or paper["venue"],
            "publication_status": (
                "formal" if formal(selected) else selected.get("type")
            ),
            "openalex": selected["id"],
            "doi": selected.get("doi"),
        }
        if selected
        else {
            **{
                k: paper[k]
                for k in ("title", "authors", "year", "venue", "publication_status")
            },
            "openalex": None,
            "doi": None,
        }
    )
    return {
        "id": paper["id"],
        "state": state,
        "reason": reason,
        "homepage": paper,
        "adopted": final,
        "candidates": scored,
        "attempts": attempts,
        "decision_sha256": digest(
            {"homepage": paper, "selected": final, "config": config}
        ),
        "identity_source": "openalex" if selected else "lab_homepage",
        "adopted_sources": {
            k: (
                "openalex"
                if selected
                and (k != "authors" or selected.get("authorships"))
                and (k != "venue" or work_venue(selected))
                else "lab_homepage"
            )
            for k in ("title", "authors", "year", "venue", "publication_status")
        },
    }


def field(value, source, missing="source_field_absent", event=None):
    state = (
        "missing"
        if value is None or value == ""
        else "empty" if value == [] else "ready"
    )
    return {
        "value": value,
        "state": state,
        "reason": (
            missing
            if state == "missing"
            else (
                "source_returned_empty" if state == "empty" else "source_value_received"
            )
        ),
        "source": source,
        "request": event,
    }


def abstract_quality(work):
    index = work.get("abstract_inverted_index")
    if not index:
        return None, "source_field_absent"
    if not isinstance(index, dict) or any(
        not isinstance(v, list) for v in index.values()
    ):
        return None, "invalid_abstract_index_shape"
    positions = [(p, token) for token, values in index.items() for p in values]
    if any(
        not isinstance(p, int) or p < 0 or not isinstance(token, str)
        for p, token in positions
    ):
        return None, "invalid_abstract_index_position"
    if len({p for p, token in positions}) != len(positions):
        return None, "conflicting_abstract_index_positions"
    value = " ".join(token for p, token in sorted(positions))
    if (
        value.strip().lower() in ("metadata only record", "international audience")
        or value.strip().isdigit()
        or len(value.split()) < 5
    ):
        return None, "abstract_is_placeholder_or_fragment"
    if re.search(
        r"<(?:html|div|script|!DOCTYPE)|Access Denied|Just a moment", value, re.I
    ):
        return None, "abstract_is_markup_or_access_page"
    if (
        len(value.split()) < 80
        and value.count(",") >= 5
        and re.search(r"Proceedings of .*\b(?:19|20)\d{2}\.?$", value, re.I)
    ):
        return None, "abstract_is_bibliographic_citation"
    return value, "source_abstract_received"


def abstract(work):
    return abstract_quality(work)[0]


def bibliography(work):
    value, reason = abstract_quality(work)
    return {
        "id": oid(work["id"]),
        "openalex": work["id"],
        "doi": work.get("doi"),
        "title": work.get("title"),
        "authors": [a["author"]["display_name"] for a in work.get("authorships") or []],
        "author_records": work.get("authorships") or [],
        "year": work.get("publication_year"),
        "venue": work_venue(work),
        "abstract": value,
        "abstract_state": (
            "ready"
            if value
            else "missing" if reason == "source_field_absent" else "invalid"
        ),
        "abstract_reason": reason,
        "citations": work.get("cited_by_count"),
        "topics": work.get("topics"),
        "keywords": work.get("keywords"),
        "counts_by_year": work.get("counts_by_year"),
        "source": "openalex",
    }


def citing_list(identity, client, policy):
    work_id = oid(identity["adopted"]["openalex"])
    cursor, records, attempts, total = "*", {}, [], None
    complete, reason = False, "not_queried"
    pages = (policy["citing_max_records"] + policy["citing_page_size"] - 1) // policy[
        "citing_page_size"
    ]
    for page in range(pages):
        data, event = client.request(
            "/works",
            {
                "filter": "cites:" + work_id,
                "per_page": policy["citing_page_size"],
                "cursor": cursor,
                "sort": "publication_date:desc",
                "select": "id,title,publication_year",
            },
        )
        attempts.append(event)
        if data is None:
            reason = event["reason"]
            break
        total = data.get("meta", {}).get("count")
        for w in data.get("results", []):
            records[oid(w["id"])] = w
        next_cursor = data.get("meta", {}).get("next_cursor")
        if not next_cursor or (total is not None and len(records) >= total):
            complete, reason = True, "complete_query_snapshot"
            break
        if next_cursor == cursor:
            reason = "cursor_did_not_advance"
            break
        cursor = next_cursor
        reason = "configured_citing_limit_600"
    state = (
        "ready"
        if complete and records
        else "empty" if complete else "partial" if records else "query_failed"
    )
    return {
        "state": state,
        "reason": reason,
        "ids": sorted(records),
        "query_total": total,
        "collected": len(records),
        "complete": complete,
        "attempts": attempts,
        "source": "openalex",
    }


def collect_detail(identity, client, policy):
    keys = [
        "abstract",
        "database_keywords",
        "database_topics",
        "citations",
        "references",
        "citing",
    ]
    if identity["state"] != "ready":
        return {
            "id": identity["id"],
            "fields": {
                k: {
                    "value": None,
                    "state": "identity_unresolved",
                    "reason": identity["reason"],
                    "source": None,
                }
                for k in keys
            },
            "bibliography": None,
        }
    expected = identity["adopted"]["openalex"]
    work, event = client.request("/works/" + oid(expected), {"select": DETAIL_FIELDS})
    if not work or work.get("id") != expected:
        return {
            "id": identity["id"],
            "fields": {
                k: {
                    "value": None,
                    "state": "query_failed",
                    "reason": event["reason"] if not work else "work_id_mismatch",
                    "source": "openalex",
                    "request": event,
                }
                for k in keys
            },
            "bibliography": None,
        }
    actual = identity_projection(work)
    accepted = next(
        c["work"] for c in identity["candidates"] if c["work"]["id"] == expected
    )
    # Do not overwrite identity if OpenAlex changed between the two queries.
    drift = identity_signature(actual) != identity_signature(accepted)
    if drift:
        return {
            "id": identity["id"],
            "fields": {
                k: {
                    "value": None,
                    "state": "identity_unresolved",
                    "reason": "identity_changed_between_search_and_detail",
                    "source": "openalex",
                    "request": event,
                }
                for k in keys
            },
            "identity_drift": actual,
            "bibliography": None,
        }
    fields = {
        "abstract": field(abstract(work), "openalex", event=event),
        "database_keywords": field(work.get("keywords"), "openalex", event=event),
        "database_topics": field(work.get("topics"), "openalex", event=event),
        "citations": field(work.get("cited_by_count"), "openalex", event=event),
        "references": field(
            (
                [oid(x) for x in work["referenced_works"]]
                if "referenced_works" in work
                else None
            ),
            "openalex",
            event=event,
        ),
        "citing": citing_list(identity, client, policy),
    }
    abstract_value, abstract_reason = abstract_quality(work)
    fields["abstract"]["reason"] = abstract_reason
    if abstract_value is None and abstract_reason != "source_field_absent":
        fields["abstract"]["state"] = "invalid"
        fields["abstract"]["raw_index_sha256"] = digest(
            work.get("abstract_inverted_index")
        )
    record_count = work.get("cited_by_count")
    query_count = fields["citing"].get("query_total")
    fields["citations"]["observations"] = [
        {"value": record_count, "method": "work_record", "request": event}
    ]
    if isinstance(query_count, int) and query_count >= 0:
        fields["citations"].update(
            value=query_count,
            state="ready",
            reason="citing_query_total_adopted",
            request=fields["citing"]["attempts"][0],
            adopted_method="citing_query_total",
        )
        fields["citations"]["observations"].append(
            {
                "value": query_count,
                "method": "citing_query_total",
                "request": fields["citing"]["attempts"][0],
            }
        )
    else:
        fields["citations"]["adopted_method"] = "work_record"
    return {"id": identity["id"], "fields": fields, "bibliography": bibliography(work)}


def author_occurrences(identities, roster):
    group_names = {
        author_norm(r["author_name"].split(" — ")[0]): group
        for group, rows in roster.items()
        for r in rows
        if r.get("author_name")
    }
    rows = []
    for paper in identities:
        selected = next(
            (
                r["work"]
                for r in paper["candidates"]
                if r["work"]["id"] == paper["adopted"]["openalex"]
            ),
            None,
        )
        authorships = selected.get("authorships") or [] if selected else []
        for index, name in enumerate(paper["adopted"]["authors"]):
            auth = authorships[index] if index < len(authorships) else {}
            author = auth.get("author") or {}
            aid = author.get("id")
            institutions = auth.get("institutions") or []
            institution_names = [i.get("display_name", "") for i in institutions]
            group = group_names.get(author_norm(name))
            # Name can identify roster candidate, never prove a person or group.
            seu = any("southeast university" in x.lower() for x in institution_names)
            outside = any("monash" in x.lower() for x in institution_names)
            state = "ready" if aid else "ambiguous"
            rows.append(
                {
                    "paper_id": paper["id"],
                    "position": index + 1,
                    "name": name,
                    "person_key": aid
                    or "occurrence:" + paper["id"] + ":" + str(index + 1),
                    "openalex_author_id": aid,
                    "orcid": author.get("orcid"),
                    "institutions": institutions,
                    "state": state,
                    "reason": (
                        "openalex_authorship_identifier"
                        if aid
                        else "name_only_no_cross_paper_merge"
                    ),
                    "roster_candidate": group,
                    "roster_affiliation_support": seu and not outside,
                    "group": "other",
                    "group_state": (
                        "needs_roster_identity_confirmation"
                        if group
                        else "not_in_roster"
                    ),
                }
            )
    return rows


def select_external_nodes(records, connections, config):
    """Degree counts distinct lab works in the full direct citation neighborhood.

    A reference and a citing observation for the same pair count once. Semantic
    edges, external-external links, UI filters and top-K do not affect eligibility.
    """
    minimum = config.get("graph_min_lab_neighbors", 1)
    eligible = [i for i in records if len(connections[i]) >= minimum]
    return sorted(eligible, key=lambda i: (-len(connections[i]), i))[
        : config["graph_budget"]
    ]


def external_stage(details, identities, client, config):
    lab_ids = {
        oid(r["adopted"]["openalex"]): r["id"]
        for r in identities
        if r["adopted"]["openalex"]
    }
    associations = collections.defaultdict(set)
    relations = []
    for paper in details:
        refs = paper["fields"]["references"].get("value") or []
        cites = paper["fields"]["citing"].get("ids") or []
        for kind, ids in [("reference", refs), ("citing", cites)]:
            for work_id in sorted(set(ids)):
                relations.append(
                    {"lab_id": paper["id"], "work_id": work_id, "direction": kind}
                )
                if work_id not in lab_ids:
                    associations[work_id].add(paper["id"])
    requested = sorted(associations)
    records, events = {}, []
    batches = [
        requested[i : i + config["requests"]["batch_size"]]
        for i in range(0, len(requested), config["requests"]["batch_size"])
    ]

    def batch_lookup(batch):
        return batch, client.request(
            "/works",
            {
                "filter": "openalex_id:" + "|".join(batch),
                "per_page": 100,
                "select": DETAIL_FIELDS,
            },
        )

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=config["requests"]["workers"]
    ) as pool:
        for batch, (payload, event) in pool.map(batch_lookup, batches):
            events.append(event)
            found = {oid(w["id"]): w for w in (payload or {}).get("results", [])}
            for work_id in batch:
                work = found.get(work_id)
                records[work_id] = {
                    "id": work_id,
                    "state": (
                        "ready"
                        if work
                        else "query_failed" if payload is None else "missing"
                    ),
                    "reason": (
                        "openalex_record_received"
                        if work
                        else (
                            event["reason"]
                            if payload is None
                            else "requested_id_not_returned"
                        )
                    ),
                    "record": bibliography(work) if work else None,
                    "request": event,
                    "connected_lab_ids": sorted(associations[work_id]),
                }
    # Batch omission is not equivalent to a missing work: individual lookup can
    # expose a merged-ID redirect or a record excluded from list endpoints.
    missing_ids = [i for i in requested if records[i]["state"] == "missing"]

    def single_lookup(work_id):
        return work_id, client.request("/works/" + work_id, {"select": DETAIL_FIELDS})

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=config["requests"]["workers"]
    ) as pool:
        for work_id, (payload, event) in pool.map(single_lookup, missing_ids):
            previous = records[work_id]["request"]
            usable = payload is not None and re.fullmatch(
                r"W\d+", oid(payload.get("id"))
            )
            records[work_id].update(
                state=(
                    "ready"
                    if usable
                    else "missing" if event.get("http") == 404 else "query_failed"
                ),
                reason=(
                    "individual_lookup_after_batch_omission"
                    if usable
                    else (
                        "individual_lookup_http_404"
                        if event.get("http") == 404
                        else event["reason"]
                    )
                ),
                record=bibliography(payload) if usable else None,
                request=event,
                batch_request=previous,
                canonical_id=oid(payload["id"]) if usable else None,
            )
    canonical_connections = collections.defaultdict(set)
    canonical_records = {}
    for row in records.values():
        if row["record"]:
            key = row["record"]["id"]
            if key not in lab_ids:
                canonical_connections[key].update(row["connected_lab_ids"])
                canonical_records[key] = row
    for relation in relations:
        work_id = relation["work_id"]
        relation["endpoint_state"] = (
            "ready" if work_id in lab_ids else records[work_id]["state"]
        )
        canonical = (
            work_id
            if work_id in lab_ids
            else (
                records[work_id]["record"]["id"]
                if records[work_id]["record"]
                else work_id
            )
        )
        relation["endpoint_id"] = lab_ids.get(canonical, canonical)
    selected = select_external_nodes(
        canonical_records, canonical_connections, config["external"]
    )
    return (
        {
            "records": [records[i] for i in requested],
            "summary": summary(list(records.values())),
            "attempts": events,
        },
        relations,
        selected,
    )


def feature_inputs(identities, details, external, selection, vocabulary, output):
    detail_map = {r["id"]: r for r in details}
    papers = []
    for row in identities:
        a = row["adopted"]
        detail = detail_map[row["id"]]
        papers.append(
            {
                "id": row["id"],
                "lab": True,
                "title": a["title"],
                "abstract": detail["fields"]["abstract"].get("value") or "",
                "authors": a["authors"],
                "year": a["year"],
                "citations": detail["fields"]["citations"].get("value"),
            }
        )
    selected = set(selection)
    included = set()
    for row in external["records"]:
        if (
            row["record"]
            and row["record"]["id"] in selected
            and row["record"]["id"] not in included
        ):
            record = row["record"]
            papers.append(
                {
                    **{
                        k: record.get(k)
                        for k in (
                            "id",
                            "title",
                            "abstract",
                            "authors",
                            "year",
                            "citations",
                        )
                    },
                    "lab": False,
                }
            )
            included.add(record["id"])
    tasks = []
    prompt = (ROOT / "data/two-source/prompts/keywords.txt").read_text(encoding="utf-8")
    for paper in papers:
        paper["abstract"] = paper["abstract"] or ""
        text = {k: paper[k] for k in ("id", "title", "abstract")}
        paper["input_sha256"] = digest(text)
        tasks.append(
            {
                "paper_id": paper["id"],
                "title": paper["title"],
                "abstract": paper["abstract"],
                "input_sha256": paper["input_sha256"],
                "prompt_sha256": digest(prompt.encode()),
                "vocabulary_sha256": digest(vocabulary),
                "state": "not_generated",
                "reason": "keyword_annotation_not_executed",
            }
        )
    save(
        output / "05-feature-inputs.json",
        {"papers": papers, "vocabulary_sha256": digest(vocabulary)},
    )
    (output / "05-keyword-tasks.jsonl").write_bytes(
        ("\n".join(json.dumps(t, ensure_ascii=False) for t in tasks) + "\n").encode(
            "utf-8"
        )
    )
    save(
        output / "05-feature-status.json",
        {
            "papers": len(papers),
            "keyword_tasks": summary(tasks),
            "vectors": {"state": "not_generated", "reason": "run_local_vector_command"},
            "author_weights": {"first": 1, "others": 0.2},
        },
    )
    return papers


def initialize(run_dir):
    run_dir.mkdir(parents=True, exist_ok=True)
    source = ROOT / "data/sources/homepage-papers.html"
    frozen = run_dir / "inputs/homepage.html"
    frozen.parent.mkdir(parents=True, exist_ok=True)
    if not frozen.exists():
        shutil.copy2(source, frozen)
        for name in ("current-students", "graduated-students"):
            shutil.copy2(
                ROOT / ("data/people/" + name + ".json"),
                frozen.parent / (name + ".json"),
            )
        shutil.copy2(
            ROOT / "data/keywords/vocabulary.json", frozen.parent / "vocabulary.json"
        )
    for name in ("identity-audit.txt", "keywords.txt"):
        dest = frozen.parent / name
        if not dest.exists():
            shutil.copy2(ROOT / "data/two-source/prompts" / name, dest)
    manifest = run_dir / "source-manifest.json"
    if manifest.exists():
        previous = read(manifest)
        for record in previous["files"]:
            assert (
                digest((run_dir / record["path"]).read_bytes()) == record["sha256"]
            ), ("Frozen input changed: " + record["path"])
        previous_paths = {record["path"] for record in previous["files"]}
        actual_paths = {
            p.relative_to(run_dir).as_posix() for p in frozen.parent.glob("*")
        }
        # Only this one-time protocol upgrade may append prompt templates to an
        # older pilot freeze. Other additions are refused, never silently adopted.
        assert actual_paths - previous_paths <= {
            "inputs/identity-audit.txt",
            "inputs/keywords.txt",
        }
        if actual_paths == previous_paths:
            return
    save(
        manifest,
        {
            "homepage_url": read(CONFIG)["homepage_url"],
            "snapshot_policy": "Existing original lab HTML snapshot, deliberately frozen for comparison; no old enriched fields.",
            "files": [
                {
                    "path": p.relative_to(run_dir).as_posix(),
                    "sha256": digest(p.read_bytes()),
                }
                for p in sorted(frozen.parent.glob("*"))
            ],
        },
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="work/two-source/current")
    parser.add_argument("--iteration", default="v1")
    parser.add_argument(
        "--ids", help="Comma-separated pilot IDs; omit for entire lab list"
    )
    parser.add_argument("--broad", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--through", type=int, default=5, choices=(1, 2, 3, 4, 5))
    args = parser.parse_args()
    config = read(CONFIG)
    run_dir = ROOT / args.run
    initialize(run_dir)
    output = run_dir / "iterations" / args.iteration
    output.mkdir(parents=True, exist_ok=True)
    save(output / "protocol.json", config)
    shutil.copy2(Path(__file__), output / "pipeline.py")
    homepage = parse_homepage(
        (run_dir / "inputs/homepage.html").read_text(encoding="utf-8"),
        config["homepage_url"],
    )
    if args.ids:
        wanted = set(args.ids.split(","))
        assert wanted <= {r["id"] for r in homepage["papers"]}, "Unknown pilot IDs"
        homepage["papers"] = [r for r in homepage["papers"] if r["id"] in wanted]
    save(output / "01-homepage.json", homepage)
    save(
        output / "run-manifest.json",
        {
            "started_at": now(),
            "rules_sha256": digest(config),
            "rules_version": config["rules_version"],
            "script_sha256": digest(Path(__file__).read_bytes()),
            "offline": args.offline,
            "broad": args.broad,
            "paper_ids": [r["id"] for r in homepage["papers"]],
            "fact_sources": config["allowed_fact_sources"],
            "input_manifest_sha256": digest(read(run_dir / "source-manifest.json")),
        },
    )
    print("Stage 1:", len(homepage["papers"]), "papers", flush=True)
    if args.through == 1:
        return
    client = Client(run_dir, config["requests"], args.offline)
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=config["requests"]["workers"]
    ) as pool:
        identities = list(
            pool.map(
                lambda p: resolve(p, client, config["identity"], args.broad),
                homepage["papers"],
            )
        )
    save(
        output / "02-identity.json",
        {"summary": summary(identities), "papers": identities},
    )
    graduated = read(run_dir / "inputs/graduated-students.json")
    roster = {
        "current": read(run_dir / "inputs/current-students.json")["students"],
        "graduated": graduated["students"]
        + [
            {"author_name": x}
            for x in graduated.get("previously_confirmed_retained", [])
        ],
    }
    save(
        output / "02-author-occurrences.json",
        {
            "rows": author_occurrences(identities, roster),
            "policy": "Identifiers and occurrences, never name-only cross-paper merge. Roster candidate is distinct from confirmed personnel.",
        },
    )
    save(
        output / "02-review-queue.json",
        {
            "prompt": "data/two-source/prompts/identity-audit.txt",
            "ai_executed": False,
            "papers": [
                r
                for r in identities
                if r["state"] in ("ambiguous", "unmatched", "query_failed")
            ],
        },
    )
    print("Stage 2:", json.dumps(summary(identities)), flush=True)
    if args.through == 2:
        return
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=config["requests"]["workers"]
    ) as pool:
        details = list(
            pool.map(
                lambda p: collect_detail(p, client, config["requests"]), identities
            )
        )
    field_coverage = (
        {k: summary([p["fields"][k] for p in details]) for k in details[0]["fields"]}
        if details
        else {}
    )
    save(
        output / "03-lab-details.json", {"coverage": field_coverage, "papers": details}
    )
    save(
        output / "03-identity-review-queue.json",
        {
            "papers": [
                {
                    "id": p["id"],
                    "reason": "identity_changed_between_search_and_detail",
                    "identity_drift": p["identity_drift"],
                }
                for p in details
                if "identity_drift" in p
            ],
            "action": "Return to stage 2; never overwrite frozen identity in detail collection.",
        },
    )
    print(
        "Stage 3:",
        json.dumps({k: v["success"] for k, v in field_coverage.items()}),
        flush=True,
    )
    if args.through == 3:
        return
    external, relations, selection = external_stage(details, identities, client, config)
    save(output / "04-external.json", external)
    save(
        output / "04-relations.json",
        {"rows": relations, "external_external_citations": False, "depth": 1},
    )
    save(
        output / "04-graph-selection.json",
        {
            "ids": selection,
            "budget": config["external"]["graph_budget"],
            "ranking": config["external"]["graph_ranking"],
            "minimum_distinct_lab_neighbors": config["external"].get(
                "graph_min_lab_neighbors", 1
            ),
            "degree_basis": "full_direct_reference_and_citing_relations_before_topK_and_UI_filters",
            "candidate_count": len(external["records"]),
        },
    )
    print(
        "Stage 4:",
        json.dumps(external["summary"]),
        "graph:",
        len(selection),
        flush=True,
    )
    if args.through == 5:
        papers = feature_inputs(
            identities,
            details,
            external,
            selection,
            read(run_dir / "inputs/vocabulary.json"),
            output,
        )
        print(
            "Stage 5: frozen text inputs:",
            len(papers),
            "AI tasks not executed",
            flush=True,
        )


if __name__ == "__main__":
    main()
