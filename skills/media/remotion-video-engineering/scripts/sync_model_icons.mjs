/**
 * Copy vendor brand icons from @lobehub/icons-static-svg into a Remotion
 * project's public/ directory, fixing the two things that make them unusable
 * inside an <img>.
 *
 * Install first:  npm i -D @lobehub/icons-static-svg
 * Run from the Remotion project root:  node scripts/sync-model-icons.mjs
 *
 * WHY COPY INSTEAD OF IMPORTING FROM node_modules
 * -----------------------------------------------
 * Remotion resolves asset URLs through staticFile(), which only looks inside
 * public/. Reaching into node_modules from a component works in the dev bundler
 * and then 404s in a rendered still — green locally, blank logos in the
 * delivered MP4.
 *
 * WHY currentColor IS REWRITTEN
 * -----------------------------
 * Roughly a fifth of these icons are monochrome and painted fill="currentColor".
 * Inside an <img> there is no inherited colour for currentColor to resolve
 * against, so the browser falls back to BLACK — an invisible logo on a dark
 * backdrop, with no error anywhere. A component cannot fix this because it
 * cannot pass a colour into an <img>. So fix the asset at copy time.
 *
 * CURATE THE LIST. Copying all ~900 puts 4.3 MB of unused SVG into every render
 * bundle, including text lockups that read as noise at avatar size.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, '..', 'node_modules', '@lobehub', 'icons-static-svg', 'icons');
const DEST = join(here, '..', 'public', 'model-icons');

/**
 * Verified against @lobehub/icons-static-svg@1.94.0. Note the absences:
 *   - no `glm` / `glm-color` (glmv is a different product) -> zhipu-color
 *   - no `openai-color` / `grok-color` -> monochrome only, rewritten to white
 *   - no `llama` brand mark -> meta-color
 */
const ICONS = [
  // Chinese labs
  'qwen-color', 'deepseek-color', 'zhipu-color', 'kimi-color', 'minimax-color',
  'yi-color', 'baichuan-color', 'stepfun-color', 'hunyuan-color', 'doubao-color',
  'wenxin-color', 'internlm-color', 'spark-color', 'sensenova-color',
  // Western labs
  'openai', 'claude-color', 'anthropic', 'gemini-color', 'meta-color',
  'mistral-color', 'cohere-color', 'grok', 'xai', 'gemma-color', 'aya-color',
  'dbrx-color', 'nova-color', 'perplexity-color', 'upstage-color',
  // Infra / runtimes that show up in comparison charts
  'nvidia-color', 'microsoft-color', 'google-color', 'aws-color', 'bedrock-color',
  'azure-color', 'vertexai-color', 'together-color', 'fireworks-color',
  'cerebras-color', 'huggingface-color', 'ollama', 'vllm-color',
];

mkdirSync(DEST, { recursive: true });

let copied = 0;
const missing = [];
for (const name of ICONS) {
  const src = join(SRC, `${name}.svg`);
  if (!existsSync(src)) {
    missing.push(name);
    continue;
  }
  let svg = readFileSync(src, 'utf8');
  const had = svg.includes('currentColor');
  svg = svg.replaceAll('currentColor', '#FFFFFF');
  // 1em sizing is meaningless in an <img>; give the asset a real viewport.
  svg = svg.replace('height="1em"', 'height="24"').replace('width="1em"', 'width="24"');
  writeFileSync(join(DEST, `${name}.svg`), svg, 'utf8');
  copied += 1;
  if (had) console.log(`  ${name}: monochrome -> white`);
}

console.log(`copied ${copied}/${ICONS.length} icons to public/model-icons/`);
if (missing.length) {
  // Loud: a silently missing icon degrades to a letter avatar and looks like a
  // deliberate design choice rather than a broken asset list.
  console.error(`MISSING from the vendor package: ${missing.join(', ')}`);
  process.exitCode = 1;
}
