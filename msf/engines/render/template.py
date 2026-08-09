"""MSF HTML Template Engine.

Generates self-contained 1080x1920 HTML documents for scene rendering with CSS Grid layouts,
preset typography, keyframe animations, camera transforms, subtitle display, and frame-accurate JS controls.
"""

from __future__ import annotations

import html
import json
import logging
from typing import Any, Optional

from msf.contracts.models import SceneComposition
from msf.libraries.camera_library import CameraLibrary
from msf.libraries.layout_library import LayoutLibrary
from msf.libraries.motion_library import MotionLibrary
from msf.libraries.typography_library import TypographyLibrary

logger = logging.getLogger(__name__)


class HTMLTemplateEngine:
    """Engine for building dynamic, self-contained 1080x1920 HTML/CSS/JS scene templates."""

    def __init__(self) -> None:
        self.layout_lib = LayoutLibrary()
        self.motion_lib = MotionLibrary()
        self.camera_lib = CameraLibrary()
        self.typo_lib = TypographyLibrary()

    def generate_scene_html(self, scene: SceneComposition, words: list[str]) -> str:
        """Generate complete self-contained HTML page (1080x1920) for Playwright rendering.

        Args:
            scene: The SceneComposition instance specifying layout, camera, motions, etc.
            words: List of word strings for subtitle synchronization.

        Returns:
            HTML string ready for rendering.
        """
        bg_color = scene.background_color or "#000000"

        # 1. Resolve Layout CSS Grid
        layout_obj = scene.layout
        if layout_obj and layout_obj.layout_id:
            try:
                layout_obj = self.layout_lib.get(layout_obj.layout_id)
            except KeyError:
                logger.warning("Layout ID %s not found in registry, falling back", layout_obj.layout_id)

        grid_template_areas = '"main"'
        grid_template_rows = "1fr"
        grid_template_columns = "1fr"
        row_gap = "0px"
        column_gap = "0px"

        if layout_obj and layout_obj.grid_areas:
            grid_template_areas = layout_obj.grid_areas.get("grid_template_areas", grid_template_areas)
            grid_template_rows = layout_obj.grid_areas.get("grid_template_rows", grid_template_rows)
            grid_template_columns = layout_obj.grid_areas.get("grid_template_columns", grid_template_columns)
            row_gap = layout_obj.grid_areas.get("row_gap", row_gap)
            column_gap = layout_obj.grid_areas.get("column_gap", column_gap)

        # Build grid area elements HTML
        # Extract unique grid area names from grid_template_areas string
        raw_areas = grid_template_areas.replace('"', '').replace("'", '').split()
        area_names = list(dict.fromkeys(a for a in raw_areas if a and a != "."))
        if not area_names:
            area_names = ["main"]

        # 2. Keyframes & Motion CSS
        keyframes_css_list = []
        element_animation_rules = []
        for i, m in enumerate(scene.motions):
            m_preset = m
            if m.preset_id:
                try:
                    m_preset = self.motion_lib.get(m.preset_id)
                except KeyError:
                    pass

            params = m_preset.params or {}
            kf = params.get("css_keyframes", "")
            if kf:
                keyframes_css_list.append(kf)

            anim_name = m_preset.preset_id
            dur = m_preset.duration or 1.0
            easing = m_preset.easing or "ease-out"
            # Apply to appropriate grid area or container
            target_area = area_names[i % len(area_names)]
            element_animation_rules.append(
                f".grid-area-{target_area} {{ animation: {anim_name} {dur}s {easing} both; }}"
            )

        # 3. Camera CSS
        camera_kf = ""
        camera_anim_rule = ""
        if scene.camera:
            cam_preset = scene.camera
            if cam_preset.preset_id:
                try:
                    cam_preset = self.camera_lib.get(cam_preset.preset_id)
                except KeyError:
                    pass

            if cam_preset.css_transform:
                camera_kf = cam_preset.css_transform
                cam_name = f"camera_{cam_preset.preset_id}"
                if f"@keyframes {cam_name}" not in camera_kf and "@keyframes" in camera_kf:
                    # extract or use keyframe name as is
                    pass
                else:
                    cam_name = f"camera_{cam_preset.preset_id}"
                
                # Check actual keyframe name in css_transform
                import re
                match = re.search(r"@keyframes\s+([a-zA-Z0-9_-]+)", camera_kf)
                if match:
                    cam_name = match.group(1)
                
                cam_dur = cam_preset.duration or scene.duration or 5.0
                cam_easing = cam_preset.easing or "linear"
                camera_anim_rule = f"#camera-stage {{ animation: {cam_name} {cam_dur}s {cam_easing} both; }}"

        # 4. Typography CSS
        try:
            heading_css = self.typo_lib.get_css("heading")
        except KeyError:
            heading_css = "font-family: 'Inter', sans-serif; font-size: 72px; font-weight: 700;"
        try:
            body_css = self.typo_lib.get_css("body")
        except KeyError:
            body_css = "font-family: 'Inter', sans-serif; font-size: 36px; font-weight: 400;"
        try:
            subtitle_css = self.typo_lib.get_css("subtitle_word")
        except KeyError:
            subtitle_css = "font-family: 'Inter', sans-serif; font-size: 42px; font-weight: 600;"
        # Grid area divs HTML
        grid_divs_html = []
        for idx, name in enumerate(area_names):
            asset_title = scene.scene_id
            asset_desc = ""
            if scene.assets and idx < len(scene.assets):
                # AssetResult has no `description` field -- it carries free-form
                # data in `metadata`. Reading .description raised AttributeError
                # and killed the whole pipeline run.
                asset = scene.assets[idx]
                asset_desc = str(asset.metadata.get("description", "") or "")
            
            accent_color = "#E6C475" if idx % 2 == 0 else "#00FF88"

            grid_divs_html.append(
                f'        <div class="grid-area-{name}" style="grid-area: {name}; padding: 20px;">\n'
                f'          <div class="area-content" style="background: rgba(22, 24, 28, 0.85); border: 2px solid {accent_color}; border-radius: 24px; padding: 48px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); backdrop-filter: blur(16px); text-align: center;">\n'
                f'            <div style="background: {accent_color}; color: #0E0F11; font-weight: 800; font-size: 24px; padding: 8px 24px; border-radius: 50px; display: inline-block; margin-bottom: 24px; text-transform: uppercase; letter-spacing: 2px;">\n'
                f'              .LLM HUBS EXPLORER\n'
                f'            </div>\n'
                f'            <h1 class="heading-text" style="color: #FFFFFF; font-size: 64px; font-weight: 900; line-height: 1.2; margin-bottom: 24px; text-shadow: 0 4px 20px rgba(0,0,0,0.5);">\n'
                f'              {html.escape(asset_desc or scene.scene_id)}\n'
                f'            </h1>\n'
                f'            <div style="height: 4px; width: 120px; background: {accent_color}; margin: 0 auto 24px auto; border-radius: 2px;"></div>\n'
                f'          </div>\n'
                f'        </div>'
            )
        grid_content_str = "\n".join(grid_divs_html)

        # Escape JSON safely for script tag
        words_json = json.dumps(words, ensure_ascii=False)

        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MSF Scene {html.escape(scene.scene_id)}</title>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    html, body {{
      width: 1080px;
      height: 1920px;
      overflow: hidden;
      background-color: {bg_color};
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      color: #FFFFFF;
    }}
    
    /* Viewport Stage & Camera Wrapper */
    #stage-container {{
      width: 1080px;
      height: 1920px;
      position: relative;
      overflow: hidden;
    }}

    #camera-stage {{
      width: 1080px;
      height: 1920px;
      position: absolute;
      top: 0;
      left: 0;
      transform-origin: center center;
    }}

    /* CSS Grid Layout */
    .layout-grid {{
      display: grid;
      width: 100%;
      height: 100%;
      padding: 140px 56px 240px 56px;
      grid-template-areas: {grid_template_areas};
      grid-template-rows: {grid_template_rows};
      grid-template-columns: {grid_template_columns};
      row-gap: {row_gap};
      column-gap: {column_gap};
    }}

    .area-content {{
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
    }}

    /* Typography Classes */
    .heading-text {{
      {heading_css}
    }}
    .body-text {{
      {body_css}
    }}
    .subtitle-style {{
      {subtitle_css}
    }}

    /* Subtitle Display Overlay */
    #subtitle-container {{
      position: absolute;
      bottom: 120px;
      left: 56px;
      right: 56px;
      height: 100px;
      display: flex;
      justify-content: center;
      align-items: center;
      text-align: center;
      pointer-events: none;
      z-index: 100;
    }}

    #subtitle-text {{
      {subtitle_css}
      background: rgba(0, 0, 0, 0.65);
      padding: 16px 32px;
      border-radius: 12px;
      backdrop-filter: blur(8px);
      max-width: 960px;
      word-wrap: break-word;
    }}

    .word-highlight {{
      color: #FFE600;
      font-weight: 800;
      text-shadow: 0 0 12px rgba(255, 230, 0, 0.5);
    }}

    /* Progress Bar */
    #progress-container {{
      position: absolute;
      bottom: 0;
      left: 0;
      width: 1080px;
      height: 12px;
      background: rgba(255, 255, 255, 0.15);
      z-index: 200;
    }}

    #progress-bar {{
      width: 0%;
      height: 100%;
      background: linear-gradient(90deg, #4F46E5, #9333EA);
      transition: width 0.033s linear;
    }}

    /* Keyframe Animations */
    {chr(10).join(keyframes_css_list)}
    {camera_kf}

    /* Animation Rules */
    {chr(10).join(element_animation_rules)}
    {camera_anim_rule}
  </style>
