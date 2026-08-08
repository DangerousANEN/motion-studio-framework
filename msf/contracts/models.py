"""MSF Domain Models and Serialization Contracts.

Contains all dataclasses and enums representing the core domain model of the Motion Studio Framework.
All dataclasses support full JSON serialization and deserialization via to_dict() and from_dict().
"""

from __future__ import annotations

import dataclasses
import enum
import sys
import typing
from datetime import datetime, timezone
from typing import Any, Optional, Self, get_args, get_origin, get_type_hints


class StrEnum(str, enum.Enum):
    """String Enum base providing clean string representations."""

    def __str__(self) -> str:
        return self.value


class AssetType(StrEnum):
    """Types of assets supported by MSF."""
    IMAGE = "image"
    VECTOR = "vector"
    ICON = "icon"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT_BLOCK = "text_block"
    HTML = "html"
    CSS = "css"
    OTHER = "other"


class Emotion(StrEnum):
    """Emotional tones for narration and scenes."""
    NEUTRAL = "neutral"
    EXCITED = "excited"
    SERIOUS = "serious"
    ENERGETIC = "energetic"
    CALM = "calm"
    DRAMATIC = "dramatic"
    CURIOSITY = "curiosity"
    URGENT = "urgent"
    INSPIRATIONAL = "inspirational"


class ReviewVerdict(StrEnum):
    """QC review verdict."""
    PASS = "pass"
    FAIL = "fail"


class ProjectStatus(StrEnum):
    """Pipeline progression status of an MSF project."""
    CREATED = "created"
    BRIEFED = "briefed"
    RESEARCHED = "researched"
    SCRIPTED = "scripted"
    STORYBOARDED = "storyboarded"
    COMPOSING = "composing"
    RENDERING = "rendering"
    AUDIO_MASTERING = "audio_mastering"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnimationType(StrEnum):
    """Motion graphic animation types."""
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_IN = "slide_in"
    SLIDE_OUT = "slide_out"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    BOUNCE = "bounce"
    PULSE = "pulse"
    ROTATE = "rotate"
    TYPEWRITER = "typewriter"
    STAGGER = "stagger"
    SCALE_UP = "scale_up"


class MovementType(StrEnum):
    """Camera preset movement patterns."""
    NONE = "none"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    PAN_UP = "pan_up"
    PAN_DOWN = "pan_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    ORBIT = "orbit"
    PARALLAX = "parallax"
    SHAKE = "shake"
    CRANE_UP = "crane_up"
    CRANE_DOWN = "crane_down"
    WHIP_PAN = "whip_pan"
    DOLLY_ZOOM = "dolly_zoom"

def _serialize_value(val: Any) -> Any:
    """Recursively serialize enums, dataclasses, lists, tuples, and dicts to primitive JSON values."""
    if val is None:
        return None
    if isinstance(val, enum.Enum):
        return val.value
    if hasattr(val, "to_dict") and callable(val.to_dict):
        return val.to_dict()
    if isinstance(val, (list, tuple, set)):
        return [_serialize_value(item) for item in val]
    if isinstance(val, dict):
        return {str(k): _serialize_value(v) for k, v in val.items()}
    return val


def _deserialize_value(tp: Any, val: Any, global_ns: dict | None = None) -> Any:
    """Recursively deserialize JSON primitive values into strongly typed domain objects."""
    if val is None:
        return None

    if isinstance(tp, str):
        ns = dict(global_ns or {})
        ns.update(typing.__dict__)
        if tp in ns:
            tp = ns[tp]
        else:
            try:
                tp = eval(tp, ns)
            except Exception:
                pass

    while True:
        origin = get_origin(tp)
        args = get_args(tp)
        if origin is typing.Union:
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                tp = non_none[0]
            else:
                break
        else:
            break

    if isinstance(tp, type) and issubclass(tp, enum.Enum):
        if isinstance(val, tp):
            return val
        try:
            return tp(val)
        except ValueError:
            for m in tp:
                if m.name.lower() == str(val).lower() or m.value.lower() == str(val).lower():
                    return m
            return val

    if isinstance(tp, type) and hasattr(tp, "from_dict") and isinstance(val, dict):
        return tp.from_dict(val)

    if origin in (list, set):
        elem_tp = args[0] if args else Any
        return [_deserialize_value(elem_tp, item, global_ns) for item in val]

    if origin is tuple:
        if args and len(args) > 0 and args[-1] is not Ellipsis:
            return tuple(
                _deserialize_value(args[i] if i < len(args) else Any, item, global_ns)
                for i, item in enumerate(val)
            )
        elif args:
            return tuple(_deserialize_value(args[0], item, global_ns) for item in val)
        return tuple(val)

    if origin is dict:
        key_tp = args[0] if args else Any
        val_tp = args[1] if len(args) > 1 else Any
        return {
            _deserialize_value(key_tp, k, global_ns): _deserialize_value(val_tp, v, global_ns)
            for k, v in val.items()
        }

    return val


