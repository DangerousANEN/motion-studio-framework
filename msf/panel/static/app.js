/**
 * MSF Control Panel — client.
 *
 * No framework and no build step, deliberately: this ships inside a Python
 * package and must not need `npm install` to open. Everything renders from the
 * API responses, which come from the pipeline's own registries.
 *
 * ONE RULE THROUGHOUT: never invent state. If a fetch fails, the view shows the
 * error text. A panel that renders an empty-but-tidy list when the backend is
 * broken is how the pipeline hid five-preset rotation for weeks.
 */
'use strict';

const $ = (sel, root = document) => root.querySelector(sel);
const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') n.className = v;
    else if (k === 'html') n.innerHTML = v;
    else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else if (v !== null && v !== undefined) n.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid === null || kid === undefined || kid === false) continue;
    n.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return n;
};
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/**
 * Replace a container's children, dropping absent nodes.
 *
 * Node.replaceChildren() STRINGIFIES a null argument, so a conditional section
 * written as `mount(root, header, warn, list)` with warn=null rendered the literal
 * text "null" on the page. el() already filters its kids; this gives the top-level
 * calls the same behaviour instead of relying on every call site to remember.
 */
const mount = (root, ...kids) =>
  root.replaceChildren(...kids.flat().filter((k) => k !== null && k !== undefined && k !== false));

/** Fetch JSON, surfacing the server's own error text instead of a generic one. */
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { /* keep raw */ }
  if (!res.ok) {
    const detail = data && data.detail ? data.detail : text.slice(0, 500);
    throw new Error(`${res.status}: ${detail}`);
  }
  return data;
}

const CACHE = {};
async function load(key, path) {
  if (!CACHE[key]) CACHE[key] = api(path);
  return CACHE[key];
}
const invalidate = (key) => { delete CACHE[key]; };

function fail(container, err) {
  container.replaceChildren(
    el('div', { class: 'card' },
      el('h3', { class: 'err' }, 'Ошибка запроса'),
      el('pre', { class: 'log err' }, err.message)));
}

// ------------------------------------------------------------------ status

async function viewStatus(root) {
  root.replaceChildren(el('div', { class: 'empty' }, el('span', { class: 'spinner' })));
  let s, g;
  try {
    [s, g] = await Promise.all([api('/api/status'), api('/api/graph')]);
  } catch (e) { return fail(root, e); }

  const checks = el('div', { class: 'card' },
    el('h3', {}, 'Проверки окружения'),
    el('table', {},
      el('tbody', {}, s.checks.map((c) =>
        el('tr', {},
          el('td', { class: c.ok ? 'ok' : 'err' }, c.ok ? '✓' : '✗'),
          el('td', {}, c.name),
          el('td', { class: 'muted' }, c.detail))))));

  const cfg = el('div', { class: 'card' },
    el('h3', {}, 'Конфигурация'),
    el('dl', { class: 'kv' },
      el('dt', {}, 'LLM'), el('dd', {}, `${s.llm.model} @ ${s.llm.base_url}`),
      el('dt', {}, 'Формат'), el('dd', {}, `${s.render.width}×${s.render.height} @ ${s.render.fps}fps`),
      el('dt', {}, 'Пресетов'), el('dd', {}, String(g.allowed_presets)),
      el('dt', {}, 'Data-driven'), el('dd', {}, String(g.data_driven_count))));

  const graph = el('div', { class: 'card' },
    el('h3', {}, 'Граф пайплайна'),
    el('div', { class: 'stepper' }, g.nodes.map((n) => el('span', { class: 'step' }, n))),
    g.unwired_functions.length
      ? el('p', { class: 'warn' }, `Не подключены: ${g.unwired_functions.join(', ')}`)
      : el('p', { class: 'muted' }, 'Все node_* функции подключены к графу.'));

  const rot = el('div', { class: 'card' },
    el('h3', {}, 'Ротация сцен',
      el('span', { class: 'tag used' }, `${g.rotation_presets.length} шт.`)),
    el('p', { class: 'sum' },
      'Эти пресеты подставляются в сцены, у которых есть только текст. ' +
      'Остальные требуют данных или рисуют собственный демо-контент.'),
    el('div', { class: 'tags' },
      g.rotation_presets.map((p) => el('span', { class: 'tag used' }, p))));

  mount(root,
    el('div', { class: 'grid g-two' }, checks, cfg),
    el('div', { class: 'grid g-two', style: 'margin-top:12px' }, graph, rot));
}