</head>
<body>
  <div id="stage-container">
    <div id="camera-stage">
      <div class="layout-grid">
{grid_content_str}
      </div>
    </div>

    <div id="subtitle-container">
      <div id="subtitle-text"></div>
    </div>

    <div id="progress-container">
      <div id="progress-bar"></div>
    </div>
  </div>

  <script>
    let currentWords = {words_json};
    let currentTitle = "";

    function setData(title, words) {{
      if (title !== undefined && title !== null) {{
        currentTitle = title;
        const mainHeading = document.querySelector('.heading-text');
        if (mainHeading) {{
          mainHeading.textContent = title;
        }}
      }}
      if (Array.isArray(words)) {{
        currentWords = words;
      }}
    }}

    function updateFrame(t, duration, wordIdx) {{
      // 1. Update Progress Bar
      const progressBar = document.getElementById('progress-bar');
      if (progressBar && duration > 0) {{
        const pct = Math.min(100, Math.max(0, (t / duration) * 100));
        progressBar.style.width = pct + '%';
      }}

      // 2. Update Subtitle Display (Sliding Window of 4-5 words)
      const subtitleText = document.getElementById('subtitle-text');
      if (subtitleText && currentWords && currentWords.length > 0) {{
        const activeIdx = (wordIdx !== undefined && wordIdx !== null && wordIdx >= 0)
          ? wordIdx
          : Math.floor((t / Math.max(0.001, duration)) * currentWords.length);

        const windowSize = 5;
        const startWindow = Math.max(0, Math.min(activeIdx - 2, currentWords.length - windowSize));
        const endWindow = Math.min(currentWords.length, startWindow + windowSize);

        const formatted = currentWords.slice(startWindow, endWindow).map((w, idx) => {{
          const globalIdx = startWindow + idx;
          if (globalIdx === activeIdx) {{
            return `<span class="word-highlight">${{w}}</span>`;
          }}
          return w;
        }}).join(' ');
        
        subtitleText.innerHTML = formatted;
      }}

      // 3. Sync Keyframe Animations & Camera Transform via Animation Playback
      const currentMs = t * 1000;
      document.getAnimations().forEach(anim => {{
        try {{
          anim.currentTime = currentMs;
          anim.pause();
        }} catch (e) {{
          // fallback if animation unsupported
        }}
      }});
    }}

    // Initial render setup
    if (currentWords && currentWords.length > 0) {{
      updateFrame(0, {scene.duration or 5.0}, 0);
    }}
  </script>
</body>
</html>
"""
        return html_doc
