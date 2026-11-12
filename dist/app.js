'use strict';
(() => {
  const chapters = [...document.querySelectorAll('.chapter')];
  const nav = [...document.querySelectorAll('[data-chapter]')];
  const previous = document.getElementById('previous');
  const next = document.getElementById('next');
  const reading = document.getElementById('reading');
  const menu = document.getElementById('chapter-nav');
  const toggle = document.getElementById('menu-toggle');
  let current = 0;
  function render(index, scroll = false) {
    current = Math.max(0, Math.min(chapters.length - 1, index));
    chapters.forEach((section, i) => { section.hidden = i !== current; });
    nav.forEach((link, i) => {
      if (i === current) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    previous.disabled = current === 0;
    next.disabled = current === chapters.length - 1;
    document.getElementById('current-chapter').textContent = current === chapters.length - 1 ? 'GLOSSARY & SELF CHECK' : `CHAPTER ${String(current + 1).padStart(2, '0')}`;
    document.getElementById('reading-progress').textContent = `${current + 1} / ${chapters.length}`;
    document.getElementById('page-title').textContent = chapters[current].dataset.title;
    document.getElementById('progress-fill').style.width = `${100 * (current + 1) / chapters.length}%`;
    try { localStorage.setItem('ads-data-reader-chapter', String(current)); } catch (_) { /* Reading works without storage. */ }
    menu.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    if (scroll) { reading.focus({preventScroll: true}); reading.scrollIntoView({block: 'start'}); }
  }
  function fromHash(scroll = false) {
    const id = decodeURIComponent(location.hash.slice(1));
    const target = document.getElementById(id);
    const parent = target?.closest('.chapter');
    if (parent) { render(chapters.indexOf(parent), scroll); return true; }
    return false;
  }
  document.body.classList.add('enhanced');
  let saved = 0;
  try { saved = Number(localStorage.getItem('ads-data-reader-chapter')) || 0; } catch (_) {}
  if (!fromHash()) render(Number.isInteger(saved) ? saved : 0);
  window.addEventListener('hashchange', () => fromHash(true));
  document.querySelectorAll('a[href^="#"]').forEach(link => link.addEventListener('click', () => {
    if (link.hash === location.hash) fromHash(true);
  }));
  previous.addEventListener('click', () => { if (current > 0) location.hash = chapters[current - 1].id; });
  next.addEventListener('click', () => { if (current < chapters.length - 1) location.hash = chapters[current + 1].id; });
  toggle.addEventListener('click', () => { const open = menu.classList.toggle('open'); toggle.setAttribute('aria-expanded', String(open)); });
  document.getElementById('print-guide').addEventListener('click', () => window.print());
  const terms = [...document.querySelectorAll('.term')];
  const search = document.getElementById('glossary-search');
  function filterTerms() {
    const query = search.value.trim().toLowerCase();
    let count = 0;
    terms.forEach(term => { term.hidden = !term.textContent.toLowerCase().includes(query); if (!term.hidden) count++; });
    document.getElementById('term-count').textContent = `${count} of ${terms.length} definitions`;
  }
  search.addEventListener('input', filterTerms); filterTerms();
  const outcome = document.getElementById('outcome');
  const representation = document.getElementById('representation');
  const metadata = {impression_id:'imp_101', request_id:'req_10', prediction_time:'2026-11-01T09:59:58Z', shown_at:'2026-11-01T10:00:00Z', label_finalized_at:'2026-11-01T10:35:00Z'};
  const features = {user_id:'U7', candidate_item_id:'A42', candidate_category:'shoes', candidate_price:80, device:'mobile', surface:'home_feed', hour_utc:9, recent_history:[{item_id:'A12',category:'shoes'},{item_id:'A18',category:'shoes'},{item_id:'A33',category:'books'}]};
  function inspect() {
    const pending = outcome.value === 'pending';
    const y = pending ? null : outcome.value === 'clicked' ? 1 : 0;
    let result;
    if (representation.value === 'raw') result = {...metadata, user_id:'U7', item_id:'A42', device:'mobile', surface:'home_feed', note:'The response is logged separately; it is never an impression input.'};
    else if (representation.value === 'record') result = {metadata, features, labels:{clicked:y}, label_status:pending?'pending':'final', sample_weight:1};
    else result = {x:{user_id:[7],candidate_item_id:[42],candidate_category:[2],device:[2],surface:[2],dense:[[0.8,9/23]],history_item_ids:[[12,18,33,0,0]],history_category_ids:[[2,2,3,0,0]],history_mask:[[true,true,true,false,false]]},y:pending?null:[[y]],weight:[[1]],eligible_for_final_click_training:!pending};
    document.getElementById('inspector-output').textContent = JSON.stringify(result,null,2);
    document.getElementById('inspector-note').textContent = pending ? 'Pending is not zero. Hold this example out of finalized click training until its window closes.' : `Final click label: ${y}. Changing the outcome does not change any prediction-time feature.`;
  }
  outcome.addEventListener('change', inspect); representation.addEventListener('change', inspect); inspect();
})();
