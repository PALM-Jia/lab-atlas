"""Refresh retrieval descriptions without changing collected data or evidence."""

import copy
import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "data" / "atlas"
METHOD = (
    "DeepSeek V4.1 Flash 标注，GPT-6.1 Sol 复核；按标题及可用摘要从 49 个关键词中标注。"
)


def evidence_only(value):
    """Omit only editorial keys when checking that source evidence is intact."""
    editorial = {"explanation", "identityLabel", "keywordSource", "keywordMethod"}
    if isinstance(value, dict):
        return {k: evidence_only(v) for k, v in value.items() if k not in editorial}
    if isinstance(value, list):
        return [evidence_only(v) for v in value]
    return value


def refresh(dashboard):
    before = evidence_only(copy.deepcopy(dashboard))
    for paper in dashboard["papers"] + dashboard.get("external", []):
        fields = paper["fields"]
        for key in ("title", "year", "abstract"):
            if (
                fields[key].get("explanation")
                == "列出已保存来源的值；大小写和标点差异归并。"
            ):
                fields[key][
                    "explanation"
                ] = "各来源的值并列展示；大小写和标点差异已合并。"
        if (
            fields["authors"]
            .get("explanation", "")
            .startswith("同篇论文内归并姓名顺序")
        ):
            fields["authors"][
                "explanation"
            ] = "已核对的姓名写法合并；各来源的作者名单和署名顺序保留。"
        venue = fields["venue"]
        if venue.get("explanation", "").startswith("会刊简称与全称按别名表归一"):
            venue["explanation"] = (
                "会刊简称与全称合并，原名保留在来源中；不同发表版本分别展示。"
            )
        for key in ("venue", "abstract"):
            if fields[key].get("explanation") == "现有记录没有该字段的可用值。":
                fields[key]["explanation"] = "来源记录中无可用值。"
        references = fields["references"]
        if re.fullmatch(
            r"\d+ 个参考文献 ID；\d+ 条已取得标题，\d+ 条缺标题等详情。",
            references.get("explanation", ""),
        ):
            references["explanation"] = (
                "OpenAlex 参考名单；未取得标题的文献保留数据库标识。"
            )
        citing = fields["citing"]
        if re.fullmatch(
            r"OpenAlex 报告 \d+ 篇施引文献；已收集 \d+ 个标识符，当前汇总已匹配详情 \d+ 篇。",
            citing.get("explanation", ""),
        ):
            citing["explanation"] = (
                "OpenAlex 施引查询报告为 0 篇。"
                if citing.get("total") == 0
                else "OpenAlex 施引查询名单，按数据库标识匹配文献详情。"
            )
        keywords = fields["keywords"]
        old = keywords.get("explanation", "")
        if keywords["state"] == "excluded":
            # Keep the complete original exclusion reason, including exact quotes.
            reason = old.split("标注未采用：", 1)[-1]
            keywords["explanation"] = "标注未采用：" + reason
        else:
            keywords["explanation"] = METHOD
        topics = fields["topics"]
        topics["explanation"] = "OpenAlex 提供的研究主题及相关度。"
        vector = fields["vector"]
        if (
            vector.get("state") == "ready"
            and vector.get("model") == "specter2_proximity"
        ):
            uses_abstract = "abstract" in vector.get("input", {}).get("fields", [])
            vector["explanation"] = "本地 SPECTER2 输入：" + (
                "标题＋摘要。" if uses_abstract else "仅标题。"
            )
            if vector.get("input", {}).get("truncated"):
                vector["explanation"] += "超过模型长度的部分已截断。"
        identity = fields["identity"]
        identity["explanation"] = {
            "至少一个数据库记录已通过身份校验。": "已核对并匹配数据库记录。",
            "尚无已校验的 OpenAlex 或 Semantic Scholar 记录。": "未匹配到已核对的 OpenAlex 或 Semantic Scholar 记录。",
            "论文版本或候选身份尚未确认。": "论文版本或记录归属待核对。",
        }.get(identity.get("explanation"), identity.get("explanation", ""))
    for author in dashboard["authors"]:
        author["identityLabel"] = {
            "按署名归一": "按论文署名合并",
            "中文姓名尚未对应署名": "中文姓名未对应到论文署名",
            "尚未关联论文": "未关联论文",
            "同名身份待确认": "同名身份待核对",
        }.get(author["identityLabel"], author["identityLabel"])
        if "keywordSource" in author:
            author["keywordSource"] = "标题/摘要标注 · 按作者汇总"
    dashboard["meta"]["keywordMethod"] = METHOD
    assert evidence_only(dashboard) == before, "Collected evidence changed"
    return dashboard


if __name__ == "__main__":
    path = OUT / "retrieval-data.json"
    dashboard = refresh(json.loads(path.read_text(encoding="utf-8")))
    payload = json.dumps(dashboard, ensure_ascii=False, separators=(",", ":"))
    path.write_text(payload + "\n", encoding="utf-8")
    print("Retrieval descriptions refreshed; source evidence unchanged.")
