/**
 * Long-lived Remotion render server for the control panel.
 *
 * WHY THIS EXISTS
 * ---------------
 * The panel needs previews that update while you edit a parameter. `npx remotion
 * still` cannot do that: it re-bundles per invocation, measured at 19.7s cold on
 * this machine. Nobody edits a font size against a 20-second feedback loop.
 *
 * Measured with @remotion/bundler + @remotion/renderer held open in one process:
 *
 *     bundle (once)   19.7s cold / 3.8s warm (webpack cache)
 *     selectComposition 2.4s
 *     renderStill      1.7s
 *     renderStill again 1.7s   <- no re-bundle
 *     renderMedia 60f   4.3s   at scale 0.5, crf 26
 *
 * So: bundle once at startup, then answer requests forever. That is the whole
 * point of this file.
 *
 * PROTOCOL — newline-delimited JSON on stdin/stdout
 * ------------------------------------------------
 * Request:  {"id":"abc","op":"still","spec":{...},"frame":120,"scale":0.5,"out":"C:/…png"}
 *           {"id":"abc","op":"clip","spec":{...},"from":0,"to":120,"out":"…mp4"}
 *           {"id":"abc","op":"ping"}
 * Response: {"id":"abc","ok":true,"out":"…","ms":1700,"durationInFrames":180}
 *           {"id":"abc","ok":false,"error":"…"}
 *
 * One line per response, and EVERY request gets exactly one — a request that
 * throws must not leave the caller waiting for a line that never comes.
 *
 * WHY REQUESTS ARE SERIALISED
 * ---------------------------
 * renderMedia already saturates the CPU with its own concurrency. Running two
 * renders at once made both slower and occasionally raced on the output path.
 * Requests queue; the panel debounces on its side so a slider drag does not
 * enqueue thirty stills.
 *
 * PITFALL: renderMedia's output option is `outputLocation`, NOT `output` (that is
 * renderStill). Passing `output` is silently accepted and writes nothing —
 * renderMedia resolves fine and the file is simply absent.
 *
 * PITFALL: inputProps must be passed to BOTH selectComposition and the render
 * call. selectComposition uses them to resolve durationInFrames via calculateMetadata;
 * omitting them there returns the default duration and the clip gets truncated.
 */
import { bundle } from '@remotion/bundler';
import { selectComposition, renderStill, renderMedia } from '@remotion/renderer';
import { createInterface } from 'node:readline';
import { existsSync, mkdirSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const ROOT = resolve(import.meta.dirname, '..');

const log = (...a) => process.stderr.write(`[render-server] ${a.join(' ')}\n`);
const send = (obj) => process.stdout.write(`${JSON.stringify(obj)}\n`);

let serveUrl = null;

async function ensureBundle() {
  if (serveUrl) return serveUrl;
  const t0 = Date.now();
  serveUrl = await bundle({
    entryPoint: join(ROOT, 'src/index.ts'),
    onProgress: () => {},
    // Keep webpack's cache between server restarts: a cold bundle is 20s, a
    // warm one under 4s, and the panel is restarted often during development.
    webpackOverride: (c) => c,
  });
  log(`bundled in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  return serveUrl;
}

async function handleStill(req) {
  const url = await ensureBundle();
  const comp = await selectComposition({ serveUrl: url, id: 'Main', inputProps: req.spec });
  const total = comp.durationInFrames;
  // `frame_pct` is resolved HERE, not by the caller: durationInFrames is only
  // known after calculateMetadata runs (transitions shorten the timeline), so a
  // caller asking for "90% through" cannot compute the frame itself.
  // Clamp either way — a frame past the end throws, and asking for frame 200 of a
  // 180-frame video is normal when following a percentage.
  const wanted = req.frame ?? (req.frame_pct != null ? total * req.frame_pct : total * 0.9);
  const frame = Math.max(0, Math.min(total - 1, Math.round(wanted)));
  mkdirSync(dirname(req.out), { recursive: true });
  await renderStill({
    serveUrl: url,
    composition: comp,
    output: req.out,
    frame,
    inputProps: req.spec,
    scale: req.scale ?? 1,
    overwrite: true,
    chromiumOptions: { gl: 'angle' },
  });
  return { frame, durationInFrames: total, bytes: statSync(req.out).size };
}

async function handleClip(req) {
  const url = await ensureBundle();
  const comp = await selectComposition({ serveUrl: url, id: 'Main', inputProps: req.spec });
  const total = comp.durationInFrames;
  const from = Math.max(0, Math.min(total - 1, Math.round(req.from ?? 0)));
  const to = Math.max(from, Math.min(total - 1, Math.round(req.to ?? total - 1)));
  mkdirSync(dirname(req.out), { recursive: true });
  await renderMedia({
    serveUrl: url,
    composition: comp,
    codec: req.codec ?? 'h264',
    // NOT `output` — see the pitfall note at the top of this file.
    outputLocation: req.out,
    inputProps: req.spec,
    frameRange: [from, to],
    crf: req.crf ?? 26,
    scale: req.scale ?? 0.5,
    concurrency: req.concurrency ?? 4,
    // Previews are silent by design: audio comes from per-scene wav files the
    // panel does not have when previewing a bare preset, and muted rendering
    // avoids a stall looking for them.
    muted: req.muted ?? true,
    overwrite: true,
    onProgress: () => {},
    chromiumOptions: { gl: 'angle' },
  });
  return { from, to, durationInFrames: total, bytes: statSync(req.out).size };
}

const OPS = {
  ping: async () => ({ pong: true, bundled: Boolean(serveUrl) }),
  still: handleStill,
  clip: handleClip,
};

// Serial queue. See the note at the top about why.
let chain = Promise.resolve();

const rl = createInterface({ input: process.stdin, crlfDelay: Infinity });
rl.on('line', (line) => {
  const text = line.trim();
  if (!text) return;
  let req;
  try {
    req = JSON.parse(text);
  } catch (e) {
    send({ id: null, ok: false, error: `bad JSON: ${e.message}` });
    return;
  }
  chain = chain.then(async () => {
    const t0 = Date.now();
    const op = OPS[req.op];
    if (!op) {
      send({ id: req.id, ok: false, error: `unknown op ${req.op}` });
      return;
    }
    try {
      const extra = await op(req);
      send({ id: req.id, ok: true, out: req.out, ms: Date.now() - t0, ...extra });
    } catch (e) {
      // The useful part of a Remotion error is usually the last few lines (the
      // component stack); the first lines are webpack noise.
      const msg = (e?.stack ?? String(e)).split('\n').slice(0, 6).join(' | ');
      send({ id: req.id, ok: false, error: msg, ms: Date.now() - t0 });
    }
  });
});

rl.on('close', () => process.exit(0));

// Bundle eagerly so the first real preview is fast, and announce readiness so the
// panel can show "warming up" instead of a preview that appears to hang.
ensureBundle()
  .then(() => send({ id: null, ok: true, event: 'ready' }))
  .catch((e) => {
    send({ id: null, ok: false, event: 'ready', error: String(e?.stack ?? e) });
    log('bundle failed:', e);
  });
