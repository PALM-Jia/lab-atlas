"""Concise display wording; keep original audit evidence unchanged."""
REPLACEMENTS = {
    '本轮核查来源与历史请求': '来源与请求记录',
    '本轮主页/公开页核查': '主页与论文页',
    '以下逐篇列出发表状态、当前关键词缺口及补采来源。': '',
    '成功项只作汇总。': '',
    '缺关键词首先是尚无可确认的公开论文身份和文本，而非 ICLR 早年无 DOI。': '缺公开论文身份与正文。',
    '尚无两题版本对应证据，不能直接把候选关键词归给原条目。': '缺两题的版本对应证据。',
    '新候选确实刚公开，但原条目身份仍不能凭相似题名归并。': '',
    '暂可用标题提取关键词，标注“标题提取”；不能当作论文作者关键词或 OpenAlex keywords。': '从标题提取关键词，来源标为“标题提取”。',
    '本轮网页检索工具无法访问该结构化 API URL，未取得响应正文；不归因为 HTTP 403。': '网页检索工具拒绝访问该 API URL，未取得 HTTP 响应。',
    '个人主页原题确实写 Hyerspectral，不是采集时误写；': '个人主页拼写为 Hyerspectral；',
    '拼写错误可能影响检索，但不能作为唯一缺失原因。': '',
    '尚不能确认同一版本': '缺版本对应证据',
    '自动主题、姓名候选和内容相似均标为候选。': '',
    '路径核算 100% 表示知道在哪一步失败；合理性判断按逐项证据单独列出。': '失败项列出请求路径、判断依据与补采方案。',
    '布局基于引用和共同参考文献，颜色仍为关键词主题。静态网页在打开时不请求 API。': '',
}


def clean_public_copy(text):
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


if __name__ == '__main__':
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent / 'outputs/paper-atlas'
    for name in ('keyword-missing.html', 'acceptance-report.html'):
        path = root / name
        path.write_text(clean_public_copy(path.read_text(encoding='utf-8')), encoding='utf-8')
