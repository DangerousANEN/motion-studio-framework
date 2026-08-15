"""Video spec: the single source of truth shared by Python and Remotion.

Wire format is camelCase (TypeScript side); Python attributes are snake_case and
converted in `to_dict()`. Keep this file and remotion/src/VideoSpec.schema.ts in
sync — a field added here is invisible to the renderer until the Zod schema
knows about it too.
"""
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

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

# Mirrors THEMES in remotion/src/presets/brand.ts. tests/test_theme_parity.py
# asserts the two stay in sync, so adding a theme on one side fails loudly
# instead of only blowing up at render time.
THEMES: Tuple[str, ...] = ("pop", "noir", "glass", "blueprint", "sunset")
DEFAULT_THEME = "pop"

# Kept for backwards compatibility with older callers that imported these.
WIDTH = FORMATS[DEFAULT_FORMAT].width
HEIGHT = FORMATS[DEFAULT_FORMAT].height

TAIL_PAD_FRAMES = 12

# Reading speed for the on-screen dwell check in validate_spec. MUST match
# READ_CHARS_PER_SEC in remotion/src/lib/pacing.ts and CHARS_PER_SEC in
# tools/timing_probe.py — three places grade the same contract, and if they
# disagree the warning fires on scenes the presets consider fine.
READ_CHARS_PER_SEC = 12.0


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
    # Studio v2 BeforeAfter: two labelled textual states.
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    # Studio v2 MetricTrend: 2–6 labelled numeric values.
    points: Optional[List[Dict[str, Any]]] = None
    metric_label: Optional[str] = None
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
    # DonutFill — ring/pie charts. `segments` is [{"label": str, "value": float}].
    # Shares are computed from the sum, so values need not total 100.
    segments: Optional[List[Dict[str, Any]]] = None
    shape: Optional[str] = None
    thickness: Optional[float] = None
    fill_mode: Optional[str] = None
    center_content: Optional[str] = None
    label_placement: Optional[str] = None
    percent_counters: Optional[bool] = None
    gap_angle: Optional[float] = None
    highlight_segment: Optional[int] = None
    value_suffix: Optional[str] = None
    # TgChat / AiChatStream — `messages` is [{"from"?, "text", "out"?, "read"?}].
    # `response` is the streamed assistant reply (AiChatStream only).
    messages: Optional[List[Dict[str, Any]]] = None
    response: Optional[str] = None
    chat_title: Optional[str] = None
    # TgChat fidelity controls: typed composer, client identity and safe theme.
    contact_name: Optional[str] = None
    contact_status: Optional[str] = None
    compose: Optional[str] = None
    typing: Optional[bool] = None
    show_cursor: Optional[bool] = None
    show_input_bar: Optional[bool] = None
    send_at_progress: Optional[float] = None
    tg_theme: Optional[str] = None
    date_pill: Optional[str] = None
    is_group: Optional[bool] = None
    # CryptoWallet — `tokens` is [{"symbol", "amount", "change"}].
    # amount/change/balance are NUMBERS on the wire (Zod rejects "2.4" and
    # "+3.1%"); formatting and the % sign are the preset's job, not the spec's.
    balance: Optional[float] = None
    tokens: Optional[List[Dict[str, Any]]] = None
    address: Optional[str] = None
    currency: Optional[str] = None
    # BankCard — never accept full card numbers; last 4 digits only.
    last4: Optional[str] = None
    holder: Optional[str] = None
    expiry: Optional[str] = None
    card_brand: Optional[str] = None
    # ---------------------------------------------------------------- media
    # ImageShowcase / VideoEmbed / ScreenRecord. `src` is a URL or a path
    # relative to remotion/public/.
    src: Optional[str] = None
    images: Optional[List[str]] = None
    fit: Optional[str] = None
    ken_burns: Optional[bool] = None
    start_from: Optional[int] = None
    show_controls: Optional[bool] = None
    muted: Optional[bool] = None
    chrome: Optional[str] = None
    url_bar: Optional[str] = None
    app_name: Optional[str] = None
    show_rec: Optional[bool] = None
    # ScreenGuide: normalized focus anchor, optional pan and click path.
    focus_x: Optional[float] = None
    focus_y: Optional[float] = None
    focus_scale: Optional[float] = None
    pan_x: Optional[float] = None
    pan_y: Optional[float] = None
    cursor_steps: Optional[List[Dict[str, Any]]] = None
    guide_text: Optional[str] = None
    # VoiceMemo / TelegramVoiceRound
    avatar: Optional[str] = None
    duration: Optional[float] = None
    waveform_seed: Optional[int] = None
    transcript: Optional[str] = None
    # --------------------------------------------------------------- device
    # PhoneMockup renders ANOTHER preset on its screen. `inner_props` carries
    # that preset's own fields, in wire (camelCase) form.
    inner_preset: Optional[str] = None
    inner_props: Optional[Dict[str, Any]] = None
    device: Optional[str] = None
    tilt: Optional[float] = None
    # ---------------------------------------------------------------- audio
    track_title: Optional[str] = None
    artist: Optional[str] = None
    cover: Optional[str] = None
    rpm: Optional[float] = None
    spin: Optional[bool] = None
    # --------------------------------------------------------------- charts
    ring_max: Optional[float] = None
    bar_depth: Optional[float] = None
    # --------------------------------------------------------------- social
    # PostCard / CommentWall / SubscribeCTA / Leaderboard.
    author: Optional[str] = None
    handle: Optional[str] = None
    verified: Optional[bool] = None
    likes: Optional[int] = None
    reposts: Optional[int] = None
    # A number for PostCard's counter, a list for CommentWall's data.
    comments: Optional[Any] = None
    channel_name: Optional[str] = None
    subscribers: Optional[int] = None
    button_text: Optional[str] = None
    subscribed_text: Optional[str] = None
    rows: Optional[List[Dict[str, Any]]] = None
    # ---------------------------------------------------------------- learn
    question: Optional[str] = None
    # QuizCard accepts strings; PollResult also accepts typed {label, value} rows.
    options: Optional[List[Any]] = None
    correct_index: Optional[int] = None
    reveal_at_progress: Optional[float] = None
    current_step: Optional[int] = None
    orientation: Optional[str] = None
    term: Optional[str] = None
    definition: Optional[str] = None
    example: Optional[str] = None
    source: Optional[str] = None
    events: Optional[List[Dict[str, Any]]] = None
    # ---------------------------------------------------------------- stage
    # LyricLines karaoke lines; ScoreHud game state; CountdownHero; VersusSplit.
    lines: Optional[List[Any]] = None
    score: Optional[int] = None
    health: Optional[float] = None
    combo: Optional[int] = None
    time_left: Optional[float] = None
    player_name: Optional[str] = None
    # `from` is a Python keyword, so the attribute is count_from and _CAMEL
    # emits it as `from` on the wire.
    count_from: Optional[int] = None
    final_word: Optional[str] = None
    left: Optional[Dict[str, Any]] = None
    right: Optional[Dict[str, Any]] = None
    vs_label: Optional[str] = None
    # ------------------------------------------------------- v2.3 expansion
    headline: Optional[str] = None
    subhead: Optional[str] = None
    proof: Optional[str] = None
    urgency: Optional[str] = None
    phrase: Optional[str] = None
    highlight: Optional[str] = None
    caption: Optional[str] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    feature: Optional[str] = None
    benefit: Optional[str] = None
    index: Optional[str] = None
    context: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None
    myth: Optional[str] = None
    fact: Optional[str] = None
    quote: Optional[str] = None
    footnote: Optional[str] = None
    status: Optional[str] = None
    value: Optional[Any] = None
    progress: Optional[float] = None
    stats: Optional[List[Dict[str, Any]]] = None
    sources: Optional[List[Dict[str, Any]]] = None
    prompt: Optional[str] = None
    provider: Optional[str] = None
    send_label: Optional[str] = None
    avatar_text: Optional[str] = None
    answer: Optional[str] = None
    chips: Optional[List[str]] = None
    notifications: Optional[List[Dict[str, Any]]] = None
    platform_label: Optional[str] = None
    screenshot_url: Optional[str] = None
    media_url: Optional[str] = None
    focus: Optional[str] = None
    zoom: Optional[float] = None
    speaker: Optional[str] = None
    channel: Optional[str] = None
    chapter: Optional[str] = None
    # ---------------------------------------------------------- v2.4 scene 50
    benchmark: Optional[str] = None
    models: Optional[List[Dict[str, Any]]] = None
    rank_before: Optional[List[Dict[str, Any]]] = None
    rank_after: Optional[List[Dict[str, Any]]] = None
    scatter_points: Optional[List[Dict[str, Any]]] = None
    axes: Optional[List[str]] = None
    series: Optional[List[Dict[str, Any]]] = None
    items: Optional[List[Dict[str, Any]]] = None
    line_items: Optional[List[Dict[str, Any]]] = None
    flow_nodes: Optional[List[Dict[str, Any]]] = None
    decision_nodes: Optional[List[Dict[str, Any]]] = None
    workflow_nodes: Optional[List[Dict[str, Any]]] = None
    links: Optional[List[Dict[str, Any]]] = None
    evidence: Optional[List[Dict[str, Any]]] = None
    caveat: Optional[str] = None
    source_a: Optional[Dict[str, Any]] = None
    source_b: Optional[Dict[str, Any]] = None
    difference: Optional[str] = None
    threshold: Optional[str] = None
    previous: Optional[str] = None
    current: Optional[str] = None
    deltas: Optional[List[Dict[str, Any]]] = None
    as_of: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    unit: Optional[str] = None
    method: Optional[str] = None
    # Telegram, community and agent workflow
    post_text: Optional[str] = None
    reactions: Optional[List[Dict[str, Any]]] = None
    views: Optional[int] = None
    time: Optional[str] = None
    cta: Optional[str] = None
    posts: Optional[List[Dict[str, Any]]] = None
    focus_post_id: Optional[Any] = None
    scroll_direction: Optional[str] = None
    origin: Optional[Dict[str, Any]] = None
    forwards: Optional[List[Dict[str, Any]]] = None
    original: Optional[Dict[str, Any]] = None
    commentary: Optional[str] = None
    questions: Optional[List[str]] = None
    answers: Optional[List[str]] = None
    changes: Optional[List[Dict[str, Any]]] = None
    prompt_a: Optional[str] = None
    prompt_b: Optional[str] = None
    result_a: Optional[str] = None
    result_b: Optional[str] = None
    rubric: Optional[List[str]] = None
    artifacts: Optional[List[str]] = None
    selected_cell: Optional[Dict[str, Any]] = None
    period: Optional[str] = None
    product: Optional[str] = None
    version: Optional[str] = None
    columns: Optional[List[str]] = None
    # Media choreography
    positions: Optional[List[Dict[str, Any]]] = None
    camera_path: Optional[List[float]] = None
    captions: Optional[List[str]] = None
    layout_seed: Optional[int] = None
    focus_order: Optional[List[int]] = None
    image: Optional[str] = None
    stops: Optional[List[Dict[str, Any]]] = None
    before_url: Optional[str] = None
    after_url: Optional[str] = None
    label_before: Optional[str] = None
    label_after: Optional[str] = None
    video_url: Optional[str] = None
    chapters: Optional[List[Dict[str, Any]]] = None
    document_url: Optional[str] = None
    notes: Optional[List[Dict[str, Any]]] = None
    screens: Optional[List[str]] = None
    windows: Optional[List[Dict[str, Any]]] = None
    left_image: Optional[str] = None
    right_image: Optional[str] = None
    left_meta: Optional[str] = None
    right_meta: Optional[str] = None
    # Universal 3D
    asset_url: Optional[str] = None
    asset_license: Optional[str] = None
    asset_attribution: Optional[str] = None
    camera_preset: Optional[str] = None
    material_mode: Optional[str] = None
    fallback_shape: Optional[str] = None
    parts: Optional[List[Dict[str, Any]]] = None
    explode_distance: Optional[float] = None
    svg_url: Optional[str] = None
    devices: Optional[List[str]] = None
    groups: Optional[List[Dict[str, Any]]] = None
    zones: Optional[List[Dict[str, Any]]] = None
    active_path: Optional[List[str]] = None
    locations: Optional[List[Dict[str, Any]]] = None
    routes: Optional[List[Dict[str, Any]]] = None
    milestones: Optional[List[Dict[str, Any]]] = None
    values: Optional[List[float]] = None
    focus_group: Optional[str] = None
    tagline: Optional[str] = None
    # Narrative, conversion and utility
    claim_a: Optional[str] = None
    claim_b: Optional[str] = None
    real_question: Optional[str] = None
    proof_label: Optional[str] = None
    choice_a: Optional[str] = None
    choice_b: Optional[str] = None
    outcomes_a: Optional[List[str]] = None
    outcomes_b: Optional[List[str]] = None
    past: Optional[str] = None
    present: Optional[str] = None
    next: Optional[str] = None
    chosen_path: Optional[List[str]] = None
    dimensions: Optional[List[Dict[str, Any]]] = None
    takeaway: Optional[str] = None
    window: Optional[str] = None
    timezone: Optional[str] = None
    what_changes: Optional[str] = None
    brand_name: Optional[str] = None
    logo_url: Optional[str] = None
    media: Optional[List[Dict[str, Any]]] = None
    date: Optional[str] = None
    # -------------------------------------------------------------- overlays
    # HUD elements above the scene: [{"type": "timer"|"notification"|"money", ...}].
    # See remotion/src/compositions/OverlayStack.tsx for per-type fields.
    overlays: Optional[List[Dict[str, Any]]] = None
    # Style family plus safe per-scene token overrides (wire: styleConfig).
    style: Optional[str] = None
    style_config: Optional[Dict[str, Any]] = None
    audio_url: Optional[str] = None
    # Transition played BEFORE this scene. Ignored on scene 0 (nothing to come
    # from). Dict on the wire: {"type", "durationInFrames", "direction", "timing"}.
    # NOTE: every transition SHORTENS the composition by its own duration, because
    # it overlaps the two neighbouring scenes. The renderer accounts for this in
    # lib/transitions.ts getTransitionPlan(); total_frames() below mirrors it so
    # the audio track length matches the video.
    transition: Optional[Dict[str, Any]] = None

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
        "fill_mode": "fillMode",
        "center_content": "centerContent",
        "label_placement": "labelPlacement",
        "percent_counters": "percentCounters",
        "gap_angle": "gapAngle",
        "highlight_segment": "highlightSegment",
        "value_suffix": "valueSuffix",
        "metric_label": "metricLabel",
        # TgChat renders `title` as the scene caption and `contactName` as the
        # chat partner. Keeping them separate stops a caption from silently
        # renaming the contact.
        "chat_title": "contactName",
        "contact_name": "contactName",
        "contact_status": "contactStatus",
        "show_cursor": "showCursor",
        "show_input_bar": "showInputBar",
        "send_at_progress": "sendAtProgress",
        "tg_theme": "tgTheme",
        "date_pill": "datePill",
        "is_group": "isGroup",
        # `brand` is taken on the wire by BankCard's scheme mark; the Python
        # attribute is card_brand so it cannot collide with a future top-level
        # brand field.
        "card_brand": "brand",
        "ken_burns": "kenBurns",
        "start_from": "startFrom",
        "show_controls": "showControls",
        "url_bar": "urlBar",
        "app_name": "appName",
        "show_rec": "showRec",
        "focus_x": "focusX",
        "focus_y": "focusY",
        "focus_scale": "focusScale",
        "pan_x": "panX",
        "pan_y": "panY",
        "cursor_steps": "cursorSteps",
        "guide_text": "guideText",
        "waveform_seed": "waveformSeed",
        "inner_preset": "innerPreset",
        "inner_props": "innerProps",
        "track_title": "trackTitle",
        "ring_max": "ringMax",
        "bar_depth": "barDepth",
        "channel_name": "channelName",
        "button_text": "buttonText",
        "subscribed_text": "subscribedText",
        "correct_index": "correctIndex",
        "reveal_at_progress": "revealAtProgress",
        "current_step": "currentStep",
        "time_left": "timeLeft",
        "player_name": "playerName",
        # `from` is reserved in Python; the dataclass field is count_from.
        "count_from": "from",
        "final_word": "finalWord",
        "vs_label": "vsLabel",
        "send_label": "sendLabel",
        "avatar_text": "avatarText",
        "platform_label": "platformLabel",
        "screenshot_url": "screenshotUrl",
        "media_url": "mediaUrl",
        "rank_before": "rankBefore",
        "rank_after": "rankAfter",
        "scatter_points": "scatterPoints",
        "line_items": "lineItems",
        "flow_nodes": "flowNodes",
        "decision_nodes": "decisionNodes",
        "workflow_nodes": "workflowNodes",
        "source_a": "sourceA",
        "source_b": "sourceB",
        "as_of": "asOf",
        "x_label": "xLabel",
        "y_label": "yLabel",
        "post_text": "postText",
        "focus_post_id": "focusPostId",
        "scroll_direction": "scrollDirection",
        "prompt_a": "promptA",
        "prompt_b": "promptB",
        "result_a": "resultA",
        "result_b": "resultB",
        "selected_cell": "selectedCell",
        "camera_path": "cameraPath",
        "layout_seed": "layoutSeed",
        "focus_order": "focusOrder",
        "before_url": "beforeUrl",
        "after_url": "afterUrl",
        "label_before": "labelBefore",
        "label_after": "labelAfter",
        "video_url": "videoUrl",
        "document_url": "documentUrl",
        "left_image": "leftImage",
        "right_image": "rightImage",
        "left_meta": "leftMeta",
        "right_meta": "rightMeta",
        "asset_url": "assetUrl",
        "asset_license": "assetLicense",
        "asset_attribution": "assetAttribution",
        "camera_preset": "cameraPreset",
        "material_mode": "materialMode",
        "fallback_shape": "fallbackShape",
        "explode_distance": "explodeDistance",
        "svg_url": "svgUrl",
        "active_path": "activePath",
        "focus_group": "focusGroup",
        "claim_a": "claimA",
        "claim_b": "claimB",
        "real_question": "realQuestion",
        "proof_label": "proofLabel",
        "choice_a": "choiceA",
        "choice_b": "choiceB",
        "outcomes_a": "outcomesA",
        "outcomes_b": "outcomesB",
        "chosen_path": "chosenPath",
        "what_changes": "whatChanges",
        "brand_name": "brandName",
        "logo_url": "logoUrl",
        "style_config": "styleConfig",
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


