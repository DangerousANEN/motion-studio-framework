# Motion Studio Framework (MSF) - Qwen3-TTS 1.7B Integration Guide

This reference documents how `Qwen3TTSModel` (1.7B CustomVoice & 1.7B Base Zero-Shot Voice Clone) is integrated into MSF's `VoiceAgent` for vertical promo Shorts generation (1080x1920).

## MSF VoiceAgent Implementation Pattern

### 1. Preset Speaker Synthesis (1.7B-CustomVoice)
```python
import os
import torch
import soundfile as sf
import warnings
from qwen_tts import Qwen3TTSModel

class Qwen3TTSVoiceEngine:
    def __init__(self, speaker: str = "Serena"):
        self.speaker = speaker
        warnings.filterwarnings('ignore')
        os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
        self.model = Qwen3TTSModel.from_pretrained(
            'Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice',
            device_map='cuda:0',
            dtype=torch.bfloat16,
            attn_implementation='eager'
        )

    def synthesize(self, text: str, output_path: str, peak_level: float = 0.95) -> str:
        wavs, sr = self.model.generate_custom_voice(
            text=text,
            language='Russian',
            speaker=self.speaker
        )
        audio = wavs[0]
        max_val = abs(audio).max()
        if max_val > 0:
            audio = audio / max_val * peak_level

        sf.write(output_path, audio, sr)
        return output_path
```

### 2. Zero-Shot Voice Cloning (1.7B-Base)
```python
def _synthesize_qwen3_tts_clone(self, text: str, output_path: str, ref_audio: str) -> bool:
    """Zero-shot voice cloning from user reference audio."""
    model = Qwen3TTSModel.from_pretrained(
        'Qwen/Qwen3-TTS-12Hz-1.7B-Base',
        device_map='cuda:0',
        dtype=torch.bfloat16,
        attn_implementation='eager'
    )
    wavs, sr = model.generate_voice_clone(
        text=text,
        language='Russian',
        ref_audio=ref_audio,
        x_vector_only_mode=True
    )
    audio = wavs[0]
    max_val = abs(audio).max()
    if max_val > 0:
        audio = audio / max_val * 0.95
    sf.write(output_path, audio, sr)
    return True
```

## Key Requirements for High-Volume Promo Output:
1. **Phonetic Spelling:** Always transliterate English words into Russian phonetics (`"ЛЛМ Хабс"`, `"Гитхаб"`, `"ДевТулз"`, `"Оупен сорс"`) for clean pronunciation.
2. **Audio Normalization:** Always apply `audio / max_val * 0.95` (-0.4 dB peak) so the voice is loud and clear. Avoid aggressive FFmpeg filters like `equalizer=f=3000` or `acompressor` that introduce high-pitched squeaks ("писк").
3. **HTML UI & Subtitles:** Render styled glassmorphism cards instead of `area top`/`area body` text. Display a sliding 5-word window for subtitles.
