(() => {
  'use strict';

  const $ = (selector) => document.querySelector(selector);
  const catalogQuery = $('#catalogQuery');
  const catalogTier = $('#catalogTier');
  const catalogCards = $('#catalogCards');
  const presetSelect = $('#preset');
  const catalogStatus = $('#catalogStatus');
  const catalogTotal = $('#catalogTotal');
  const researchJson = $('#researchJson');
  const researchState = $('#researchState');
  const researchResult = $('#researchResult');
  const storyboardJson = $('#storyboardJson');
  const storyboardResult = $('#storyboardResult');
  const storyboardCount = $('#storyboardCount');
  const runResult = $('#runResult');
  const runIdInput = $('#runIdInput');
  const runSnapshot = $('#runSnapshot');
  const timeline = $('#timeline');
  const styleFamily = $('#styleFamily');
  const styleNeon = $('#styleNeon');
  const styleBg = $('#styleBg');
  const styleSurface = $('#styleSurface');
  const styleBloom = $('#styleBloom');
  const styleBloomValue = $('#styleBloomValue');
  const styleSummary = $('#styleSummary');
  const styleDescription = $('#styleDescription');
  const styleConfigPreview = $('#styleConfigPreview');

  let catalogItems = [];
  let styleFamilies = [];

  const sampleResearch = {
    research_id: 'research_studio_demo_ollama',
    topic: 'Локальный запуск LLM через Ollama',
    sources: [{
      source_id: 'src_ollama_quickstart',
      url: 'https://docs.ollama.com/quickstart',
      title: 'Ollama Quickstart',
      publisher: 'Ollama',
      source_type: 'official_docs',
      excerpt: 'Ollama provides a local runtime and API for running supported models on a computer.'
    }, {
      source_id: 'src_ollama_api',
      url: 'https://docs.ollama.com/api/introduction',
      title: 'Ollama API Introduction',
      publisher: 'Ollama',
      source_type: 'official_docs',
      excerpt: 'The Ollama API documentation describes local endpoints for model generation and management.'
    }],
    claims: [{
      claim_id: 'claim_ollama_local',
      statement: 'Ollama documents a local runtime and API for running supported models on a computer.',
      source_ids: ['src_ollama_quickstart', 'src_ollama_api'],
      confidence: 'high',
      claim_type: 'fact',
      freshness_days: 0
    }],
    summary: 'Демо pack для проверки evidence-first workflow.'
  };

  async function request(url, options = {}) {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    });
    const payload = await response.json().catch(() => ({ message: response.statusText }));
    if (!response.ok) {
      const detail = typeof payload.detail === 'object' ? JSON.stringify(payload.detail) : (payload.detail || payload.message || response.statusText);
      throw new Error(detail);
    }
    return payload;
  }

  function parseJson(text, label) {
    if (!text.trim()) throw new Error(`${label}: вставьте JSON.`);
    try { return JSON.parse(text); } catch (error) { throw new Error(`${label}: некорректный JSON (${error.message}).`); }
  }

  function setGateState(element, text, state = '') {
    element.textContent = text;
    element.className = `gate-state ${state}`;
  }

  function diagnostics(container, items, successText) {
    container.replaceChildren();
    if (!items || items.length === 0) {
      if (successText) {
        const line = document.createElement('div');
        line.className = 'diagnostic ok';
        line.textContent = successText;
        container.appendChild(line);
      }
      return;
    }
    items.forEach((item) => {
      const line = document.createElement('div');
      line.className = `diagnostic ${item.severity === 'error' ? 'error' : ''}`;
      const prefix = item.code ? `[${item.code}] ` : '';
      line.textContent = `${prefix}${item.message || String(item)}`;
      container.appendChild(line);
    });
  }

  function setRunResult(text, type = 'empty') {
    runResult.textContent = text;
    runResult.className = `run-result ${type}`;
  }

  function renderCatalog(items) {
    catalogCards.replaceChildren();
    if (items.length === 0) {
      catalogCards.innerHTML = '<p class="empty-state">Ничего не найдено. Измените intent или поисковую фразу.</p>';
      return;
    }
    const template = $('#catalogCardTemplate');
    items.forEach((scene) => {
      const fragment = template.content.cloneNode(true);
      const card = fragment.querySelector('.scene-card');
      fragment.querySelector('.scene-category').textContent = scene.category;
      fragment.querySelector('strong').textContent = scene.name;
      fragment.querySelector('p').textContent = scene.summary;
      const tags = fragment.querySelector('.scene-tags');
      scene.intent_tags.slice(0, 3).forEach((tag) => {
        const badge = document.createElement('span');
        badge.textContent = tag;
        tags.appendChild(badge);
      });
      const helper = scene.data_driven
        ? `Данные: ${(scene.required_data_hints || []).join(', ') || 'обязательны'}`
        : `Audio: ${(scene.recommended_audio_roles || []).slice(0, 2).join(', ') || 'default'}`;
      fragment.querySelector('small').textContent = helper;
      card.title = `Выбрать ${scene.name} как основную сцену`;
      card.addEventListener('click', () => selectPreset(scene.name));
      catalogCards.appendChild(fragment);
    });
  }

  function selectPreset(name) {
    const option = [...presetSelect.options].find((item) => item.value === name);
    if (option) {
      presetSelect.value = name;
      presetSelect.focus();
      setRunResult(`Выбрана сцена ${name}. Заполните brief и подготовьте run.`, 'empty');
    }
  }

  async function loadCatalog() {
    catalogStatus.textContent = 'Обновляем live catalog…';
    try {
      const params = new URLSearchParams({ query: catalogQuery.value.trim(), tier: catalogTier.value, limit: '50' });
      const data = await request(`/api/studio/catalog?${params}`);
      catalogItems = data.items || [];
      renderCatalog(catalogItems);
      catalogTotal.textContent = `${data.total} сцен`;
      catalogStatus.textContent = `Live catalog: ${data.total} доступных сцен`;
      const selected = presetSelect.value;
      presetSelect.replaceChildren();
      catalogItems.forEach((scene) => {
        const option = document.createElement('option');
        option.value = scene.name;
        option.textContent = scene.name;
        presetSelect.appendChild(option);
      });
      if ([...presetSelect.options].some((item) => item.value === selected)) presetSelect.value = selected;
    } catch (error) {
      catalogCards.innerHTML = `<p class="empty-state">Catalog unavailable: ${escapeHtml(error.message)}</p>`;
      catalogStatus.textContent = 'Catalog недоступен';
      catalogTotal.textContent = 'error';
    }
  }

  function selectedStyleFamily() {
    return styleFamilies.find((item) => item.id === styleFamily.value) || styleFamilies[0] || null;
  }

  function styleConfig() {
    const palette = {};
    [[styleNeon, 'neon'], [styleBg, 'bg'], [styleSurface, 'surface']].forEach(([input, key]) => {
      if (input.dataset.override === 'true') palette[key] = input.value;
    });
    const effects = {};
    if (styleBloom.dataset.override === 'true') effects.bloom = Number(styleBloom.value);
    const config = {};
    if (Object.keys(palette).length) config.palette = palette;
    if (Object.keys(effects).length) config.effects = effects;
    return config;
  }

  function refreshStyleControls() {
    const family = selectedStyleFamily();
    const config = styleConfig();
    styleBloomValue.textContent = Number(styleBloom.value).toFixed(2);
    if (!family) {
      styleSummary.textContent = 'Style catalog недоступен';
      styleConfigPreview.textContent = 'styleConfig: —';
      return;
    }
    styleSummary.textContent = family.label;
    styleDescription.textContent = family.summary;
    styleConfigPreview.textContent = `style: ${family.id}\nstyleConfig: ${JSON.stringify(config)}`;
  }

  function applyStyleFamily() {
    const family = selectedStyleFamily();
    const defaults = (family && family.defaults) || {};
    const palette = defaults.palette || {};
    [[styleNeon, palette.neon], [styleBg, palette.bg], [styleSurface, palette.surface]].forEach(([input, value]) => {
      if (value) input.value = value;
      input.dataset.override = 'false';
    });
    if (defaults.effects && typeof defaults.effects.bloom === 'number') styleBloom.value = defaults.effects.bloom;
    styleBloom.dataset.override = 'false';
    refreshStyleControls();
  }

  async function loadStyles() {
    try {
      const data = await request('/api/studio/styles');
      styleFamilies = data.families || [];
      styleFamily.replaceChildren();
      styleFamilies.forEach((family) => {
        const option = document.createElement('option');
        option.value = family.id;
        option.textContent = family.label;
        styleFamily.appendChild(option);
      });
      if ([...styleFamily.options].some((item) => item.value === 'llm_hubs_neon')) styleFamily.value = 'llm_hubs_neon';
      applyStyleFamily();
    } catch (error) {
      styleSummary.textContent = `Style catalog недоступен: ${error.message}`;
      styleConfigPreview.textContent = 'styleConfig: unavailable';
    }
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
  }

  async function validateEvidence() {
    researchResult.replaceChildren();
    try {
      const research = parseJson(researchJson.value, 'Research pack');
      const data = await request('/api/studio/research/validate', { method: 'POST', body: JSON.stringify({ research }) });
      setGateState(researchState, data.valid ? `Evidence OK · ${data.research_id}` : 'Evidence содержит warnings', data.valid ? 'ok' : 'bad');
      diagnostics(researchResult, (data.warnings || []).map((message) => ({ severity: 'warning', message })), data.valid ? 'Evidence pack прошёл fail-closed policy.' : 'Проверьте warnings перед написанием facts.');
      return { research, valid: data.valid };
    } catch (error) {
      setGateState(researchState, 'Evidence не прошёл', 'bad');
      diagnostics(researchResult, [{ severity: 'error', code: 'research.invalid', message: error.message }]);
      throw error;
    }
  }

  function updateStoryboardCount() {
    try {
      const value = parseJson(storyboardJson.value, 'Storyboard');
      storyboardCount.textContent = `${Array.isArray(value.scenes) ? value.scenes.length : 0} сцен`;
    } catch (_) {
      storyboardCount.textContent = 'JSON не прочитан';
    }
  }

  async function validateStoryboard(save = false) {
    storyboardResult.replaceChildren();
    try {
      const storyboard = parseJson(storyboardJson.value, 'Storyboard');
      let research = null;
      if (researchJson.value.trim()) research = parseJson(researchJson.value, 'Research pack');
      const endpoint = save ? '/api/studio/storyboards/save' : '/api/studio/storyboards/validate';
      const data = await request(endpoint, { method: 'POST', body: JSON.stringify({ storyboard, research, tier: catalogTier.value }) });
      const result = data.validation || data;
      diagnostics(storyboardResult, result.diagnostics, result.valid ? (save ? 'Draft сохранён локально после успешной проверки.' : 'Storyboard готов к сохранению или подготовке run.') : 'Storyboard содержит ошибки.');
      if (result.valid && data.storyboard) storyboardJson.value = JSON.stringify(data.storyboard, null, 2);
      updateStoryboardCount();
      return result;
    } catch (error) {
      diagnostics(storyboardResult, [{ severity: 'error', code: 'storyboard.invalid', message: error.message }]);
      throw error;
    }
  }

  async function prepareRun(event) {
    event.preventDefault();
    setRunResult('Подготавливаем run draft…', 'empty');
    try {
      const data = await request('/api/studio/runs/prepare', {
        method: 'POST',
        body: JSON.stringify({
          topic: $('#topic').value.trim(),
          preset: presetSelect.value,
          style: styleFamily.value || null,
          style_config: styleConfig(),
          research: $('#researchToggle').checked,
          agent_level: Number($('#agentLevel').value),
        }),
      });
      const run = data.run;
      runIdInput.value = run.run_id;
      setRunResult(`Draft ${run.run_id} создан. Статус: ${run.status}. Renderer не запущен: требуется отдельное явное approval.`, 'success');
      await inspectRun();
    } catch (error) {
      setRunResult(`Run не подготовлен: ${error.message}`, 'error');
    }
  }

  function renderSnapshot(snapshot) {
    runSnapshot.replaceChildren();
    if (!snapshot) { runSnapshot.textContent = 'Run не найден.'; return; }
    const fields = [['run', snapshot.run_id], ['status', snapshot.status], ['node', snapshot.current_node || '—'], ['created', new Date(snapshot.created_at).toLocaleString('ru-RU')], ['artifacts', String((snapshot.artifacts || []).length)]];
    const wrap = document.createElement('div');
    wrap.className = 'snapshot-line';
    fields.forEach(([label, value]) => {
      const row = document.createElement('div');
      const key = document.createElement('span'); key.textContent = label;
      const val = document.createElement('strong'); val.textContent = value;
      row.append(key, val); wrap.appendChild(row);
    });
    runSnapshot.appendChild(wrap);
  }

  function renderTimeline(events, traces) {
    timeline.replaceChildren();
    const entries = [
      ...(events || []).map((item) => ({ kind: 'event', at: item.timestamp, type: item.type, message: item.message, level: item.level })),
      ...(traces || []).map((item) => ({ kind: 'trace', at: item.started_at, type: item.name, message: item.status === 'error' ? item.error : `status: ${item.status}`, level: item.status === 'error' ? 'error' : 'info' })),
    ].sort((a, b) => new Date(a.at) - new Date(b.at));
    if (!entries.length) {
      timeline.innerHTML = '<li class="empty-state">Пока нет событий. Draft run будет наполняться после validation/approval/worker start.</li>';
      return;
    }
    entries.forEach((entry) => {
      const item = document.createElement('li');
      item.className = `${entry.kind} ${entry.level === 'error' ? 'error' : ''}`;
      const at = document.createElement('span');
      at.className = 'event-time';
      at.textContent = new Date(entry.at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const content = document.createElement('div');
      const type = document.createElement('div'); type.className = 'event-type'; type.textContent = entry.type;
      const message = document.createElement('div'); message.className = 'event-message'; message.textContent = entry.message || '—';
      content.append(type, message); item.append(at, content); timeline.appendChild(item);
    });
  }

  async function inspectRun() {
    const runId = runIdInput.value.trim();
    if (!runId) return;
    try {
      const data = await request(`/api/studio/runs/${encodeURIComponent(runId)}/timeline`);
      renderSnapshot(data.snapshot);
      renderTimeline(data.events, data.traces);
    } catch (error) {
      runSnapshot.textContent = `Не удалось прочитать run: ${error.message}`;
      timeline.innerHTML = '<li class="empty-state">Проверьте opaque run ID.</li>';
    }
  }

  $('#runForm').addEventListener('submit', prepareRun);
  $('#validateResearch').addEventListener('click', () => validateEvidence().catch(() => {}));
  $('#loadSampleEvidence').addEventListener('click', () => { researchJson.value = JSON.stringify(sampleResearch, null, 2); setGateState(researchState, 'Пример загружен', ''); });
  $('#validateStoryboard').addEventListener('click', () => validateStoryboard(false).catch(() => {}));
  $('#saveStoryboard').addEventListener('click', () => validateStoryboard(true).catch(() => {}));
  $('#inspectRun').addEventListener('click', inspectRun);
  styleFamily.addEventListener('change', applyStyleFamily);
  [styleNeon, styleBg, styleSurface].forEach((input) => input.addEventListener('input', () => { input.dataset.override = 'true'; refreshStyleControls(); }));
  styleBloom.addEventListener('input', () => { styleBloom.dataset.override = 'true'; refreshStyleControls(); });
  storyboardJson.addEventListener('input', updateStoryboardCount);
  let debounce = 0;
  catalogQuery.addEventListener('input', () => { clearTimeout(debounce); debounce = setTimeout(loadCatalog, 220); });
  catalogTier.addEventListener('change', loadCatalog);
  loadCatalog();
  loadStyles();
})();
