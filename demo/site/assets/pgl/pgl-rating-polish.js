(() => {
  'use strict';
  const root = document.getElementById('prospero-great-library');
  const chart = document.getElementById('pgl-rating-chart');
  const scopes = document.getElementById('pgl-rating-scopes');
  const tooltip = document.getElementById('pgl-rating-tooltip');
  const summary = document.getElementById('pgl-rating-summary');
  if (!root || !chart || !scopes) return;

  let distribution = null;
  let currentScope = 'all';
  let scheduled = false;

  const svg = (tag, attrs = {}) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, String(v)));
    return node;
  };

  function monotonePath(points) {
    if (!points.length) return '';
    if (points.length === 1) return `M${points[0].x},${points[0].y}`;
    const n = points.length, d = new Array(n - 1), m = new Array(n);
    for (let i = 0; i < n - 1; i += 1) d[i] = (points[i + 1].y - points[i].y) / (points[i + 1].x - points[i].x);
    m[0] = d[0]; m[n - 1] = d[n - 2];
    for (let i = 1; i < n - 1; i += 1) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (2 * d[i - 1] * d[i]) / (d[i - 1] + d[i]);
    for (let i = 0; i < n - 1; i += 1) {
      if (d[i] === 0) { m[i] = 0; m[i + 1] = 0; continue; }
      const a = m[i] / d[i], b = m[i + 1] / d[i], h = Math.hypot(a, b);
      if (h > 3) { const t = 3 / h; m[i] = t * a * d[i]; m[i + 1] = t * b * d[i]; }
    }
    let path = `M${points[0].x.toFixed(2)},${points[0].y.toFixed(2)}`;
    for (let i = 0; i < n - 1; i += 1) {
      const p0 = points[i], p1 = points[i + 1], dx = p1.x - p0.x;
      path += ` C${(p0.x + dx / 3).toFixed(2)},${(p0.y + m[i] * dx / 3).toFixed(2)} ${(p1.x - dx / 3).toFixed(2)},${(p1.y - m[i + 1] * dx / 3).toFixed(2)} ${p1.x.toFixed(2)},${p1.y.toFixed(2)}`;
    }
    return path;
  }

  function updateSummary(bins, counts) {
    if (!summary) return;
    const total = counts.reduce((a, b) => a + Number(b || 0), 0);
    if (!total) { summary.textContent = `0 ${summary.dataset.countLabel || 'rated works'}`; return; }
    const weighted = counts.reduce((acc, count, i) => acc + Number(count || 0) * Number(bins[i] || 0), 0);
    const mean = weighted / total;
    let modeIndex = 0;
    counts.forEach((value, i) => { if (Number(value) > Number(counts[modeIndex])) modeIndex = i; });
    summary.textContent = `${total} ${summary.dataset.countLabel || 'rated works'} · ${summary.dataset.meanLabel || 'Mean'} ${mean.toFixed(1)} · ${summary.dataset.modeLabel || 'Peak'} ${bins[modeIndex]}`;
  }

  function render(scope = currentScope) {
    if (!distribution) return;
    currentScope = scope;
    const bins = distribution.bins || [], counts = distribution.scopes?.[scope] || [];
    if (!bins.length || bins.length !== counts.length) return;
    const W = 760, H = 260, M = { l: 42, r: 18, t: 18, b: 42 };
    const baseline = H - M.b, maxCount = Math.max(1, ...counts.map(Number));
    const xAt = (i) => M.l + (i / Math.max(1, bins.length - 1)) * (W - M.l - M.r);
    const yAt = (n) => baseline - (Number(n) / maxCount) * (H - M.t - M.b);
    const points = counts.map((count, i) => ({ x:xAt(i), y:yAt(count), count:Number(count), bin:bins[i] }));
    const curve = monotonePath(points);

    chart.replaceChildren();
    const defs = svg('defs');
    const gradient = svg('linearGradient', { id:'pgl-rating-area-gradient', x1:'0', y1:'0', x2:'0', y2:'1' });
    gradient.append(svg('stop', { offset:'0%', class:'pgl-chart-area-stop-start' }), svg('stop', { offset:'100%', class:'pgl-chart-area-stop-end' }));
    defs.append(gradient); chart.append(defs);

    for (let i = 0; i <= 3; i += 1) {
      const y = M.t + ((H - M.t - M.b) * i / 3);
      chart.append(svg('line', { x1:M.l, y1:y, x2:W-M.r, y2:y, class:'pgl-chart-gridline' }));
    }
    chart.append(svg('line', { x1:M.l, y1:baseline, x2:W-M.r, y2:baseline, class:'pgl-chart-axis' }));

    const step = (W - M.l - M.r) / Math.max(1, bins.length - 1);
    const barWidth = Math.max(3, step * .34);
    points.forEach((point, i) => {
      if (point.count > 0) chart.append(svg('rect', { x:point.x-barWidth/2, y:point.y, width:barWidth, height:Math.max(0,baseline-point.y), rx:Math.min(3,barWidth/3), class:'pgl-chart-bar' }));
      const label = svg('text', { x:point.x, y:H-14, 'text-anchor':'middle', class:'pgl-chart-label' }); label.textContent=String(bins[i]); chart.append(label);
    });

    if (points.length) {
      const first=points[0], last=points[points.length-1];
      chart.append(svg('path', { d:`${curve} L${last.x.toFixed(2)},${baseline} L${first.x.toFixed(2)},${baseline} Z`, class:'pgl-chart-area' }));
      chart.append(svg('path', { d:curve, class:'pgl-chart-curve', fill:'none' }));
    }

    for (const point of points) {
      if (point.count > 0) chart.append(svg('circle', { cx:point.x, cy:point.y, r:2.8, class:'pgl-chart-point' }));
      const hit=svg('circle',{cx:point.x,cy:point.y,r:11,class:'pgl-chart-hit',tabindex:0,role:'img','aria-label':`${root.dataset.ratingAxis || 'Rating'} ${point.bin}: ${point.count}`});
      const show=()=>{ if(!tooltip)return; tooltip.hidden=false; tooltip.textContent=`${point.bin} · ${point.count} ${root.dataset.items || 'items'}`; tooltip.style.left=`${point.x/W*100}%`; tooltip.style.top=`${point.y/H*100}%`; };
      const hide=()=>{ if(tooltip)tooltip.hidden=true; };
      hit.addEventListener('mouseenter',show); hit.addEventListener('focus',show); hit.addEventListener('mouseleave',hide); hit.addEventListener('blur',hide); chart.append(hit);
    }
    scopes.querySelectorAll('[data-rating-scope]').forEach((button)=>button.classList.toggle('is-active',button.dataset.ratingScope===scope));
    updateSummary(bins,counts);
  }

  const scheduleRender = () => {
    if (scheduled || !distribution) return;
    scheduled = true;
    requestAnimationFrame(() => { scheduled = false; render(currentScope); });
  };

  // The alpha.5 router owns the original chart renderer. If it redraws after
  // this enhancement (initial async race or scope click), restore the polished
  // representation whenever the area layer disappears.
  new MutationObserver(() => {
    if (distribution && !chart.querySelector('.pgl-chart-area')) scheduleRender();
  }).observe(chart,{childList:true});

  scopes.addEventListener('click',(event)=>{
    const button=event.target.closest('[data-rating-scope]');
    if (!button) return;
    currentScope=button.dataset.ratingScope || 'all';
    queueMicrotask(()=>render(currentScope));
  });

  fetch(root.dataset.statsUrl,{credentials:'same-origin'})
    .then((response)=>{ if(!response.ok)throw new Error(`HTTP ${response.status}`); return response.json(); })
    .then((stats)=>{ distribution=stats?.rating_curve_distribution || null; if(distribution)render('all'); })
    .catch(()=>{});
})();
