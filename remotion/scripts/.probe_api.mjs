// Probe: does the programmatic bundle+render path work, and how fast is a warm render?
import { bundle } from '@remotion/bundler';
import { selectComposition, renderStill, renderMedia } from '@remotion/renderer';
import { resolve, join } from 'node:path';
import { statSync } from 'node:fs';

const ROOT = resolve(import.meta.dirname, '..');
const t0 = Date.now();
const serveUrl = await bundle({
  entryPoint: join(ROOT, 'src/index.ts'),
  onProgress: () => {},
});
console.log('bundle_sec', ((Date.now() - t0) / 1000).toFixed(1), serveUrl);

const spec = {
  width: 1080, height: 1920, fps: 60, style: 'pop',
  scenes: [
    { id: 'a', preset: 'HeroKinetic', durationInFrames: 60, title: 'ПЕРВАЯ' },
    { id: 'b', preset: 'QuoteCard', durationInFrames: 60, text: 'Вторая сцена', transition: { type: 'clockWipe', durationInFrames: 20 } },
  ],
};

let t = Date.now();
const comp = await selectComposition({ serveUrl, id: 'Main', inputProps: spec });
console.log('select_sec', ((Date.now() - t) / 1000).toFixed(1), 'dur', comp.durationInFrames);

t = Date.now();
await renderStill({
  serveUrl, composition: comp, output: join(ROOT, 'out/.probe_still.png'),
  frame: 40, inputProps: spec,
});
console.log('still_sec', ((Date.now() - t) / 1000).toFixed(1),
  statSync(join(ROOT, 'out/.probe_still.png')).size);

t = Date.now();
await renderStill({
  serveUrl, composition: comp, output: join(ROOT, 'out/.probe_still2.png'),
  frame: 55, inputProps: spec,
});
console.log('still2_warm_sec', ((Date.now() - t) / 1000).toFixed(1));

t = Date.now();
await renderMedia({
  serveUrl, composition: comp, codec: 'h264',
  outputLocation: join(ROOT, 'out/.probe_clip.mp4'),
  inputProps: spec, frameRange: [30, 90],
  crf: 26, scale: 0.5, concurrency: 4,
  onProgress: () => {},
});
console.log('clip_sec', ((Date.now() - t) / 1000).toFixed(1),
  statSync(join(ROOT, 'out/.probe_clip.mp4')).size);
