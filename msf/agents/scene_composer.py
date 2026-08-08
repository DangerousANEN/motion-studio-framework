"""MSF Scene Composer Agent.

Assembles scene design decisions (layout, camera, motion, assets) for individual video scenes.
"""

from __future__ import annotations
import json
import logging
from typing import Any, Optional

from msf.agents.base import BaseAgent
from msf.agents.llm_client import LLMClient
from msf.config import MSFConfig
from msf.contracts.models import (
    AssetRequest,
    AssetResult,
    AssetType,
    CameraPreset,
    LayoutChoice,
    MotionPreset,
    ReviewResult,
    ReviewVerdict,
    SceneComposition,
    SceneSpec,
)
from msf.libraries.camera_library import CameraLibrary
from msf.libraries.layout_library import LayoutLibrary
from msf.libraries.motion_library import MotionLibrary
from msf.utils.logger import StageLogger, setup_logger


class SceneComposer(BaseAgent[dict[str, Any], SceneComposition]):
    """Agent responsible for selecting layout, camera, motions, and asset requests for a scene."""

    def __init__(
        self,
        config: Optional[MSFConfig] = None,
        logger: Optional[StageLogger | logging.Logger] = None,
        llm: Optional[LLMClient] = None,
        layout_lib: Optional[LayoutLibrary] = None,
        camera_lib: Optional[CameraLibrary] = None,
        motion_lib: Optional[MotionLibrary] = None,
    ) -> None:
        cfg = config or MSFConfig()
        log = logger or setup_logger(self.__class__.__name__)
        super().__init__(config=cfg, logger=log)
        if llm is not None:
            self.llm = llm
        self.layout_lib = layout_lib or LayoutLibrary()
        self.camera_lib = camera_lib or CameraLibrary()
        self.motion_lib = motion_lib or MotionLibrary()

    def execute(self, input_data: dict[str, Any]) -> SceneComposition:
        """Execute scene composition for a single scene specification."""
        raw_scene = input_data.get("scene_spec") or input_data.get("scene") or input_data
        if isinstance(raw_scene, SceneSpec):
            scene_spec = raw_scene
        elif isinstance(raw_scene, dict):
            scene_spec = SceneSpec.from_dict(raw_scene)
        else:
            scene_spec = SceneSpec(scene_id="scene_001")

        all_layouts = self.layout_lib.list_all()
        layout_options = [
            {"layout_id": l.layout_id, "name": l.name, "max_text_blocks": l.max_text_blocks}
            for l in all_layouts
        ]

        all_motions = self.motion_lib.list_all()
        motion_options = [
            {"preset_id": m.preset_id, "name": m.name, "animation_type": str(m.animation_type)}
            for m in all_motions
        ]

        prompt = (
            f"Скомпонуй визуальные элементы для сцены видео.\n"
            f"ID сцены: {scene_spec.scene_id}\n"
            f"Название: {scene_spec.title}\n"
            f"Текст озвучки: {scene_spec.narration_text}\n"
            f"Информационная нагрузка: {scene_spec.information_load}\n"
            f"Визуальная цель: {scene_spec.visual_goal}\n"
            f"Эмоция: {scene_spec.emotion}\n"
            f"Длительность: {scene_spec.duration} сек.\n\n"
            f"Доступные варианты макетов (layout_id):\n"
            f"{json.dumps(layout_options, ensure_ascii=False)}\n\n"
            f"Доступные варианты анимаций (motion preset_id):\n"
            f"{json.dumps(motion_options, ensure_ascii=False)}\n\n"
            f"Выбери решения для этой сцены и верни JSON со следующими полями:\n"
            f"1. layout_id: выбери наиболее подходящий layout_id из списка доступных на основе info_load и visual_goal.\n"
            f"2. camera_id: выбери preset_id камеры, совместимый с выбранным макетом (например: 'static_center', 'slow_zoom_in', 'pan_left', 'parallax_subtle').\n"
            f"3. motion_ids: выбери от 2 до 4 preset_id анимаций движения из списка доступных.\n"
            f"4. asset_requests: список из 1-3 запросов на визуальные ассеты, где каждый ассет это объект с полями:\n"
            f"   - asset_id: строка (напр. '{scene_spec.scene_id}_bg')\n"
            f"   - asset_type: 'image', 'vector', 'icon', 'video', 'text_block' или 'html'\n"
            f"   - description: детальное описание требуемого изображения/ассета на русском или английском\n"
            f"5. background_color: HEX-цвет фона (например, '#0f172a')\n"
        )

        system_prompt = (
            "Ты главный художник и арт-директор моушн-дизайна. Выбери идеальный макет, камеру и анимации для сцены. "
            "Отвечай строго в формате JSON."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        response_dict = self.llm.chat_json(messages=messages)
        # 1. Resolve layout
        layout_id = response_dict.get("layout_id", "centered_single")
        try:
            layout = self.layout_lib.get(layout_id)
        except KeyError:
            layout = self.layout_lib.list_all()[0]

        # 2. Resolve camera
        compatible_cameras = self.camera_lib.get_compatible(layout.layout_id)
        camera_id = response_dict.get("camera_id")
        camera = None
        if camera_id:
            try:
                candidate = self.camera_lib.get(camera_id)
                if "*" in candidate.compatible_layouts or layout.layout_id in candidate.compatible_layouts:
                    camera = candidate
            except KeyError:
                pass

        if camera is None:
            camera = compatible_cameras[0] if compatible_cameras else self.camera_lib.list_all()[0]

        # 3. Resolve motions (2-4 animations)
        motion_ids = response_dict.get("motion_ids", [])
        if not isinstance(motion_ids, list):
            motion_ids = []

        motions: list[MotionPreset] = []
        for m_id in motion_ids:
            try:
                motions.append(self.motion_lib.get(m_id))
            except KeyError:
                continue

        if len(motions) < 2:
            all_m = self.motion_lib.list_all()
            motions = all_m[:2]

        # 4. Resolve AssetRequests -> AssetResults
        raw_requests = response_dict.get("asset_requests", [])
        assets: list[AssetResult] = []
        if isinstance(raw_requests, list):
            for i, req_dict in enumerate(raw_requests):
                if isinstance(req_dict, dict):
                    a_id = req_dict.get("asset_id", f"{scene_spec.scene_id}_asset_{i+1}")
                    desc = req_dict.get("description", scene_spec.visual_goal)
                    a_type_str = req_dict.get("asset_type", "image")
                    try:
                        a_type = AssetType(a_type_str)
                    except ValueError:
                        a_type = AssetType.IMAGE

                    req = AssetRequest(
                        asset_id=a_id,
                        asset_type=a_type,
                        description=desc,
                        dimensions=(1080, 1920),
                    )
                    assets.append(
                        AssetResult(
                            asset_id=req.asset_id,
                            file_path=f"assets/{req.asset_id}.png",
                            format="png",
                            dimensions=req.dimensions,
                            metadata={"description": req.description, "asset_type": req.asset_type.value},
                        )
                    )

        if not assets:
            assets.append(
                AssetResult(
                    asset_id=f"{scene_spec.scene_id}_bg",
                    file_path=f"assets/{scene_spec.scene_id}_bg.png",
                    format="png",
                    metadata={"description": scene_spec.visual_goal},
                )
            )

        bg_color = response_dict.get("background_color", "#0f172a")

        return SceneComposition(
            scene_id=scene_spec.scene_id,
            layout=layout,
            camera=camera,
            motions=motions,
            assets=assets,
            background_color=bg_color,
            duration=scene_spec.duration,
        )

    def validate(self, output: SceneComposition) -> ReviewResult:
        """Validate scene composition against design rules."""
        issues: list[str] = []

        # Check layout exists in library
        if output.layout is None:
            issues.append("Scene layout is missing.")
        else:
            try:
                self.layout_lib.get(output.layout.layout_id)
            except KeyError:
                issues.append(f"Layout '{output.layout.layout_id}' does not exist in LayoutLibrary.")

        # Check camera compatibility
        if output.camera is None or output.layout is None:
            issues.append("Scene camera or layout is missing.")
        else:
            try:
                cam = self.camera_lib.get(output.camera.preset_id)
                if (
                    cam.compatible_layouts
                    and "*" not in cam.compatible_layouts
                    and output.layout.layout_id not in cam.compatible_layouts
                ):
                    issues.append(
                        f"Camera '{cam.preset_id}' is incompatible with layout '{output.layout.layout_id}'."
                    )
            except KeyError:
                issues.append(f"Camera '{output.camera.preset_id}' does not exist in CameraLibrary.")

        # Check motions valid
        if not output.motions or len(output.motions) == 0:
            issues.append("Motions list is empty.")
        else:
            for m in output.motions:
                try:
                    self.motion_lib.get(m.preset_id)
                except KeyError:
                    issues.append(f"Motion preset '{m.preset_id}' does not exist in MotionLibrary.")

        if issues:
            return ReviewResult(
                stage="scene_composition",
                verdict=ReviewVerdict.FAIL,
                score=0.0,
                issues=issues,
                suggestions=["Fix missing/incompatible layout, camera, or motions."],
            )

        return ReviewResult(
            stage="scene_composition",
            verdict=ReviewVerdict.PASS,
            score=1.0,
            issues=[],
            suggestions=[],
        )
