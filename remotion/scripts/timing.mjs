/**
 * Render a scene as a frame SEQUENCE so timing can be measured, not guessed.
 *
 * WHY THIS EXISTS
 * ---------------
 * A still proves layout. It says nothing about whether a viewer can READ what is
 * on screen. Presets reveal their parts on internal schedules expressed as
 * fractions of durationInFrames, and those schedules were never checked against
 * the clock — so an element can legitimately appear at 78% of a scene and sit
 * there for 0.5s before the cut. Nothing overflows, nothing errors, and the
 * information is simply unreadable.
 *
 * One `remotion render --sequence` pass bundles once and writes every frame, so
 * a 150-frame scene costs about what a single still costs. Sampling stills
 * frame-by-frame would cost 30x that.
 *
 * USAGE
 *   node scripts/timing.mjs <cases.json> [outDir] [--every=N]
 *
 * cases.json is the same format scripts/stress.mjs takes. Writes
 * <outDir>/<name>/element-NNNNN.png plus <outDir>/<name>.meta.json carrying
 * { name, fps, durationInFrames, text } so the analysis step knows the clock and
 * how much reading the scene demands.
 *
 * PITFALL: --sequence needs an OUTPUT DIRECTORY, and Remotion refuses to write
 * into a non-empty one. The directory is removed first.
 */
import { execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync, readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

const args = process.argv.slice(2);
const flags = args.filter((a) => a.startsWith('--'));
const [casesPath, outDirArg] = args.filter((a) => !a.startsWith('--'));
if (!casesPath) {
  console.error('usage: node scripts/timing.mjs <cases.json> [outDir] [--every=N]');
  process.exit(2);
}
const every = Number(flags.find((f) => f.startsWith('--every='))?.slice(8) ?? 1);

const ROOT = resolve(import.meta.dirname, '..');
const outDir = outDirArg ?? 'out/timing';
mkdirSync(join(ROOT, outDir), { recursive: true });

const cases = JSON.parse(readFileSync(resolve(casesPath), 'utf8'));

/** Every string a scene puts on screen, for a reading-time budget. */
const collectText = (o, acc = []) => {
  if (typeof o === 'string') acc.push(o);
  else if (Array.isArray(o)) o.forEach((v) => collectText(v, acc));
  else if (o && typeof o === 'object') {
    for (const [k, v] of Object.entries(o)) {
      if (k === 'preset' || k === 'id' || k.endsWith('Color') || k === 'audioUrl') continue;
      collectText(v, acc);
    }
  }
  return acc;
};

let failed = 0;
for (const c of cases) {
  const name = c.name ?? `case_${cases.indexOf(c)}`;
  const dur = c.scene.durationInFrames ?? 150;
  const fps = c.fps ?? 60;
  const spec = {
    width: 1080,
    height: 1920,
    fps,
    style: c.style ?? 'pop',
    scenes: [{ id: name, durationInFrames: dur, ...c.scene }],
  };
  const propsPath = join(ROOT, `.timing_${name}.json`);
  writeFileSync(propsPath, JSON.stringify(spec), 'utf8');

  const seqDir = join(ROOT, outDir, name);
  rmSync(seqDir, { recursive: true, force: true });
  mkdirSync(seqDir, { recursive: true });

  try {
    execFileSync(
      'npx',
      ['remotion', 'render', 'src/index.ts', 'Main', `${outDir}/${name}`,
       '--sequence', `--props=${propsPath}`, '--log=error',
       // Half scale: timing analysis compares frames to each other, and 540x960
       // resolves every reveal while quartering the decode cost.
       '--scale=0.5'],
      { cwd: ROOT, stdio: ['ignore', 'ignore', 'pipe'], timeout: 900000, shell: true }
    );
    const frames = existsSync(seqDir)
      ? readdirSync(seqDir).filter((f) => /\.(png|jpe?g)$/i.test(f))
      : [];
    if (every > 1) {
      // Thin the sequence on disk so the analysis step reads less.
      frames.forEach((f) => {
        const n = Number(f.replace(/\D/g, ''));
        if (n % every !== 0) rmSync(join(seqDir, f), { force: true });
      });
    }
    writeFileSync(
      join(ROOT, outDir, `${name}.meta.json`),
      JSON.stringify({ name, fps, durationInFrames: dur, every, text: collectText(c.scene) }, null, 2),
      'utf8'
    );
    console.log(`OK   ${name} -> ${outDir}/${name} (${frames.length} frames)`);
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
