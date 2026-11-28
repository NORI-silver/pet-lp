(function () {
  'use strict';
  const kinds = {
    trial: ['初回から実技', '体験の申込先へ'],
    practice: ['単発レッスン', 'レッスンの申込先へ'],
    counsel: ['初回は相談', '初回相談の申込先へ'],
    daycare: ['まず体験入園', '体験入園の申込先へ'],
    check: ['受け入れ・料金は要確認', '事業者に確認する']
  };
  function select(rows, req) {
    if (!req.city) return [];
    return rows.filter(m => (!req.mode || m.mode === req.mode)
      && (m.mode === 'visit' ? (m.area || []).includes(req.city) : m.city === req.city)
      && !(req.age !== '' && req.age != null && ((m.minAge != null && Number(req.age) < m.minAge)
        || (m.maxAge != null && Number(req.age) >= m.maxAge)))
      && !(req.weight !== '' && req.weight != null && m.maxWeight != null && Number(req.weight) > m.maxWeight))
      .map(m => {
        const topic = req.issue && req.issue !== 'other' && (m.topics || []).includes(req.issue);
        const unknown = [];
        if (req.issue && !topic) unknown.push('選んだ困りごとに対応するか');
        if (req.issue === 'bite') unknown.push('噛みつきの状況と受け入れ可否');
        if (req.age === '' && (m.minAge != null || m.maxAge != null)) unknown.push('対象月齢');
        if (Number(req.weight) >= 25 && m.large !== true && m.maxWeight == null) unknown.push('大型犬の受け入れ');
        if (req.breed && m.breedOpen !== true) unknown.push('犬種ごとの受け入れ条件');
        if (m.kind === 'check') unknown.push('初回の利用条件');
        if (m.checkAvailability) unknown.push('現在の初回受付');
        return {m, topic, unknown, score: (topic ? 4 : 0) + (m.kind === 'check' ? 0 : 2) + (m.priceType === 'known' ? 1 : 0)};
      }).sort((a,b) => b.score - a.score);
  }
  if (typeof module !== 'undefined') module.exports = {select};
  if (typeof document === 'undefined') return;
  const panel = document.querySelector('#first-lesson');
  if (!panel) return;
  const rows = window.trainerFirstLessonMenus;
  if (!Array.isArray(rows)) { panel.querySelector('.tc-status').textContent = '比較を読み込めませんでした。下の一覧をご覧ください。'; return; }
  const form = panel.querySelector('form'), status = panel.querySelector('.tc-status'), results = panel.querySelector('.tc-results');
  const el = (tag, klass, value) => {const e = document.createElement(tag); if (klass) e.className = klass; if (value) e.textContent = value; return e;};
  const link = (url, label, klass) => {const a = el('a', klass, label); a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a;};
  const formats = {visit:'出張', school:'来所', day:'預かり'};
  function card({m, topic, unknown}) {
    const item = el('article', 'tc-menu');
    const [kind, action] = kinds[m.kind];
    item.append(el('span','tc-kind',kind), el('h3','',m.name + '｜' + m.menu),
      el('p','tc-note', formats[m.mode] + '・' + (m.mode === 'visit' ? '選んだ市区町村へ出張' : m.city) + (topic ? '・選んだ困りごとの案内あり' : '')),
      el('p','tc-price',(m.priceType === 'base' ? '初回の掲載料金：' : '') + m.price), el('p','tc-note',m.feeNote), el('p','',m.first));
    if (unknown.length) item.append(el('p','tc-note','事前に確認：' + unknown.join('、')));
    const detail = el('details');
    detail.append(el('summary','', '申込みに必要なこと・支払い'),el('p','',m.needs),el('p','tc-note',m.payment));
    const source = el('p','tc-source','掲載情報：' + m.checked + ' ');
    source.append(link(m.source,'料金・条件の出典'));
    detail.append(source);
    item.append(detail,link(m.contact,unknown.length ? '事業者に条件を確認する ↗' : action + ' ↗','tc-cta'));
    return item;
  }
  form.addEventListener('input', () => { status.textContent = ''; results.replaceChildren(); });
  form.addEventListener('submit', e => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    const req = Object.fromEntries(new FormData(form));
    const matches = select(rows, req);
    status.textContent = matches.length ? '比較できる初回メニュー：' + matches.length + '件'
      : 'この条件の初回メニューはまだ掲載していません。受け入れ不可という意味ではありません。下の事業者一覧もご覧ください。';
    results.replaceChildren(...matches.map(card));
    status.focus();
  });
  form.querySelector('button[type=submit]').disabled = false;
})();
