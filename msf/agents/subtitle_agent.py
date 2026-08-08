"""MSF Subtitle Agent.

Converts word timestamps into formatted, styled SubtitleEntry elements.
"""

from __future__ import annotations

from typing import Any, Optional

from msf.agents.base import BaseAgent
from msf.contracts.models import (
    ReviewResult,
    ReviewVerdict,
    SubtitleEntry,
    VoiceResult,
    WordTimestamp,
)
from msf.libraries.typography_library import TypographyLibrary
from msf.utils.logger import StageLogger, setup_logger


class SubtitleAgent(BaseAgent[VoiceResult, list[SubtitleEntry]]):
    """Agent responsible for creating styled subtitle entries from voice timestamps."""

    def __init__(
        self,
        config: Optional[MSFConfig] = None,
        logger: Optional[StageLogger | logging.Logger] = None,
        typography_lib: Optional[TypographyLibrary] = None,
    ) -> None:
        cfg = config or MSFConfig()
        log = logger or setup_logger(self.__class__.__name__)
        super().__init__(config=cfg, logger=log)
        self.typography_lib = typography_lib or TypographyLibrary()

    def execute(self, input_data: VoiceResult | dict[str, Any]) -> list[SubtitleEntry]:
        """Execute subtitle generation from a VoiceResult object."""
        if isinstance(input_data, VoiceResult):
            voice_result = input_data
        elif isinstance(input_data, dict):
            voice_result = VoiceResult.from_dict(input_data)
        else:
            voice_result = VoiceResult()

        timestamps = voice_result.word_timestamps
        if not timestamps:
            return []

        # Get styling specs from TypographyLibrary
        try:
            preset = self.typography_lib.get("heading")
        except KeyError:
            preset = self.typography_lib.list_all()[0]
        font_family = preset.font_family
        font_size = preset.font_size_px
        contrast_ratio = preset.contrast_ratio

        base_style = {
            "font_family": font_family,
            "font_size": font_size,
            "color": preset.color,
            "text_shadow": "0px 4px 12px rgba(0, 0, 0, 0.8)",
            "text_transform": preset.text_transform if preset.text_transform != "none" else "uppercase",
            "contrast_ratio": contrast_ratio,
        }

        base_position = {
            "bottom": "280px",
            "left": "50%",
            "transform": "translateX(-50%)",
            "text_align": "center",
            "width": "90%",
        }

        # Group words into subtitle lines (max 3-4 words per line)
        max_words_per_line = 3
        subtitles: list[SubtitleEntry] = []

        chunk_words: list[WordTimestamp] = []
        for i, wt in enumerate(timestamps):
            chunk_words.append(wt)
            if len(chunk_words) == max_words_per_line or i == len(timestamps) - 1:
                line_text = " ".join(w.word for w in chunk_words)
                start_time = chunk_words[0].start
                end_time = chunk_words[-1].end

                # Ensure minimum visible duration of 0.3s
                if end_time - start_time < 0.3:
                    end_time = start_time + 0.3

                subtitles.append(
                    SubtitleEntry(
                        word=line_text,
                        start=round(start_time, 2),
                        end=round(end_time, 2),
                        style=dict(base_style),
                        position=dict(base_position),
                    )
                )
                chunk_words = []

        return subtitles

    def validate(self, output: list[SubtitleEntry]) -> ReviewResult:
        """Validate subtitle entries."""
        issues: list[str] = []

        if not output or len(output) == 0:
            issues.append("Subtitle entries list is empty.")
        if issues:
            return ReviewResult(
                stage="subtitles",
                verdict=ReviewVerdict.FAIL,
                score=0.0,
                issues=issues,
                suggestions=["Ensure subtitle entries exist and timing covers text."],
            )

        return ReviewResult(
            stage="subtitles",
            verdict=ReviewVerdict.PASS,
            score=1.0,
            issues=[],
            suggestions=[],
        )
