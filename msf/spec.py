"""Video spec: the single source of truth shared by Python and Remotion.

Wire format is camelCase (TypeScript side); Python attributes are snake_case and
converted in `to_dict()`. Keep this file and remotion/src/VideoSpec.schema.ts in
sync — a field added here is invisible to the renderer until the Zod schema
knows about it too.
"""
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

FPS = 60

# ---------------------------------------------------------------- formats

@dataclass(frozen=True)
class VideoFormat:
    """A named output geometry.

    `safe_margin_px` is the padding presets should keep clear of the edges so
    platform UI (captions, action buttons, progress bars) never covers content.
    """

    name: str
    width: int
    height: int
    safe_margin_px: int
    description: str

    @property
    def aspect(self) -> float:
        return self.width / self.height

    @property
    def is_vertical(self) -> bool:
        return self.height > self.width

    @property
    def is_square(self) -> bool:
        return self.width == self.height


FORMATS: Dict[str, VideoFormat] = {
    "vertical": VideoFormat("vertical", 1080, 1920, 120,
                            "Shorts / Reels / TikTok / Telegram 9:16"),
    "horizontal": VideoFormat("horizontal", 1920, 1080, 90,
                              "YouTube / landing hero 16:9"),
    "square": VideoFormat("square", 1080, 1080, 90,
                          "Feed posts 1:1"),
    "classic": VideoFormat("classic", 1440, 1080, 90,
                           "4:3 archival / slide style"),
    "cinema": VideoFormat("cinema", 1920, 816, 80,
                          "2.35:1 letterbox, title sequences"),
}

DEFAULT_FORMAT = "vertical"

# Kept for backwards compatibility with older callers that imported these.
WIDTH = FORMATS[DEFAULT_FORMAT].width
HEIGHT = FORMATS[DEFAULT_FORMAT].height

TAIL_PAD_FRAMES = 12


def resolve_format(fmt: Optional[Any]) -> VideoFormat:
    """Accept a format name, a VideoFormat, or an explicit (width, height)."""
    if fmt is None:
        return FORMATS[DEFAULT_FORMAT]
    if isinstance(fmt, VideoFormat):
        return fmt
    if isinstance(fmt, str):
        key = fmt.strip().lower()
        if key not in FORMATS:
            raise ValueError(
                f"Unknown format {fmt!r}. Available: {sorted(FORMATS)}. "
                "Or pass an explicit (width, height) tuple."
            )
        return FORMATS[key]
    if isinstance(fmt, (tuple, list)) and len(fmt) == 2:
        w, h = int(fmt[0]), int(fmt[1])
        if w <= 0 or h <= 0:
            raise ValueError(f"Custom format needs positive dimensions, got {fmt!r}.")
        margin = round(min(w, h) * 0.09)
        return VideoFormat("custom", w, h, margin, f"custom {w}x{h}")
    raise TypeError(f"Cannot interpret format {fmt!r}.")


def frames_for(duration_sec: float, fps: int = FPS) -> int:
    """Frame count for an audio clip, with a little tail padding."""
    return math.ceil(duration_sec * fps) + TAIL_PAD_FRAMES