// ------------------------------------------------------------------ scenes

const SCENE_DEMO = {
  title: 'НЕЙРОСЕТИ 2026',
  text: 'Открытые модели догнали закрытые по длине контекста и по цене.',
};

async function viewScenes(root) {
  root.replaceChildren(el('div', { class: 'empty' }, el('span', { class: 'spinner' })));
  let d;
  try { d = await load('scenes', '/api/scenes'); } catch (e) { return fail(root, e); }

  const state = { q: '', cat: '', only: '' };
  const list = el('div', { class: 'grid g-cards' });
  const preview = el('div', { class: 'card', style: 'margin-bottom:14px;display:none' });

  const render = () => {
    const items = d.items.filter((it) => {
      if (state.cat && it.category !== state.cat) return false;
      if (state.only === 'rotation' && !it.rotation_used) return false;
      if (state.only === 'data' && !it.data_driven) return false;
      if (state.only === 'unused' && it.rotation_used) return false;
      if (state.q) {
        const hay = `${it.name} ${it.category} ${it.summary}`.toLowerCase();
        if (!hay.includes(state.q.toLowerCase())) return false;
      }
      return true;
    });
    count.textContent = `${items.length} из ${d.total}`;
    list.replaceChildren(...items.map(sceneCard));
    if (!items.length) list.replaceChildren(el('div', { class: 'empty' }, 'Ничего не найдено'));
  };

  function sceneCard(it) {
    return el('div', { class: 'card' },
      el('h3', {}, it.name,
        it.rotation_used && el('span', { class: 'tag used' }, 'в ротации'),
        it.data_driven && el('span', { class: 'tag data' }, 'нужны данные'),
        it.rotation_blocked && el('span', { class: 'tag blocked' }, 'свой демо-контент'),
        it.three && el('span', { class: 'tag three' }, '3D')),
      el('div', { class: 'sum' }, it.summary),
      el('div', { class: 'tags' },
        el('span', { class: 'tag' }, it.category),
        // The pack tag is only informative when it names something different
        // from the category. `media` presets live in the media pack (rendered a
        // literal "media media"), and the ui-mock category lives in the ui_mock
        // pack — same word, different separator, so normalise before comparing.
        it.pack.replace(/_/g, '-') !== it.category
          ? el('span', { class: 'tag' }, it.pack) : null),
      el('div', { class: 'fields' }, 'Поля: ' + (it.fields.join(', ') || '—')),
      el('div', { style: 'margin-top:10px' },
        el('button', {
          class: 'act', onclick: (ev) => previewScene(it, ev.target),
        }, 'Предпросмотр')));
  }

  async function previewScene(it, btn) {
    const orig = btn.textContent;
    btn.disabled = true; btn.textContent = 'Рендер…';
    preview.style.display = '';
    preview.replaceChildren(
      el('h3', {}, `Предпросмотр: ${it.name}`, el('span', { class: 'spinner' })),
      el('p', { class: 'muted' }, 'Первый кадр рендерится ~20–40 с (Remotion пересобирает бандл).'));
    try {
      const res = await api('/api/preview/scene', {
        method: 'POST',
        body: { preset: it.name, props: SCENE_DEMO, frame_pct: 0.9, duration_frames: 180 },
      });
      preview.replaceChildren(
        el('h3', {}, `Предпросмотр: ${it.name}`,
          el('span', { class: 'tag' }, `кадр ${res.frame}`)),
        el('div', { class: 'previewbox' },
          el('img', { src: res.url + '?t=' + Date.now(), alt: it.name }),
          el('div', {},
            el('div', { class: 'sum' }, it.summary),
            el('div', { class: 'fields' }, 'Поля: ' + it.fields.join(', ')),
            el('p', { class: 'muted' }, 'Передан только заголовок и текст — то же, что получает сцена при ротации.'))));
    } catch (e) {
      preview.replaceChildren(
        el('h3', { class: 'err' }, `Предпросмотр не удался: ${it.name}`),
        el('pre', { class: 'log err' }, e.message));
    } finally {
      btn.disabled = false; btn.textContent = orig;
    }
  }

  const count = el('span', { class: 'pill' }, '');
  const cats = Object.keys(d.categories).sort();
  const bar = el('div', { class: 'toolbar' },
    el('input', {
      placeholder: 'Поиск по названию или описанию', style: 'min-width:280px',
      oninput: (e) => { state.q = e.target.value; render(); },
    }),
    el('select', { onchange: (e) => { state.cat = e.target.value; render(); } },
      el('option', { value: '' }, 'Все категории'),
      cats.map((c) => el('option', { value: c }, `${c} (${d.categories[c].length})`))),
    el('select', { onchange: (e) => { state.only = e.target.value; render(); } },
      el('option', { value: '' }, 'Все пресеты'),
      el('option', { value: 'rotation' }, 'Только в ротации'),
      el('option', { value: 'unused' }, 'Не в ротации'),
      el('option', { value: 'data' }, 'Только data-driven')),
    count);

  root.replaceChildren(bar, preview, list);
  render();
}