# ---------------------------------------------------------------- transitions

# Mirrors TRANSITION_NAMES in remotion/src/lib/transitions.ts and
# TransitionTypeSchema in VideoSpec.schema.ts. tests/test_transition_parity.py
# asserts all three stay in sync.
TRANSITIONS: Tuple[str, ...] = (
    "none", "fade", "slide", "wipe", "flip", "clockWipe", "iris",
    "pushCut", "ripple", "crosswarp", "crossZoom", "swap", "linearBlur",
    "zoomInOut", "dreamyZoom", "filmBurn", "zoomBlur", "bookFlip",
)

# 18 frames = 300ms at 60fps. Must match DEFAULT_TRANSITION_FRAMES in transitions.ts.
DEFAULT_TRANSITION_FRAMES = 18


def compute_total_frames(scene_dicts: List[Dict[str, Any]]) -> int:
    """Total composition length, with transition overlap subtracted.

    A transition overlaps the outgoing and incoming scene, so a TransitionSeries
    is SHORTER than the sum of its scene durations. MSF lays one continuous
    voice-over over the whole video: if this number is too large, the video ends
    on a frozen frame and every scene after the first transition drifts against
    the narration.

    This is a line-by-line mirror of getTransitionPlan() in
    remotion/src/lib/transitions.ts, including the clamp that keeps at least one
    frame of each neighbour visible. The two MUST agree — tests/test_transition_parity.py
    checks them against shared fixtures.
    """
    total = sum(int(s["durationInFrames"]) for s in scene_dicts)

    for i in range(1, len(scene_dicts)):
        cfg = scene_dicts[i].get("transition")
        if not isinstance(cfg, dict):
            continue
        if cfg.get("type", "fade") == "none":
            continue

        requested = cfg.get("durationInFrames") or DEFAULT_TRANSITION_FRAMES
        max_allowed = max(
            0,
            min(
                int(scene_dicts[i - 1]["durationInFrames"]),
                int(scene_dicts[i]["durationInFrames"]),
            ) - 1,
        )
        overlap = min(int(requested), max_allowed)
        if overlap > 0:
            total -= overlap

    return max(1, total)


