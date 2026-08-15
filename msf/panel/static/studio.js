(() => {
  'use strict';

  const $ = (selector) => document.querySelector(selector);
  const state = {
    page: 'overview', settings: null, styles: [], voices: [], audio: null, catalog: [], graph: [],
    selectedRun: null, selectedRequest: null, events: [], selectedNode: null, selectedScene: null,
    thumbnailQueue: [], queuedThumbnails: new Set(), thumbnailBusy: false, thumbnailObserver: null,
    pollTimer: null, lastSequence: 0, runHistory: [], voicePreparedPath: null,
  };

  async function api(url, options = {}) {
    const headers = { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(options.headers || {}) };
    const response = await fetch(url, { ...options, headers });
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    if (!response.ok) throw new Error(typeof payload.detail === 'object' ? JSON.stringify(payload.detail) : (payload.detail || response.statusText));
    return payload;
  }
  const esc = (value) => String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
  const time = (value) => value ? new Date(value).toLocaleString('ru-RU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—';
  const runActive = () => ['queued', 'running', 'retrying'].includes(state.selectedRun?.status);
  const activePage = () => (location.hash || '#overview').slice(1);

  function setMessage(id, text, kind = '') { const el = $(id); el.textContent = text; el.className = `notice ${kind}`; }
  function setPage(page) {
    state.page = ['overview', 'runs', 'scenes', 'voices', 'settings'].includes(page) ? page : 'overview';
    document.querySelectorAll('[data-page]').forEach((el) => { el.hidden = el.dataset.page !== state.page; });
    document.querySelectorAll('[data-page-link]').forEach((el) => el.classList.toggle('active', el.dataset.pageLink === state.page));
    const meta = { overview: ['MSF STUDIO', 'Новый запуск'], runs: ['RUN HISTORY', 'Прогоны'], scenes: ['SCENE LIBRARY', 'Сцены'], voices: ['VOICE LAB', 'Голоса'], settings: ['SETTINGS', 'Настройки'] }[state.page];
    $('#pageEyebrow').textContent = meta[0]; $('#pageTitle').textContent = meta[1];
    if (state.page === 'runs') loadRuns();
    if (state.page === 'scenes' && !state.catalog.length) loadCatalog();
    if (state.page === 'voices') { loadVoices(); loadAudio(); }
  }

  function applySettingsToComposer() {
    if (!state.settings) return;
    const settings = state.settings;
    if (settings.default_style && [...$('#styleFamily').options].some((option) => option.value === settings.default_style)) $('#styleFamily').value = settings.default_style;
    if (settings.default_voice && [...$('#runVoice').options].some((option) => option.value === settings.default_voice)) $('#runVoice').value = settings.default_voice;
    $('#agentLevel').value = String(settings.default_agent_level || 3);
    $('#researchMode').checked = Boolean(settings.default_research);
    $('#musicToggle').checked = Boolean(settings.default_music);
  }

  async function loadSettings() {
    const data = await api('/api/studio/settings'); state.settings = data.settings; state.runtime = data.runtime;
    $('#defaultVoice').replaceChildren(); state.voices.forEach((voice) => {
      const opt = document.createElement('option'); opt.value = voice.key; opt.textContent = `${voice.key}${voice.is_default ? ' · system default' : ''}`; $('#defaultVoice').appendChild(opt);
    });
    $('#defaultStyle').replaceChildren(); state.styles.forEach((style) => { const opt = document.createElement('option'); opt.value = style.id; opt.textContent = style.label; $('#defaultStyle').appendChild(opt); });
    $('#defaultVoice').value = data.settings.default_voice || data.available_voice_keys[0] || '';
    $('#defaultStyle').value = data.settings.default_style || state.styles[0]?.id || '';
    $('#defaultAgentLevel').value = String(data.settings.default_agent_level || 3);
    $('#defaultResearch').checked = Boolean(data.settings.default_research); $('#defaultMusic').checked = Boolean(data.settings.default_music);
    $('#runtimeFacts').innerHTML = Object.entries(data.runtime).map(([key, value]) => `<dt>${esc({ render: 'Кадр', audio: 'Мастеринг', storage: 'Хранилище' }[key] || key)}</dt><dd>${esc(typeof value === 'object' ? Object.values(value).join(' · ') : value)}</dd>`).join('');
    setMessage('#settingsMessage', 'Загружены текущие значения по умолчанию для новых черновиков.');
    applySettingsToComposer();
  }
  async function saveSettings(event) {
    event.preventDefault();
    try {
      const result = await api('/api/studio/settings', { method: 'PATCH', body: JSON.stringify({ default_voice: $('#defaultVoice').value || null, default_style: $('#defaultStyle').value || null, default_agent_level: Number($('#defaultAgentLevel').value), default_research: $('#defaultResearch').checked, default_music: $('#defaultMusic').checked, default_sfx: $('#defaultMusic').checked }) });
      state.settings = result.settings; applySettingsToComposer(); setMessage('#settingsMessage', 'Настройки сохранены для будущих черновиков.', 'success');
    } catch (error) { setMessage('#settingsMessage', `Не удалось сохранить: ${error.message}`, 'error'); }
  }

  async function loadStyles() {
    const data = await api('/api/studio/styles'); state.styles = data.families || [];
    $('#styleFamily').replaceChildren(); state.styles.forEach((style) => { const opt = document.createElement('option'); opt.value = style.id; opt.textContent = style.label; $('#styleFamily').appendChild(opt); });
  }
  async function loadVoices() {
    try {
      const data = await api('/api/voices'); state.voices = data.items || [];
      $('#runVoice').replaceChildren(); state.voices.filter((voice) => voice.usable).forEach((voice) => { const opt = document.createElement('option'); opt.value = voice.key; opt.textContent = `${voice.key} · ${voice.mode || 'reference'}`; $('#runVoice').appendChild(opt); });
      if (!$('#runVoice').options.length) { const opt = document.createElement('option'); opt.value = ''; opt.textContent = 'Нет готовых голосов'; $('#runVoice').appendChild(opt); }
      renderVoiceCatalog();
      if (state.settings) loadSettings();
    } catch (error) { $('#voiceCatalog').textContent = `Каталог голосов недоступен: ${error.message}`; }
  }
  function renderVoiceCatalog() {
    const root = $('#voiceCatalog');
    if (!state.voices.length) { root.textContent = 'В каталоге пока нет голосов.'; return; }
    root.innerHTML = state.voices.map((voice) => { const status = !voice.exists ? 'Файл не найден' : !voice.icl ? 'Нужен текст' : 'Готов'; const tone = voice.usable ? 'completed' : 'failed'; return `<article class="voice-row"><header><b>${esc(voice.key)}</b><span class="status-badge ${tone}">${status}</span></header><p>${esc(voice.mode || '—')} · ${voice.duration_sec || '—'} c · ${esc(voice.lang || '—')}${voice.icl ? ' · текст проверен' : ''}</p><p>${esc(voice.notes || '')}</p><div class="voice-actions"><button class="button button-secondary" data-voice-preview="${esc(voice.key)}" ${voice.usable ? '' : 'disabled'}>Слушать референс</button><button class="button button-secondary" data-voice-sample="${esc(voice.key)}" ${voice.usable ? '' : 'disabled'}>Проверить озвучку</button><button class="button button-secondary" data-voice-use="${esc(voice.key)}" ${voice.usable ? '' : 'disabled'}>Выбрать для запуска</button></div></article>`; }).join('');
    root.querySelectorAll('[data-voice-preview]').forEach((button) => button.addEventListener('click', () => previewVoice(button.dataset.voicePreview)));
    root.querySelectorAll('[data-voice-sample]').forEach((button) => button.addEventListener('click', () => synthesizeVoiceSample(button)));
    root.querySelectorAll('[data-voice-use]').forEach((button) => button.addEventListener('click', () => { $('#runVoice').value = button.dataset.voiceUse; location.hash = '#overview'; }));
  }
  async function previewVoice(voice) {
    const item = state.voices.find((candidate) => candidate.key === voice);
    if (!item?.reference_preview_url) { setMessage('#voiceMessage', 'Reference audio для этого голоса недоступен.', 'error'); return; }
    try { const audio = new Audio(item.reference_preview_url); await audio.play(); }
    catch (error) { setMessage('#voiceMessage', `Не удалось воспроизвести референс: ${error.message}`, 'error'); }
  }

  async function synthesizeVoiceSample(button) {
    const voice = button.dataset.voiceSample;
    const original = button.textContent;
    button.disabled = true;
    button.textContent = 'Генерируем…';
    try {
      const result = await api('/api/preview/voice', { method: 'POST', body: JSON.stringify({ voice }) });
      const audio = new Audio(result.url);
      await audio.play();
      setMessage('#voiceMessage', `Проверочная фраза создана за ${result.synth_sec} с (${result.mode}).`, 'success');
    } catch (error) { setMessage('#voiceMessage', `Не удалось синтезировать проверочную фразу: ${error.message}`, 'error'); }
    finally { button.disabled = false; button.textContent = original; }
  }

  async function measureVoice() {
    const path = $('#voicePath').value.trim(); if (!path) { setMessage('#voiceMessage', 'Укажите путь к записи.', 'error'); return; }
    try {
      $('#voiceMeasurements').textContent = 'Измеряем запись…'; const data = await api('/api/voices/measure', { method: 'POST', body: JSON.stringify({ path }) });
      $('#voiceCleanControls').disabled = false; state.voicePreparedPath = null;
      const stats = data.stats || {}; const findings = (data.findings || []).map((item) => `<div class="finding ${esc(item.level)}">${esc(item.text)}</div>`).join('');
      $('#voiceMeasurements').innerHTML = `<dl><dt>Длительность</dt><dd>${esc(stats.duration_sec)} c</dd><dt>SNR</dt><dd>${esc(stats.snr_db)} dB</dd><dt>Частота</dt><dd>${esc(stats.sample_rate)} Гц</dd><dt>Клиппинг</dt><dd>${esc(stats.clipped_samples)}</dd></dl>${findings || '<div class="finding info">Явных проблем не найдено.</div>'}`;
      $('#denoiseVoice').checked = Boolean(data.recommend_denoise); $('#trimVoice').checked = Boolean(data.recommend_trim); $('#voiceStep').textContent = '2 · подготовка';
    } catch (error) { $('#voiceMeasurements').textContent = `Проверка не выполнена: ${error.message}`; }
  }
  async function prepareVoice() {
    const path = $('#voicePath').value.trim(); if (!path) return;
    try {
      $('#voicePrepResult').hidden = false; $('#voicePrepResult').textContent = 'Создаём подготовленную копию…';
      const data = await api('/api/voices/prepare', { method: 'POST', body: JSON.stringify({ path, denoise: $('#denoiseVoice').checked, trim_silence: $('#trimVoice').checked, normalize: $('#normalizeVoice').checked, denoise_strength: Number($('#denoiseStrength').value) }) });
      state.voicePreparedPath = data.out_path; $('#voicePrepResult').innerHTML = `<b>Готово:</b> ${esc(data.out_path)}<br/>SNR: ${esc(data.before.snr_db)} → ${esc(data.after.snr_db)} dB (${esc(data.snr_gain_db >= 0 ? '+' : '')}${esc(data.snr_gain_db)} dB)<br/><small>${esc((data.applied || []).join(' · '))}</small>`; $('#voiceStep').textContent = '3 · расшифровка';
    } catch (error) { $('#voicePrepResult').textContent = `Очистка не выполнена: ${error.message}`; }
  }
  async function transcribeVoice() {
    const path = state.voicePreparedPath || $('#voicePath').value.trim(); if (!path) { setMessage('#voiceMessage', 'Сначала укажите и проверьте запись.', 'error'); return; }
    try { $('#transcriptMeta').textContent = 'Распознаём речь…'; const data = await api('/api/voices/transcribe', { method: 'POST', body: JSON.stringify({ path, language: $('#voiceLanguage').value }) }); $('#voiceTranscript').value = data.text || ''; $('#transcriptMeta').textContent = `Модель ${data.model} · ${data.device} · уверенность ${data.mean_logprob}; обязательно вычитайте текст.`; $('#voiceStep').textContent = '4 · вычитка и сохранение'; }
    catch (error) { $('#transcriptMeta').textContent = `Не удалось распознать: ${error.message}`; }
  }
  async function registerVoice() {
    const path = state.voicePreparedPath || $('#voicePath').value.trim(); const key = $('#voiceKey').value.trim(); const ref_text = $('#voiceTranscript').value.trim();
    if (!path || !key || !ref_text) { setMessage('#voiceMessage', 'Нужны путь, ключ и вычитанный текст референса.', 'error'); return; }
    try { const result = await api('/api/voices', { method: 'POST', body: JSON.stringify({ key, ref_audio: path, ref_text, lang: $('#voiceLanguage').value, notes: $('#voiceNotes').value.trim() }) }); setMessage('#voiceMessage', `Голос ${result.key} добавлен в каталог.`, 'success'); $('#voiceKey').value = ''; $('#voiceNotes').value = ''; await loadVoices(); }
    catch (error) { setMessage('#voiceMessage', `Не удалось добавить голос: ${error.message}`, 'error'); }
  }
  async function loadAudio() {
    try { const data = await api('/api/audio'); state.audio = data; renderAudio(); } catch (error) { $('#audioLibrary').textContent = `Библиотека звука недоступна: ${error.message}`; }
  }
  function renderAudio() {
    const section = (title, items, kind) => `<div class="audio-section"><h3>${title}</h3>${items.slice(0, 12).map((item) => `<div class="audio-row"><div><b>${esc(item.name)}</b><small>${esc(item.character || item.summary || item.family || '')}</small></div><button class="button button-secondary" data-audio-kind="${kind}" data-audio-name="${esc(item.name)}">▶</button></div>`).join('')}</div>`;
    $('#audioLibrary').innerHTML = section('Музыка', state.audio.music || [], 'music') + section('SFX', state.audio.sfx || [], 'sfx');
    $('#audioLibrary').querySelectorAll('[data-audio-name]').forEach((button) => button.addEventListener('click', async () => { try { const endpoint = button.dataset.audioKind === 'music' ? `/api/preview/music/${encodeURIComponent(button.dataset.audioName)}` : `/api/preview/sfx/${encodeURIComponent(button.dataset.audioName)}`; const data = await api(endpoint); const audio = new Audio(data.url); await audio.play(); } catch (_) {} }));
  }

  async function loadGraph() { const data = await api('/api/studio/control-room/graph'); state.graph = data.nodes || []; if (!state.selectedNode && state.graph[0]) state.selectedNode = state.graph[0].id; renderGraph(); }
  function nodeState(id) { if (state.selectedRun?.current_node === id) return 'active'; const relevant = state.events.filter((event) => event.node === id); const last = relevant[relevant.length - 1]; if (!last) return ''; return last.type === 'node.failed' ? 'failed' : last.type === 'node.completed' ? 'done' : ''; }
  function renderGraph() {
    const root = $('#pipelineGraph'); root.replaceChildren(); state.graph.forEach((node, index) => { const button = document.createElement('button'); button.type = 'button'; button.className = `pipeline-node ${nodeState(node.id)} ${state.selectedNode === node.id ? 'selected' : ''}`; button.innerHTML = `<small>${String(index + 1).padStart(2, '0')} · ${esc(node.label)}</small><b>${esc(node.title)}</b><span>${esc(node.description)}</span>`; button.addEventListener('click', () => { state.selectedNode = node.id; renderGraph(); renderNode(); }); root.appendChild(button); }); renderNode();
    const current = state.graph.find((node) => node.id === state.selectedRun?.current_node); const started = [...state.events].reverse().find((event) => event.type === 'node.started' && event.node === state.selectedRun?.current_node); $('#pipelineActivity').textContent = current ? (started?.payload?.activity || current.title) : 'Выберите или создайте прогон';
  }
  function renderNode() {
    const node = state.graph.find((item) => item.id === state.selectedNode); if (!node) return; const latest = [...state.events].reverse().find((event) => event.node === node.id); const editable = Boolean(node.editable_instruction) && state.selectedRun?.status === 'draft';
    $('#nodeKicker').textContent = `NODE · ${node.label}`; $('#nodeTitle').textContent = node.title; $('#nodeDescription').textContent = node.description; $('#nodeEvent').textContent = latest ? `${time(latest.timestamp)} · ${latest.message || latest.type}` : 'Событий для этого этапа пока нет.';
    $('#nodeDirection').hidden = !node.editable_instruction; if (node.editable_instruction) { $('#nodeInstruction').disabled = !editable; $('#saveNodeInstruction').disabled = !editable; $('#nodeInstruction').value = state.selectedRequest?.operator_overrides?.[node.id] || ''; $('#instructionCount').textContent = `${$('#nodeInstruction').value.length} / 480`; }
  }
  async function prepareRun(event) {
    event.preventDefault();
    try { const data = await api('/api/studio/runs/prepare', { method: 'POST', body: JSON.stringify({ topic: $('#topic').value.trim(), preset: $('#preset').value, style: $('#styleFamily').value || null, voice: $('#runVoice').value || null, research: $('#researchMode').checked, music: $('#musicToggle').checked, sfx: $('#musicToggle').checked, agent_level: Number($('#agentLevel').value) }) }); setMessage('#runMessage', `Черновик ${data.run.run_id} создан. Проверьте этапы и затем запустите.`, 'success'); await loadRun(data.run.run_id); }
    catch (error) { setMessage('#runMessage', `Черновик не создан: ${error.message}`, 'error'); }
  }
  function draftPatch() { return { topic: $('#topic').value.trim(), preset: $('#preset').value, style: $('#styleFamily').value || null, voice: $('#runVoice').value || null, research: $('#researchMode').checked, music: $('#musicToggle').checked, sfx: $('#musicToggle').checked, agent_level: Number($('#agentLevel').value) }; }
  async function loadRun(runId) {
    try { const control = await api(`/api/studio/runs/${encodeURIComponent(runId)}/control`); const timeline = await api(`/api/studio/runs/${encodeURIComponent(runId)}/timeline?after_sequence=0&limit=500`); state.selectedRun = control.snapshot; state.selectedRequest = control.request; state.events = timeline.events || []; state.lastSequence = state.events.reduce((max, event) => Math.max(max, event.sequence || 0), 0); renderCurrentRun(); renderGraph(); renderTimeline(); if (runActive()) enablePolling(true); }
    catch (error) { setMessage('#runMessage', `Не удалось открыть прогон: ${error.message}`, 'error'); }
  }
  function renderCurrentRun() {
    const run = state.selectedRun; const request = state.selectedRequest; const badge = $('#runStatus'); if (!run || !request) { $('#currentRun').textContent = 'Выберите прогон в истории или создайте новый черновик.'; badge.textContent = 'Нет выбора'; badge.className = 'status-badge muted'; return; }
    badge.textContent = run.status; badge.className = `status-badge ${run.status}`; $('#currentRun').innerHTML = `<b>${esc(request.topic)}</b><p class="helper">${esc(run.run_id)} · ${esc(request.preset)} · ${esc(request.style || 'default')} · ${esc(request.voice || 'default voice')}</p>`;
    const draft = run.status === 'draft'; $('#saveDraft').disabled = !draft; $('#approveRun').disabled = !draft; $('#cancelRun').disabled = !['draft', 'validated', 'queued', 'running', 'retrying'].includes(run.status); $('#openCurrentRun').disabled = false;
    if (draft) { $('#topic').value = request.topic; $('#preset').value = request.preset; $('#styleFamily').value = request.style || $('#styleFamily').value; if (request.voice) $('#runVoice').value = request.voice; $('#researchMode').checked = request.research; $('#musicToggle').checked = request.music; $('#agentLevel').value = request.agent_level; }
  }
  async function saveDraft(onlyDirection = false) {
    if (!state.selectedRun || state.selectedRun.status !== 'draft') return;
    const override = {}; const node = state.graph.find((item) => item.id === state.selectedNode); if (onlyDirection && node?.editable_instruction) override[node.id] = $('#nodeInstruction').value.trim();
    try { const data = await api(`/api/studio/runs/${encodeURIComponent(state.selectedRun.run_id)}/draft`, { method: 'PATCH', body: JSON.stringify({ request_patch: onlyDirection ? {} : draftPatch(), operator_overrides: override }) }); state.selectedRun = data.snapshot; state.selectedRequest = data.request; renderCurrentRun(); renderGraph(); setMessage('#runMessage', onlyDirection ? 'Направление сохранено в черновике.' : 'Черновик сохранён.', 'success'); }
    catch (error) { setMessage('#runMessage', `Не удалось сохранить: ${error.message}`, 'error'); }
  }
  async function approveRun() { if (!state.selectedRun) return; try { const data = await api(`/api/studio/runs/${encodeURIComponent(state.selectedRun.run_id)}/approve-and-start`, { method: 'POST', body: JSON.stringify({ approved: true }) }); state.selectedRun = data.run; renderCurrentRun(); renderGraph(); enablePolling(true); setMessage('#runMessage', 'Worker запущен. События появятся в разделе «Прогоны».', 'success'); } catch (error) { setMessage('#runMessage', `Не удалось запустить: ${error.message}`, 'error'); } }
  async function cancelRun() { if (!state.selectedRun) return; try { const data = await api(`/api/studio/runs/${encodeURIComponent(state.selectedRun.run_id)}/cancel`, { method: 'POST' }); state.selectedRun = data.run; renderCurrentRun(); renderGraph(); enablePolling(false); } catch (error) { setMessage('#runMessage', `Не удалось отменить: ${error.message}`, 'error'); } }
  function renderTimeline() { const list = $('#timeline'); $('#timelineState').textContent = state.selectedRun ? `${state.selectedRun.run_id} · ${state.selectedRun.status}` : 'Нет выбранного прогона'; if (!state.events.length) { list.innerHTML = '<li class="empty-state">Событий пока нет.</li>'; } else list.innerHTML = state.events.map((event) => `<li><time>${esc(time(event.timestamp))}</time><div><strong>${esc(event.type)}${event.node ? ` · ${esc(event.node)}` : ''}</strong><p>${esc(event.message || '—')}</p></div></li>`).join(''); const artifacts = state.selectedRun?.artifacts || []; $('#artifactList').innerHTML = artifacts.length ? artifacts.map((item) => `<div class="artifact"><div><b>${esc(item.name)}</b><small>${esc(item.kind)} · ${esc(item.mime_type)}</small></div><span>${esc(item.size_bytes || 0)} B</span></div>`).join('') : 'Артефакты появятся после работы pipeline.'; }
  async function pollRun() { if (!state.selectedRun || !runActive()) return; try { const [control, timeline] = await Promise.all([api(`/api/studio/runs/${encodeURIComponent(state.selectedRun.run_id)}/control`), api(`/api/studio/runs/${encodeURIComponent(state.selectedRun.run_id)}/timeline?after_sequence=${state.lastSequence}&limit=200`)]); state.selectedRun = control.snapshot; state.selectedRequest = control.request; const additions = timeline.events || []; state.events.push(...additions); if (additions.length) state.lastSequence = Math.max(state.lastSequence, ...additions.map((event) => event.sequence || 0)); renderCurrentRun(); renderGraph(); renderTimeline(); if (!runActive()) { enablePolling(false); loadRuns(); } } catch (_) {} }
  function enablePolling(on) { clearInterval(state.pollTimer); state.pollTimer = on ? setInterval(pollRun, 1500) : null; }

  async function loadRuns() { try { const status = $('#runStatusFilter').value; const data = await api(`/api/studio/runs?limit=80${status ? `&status=${encodeURIComponent(status)}` : ''}`); state.runHistory = data.items || []; renderRuns(); } catch (error) { $('#runTable').textContent = `Не удалось загрузить историю: ${error.message}`; } }
  function renderRuns() { const root = $('#runTable'); if (!state.runHistory.length) { root.textContent = 'Прогонов по этому фильтру пока нет.'; return; } root.innerHTML = `<table><thead><tr><th>Тема</th><th>Статус</th><th>Создан</th><th>Стиль / голос</th><th>Артефакты</th></tr></thead><tbody>${state.runHistory.map((run) => `<tr data-run-id="${esc(run.run_id)}"><td><div class="run-topic">${esc(run.topic || '—')}</div><div class="run-meta">${esc(run.run_id)} · ${esc(run.preset || '—')}</div></td><td><span class="status-badge ${esc(run.status)}">${esc(run.status)}</span></td><td>${esc(time(run.created_at))}</td><td>${esc(run.style || 'default')}<div class="run-meta">${esc(run.voice || 'default voice')}</div></td><td>${esc(run.artifacts_count || 0)}</td></tr>`).join('')}</tbody></table>`; root.querySelectorAll('[data-run-id]').forEach((row) => row.addEventListener('click', () => { location.hash = '#runs'; loadRun(row.dataset.runId); })); }

  function renderCatalog() { const root = $('#catalogCards'); root.replaceChildren(); if (!state.catalog.length) { root.innerHTML = '<p class="empty-state">По этому запросу сцен не найдено.</p>'; return; } state.catalog.forEach((scene) => { const card = document.createElement('button'); card.type = 'button'; card.className = `scene-card ${state.selectedScene?.name === scene.name ? 'selected' : ''}`; card.dataset.preset = scene.name; card.innerHTML = `<div class="scene-image"><span>Превью</span></div><div class="scene-body"><small>${esc(scene.category || 'general')}</small><strong>${esc(scene.name)}</strong><p>${esc(scene.summary || '')}</p></div>`; card.addEventListener('click', () => selectScene(scene)); root.appendChild(card); }); observeThumbnails(); }
  async function loadCatalog() { try { const params = new URLSearchParams({ query: $('#catalogQuery').value.trim(), tier: $('#catalogTier').value, limit: '80' }); const data = await api(`/api/studio/catalog?${params}`); state.catalog = data.items || []; $('#preset').replaceChildren(); state.catalog.forEach((scene) => { const option = document.createElement('option'); option.value = scene.name; option.textContent = scene.name; $('#preset').appendChild(option); }); applySettingsToComposer(); renderCatalog(); } catch (error) { $('#catalogCards').textContent = `Каталог недоступен: ${error.message}`; } }
  function setThumbnail(preset, url, cached) { document.querySelectorAll(`.scene-card[data-preset="${CSS.escape(preset)}"] .scene-image`).forEach((root) => { root.innerHTML = `<img alt="${esc(preset)} preview" src="${esc(url)}"/><span class="cache-pill">${cached ? 'Cached' : 'Rendered'}</span>`; }); }
  async function fetchThumbnail(preset) { try { const cached = await api(`/api/preview/thumbnail/${encodeURIComponent(preset)}`); setThumbnail(preset, cached.url, true); } catch (error) { if (String(error.message).includes('thumbnail not cached')) queueThumbnail(preset); } }
  function queueThumbnail(preset) { if (state.queuedThumbnails.has(preset)) return; state.queuedThumbnails.add(preset); state.thumbnailQueue.push(preset); runThumbnailQueue(); }
  async function runThumbnailQueue() { if (state.thumbnailBusy || !state.thumbnailQueue.length) return; state.thumbnailBusy = true; const preset = state.thumbnailQueue.shift(); try { const result = await api('/api/preview/thumbnail', { method: 'POST', body: JSON.stringify({ preset, demo_props: true }) }); setThumbnail(preset, result.url, result.cached); } catch (_) {} finally { state.thumbnailBusy = false; if (state.thumbnailQueue.length) setTimeout(runThumbnailQueue, 80); } }
  function observeThumbnails() { state.thumbnailObserver?.disconnect(); state.thumbnailObserver = new IntersectionObserver((entries) => entries.forEach((entry) => { if (entry.isIntersecting) { state.thumbnailObserver.unobserve(entry.target); fetchThumbnail(entry.target.dataset.preset); } }), { root: null, rootMargin: '180px 0px' }); document.querySelectorAll('.scene-card').forEach((card) => state.thumbnailObserver.observe(card)); }
  async function selectScene(scene) { state.selectedScene = scene; renderCatalog(); $('#sceneTitle').textContent = scene.name; $('#sceneInfo').innerHTML = `<p>${esc(scene.summary || '')}</p><dl class="scene-details"><dt>Категория</dt><dd>${esc(scene.category || '—')}</dd><dt>Tier</dt><dd>${esc(scene.tier || 'preset')}</dd><dt>Нужные данные</dt><dd>${esc((scene.required_data_hints || []).join(', ') || 'Нет')}</dd><dt>Audio roles</dt><dd>${esc((scene.recommended_audio_roles || []).join(', ') || 'Auto')}</dd></dl>`; $('#scenePreview').className = 'preview-empty'; $('#scenePreview').textContent = 'Загружаем cached preview…'; $('#renderStill').disabled = false; $('#renderClip').disabled = false; $('#useScene').disabled = false; try { const cached = await api(`/api/preview/thumbnail/${encodeURIComponent(scene.name)}`); $('#scenePreview').className = 'preview-media'; $('#scenePreview').innerHTML = `<img alt="${esc(scene.name)} preview" src="${esc(cached.url)}"/>`; } catch (_) { $('#scenePreview').textContent = 'Для этой сцены ещё нет превью. Нажмите «Обновить превью».'; } }
  async function renderSelectedStill() { if (!state.selectedScene) return; $('#scenePreview').textContent = 'Рендерим preview…'; try { const data = await api('/api/preview/scene', { method: 'POST', body: JSON.stringify({ preset: state.selectedScene.name, demo_props: true, scale: .5 }) }); $('#scenePreview').className = 'preview-media'; $('#scenePreview').innerHTML = `<img alt="${esc(data.preset)} preview" src="${esc(data.url)}"/>`; } catch (error) { $('#scenePreview').textContent = `Preview не создан: ${error.message}`; } }
  async function renderSelectedClip() { if (!state.selectedScene) return; $('#scenePreview').textContent = 'Рендерим короткий motion preview…'; try { const data = await api('/api/preview/clip', { method: 'POST', body: JSON.stringify({ preset: state.selectedScene.name, demo_props: true, scale: .35, to_frame: 80 }) }); $('#scenePreview').className = 'preview-media'; $('#scenePreview').innerHTML = `<video controls autoplay muted src="${esc(data.url)}"></video>`; } catch (error) { $('#scenePreview').textContent = `Motion preview не создан: ${error.message}`; } }

  async function refreshAll() { try { await Promise.all([loadGraph(), loadStyles(), loadVoices(), loadSettings(), loadCatalog()]); $('#systemStatus').textContent = 'Система доступна'; } catch (error) { $('#systemStatus').textContent = `Проверьте локальный сервис`; } }
  function bind() {
    window.addEventListener('hashchange', () => setPage(activePage()));
    $('#runForm').addEventListener('submit', prepareRun); $('#saveDraft').addEventListener('click', () => saveDraft(false)); $('#saveNodeInstruction').addEventListener('click', () => saveDraft(true)); $('#approveRun').addEventListener('click', approveRun); $('#cancelRun').addEventListener('click', cancelRun); $('#openCurrentRun').addEventListener('click', () => { location.hash = '#runs'; }); $('#nodeInstruction').addEventListener('input', () => { $('#instructionCount').textContent = `${$('#nodeInstruction').value.length} / 480`; });
    $('#refreshCatalog').addEventListener('click', loadCatalog); $('#renderStill').addEventListener('click', renderSelectedStill); $('#renderClip').addEventListener('click', renderSelectedClip); $('#useScene').addEventListener('click', () => { if (!state.selectedScene) return; $('#preset').value = state.selectedScene.name; location.hash = '#overview'; setMessage('#runMessage', `Сцена ${state.selectedScene.name} выбрана для следующего черновика.`, 'success'); });
    $('#refreshRuns').addEventListener('click', loadRuns); $('#runStatusFilter').addEventListener('change', loadRuns); $('#settingsForm').addEventListener('submit', saveSettings); $('#refreshVoices').addEventListener('click', loadVoices); $('#measureVoice').addEventListener('click', measureVoice); $('#prepareVoice').addEventListener('click', prepareVoice); $('#transcribeVoice').addEventListener('click', transcribeVoice); $('#registerVoice').addEventListener('click', registerVoice); $('#denoiseStrength').addEventListener('input', () => { $('#denoiseStrengthValue').textContent = $('#denoiseStrength').value; }); $('#refreshAll').addEventListener('click', refreshAll);
  }
  async function init() { bind(); try { await Promise.all([loadGraph(), loadStyles(), loadVoices(), loadCatalog()]); await loadSettings(); $('#systemStatus').textContent = 'Система доступна'; } catch (error) { $('#systemStatus').textContent = 'Не удалось загрузить данные'; } setPage(activePage()); }
  document.addEventListener('DOMContentLoaded', init);
})();