// ------------------------------------------------------------------ effects

async function viewEffects(root) {
  root.replaceChildren(el('div', { class: 'empty' }, el('span', { class: 'spinner' })));
  let d;
  try { d = await load('effects', '/api/effects'); } catch (e) { return fail(root, e); }

  const fams = Object.keys(d.by_family).sort();
  const groups = fams.map((f) => el('div', { class: 'card' },
    el('h3', {}, f, el('span', { class: 'tag' }, `${d.by_family[f].length}`)),
    el('table', {},
      el('tbody', {}, d.by_family[f].map((name) => {
        const e = d.effects.find((x) => x.name === name);
        return el('tr', {},
          el('td', { style: 'white-space:nowrap' }, name,
            e.stochastic ? el('span', { class: 'tag', style: 'margin-left:6px' }, 'seed') : null),
          el('td', { class: 'muted' }, e.summary));
      })))));

  const trans = el('div', { class: 'card' },
    el('h3', {}, 'Переходы между сценами',
      el('span', { class: 'tag' }, String(d.transitions.length))),
    el('p', { class: 'sum' },
      'Это НЕ эффекты: в списке scene.effects они игнорируются с предупреждением в консоли. ' +
      'Указывать их надо в transition.'),
    el('div', { class: 'tags' }, d.transitions.map((t) => el('span', { class: 'tag' }, t))));

  root.replaceChildren(
    el('div', { class: 'toolbar' },
      el('span', { class: 'pill' }, `${d.effects.length} эффектов`),
      el('span', { class: 'pill' }, `${d.transitions.length} переходов`)),
    trans,
    el('div', { class: 'grid g-two', style: 'margin-top:12px' }, groups));
}

// ------------------------------------------------------------------ voices

