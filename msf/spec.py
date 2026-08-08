import math
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

FPS = 60
WIDTH = 1080
HEIGHT = 1920
TAIL_PAD_FRAMES = 12


def frames_for(duration_sec: float, fps: int = FPS) -> int:
    """Compute frame count from audio duration in seconds with ceil and tail padding."""
    return math.ceil(duration_sec * fps) + TAIL_PAD_FRAMES


@dataclass
class Scene:
    id: str
    duration_in_frames: int
    preset: str = "HeroKinetic"
    title: Optional[str] = None
    subtitle: Optional[str] = None
    text: Optional[str] = None
    body_text: Optional[str] = None
    accent_color: Optional[str] = None
    badge: Optional[str] = None
    stat_value: Optional[float] = None
    stat_prefix: Optional[str] = None
    stat_suffix: Optional[str] = None
    stat_label: Optional[str] = None
    cards: Optional[List[Dict[str, Any]]] = None
    audio_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize scene to camelCase dictionary expected by VideoSpec.schema.ts."""
        res: Dict[str, Any] = {
            "id": self.id,
            "durationInFrames": self.duration_in_frames,
            "preset": self.preset,
        }
        if self.title is not None:
            res["title"] = self.title
        if self.subtitle is not None:
            res["subtitle"] = self.subtitle
        if self.text is not None:
            res["text"] = self.text
        if self.body_text is not None:
            res["bodyText"] = self.body_text
        if self.accent_color is not None:
            res["accentColor"] = self.accent_color
        if self.badge is not None:
            res["badge"] = self.badge
        if self.stat_value is not None:
            res["statValue"] = self.stat_value
        if self.stat_prefix is not None:
            res["statPrefix"] = self.stat_prefix
        if self.stat_suffix is not None:
            res["statSuffix"] = self.stat_suffix
        if self.stat_label is not None:
            res["statLabel"] = self.stat_label
        if self.cards is not None:
            res["cards"] = self.cards
        if self.audio_url is not None:
            res["audioUrl"] = self.audio_url
        return res


def validate_spec(spec: Dict[str, Any]) -> None:
    """Fail-fast validation of a spec dict before it is handed to Remotion.

    The Zod schema in VideoSpec.schema.ts is the second line of defence (it renders
    a loud red ERROR scene). This is the first: a broken spec must raise in Python
    BEFORE we burn minutes on a render that can only produce garbage.

    Raises:
        ValueError: if the spec cannot produce a meaningful video.
    """
    if not isinstance(spec, dict):
        raise ValueError(f"Spec must be a dict, got {type(spec).__name__}.")

    scenes = spec.get("scenes")
    if not isinstance(scenes, list) or len(scenes) == 0:
        raise ValueError(
            "Spec validation failed: 'scenes' must be a non-empty list. "
            "Refusing to render — an empty spec can only produce a placeholder video."
        )

    for key, expected in (("fps", int), ("width", int), ("height", int)):
        val = spec.get(key)
        if not isinstance(val, expected) or val <= 0:
            raise ValueError(f"Spec validation failed: '{key}' must be a positive int, got {val!r}.")

    for i, sc in enumerate(scenes):
        if not isinstance(sc, dict):
            raise ValueError(f"Spec validation failed: scene[{i}] must be a dict, got {type(sc).__name__}.")

        frames = sc.get("durationInFrames")
        if not isinstance(frames, int) or frames <= 0:
            raise ValueError(
                f"Spec validation failed: scene[{i}] 'durationInFrames' must be a positive int, got {frames!r}. "
                "(Check for snake_case leakage — the wire format is camelCase.)"
            )

        # A scene with no renderable content would produce an empty frame.
        has_content = any(
            sc.get(k) for k in ("title", "subtitle", "text", "bodyText", "statLabel", "cards")
        )
        if sc.get("statValue") is not None:
            has_content = True
        if not has_content:
            raise ValueError(
                f"Spec validation failed: scene[{i}] (id={sc.get('id')!r}, preset={sc.get('preset')!r}) "
                "has no renderable content — every scene needs at least one of "
                "title/subtitle/text/bodyText/statValue/statLabel/cards."
            )

    return None


def build_spec(
    scenes: List[Scene],
    fps: int = FPS,
    width: int = WIDTH,
    height: int = HEIGHT,
    audio_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Build single source of truth VideoSpec dictionary for Remotion."""
    scene_dicts = [s.to_dict() if isinstance(s, Scene) else s for s in scenes]
    total_frames = sum(s["durationInFrames"] for s in scene_dicts)

    spec: Dict[str, Any] = {
        "width": width,
        "height": height,
        "fps": fps,
        "durationInFrames": total_frames,
        "brandColors": {
            "bg": "#0E0F11",
            "surface": "#16181C",
            "gold": "#E6C475",
            "neon": "#00FF88",
            "cyan": "#00D4FF",
            "text": "#FFFFFF",
            "muted": "#8B92A0",
        },
        "scenes": scene_dicts,
    }
    if audio_url:
        spec["audioUrl"] = audio_url

    return spec
