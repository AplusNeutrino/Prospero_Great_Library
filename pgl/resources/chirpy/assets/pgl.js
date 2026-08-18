(() => {
  'use strict';

  const root = document.getElementById('prospero-great-library');
  if (!root) return;

  const $ = (id) => document.getElementById(id);
  const grid = $('pgl-grid');
  if (!grid) return;

  const controls = {
    search: $('pgl-search'),
    category: $('pgl-category'),
    status: $('pgl-status'),
    source: $('pgl-source'),
    year: $('pgl-year'),
    sort: $('pgl-sort'),
    count: $('pgl-result-count'),
    loadMore: $('pgl-load-more'),
    layout: $('pgl-layout'),
  };

  const initialLimit = Math.max(1, Number(root.dataset.initialLimit || 60));
  const lazyRender = root.dataset.lazyRender !== 'false';
  const drawerEnabled = root.dataset.drawerEnabled !== 'false';
  const showSources = root.dataset.showSources !== 'false';
  const showSteamPlaytime = root.dataset.showSteamPlaytime !== 'false';
  const showAchievements = root.dataset.showAchievements !== 'false';
  const initialCards = [...grid.querySelectorAll('.pgl-card')];
  let items = null;
  let itemById = new Map();
  let renderLimit = lazyRender ? initialLimit : Number.POSITIVE_INFINITY;
  let libraryPromise = null;
  let lastFocused = null;

  const params = new URLSearchParams(location.search);
  if (controls.category && params.get('type')) controls.category.value = params.get('type');
  if (controls.status && params.get('status')) controls.status.value = params.get('status');
  if (controls.search && params.get('q')) controls.search.value = params.get('q');
  if (controls.source && params.get('source')) controls.source.value = params.get('source');
  if (controls.sort && params.get('sort')) controls.sort.value = params.get('sort');

  if (params.get('view') === 'list') {
    grid.classList.add('is-list');
    controls.layout?.setAttribute('aria-pressed', 'true');
  } else if (params.get('view') === 'grid') {
    grid.classList.remove('is-list');
    controls.layout?.setAttribute('aria-pressed', 'false');
  }

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
  const formatRating = (value) => {
    if (value === null || value === undefined || value === '') return '';
    const n = Number(value);
    return Number.isFinite(n) ? (Number.isInteger(n) ? String(n) : n.toFixed(1)) : '';
  };
  const formatHours = (minutes) => {
    const hours = (Number(minutes) || 0) / 60;
    return hours >= 100 ? String(Math.round(hours)) : hours.toFixed(1);
  };
  const categoryLabel = (category) => root.dataset[`category${toPascal(category)}`] || category || '';
  const statusLabel = (status) => root.dataset[`status${toPascal(status)}`] || status || '';
  function toPascal(value) {
    return String(value || '')
      .split(/[_-]/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join('');
  }
  function make(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function itemSearchText(item) {
    return normalizeText([item.title, item.title_original, ...(item.alternate_titles || [])].filter(Boolean).join(' '));
  }

  function itemSources(item) {
    return Object.keys(item.sources || {});
  }

  function itemSortValue(item, key) {
    if (key === 'rating') return Number(item.rating?.normalized_10 || 0);
    if (key === 'playtime') return Number(item.telemetry?.steam?.playtime_minutes || 0);
    if (key === 'title') return normalizeText(item.title);
    return item.timestamps?.canonical_updated_at || '';
  }

  function buildCard(item) {
    const card = make('article', 'pgl-card');
    card.dataset.pglId = item.id || '';
    card.dataset.category = item.category || '';
    card.dataset.categoryLabel = categoryLabel(item.category);
    card.dataset.status = item.status || '';
    card.dataset.statusLabel = statusLabel(item.status);
    card.dataset.year = item.year || '';
    card.dataset.title = itemSearchText(item);
    card.dataset.rating = String(item.rating?.normalized_10 || 0);
    card.dataset.playtime = String(item.telemetry?.steam?.playtime_minutes || 0);
    card.dataset.updated = item.timestamps?.canonical_updated_at || '';
    card.dataset.sources = itemSources(item).join(' ');
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
      image.loading = 'lazy';
      image.decoding = 'async';
      image.referrerPolicy = 'no-referrer';
      coverWrap.append(image);
    } else {
      const placeholder = make('div', 'pgl-cover pgl-cover-placeholder', 'PGL');
      placeholder.setAttribute('aria-hidden', 'true');
      coverWrap.append(placeholder);
    }

    const body = make('div', 'pgl-card-body');
    const kickers = make('div', 'pgl-card-kickers');
    kickers.append(make('span', 'pgl-type', categoryLabel(item.category)));
    if ((item.tags || []).includes('performance')) {
      kickers.append(make('span', 'pgl-badge', root.dataset.performance || 'Performance'));
    }
    body.append(kickers);
    body.append(make('h3', 'pgl-card-title', item.title || ''));
    if (item.title_original && item.title_original !== item.title) {
      body.append(make('div', 'pgl-alt-title', item.title_original));
    }

    const meta = make('div', 'pgl-meta');
    if (item.year) meta.append(make('span', '', item.year));
    if (item.status) meta.append(make('span', 'pgl-status', statusLabel(item.status)));
    if (item.rating) meta.append(make('span', '', `★ ${formatRating(item.rating.normalized_10)}`));
    const playtime = item.telemetry?.steam?.playtime_minutes;
    if (showSteamPlaytime && playtime) meta.append(make('span', '', `Steam ${formatHours(playtime)}h`));
    body.append(meta);

    if (item.progress && item.progress.current !== null && item.progress.current !== undefined) {
      const progress = make('div', 'pgl-progress');
      progress.title = `${item.progress.current} / ${item.progress.total ?? '?'}`;
      const bar = make('span');
      bar.style.width = `${clamp(item.progress.percent, 0, 100)}%`;
      progress.append(bar);
      body.append(progress);
    }

    if (showSources) {
      const sourceRow = make('div', 'pgl-source-row');
      for (const sourceName of itemSources(item)) {
        const badge = make('span', 'pgl-source', sourceName);
        badge.dataset.source = sourceName;
        sourceRow.append(badge);
      }
      if ((item.articles || []).length) {
        sourceRow.append(make('span', 'pgl-source', `${root.dataset.blog || 'Blog'} ×${item.articles.length}`));
      }
      body.append(sourceRow);
    }

    card.append(coverWrap, body);
    return card;
  }

  function filteredItems() {
    if (!items) return [];
    const q = normalizeText(controls.search?.value || '').trim();
    return items.filter((item) => {
      if (q && !itemSearchText(item).includes(q)) return false;
      if (controls.category?.value && item.category !== controls.category.value) return false;
      if (controls.status?.value && item.status !== controls.status.value) return false;
      if (controls.source?.value && !itemSources(item).includes(controls.source.value)) return false;
      if (controls.year?.value && String(item.year || '') !== controls.year.value) return false;
      return true;
    });
  }

  function sortedItems(input) {
    const key = controls.sort?.value || 'updated';
    return [...input].sort((a, b) => {
      const av = itemSortValue(a, key);
      const bv = itemSortValue(b, key);
      if (key === 'rating' || key === 'playtime') return bv - av;
      if (key === 'title') return String(av).localeCompare(String(bv));
      return String(bv).localeCompare(String(av));
    });
  }

  function legacyEligibleCards() {
    const q = normalizeText(controls.search?.value || '').trim();
    return initialCards.filter((card) => {
      if (q && !normalizeText(card.dataset.title).includes(q)) return false;
      if (controls.category?.value && card.dataset.category !== controls.category.value) return false;
      if (controls.status?.value && card.dataset.status !== controls.status.value) return false;
      if (controls.source?.value && !String(card.dataset.sources || '').split(/\s+/).includes(controls.source.value)) return false;
      if (controls.year?.value && card.dataset.year !== controls.year.value) return false;
      return true;
    });
  }

  function updateCount(visible, total, all) {
    if (controls.count) controls.count.textContent = `${visible} / ${total} (${all})`;
  }

  function apply(reset = false) {
    if (reset) renderLimit = lazyRender ? initialLimit : Number.POSITIVE_INFINITY;

    if (items) {
      const selected = sortedItems(filteredItems());
      const visibleCount = Math.min(selected.length, renderLimit);
      const fragment = document.createDocumentFragment();
      for (const item of selected.slice(0, visibleCount)) fragment.append(buildCard(item));
      grid.replaceChildren(fragment);
      updateCount(visibleCount, selected.length, items.length);
      if (controls.loadMore) controls.loadMore.hidden = !lazyRender || selected.length <= renderLimit;
    } else {
      const selected = legacyEligibleCards();
      selected.sort((a, b) => {
        const key = controls.sort?.value || 'updated';
        if (key === 'rating' || key === 'playtime') return Number(b.dataset[key] || 0) - Number(a.dataset[key] || 0);
        if (key === 'title') return String(a.dataset.title || '').localeCompare(String(b.dataset.title || ''));
        return String(b.dataset.updated || '').localeCompare(String(a.dataset.updated || ''));
      });
      const visibleCount = Math.min(selected.length, renderLimit);
      initialCards.forEach((card) => { card.hidden = true; });
      selected.forEach((card, index) => {
        grid.append(card);
        card.hidden = index >= visibleCount;
      });
      updateCount(visibleCount, selected.length, initialCards.length);
      if (controls.loadMore) controls.loadMore.hidden = !lazyRender || selected.length <= renderLimit;
    }

    syncUrlState();
  }

  function syncUrlState() {
    if (!history.replaceState) return;
    const next = new URLSearchParams(location.search);
    const setOrDelete = (key, value, defaultValue = '') => {
      if (value && value !== defaultValue) next.set(key, value);
      else next.delete(key);
    };
    setOrDelete('type', controls.category?.value || '');
    setOrDelete('status', controls.status?.value || '');
    setOrDelete('q', (controls.search?.value || '').trim());
    setOrDelete('source', controls.source?.value || '');
    setOrDelete('year', controls.year?.value || '');
    setOrDelete('sort', controls.sort?.value || '', 'updated');
    setOrDelete('view', grid.classList.contains('is-list') ? 'list' : 'grid', 'grid');
    const query = next.toString();
    history.replaceState(null, '', `${location.pathname}${query ? `?${query}` : ''}${location.hash}`);
  }

  function populateYears(values) {
    if (!controls.year) return;
    const selected = params.get('year') || controls.year.value;
    const first = controls.year.options[0];
    controls.year.replaceChildren(first);
    [...new Set(values.filter(Boolean).map(String))]
      .sort((a, b) => Number(b) - Number(a))
      .forEach((value) => controls.year.add(new Option(value, value)));
    if ([...controls.year.options].some((option) => option.value === selected)) controls.year.value = selected;
  }

  function loadLibrary() {
    if (!libraryPromise) {
      libraryPromise = fetch(root.dataset.libraryUrl, { credentials: 'same-origin' }).then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      });
    }
    return libraryPromise;
  }

  const dialog = $('pgl-drawer');
  const dialogContent = $('pgl-drawer-content');

  function appendSafeLink(container, label, rawUrl, className = '', external = true) {
    const url = safeUrl(rawUrl);
    if (!url) return;
    const link = make('a', className, label);
    link.href = url;
    if (external) {
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
    }
    container.append(link);
  }

  function openItem(item) {
    if (!drawerEnabled || !dialog || !dialogContent || !item) return;
    lastFocused = document.activeElement;
    dialogContent.replaceChildren();

    const coverUrl = safeUrl(item.cover?.url);
    if (coverUrl) {
      const cover = make('img', 'pgl-detail-cover');
      cover.src = coverUrl;
      cover.alt = '';
      cover.referrerPolicy = 'no-referrer';
      dialogContent.append(cover);
    }
    dialogContent.append(make('h2', '', item.title || ''));
    if (item.title_original && item.title_original !== item.title) dialogContent.append(make('p', '', item.title_original));

    const details = [categoryLabel(item.category), statusLabel(item.status)];
    if (item.rating) details.push(`★ ${formatRating(item.rating.normalized_10)}`);
    dialogContent.append(make('p', '', details.filter(Boolean).join(' · ')));

    const steam = item.telemetry?.steam;
    if (steam && showSteamPlaytime) {
      let text = `Steam: ${formatHours(steam.playtime_minutes)} h`;
      if (showAchievements && steam.achievements) text += ` · ${steam.achievements.unlocked}/${steam.achievements.total}`;
      dialogContent.append(make('p', '', text));
    }
    if (item.summary) dialogContent.append(make('p', '', item.summary));

    const links = make('div', 'pgl-detail-links');
    appendSafeLink(links, root.dataset.openSource || 'Open primary source', item.links?.primary, 'pgl-primary-link', true);
    for (const [name, rawUrl] of Object.entries(item.links || {})) {
      if (name === 'primary' || !rawUrl) continue;
      appendSafeLink(links, name, rawUrl, '', true);
    }
    for (const article of item.articles || []) {
      const articleUrl = safeUrl(article.url);
      if (!articleUrl) continue;
      const external = new URL(articleUrl).origin !== location.origin;
      appendSafeLink(links, article.title || root.dataset.blog || 'Blog', articleUrl, 'pgl-article-link', external);
    }
    dialogContent.append(links);

    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', '');
    dialog.querySelector('.pgl-close')?.focus();
  }

  async function openById(id) {
    if (!id) return;
    if (itemById.has(id)) {
      openItem(itemById.get(id));
      return;
    }
    try {
      const library = await loadLibrary();
      const item = (library.items || []).find((candidate) => candidate.id === id);
      if (item) openItem(item);
    } catch {
      // The server-rendered card remains usable as static content.
    }
  }

  if (drawerEnabled) {
    grid.addEventListener('click', (event) => {
      const card = event.target.closest('.pgl-card');
      if (card && grid.contains(card)) openById(card.dataset.pglId);
    });
    grid.addEventListener('keydown', (event) => {
      if (!['Enter', ' '].includes(event.key)) return;
      const card = event.target.closest('.pgl-card');
      if (!card || !grid.contains(card)) return;
      event.preventDefault();
      openById(card.dataset.pglId);
    });
    document.querySelectorAll('[data-open-pgl]').forEach((button) => {
      button.addEventListener('click', () => openById(button.dataset.openPgl));
    });
    dialog?.addEventListener('close', () => {
      if (lastFocused && typeof lastFocused.focus === 'function') lastFocused.focus();
      lastFocused = null;
    });
  }

  function eventLabel(name) {
    return root.dataset[`event${toPascal(name)}`] || name || '';
  }

  async function loadTimeline() {
    const box = $('pgl-timeline');
    if (!box) return;
    try {
      const response = await fetch(root.dataset.historyManifest, { credentials: 'same-origin' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const manifest = await response.json();
      const years = (manifest.history_years || []).slice(0, 3);
      const events = [];
      for (const year of years) {
        const url = new URL(root.dataset.historyManifest, location.href);
        url.pathname = url.pathname.replace(/manifest\.json$/, `history/${encodeURIComponent(year)}.json`);
        const historyResponse = await fetch(url, { credentials: 'same-origin' });
        if (!historyResponse.ok) throw new Error(`HTTP ${historyResponse.status}`);
        const data = await historyResponse.json();
        events.push(...(data.events || []));
      }
      events.sort((a, b) => String(b.observed_at || '').localeCompare(String(a.observed_at || '')));
      const list = make('ul', 'pgl-timeline-list');
      for (const event of events.slice(0, 100)) {
        const row = make('li');
        row.append(make('time', '', event.local_date || ''));
        row.append(document.createTextNode(` · ${eventLabel(event.event)} · ${event.data?.title || event.entity_id || ''}`));
        list.append(row);
      }
      box.replaceChildren(list);
    } catch (error) {
      box.textContent = `${root.dataset.timelineUnavailable || 'Timeline unavailable'}: ${error.message}`;
    }
  }

  $('pgl-load-timeline')?.addEventListener('click', loadTimeline);

  let searchTimer = null;
  controls.search?.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => apply(true), 140);
  });
  [controls.category, controls.status, controls.source, controls.year].forEach((control) => {
    control?.addEventListener('change', () => apply(true));
  });
  controls.sort?.addEventListener('change', () => apply(false));
  controls.loadMore?.addEventListener('click', () => {
    renderLimit += initialLimit;
    apply(false);
  });
  controls.layout?.addEventListener('click', () => {
    grid.classList.toggle('is-list');
    controls.layout.setAttribute('aria-pressed', String(grid.classList.contains('is-list')));
    syncUrlState();
  });

  populateYears(initialCards.map((card) => card.dataset.year));
  apply(true);

  loadLibrary()
    .then((library) => {
      items = Array.isArray(library.items) ? library.items : [];
      itemById = new Map(items.map((item) => [item.id, item]));
      populateYears(items.map((item) => item.year));
      apply(true);
    })
    .catch(() => {
      // Keep and operate on the server-rendered initial subset when the static
      // JSON artifact cannot be fetched. The page therefore never blanks out.
    });
})();