async function viewVoices(root) {
  root.replaceChildren(el('div', { class: 'empty' }, el('span', { class: 'spinner' })));
  let d;
  try { d = await api('/api/voices'); } catch (e) { return fail(root, e); }

  const warn = !d.configured_is_valid
    ? el('div', { class: 'card' },
        el('h3', { class: 'err' }, 'Настроенный голос не существует'),
        el('p', {}, `config tts.speaker = ${esc(d.configured)}, но такого ключа нет в реестре. ` +
          'Синтез упадёт и подставит другой (женский) голос.'))
    : null;

  const cards = d.items.map((v) => el('div', { class: 'card' },
    el('h3', {}, v.key,
      v.is_default && el('span', { class: 'tag used' }, 'по умолчанию'),
      v.key === d.configured && el('span', { class: 'tag data' }, 'в конфиге'),
      v.icl ? el('span', { class: 'tag used' }, 'ICL')
            : el('span', { class: 'tag blocked' }, 'x-vector (плоско)')),
    el('dl', { class: 'kv' },
      el('dt', {}, 'Режим'), el('dd', { class: v.icl ? 'ok' : 'warn' }, v.mode || '—'),
      el('dt', {}, 'Длина'), el('dd', {}, v.duration_sec ? `${v.duration_sec} с` : '—'),
      el('dt', {}, 'Частота'), el('dd', {}, v.sample_rate ? `${v.sample_rate} Гц` : '—'),
      el('dt', {}, 'Файл'), el('dd', { class: v.exists ? '' : 'err' },
        (v.ref_audio || '').split(/[\\/]/).pop() + (v.exists ? '' : ' — НЕ НАЙДЕН'))),
    v.notes ? el('div', { class: 'sum' }, v.notes) : null,
    v.ref_text ? el('details', {}, el('summary', { class: 'muted' }, 'Транскрипт'),
      el('div', { class: 'fields' }, v.ref_text)) : null,
    el('div', { style: 'margin-top:10px;display:flex;gap:8px;align-items:center;flex-wrap:wrap' },
      el('button', { class: 'act', onclick: (ev) => speak(v.key, ev.target) }, 'Прослушать'),
      el('span', { class: 'slot' }))));

  async function speak(key, btn) {
    const slot = btn.parentElement.querySelector('.slot');
    const orig = btn.textContent;
    btn.disabled = true; btn.textContent = 'Синтез…';
    slot.replaceChildren(el('span', { class: 'spinner' }));
    try {
      const res = await api('/api/preview/voice', { method: 'POST', body: { voice: key, text: sampleText.value } });
      slot.replaceChildren(
        el('audio', { controls: '', src: res.url + '?t=' + Date.now() }),
        el('span', { class: 'tag' }, `${res.duration_sec}s / ${res.synth_sec}s синтез`));
    } catch (e) {
      slot.replaceChildren(el('span', { class: 'err' }, e.message));
    } finally { btn.disabled = false; btn.textContent = orig; }
  }

  const sampleText = el('input', {
    value: 'Открытые модели догнали закрытые по длине контекста и по цене.',
    style: 'min-width:420px;flex:1',
  });

  // Adding a voice: transcript is required by the API, and the form says why.
  const addForm = el('div', { class: 'card' },
    el('h3', {}, 'Добавить голос'),
    el('p', { class: 'sum' },
      'Транскрипт обязателен. Без него модель уходит в x-vector режим: тембр копируется, ' +
      'интонация — нет. Файл копируется в assets/voices/refs/, в реестр пишется относительный путь.'),
    el('div', { class: 'toolbar' },
      el('input', { id: 'nv-key', placeholder: 'ключ (voice_4)', style: 'width:160px' }),
      el('input', { id: 'nv-path', placeholder: 'C:\\путь\\к\\reference.wav', style: 'flex:1;min-width:280px' })),
    el('textarea', { id: 'nv-text', rows: '3', placeholder: 'Дословный транскрипт записи…', style: 'width:100%' }),
    el('div', { class: 'toolbar' },
      el('input', { id: 'nv-notes', placeholder: 'заметка (необязательно)', style: 'flex:1' }),
      el('button', { class: 'act primary', onclick: addVoice }, 'Добавить'),
      el('span', { id: 'nv-msg', class: 'muted' })));

  async function addVoice(ev) {
    const msg = $('#nv-msg');
    msg.className = 'muted'; msg.textContent = 'Проверка…';
    try {
      const res = await api('/api/voices', {
        method: 'POST',
        body: {
          key: $('#nv-key').value.trim(),
          ref_audio: $('#nv-path').value.trim(),
          ref_text: $('#nv-text').value.trim(),
          notes: $('#nv-notes').value.trim(),
        },
      });
      msg.className = 'ok';
      msg.textContent = `Добавлен ${res.key}: ${res.duration_sec}s, ${res.mode}`;
      invalidate('voices');
      setTimeout(() => switchTo('voices'), 700);
    } catch (e) {
      msg.className = 'err'; msg.textContent = e.message;
    }
  }

  mount(root,
    el('div', { class: 'toolbar' },
      el('span', { class: 'pill' }, `${d.items.length} голосов`),
      el('span', { class: d.configured_is_valid ? 'pill ok' : 'pill bad' },
        `в конфиге: ${d.configured}`),
      el('span', { class: 'muted' }, 'Текст пробы:'), sampleText),
    warn,
    el('div', { class: 'grid g-cards' }, cards),
    el('div', { style: 'margin-top:14px' }, addForm));
}