# ---------------------------------------------------------------- validation

# Presets that cannot render from plain narration text alone.
_DATA_REQUIREMENTS = {
    "StatCounter": ("statValue", "statLabel"),
    "SwipePanels": ("cards",),
    "CompareSplit": ("cards",),
    "FlowDiagram": ("nodes", "steps"),
    "CodeReveal": ("code",),
    "ModelShowcase": ("modelUrl",),
    # A chart with no numbers, a chat with no messages and a wallet with no
    # tokens all render as empty chrome. Catch it here, not in the pixels.
    "DonutFill": ("segments",),
    "TgChat": ("messages",),
    "AiChatStream": ("response",),
    "CryptoWallet": ("tokens",),
    # Media presets host an external asset; without it they render a loud
    # placeholder, which is worse than failing here because it ships.
    # BankCard is deliberately NOT listed: it renders a plausible card from its
    # own defaults, so a spec using it as decoration is legitimate.
    "ImageShowcase": ("images", "src"),
    "VideoEmbed": ("src",),
    "ScreenRecord": ("src", "images"),
    "PhoneMockup": ("innerPreset",),
    "RingStats": ("segments",),
    "Bars3D": ("segments",),
    # social / learn / stage packs — each renders empty chrome without its data.
    "CommentWall": ("comments",),
    "Leaderboard": ("rows",),
    "QuizCard": ("question", "options"),
    "ProgressPath": ("steps",),
    "DefinitionCard": ("term", "definition"),
    "TimelineReveal": ("events",),
    "LyricLines": ("lines",),
    "VersusSplit": ("left", "right"),
    # v2.3 expansion — all of these require structured or scene-specific copy.
    "HookStack": ("headline", "title"),
    "KineticPhrase": ("phrase", "title", "text"),
    "ProblemSolution": ("problem", "solution"),
    "FeatureSpotlight": ("feature", "benefit"),
    "CaseStudyBoard": ("context", "action", "result"),
    "MythFact": ("myth", "fact"),
    "QuoteEvidence": ("quote", "text"),
    "StatsBand": ("stats",),
    "SourceStack": ("sources",),
    "CountdownRing": ("value", "title", "label"),
    "PromptComposer": ("prompt",),
    "ProviderChat": ("provider", "prompt", "answer"),
    "NotificationStack": ("notifications",),
    "CommentThread": ("comments",),
    "PollResult": ("options",),
    "BrowserTour": ("screenshotUrl", "src"),
    "ScreenMagnifier": ("mediaUrl", "src", "images"),
    "DeviceShowcase": ("mediaUrl", "src", "images"),
    "VoiceWave": ("speaker", "caption"),
    "VideoFrame": ("mediaUrl", "src", "images"),
}


