(() => {
  'use strict';

  const root = document.getElementById('prospero-great-library');
  if (!root) return;
  const $ = (id) => document.getElementById(id);
  const CATEGORY_ORDER = ['book', 'comic', 'movie', 'drama', 'anime', 'game', 'music'];
  const DEFAULT_STATUSES = new Set(['in_progress', 'completed']);
  const OTHER_STATUSES = new Set(['on_hold', 'dropped']);
  const PAGE_SIZE = Math.max(1, Number(root.dataset.pageSize || 24));

  const rootView = $('pgl-root-view');
  const browserView = $('pgl-browser-view');
  const cardView = $('pgl-card-view');
  const wishlistLedger = $('pgl-wishlist-ledger');
  const grid = $('pgl-grid');
  const pagination = $('pgl-pagination');
  const browserTitle = $('pgl-browser-title');
  const resultCount = $('pgl-result-count');
  const search = $('pgl-search');
  const searchToggle = $('pgl-search-toggle');
  const sort = $('pgl-sort');
  const source = $('pgl-source');
  const year = $('pgl-year');
  const clearFilters = $('pgl-clear-filters');
  const layoutGrid = $('pgl-layout-grid');
  const layoutList = $('pgl-layout-list');
  const back = $('pgl-back');
  const drawerEnabled = root.dataset.drawerEnabled !== 'false';
  const showSteamPlaytime = root.dataset.showSteamPlaytime !== 'false';
  const showAchievements = root.dataset.showAchievements !== 'false';

  let items = [];
  let stats = {};
  let itemById = new Map();
  let searchTimer = null;
  let previousNonSearchState = null;

  const normalizeText = (value) => String(value ?? '').normalize('NFKC').toLocaleLowerCase();
  const safeUrl = (value) => {
    if (!value) return null;
    try {
      const url = new URL(String(value), location.href);
      return ['http:', 'https:'].includes(url.protocol) ? url.href : null;
    } catch {
      return null;
    }
  };
  const clamp = (value, low, high) => Math.min(high, Math.max(low, Number(value) || 0));
  const toPascal = (value) => String(value || '').split(/[_-]/).filter(Boolean).map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join('');
  const categoryLabel = (category) => root.dataset[`category${toPascal(category)}`] || category || '';
  const statusLabel = (status) => root.dataset[`status${toPascal(status)}`] || status || '';
  const formatRating = (value) => {
    const n = Number(value);
    if (!Number.isFinite(n)) return '';
    return Number.isInteger(n) ? String(n) : n.toFixed(1);
  };
  const formatHours = (minutes) => {
    const hours = (Number(minutes) || 0) / 60;
    return hours >= 100 ? String(Math.round(hours)) : hours.toFixed(1);
  };
  function make(tag, className = '', text = null) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== null && text !== undefined) node.textContent = String(text);
    return node;
  }

  function cloneState(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function defaultState() {
    return { view: 'index', category: null, status: null, q: '', page: 1, sort: 'updated', source: '', year: '' };
  }

  function parseState() {
    const params = new URLSearchParams(location.search);
    const next = defaultState();
    const legacyType = params.get('type');
    const category = params.get('category') || legacyType;
    const rawView = params.get('view');

    // alpha.3 used view=grid|list. Preserve it as a local preference while the
    // new router reserves `view` for semantic Library views.
    if (rawView === 'grid' || rawView === 'list') {
      try { localStorage.setItem('pgl.layout', rawView); } catch { /* ignore */ }
    }

    next.q = (params.get('q') || '').trim();
    next.category = CATEGORY_ORDER.includes(category) ? category : null;
    next.status = OTHER_STATUSES.has(params.get('status')) ? params.get('status') : null;
    next.page = Math.max(1, Number.parseInt(params.get('page') || '1', 10) || 1);
    next.sort = ['updated', 'rating', 'year', 'playtime', 'title'].includes(params.get('sort')) ? params.get('sort') : 'updated';
    next.source = ['bangumi', 'neodb', 'steam'].includes(params.get('source')) ? params.get('source') : '';
    next.year = params.get('year') || '';

    if (next.q) { next.view = 'search'; next.category = null; next.status = null; }
    else if (rawView === 'wishlist') next.view = 'wishlist';
    else if (next.category) next.view = next.status ? 'other' : 'category';
    return next;
  }

  let state = parseState();

  function stateUrl(next) {
    const params = new URLSearchParams();
    if (next.view === 'wishlist') params.set('view', 'wishlist');
    if (next.category) params.set('category', next.category);
    if (next.view === 'other' && next.status) params.set('status', next.status);
    if (next.view === 'search' && next.q) params.set('q', next.q);
    if (next.page > 1) params.set('page', String(next.page));
    if (next.sort && next.sort !== 'updated') params.set('sort', next.sort);
    if (next.source) params.set('source', next.source);
    if (next.year) params.set('year', next.year);
    const query = params.toString();
    return `${location.pathname}${query ? `?${query}` : ''}${location.hash}`;
  }

  function writeHistory(next, { replace = false } = {}) {
    const method = replace ? 'replaceState' : 'pushState';
    if (history[method]) history[method]({ pgl: true }, '', stateUrl(next));
  }

  function navigate(next, options = {}) {
    if (state.view !== 'search' && next.view === 'search') previousNonSearchState = cloneState(state);
    state = { ...defaultState(), ...next };
    state.page = Math.max(1, Number(state.page) || 1);
    writeHistory(state, options);
    render();
  }

  function itemSources(item) { return Object.keys(item.sources || {}); }

  function itemSearchText(item) {
    return normalizeText([
      item.title,
      item.title_original,
      ...(item.alternate_titles || []),
      ...(item.tags || []),
      item.year,
      categoryLabel(item.category),
      ...itemSources(item),
    ].filter(Boolean).join(' '));
  }

  function steam(item) { return item.telemetry?.steam || {}; }
  function recentMinutes(item) { return Number(steam(item).recent_playtime_minutes || steam(item).playtime_2weeks_minutes || 0); }

  function itemSortValue(item, key) {
    if (key === 'rating') return Number(item.rating?.normalized_10 || -1);
    if (key === 'playtime') return Number(steam(item).playtime_minutes || 0);
    if (key === 'year') return Number(item.year || 0);
    if (key === 'title') return normalizeText(item.title);
    return item.timestamps?.canonical_updated_at || item.release_date || '';
  }

  function compareByKey(a, b, key) {
    const av = itemSortValue(a, key);
    const bv = itemSortValue(b, key);
    if (key === 'rating' || key === 'playtime' || key === 'year') return bv - av;
    if (key === 'title') return String(av).localeCompare(String(bv));
    return String(bv).localeCompare(String(av));
  }

  function stableTie(a, b) {
    return normalizeText(a.title).localeCompare(normalizeText(b.title)) || String(a.id || '').localeCompare(String(b.id || ''));
  }

  function sortCategoryItems(input) {
    return [...input].sort((a, b) => {
      // The locked display contract always keeps in_progress above completed,
      // regardless of the secondary sort selected by the visitor.
      if (!state.status && state.view === 'category') {
        const ar = a.status === 'in_progress' ? 0 : 1;
        const br = b.status === 'in_progress' ? 0 : 1;
        if (ar !== br) return ar - br;
      }
      return compareByKey(a, b, state.sort) || stableTie(a, b);
    });
  }

  function filterAdvanced(input) {
    return input.filter((item) => {
      if (state.source && !itemSources(item).includes(state.source)) return false;
      if (state.year && String(item.year || '') !== state.year) return false;
      return true;
    });
  }

  function selectedItems() {
    if (state.view === 'category') {
      return sortCategoryItems(filterAdvanced(items.filter((item) => item.category === state.category && DEFAULT_STATUSES.has(item.status))));
    }
    if (state.view === 'wishlist' && state.category) {
      return sortCategoryItems(filterAdvanced(items.filter((item) => item.category === state.category && item.status === 'wishlist')));
    }
    if (state.view === 'other' && state.category && state.status) {
      return sortCategoryItems(filterAdvanced(items.filter((item) => item.category === state.category && item.status === state.status)));
    }
    if (state.view === 'search') {
      const q = normalizeText(state.q);
      const matched = filterAdvanced(items.filter((item) => itemSearchText(item).includes(q)));
      return [...matched].sort((a, b) => {
        const ac = CATEGORY_ORDER.indexOf(a.category);
        const bc = CATEGORY_ORDER.indexOf(b.category);
        if (ac !== bc) return ac - bc;
        return compareByKey(a, b, state.sort) || stableTie(a, b);
      });
    }
    return [];
  }

  function currentLayout() {
    try {
      const saved = localStorage.getItem('pgl.layout');
      if (saved === 'grid' || saved === 'list') return saved;
    } catch { /* ignore */ }
    return grid?.classList.contains('is-list') ? 'list' : 'grid';
  }

  function setLayout(layout) {
    if (!grid) return;
    grid.classList.toggle('is-list', layout === 'list');
    layoutGrid?.classList.toggle('is-active', layout === 'grid');
    layoutList?.classList.toggle('is-active', layout === 'list');
    layoutGrid?.setAttribute('aria-pressed', String(layout === 'grid'));
    layoutList?.setAttribute('aria-pressed', String(layout === 'list'));
    try { localStorage.setItem('pgl.layout', layout); } catch { /* ignore */ }
  }

  function buildCard(item) {
    const card = make('article', 'pgl-card');
    card.dataset.pglId = item.id || '';
    card.dataset.category = item.category || '';
    card.dataset.status = item.status || '';
    if (drawerEnabled) {
      card.tabIndex = 0;
      card.setAttribute('role', 'button');
      card.setAttribute('aria-haspopup', 'dialog');
    }

    const coverWrap = make('div', 'pgl-cover-wrap');
    const coverUrl = safeUrl(item.cover?.url);
    if (coverUrl) {
      const image = make('img', 'pgl-cover');
      image.src = coverUrl;
      image.alt = item.title || '';
      image.loading = 'lazy'; image.decoding = 'async'; image.referrerPolicy = 'no-referrer';
      coverWrap.append(image);
    } else {
      const placeholder = make('div', 'pgl-cover pgl-cover-placeholder', 'PGL');
      placeholder.setAttribute('aria-hidden', 'true');
      coverWrap.append(placeholder);
    }

    const body = make('div', 'pgl-card-body');
    const kickers = make('div', 'pgl-card-kickers');
    if ((item.tags || []).includes('performance')) kickers.append(make('span', 'pgl-badge', root.dataset.performance || 'Performance'));
    const showStatus = item.status === 'in_progress' || state.view === 'other' || state.view === 'search';
    if (showStatus && item.status && item.status !== 'completed') kickers.append(make('span', `pgl-status${item.status === 'in_progress' ? ' pgl-status-active' : ''}`, statusLabel(item.status)));
    if (kickers.childNodes.length) body.append(kickers);
    body.append(make('h3', 'pgl-card-title', item.title || ''));

    const meta = make('div', 'pgl-meta');
    if (item.year) meta.append(make('span', '', item.year));
    if (item.rating) meta.append(make('span', '', `★ ${formatRating(item.rating.normalized_10)}`));
    const playtime = steam(item).playtime_minutes;
    if (showSteamPlaytime && item.category === 'game' && playtime) meta.append(make('span', '', `Steam ${formatHours(playtime)}h`));
    if (meta.childNodes.length) body.append(meta);

    if (item.progress && item.progress.current !== null && item.progress.current !== undefined) {
      const progress = make('div', 'pgl-progress');
      progress.title = `${item.progress.current} / ${item.progress.total ?? '?'}`;
      const bar = make('span'); bar.style.width = `${clamp(item.progress.percent, 0, 100)}%`; progress.append(bar); body.append(progress);
    }
    card.append(coverWrap, body);
    return card;
  }

  function makeGroupHeading(category, count) {
    const heading = make('div', 'pgl-search-group-heading');
    heading.append(make('strong', '', categoryLabel(category)), make('span', '', `${count} ${root.dataset.items || 'items'}`));
    return heading;
  }

  function renderCards(allSelected) {
    if (!grid) return;
    const totalPages = Math.max(1, Math.ceil(allSelected.length / PAGE_SIZE));
    if (state.page > totalPages) state.page = totalPages;
    const start = (state.page - 1) * PAGE_SIZE;
    const pageItems = allSelected.slice(start, start + PAGE_SIZE);
    const fragment = document.createDocumentFragment();

    if (state.view === 'search') {
      let lastCategory = null;
      for (const item of pageItems) {
        if (item.category !== lastCategory) {
          const count = allSelected.filter((candidate) => candidate.category === item.category).length;
          fragment.append(makeGroupHeading(item.category, count));
          lastCategory = item.category;
        }
        fragment.append(buildCard(item));
      }
    } else {
      let insertedCompletedDivider = false;
      const hasInProgress = state.view === 'category' && allSelected.some((candidate) => candidate.status === 'in_progress');
      if (hasInProgress && state.page === 1 && pageItems[0]?.status === 'in_progress') {
        fragment.append(make('div', 'pgl-status-divider pgl-status-divider-active', root.dataset.inProgressSection || 'In progress'));
      }
      for (const item of pageItems) {
        if (state.view === 'category' && item.status === 'completed' && !insertedCompletedDivider && hasInProgress) {
          const divider = make('div', 'pgl-status-divider', root.dataset.completedSection || 'Completed');
          fragment.append(divider);
          insertedCompletedDivider = true;
        }
        fragment.append(buildCard(item));
      }
    }
    if (!pageItems.length) fragment.append(make('p', 'pgl-empty', state.view === 'search' ? (root.dataset.searchEmpty || 'No matching items') : (root.dataset.noItems || 'No records')));
    grid.replaceChildren(fragment);
    if (resultCount) resultCount.textContent = `${allSelected.length} ${root.dataset.items || 'items'}`;
    renderPagination(allSelected.length);
  }

  function pageTokens(current, total) {
    const keep = new Set([1, total]);
    for (let i = current - 2; i <= current + 2; i += 1) if (i >= 1 && i <= total) keep.add(i);
    const sorted = [...keep].sort((a, b) => a - b);
    const tokens = [];
    sorted.forEach((value, index) => {
      if (index && value - sorted[index - 1] > 1) tokens.push('…');
      tokens.push(value);
    });
    return tokens;
  }

  function renderPagination(total) {
    if (!pagination) return;
    const pages = Math.ceil(total / PAGE_SIZE);
    if (pages <= 1) { pagination.hidden = true; pagination.replaceChildren(); return; }
    pagination.hidden = false;
    const fragment = document.createDocumentFragment();
    const prev = make('button', 'pgl-page-nav', '‹'); prev.disabled = state.page <= 1; prev.setAttribute('aria-label', root.dataset.previousPage || 'Previous page'); prev.dataset.page = String(state.page - 1); fragment.append(prev);
    for (const token of pageTokens(state.page, pages)) {
      if (token === '…') { fragment.append(make('span', 'pgl-page-ellipsis', '…')); continue; }
      const button = make('button', 'pgl-page-number', token); button.dataset.page = String(token);
      if (token === state.page) { button.classList.add('is-active'); button.setAttribute('aria-current', 'page'); }
      fragment.append(button);
    }
    const next = make('button', 'pgl-page-nav', '›'); next.disabled = state.page >= pages; next.setAttribute('aria-label', root.dataset.nextPage || 'Next page'); next.dataset.page = String(state.page + 1); fragment.append(next);
    pagination.replaceChildren(fragment);
  }

  function buildWishlistLedger() {
    if (!wishlistLedger) return;
    const counts = stats.navigation?.wishlist_by_category || {};
    const nav = make('nav', 'pgl-category-ledger'); nav.setAttribute('aria-label', root.dataset.wishlist || 'Wishlist');
    for (const category of CATEGORY_ORDER) {
      const count = Number(counts[category] || 0);
      const link = make('a', 'pgl-category-ledger-item');
      link.href = stateUrl({ ...defaultState(), view: 'wishlist', category });
      link.dataset.pglWishlistCategory = category;
      const primary = make('span', 'pgl-ledger-primary'); primary.append(make('span', 'pgl-ledger-icon', '›'), make('strong', '', categoryLabel(category)));
      link.append(primary, make('span', 'pgl-ledger-count', `${count} ${root.dataset.items || 'items'}`)); nav.append(link);
    }
    wishlistLedger.replaceChildren(nav);
  }

  function updateToolbar() {
    if (sort) sort.value = state.sort;
    if (source) source.value = state.source;
    if (year) year.value = state.year;
    const playtimeOption = sort?.querySelector('option[value="playtime"]');
    if (playtimeOption) playtimeOption.disabled = Boolean(state.category && state.category !== 'game');
    if (playtimeOption?.disabled && state.sort === 'playtime') { state.sort = 'updated'; sort.value = 'updated'; }
    document.querySelectorAll('[data-pgl-status]').forEach((button) => { button.disabled = !state.category; });
  }

  function renderBrowserHeading() {
    if (!browserTitle) return;
    if (state.view === 'search') browserTitle.textContent = root.dataset.searchResults || 'Search results';
    else if (state.view === 'wishlist') browserTitle.textContent = state.category ? `${root.dataset.wishlist || 'Wishlist'} · ${categoryLabel(state.category)}` : (root.dataset.wishlist || 'Wishlist');
    else if (state.view === 'other') browserTitle.textContent = `${categoryLabel(state.category)} · ${statusLabel(state.status)}`;
    else browserTitle.textContent = categoryLabel(state.category);
  }

  function render() {
    const atRoot = state.view === 'index';
    if (rootView) rootView.hidden = !atRoot;
    if (browserView) browserView.hidden = atRoot;
    if (search) search.value = state.view === 'search' ? state.q : '';
    root.classList.toggle('is-searching', state.view === 'search');
    if (atRoot) return;

    renderBrowserHeading();
    const wishlistIndex = state.view === 'wishlist' && !state.category;
    if (wishlistLedger) wishlistLedger.hidden = !wishlistIndex;
    if (cardView) cardView.hidden = wishlistIndex;
    if (wishlistIndex) {
      buildWishlistLedger();
      if (resultCount) resultCount.textContent = `${stats.navigation?.wishlist_total || 0} ${root.dataset.items || 'items'}`;
      return;
    }
    updateToolbar();
    renderCards(selectedItems());
    setLayout(currentLayout());
  }

  function populateYears() {
    if (!year) return;
    const selected = state.year;
    const first = year.options[0];
    year.replaceChildren(first);
    [...new Set(items.map((item) => item.year).filter(Boolean).map(String))].sort((a, b) => Number(b) - Number(a)).forEach((value) => year.add(new Option(value, value)));
    if ([...year.options].some((option) => option.value === selected)) year.value = selected;
  }

  function loadJson(url) {
    return fetch(url, { credentials: 'same-origin' }).then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    });
  }

  // Drawer ------------------------------------------------------------------
  const dialog = $('pgl-drawer');
  const dialogContent = $('pgl-drawer-content');
  let lastFocused = null;

  function appendSafeLink(container, label, rawUrl, className = '', external = true) {
    const url = safeUrl(rawUrl); if (!url) return;
    const link = make('a', className, label); link.href = url;
    if (external) { link.target = '_blank'; link.rel = 'noopener noreferrer'; }
    container.append(link);
  }

  function openItem(item) {
    if (!drawerEnabled || !dialog || !dialogContent || !item) return;
    lastFocused = document.activeElement; dialogContent.replaceChildren();
    const coverUrl = safeUrl(item.cover?.url);
    if (coverUrl) { const cover = make('img', 'pgl-detail-cover'); cover.src = coverUrl; cover.alt = ''; cover.referrerPolicy = 'no-referrer'; dialogContent.append(cover); }
    dialogContent.append(make('h2', '', item.title || ''));
    if (item.title_original && item.title_original !== item.title) dialogContent.append(make('p', 'pgl-detail-original', item.title_original));
    const details = [categoryLabel(item.category), statusLabel(item.status)];
    if (item.rating) details.push(`★ ${formatRating(item.rating.normalized_10)}`);
    dialogContent.append(make('p', 'pgl-detail-meta', details.filter(Boolean).join(' · ')));
    const steamData = steam(item);
    if (steamData && showSteamPlaytime && steamData.playtime_minutes !== undefined) {
      let text = `Steam: ${formatHours(steamData.playtime_minutes)} h`;
      if (showAchievements && steamData.achievements) text += ` · ${steamData.achievements.unlocked}/${steamData.achievements.total}`;
      dialogContent.append(make('p', '', text));
    }
    if (item.summary) dialogContent.append(make('p', '', item.summary));
    const links = make('div', 'pgl-detail-links');
    appendSafeLink(links, root.dataset.openSource || 'Open primary source', item.links?.primary, 'pgl-primary-link', true);
    for (const [name, rawUrl] of Object.entries(item.links || {})) if (name !== 'primary' && rawUrl) appendSafeLink(links, name, rawUrl, '', true);
    for (const article of item.articles || []) {
      const articleUrl = safeUrl(article.url); if (!articleUrl) continue;
      const external = new URL(articleUrl).origin !== location.origin;
      appendSafeLink(links, article.title || root.dataset.blog || 'Blog', articleUrl, 'pgl-article-link', external);
    }
    dialogContent.append(links);
    if (typeof dialog.showModal === 'function') dialog.showModal(); else dialog.setAttribute('open', '');
    dialog.querySelector('.pgl-close')?.focus();
  }

  function openById(id) { if (id && itemById.has(id)) openItem(itemById.get(id)); }

  document.addEventListener('click', (event) => {
    const opener = event.target.closest('[data-open-pgl]');
    if (opener) { openById(opener.dataset.openPgl); return; }
    const card = event.target.closest('.pgl-card');
    if (card && grid?.contains(card)) openById(card.dataset.pglId);
  });
  document.addEventListener('keydown', (event) => {
    if (!['Enter', ' '].includes(event.key)) return;
    const card = event.target.closest('.pgl-card');
    if (!card || !grid?.contains(card)) return;
    event.preventDefault(); openById(card.dataset.pglId);
  });
  dialog?.addEventListener('close', () => { if (lastFocused?.focus) lastFocused.focus(); lastFocused = null; });

  // Rating chart ------------------------------------------------------------
  const chart = $('pgl-rating-chart');
  const chartTooltip = $('pgl-rating-tooltip');

  function svgNode(tag, attrs = {}) {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
    return node;
  }

  function monotonePath(points) {
    if (!points.length) return '';
    if (points.length === 1) return `M${points[0].x},${points[0].y}`;
    const n = points.length;
    const d = new Array(n - 1);
    const m = new Array(n);
    for (let i = 0; i < n - 1; i += 1) d[i] = (points[i + 1].y - points[i].y) / (points[i + 1].x - points[i].x);
    m[0] = d[0]; m[n - 1] = d[n - 2];
    for (let i = 1; i < n - 1; i += 1) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (2 * d[i - 1] * d[i]) / (d[i - 1] + d[i]);
    for (let i = 0; i < n - 1; i += 1) {
      if (d[i] === 0) { m[i] = 0; m[i + 1] = 0; continue; }
      const a = m[i] / d[i], b = m[i + 1] / d[i];
      const h = Math.hypot(a, b);
      if (h > 3) { const t = 3 / h; m[i] = t * a * d[i]; m[i + 1] = t * b * d[i]; }
    }
    let path = `M${points[0].x.toFixed(2)},${points[0].y.toFixed(2)}`;
    for (let i = 0; i < n - 1; i += 1) {
      const p0 = points[i], p1 = points[i + 1], dx = p1.x - p0.x;
      const c1x = p0.x + dx / 3, c1y = p0.y + m[i] * dx / 3;
      const c2x = p1.x - dx / 3, c2y = p1.y - m[i + 1] * dx / 3;
      path += ` C${c1x.toFixed(2)},${c1y.toFixed(2)} ${c2x.toFixed(2)},${c2y.toFixed(2)} ${p1.x.toFixed(2)},${p1.y.toFixed(2)}`;
    }
    return path;
  }

  function renderRatingChart(scope = 'all') {
    if (!chart) return;
    const distribution = stats.rating_curve_distribution;
    const bins = distribution?.bins || [];
    const counts = distribution?.scopes?.[scope] || [];
    if (!bins.length || bins.length !== counts.length) return;
    chart.replaceChildren();
    const W = 760, H = 260, M = { l: 42, r: 18, t: 18, b: 42 };
    const maxCount = Math.max(1, ...counts.map(Number));
    const xAt = (index) => M.l + (index / Math.max(1, bins.length - 1)) * (W - M.l - M.r);
    const yAt = (count) => H - M.b - (Number(count) / maxCount) * (H - M.t - M.b);

    for (let i = 0; i <= 4; i += 1) {
      const y = M.t + ((H - M.t - M.b) * i / 4);
      chart.append(svgNode('line', { x1: M.l, y1: y, x2: W - M.r, y2: y, class: 'pgl-chart-gridline' }));
    }
    chart.append(svgNode('line', { x1: M.l, y1: H - M.b, x2: W - M.r, y2: H - M.b, class: 'pgl-chart-axis' }));

    bins.forEach((bin, index) => {
      const text = svgNode('text', { x: xAt(index), y: H - 14, 'text-anchor': 'middle', class: 'pgl-chart-label' }); text.textContent = String(bin); chart.append(text);
    });

    const points = counts.map((count, index) => ({ x: xAt(index), y: yAt(count), count: Number(count), bin: bins[index] }));
    chart.append(svgNode('path', { d: monotonePath(points), class: 'pgl-chart-curve', fill: 'none' }));
    for (const point of points) {
      const hit = svgNode('circle', { cx: point.x, cy: point.y, r: 10, class: 'pgl-chart-hit', tabindex: 0, role: 'img', 'aria-label': `${root.dataset.ratingAxis || 'Rating'} ${point.bin}: ${point.count}` });
      const show = () => {
        if (!chartTooltip) return;
        chartTooltip.hidden = false; chartTooltip.textContent = `${point.bin} · ${point.count} ${root.dataset.items || 'items'}`;
        chartTooltip.style.left = `${point.x / W * 100}%`; chartTooltip.style.top = `${point.y / H * 100}%`;
      };
      const hide = () => { if (chartTooltip) chartTooltip.hidden = true; };
      hit.addEventListener('mouseenter', show); hit.addEventListener('focus', show); hit.addEventListener('mouseleave', hide); hit.addEventListener('blur', hide); chart.append(hit);
    }
    document.querySelectorAll('[data-rating-scope]').forEach((button) => button.classList.toggle('is-active', button.dataset.ratingScope === scope));
  }

  document.getElementById('pgl-rating-scopes')?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-rating-scope]'); if (button) renderRatingChart(button.dataset.ratingScope);
  });

  // Timeline ----------------------------------------------------------------
  function eventLabel(name) { return root.dataset[`event${toPascal(name)}`] || name || ''; }
  async function loadTimeline() {
    const box = $('pgl-timeline'); if (!box) return;
    try {
      const manifest = await loadJson(root.dataset.historyManifest);
      const years = (manifest.history_years || []).slice(0, 3); const events = [];
      for (const historyYear of years) {
        const url = new URL(root.dataset.historyManifest, location.href); url.pathname = url.pathname.replace(/manifest\.json$/, `history/${encodeURIComponent(historyYear)}.json`);
        const data = await loadJson(url.href); events.push(...(data.events || []));
      }
      events.sort((a, b) => String(b.observed_at || '').localeCompare(String(a.observed_at || '')));
      const list = make('ul', 'pgl-timeline-list');
      for (const event of events.slice(0, 100)) {
        const row = make('li'); row.append(make('time', '', event.local_date || '')); row.append(document.createTextNode(` · ${eventLabel(event.event)} · ${event.data?.title || event.entity_id || ''}`)); list.append(row);
      }
      box.replaceChildren(list);
    } catch (error) { box.textContent = `${root.dataset.timelineUnavailable || 'Timeline unavailable'}: ${error.message}`; }
  }
  $('pgl-load-timeline')?.addEventListener('click', loadTimeline);

  // Navigation/events -------------------------------------------------------
  document.addEventListener('click', (event) => {
    const category = event.target.closest('[data-pgl-category]');
    if (category) { event.preventDefault(); navigate({ ...defaultState(), view: 'category', category: category.dataset.pglCategory }); return; }
    const wishlist = event.target.closest('[data-pgl-wishlist]');
    if (wishlist) { event.preventDefault(); navigate({ ...defaultState(), view: 'wishlist' }); return; }
    const wishlistCategory = event.target.closest('[data-pgl-wishlist-category]');
    if (wishlistCategory) { event.preventDefault(); navigate({ ...defaultState(), view: 'wishlist', category: wishlistCategory.dataset.pglWishlistCategory }); return; }
    const statusButton = event.target.closest('[data-pgl-status]');
    if (statusButton && state.category) { navigate({ ...state, view: 'other', status: statusButton.dataset.pglStatus, page: 1 }); }
  });

  back?.addEventListener('click', () => {
    if (state.view === 'wishlist' && state.category) navigate({ ...defaultState(), view: 'wishlist' });
    else if (state.view === 'search' && previousNonSearchState) navigate(previousNonSearchState);
    else navigate(defaultState());
  });

  pagination?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-page]');
    if (!button || button.disabled) return;
    const page = Number(button.dataset.page); if (!Number.isFinite(page) || page < 1) return;
    navigate({ ...state, page });
    browserView?.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
  });

  search?.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      const q = search.value.trim();
      if (q) navigate({ ...defaultState(), view: 'search', q }, { replace: true });
      else if (state.view === 'search') navigate(previousNonSearchState || defaultState(), { replace: true });
    }, 140);
  });
  search?.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') { root.classList.remove('is-search-open'); searchToggle?.setAttribute('aria-expanded', 'false'); search.blur(); }
  });
  searchToggle?.addEventListener('click', () => {
    const open = !root.classList.contains('is-search-open'); root.classList.toggle('is-search-open', open); searchToggle.setAttribute('aria-expanded', String(open)); if (open) search?.focus();
  });

  sort?.addEventListener('change', () => navigate({ ...state, sort: sort.value, page: 1 }));
  source?.addEventListener('change', () => navigate({ ...state, source: source.value, page: 1 }));
  year?.addEventListener('change', () => navigate({ ...state, year: year.value, page: 1 }));
  clearFilters?.addEventListener('click', () => navigate({ ...state, source: '', year: '', sort: 'updated', page: 1 }));
  layoutGrid?.addEventListener('click', () => setLayout('grid'));
  layoutList?.addEventListener('click', () => setLayout('list'));
  window.addEventListener('popstate', () => { state = parseState(); render(); });

  // Load static public artifacts and initialize. --------------------------------
  Promise.all([loadJson(root.dataset.libraryUrl), loadJson(root.dataset.statsUrl)])
    .then(([library, loadedStats]) => {
      items = Array.isArray(library.items) ? library.items : [];
      stats = loadedStats || {};
      itemById = new Map(items.map((item) => [item.id, item]));
      populateYears();
      setLayout(currentLayout());
      renderRatingChart('all');
      render();
      // Normalize legacy ?type= and view=grid/list URLs without adding history.
      if (location.search.includes('type=') || /(?:^|[?&])view=(?:grid|list)(?:&|$)/.test(location.search)) writeHistory(state, { replace: true });
    })
    .catch((error) => {
      // Root SSR remains useful. Direct browser views fail visibly instead of
      // presenting an empty grid that looks like a valid empty library.
      if (state.view !== 'index' && resultCount) resultCount.textContent = `PGL data unavailable: ${error.message}`;
      render();
    });
})();