// ------------------------------------------------------------------ audio

async function viewAudio(root) {
  root.replaceChildren(el('div', { class: 'empty' }, el('span', { class: 'spinner' })));
  let d;
  try { d = await load('audio', '/api/audio'); } catch (e) { return fail(root, e); }

  const playCell = (path) => {
    const slot = el('td', {});
    slot.append(el('button', {
      class: 'act',
      onclick: async (ev) => {
        const btn = ev.target;
        btn.disabled = true;
        try {
          const res = await api(path);
          slot.replaceChildren(el('audio', { controls: '', autoplay: '', src: res.url }));
        } catch (e) { slot.replaceChildren(el('span', { class: 'err' }, e.message)); }
      },
    }, '▶'));
    return slot;
  };

  const byFam = {};
  for (const s of d.sfx) (byFam[s.family] ||= []).push(s);

  const sfxCards = Object.keys(byFam).sort().map((f) => el('div', { class: 'card' },
    el('h3', {}, `SFX: ${f}`, el('span', { class: 'tag' }, String(byFam[f].length))),
    el('table', {}, el('tbody', {}, byFam[f].map((s) => el('tr', {},
      el('td', { style: 'white-space:nowrap' }, s.name),
      el('td', { class: 'muted' }, s.summary),
      el('td', { class: 'muted', style: 'white-space:nowrap' }, `${s.max_ms} мс`),
      playCell(`/api/preview/sfx/${encodeURIComponent(s.name)}`)))))));

  const music = el('div', { class: 'card' },
    el('h3', {}, 'Музыкальные подложки', el('span', { class: 'tag' }, String(d.music.length))),
    el('table', {},
      el('thead', {}, el('tr', {},
        el('th', {}, 'Название'), el('th', {}, 'Характер'), el('th', {}, 'Применение'),
        el('th', {}, 'BPM'), el('th', {}, 'Тон.'), el('th', {}, ''))),
      el('tbody', {}, d.music.map((b) => el('tr', {},
        el('td', { style: 'white-space:nowrap' }, b.name),
        el('td', { class: 'muted' }, b.character),
        el('td', { class: 'muted' }, b.use),
        el('td', { class: 'muted' }, String(b.bpm)),
        el('td', { class: 'muted' }, b.key),
        playCell(`/api/preview/music/${encodeURIComponent(b.name)}?seconds=8`))))));

  root.replaceChildren(
    el('div', { class: 'toolbar' },
      el('span', { class: 'pill' }, `${d.sfx.length} SFX`),
      el('span', { class: 'pill' }, `${d.music.length} подложек`)),
    music,
    el('div', { class: 'grid g-two', style: 'margin-top:12px' }, sfxCards));
}

// ------------------------------------------------------------------ LDR

async function viewLdr(root) {
  root.replaceChildren(el('div', { class: 'empty' }, el('span', { class: 'spinner' })));
  let d;
  try { d = await api('/api/ldr'); } catch (e) { return fail(root, e); }

  const row = (label, ok, detail) => el('tr', {},
    el('td', { class: ok ? 'ok' : 'err' }, ok ? '✓' : '✗'),
    el('td', {}, label),
    el('td', { class: 'muted' }, detail));

  const wiring = el('div', { class: 'card' },
    el('h3', {}, 'Подключение LDR'),
    el('p', { class: 'sum' },
      'Нода fail-closed: если LDR недоступен, пайплайн падает, а не выдумывает факты.'),
    el('table', {}, el('tbody', {},
      row('Рабочий каталог', d.work_dir_exists, d.work_dir),
      row('Python окружения', d.python_exists, d.python),
      row('Скрипт запуска', d.runner_exists, d.runner),
      row('SearXNG', d.searxng_ok, `${d.searxng_url} — ${d.searxng_detail}`))));

  const last = el('div', { class: 'card' },
    el('h3', {}, 'Последний результат'),
    d.last_result_at
      ? el('div', {},
          el('p', { class: 'muted' }, d.last_result_at),
          el('pre', { class: 'log' }, JSON.stringify(d.last_result_preview, null, 1).slice(0, 4000)))
      : el('p', { class: 'muted' }, 'Ещё не запускался (ldr_last_raw.json отсутствует).'));

  root.replaceChildren(el('div', { class: 'grid g-two' }, wiring, last));
}

