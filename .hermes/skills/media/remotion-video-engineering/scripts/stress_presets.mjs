/**
 * Stress-render presets to PNGs from a JSON case list.
 *
 * WHY THIS EXISTS
 * ---------------
 * Every preset defect found in this project was invisible to the demo data. The
 * demo rows say "Aria Chen"; the pipeline says "Qwen3.6-235B-A22B". Only the
 * second one overflows. A preset that looks correct in the Remotion studio is
 * therefore NOT evidence that it is correct — reviewing one means rendering it
 * with hostile data (longest realistic strings, most items, the project's real
 * script), and that has to be one command or it does not get done.
 *
 * Drop this at remotion/scripts/stress.mjs in the target project.
 *
 * USAGE
 *   node scripts/stress.mjs <cases.json> [outDir]
 *
 * cases.json is an array of:
 *   { "name": "leaderboard_long", "frame": 140, "style": "pop",
 *     "scene": { "preset": "Leaderboard", "title": "...", "rows": [...] } }
 *
 * `scene` is one scene object exactly as it appears in a VideoSpec's `scenes[]`;
 * it is wrapped into a full 1080x1920 spec here so a case only describes what it
 * is testing. Writes <outDir>/<name>.png and prints one line per case, so a
 * failure is attributable without reading the render log.
 *
 * PITFALLS
 * - `frame` defaults to 90% of the scene duration. A frame-0 still shows an empty
 *   scene and proves nothing; entrance animations are usually done by ~60%.
 * - For BEAT-DIVIDED presets (`from`, `revealAtProgress`, `sendAtProgress`,
 *   `steps[]`) one frame is not enough — add several cases with explicit `frame`
 *   values, one per beat. See references/text-fitting-and-beat-sampling.md §2.
 * - `npx remotion still` re-bundles per invocation (~20s). Batching every case
 *   through one bundle would be faster but hides which case broke the bundle;
 *   the loop is deliberate.
 * - Watch the frame arithmetic when hand-picking frames. With 150-frame scenes,
 *   frames 120/130/140 are all still scene 0 — mistaking them for later scenes
 *   produces confident nonsense diagnoses ("preset X renders bars, not rings").
 */
import { execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync, existsSync, rmSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const [casesPath, outDirArg] = process.argv.slice(2);
if (!casesPath) {
  console.error('usage: node scripts/stress.mjs <cases.json> [outDir]');
  process.exit(2);
}

const ROOT = resolve(import.meta.dirname, '..');
const outDir = outDirArg ?? 'out/stress';
mkdirSync(join(ROOT, outDir), { recursive: true });

const cases = JSON.parse(readFileSync(resolve(casesPath), 'utf8'));

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
