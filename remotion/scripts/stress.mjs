/**
 * Stress-render one preset to a PNG, or a whole batch from a JSON file.
 *
 * WHY THIS EXISTS
 * ---------------
 * Every preset defect found so far was invisible to the demo data: the demo rows
 * say "Aria Chen" and the pipeline says "Qwen3.6-235B-A22B", and only the second
 * one overflows. Reviewing a preset therefore means rendering it with HOSTILE
 * data — longest realistic strings, most items, both light and dark style kits —
 * and that needs to be one command, not a hand-built spec each time.
 *
 * USAGE
 *   node scripts/stress.mjs <cases.json> [outDir]
 *
 * cases.json is an array of:
 *   { "name": "leaderboard_long", "frame": 140, "style": "pop", "scene": { ...spec fields... } }
 *
 * `scene` is a single scene object exactly as it appears in a VideoSpec's
 * `scenes[]`. It is wrapped into a full 1080x1920 spec here so a case only has
 * to describe what it is testing.
 *
 * Writes <outDir>/<name>.png (default outDir: out/stress) and prints one line per
 * case so a failure is attributable without reading the render log.
 *
 * PITFALL: `npx remotion still` re-bundles per invocation (~20s). Batching all
 * cases through one bundle would be faster but hides which case crashed the
 * bundle; the loop is deliberate.
 */
import { execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync, existsSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';

const [casesPath, outDirArg] = process.argv.slice(2);
if (!casesPath) {
  console.error('usage: node scripts/stress.mjs <cases.json> [outDir]');
  process.exit(2);
}

const ROOT = resolve(import.meta.dirname, '..');
const outDir = outDirArg ?? 'out/stress';
mkdirSync(join(ROOT, outDir), { recursive: true });

const cases = JSON.parse(
  await import('node:fs').then((fs) => fs.readFileSync(resolve(casesPath), 'utf8'))
);

let failed = 0;
for (const c of cases) {
  const name = c.name ?? `case_${cases.indexOf(c)}`;
  const dur = c.scene.durationInFrames ?? 150;
  const spec = {
    width: 1080,
    height: 1920,
    fps: 60,
    style: c.style ?? 'pop',
    scenes: [{ id: name, durationInFrames: dur, ...c.scene }],
  };
  const propsPath = join(ROOT, `.stress_${name}.json`);
  writeFileSync(propsPath, JSON.stringify(spec), 'utf8');
  const outPng = `${outDir}/${name}.png`;
  const abs = join(ROOT, outPng);
  if (existsSync(abs)) rmSync(abs);
  // Default to a late frame: entrance animations are usually done by ~60% in,
  // and a frame-0 screenshot shows an empty scene and proves nothing.
  const frame = c.frame ?? Math.floor(dur * 0.9);
  try {
    execFileSync(
      'npx',
      ['remotion', 'still', 'src/index.ts', 'Main', outPng,
       `--frame=${frame}`, `--props=${propsPath}`, '--log=error'],
      { cwd: ROOT, stdio: ['ignore', 'ignore', 'pipe'], timeout: 300000, shell: true }
    );
    console.log(existsSync(abs) ? `OK   ${name} -> ${outPng}` : `EMPTY ${name}`);
    if (!existsSync(abs)) failed++;
  } catch (e) {
    failed++;
    const err = (e.stderr?.toString() ?? e.message).trim().split('\n').slice(-3).join(' | ');
    console.log(`FAIL ${name}: ${err}`);
  } finally {
    rmSync(propsPath, { force: true });
  }
}
console.log(`\n${cases.length - failed}/${cases.length} rendered`);
process.exit(failed ? 1 : 0);
