/**
 * Copy the model-brand icons this project uses out of
 * @lobehub/icons-static-svg and into public/model-icons/.
 *
 * WHY COPY INSTEAD OF IMPORTING FROM node_modules
 * -----------------------------------------------
 * Remotion resolves asset URLs through `staticFile()`, which only looks inside
 * public/. Reaching into node_modules from a component would work in the dev
 * bundler and then 404 in a rendered still, which is the worst failure shape:
 * green locally, blank logos in the delivered MP4.
 *
 * WHY currentColor IS REWRITTEN
 * -----------------------------
 * Roughly half of these icons are monochrome and painted `fill="currentColor"`
 * (grok, xai, openai, anthropic, meta, microsoft). Inside an <img> tag there is
 * no inherited colour for `currentColor` to resolve against, so the browser
 * falls back to BLACK — an invisible logo on this library's dark backdrop, with
 * no error anywhere. Every occurrence is rewritten to white at copy time so the
 * asset is correct by construction rather than by hoping a component sets a
 * colour it cannot actually pass into an <img>.
 *
 * Run: node scripts/sync-model-icons.mjs
 */
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, '..', 'node_modules', '@lobehub', 'icons-static-svg', 'icons');
const DEST = join(here, '..', 'public', 'model-icons');

/**
 * Curated list. Deliberately NOT "copy all 903": the vendor ships text
 * lockups and product marks that read as noise at avatar size, and 4.3 MB of
 * unused SVG in public/ ends up in every render bundle.
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
  // See the header: currentColor inside <img> resolves to black, not to the
  // surrounding text colour.
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
  // Loud, because a silently missing icon degrades to a letter avatar and looks
  // like a deliberate design choice rather than a broken asset list.
  console.error(`MISSING from the vendor package: ${missing.join(', ')}`);
  process.exitCode = 1;
}