@dataclasses.dataclass
class BaseContract:
    """Base dataclass providing JSON dictionary serialization and deserialization."""

    def to_dict(self) -> dict[str, Any]:
        """Convert contract instance into a JSON-serializable dictionary."""
        return {
            f.name: _serialize_value(getattr(self, f.name)) for f in dataclasses.fields(self)
        }

    @classmethod
    def from_dict(cls: type[Self], data: dict[str, Any]) -> Self:
        """Construct a contract instance from a dictionary."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict for {cls.__name__}, got {type(data)}")

        mod = sys.modules.get(cls.__module__)
        global_ns = dict(getattr(mod, "__dict__", {}))
        global_ns.update(globals())
        global_ns.update(typing.__dict__)
        try:
            type_hints = get_type_hints(cls, global_ns)
        except Exception:
            type_hints = {}

        kwargs = {}
        for f in dataclasses.fields(cls):
            if f.name in data:
                raw_val = data[f.name]
                hint = type_hints.get(f.name, f.type)
                kwargs[f.name] = _deserialize_value(hint, raw_val, global_ns)
            else:
                if f.default is not dataclasses.MISSING:
                    kwargs[f.name] = f.default
                elif f.default_factory is not dataclasses.MISSING:
                    kwargs[f.name] = f.default_factory()

        return cls(**kwargs)


@dataclasses.dataclass
class ProjectBrief(BaseContract):
    """Initial input specification for an MSF video production project."""
    topic: str
    style: str = "modern_tech"
    duration_range: tuple[int, int] = (30, 90)
    language: str = "ru"
    output_format: str = "9:16"


@dataclasses.dataclass
class ResearchResult(BaseContract):
    """Synthesized research output gathered for the project topic."""
    facts: list[str] = dataclasses.field(default_factory=list)
    sources: list[str] = dataclasses.field(default_factory=list)
    key_points: list[str] = dataclasses.field(default_factory=list)
    statistics: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Script(BaseContract):
    """Narrative script structured into video scenes."""
    title: str = ""
    hook: str = ""
    scenes_text: list[str] = dataclasses.field(default_factory=list)
    cta: str = ""
    total_duration: float = 0.0
    language: str = "ru"


@dataclasses.dataclass
class SceneSpec(BaseContract):
    """Specification of an individual scene within a storyboard."""
    scene_id: str
    title: str = ""
    narration_text: str = ""
    duration: float = 5.0
    emotion: Emotion = Emotion.NEUTRAL
    information_load: str = "medium"
    visual_goal: str = ""


@dataclasses.dataclass
class Storyboard(BaseContract):
    """Overall sequence of SceneSpecs composing a project."""
    project_id: str
    scenes: list[SceneSpec] = dataclasses.field(default_factory=list)
    total_duration: float = 0.0
    narrative_arc: str = ""


@dataclasses.dataclass
class LayoutChoice(BaseContract):
    """Selected composition layout template for a scene."""
    layout_id: str
    name: str = ""
    grid_areas: dict[str, Any] = dataclasses.field(default_factory=dict)
    safe_zones: dict[str, Any] = dataclasses.field(default_factory=dict)
    max_text_blocks: int = 3


@dataclasses.dataclass
class CameraPreset(BaseContract):
    """Camera movement configuration for scene rendering."""
    preset_id: str
    movement_type: MovementType = MovementType.NONE
    css_transform: str = ""
    duration: float = 5.0
    easing: str = "ease-in-out"
    speed: float = 1.0
    compatible_layouts: list[str] = dataclasses.field(default_factory=list)

@dataclasses.dataclass
class MotionPreset(BaseContract):
    """Motion graphic animation rule for visual elements."""
    preset_id: str
    name: str = ""
    animation_type: AnimationType = AnimationType.FADE_IN
    params: dict[str, Any] = dataclasses.field(default_factory=dict)
    duration: float = 1.0
    easing: str = "ease-out"


@dataclasses.dataclass
class TypographySpec(BaseContract):
    """Font and text formatting design rules."""
    font_family: str = "Inter"
    sizes: dict[str, int] = dataclasses.field(default_factory=dict)
    line_heights: dict[str, float] = dataclasses.field(default_factory=dict)
    contrast_ratio: float = 4.5
    safe_margins: dict[str, int] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class AssetRequest(BaseContract):
    """Specification for generating or fetching a visual asset."""
    asset_id: str
    asset_type: AssetType = AssetType.IMAGE
    description: str = ""
    style_constraints: dict[str, Any] = dataclasses.field(default_factory=dict)
    dimensions: tuple[int, int] = (1080, 1920)


@dataclasses.dataclass
class AssetResult(BaseContract):
    """Result artifact of a generated or resolved asset."""
    asset_id: str
    file_path: str = ""
    format: str = "png"
    dimensions: tuple[int, int] = (1080, 1920)
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class VoiceSpec(BaseContract):
    """Synthesis specification for Text-to-Speech generation."""
    text: str
    speaker: str = "kseniya"
    emotion: Emotion = Emotion.NEUTRAL
    speed: float = 1.0
    sample_rate: int = 24000
    output_path: str = ""


@dataclasses.dataclass
class WordTimestamp(BaseContract):
    """Word-level audio timestamp for exact subtitle alignment."""
    word: str
    start: float
    end: float


@dataclasses.dataclass
class VoiceResult(BaseContract):
    """Generated audio artifact with precise word timestamps."""
    audio_path: str = ""
    duration_seconds: float = 0.0
    sample_rate: int = 24000
    word_timestamps: list[WordTimestamp] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class SubtitleEntry(BaseContract):
    """Visual subtitle entry for rendering styled text overlays."""
    word: str
    start: float
    end: float
    style: dict[str, Any] = dataclasses.field(default_factory=dict)
    position: dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class SceneComposition(BaseContract):
    """Complete assembled representation of a single video scene."""
    scene_id: str
    layout: Optional[LayoutChoice] = None
    camera: Optional[CameraPreset] = None
    motions: list[MotionPreset] = dataclasses.field(default_factory=list)
    assets: list[AssetResult] = dataclasses.field(default_factory=list)
    voice: Optional[VoiceResult] = None
    subtitles: list[SubtitleEntry] = dataclasses.field(default_factory=list)
    background_color: str = "#000000"
    duration: float = 5.0


@dataclasses.dataclass
class ReviewResult(BaseContract):
    """Quality control evaluation result for a production stage."""
    stage: str
    verdict: ReviewVerdict = ReviewVerdict.PASS
    score: float = 1.0
    issues: list[str] = dataclasses.field(default_factory=list)
    suggestions: list[str] = dataclasses.field(default_factory=list)
    attempt: int = 1
    max_attempts: int = 3


@dataclasses.dataclass
class ProjectState(BaseContract):
    """Persistent state tracking the entire lifecycle of an MSF project."""
    project_id: str
    created_at: str = dataclasses.field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    status: ProjectStatus = ProjectStatus.CREATED
    brief: Optional[ProjectBrief] = None
    research: Optional[ResearchResult] = None
    script: Optional[Script] = None
    storyboard: Optional[Storyboard] = None
    scenes: dict[str, SceneComposition] = dataclasses.field(default_factory=dict)
    reviews: list[ReviewResult] = dataclasses.field(default_factory=list)
    output_path: Optional[str] = None
