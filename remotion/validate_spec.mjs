/**
 * Validate VideoSpec JSON files against the real Zod schema used at render time.
 *
 * Why this exists: the Python-side validate_spec() only checks preset names and
 * required keys. Zod enforces field *types* (statValue must be a number, cards
 * must be objects). A spec can pass Python and still make Remotion render a red
 * RENDER ERROR screen. Running this before render turns that silent failure into
 * a loud pre-flight error.
 *
 * The schema is TypeScript, so it is bundled on the fly with esbuild (already a
 * Remotion dependency) instead of requiring ts-node.
 *
 * Usage: node validate_spec.mjs <spec.json> [...more.json]
 * Exit code 0 = all valid, 1 = at least one invalid.
 */
import { readFileSync, writeFileSync, unlinkSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import esbuild from 'esbuild';

const files = process.argv.slice(2);
if (files.length === 0) {
  console.error('usage: node validate_spec.mjs <spec.json> [...]');
  process.exit(2);
}

// Bundle the TS schema into a temporary ESM file we can import.
const tmp = join(process.cwd(), '.schema.bundle.mjs');
await esbuild.build({
  entryPoints: [join(process.cwd(), 'src', 'VideoSpec.schema.ts')],
  bundle: true,
  format: 'esm',
  platform: 'node',
  outfile: tmp,
  logLevel: 'error',
});

const { VideoSpecSchema } = await import(pathToFileURL(tmp).href);

let failed = 0;

for (const file of files) {
  let parsed;
  try {
    parsed = JSON.parse(readFileSync(file, 'utf8'));
  } catch (err) {
    console.error(`INVALID ${file}: not readable JSON -- ${err.message}`);
    failed += 1;
    continue;
  }

  const result = VideoSpecSchema.safeParse(parsed);
  if (result.success) {
    const scenes = result.data.scenes ?? [];
    console.log(`VALID   ${file} -- ${scenes.length} scenes [${scenes.map((s) => s.preset).join(', ')}]`);
  } else {
    failed += 1;
    console.error(`INVALID ${file}`);
    for (const issue of result.error.issues) {
      console.error(`  path=${issue.path.join('.')} :: ${issue.message}`);
    }
  }
}

try {
  unlinkSync(tmp);
} catch {
  /* best effort cleanup */
}

if (failed > 0) {
  console.error(`\n${failed} spec(s) failed validation -- fix before rendering.`);
  process.exit(1);
}
console.log(`\nAll ${files.length} spec(s) valid.`);
