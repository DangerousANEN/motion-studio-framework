"""MSF Layout Library.

Provides composition layout templates for 1080x1920 vertical video scenes.
Each layout specifies CSS grid templates, safe zones, and text block capacity.
"""

from __future__ import annotations

from typing import Any, Optional

from msf.contracts.models import LayoutChoice


class LayoutLibrary:
    """Registry and query interface for scene layout templates."""

    def __init__(self) -> None:
        self._layouts: dict[str, LayoutChoice] = {}
        self._register_default_layouts()

    def _register(self, layout: LayoutChoice) -> None:
        self._layouts[layout.layout_id] = layout

    def get(self, layout_id: str) -> LayoutChoice:
        """Retrieve a LayoutChoice by its layout_id.

        Raises:
            KeyError: If layout_id is not found in the registry.
        """
        if layout_id not in self._layouts:
            raise KeyError(f"LayoutChoice with id '{layout_id}' not found in registry.")
        return self._layouts[layout_id]

    def list_all(self) -> list[LayoutChoice]:
        """Return all registered LayoutChoices."""
        return list(self._layouts.values())

    def get_by_max_blocks(self, n: int) -> list[LayoutChoice]:
        """Return LayoutChoices that can accommodate at least n text blocks."""
        return [layout for layout in self._layouts.values() if layout.max_text_blocks >= n]

    def _register_default_layouts(self) -> None:
        """Populate registry with 10+ production layout templates tuned for 1080x1920."""

        standard_safe_zone = {
            "top": 140,
            "bottom": 240,
            "left": 56,
            "right": 56,
            "width": 968,
            "height": 1540,
        }

        # 1. Centered Single
        self._register(
            LayoutChoice(
                layout_id="centered_single",
                name="Centered Single",
                grid_areas={
                    "grid_template_areas": '"main"',
                    "grid_template_rows": "1fr",
                    "grid_template_columns": "1fr",
                    "justify_items": "center",
                    "align_items": "center",
                },
                safe_zones=standard_safe_zone,
                max_text_blocks=1,
            )
        )

        # 2. Title Body
        self._register(
            LayoutChoice(
                layout_id="title_body",
                name="Title Body",
                grid_areas={
                    "grid_template_areas": '"title" "body"',
                    "grid_template_rows": "auto 1fr",
                    "grid_template_columns": "1fr",
                    "row_gap": "40px",
                },
                safe_zones=standard_safe_zone,
                max_text_blocks=2,
            )
        )

        # 3. Split Horizontal
        self._register(
            LayoutChoice(
                layout_id="split_horizontal",
                name="Split Horizontal",
                grid_areas={
                    "grid_template_areas": '"top" "bottom"',
                    "grid_template_rows": "1fr 1fr",
                    "grid_template_columns": "1fr",
                    "row_gap": "32px",
                },
                safe_zones=standard_safe_zone,
                max_text_blocks=2,
            )
        )

        # 4. Split Vertical
        self._register(
            LayoutChoice(
                layout_id="split_vertical",
                name="Split Vertical",
                grid_areas={
                    "grid_template_areas": '"left right"',
                    "grid_template_rows": "1fr",
                    "grid_template_columns": "1fr 1fr",
                    "column_gap": "32px",
                },
                safe_zones=standard_safe_zone,
                max_text_blocks=2,
            )
        )

        # 5. Thirds Grid
        self._register(
            LayoutChoice(
                layout_id="thirds_grid",
                name="Thirds Grid",
                grid_areas={
                    "grid_template_areas": '"top" "middle" "bottom"',
                    "grid_template_rows": "1fr 1fr 1fr",
                    "grid_template_columns": "1fr",
                    "row_gap": "24px",
                },
                safe_zones=standard_safe_zone,
                max_text_blocks=3,
            )
        )

        # 6. Quad Grid
        self._register(
            LayoutChoice(
                layout_id="quad_grid",
                name="Quad Grid",
                grid_areas={
                    "grid_template_areas": '"top_left top_right" "bottom_left bottom_right"',
                    "grid_template_rows": "1fr 1fr",
                    "grid_template_columns": "1fr 1fr",
                    "gap": "24px",
                },
                safe_zones=standard_safe_zone,
                max_text_blocks=4,
            )
        )

        # 7. Sidebar Main
        self._register(
            LayoutChoice(
                layout_id="sidebar_main",
                name="Sidebar Main",
                grid_areas={
                    "grid_template_areas": '"sidebar main"',
                    "grid_template_rows": "1fr",
                    "grid_template_columns": "30% 70%",
                    "column_gap": "24px",
                },
                safe_zones=standard_safe_zone,
                max_text_blocks=3,
            )
        )

        # 8. Full Bleed
        self._register(
            LayoutChoice(
                layout_id="full_bleed",
                name="Full Bleed",
                grid_areas={
                    "grid_template_areas": '"canvas"',
                    "grid_template_rows": "100%",
                    "grid_template_columns": "100%",
                },
                safe_zones={
                    "top": 0,
                    "bottom": 0,
                    "left": 0,
                    "right": 0,
                    "width": 1080,
                    "height": 1920,
                },
                max_text_blocks=1,
            )
        )

        # 9. Bottom Bar
        self._register(
            LayoutChoice(
                layout_id="bottom_bar",
                name="Bottom Bar",
                grid_areas={
                    "grid_template_areas": '"main" "bar"',
                    "grid_template_rows": "1fr 180px",
                    "grid_template_columns": "1fr",
                    "row_gap": "20px",
                },
                safe_zones=standard_safe_zone,
                max_text_blocks=2,
            )
        )

        # 10. Dashboard
        self._register(
            LayoutChoice(
                layout_id="dashboard",
                name="Dashboard KPI Grid",
                grid_areas={
                    "grid_template_areas": '"header header" "kpi1 kpi2" "kpi3 kpi4"',
                    "grid_template_rows": "auto 1fr 1fr",
                    "grid_template_columns": "1fr 1fr",
                    "gap": "20px",
                },
                safe_zones=standard_safe_zone,
                max_text_blocks=5,
            )
        )

        # 11. Timeline Vertical
        self._register(
            LayoutChoice(
                layout_id="timeline_vertical",
                name="Timeline Vertical",
                grid_areas={
                    "grid_template_areas": '"step1" "step2" "step3" "step4"',
                    "grid_template_rows": "repeat(4, 1fr)",
                    "grid_template_columns": "1fr",
                    "row_gap": "16px",
                },
                safe_zones=standard_safe_zone,
                max_text_blocks=4,
            )
        )