// ------------------------------------------------------------------ runs

let runTimer = null;

async function viewRuns(root) {
  if (runTimer) { clearInterval(runTimer); runTimer = null; }

  let scenes, voices, graph;
  try {
    [scenes, voices, graph] = await Promise.all([
      load('scenes', '/api/scenes'), api('/api/voices'), api('/api/graph'),
    ]);
  } catch (e) { return fail(root, e); }

  const form = el('div', { class: 'card' },
    el('h3', {}, 'Новый прогон'),
    el('div', { class: 'toolbar' },
      el('input', { id: 'r-topic', placeholder: 'Тема ролика', style: 'flex:1;min-width:300px' })),
    el('textarea', { id: 'r-text', rows: '3', style: 'width:100%',
      placeholder: 'Текст озвучки (необязательно — если пусто, берётся тема)' }),
    el('div', { class: 'toolbar' },
      el('select', { id: 'r-preset' },
        scenes.items.map((it) => el('option', { value: it.name },
          `${it.name}${it.data_driven ? ' (нужны данные)' : ''}`))),
      el('select', { id: 'r-voice' },
        el('option', { value: '' }, `по умолчанию (${voices.default})`),
        voices.items.map((v) => el('option', { value: v.key }, `${v.key}${v.icl ? '' : ' — x-vector'}`))),
      el('label', { class: 'chk' }, el('input', { type: 'checkbox', id: 'r-research' }), 'LDR-исследование'),
      el('button', { class: 'act primary', onclick: startRun }, 'Запустить'),
      el('span', { id: 'r-msg', class: 'muted' })),
    el('p', { class: 'sum' },
      'Прогон идёт отдельным процессом: он грузит 1.7B TTS на CUDA и вызывает Remotion с ffmpeg.'));

  // Preselect the configured preset so a run matches what the pipeline would do.
  const list = el('div', {});
  root.replaceChildren(form, el('div', { style: 'margin-top:14px' }, list));
  $('#r-preset').value = graph.rotation_presets[0] || 'HeroKinetic';

  async function startRun() {
    const msg = $('#r-msg');
    msg.className = 'muted'; msg.textContent = 'Запуск…';
    try {
      const res = await api('/api/graph/run', {
        method: 'POST',
        body: {
          topic: $('#r-topic').value.trim(),
          text: $('#r-text').value.trim() || null,
          preset: $('#r-preset').value,
          voice: $('#r-voice').value || null,
          research: $('#r-research').checked,
        },
      });
      msg.className = 'ok'; msg.textContent = `Запущен ${res.run_id}`;
      refresh();
    } catch (e) { msg.className = 'err'; msg.textContent = e.message; }
  }

  const openLogs = new Set();

  async function refresh() {
    let d;
    try { d = await api('/api/runs'); } catch (e) { return fail(list, e); }
    if (!d.runs.length) {
      list.replaceChildren(el('div', { class: 'empty' }, 'Прогонов ещё не было'));
      return;
    }
    list.replaceChildren(...d.runs.map(runCard));
    for (const id of openLogs) loadLog(id);
  }

  function runCard(r) {
    const cls = { done: 'ok', failed: 'err', killed: 'warn', running: 'muted' }[r.status] || 'muted';
    const steps = el('div', { class: 'stepper' }, graph.nodes.map((n) => {
      const idx = graph.nodes.indexOf(n), cur = graph.nodes.indexOf(r.node);
      const k = r.node === n ? 'step now' : (cur > idx && cur >= 0 ? 'step done' : 'step');
      return el('span', { class: k }, n);
    }));
    return el('div', { class: 'card', id: `run-${r.run_id}` },
      el('h3', {}, r.topic || r.run_id,
        el('span', { class: `tag ${r.status === 'done' ? 'used' : ''}` }, r.status),
        el('span', { class: 'tag' }, `${r.elapsed_sec}s`)),
      steps,
      r.error ? el('p', { class: 'err' }, r.error) : null,
      r.output_path ? el('p', { class: 'ok' }, `Готово: ${r.output_path}`) : null,
      el('div', { class: 'toolbar' },
        el('button', {
          class: 'act', onclick: () => {
            if (openLogs.has(r.run_id)) { openLogs.delete(r.run_id); refresh(); }
            else { openLogs.add(r.run_id); loadLog(r.run_id); }
          },
        }, openLogs.has(r.run_id) ? 'Скрыть лог' : `Лог (${r.log_lines})`),
        r.status === 'running'
          ? el('button', {
              class: 'act', onclick: async () => {
                await api(`/api/runs/${r.run_id}/kill`, { method: 'POST' }); refresh();
              },
            }, 'Остановить')
          : null),
      el('pre', { class: 'log', id: `log-${r.run_id}`, style: openLogs.has(r.run_id) ? '' : 'display:none' }));
  }

  async function loadLog(id) {
    const pre = document.getElementById(`log-${id}`);
    if (!pre) return;
    try {
      const d = await api(`/api/runs/${id}?tail=400`);
      pre.style.display = '';
      pre.textContent = d.log.join('\n') || '(пусто)';
      pre.scrollTop = pre.scrollHeight;
    } catch (e) { pre.textContent = e.message; }
  }

  await refresh();
  // Poll while this view is open. Cleared on navigation so a background tab does
  // not keep hitting the API.
  runTimer = setInterval(refresh, 2500);
}

