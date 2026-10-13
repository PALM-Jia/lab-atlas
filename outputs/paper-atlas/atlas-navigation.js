/* Shared navigation data explanation on all Atlas pages. */
(() => {
  const about = document.getElementById('about');
  if (!about) return;
  let info = document.getElementById('info');
  if (!info) {
    info = document.createElement('dialog');
    info.id = 'info';
    info.innerHTML = '<button id="close-info" class="quiet" type="button">关闭 ×</button><h2 id="info-title">数据来源与覆盖范围</h2><div id="info-content"></div>';
    document.body.append(info);
  }
  info.setAttribute('aria-label', '数据来源与覆盖范围');
  document.getElementById('info-content').innerHTML = `<p>论文信息以 OpenAlex 为主，Semantic Scholar 和原始发布页补充。</p><p>关键词由标题和可用摘要标注；研究领域用于筛选和染色。内容相似度使用本地 SPECTER2 向量。</p><p>外部文献来自实验室论文的引用与被引邻域，外部文献之间不绘制引用边。</p><p><a href="retrieval.html">查看字段来源与采集情况 ↗</a></p>`;
  about.onclick = () => info.showModal();
  document.getElementById('close-info').onclick = () => info.close();
})();
