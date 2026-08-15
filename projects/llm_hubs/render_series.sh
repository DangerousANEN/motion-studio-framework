#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTION_DIR="$REPO_ROOT/remotion"
GENERATED_DIR="$REPO_ROOT/projects/llm_hubs/generated"
RENDERED_DIR="$REPO_ROOT/projects/llm_hubs/rendered"
REMOTION_BIN="$REMOTION_DIR/node_modules/.bin/remotion"

mkdir -p "$RENDERED_DIR"
cd "$REMOTION_DIR"

slugs=(
  "01_gemini37_flash_vs_sonnet5"
  "02_deepseek_v4pro_0813"
  "03_deepseek_v4pro_cost_clock"
  "04_grok46_long_agent"
  "05_august_model_costmap"
)

for slug in "${slugs[@]}"; do
  output="$RENDERED_DIR/${slug}.mp4"
  spec="$GENERATED_DIR/${slug}.spec.json"
  printf '\n=== Rendering %s ===\n' "$slug"
  "$REMOTION_BIN" render src/index.ts Main "$output" \
    --props="$spec" \
    --concurrency=2 \
    --browser-executable=/usr/bin/chromium
  printf '=== Complete: %s ===\n' "$output"
done
