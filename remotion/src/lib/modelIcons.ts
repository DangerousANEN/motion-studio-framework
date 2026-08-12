/**
 * Map a model name to its brand icon in public/model-icons/.
 *
 * WHY THIS IS PATTERN MATCHING AND NOT A LOOKUP TABLE
 * --------------------------------------------------
 * Nothing feeding this library emits canonical vendor slugs. Labels arrive as
 * whatever the script or the research node produced: "Qwen3.6-235B-A22B",
 * "GLM-5.2-Air", "Llama-4-Scout-109B", "claude opus 4.6". A dictionary keyed on
 * exact names would miss on the next release and silently fall back to a letter
 * avatar — which reads as a design choice, not as a miss. Matching on the brand
 * SUBSTRING survives version bumps: "Qwen4-Max" resolves the day it ships.
 *
 * ORDER MATTERS. `glm` must be tested before `gpt`-style short tokens and
 * `llama` before `meta`, because several patterns can match one string and the
 * first hit wins. Specific before generic, always.
 */
import { staticFile } from 'remotion';

export type ModelIcon = {
  /** Path usable directly as an <img src>. */
  src: string;
  /** Brand slug, for debugging and for tests to assert against. */
  slug: string;
};

/**
 * [pattern, icon slug]. Patterns are matched against the lower-cased label with
 * separators stripped, so "GLM-5.2-Air", "glm 5.2 air" and "glm5.2air" all hit.
 */
const RULES: Array<[RegExp, string]> = [
  // ---- Chinese labs. GLM is Zhipu's model family; the vendor package ships no
  // `glm` icon (only `glmv`, a different product), so Zhipu's mark is correct.
  [/qwen|tongyi/, 'qwen-color'],
  [/deepseek/, 'deepseek-color'],
  [/\bglm\b|glm\d|zhipu|chatglm/, 'zhipu-color'],
  [/kimi|moonshot/, 'kimi-color'],
  [/minimax|abab/, 'minimax-color'],
  [/\byi[-\d]|yi\d|01ai/, 'yi-color'],
  [/baichuan/, 'baichuan-color'],
  [/stepfun|step\d/, 'stepfun-color'],
  [/hunyuan|tencent/, 'hunyuan-color'],
  [/doubao|seed\d/, 'doubao-color'],
  [/wenxin|ernie|baidu/, 'wenxin-color'],
  [/internlm|intern-/, 'internlm-color'],
  [/sensenova|sensetime/, 'sensenova-color'],
  [/sparkdesk|iflytek/, 'spark-color'],
  // ---- Western labs. Claude before Anthropic: the model name is what appears
  // on screen, and claude-color is the recognisable mark.
  [/claude/, 'claude-color'],
  [/anthropic/, 'anthropic'],
  [/gpt|openai|\bo[1-9]\b|davinci|dall-?e|whisper|sora/, 'openai'],
  [/gemini|palm|bard/, 'gemini-color'],
  [/gemma/, 'gemma-color'],
  [/llama|codellama/, 'meta-color'],
  [/\bmeta\b/, 'meta-color'],
  [/mistral|mixtral|codestral|magistral|devstral/, 'mistral-color'],
  [/command-?r|cohere/, 'cohere-color'],
  [/aya/, 'aya-color'],
  [/grok/, 'grok'],
  [/\bxai\b/, 'xai'],
  [/dbrx|databricks/, 'dbrx-color'],
  [/nova/, 'nova-color'],
  [/perplexity|sonar/, 'perplexity-color'],
  [/solar|upstage/, 'upstage-color'],
  [/phi-?\d|microsoft/, 'microsoft-color'],
  [/nemotron|nvidia/, 'nvidia-color'],
  // ---- Infra / runtimes that appear in comparison charts.
  [/bedrock/, 'bedrock-color'],
  [/vertex/, 'vertexai-color'],
  [/azure/, 'azure-color'],
  [/\baws\b|amazon/, 'aws-color'],
  [/\bgoogle\b/, 'google-color'],
  [/together/, 'together-color'],
  [/fireworks/, 'fireworks-color'],
  [/cerebras/, 'cerebras-color'],
  [/huggingface|hugging-face/, 'huggingface-color'],
  [/ollama/, 'ollama'],
  [/vllm/, 'vllm-color'],
];

/**
 * Resolve a label to a brand icon, or null when nothing matches.
 *
 * Returning null rather than a placeholder is deliberate: the caller already has
 * a good fallback (the gradient letter avatar), and inventing a generic "AI chip"
 * icon would make an unrecognised model look like a recognised one.
 */
export const resolveModelIcon = (label?: string): ModelIcon | null => {
  if (!label) return null;
  // Strip separators so "GLM-5.2-Air" and "glm 5.2 air" normalise the same way,
  // while keeping digits: several rules key on them (yi-34b, phi-4, step2).
  const key = String(label).toLowerCase();
  for (const [pattern, slug] of RULES) {
    if (pattern.test(key)) {
      return { slug, src: staticFile(`model-icons/${slug}.svg`) };
    }
  }
  return null;
};

/** Slugs referenced by RULES — used by the asset test to prove each file exists. */
export const REFERENCED_SLUGS = Array.from(new Set(RULES.map(([, slug]) => slug)));
