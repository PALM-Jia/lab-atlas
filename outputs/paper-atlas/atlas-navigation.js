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
  document.getElementById('info-content').innerHTML = `<p>基础论文事实、人员归属与引用关系来自实验室主页原始 HTML 快照、用户确认的实验室人员名单和 OpenAlex 数据库。主页原始字段持续保留。</p><p>论文关键词由标题和可用摘要在版本化的受控关键词词表内标注，每项均附连续原文证据；研究领域用于筛选和染色。内容相似度使用固定版本的本地 SPECTER2 语义向量。</p><p>外部文献来自实验室论文的一层引用与被引邻域。完整外部记录保留在数据层，网络节点仅纳入与至少两篇不同实验室论文存在直接关系的外部作品，外部文献之间不绘制引用边。</p><p><a href="retrieval.html">查看字段来源与采集情况 ↗</a></p>`;
  about.onclick = () => info.showModal();
  document.getElementById('close-info').onclick = () => info.close();
})();