# ---------------------------------------------------------------- scene

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
    # StatCounter
    stat_value: Optional[float] = None
    stat_prefix: Optional[str] = None
    stat_suffix: Optional[str] = None
    stat_label: Optional[str] = None
    # SwipePanels / comparisons
    cards: Optional[List[Dict[str, Any]]] = None
    # 3D presets
    model_url: Optional[str] = None
    model_scale: Optional[float] = None
    orbit_speed: Optional[float] = None
    # Diagrams / flows
    nodes: Optional[List[Dict[str, Any]]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    # Code / terminal
    code: Optional[str] = None
    language: Optional[str] = None
    # QuoteCard
    author: Optional[str] = None
    role: Optional[str] = None
    # TokenCloud3D / LayerStack3D
    point_count: Optional[int] = None
    layers: Optional[List[str]] = None
    # Style
    style: Optional[str] = None
    audio_url: Optional[str] = None

    _CAMEL = {
        "duration_in_frames": "durationInFrames",
        "body_text": "bodyText",
        "accent_color": "accentColor",
        "stat_value": "statValue",
        "stat_prefix": "statPrefix",
        "stat_suffix": "statSuffix",
        "stat_label": "statLabel",
        "model_url": "modelUrl",
        "model_scale": "modelScale",
        "orbit_speed": "orbitSpeed",
        "point_count": "pointCount",
        "audio_url": "audioUrl",
    }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to the camelCase shape VideoSpec.schema.ts expects."""
        res: Dict[str, Any] = {
            "id": self.id,
            "durationInFrames": self.duration_in_frames,
            "preset": self.preset,
        }
        for field_name, value in self.__dict__.items():
            if field_name in ("id", "duration_in_frames", "preset") or value is None:
                continue
            res[self._CAMEL.get(field_name, field_name)] = value
        return res


# ---------------------------------------------------------------- validation

# Presets that cannot render from plain narration text alone.
_DATA_REQUIREMENTS = {
    "StatCounter": ("statValue", "statLabel"),
    "SwipePanels": ("cards",),
    "CompareSplit": ("cards",),
    "FlowDiagram": ("nodes", "steps"),
    "CodeReveal": ("code",),
    "ModelShowcase": ("modelUrl",),
}


def validate_spec(spec: Dict[str, Any]) -> None:
    """Fail fast on a spec that cannot produce a meaningful video.

    The Zod schema on the TypeScript side is the second line of defence. This is
    the first: raise in Python BEFORE burning minutes on a doomed render.
    """
    if not isinstance(spec, dict):
        raise ValueError(f"Spec must be a dict, got {type(spec).__name__}.")

    scenes = spec.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError(
            "Spec validation failed: 'scenes' must be a non-empty list. "
            "Refusing to render — an empty spec can only produce a placeholder video."
        )

    for key in ("fps", "width", "height"):
        val = spec.get(key)
        if not isinstance(val, int) or val <= 0:
            raise ValueError(
                f"Spec validation failed: '{key}' must be a positive int, got {val!r}."
            )

    for i, sc in enumerate(scenes):
        if not isinstance(sc, dict):
            raise ValueError(
                f"Spec validation failed: scene[{i}] must be a dict, got {type(sc).__name__}."
            )

        frames = sc.get("durationInFrames")
        if not isinstance(frames, int) or frames <= 0:
            raise ValueError(
                f"Spec validation failed: scene[{i}] 'durationInFrames' must be a positive int, "
                f"got {frames!r}. (Check for snake_case leakage — the wire format is camelCase.)"
            )

        content_keys = (
            "title", "subtitle", "text", "bodyText", "statLabel",
            "cards", "nodes", "steps", "code", "modelUrl",
        )
        has_content = any(sc.get(k) for k in content_keys) or sc.get("statValue") is not None
        if not has_content:
            raise ValueError(
                f"Spec validation failed: scene[{i}] (id={sc.get('id')!r}, "
                f"preset={sc.get('preset')!r}) has no renderable content."
            )

        # Data-driven presets would silently render their ⚠ placeholder otherwise.
        preset = sc.get("preset")
        required = _DATA_REQUIREMENTS.get(preset)
        if required and not any(sc.get(k) is not None for k in required):
            raise ValueError(
                f"Spec validation failed: scene[{i}] (id={sc.get('id')!r}) uses preset "
                f"{preset!r} which needs one of {list(required)}, but none were supplied. "
                "That would render a placeholder instead of real content."
            )


# ---------------------------------------------------------------- builder

def build_spec(
    scenes: List[Scene],
    fps: int = FPS,
    width: Optional[int] = None,
    height: Optional[int] = None,
    video_format: Optional[Any] = None,
    audio_url: Optional[str] = None,
    theme: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the VideoSpec dict handed to Remotion.

    Geometry comes from `video_format` (name/tuple/VideoFormat); explicit
    width/height still win so existing callers keep working.
    """
    fmt = resolve_format(video_format) if video_format is not None else FORMATS[DEFAULT_FORMAT]
    out_w = width if width is not None else fmt.width
    out_h = height if height is not None else fmt.height

    scene_dicts = [s.to_dict() if isinstance(s, Scene) else s for s in scenes]
    total_frames = sum(s["durationInFrames"] for s in scene_dicts)

    spec: Dict[str, Any] = {
        "width": out_w,
        "height": out_h,
        "fps": fps,
        "durationInFrames": total_frames,
        "format": fmt.name,
        "safeMargin": fmt.safe_margin_px,
        "theme": theme or "pop",
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
