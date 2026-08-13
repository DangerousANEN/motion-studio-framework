# Qwen3-TTS Windows Setup & Troubleshooting Reference

## Key Models
- `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` (4.21 GB) - 9 speaker presets + instruction control
- `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` (2.33 GB) - Lightweight 9 speaker presets
- `Qwen/Qwen3-TTS-12Hz-1.7B-Base` - 3-second rapid voice cloning
- `Qwen/Qwen3-TTS-Tokenizer-12Hz` (0.64 GB) - Audio codec tokenizer

## Troubleshooting & Common Pitfalls

### 1. PyTorch SDPA mRoPE Tensor Dimension Mismatch
**Error:** `RuntimeError: The expanded size of the tensor (17) must match the existing size (32) at non-singleton dimension 3`
**Cause:** PyTorch's native SDPA attention cannot handle 3D multi-dimensional rotary position embeddings (mRoPE) without `flash-attn`.
**Fix:** Force `attn_implementation="eager"` in `Qwen3TTSModel.from_pretrained(...)`.

### 2. `create_causal_mask()` TypeError (Argument Name Mismatch)
**Error:** `TypeError: create_causal_mask() got an unexpected keyword argument 'inputs_embeds'`
**Cause:** Upstream `qwen_tts 0.1.1` passes `inputs_embeds` (with 's') to `create_causal_mask()`, but `transformers` expects `input_embeds` (without 's').
**Fix:** Edit `qwen_tts/core/models/modeling_qwen3_tts.py` and `modeling_qwen3_tts_tokenizer_v2.py`:
Change `"inputs_embeds": inputs_embeds` to `"input_embeds": inputs_embeds`.

### 3. Missing `cache_position` Argument
**Error:** `TypeError: create_causal_mask() missing 1 required positional argument: 'cache_position'`
**Cause:** `transformers==4.57.3` requires `cache_position` in `create_causal_mask()`.
**Fix:** Add `cache_position=cache_position` to the `create_causal_mask(...)` keyword arguments in `modeling_qwen3_tts.py`.