# Required keys INSIDE each item of a list-valued field.
#
# _DATA_REQUIREMENTS above only asks "is the list there". A list that is present
# but whose rows are the wrong SHAPE is a different failure with a different blast
# radius, and the two classes below are NOT interchangeable — I checked each field
# against src/VideoSpec.schema.ts rather than assuming.
#
# HARD: the TS schema declares these item keys as REQUIRED (no `.optional()`), so a
# missing one fails Zod inside Root.tsx and degrades the ENTIRE video to a red
# ERROR card — not one placeholder scene, the whole render. Found with
# `tokens: [{name, symbol, value, change}]`: plausible, accepted by every Python
# check, and `value` is not `amount`, so all three rows failed `invalid_type`. A
# rendered red card is worse than an exception because it is a FILE: it uploads.
_ROW_SHAPES_HARD: Dict[str, tuple] = {
    "tokens": ("symbol", "amount"),        # TokenRowSchema
    "transactions": ("label", "amount"),   # TransactionSchema
    "segments": ("label", "value"),        # SegmentSchema
    # messages are checked separately: a regular bubble needs text, but a
    # bounded sticker-only item is now valid in the TypeScript contract.
}
_ALLOWED_CHAT_STICKERS = {"brain", "rocket", "spark", "thumbsUp"}

