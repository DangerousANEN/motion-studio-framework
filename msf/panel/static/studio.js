(() => {
  'use strict';

  const $ = (selector) => document.querySelector(selector);
  const state = { catalog: [], styles: [], graph: [], runId: '', snapshot: null, request: null, events: [], traces: [], selectedNode: null, selectedScene: null, polling: false, pollTimer: null, lastSequence: 0, thumbnailQueue: [], queuedThumbnails: new Set(), thumbnailBusy: false, thumbnailObserver: null };
  const catalogCards = $('#catalogCards');
  const presetSelect = $('#preset');
  const styleFamily = $('#styleFamily');
  const runIdInput = $('#runIdInput');
  const nodeInstruction = $('#nodeInstruction');

  async function request(url, options = {}) {
    const headers = { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(options.headers || {}) };
    const response = await fetch(url, { ...options, headers });
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    if (!response.ok) throw new Error(typeof payload.detail === 'object' ? JSON.stringify(payload.detail) : (payload.detail || payload.message || response.statusText));
    return payload;
  }

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
  const time = (value) => value ? new Date(value).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—';
  const isActive = () => ['queued', 'running', 'retrying'].includes(state.snapshot?.status);

  function setRunResult(text, kind = 'empty') { const el = $('#runResult'); el.textContent = text; el.className = `run-result ${kind}`; }
  function setStatusBadge(status) { const el = $('#runStatusBadge'); el.textContent = (status || 'NO RUN').toUpperCase(); el.className = `chip ${status === 'running' ? 'safe' : 'muted'}`; }

  function styleConfig() {
    const palette = {};
    [['#styleNeon', 'neon'], ['#styleBg', 'bg'], ['#styleSurface', 'surface']].forEach(([id, key]) => { const input = $(id); if (input?.dataset.override === 'true') palette[key] = input.value; });
    const effects = {}; const bloom = $('#styleBloom'); if (bloom?.dataset.override === 'true') effects.bloom = Number(bloom.value);
    const output = {}; if (Object.keys(palette).length) output.palette = palette; if (Object.keys(effects).length) output.effects = effects; return output;
  }

  function selectedStyle() { return state.styles.find((style) => style.id === styleFamily.value) || state.styles[0] || null; }
  function refreshStyleControls() {
    const family = selectedStyle(); if (!family) return;
    $('#styleSummary').textContent = family.label; $('#styleDescription').textContent = family.summary;
    const palette = styleConfig().palette || family.defaults?.palette || {};
    $('#styleSwatch').style.background = `linear-gradient(135deg, ${palette.neon || '#65f5c1'}, ${palette.bg || '#aa8cff'})`;
    $('#styleBloomValue').textContent = Number($('#styleBloom').value).toFixed(2);
  }
  function applyStyleFamily() {
    const family = selectedStyle(); const palette = family?.defaults?.palette || {};
    [['#styleNeon', palette.neon], ['#styleBg', palette.bg], ['#styleSurface', palette.surface]].forEach(([id, color]) => { if (color) $(id).value = color; $(id).dataset.override = 'false'; });
    if (typeof family?.defaults?.effects?.bloom === 'number') $('#styleBloom').value = family.defaults.effects.bloom;
    $('#styleBloom').dataset.override = 'false'; refreshStyleControls();
  }

  async function loadStyles() {
    const data = await request('/api/studio/styles'); state.styles = data.families || []; styleFamily.replaceChildren();
    state.styles.forEach((family) => { const option = document.createElement('option'); option.value = family.id; option.textContent = family.label; styleFamily.appendChild(option); });
    if (state.styles.some((style) => style.id === 'llm_hubs_neon')) styleFamily.value = 'llm_hubs_neon'; applyStyleFamily();
  }

  function renderCatalog() {
    catalogCards.replaceChildren();
    if (!state.catalog.length) { catalogCards.innerHTML = '<p class="empty-state">Ничего не найдено. Измените поисковую фразу или tier.</p>'; return; }
    const template = $('#catalogCardTemplate');
    state.catalog.forEach((scene) => {
      const fragment = template.content.cloneNode(true); const card = fragment.querySelector('.scene-card'); card.dataset.preset = scene.name;
      fragment.querySelector('.scene-category').textContent = scene.category || 'general'; fragment.querySelector('strong').textContent = scene.name; fragment.querySelector('p').textContent = scene.summary || '—';
      const tags = fragment.querySelector('.scene-tags'); (scene.intent_tags || []).slice(0, 3).forEach((tag) => { const item = document.createElement('span'); item.textContent = tag; tags.appendChild(item); });
      fragment.querySelector('small').textContent = scene.data_driven ? `Данные: ${(scene.required_data_hints || []).join(', ') || 'обязательны'}` : `Audio: ${(scene.recommended_audio_roles || []).slice(0, 2).join(', ') || 'auto'}`;
      card.addEventListener('click', () => openSceneDrawer(scene)); catalogCards.appendChild(fragment);
    });
    observeCatalogThumbnails();
  }
  function setThumbnail(preset, url, cached) {
    document.querySelectorAll(`.scene-card[data-preset="${CSS.escape(preset)}"] .scene-thumb`).forEach((thumb) => {
      thumb.innerHTML = `<img loading="lazy" alt="${escapeHtml(preset)} preview" src="${escapeHtml(url)}"/><span class="thumb-state">${cached ? 'Cached' : 'Rendered'}</span>`;
      thumb.classList.add('ready');
    });
  }
  async function fetchThumbnail(preset) {
    try { const cached = await request(`/api/preview/thumbnail/${encodeURIComponent(preset)}`); setThumbnail(preset, cached.url, true); return; }
    catch (error) { if (!String(error.message).includes('thumbnail not cached')) throw error; }
    queueThumbnail(preset);
  }
  function queueThumbnail(preset) {
    if (state.queuedThumbnails.has(preset)) return; state.queuedThumbnails.add(preset); state.thumbnailQueue.push(preset);
    document.querySelectorAll(`.scene-card[data-preset="${CSS.escape(preset)}"] .thumb-state`).forEach((label) => { label.textContent = 'Queued'; }); runThumbnailQueue();
  }
  async function runThumbnailQueue() {
    if (state.thumbnailBusy || !state.thumbnailQueue.length) return; state.thumbnailBusy = true; const preset = state.thumbnailQueue.shift();
    try { const result = await request('/api/preview/thumbnail', { method: 'POST', body: JSON.stringify({ preset, demo_props: true }) }); setThumbnail(preset, result.url, result.cached); }
    catch (_) { document.querySelectorAll(`.scene-card[data-preset="${CSS.escape(preset)}"] .thumb-state`).forEach((label) => { label.textContent = 'Unavailable'; }); }
    finally { state.thumbnailBusy = false; if (state.thumbnailQueue.length) setTimeout(runThumbnailQueue, 50); }
  }
  function observeCatalogThumbnails() {
    state.thumbnailObserver?.disconnect();
    state.thumbnailObserver = new IntersectionObserver((entries) => entries.forEach((entry) => { if (entry.isIntersecting) { state.thumbnailObserver.unobserve(entry.target); fetchThumbnail(entry.target.dataset.preset).catch(() => {}); } }), { root: catalogCards, rootMargin: '180px 0px' });
    catalogCards.querySelectorAll('.scene-card').forEach((card) => state.thumbnailObserver.observe(card));
  }
  async function loadCatalog() {
    $('#catalogStatus').textContent = 'Обновляем live catalog…';
    try {
      const params = new URLSearchParams({ query: $('#catalogQuery').value.trim(), tier: $('#catalogTier').value, limit: '80' });
      const data = await request(`/api/studio/catalog?${params}`); state.catalog = data.items || []; renderCatalog(); $('#catalogTotal').textContent = `${data.total} сцен`;
      $('#catalogStatus').textContent = `Live catalog · ${data.total} scenes`;
      const chosen = presetSelect.value; presetSelect.replaceChildren(); state.catalog.forEach((scene) => { const option = document.createElement('option'); option.value = scene.name; option.textContent = scene.name; presetSelect.appendChild(option); });
      if ([...presetSelect.options].some((option) => option.value === chosen)) presetSelect.value = chosen;
    } catch (error) { catalogCards.innerHTML = `<p class="empty-state">Catalog unavailable: ${escapeHtml(error.message)}</p>`; $('#catalogStatus').textContent = 'Catalog недоступен'; }
  }

  async function loadGraph() { const data = await request('/api/studio/control-room/graph'); state.graph = data.nodes || []; if (!state.selectedNode && state.graph[0]) state.selectedNode = state.graph[0].id; renderGraph(); renderNodeInspector(); }
  function nodeState(nodeId) {
    if (state.snapshot?.current_node === nodeId) return 'active';
    const relevant = state.events.filter((event) => event.node === nodeId); const last = relevant[relevant.length - 1];
    if (!last) return ''; if (last.type === 'node.failed') return 'failed'; if (last.type === 'node.completed') return 'done'; return '';
  }
  function renderGraph() {
    const root = $('#pipelineGraph'); root.replaceChildren();
    state.graph.forEach((node, index) => {
      const button = document.createElement('button'); button.type = 'button'; button.className = `graph-node ${nodeState(node.id)} ${state.selectedNode === node.id ? 'selected' : ''}`; button.dataset.node = node.id;
      button.innerHTML = `<span class="node-index">${String(index + 1).padStart(2, '0')} · ${escapeHtml(node.label)}</span><b>${escapeHtml(node.title)}</b><small>${escapeHtml(node.description)}</small>`;
      button.addEventListener('click', () => { state.selectedNode = node.id; renderGraph(); renderNodeInspector(); }); root.appendChild(button);
      if (index < state.graph.length - 1) { const edge = document.createElement('i'); edge.className = 'graph-edge'; root.appendChild(edge); }
    });
    const active = state.snapshot?.current_node; const node = state.graph.find((item) => item.id === active);
    const activity = $('#currentActivity'); const lastStart = [...state.events].reverse().find((event) => event.type === 'node.started' && event.node === active);
    activity.innerHTML = `<span class="activity-dot"></span><div><small>${active ? `CURRENT NODE · ${escapeHtml(active)}` : 'WAITING FOR RUN'}</small><strong>${escapeHtml(lastStart?.payload?.activity || node?.title || 'Выберите или создайте draft')}</strong></div>`;
  }
  function renderNodeInspector() {
    const node = state.graph.find((item) => item.id === state.selectedNode); if (!node) return;
    $('#inspectorTitle').textContent = node.title; $('#inspectorDescription').textContent = node.description; const status = nodeState(node.id) || 'queued'; $('#inspectorStatus').textContent = status.toUpperCase(); $('#inspectorStatus').className = `chip ${status === 'active' || status === 'done' ? 'safe' : 'muted'}`;
    const latest = [...state.events].reverse().find((event) => event.node === node.id); const meta = [['Node ID', node.id], ['State', status], ['Direction', node.editable_instruction ? 'Редактируемое · до approval' : 'Системный этап · read-only'], ['Latest event', latest?.type || '—']];
    $('#inspectorMeta').innerHTML = meta.map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd>`).join('');
    $('#inspectorEvent').textContent = latest ? `${time(latest.timestamp)} · ${latest.message || latest.type}` : 'Событий для этого node пока нет.';
    const editable = Boolean(node.editable_instruction) && state.snapshot?.status === 'draft'; nodeInstruction.disabled = !editable; $('#saveNodeInstruction').disabled = !editable; $('#instructionPolicy').textContent = editable ? 'Короткое направление, max 480 символов.' : (node.editable_instruction ? 'После approval direction блокируется.' : 'Этот node детерминированный или read-only.');
    nodeInstruction.value = state.request?.operator_overrides?.[node.id] || ''; $('#instructionCount').textContent = `${nodeInstruction.value.length} / 480`;
  }

  function renderActiveRun() {
    const snapshot = state.snapshot; const requestData = state.request; setStatusBadge(snapshot?.status);
    const wrap = $('#activeRunSummary'); if (!snapshot || !requestData) { wrap.className = 'active-run-summary empty-state'; wrap.textContent = 'Создайте draft или вставьте Run ID ниже.'; ['#saveDraft','#approveRun','#cancelRun'].forEach((id) => $(id).disabled = true); return; }
    wrap.className = 'active-run-summary'; wrap.innerHTML = `<div class="summary-topic">${escapeHtml(requestData.topic)}</div><div class="summary-meta">${escapeHtml(snapshot.run_id)} · ${escapeHtml(snapshot.current_node || 'not started')}</div><div class="summary-meta">preset ${escapeHtml(requestData.preset)} · style ${escapeHtml(requestData.style || 'default')}</div>`;
    $('#saveDraft').disabled = snapshot.status !== 'draft'; $('#approveRun').disabled = snapshot.status !== 'draft'; $('#cancelRun').disabled = !['draft','validated','queued','running','retrying'].includes(snapshot.status);
  }
  function renderTimeline() {
    const list = $('#timeline'); const entries = [...state.events].sort((a, b) => (a.sequence || 0) - (b.sequence || 0));
    if (!entries.length) { list.innerHTML = '<li class="empty-state">События появятся после запуска worker.</li>'; } else list.innerHTML = entries.map((event) => `<li class="${event.level === 'error' ? 'error' : ''}"><span class="event-time">${time(event.timestamp)}</span><div><div class="event-type">${escapeHtml(event.type)}${event.node ? ` · ${escapeHtml(event.node)}` : ''}</div><div class="event-message">${escapeHtml(event.message || '—')}</div></div></li>`).join('');
    const artifacts = state.snapshot?.artifacts || []; const area = $('#artifactList');
    area.innerHTML = artifacts.length ? artifacts.map((artifact) => `<div class="artifact"><span class="artifact-icon">${artifact.kind === 'video' ? 'MP4' : 'FILE'}</span><div><strong>${escapeHtml(artifact.name)}</strong><small>${escapeHtml(artifact.mime_type)} · ${artifact.size_bytes || 0} bytes</small></div></div>`).join('') : '<p class="empty-state">Пока нет артефактов.</p>';
  }

  async function loadRun(runId = runIdInput.value.trim(), reset = true) {
    if (!runId) return; state.runId = runId; runIdInput.value = runId;
    try {
      const control = await request(`/api/studio/runs/${encodeURIComponent(runId)}/control`); state.snapshot = control.snapshot; state.request = control.request;
      const timeline = await request(`/api/studio/runs/${encodeURIComponent(runId)}/timeline?after_sequence=0&limit=500`); state.events = timeline.events || []; state.traces = timeline.traces || []; state.lastSequence = state.events.reduce((max, event) => Math.max(max, event.sequence || 0), 0);
      renderActiveRun(); renderGraph(); renderNodeInspector(); renderTimeline(); if (isActive()) enablePolling(true);
    } catch (error) { setRunResult(`Не удалось открыть run: ${error.message}`, 'error'); }
  }
  async function pollRun() {
    if (!state.runId) return;
    try {
      const [control, timeline] = await Promise.all([request(`/api/studio/runs/${encodeURIComponent(state.runId)}/control`), request(`/api/studio/runs/${encodeURIComponent(state.runId)}/timeline?after_sequence=${state.lastSequence}&limit=200`)]);
      state.snapshot = control.snapshot; state.request = control.request; const additions = timeline.events || []; if (additions.length) { state.events.push(...additions); state.lastSequence = Math.max(state.lastSequence, ...additions.map((event) => event.sequence || 0)); }
      renderActiveRun(); renderGraph(); renderNodeInspector(); renderTimeline(); if (!isActive()) enablePolling(false);
    } catch (_) { $('#refreshState').textContent = 'Переподключение к local API…'; }
  }
  function enablePolling(value) { state.polling = value; clearInterval(state.pollTimer); state.pollTimer = value ? setInterval(pollRun, 1500) : null; $('#togglePolling').textContent = `Live: ${value ? 'on' : 'off'}`; $('#refreshState').textContent = value ? 'Обновление каждые 1.5 сек.' : 'Live polling выключен'; }

  async function prepareRun(event) {
    event.preventDefault(); setRunResult('Создаём управляемый draft…');
    try {
      const data = await request('/api/studio/runs/prepare', { method: 'POST', body: JSON.stringify({ topic: $('#topic').value.trim(), preset: presetSelect.value, style: styleFamily.value || null, style_config: styleConfig(), research: $('#researchMode').value === 'on', music: $('#musicToggle').checked, sfx: $('#musicToggle').checked, agent_level: Number($('#agentLevel').value) }) });
      setRunResult(`Draft ${data.run.run_id} создан. Renderer ещё не запущен.`, 'success'); await loadRun(data.run.run_id);
    } catch (error) { setRunResult(`Draft не создан: ${error.message}`, 'error'); }
  }
  function currentDraftPatch() { return { topic: $('#topic').value.trim(), preset: presetSelect.value, style: styleFamily.value || null, style_config: styleConfig(), research: $('#researchMode').value === 'on', music: $('#musicToggle').checked, sfx: $('#musicToggle').checked, agent_level: Number($('#agentLevel').value) }; }
  async function patchDraft(onlyInstruction = false) {
    if (!state.runId || state.snapshot?.status !== 'draft') return;
    const overrides = { ...(state.request?.operator_overrides || {}) }; const node = state.selectedNode;
    if (node && state.graph.find((item) => item.id === node)?.editable_instruction) overrides[node] = nodeInstruction.value.trim();
    try { const data = await request(`/api/studio/runs/${encodeURIComponent(state.runId)}/draft`, { method: 'PATCH', body: JSON.stringify({ request_patch: onlyInstruction ? {} : currentDraftPatch(), operator_overrides: overrides }) }); state.snapshot = data.snapshot; state.request = data.request; setRunResult('Draft и разрешённые operator directions сохранены.', 'success'); renderActiveRun(); renderNodeInspector(); }
    catch (error) { setRunResult(`Не удалось сохранить правки: ${error.message}`, 'error'); }
  }
  async function approveRun() { if (!state.runId) return; try { await request(`/api/studio/runs/${encodeURIComponent(state.runId)}/approve-and-start`, { method: 'POST', body: JSON.stringify({ approved: true }) }); setRunResult('Worker запущен. Graph будет подсвечивать текущий node.', 'success'); await loadRun(state.runId); enablePolling(true); } catch (error) { setRunResult(`Запуск отклонён: ${error.message}`, 'error'); } }
  async function cancelRun() { if (!state.runId || !confirm('Остановить текущий local run?')) return; try { await request(`/api/studio/runs/${encodeURIComponent(state.runId)}/cancel`, { method: 'POST' }); setRunResult('Run отменён. Создайте новую draft-редакцию для изменений.', 'success'); await loadRun(state.runId); } catch (error) { setRunResult(`Не удалось отменить run: ${error.message}`, 'error'); } }

  function openSceneDrawer(scene) { state.selectedScene = scene; $('#drawerTitle').textContent = scene.name; $('#drawerSummary').textContent = scene.summary || '—'; $('#drawerBadges').innerHTML = [...(scene.intent_tags || []), scene.data_driven ? 'data-driven' : 'text-safe'].map((item) => `<span>${escapeHtml(item)}</span>`).join(''); const details = [['Категория', scene.category], ['Tier', scene.capability_tier], ['Поля', (scene.fields || []).join(', ') || '—'], ['Нужные данные', (scene.required_data_hints || []).join(', ') || 'не требуются'], ['Audio роли', (scene.recommended_audio_roles || []).join(', ') || 'auto']]; $('#drawerDetails').innerHTML = details.map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value || '—')}</dd>`).join(''); $('#drawerPreview').innerHTML = '<div class="preview-placeholder"><span>MSF</span><p>Render still или motion preview по запросу.</p></div>'; $('#sceneDrawer').classList.add('open'); $('#sceneDrawer').setAttribute('aria-hidden', 'false'); }
  function closeDrawer() { $('#sceneDrawer').classList.remove('open'); $('#sceneDrawer').setAttribute('aria-hidden', 'true'); }
  async function renderScenePreview(kind) {
    if (!state.selectedScene) return; const endpoint = kind === 'clip' ? '/api/preview/clip' : '/api/preview/scene'; const stage = $('#drawerPreview'); stage.innerHTML = '<div class="preview-placeholder"><span>…</span><p>Готовим preview через canonical renderer…</p></div>';
    try { const data = await request(endpoint, { method: 'POST', body: JSON.stringify({ preset: state.selectedScene.name, demo_props: true, scale: kind === 'clip' ? 0.35 : 0.5, frame_pct: 0.78 }) }); stage.innerHTML = kind === 'clip' ? `<video controls autoplay muted loop src="${escapeHtml(data.url)}"></video>` : `<img alt="Preview ${escapeHtml(state.selectedScene.name)}" src="${escapeHtml(data.url)}"/>`; }
    catch (error) { stage.innerHTML = `<div class="preview-placeholder"><span>!</span><p>${escapeHtml(error.message)}</p></div>`; }
  }

  $('#runForm').addEventListener('submit', prepareRun); $('#loadRun').addEventListener('click', () => loadRun()); $('#refreshControl').addEventListener('click', () => { loadCatalog(); if (state.runId) loadRun(state.runId); }); $('#refreshCatalog').addEventListener('click', loadCatalog); $('#saveDraft').addEventListener('click', () => patchDraft(false)); $('#saveNodeInstruction').addEventListener('click', () => patchDraft(true)); $('#approveRun').addEventListener('click', approveRun); $('#cancelRun').addEventListener('click', cancelRun); $('#togglePolling').addEventListener('click', () => enablePolling(!state.polling));
  $('#openStyleControls').addEventListener('click', () => { const controls = $('#styleControls'); controls.hidden = !controls.hidden; }); styleFamily.addEventListener('change', applyStyleFamily); ['#styleNeon','#styleBg','#styleSurface'].forEach((id) => $(id).addEventListener('input', () => { $(id).dataset.override = 'true'; refreshStyleControls(); })); $('#styleBloom').addEventListener('input', () => { $('#styleBloom').dataset.override = 'true'; refreshStyleControls(); }); nodeInstruction.addEventListener('input', () => $('#instructionCount').textContent = `${nodeInstruction.value.length} / 480`);
  let debounce = 0; $('#catalogQuery').addEventListener('input', () => { clearTimeout(debounce); debounce = setTimeout(loadCatalog, 220); }); $('#catalogTier').addEventListener('change', loadCatalog); document.querySelectorAll('[data-close-drawer]').forEach((button) => button.addEventListener('click', closeDrawer)); $('#renderStill').addEventListener('click', () => renderScenePreview('still')); $('#renderClip').addEventListener('click', () => renderScenePreview('clip')); $('#useScene').addEventListener('click', () => { if (!state.selectedScene) return; presetSelect.value = state.selectedScene.name; closeDrawer(); setRunResult(`Выбрана стартовая сцена ${state.selectedScene.name}. Сохраните draft, чтобы применить выбор.`, 'success'); document.querySelector('#control').scrollIntoView({ behavior: 'smooth', block: 'start' }); });

  Promise.all([loadCatalog(), loadStyles(), loadGraph()]).catch((error) => { $('#catalogStatus').textContent = `Local API недоступен: ${error.message}`; });
})();
