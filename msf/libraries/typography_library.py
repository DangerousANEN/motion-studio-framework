"""MSF Typography Library.

Provides typography presets with production CSS properties, 1080x1920 safe margins,
and WCAG AAA/AA contrast specifications.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional

from msf.contracts.models import BaseContract, TypographySpec


@dataclasses.dataclass
class TypographyPreset(BaseContract):
    """Detailed typography preset combining abstract spec with concrete CSS properties."""

    preset_id: str
    name: str
    font_family: str
    font_size_px: int
    font_weight: str | int
    line_height: float | str
    letter_spacing: str
    color: str
    text_transform: str = "none"
    contrast_ratio: float = 4.5
    safe_margins: dict[str, int] = dataclasses.field(
        default_factory=lambda: {"top": 140, "bottom": 240, "left": 56, "right": 56}
    )

    def to_typography_spec(self) -> TypographySpec:
        """Convert this preset to standard domain TypographySpec contract."""
        return TypographySpec(
            font_family=self.font_family,
            sizes={self.preset_id: self.font_size_px},
            line_heights={self.preset_id: float(self.line_height) if isinstance(self.line_height, (int, float)) else 1.2},
            contrast_ratio=self.contrast_ratio,
            safe_margins=self.safe_margins,
        )


class TypographyLibrary:
    """Registry and query interface for typography presets."""

    def __init__(self) -> None:
        self._presets: dict[str, TypographyPreset] = {}
        self._register_default_presets()

    def _register(self, preset: TypographyPreset) -> None:
        self._presets[preset.preset_id] = preset

    def get(self, preset_id: str) -> TypographyPreset:
        """Retrieve a TypographyPreset by its preset_id.

        Raises:
            KeyError: If preset_id is not found in the registry.
        """
        if preset_id not in self._presets:
            raise KeyError(f"TypographyPreset with id '{preset_id}' not found in registry.")
        return self._presets[preset_id]

    def list_all(self) -> list[TypographyPreset]:
        """Return all registered TypographyPresets."""
        return list(self._presets.values())

    def get_css(self, preset_id: str) -> str:
        """Generate complete CSS declarations for a given typography preset_id.

        Raises:
            KeyError: If preset_id is not found in the registry.
        """
        preset = self.get(preset_id)
        css_lines = [
            f"font-family: {preset.font_family}, sans-serif;",
            f"font-size: {preset.font_size_px}px;",
            f"font-weight: {preset.font_weight};",
            f"line-height: {preset.line_height};",
            f"letter-spacing: {preset.letter_spacing};",
            f"color: {preset.color};",
        ]
        if preset.text_transform != "none":
            css_lines.append(f"text-transform: {preset.text_transform};")

        return "\n".join(css_lines)

    def _register_default_presets(self) -> None:
        """Populate registry with font presets for 1080x1920 viewport."""

        standard_margins = {"top": 140, "bottom": 240, "left": 56, "right": 56}

        # 1. Heading (Inter Bold 72px)
        self._register(
            TypographyPreset(
                preset_id="heading",
                name="Heading",
                font_family="Inter",
                font_size_px=72,
                font_weight=700,
                line_height=1.1,
                letter_spacing="-0.02em",
                color="#FFFFFF",
                text_transform="none",
                contrast_ratio=15.0,
                safe_margins=standard_margins,
            )
        )

        # 2. Subheading (Inter SemiBold 48px)
        self._register(
            TypographyPreset(
                preset_id="subheading",
                name="Subheading",
                font_family="Inter",
                font_size_px=48,
                font_weight=600,
                line_height=1.2,
                letter_spacing="-0.01em",
                color="#E2E8F0",
                text_transform="none",
                contrast_ratio=12.0,
                safe_margins=standard_margins,
            )
        )

        # 3. Body (Inter Regular 36px)
        self._register(
            TypographyPreset(
                preset_id="body",
                name="Body Text",
                font_family="Inter",
                font_size_px=36,
                font_weight=400,
                line_height=1.4,
                letter_spacing="0em",
                color="#CBD5E1",
                text_transform="none",
                contrast_ratio=9.5,
                safe_margins=standard_margins,
            )
        )

        # 4. Caption (Inter Regular 28px)
        self._register(
            TypographyPreset(
                preset_id="caption",
                name="Caption",
                font_family="Inter",
                font_size_px=28,
                font_weight=400,
                line_height=1.3,
                letter_spacing="0.01em",
                color="#94A3B8",
                text_transform="none",
                contrast_ratio=7.0,
                safe_margins=standard_margins,
            )
        )

        # 5. Accent (Space Grotesk Bold 56px)
        self._register(
            TypographyPreset(
                preset_id="accent",
                name="Accent Display",
                font_family="Space Grotesk",
                font_size_px=56,
                font_weight=700,
                line_height=1.15,
                letter_spacing="-0.015em",
                color="#38BDF8",
                text_transform="none",
                contrast_ratio=8.5,
                safe_margins=standard_margins,
            )
        )

        # 6. KPI Number (JetBrains Mono Bold 96px)
        self._register(
            TypographyPreset(
                preset_id="kpi_number",
                name="KPI Number",
                font_family="JetBrains Mono",
                font_size_px=96,
                font_weight=700,
                line_height=1.0,
                letter_spacing="-0.03em",
                color="#FACC15",
                text_transform="none",
                contrast_ratio=13.5,
                safe_margins=standard_margins,
            )
        )

        # 7. Subtitle Word (Inter Bold 42px)
        self._register(
            TypographyPreset(
                preset_id="subtitle_word",
                name="Subtitle Word Highlight",
                font_family="Inter",
                font_size_px=42,
                font_weight=700,
                line_height=1.2,
                letter_spacing="0em",
                color="#FFFFFF",
                text_transform="uppercase",
                contrast_ratio=15.0,
                safe_margins={"top": 1400, "bottom": 240, "left": 56, "right": 56},
            )
        )

        # 8. Tag (Inter Medium 24px)
        self._register(
            TypographyPreset(
                preset_id="tag",
                name="Tag Label",
                font_family="Inter",
                font_size_px=24,
                font_weight=500,
                line_height=1.2,
                letter_spacing="0.05em",
                color="#64748B",
                text_transform="uppercase",
                contrast_ratio=6.0,
                safe_margins=standard_margins,
            )
        )
