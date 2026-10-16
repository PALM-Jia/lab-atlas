"""Comparison is the sole new operation allowed to read the frozen legacy facts."""

import argparse
import collections
from pathlib import Path
from pipeline import read, save, ROOT, summary, digest, oid


def run(output, destination):
    output, destination = Path(output), Path(destination)
    new = read(output / "02-identity.json")["papers"]
    details = {r["id"]: r for r in read(output / "03-lab-details.json")["papers"]}
    ext = read(output / "04-external.json")
    legacy = read(ROOT / "_legacy/v1.0/data/atlas/data.json")
    legacy_retrieval = read(ROOT / "_legacy/v1.0/data/atlas/retrieval-data.json")
    old = {r["id"]: r for r in legacy["nodes"] if r["lab"]}
    old_evidence = {r["id"]: r for r in legacy_retrieval["papers"]}
    assert {p["id"] for p in new} == set(
        old
    ), "Comparison requires the same homepage set; use a separate intersection report for changed input snapshots."
    # Compare final adopted retrieval values, not an older graph projection.
    # In v1.0, some fallback counts and six venues exist only in evidence fields.
    for paper_id, paper in old.items():
        for key in (
            "title",
            "authors",
            "year",
            "venue",
            "abstract",
            "citations",
            "references",
        ):
            evidence = old_evidence[paper_id]["fields"].get(key, {})
            if key == "year" and not isinstance(evidence.get("adoptedValue"), int):
                continue  # "预印" is a publication-status label, not a numeric year.
            if evidence.get("adoptedValue") is not None:
                paper[key] = evidence["adoptedValue"]
            elif evidence.get("value") is not None and evidence.get("state") in (
                "ready",
                "empty",
                "partial",
            ):
                paper[key] = evidence["value"]
    coverage = {}
    functions = {
        "identity": (
            lambda p: bool(p.get("openalex")),
            lambda p: p["state"] == "ready",
        ),
        "authors": (
            lambda p: bool(p.get("authors")),
            lambda p: bool(p["adopted"]["authors"]),
        ),
        "year": (
            lambda p: isinstance(p.get("year"), int),
            lambda p: isinstance(p["adopted"]["year"], int),
        ),
        "venue": (
            lambda p: bool(p.get("venue")),
            lambda p: bool(p["adopted"]["venue"]),
        ),
        "abstract": (
            lambda p: bool(p.get("abstract")),
            lambda p: details[p["id"]]["fields"]["abstract"]["state"] == "ready",
        ),
        "citations": (
            lambda p: p.get("citations") is not None,
            lambda p: details[p["id"]]["fields"]["citations"]["state"] == "ready",
        ),
        "references_nonempty": (
            lambda p: bool(p.get("references")),
            lambda p: bool(details[p["id"]]["fields"]["references"].get("value")),
        ),
        "citing_list_received": (
            lambda p: old_evidence[p["id"]]["fields"]["citing"]["state"]
            in ("ready", "empty", "partial"),
            lambda p: details[p["id"]]["fields"]["citing"]["state"]
            in ("ready", "empty", "partial"),
        ),
    }
    for key, (oldfn, newfn) in functions.items():
        lost = [
            p["id"]
            for p in new
            if p["id"] in old and oldfn(old[p["id"]]) and not newfn(p)
        ]
        gained = [
            p["id"]
            for p in new
            if p["id"] in old and not oldfn(old[p["id"]]) and newfn(p)
        ]
        coverage[key] = {
            "legacy": sum(oldfn(p) for p in old.values()),
            "new": sum(newfn(p) for p in new),
            "lost": lost,
            "gained": gained,
        }
    changes = []
    failures = []
    for row in new:
        previous = old.get(row["id"])
        if previous:
            delta = {}
            for key in ("title", "authors", "year", "venue", "openalex"):
                if previous.get(key) != row["adopted"].get(key):
                    delta[key] = {
                        "legacy": previous.get(key),
                        "new": row["adopted"].get(key),
                    }
            for key in ("abstract", "citations", "references"):
                value = details[row["id"]]["fields"][key].get("value")
                oldvalue = previous.get(key)
                if oldvalue != value:
                    delta[key] = {
                        "legacy": (
                            oldvalue
                            if key == "citations"
                            else {"present": bool(oldvalue), "sha256": digest(oldvalue)}
                        ),
                        "new": (
                            value
                            if key == "citations"
                            else {"present": bool(value), "sha256": digest(value)}
                        ),
                    }
            if delta:
                changes.append(
                    {
                        "id": row["id"],
                        "title": row["homepage"]["title"],
                        "changes": delta,
                    }
                )
        if row["state"] != "ready":
            best = sorted(
                row["candidates"], key=lambda c: -c["metrics"]["title_similarity"]
            )[:3]
            failures.append(
                {
                    "id": row["id"],
                    "title": row["homepage"]["title"],
                    "state": row["state"],
                    "reason": row["reason"],
                    "queries": [
                        {
                            "url": e["url"],
                            "http": e.get("http"),
                            "state": e["state"],
                            "reason": e["reason"],
                        }
                        for e in row["attempts"]
                    ],
                    "best_candidates": [
                        {
                            "id": c["work"]["id"],
                            "title": c["work"]["title"],
                            "metrics": c["metrics"],
                        }
                        for c in best
                    ],
                }
            )
    old_external = {p["id"]: p for p in legacy["nodes"] if not p["lab"]}
    selected = set(read(output / "04-graph-selection.json")["ids"])
    new_external = {
        p["record"]["id"]: p["record"] for p in ext["records"] if p["record"]
    }
    field_coverage = read(output / "03-lab-details.json")["coverage"]
    relation_rows = read(output / "04-relations.json")["rows"]
    list_comparison = {}
    for direction, key in [("reference", "references"), ("citing", "citing")]:
        current = [r for r in relation_rows if r["direction"] == direction]
        old_fields = [r["fields"][key] for r in legacy_retrieval["papers"]]
        old_ids = sum(
            (
                len(f.get("value") or [])
                if key == "references"
                else len(f.get("ids") or [])
            )
            for f in old_fields
        )
        old_parsed = sum(f.get("parsed") or 0 for f in old_fields)
        matched = sum(r["endpoint_state"] == "ready" for r in current)
        list_comparison[key] = {
            "legacy_ids": old_ids,
            "legacy_matched_details": old_parsed,
            "new_ids": len(current),
            "new_matched_details": matched,
            "legacy_rate": round(old_parsed / old_ids * 100, 2) if old_ids else None,
            "new_rate": round(matched / len(current) * 100, 2) if current else None,
        }
    external_fields = {
        k: sum(
            bool(p.get(k)) if k != "citations" else p.get(k) is not None
            for p in new_external.values()
        )
        for k in ("authors", "abstract", "citations", "year", "venue")
    }
    compare = {
        "scope": "legacy v1.0 versus fresh two-source snapshot; database updates and source removal both contribute",
        "coverage": coverage,
        "detail_coverage": field_coverage,
        "list_matching": list_comparison,
        "identity_summary": summary(new),
        "changes": changes,
        "identity_failures": failures,
        "external": {
            "legacy_graph": len(old_external),
            "new_observed_ids": len(ext["records"]),
            "new_unique_records": len(new_external),
            "new_graph": len(selected),
            "lookup": ext["summary"],
            "field_coverage": external_fields,
            "graph_overlap": len(selected & set(old_external)),
            "new_graph_ids": sorted(selected - set(old_external)),
            "old_graph_not_selected": sorted(set(old_external) - selected),
        },
        "features": read(output / "05-feature-status.json"),
        "ai_identity_audit_executed": False,
        "replay": {"run_manifest": read(output / "run-manifest.json")},
    }
    save(destination / "comparison.json", compare)
    labels = {
        "identity": "OpenAlex 身份",
        "authors": "作者名单",
        "year": "年份",
        "venue": "发表情况",
        "abstract": "摘要",
        "citations": "被引数",
        "references_nonempty": "非空参考名单",
        "citing_list_received": "取得被引名单（含明确为空）",
    }
    text = [
        "# 两源重采集与旧版对照",
        "",
        "分母为同一主页快照的 %d 篇论文。旧版基于多源采用结果，新版仅采用主页和 OpenAlex。OpenAlex 实时更新也会造成差异，不能把全部增减归因于删去其他来源。"
        % len(new),
        "",
        "| 信息 | 旧版 | 新版 | 新增到位 | 失去到位 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for key, row in coverage.items():
        text.append(
            "| %s | %d | %d | %d | %d |"
            % (
                labels[key],
                row["legacy"],
                row["new"],
                len(row["gained"]),
                len(row["lost"]),
            )
        )
    text += ["", "| 名单详情匹配 | 旧版 | 新版 |", "| --- | ---: | ---: |"]
    for key, row in list_comparison.items():
        text.append(
            "| %s | %d / %d（%.2f%%） | %d / %d（%.2f%%） |"
            % (
                "引用文献" if key == "references" else "被引记录",
                row["legacy_matched_details"],
                row["legacy_ids"],
                row["legacy_rate"],
                row["new_matched_details"],
                row["new_ids"],
                row["new_rate"],
            )
        )
    text += [
        "",
        "这里的匹配率只针对 OpenAlex 已返回的名单 ID，不是对论文原始 PDF 的完整参考文献收集率。",
    ]
    text += [
        "",
        "## 逐步验收",
        "",
        "| 步骤／字段 | 成功 | 可解释未完成 | 成功率 | 归宿覆盖率 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    counts = (
        [("身份核对", summary(new))]
        + [
            (
                labels.get(
                    k,
                    {
                        "database_keywords": "数据库关键词",
                        "database_topics": "数据库主题",
                        "references": "引用名单查询",
                        "citing": "被引名单查询",
                    }.get(k, k),
                ),
                v,
            )
            for k, v in field_coverage.items()
        ]
        + [("外部详情", ext["summary"])]
    )
    for key, row in counts:
        text.append(
            "| %s | %d | %d | %.2f%% | %.2f%% |"
            % (
                key,
                row["success"],
                row["explained_failure"],
                row["success_rate"],
                row["accounted_rate"],
            )
        )
    policy = read(output / "protocol.json")["external"]
    text += [
        "",
        "空列表算查询完成，不代表内容到位；非空名单数量单独在上表汇报。每个外部ID都执行补全；网络候选只保留至少连接%d篇不同实验室论文的外部文献，再按连接数排序取最多%d篇。连接数依据完整直接引用／被引关系，在top-K与页面筛选之前计算；不会沿外部文献继续扩展。"
        % (policy.get("graph_min_lab_neighbors", 1), policy["graph_budget"]),
        "",
        "新版取得 %d 个不同外部记录，图节点选择 %d 个；旧图 %d 个，交集 %d 个。"
        % (
            len(new_external),
            len(selected),
            len(old_external),
            len(selected & set(old_external)),
        ),
        "",
        "## 身份未确定项",
        "",
        "仅列未完成项；成功项的逐篇详情保留在机器数据中。",
    ]
    for row in failures:
        text += [
            "",
            "### " + row["title"],
            "",
            "`" + row["id"] + "`：" + row["state"] + " — " + row["reason"],
            "",
            "实际查询：",
        ]
        for q in row["queries"]:
            text.append("- HTTP %s；%s；%s" % (q["http"], q["reason"], q["url"]))
        for candidate in row["best_candidates"]:
            m = candidate["metrics"]
            text.append(
                "- 候选：%s（%s）；标题 %.1f%%；作者交集 %d；拒绝：%s。"
                % (
                    candidate["title"],
                    candidate["id"],
                    m["title_similarity"] * 100,
                    len(m["author_overlap"]),
                    ",".join(m["reasons"]),
                )
            )
    text += [
        "",
        "## 范围与剩余产出",
        "",
        "身份与详情没有 AI 兜底，没有查询 Semantic Scholar、Crossref、Scholar 或论文发布页。人员名字与 OpenAlex 作者 ID 分开保存；无 ID 的署名只保持逐篇 occurrence，不按同名合并。人员分类需要带实验室证据的逐篇人员对应表，未确认项进入队列。",
        "",
        "关键词任务是新文本与固定词表的独立派生步骤，不属于事实补缺。任务准备、已生成、空标注与失败分别记状态，不将旧标注当成新结果。网页尚未接入新版；当前页面仍读取旧发布快照。",
        "",
    ]
    if (output / "automation-acceptance.json").exists():
        automation = read(output / "automation-acceptance.json")
        compare["automation"] = automation
        k = automation["derived"]["keywords"]
        people = automation["derived"]["persons"]
        profiles = automation["derived"]["profiles"]
        annotations = read(output / "05-keywords.json")["papers"]
        reasons = collections.Counter(p["reason"] for p in annotations)
        text += [
            "## 自动执行结果",
            "",
            "向量 %d/%d；关键词复用完成 %d/%d（%.1f%%），待标注 %d。"
            % (
                automation["vectors"]["ready"],
                automation["vectors"]["total"],
                k["success"],
                k["total"],
                k["success_rate"],
                k["states"].get("not_generated", 0),
            ),
            "",
            "关键词逐项结果："
            + "；".join(
                "%s：%d" % (reason, count) for reason, count in sorted(reasons.items())
            )
            + "。",
            "",
            "人员共 %d 条逐篇署名；明确人员对应 %d 条，待处理 %d 条。当前 %d 个临时人员键的画像均按实际依赖状态标记，不作为最终去重名单。"
            % (
                people["occurrences"],
                people["confirmed_occurrences"],
                people["pending_occurrences"],
                profiles["total"],
            ),
            "",
            "例行入口不请求AI模型。人员对应和剩余关键词有独立任务队列；带规则、代码、原始输入及响应指纹的候选结果通过校验后独立冻结。网络与检索页面仍使用旧发布快照。",
            "",
        ]
        save(destination / "comparison.json", compare)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "report.md").write_bytes("\n".join(text).encode("utf-8"))
    print("Comparison:", json_dump(coverage), flush=True)


def json_dump(value):
    import json

    return json.dumps(
        {k: {"legacy": r["legacy"], "new": r["new"]} for k, r in value.items()},
        ensure_ascii=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--destination", default="data/two-source/results")
    args = parser.parse_args()
    run(ROOT / args.output, ROOT / args.destination)
