
import { STYLE_KITS } from '../src/theme/styleKits.ts';
import { VideoSpecSchema } from '../src/VideoSpec.schema.ts';
const kits = {};
for (const [k, v] of Object.entries(STYLE_KITS)) {
  kits[k] = { theme: v.theme, fonts: v.fonts, backdrop: v.backdrop, surface: v.surface,
              transition: v.transition, effects: v.effects, description: v.description };
}
const themes = [];
for (const cand of ['pop','noir','glass','blueprint','sunset','broadcast','paper','vhs','ink','sunrise','forest','mono_warm','cyber_lime','candy','steel']) {
  const r = VideoSpecSchema.safeParse({ theme: cand, scenes: [{ durationInFrames: 60, preset: 'HeroKinetic' }] });
  if (r.success) themes.push(cand);
}
console.log(JSON.stringify({ kits, themes }));
