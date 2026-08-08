"""MSF Playwright Frame Renderer.

Executes Playwright headless Chromium to evaluate JS animation time codes and render 1080x1920 frames to disk.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright

from msf.config import RenderConfig
from msf.contracts.models import VoiceResult

logger = logging.getLogger(__name__)


class PlaywrightRenderer:
    """Renders HTML scene templates into sequential JPEG frames using Playwright headless Chromium."""

    def __init__(self, config: Optional[RenderConfig] = None) -> None:
        self.config = config or RenderConfig()

    async def render_scene(
        self,
        scene_html: str,
        voice_result: VoiceResult,
        output_dir: Path,
    ) -> Path:
        """Render scene_html into JPEG frames based on voice_result duration and config.fps.

        Args:
            scene_html: Complete HTML string representing the scene.
            voice_result: VoiceResult containing audio duration and word timestamps.
            output_dir: Directory where JPEG frames will be written.

        Returns:
            Path object pointing to output_dir containing saved frames.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        fps = self.config.fps or 30
        duration = voice_result.duration_seconds if voice_result and voice_result.duration_seconds > 0 else 5.0
        total_frames = max(1, int(round(duration * fps)))

        word_timestamps = voice_result.word_timestamps if voice_result else []

        logger.info(
            "Starting Playwright render: %d total frames @ %d fps (duration: %.2fs)",
            total_frames,
            fps,
            duration,
        )

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.config.headless)
            context = await browser.new_context(
                viewport={
                    "width": self.config.viewport_width or 1080,
                    "height": self.config.viewport_height or 1920,
                },
                device_scale_factor=1.0,
            )
            page = await context.new_page()

            # CRITICAL: Use set_content, NOT page.goto(file:///) on Windows
            await page.set_content(scene_html, wait_until="networkidle")

            for frame_idx in range(total_frames):
                t = frame_idx / fps

                # Determine active word index at timestamp t
                word_idx = -1
                if word_timestamps:
                    for w_i, wt in enumerate(word_timestamps):
                        if wt.start <= t <= wt.end:
                            word_idx = w_i
                            break
                    if word_idx == -1:
                        # Fallback to last passed word if past end
                        for w_i, wt in enumerate(word_timestamps):
                            if t >= wt.start:
                                word_idx = w_i

                # Update frame state in JS
                await page.evaluate(
                    "([t, dur, idx]) => updateFrame(t, dur, idx)",
                    [t, duration, word_idx],
                )

                frame_path = output_dir / f"frame_{frame_idx:05d}.jpg"
                await page.screenshot(
                    path=str(frame_path),
                    type="jpeg",
                    quality=90,
                    full_page=False,
                )

                if (frame_idx + 1) % 48 == 0 or (frame_idx + 1) == total_frames:
                    logger.info(
                        "Render progress: frame %d/%d (%.1f%%)",
                        frame_idx + 1,
                        total_frames,
                        ((frame_idx + 1) / total_frames) * 100,
                    )

            await browser.close()

        logger.info("Render complete. Frames saved to: %s", output_dir)
        return output_dir
