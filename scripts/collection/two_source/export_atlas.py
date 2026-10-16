"""Export the frozen two-source snapshot into the static Lab Atlas data schema.

The exporter is deterministic and reads only the two-source snapshot, the fixed
keyword vocabulary, and the user-maintained author groups.  It writes a preview
tree by default; ``--promote`` copies the preview data into ``data/`` after the
basic cardinality checks pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT = ROOT / "data/two-source/snapshot"
VOCAB = ROOT / "data/keywords/vocabulary.json"
OLD_VOCAB = ROOT / "data/atlas/paper-keywords.json"
GROUPS = ROOT / "data/people/author-groups.json"
HOME_URL = "https://jyh-learning.github.io/papers.html"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def sha(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def source(name, url=None):
    return {"name": name, "url": url or ""}


def field(value, state, sources=None, **extra):
    result = {"value": value, "state": state, "sources": sources or []}
    result.update(extra)
    return result


def url_id(url):
    return (url or "").rstrip("/").split("/")[-1] if url else None


def stable_person_id(key):
    return "person-" + hashlib.sha1(str(key).encode()).hexdigest()[:12]


def norm_name(name):
    return " ".join(str(name or "").strip().split()).casefold()


def canonical_occurrence_name(name):
    value = norm_name(name)
    value = value[4:] if value.startswith("and ") else value
    if "," in value:
        left, right = [x.strip() for x in value.split(",", 1)]
        value = (right + " " + left).strip()
    return value


def keyword_vocab():
    raw = read(OLD_VOCAB).get("vocabulary") or []
    if not raw:
        raw = read(VOCAB).get("keywords") or []
    colors = {
        "research_task": "#6877ce",
        "method": "#54a3a0",
        "research_setting": "#bd6c8c",
        "application_object": "#d99850",
    }
    out = []
    for item in raw:
        dim = item.get("dimension") or item.get("primary_dimension") or "method"
        out.append(
            {
                "id": item["id"],
                "name": item.get("name")
                or item.get("canonical_zh")
                or item.get("canonical_en")
                or item["id"],
                "color": item.get("color") or colors.get(dim, "#8e98a9"),
                "dimension": dim,
                "aliases": item.get("aliases", []),
            }
        )
    return out


def classification(paper, vocabulary):
    """Fixed rule-based display fields derived from accepted keyword IDs and title."""
    anchors = {
        "clustering": {
            "deep-clustering": 4,
            "ensemble-clustering": 4,
            "subspace-clustering": 4,
            "dimensionality-reduction": 4,
        },
        "labels": {
            "multi-label-learning": 4,
            "label-distribution-learning": 4,
            "label-enhancement": 4,
            "partial-label-learning": 4,
            "noisy-label-learning": 4,
            "label-correlation-modeling": 1,
        },
        "foundation": {
            "large-language-models": 3,
            "vision-language-models": 3,
            "large-vision-language-models": 3,
            "model-merging": 4,
            "value-preference-alignment": 4,
            "multimodal-retrieval": 4,
            "latent-reasoning": 2,
        },
        "vision": {
            "image-segmentation": 4,
            "person-reidentification": 4,
            "hyperspectral-images": 2,
            "underwater-images": 2,
            "zero-shot-learning": 2,
            "open-vocabulary-recognition": 3,
        },
        "recovery": {"data-imputation-recovery": 4, "traffic-data": 2},
        "trust": {
            "adversarial-robustness": 4,
            "confidence-calibration": 3,
            "hallucination-mitigation": 3,
            "noisy-label-learning": 2,
        },
    }
    title_rules = {
        "clustering": (
            6,
            r"\b(?:cluster(?:ing|s)?|representation learning|dimensionality reduction|spectral embedding)\b",
        ),
        "labels": (
            6,
            r"\b(?:multi[\s-]?label(?:led)?|partial[\s-]?label|label distribution|label enhancement|label disambiguation|noisy[\s-]?label|label correlation|semi[\s-]?supervised learning|weakly[\s-]?supervised (?:learning|classification)|multiple instance learning|long[\s-]?tailed (?:learning|classification))\b",
        ),
        "foundation": (
            5,
            r"\b(?:large language models?|large vision[\s-]language models?|vision[\s-]language|multi[\s-]?modal|language-assisted|model merg(?:ing|e)|preference align(?:ment)?|retrieval augmented generation|llms?|lvlms?)\b",
        ),
        "vision": (
            5,
            r"\b(?:image (?:segmentation|classification|restoration|quality|processing|enhancement)|saliency|salient(?: object)?|superpixels?|person re[\s-]?identification|hyperspectral|underwater|zero-shot (?:learning|recognition)|open-vocabulary)\b",
        ),
        "recovery": (
            6,
            r"\b(?:data (?:imputation|completion|recovery)|matrix completion|tensor completion|(?:matrix|tensor) recovery|traffic (?:data|speed|state|flow)|missing data|incomplete data)\b",
        ),
        "trust": (
            4,
            r"\b(?:adversarial|calibrat(?:ion|ed)|hallucinations?|uncertainty|trustworthy|fairness|differential privacy|certified robustness)\b",
        ),
    }
    import re

    scores = {key: 0 for key in anchors}
    evidence = []
    for item in paper.get("keywords", []):
        kid = item.get("id")
        for key, weights in anchors.items():
            if kid in weights:
                value = weights[kid] + (
                    1 if item.get("evidence_field") == "title" else 0
                )
                scores[key] = max(scores[key], value)
                evidence.append(
                    {
                        "field_id": key,
                        "keyword_id": kid,
                        "kind": "keyword",
                        "text": item.get("name", kid),
                        "score": value,
                    }
                )
    title = str(paper.get("title") or "").replace("‐", "-").replace("‑", "-")
    for key, (weight, pattern) in title_rules.items():
        match = re.search(pattern, title, flags=re.I)
        if match:
            scores[key] += weight
            evidence.append(
                {
                    "field_id": key,
                    "keyword_id": None,
                    "kind": "title",
                    "text": match.group(0),
                    "score": weight,
                }
            )
    order = ["clustering", "labels", "recovery", "vision", "foundation", "trust"]
    ranked = sorted(
        ({"id": k, "score": v} for k, v in scores.items() if v >= 2),
        key=lambda x: (-x["score"], order.index(x["id"])),
    )
    return {
        "primary": ranked[0]["id"] if ranked else None,
        "secondary": [x["id"] for x in ranked[1:]],
        "scores": scores,
        "evidence": evidence,
        "source": "title_and_keywords",
    }


def load_snapshot():
    papers = read(SNAPSHOT / "papers.json")["papers"]
    external = read(SNAPSHOT / "external.json")["records"]
    relations = read(SNAPSHOT / "04-relations.json")["rows"]
    selected = set(read(SNAPSHOT / "04-graph-selection.json")["ids"])
    keywords = {x["paper_id"]: x for x in read(SNAPSHOT / "05-keywords.json")["papers"]}
    vectors = {x["id"]: x for x in read(SNAPSHOT / "05-vectors.json")["rows"]}
    persons = read(SNAPSHOT / "02-persons.json")["rows"]
    profiles = read(SNAPSHOT / "05-author-profiles.json")["profiles"]
    return papers, external, relations, selected, keywords, vectors, persons, profiles


def build_people(person_rows, groups):
    occurrences = []
    people = {}
    affiliations = defaultdict(lambda: {"name": "", "id": None, "institutions": []})
    by_occurrence = {}
    repair_mappings = []
    legacy_people = {}
    legacy_occurrences = {}
    legacy_path = ROOT / "_legacy/v1.0/data/people/author-identities.json"
    if legacy_path.exists():
        legacy = read(legacy_path)
        legacy_people = {p["id"]: p for p in legacy.get("people", [])}
        legacy_occurrences = {
            (o["paper_id"], canonical_occurrence_name(o["name"])): o["person_id"]
            for o in legacy.get("occurrences", [])
        }
    for row in person_rows:
        occurrence_key = (
            row["paper_id"],
            canonical_occurrence_name(row.get("name") or ""),
        )
        legacy_pid = legacy_occurrences.get(occurrence_key)
        key = (
            row.get("resolved_person_id")
            or row.get("person_key")
            or row.get("openalex_author_id")
            or f"occurrence:{row['paper_id']}:{row['position']}"
        )
        pid = legacy_pid or stable_person_id(key)
        name = row.get("name") or ""
        display_name = name
        if pid not in people:
            old = legacy_people.get(pid, {})
            people[pid] = {
                "id": pid,
                "name": old.get("name") or name,
                "display_name": old.get("display_name") or old.get("name") or name,
                "identity_note": old.get("identity_note", ""),
            }
        if (
            row.get("roster_candidate")
            and row.get("group_state") == "needs_roster_identity_confirmation"
        ):
            people[pid]["identity_note"] = "实验室名册归属仍需核对。"
        occurrences.append(
            {"paper_id": row["paper_id"], "name": display_name, "person_id": pid}
        )
        by_occurrence[(row["paper_id"], int(row["position"]))] = {
            "id": pid,
            "name": display_name,
            "raw": name,
            "excluded": False,
        }
        if legacy_pid:
            repair_mappings.append(
                {
                    "occurrence_id": f"{row['paper_id']}:{row['position']}",
                    "paper_id": row["paper_id"],
                    "position": row["position"],
                    "name": name,
                    "person_id": pid,
                    "evidence": [
                        {
                            "source": "legacy_v1.0",
                            "field": "occurrence",
                            "match": "paper_id + author name",
                        }
                    ],
                }
            )
        inst = affiliations[row["paper_id"]]
        for item in row.get("institutions", []):
            if item.get("display_name"):
                inst["institutions"].append(
                    {"id": item.get("id"), "name": item["display_name"]}
                )
    for pid, item in affiliations.items():
        seen = set()
        item["institutions"] = [
            x
            for x in item["institutions"]
            if not (x["name"] in seen or seen.add(x["name"]))
        ]
    return people, occurrences, affiliations, by_occurrence, repair_mappings


def load_vectors(vector_rows):
    result = {}
    for row in vector_rows.values():
        path = SNAPSHOT / "vectors" / f"{row['vector_key']}.json"
        try:
            data = read(path)
            vec = data.get("vector")
            if isinstance(vec, list) and len(vec) == 768:
                result[row["id"]] = (row, vec)
        except (OSError, ValueError, KeyError):
            continue
    return result


def build_nodes(
    papers,
    external,
    selected,
    kw_map,
    vector_rows,
    person_rows,
    vocabulary,
    by_occurrence,
):
    lab_ids = {p["id"] for p in papers}
    ext_by_id = {
        x["id"]: x for x in external if x.get("record") and x["id"] in selected
    }
    nodes = []
    paper_fields = {}
    keyword_papers = {}
    keyword_statuses = {}
    retrieval_papers = []
    retrieval_external = []
    retrieval_bibliography = {}

    def person_records(pid):
        rows = sorted(
            (r for r in person_rows if r["paper_id"] == pid),
            key=lambda r: r["position"],
        )
        return [
            {
                "id": by_occurrence[(r["paper_id"], int(r["position"]))]["id"],
                "name": r["name"],
                "raw": r["name"],
                "excluded": False,
            }
            for r in rows
            if (r["paper_id"], int(r["position"])) in by_occurrence
        ]

    def annotation(pid, is_lab):
        raw = kw_map.get(pid)
        if raw and raw.get("state") == "ready":
            vocab = {x["id"]: x for x in vocabulary}
            values = []
            for kid in raw.get("keyword_ids", []):
                evidence = next(
                    (e for e in raw.get("evidence", []) if e.get("keyword_id") == kid),
                    {},
                )
                values.append(
                    {
                        "id": kid,
                        "name": vocab.get(kid, {}).get("name", kid),
                        "dimension": vocab.get(kid, {}).get("dimension"),
                        "score": 1,
                        "evidence_field": evidence.get("field"),
                        "exact_quote": evidence.get("quote", ""),
                    }
                )
            return values, ("annotated" if values else "empty")
        return [], "missing" if is_lab else "empty"

    def lab_record(row):
        homepage = row["homepage"]
        adopted = row.get("adopted") or {}
        matched = row.get("identity_state") == "ready"
        title = adopted.get("title") or homepage.get("title")
        authors = adopted.get("authors") or homepage.get("authors") or []
        year = adopted.get("year") or homepage.get("year") or 2027
        venue = adopted.get("venue") or homepage.get("venue") or ""
        details = row.get("fields") or {}
        oa = adopted.get("openalex")
        doi = adopted.get("doi")
        abstract = (
            details.get("abstract", {}).get("value")
            if details.get("abstract", {}).get("state") == "ready"
            else None
        )
        citations = (
            details.get("citations", {}).get("value")
            if details.get("citations", {}).get("state") == "ready"
            else None
        )
        references = (
            details.get("references", {}).get("value")
            if isinstance(details.get("references", {}).get("value"), list)
            else []
        )
        citing = details.get("citing", {})
        citing_ids = (
            citing.get("ids", []) if isinstance(citing.get("ids"), list) else []
        )
        author_recs = person_records(row["id"])
        labels, kstate = annotation(row["id"], True)
        vector = vector_rows.get(row["id"])
        node = {
            "id": row["id"],
            "title": title,
            "lab": True,
            "year": year,
            "venue": venue,
            "authors": authors,
            "author_ids": [x["id"] for x in author_recs],
            "institutions": [],
            "doi": doi,
            "openalex": oa,
            "links": list(
                dict.fromkeys(homepage.get("links", []) + [x for x in [doi, oa] if x])
            ),
            "abstract": abstract or "",
            "citations": citations if isinstance(citations, (int, float)) else 0,
            "references": references,
            "reference_status": details.get("references", {}).get("state", "missing"),
            "citing_status": citing.get("state", "missing"),
            "api_topics": details.get("database_topics", {}).get("value") or [],
            "source": "lab_homepage+openalex" if matched else "lab_homepage",
            "match_status": (
                "matched" if matched else row.get("identity_state", "unmatched")
            ),
            "publication_status": adopted.get("publication_status")
            or homepage.get("publication_status"),
            "author_records": [{"id": x["id"], "name": x["name"]} for x in author_recs],
            "institution_records": [],
            "metadata_sources": {k: details.get(k, {}).get("source") for k in details},
            "referenced_works_count": len(references),
            "source_url": homepage.get("source_url", HOME_URL),
            "list_title": homepage.get("title"),
            "list_year": homepage.get("year"),
            "list_authors": homepage.get("authors", []),
            "list_venue": homepage.get("venue", ""),
            "featured": False,
            "tags": [x["id"] for x in labels],
            "keywords": labels,
            "keyword_status": kstate,
            "keyword_reason": [],
            "keyword_input": {"title": title, "abstract_available": bool(abstract)},
        }
        if vector:
            vr = vector[0] if isinstance(vector, tuple) else vector
            node.update(
                {
                    "semantic_status": "available",
                    "semantic_source": "本地 SPECTER2",
                    "semantic_model": "specter2_proximity",
                    "semantic_vector_key": vr["vector_key"],
                    "semantic_input": vr["input"],
                }
            )
        else:
            node.update(
                {
                    "semantic_status": "not_available",
                    "semantic_source": "本地 SPECTER2",
                    "semantic_model": "specter2_proximity",
                    "semantic_vector_key": None,
                    "semantic_input": {
                        "fields": ["title"] if title else [],
                        "sha256": "",
                    },
                }
            )
        return node, labels, kstate, details, homepage, adopted, author_recs

    for row in papers:
        node, labels, kstate, details, homepage, adopted, author_recs = lab_record(row)
        nodes.append(node)
        keyword_papers[row["id"]] = labels
        keyword_statuses[row["id"]] = kstate
        paper_fields[row["id"]] = classification(node, vocabulary)
        retrieval_papers.append(
            make_retrieval_lab(
                node, row, details, homepage, adopted, author_recs, labels, kstate
            )
        )

    for ext in external:
        record = ext.get("record")
        if not record or ext["id"] not in selected:
            continue
        labels, kstate = annotation(ext["id"], False)
        vector = vector_rows.get(ext["id"])
        authors = record.get("authors") or []
        author_records = record.get("author_records") or []
        node = {
            "id": ext["id"],
            "title": record.get("title") or ext["id"],
            "lab": False,
            "year": record.get("year") or 2027,
            "venue": record.get("venue") or "",
            "authors": authors,
            "author_ids": [
                a.get("author", {}).get("id")
                for a in author_records
                if a.get("author", {}).get("id")
            ],
            "institutions": [
                i.get("display_name")
                for a in author_records
                for i in a.get("institutions", [])
                if i.get("display_name")
            ],
            "doi": record.get("doi"),
            "openalex": record.get("openalex"),
            "links": list(
                dict.fromkeys(
                    [x for x in [record.get("openalex"), record.get("doi")] if x]
                )
            ),
            "abstract": record.get("abstract") or "",
            "citations": (
                record.get("citations")
                if isinstance(record.get("citations"), (int, float))
                else 0
            ),
            "references": [],
            "reference_status": "not_collected",
            "citing_status": "not_collected",
            "api_topics": record.get("topics") or [],
            "source": "openalex",
            "match_status": "database",
            "publication_status": "formal",
            "author_records": [],
            "institution_records": [],
            "metadata_sources": {
                "title": "openalex",
                "authors": "openalex",
                "year": "openalex",
                "venue": "openalex",
                "abstract": "openalex",
            },
            "referenced_works_count": 0,
            "source_url": record.get("openalex") or "",
            "tags": [x["id"] for x in labels],
            "keywords": labels,
            "keyword_status": kstate,
            "keyword_reason": [],
            "keyword_input": {
                "title": record.get("title"),
                "abstract_available": bool(record.get("abstract")),
            },
        }
        if vector:
            vr = vector[0] if isinstance(vector, tuple) else vector
            node.update(
                {
                    "semantic_status": "available",
                    "semantic_source": "本地 SPECTER2",
                    "semantic_model": "specter2_proximity",
                    "semantic_vector_key": vr["vector_key"],
                    "semantic_input": vr["input"],
                }
            )
        else:
            node.update(
                {
                    "semantic_status": "not_available",
                    "semantic_source": "本地 SPECTER2",
                    "semantic_model": "specter2_proximity",
                    "semantic_vector_key": None,
                    "semantic_input": {"fields": ["title"]},
                }
            )
        nodes.append(node)
        keyword_papers[ext["id"]] = labels
        keyword_statuses[ext["id"]] = kstate
        paper_fields[ext["id"]] = classification(node, vocabulary)
        retrieval_external.append(
            make_retrieval_external(node, record, labels, kstate, vector)
        )
        retrieval_bibliography[ext["id"]] = {
            "id": ext["id"],
            "title": node["title"],
            "authors": authors,
            "venue": node["venue"],
            "year": node["year"],
            "citations": node["citations"],
            "url": node["openalex"] or node["doi"],
            "source": "OpenAlex",
        }
    return (
        nodes,
        paper_fields,
        keyword_papers,
        keyword_statuses,
        retrieval_papers,
        retrieval_external,
        retrieval_bibliography,
    )


def make_retrieval_lab(
    node, row, details, homepage, adopted, author_recs, labels, kstate
):
    oa = adopted.get("openalex")
    oa_src = [source("OpenAlex", oa)] if oa else []
    home_src = [source("实验室主页", homepage.get("source_url", HOME_URL))]
    sources = list(dict.fromkeys((tuple(x.items()) for x in home_src + oa_src)))
    sources = [dict(x) for x in sources]

    def sf(value, state, src=None, **extra):
        return field(
            value,
            (
                state
                if state
                in ("ready", "empty", "partial", "missing", "annotated", "excluded")
                else "missing"
            ),
            src or sources,
            **extra,
        )

    year = node["year"]
    abstract = node["abstract"] or None
    refs = node["references"]
    citing = details.get("citing", {})
    citing_ids = citing.get("ids", []) if isinstance(citing.get("ids"), list) else []
    citations = node["citations"] if node["citations"] else None
    identity = {k: adopted.get(k) for k in ["openalex", "doi"] if adopted.get(k)}
    vector_ready = node.get("semantic_status") == "available"
    vector_input = node.get("semantic_input") or {
        "fields": ["title"] if node.get("title") else []
    }
    vector_value = "SPECTER2 · 768维 · " + (
        "标题＋摘要" if "abstract" in vector_input.get("fields", []) else "仅标题"
    )
    vector = field(
        vector_value,
        "ready" if vector_ready else "missing",
        [source("本地 SPECTER2", "https://huggingface.co/allenai/specter2")],
        adoptedValue=vector_value if vector_ready else None,
        explanation=(
            "本地 SPECTER2 使用标题和可用摘要生成论文向量。"
            if vector_ready
            else "尚未生成本地 SPECTER2 向量。"
        ),
        model=node.get("semantic_model") or "specter2_proximity",
        dimensions=768,
        input=vector_input,
        routes=[],
    )
    fields = {
        "title": sf(
            node["title"],
            "ready",
            sources,
            original=homepage.get("title"),
            adoptedValue=node["title"],
            observations=[
                {"value": node["title"], "sources": sources, "adopted": True}
            ],
        ),
        "authors": sf(
            author_recs,
            "ready" if author_recs else "missing",
            oa_src or home_src,
            adoptedValue=[x["name"] for x in author_recs],
            observations=(
                [
                    {
                        "value": [x["name"] for x in author_recs],
                        "sources": oa_src or home_src,
                        "adopted": True,
                    }
                ]
                if author_recs
                else []
            ),
        ),
        "year": sf(
            year,
            "ready" if year else "missing",
            sources,
            adoptedValue=year,
            isPreprint=node.get("publication_status") == "preprint",
            observations=(
                [{"value": year, "sources": sources, "adopted": True}] if year else []
            ),
        ),
        "venue": sf(
            {
                "name": node.get("venue", ""),
                "year": year,
                "kind": node.get("publication_status") or "发表记录",
            },
            "ready" if node.get("venue") else "missing",
            sources,
            adoptedValue=node.get("venue", ""),
            observations=(
                [{"value": node.get("venue", ""), "sources": sources, "adopted": True}]
                if node.get("venue")
                else []
            ),
        ),
        "abstract": sf(
            abstract,
            "ready" if abstract else "missing",
            oa_src,
            adoptedValue=abstract,
            observations=(
                [{"value": abstract, "sources": oa_src, "adopted": True}]
                if abstract
                else []
            ),
        ),
        "references": sf(
            refs,
            details.get("references", {}).get("state", "missing"),
            oa_src,
            total=len(refs),
            parsed=len(refs),
            adoptedValue=refs,
        ),
        "citing": sf(
            citing_ids,
            citing.get("state", "missing"),
            oa_src,
            total=citing.get("query_total"),
            parsed=len(citing_ids),
            ids=citing_ids,
            adoptedValue=citing_ids,
        ),
        "citations": sf(
            citations,
            "ready" if citations is not None else "missing",
            oa_src,
            adoptedValue=citations,
            observations=(
                [{"value": citations, "sources": oa_src, "adopted": True}]
                if citations is not None
                else []
            ),
            attempts=[],
        ),
        "keywords": sf(labels, kstate, [source("标题/摘要标注")], adoptedValue=labels),
        "topics": sf(
            details.get("database_topics", {}).get("value") or [],
            (
                "ready"
                if details.get("database_topics", {}).get("state") == "ready"
                else "missing"
            ),
            oa_src,
            adoptedValue=details.get("database_topics", {}).get("value") or [],
        ),
        "vector": vector,
        "identity": sf(
            identity, "ready" if identity else "review", oa_src, adoptedValue=identity
        ),
    }
    return {
        "id": node["id"],
        "title": node["title"],
        "fields": fields,
        "issues": (
            []
            if row.get("identity_state") == "ready"
            else [
                {
                    "field": "OpenAlex 身份",
                    "reason": row.get("identity_reason", "身份未确定"),
                    "routes": [],
                }
            ]
        ),
        "providers": [x["name"] for x in sources] + ["标题/摘要标注", "本地 SPECTER2"],
        "links": node["links"],
        "publicationReview": None,
    }


def make_retrieval_external(node, record, labels, kstate, vector):
    oa = [source("OpenAlex", record.get("openalex"))]

    def sf(value, state, **extra):
        return field(value, state, oa, **extra)

    authors = [{"name": x, "raw": x, "excluded": True} for x in node["authors"]]
    vector_ready = node.get("semantic_status") == "available"
    vector_input = node.get("semantic_input") or {
        "fields": ["title"] if node.get("title") else []
    }
    vector_value = "SPECTER2 · 768维 · " + (
        "标题＋摘要" if "abstract" in vector_input.get("fields", []) else "仅标题"
    )
    vector_field = field(
        vector_value,
        "ready" if vector_ready else "missing",
        [source("本地 SPECTER2", "https://huggingface.co/allenai/specter2")],
        adoptedValue=vector_value if vector_ready else None,
        explanation=(
            "本地 SPECTER2 使用标题和可用摘要生成论文向量。"
            if vector_ready
            else "尚未生成本地 SPECTER2 向量。"
        ),
        model=node.get("semantic_model") or "specter2_proximity",
        dimensions=768,
        input=vector_input,
        routes=[],
    )
    return {
        "id": node["id"],
        "title": node["title"],
        "providers": ["OpenAlex", "本地 SPECTER2"],
        "links": node["links"],
        "issues": [],
        "fields": {
            "title": sf(
                node["title"],
                "ready",
                adoptedValue=node["title"],
                observations=[{"value": node["title"], "sources": oa, "adopted": True}],
            ),
            "authors": sf(
                authors,
                "ready" if authors else "missing",
                adoptedValue=node["authors"],
                observations=(
                    [{"value": node["authors"], "sources": oa, "adopted": True}]
                    if authors
                    else []
                ),
            ),
            "year": sf(
                node["year"],
                "ready" if node["year"] else "missing",
                adoptedValue=node["year"],
                observations=(
                    [{"value": node["year"], "sources": oa, "adopted": True}]
                    if node["year"]
                    else []
                ),
            ),
            "venue": sf(
                {"name": node["venue"]},
                "ready" if node["venue"] else "missing",
                adoptedValue=node["venue"],
                observations=(
                    [{"value": node["venue"], "sources": oa, "adopted": True}]
                    if node["venue"]
                    else []
                ),
            ),
            "abstract": sf(
                node["abstract"] or None,
                "ready" if node["abstract"] else "missing",
                adoptedValue=node["abstract"] or None,
                observations=(
                    [{"value": node["abstract"], "sources": oa, "adopted": True}]
                    if node["abstract"]
                    else []
                ),
            ),
            "references": sf([], "missing", total=None, parsed=0),
            "citing": sf([], "missing", total=None, parsed=0),
            "citations": sf(
                node["citations"],
                "ready",
                adoptedValue=node["citations"],
                observations=[
                    {"value": node["citations"], "sources": oa, "adopted": True}
                ],
                attempts=[],
            ),
            "keywords": field(
                labels, kstate, [source("标题/摘要标注")], adoptedValue=labels
            ),
            "topics": sf(
                record.get("topics") or [],
                "ready",
                adoptedValue=record.get("topics") or [],
            ),
            "vector": vector_field,
            "identity": sf(
                {k: record.get(k) for k in ["openalex", "doi"] if record.get(k)},
                "ready",
                adoptedValue={
                    k: record.get(k) for k in ["openalex", "doi"] if record.get(k)
                },
            ),
        },
    }


def make_edges(nodes, relations, vector_map, selected, work_to_lab):
    ids = {x["id"] for x in nodes}
    lab = {x["id"] for x in nodes if x["lab"]}
    edges = []
    seen = set()
    for row in relations:
        a, raw_b = row["lab_id"], row["work_id"]
        b = work_to_lab.get(raw_b, raw_b)
        if (
            a not in ids
            or b not in ids
            or (raw_b not in selected and raw_b not in work_to_lab)
        ):
            continue
        if row["direction"] == "reference":
            source_id, target_id = a, b
        else:
            source_id, target_id = b, a
        key = (source_id, target_id, "citation")
        if key in seen:
            continue
        seen.add(key)
        edges.append(
            {
                "id": f"citation:{source_id}:{target_id}",
                "source": source_id,
                "target": target_id,
                "kind": "citation",
                "score": 1.0,
                "tentative": False,
                "evidence": {
                    "source": "OpenAlex",
                    "text": "数据库记录的直接引用",
                    "referenced_id": raw_b,
                },
            }
        )
    ordered = [
        (p["id"], vector_map[p["id"]][1]) for p in nodes if p["id"] in vector_map
    ]
    if ordered:
        # Keep the exporter independent of the model runtime.  The vectors are
        # already L2-normalized, so a dot product is the cosine similarity.
        for aid, avec in ordered:
            if aid not in lab:
                continue
            for bid, bvec in ordered:
                if aid == bid:
                    continue
                key = tuple(sorted((aid, bid))) + ("semantic",)
                if key in seen:
                    continue
                seen.add(key)
                score = sum(float(x) * float(y) for x, y in zip(avec, bvec))
                edges.append(
                    {
                        "id": f"semantic:{aid}:{bid}",
                        "source": aid,
                        "target": bid,
                        "kind": "semantic",
                        "score": round(score, 6),
                        "tentative": True,
                        "evidence": {
                            "model": "specter2_proximity",
                            "source": "local",
                            "source_ids": [aid, bid],
                            "text": "本地 SPECTER2：标题与可用摘要的余弦相似度",
                        },
                    }
                )
    return edges


def build(output: Path):
    (
        papers,
        external,
        relations,
        selected,
        kw_map,
        vector_rows,
        person_rows,
        profiles,
    ) = load_snapshot()
    vocabulary = keyword_vocab()
    people, occurrences, affiliations, by_occurrence, repair_mappings = build_people(
        person_rows, read(GROUPS)
    )
    vector_map = load_vectors(vector_rows)
    snapshot_stamp = read(SNAPSHOT / "run-manifest.json").get("started_at")
    (
        nodes,
        paper_fields,
        keyword_papers,
        keyword_statuses,
        retrieval_papers,
        retrieval_external,
        bibliography,
    ) = build_nodes(
        papers,
        external,
        selected,
        kw_map,
        vector_rows,
        person_rows,
        vocabulary,
        by_occurrence,
    )
    # Citation lists use OpenAlex work IDs.  Add confirmed laboratory works to
    # the same lookup table so annual citation history can date lab-to-lab links.
    for node in nodes:
        if node.get("lab") and node.get("openalex"):
            wid = url_id(node["openalex"])
            bibliography[wid] = {
                "id": wid,
                "title": node["title"],
                "authors": node.get("authors", []),
                "venue": node.get("venue", ""),
                "year": node.get("year"),
                "citations": node.get("citations", 0),
                "url": node["openalex"],
                "source": "OpenAlex",
            }
    work_to_lab = {}
    for row in papers:
        wid = url_id((row.get("adopted") or {}).get("openalex"))
        if wid:
            work_to_lab[wid] = row["id"]
    edges = make_edges(nodes, relations, vector_map, selected, work_to_lab)
    for i, node in enumerate(nodes):
        angle = i * math.pi * (3 - math.sqrt(5))
        radius = 280 * math.sqrt(i + 1)
        node["x"], node["y"] = round(radius * math.cos(angle), 2), round(
            radius * math.sin(angle), 2
        )
    field_list = [
        {"id": "clustering", "name": "聚类与表示学习", "color": "#6877ce"},
        {"id": "labels", "name": "标签学习", "color": "#d99850"},
        {"id": "foundation", "name": "大模型与多模态", "color": "#54a3a0"},
        {"id": "vision", "name": "视觉感知与图像处理", "color": "#679aba"},
        {"id": "recovery", "name": "数据补全与恢复", "color": "#839c56"},
        {"id": "trust", "name": "鲁棒与可信学习", "color": "#bd6c8c"},
    ]
    # IDF is calculated over laboratory papers, including valid empty annotations.
    lab_ids = {x["id"] for x in nodes if x["lab"]}
    df = Counter()
    for pid in lab_ids:
        for kid in {x["id"] for x in keyword_papers.get(pid, [])}:
            df[kid] += 1
    nlab = len(lab_ids)
    idf = {
        k["id"]: math.log((nlab + 1) / (df.get(k["id"], 0) + 1)) + 1 for k in vocabulary
    }
    coverage = {
        "total": len(nodes),
        "accepted": sum(
            keyword_statuses.get(x["id"]) in ("annotated", "empty") for x in nodes
        ),
        "with_keywords": sum(bool(keyword_papers.get(x["id"])) for x in nodes),
        "empty": sum(keyword_statuses.get(x["id"]) == "empty" for x in nodes),
        "excluded": 0,
    }
    paper_keywords = {
        "papers": keyword_papers,
        "statuses": keyword_statuses,
        "vocabulary": vocabulary,
        "idf": idf,
        "coverage": coverage,
        "source": "固定词表与标题摘要证据",
        "idf_corpus": "实验室论文",
        "updated": snapshot_stamp,
    }
    fields_data = {
        "fields": field_list,
        "papers": paper_fields,
        "stats": {
            "all": Counter(
                x["primary"] or "unclassified" for x in paper_fields.values()
            ),
            "lab": Counter(
                paper_fields[x]["primary"] or "unclassified" for x in lab_ids
            ),
        },
        "schema": "two-source-title-keyword-v1",
        "method": "标题与受控关键词规则",
    }
    for key in ["all", "lab"]:
        fields_data["stats"][key] = dict(fields_data["stats"][key])
    atlas = {
        "meta": {
            "updated": snapshot_stamp or datetime.now(timezone.utc).isoformat(),
            "source": "实验室主页 + OpenAlex 两源冻结快照",
            "stats": {
                "lab": len(lab_ids),
                "external": len(nodes) - len(lab_ids),
                "vectors": len(vector_map),
                "edges": Counter(x["kind"] for x in edges),
            },
            "limits": {
                "external_nodes": len(selected),
                "external_graph_min_lab_neighbors": 2,
            },
            "layout": "two_source_circular_seed_with_dynamic_force_layout",
            "notes": [
                "外部文献来自实验室论文的一层引用与被引邻域。",
                "外部文献之间不绘制引用边。",
            ],
            "semantic": read(SNAPSHOT / "05-vectors.json")["model"],
            "keywords": coverage,
        },
        "topics": vocabulary,
        "nodes": nodes,
        "edges": edges,
    }
    retrieval = {
        "meta": {
            "snapshot": snapshot_stamp,
            "scope": "实验室主页与OpenAlex两源冻结快照",
            "coverage": {
                "total": len(lab_ids),
                "authorCount": len(people),
                "references": sum(
                    bool(x["fields"]["references"].get("value"))
                    for x in retrieval_papers
                ),
                "referenceIDs": sum(
                    len(x["fields"]["references"].get("value") or [])
                    for x in retrieval_papers
                ),
                "referenceTitles": sum(
                    1
                    for x in retrieval_papers
                    for rid in x["fields"]["references"].get("value") or []
                    if rid in bibliography
                ),
                "citingTotal": sum(
                    x["fields"]["citing"].get("total") or 0 for x in retrieval_papers
                ),
                "citingIDs": sum(
                    len(x["fields"]["citing"].get("ids") or [])
                    for x in retrieval_papers
                ),
                "citingTitles": sum(
                    1
                    for x in retrieval_papers
                    for rid in x["fields"]["citing"].get("ids") or []
                    if rid in bibliography
                ),
                "keywords": sum(
                    bool(x["fields"]["keywords"].get("value")) for x in retrieval_papers
                ),
            },
            "groups": {},
            "keywordAnnotations": {
                "annotated": sum(
                    x["fields"]["keywords"]["state"] == "annotated"
                    for x in retrieval_papers
                )
            },
            "keywordMethod": "标题与可用摘要匹配固定词表",
        },
        "papers": retrieval_papers,
        "authors": [],
        "external": retrieval_external,
        "bibliography": bibliography,
    }
    # Build authors and weighted profiles from the exported occurrence mapping.
    by_person = defaultdict(list)
    for occ in occurrences:
        by_person[occ["person_id"]].append(occ["paper_id"])
    assignments = read(GROUPS).get("assignments", {})
    profiles_by_name = {x.get("name"): x for x in profiles}
    for pid, person in sorted(people.items(), key=lambda x: x[1]["name"].casefold()):
        pids = list(dict.fromkeys(by_person[pid]))
        weights = Counter()
        denominator = 0.0
        for paper_id in pids:
            node = next((x for x in nodes if x["id"] == paper_id), None)
            if not node or keyword_statuses.get(paper_id) not in ("annotated", "empty"):
                continue
            author_ids = node.get("author_ids", [])
            if pid in author_ids:
                pos = author_ids.index(pid)
            else:
                names = node.get("authors", [])
                pos = next(
                    (
                        i
                        for i, n in enumerate(names)
                        if norm_name(n) == norm_name(person["name"])
                    ),
                    99,
                )
            first_is_yuheng = bool(node.get("authors")) and norm_name(
                node["authors"][0]
            ) == norm_name("Yuheng Jia")
            weight = 1.0 if pos == 0 or (first_is_yuheng and pos == 1) else 0.2
            denominator += weight
            for kw in keyword_papers.get(paper_id, []):
                weights[kw["id"]] += weight
        author_keywords = [
            {
                "id": kid,
                "name": next((x["name"] for x in vocabulary if x["id"] == kid), kid),
                "weight": value / denominator if denominator else 0,
                "papers": [],
            }
            for kid, value in weights.items()
        ]
        retrieval["authors"].append(
            {
                "id": pid,
                "name": person["name"],
                "identityName": person["name"],
                "aliases": [],
                "group": assignments.get(person["name"], "other"),
                "papers": pids,
                "keywords": sorted(author_keywords, key=lambda x: -x["weight"]),
                "state": "derived",
                "identityLabel": (
                    "已对应" if not person.get("identity_note") else "待核对"
                ),
                "identityNote": person.get("identity_note", ""),
                "sources": ["实验室主页", "OpenAlex"],
                "chinese": "",
                "keywordSource": "标题与摘要标注 · 按作者汇总",
            }
        )
    retrieval["meta"]["authorCount"] = len(retrieval["authors"])
    network_evidence = {
        "coverage": retrieval["meta"]["coverage"],
        "bibliography": bibliography,
        "papers": {
            x["id"]: {
                "title": x["title"],
                "fields": {
                    "title": {"adoptedValue": x["title"]},
                    "year": {"adoptedValue": x["fields"]["year"].get("value")},
                    "venue": {
                        "adoptedValue": (x["fields"]["venue"].get("value") or {}).get(
                            "name", ""
                        )
                    },
                    "authors": {
                        "adoptedValue": [
                            a.get("name")
                            for a in x["fields"]["authors"].get("value", [])
                        ]
                    },
                    "citations": {
                        "adoptedValue": x["fields"]["citations"].get("value")
                    },
                    "abstract": {"adoptedValue": x["fields"]["abstract"].get("value")},
                    "keywords": x["fields"]["keywords"],
                    "topics": x["fields"]["topics"],
                },
                "links": x.get("links", []),
            }
            for x in retrieval_papers
        },
        "keywordAnnotations": {
            "annotated": coverage["with_keywords"],
            "empty": coverage["empty"],
            "excluded": 0,
        },
    }
    people_json = {"people": list(people.values()), "occurrences": occurrences}
    group_json = read(GROUPS)
    affiliation_json = {pid: value for pid, value in affiliations.items()}
    person_mapping_payload = {
        "schema": "lab-atlas-person-mappings/v1",
        "policy": "旧版已采用 occurrence 对齐修复；新 occurrence 没有旧版对应时保留两源身份结果。",
        "mappings": repair_mappings,
    }
    for rel, payload in [
        ("data/atlas/data.json", atlas),
        ("data/atlas/paper-keywords.json", paper_keywords),
        ("data/atlas/paper-fields.json", fields_data),
        ("data/atlas/retrieval-data.json", retrieval),
        ("data/atlas/network-evidence.json", network_evidence),
        ("data/people/author-identities.json", people_json),
        ("data/people/author-affiliations.json", affiliation_json),
        ("data/people/author-groups.json", group_json),
        ("data/two-source/person-mappings.json", person_mapping_payload),
    ]:
        write(output / rel, payload)
    # Keep the frozen relation set available to later rebuilds without copying it into data/.
    write(
        output / "data/atlas/two-source-export.json",
        {
            "snapshot": "data/two-source/snapshot",
            "lab": len(lab_ids),
            "external": len(selected),
            "edges": len(edges),
        },
    )
    return {
        "nodes": len(nodes),
        "lab": len(lab_ids),
        "external": len(nodes) - len(lab_ids),
        "edges": len(edges),
        "semantic": sum(x["kind"] == "semantic" for x in edges),
        "citation": sum(x["kind"] == "citation" for x in edges),
        "authors": len(people),
    }


def promote(preview: Path):
    for rel in [
        "data/atlas/data.json",
        "data/atlas/paper-keywords.json",
        "data/atlas/paper-fields.json",
        "data/atlas/retrieval-data.json",
        "data/atlas/network-evidence.json",
        "data/people/author-identities.json",
        "data/people/author-affiliations.json",
        "data/people/author-groups.json",
        "data/two-source/person-mappings.json",
    ]:
        src = preview / rel
        dst = ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "work/two-source/atlas-preview"
    )
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        shutil.rmtree(args.output)
    result = build(args.output)
    if result["nodes"] != result["lab"] + result["external"] or result["external"] == 0:
        raise SystemExit("invalid export cardinality")
    if args.promote:
        promote(args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