// ------------------------------------------------------------------ shell

const VIEWS = {
  status: viewStatus, scenes: viewScenes, effects: viewEffects,
  voices: viewVoices, audio: viewAudio, ldr: viewLdr, runs: viewRuns,
};

function switchTo(name) {
  if (runTimer && name !== 'runs') { clearInterval(runTimer); runTimer = null; }
  for (const b of document.querySelectorAll('nav button')) {
    b.classList.toggle('on', b.dataset.view === name);
  }
  for (const v of document.querySelectorAll('.view')) {
    v.classList.toggle('on', v.id === `view-${name}`);
  }
  location.hash = name;
  VIEWS[name](document.getElementById(`view-${name}`));
}

for (const b of document.querySelectorAll('nav button')) {
  b.addEventListener('click', () => switchTo(b.dataset.view));
}

/** Header counters double as a smoke test: wrong numbers are visible immediately. */
async function header() {
  try {
    const [s, sc, ef, vo] = await Promise.all([
      api('/api/status'), load('scenes', '/api/scenes'),
      load('effects', '/api/effects'), api('/api/voices'),
    ]);
    $('#hdr-scenes').textContent = `${sc.total} сцен · ${sc.rotation_used.length} в ротации`;
    $('#hdr-effects').textContent = `${ef.effects.length} эффектов`;
    const v = vo.items.find((x) => x.key === vo.configured);
    $('#hdr-voice').textContent = `голос: ${vo.configured}${v && v.icl ? ' (ICL)' : ' (x-vector)'}`;
    $('#hdr-voice').className = vo.configured_is_valid && v && v.icl ? 'pill ok' : 'pill bad';
    const bad = s.checks.filter((c) => !c.ok).length;
    $('#hdr-health').textContent = bad ? `${bad} проблем` : 'всё готово';
    $('#hdr-health').className = bad ? 'pill bad' : 'pill ok';
  } catch (e) {
    $('#hdr-health').textContent = 'API недоступен';
    $('#hdr-health').className = 'pill bad';
  }
}

header();
switchTo((location.hash || '#status').slice(1) in VIEWS ? (location.hash || '#status').slice(1) : 'status');