# SOFT: the TS schema declares these items with all-optional keys plus
# `.passthrough()`, so Zod accepts them and the render succeeds — it just draws a
# row with nothing in it. Raising the red-card warning here would be a lie; these
# get their own message about blank content.
_ROW_SHAPES_SOFT: Dict[str, tuple] = {
    "rows": ("name",),        # `label` is an accepted alias — see _ROW_ALIASES
    "comments": ("text",),
    "events": ("label",),     # `date` alone renders a dated row with no event
    "stats": ("label", "value"),
    "sources": ("title",),
    "notifications": ("text",),
    # PollResult permits string shorthand as well as {label, value} objects.
    "options": ("label",),
}

# Fields where an alias is legitimately accepted by the TS schema, so requiring
# the canonical key alone would reject a valid spec.
_ROW_ALIASES: Dict[str, Dict[str, tuple]] = {
    "rows": {"name": ("name", "label")},
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

        # Any one of these is enough to put something real on screen. Data-driven
        # presets carry their content in a list/number field rather than in text,
        # so they must be listed here or a fully-populated chart reads as "empty".
        content_keys = (
            "title", "subtitle", "text", "bodyText", "statLabel",
            "cards", "nodes", "steps", "code", "modelUrl",
            "statValue", "segments", "messages", "response", "tokens",
            "balance", "last4", "layers", "author",
            # Media/device/audio presets carry their content in an asset path or
            # a track name, not in text. Without these a fully-populated
            # ImageShowcase read as "no renderable content".
            "src", "images", "innerPreset", "trackTitle", "artist", "cover",
            "transcript", "overlays",
            # social / learn / stage
            "author", "handle", "rows", "channelName", "subscribers",
            "question", "options", "steps", "term", "definition", "events",
            "lines", "score", "health", "playerName", "from", "finalWord",
            "left", "right", "comments",
            # v2.3 expansion
            "headline", "subhead", "phrase", "highlight", "caption",
            "problem", "solution", "feature", "benefit", "context", "action",
            "result", "myth", "fact", "quote", "footnote", "stats", "sources",
            "value", "prompt", "provider", "answer", "notifications", "screenshotUrl",
            "mediaUrl", "speaker", "channel", "chapter",
            # v2.4 expansion semantic fields
            "models", "rankBefore", "rankAfter", "scatterPoints", "axes", "series", "items",
            "lineItems", "flowNodes", "decisionNodes", "workflowNodes", "links", "evidence",
            "sourceA", "sourceB", "deltas", "postText", "reactions", "posts", "origin",
            "forwards", "original", "questions", "answers", "changes", "promptA", "promptB",
            "resultA", "resultB", "artifacts", "columns", "positions", "captions", "image",
            "stops", "beforeUrl", "afterUrl", "videoUrl", "chapters", "documentUrl", "notes",
            "screens", "windows", "leftImage", "rightImage", "assetUrl", "assetLicense", "parts",
            "devices", "groups", "zones", "locations", "routes", "milestones", "claimA", "claimB",
            "realQuestion", "choiceA", "choiceB", "outcomesA", "outcomesB", "past", "present",
            "next", "dimensions", "date", "brandName", "media", "product",
        )
        has_content = (any(sc.get(k) for k in content_keys)
                       or sc.get("statValue") is not None
                       or sc.get("value") is not None
                       or sc.get("progress") is not None)
        if not has_content:
            raise ValueError(
                f"Spec validation failed: scene[{i}] (id={sc.get('id')!r}, "
                f"preset={sc.get('preset')!r}) has no renderable content."
            )

        # Data-driven presets would silently render their ⚠ placeholder otherwise.
        #
        # The test is TRUTHINESS, not `is not None`. `tokens: []` and `rows: []` are
        # not None, so an `is not None` check accepted them — and an empty list
        # renders exactly the empty chrome this guard exists to prevent.
        #
        # But truthiness alone would reject a legitimate `statValue: 0` or
        # `health: 0`, so a numeric zero counts as content. Only empty containers
        # and empty strings are rejected.
        def _has_content(v: Any) -> bool:
            if isinstance(v, bool):
                return True
            if isinstance(v, (int, float)):
                return True  # 0 is a real value a counter may want to show
            return bool(v)

        preset = sc.get("preset")
        required = _DATA_REQUIREMENTS.get(preset)
        if required and not any(_has_content(sc.get(k)) for k in required if k in sc):
            supplied = {k: sc.get(k) for k in required if k in sc}
            raise ValueError(
                f"Spec validation failed: scene[{i}] (id={sc.get('id')!r}) uses preset "
                f"{preset!r} which needs one of {list(required)}, but none were supplied "
                f"with content (got {supplied!r}). That would render a placeholder "
                "instead of real content."
            )

        # TgChat accepts either a regular text bubble or one of the allowlisted
        # sticker-only message kinds. This mirrors ChatMessageSchema exactly.
        messages = sc.get("messages")
        if isinstance(messages, list):
            for j, item in enumerate(messages):
                if not isinstance(item, dict):
                    raise ValueError(
                        f"Spec validation failed: scene[{i}] (id={sc.get('id')!r}) "
                        f"messages[{j}] must be an object, got {type(item).__name__}."
                    )
                has_text = isinstance(item.get("text"), str)
                sticker = item.get("sticker")
                if not has_text and sticker not in _ALLOWED_CHAT_STICKERS:
                    raise ValueError(
                        f"Spec validation failed: scene[{i}] (id={sc.get('id')!r}) "
                        f"messages[{j}] needs text or an allowlisted sticker; got {item!r}."
                    )

        # ROW SHAPE. The check above proves the list exists; this proves its items
        # are the shape the TS side expects.
        for field, req_keys in _ROW_SHAPES_HARD.items():
            items = sc.get(field)
            if not isinstance(items, list):
                continue
            for j, item in enumerate(items):
                if not isinstance(item, dict):
                    continue  # bare strings are legal shorthand in several fields
                for key in req_keys:
                    if item.get(key) is None:
                        raise ValueError(
                            f"Spec validation failed: scene[{i}] (id={sc.get('id')!r}, "
                            f"preset={preset!r}) {field}[{j}] is missing required "
                            f"{key!r}. Got keys {sorted(item)}. The TypeScript schema "
                            "rejects this and Remotion renders a red ERROR card for the "
                            "WHOLE video — which is a real mp4 that can be uploaded."
                        )

        # Soft shapes pass Zod and render an empty row. Warn: a decorative row with
        # no label is conceivable, an entire wall of them is a bug upstream.
        for field, req_keys in _ROW_SHAPES_SOFT.items():
            items = sc.get(field)
            if not isinstance(items, list):
                continue
            aliases = _ROW_ALIASES.get(field, {})
            for j, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                for key in req_keys:
                    accepted = aliases.get(key, (key,))
                    if not any(item.get(a) is not None for a in accepted):
                        alt = f" (or {', '.join(accepted[1:])})" if len(accepted) > 1 else ""
                        print(
                            f"[spec] WARNING: scene[{i}] (id={sc.get('id')!r}, "
                            f"preset={preset!r}) {field}[{j}] has no {key!r}{alt}; "
                            f"keys are {sorted(item)}. That row renders blank."
                        )

        # An unknown transition name fails Zod in Root.tsx, which degrades the
        # whole render to a red ERROR card. Same failure mode as a bad theme.
        transition = sc.get("transition")
        if transition is not None:
            if not isinstance(transition, dict):
                raise ValueError(
                    f"Spec validation failed: scene[{i}] 'transition' must be a dict, "
                    f"got {type(transition).__name__}."
                )
            t_type = transition.get("type", "fade")
            if t_type not in TRANSITIONS:
                raise ValueError(
                    f"Spec validation failed: scene[{i}] has unknown transition "
                    f"{t_type!r}. Valid transitions: {sorted(TRANSITIONS)}."
                )
            t_frames = transition.get("durationInFrames")
            if t_frames is not None and (not isinstance(t_frames, int) or t_frames <= 0):
                raise ValueError(
                    f"Spec validation failed: scene[{i}] transition 'durationInFrames' "
                    f"must be a positive int, got {t_frames!r}."
                )
            if i == 0 and t_type != "none":
                raise ValueError(
                    "Spec validation failed: scene[0] declares a transition, but a "
                    "transition runs BETWEEN two scenes and the first scene has "
                    "nothing to come from. Move it to scene[1]."
                )

    # ---------------------------------------------------- reading time on screen
    # A scene can be perfectly composed and still unreadable: the text is sized
    # to fit, nothing overflows, and it is on screen for 0.4s. This is invisible
    # to a still frame and to every layout check, and it was the actual complaint
    # about the channel's output.
    #
    # Russian prose reads at roughly 12 chars/sec on a phone (deliberately
    # generous — a viewer re-reads a headline rather than parsing it once). The
    # presets now guarantee their reveals SETTLE with MIN_DWELL_SEC to spare
    # (remotion/src/lib/pacing.ts), but no preset can conjure time that the
    # scene's duration does not contain.
    #
    # Warn rather than block: duration comes from the narration length, so a
    # dense scene is a script problem to fix upstream, and a decorative scene
    # with a long caption nobody needs to read is legitimate.
    fps_val = spec.get("fps") or FPS
    for i, sc in enumerate(scenes):
        chars = sum(
            len(v)
            for k, v in sc.items()
            if isinstance(v, str) and k not in {"id", "preset", "audioUrl"} and not k.endswith("Color")
        )
        if not chars:
            continue
        need = chars / READ_CHARS_PER_SEC
        have = int(sc["durationInFrames"]) / fps_val
        if have < need * 0.6:  # 0.6: allow overlap with narration continuing
            print(
                f"[spec] WARNING: scene[{i}] (id={sc.get('id')!r}, preset={sc.get('preset')!r}) "
                f"shows {chars} chars in {have:.1f}s; reading that needs about "
                f"{need:.1f}s. The viewer will not finish it."
            )



    # ------------------------------------------------------------ audio wiring
    # Main.tsx mounts BOTH a root <Audio> and a per-scene <Audio>. Supplying both
    # is never what the author meant: the narration plays twice, offset by the
    # scene start, which sounds like an echo rather than an obvious bug. Catch it
    # here — it is inaudible in a still frame and easy to miss in review.
    root_audio = spec.get("audioUrl")
    scene_audio = [i for i, sc in enumerate(scenes) if sc.get("audioUrl")]
    if root_audio and scene_audio:
        raise ValueError(
            f"Spec validation failed: spec has a root 'audioUrl' ({root_audio!r}) AND "
            f"per-scene 'audioUrl' on scenes {scene_audio}. Remotion mounts both, so "
            "the voice-over would play twice overlapping itself. Keep one: per-scene "
            "tracks for narration, root only for a single continuous mix."
        )

    # A spec where SOME scenes speak and others do not is almost always a bug in
    # the voicing step rather than an artistic choice, and the result is a video
    # that goes silent partway through. Warn loudly; do not block, because a
    # deliberately silent B-roll scene is legitimate.
    if scene_audio and len(scene_audio) != len(scenes):
        silent = [i for i in range(len(scenes)) if i not in scene_audio]
        print(
            f"[spec] WARNING: scenes {silent} have no 'audioUrl' while "
            f"{len(scene_audio)}/{len(scenes)} do — those stretches render silent."
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
    style: Optional[str] = None,
    style_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the VideoSpec dict handed to Remotion.

    Geometry comes from `video_format` (name/tuple/VideoFormat); explicit
    width/height still win so existing callers keep working.
    """
    fmt = resolve_format(video_format) if video_format is not None else FORMATS[DEFAULT_FORMAT]
    out_w = width if width is not None else fmt.width
    out_h = height if height is not None else fmt.height

    # Themes are a closed set in remotion/src/presets/brand.ts. An unknown name
    # fails Zod parsing inside Root.tsx, which silently degrades the whole render
    # into a 2-second red ERROR card instead of the real video. Catch it here,
    # where the message can name the offending value and the valid options.
    if theme is not None and theme not in THEMES:
        raise ValueError(
            f"Spec validation failed: unknown theme {theme!r}. "
            f"Valid themes: {sorted(THEMES)}. "
            "An unknown theme renders a red ERROR card, not a video."
        )

    scene_dicts = [s.to_dict() if isinstance(s, Scene) else s for s in scenes]
    total_frames = compute_total_frames(scene_dicts)

    spec: Dict[str, Any] = {
        "width": out_w,
        "height": out_h,
        "fps": fps,
        "durationInFrames": total_frames,
        "format": fmt.name,
        "safeMargin": fmt.safe_margin_px,
        "theme": theme or DEFAULT_THEME,
        "style": style,
        "styleConfig": style_config,
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
    if style is None:
        spec.pop("style")
    if style_config is None:
        spec.pop("styleConfig")
    if audio_url:
        spec["audioUrl"] = audio_url
    return spec
