# Qwen TTS Runtime Notes

## Official sources

The primary reference is the [Qwen3-TTS 12Hz 1.7B Base model card](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base) and the [Qwen3-TTS repository](https://github.com/QwenLM/Qwen3-TTS), retrieved on 2026-08-15.

The official documentation states that both **Qwen3-TTS-12Hz-1.7B-Base** and **Qwen3-TTS-12Hz-0.6B-Base** support voice cloning from a supplied reference audio clip and its transcript. It also documents installation through `pip install -U qwen-tts` and automatic model weight retrieval when loading a model by Hugging Face identifier.

The Python package probes for the system `sox` executable during import. Install it with `sudo apt-get install -y sox` on Ubuntu before starting the panel; MSF otherwise still renders with FFmpeg but produces a misleading missing-SoX warning on each worker startup.

## MSF decision

The runtime host has no CUDA device. MSF therefore selects the official **0.6B Base** checkpoint for CPU-only fallback (`Qwen/Qwen3-TTS-12Hz-0.6B-Base`) using `device_map="cpu"`, `torch.float32`, and eager attention. CUDA-capable hosts retain the 1.7B Base default. This decision trades inference speed and some capacity for a real local synthesis path instead of attempting an invalid `cuda:0` load.

The recovered `msf_narrator_recovered` reference is a 29.72-second, 24kHz mono internal MSF narration stem. Its transcript comes from local speech-to-text and remains explicitly reviewable in Voice Lab before high-stakes use.

## References

[1]: https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base "Qwen/Qwen3-TTS-12Hz-1.7B-Base model card"
[2]: https://github.com/QwenLM/Qwen3-TTS "Qwen3-TTS official GitHub repository"
