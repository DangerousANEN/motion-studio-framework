"""Curated v2 metadata layered over the TypeScript source-of-truth registry.

The mapping intentionally contains only semantic information absent from the
renderer registry.  Names, categories and required renderer fields continue to
come from ``msf.registry`` at runtime.
"""
from __future__ import annotations

from typing import Dict, Tuple


SCENE_METADATA: Dict[str, dict] = {
    "HeroKinetic": {
        "intent_tags": ("hook", "headline", "announcement"),
        "audio_roles": ("intro_hit", "riser"),
    },
    "QuoteCard": {
        "intent_tags": ("quote", "evidence", "testimonial"),
        "audio_roles": ("paper_tick", "soft_hit"),
    },
    "TgChat": {
        "intent_tags": ("dialogue", "before_after", "support_chat"),
        "required_data_hints": ("messages",),
        "audio_roles": ("message", "ui_click"),
    },
    "PhoneMockup": {
        "intent_tags": ("app_demo", "mobile", "product"),
        "audio_roles": ("ui_click", "swipe"),
    },
    "StatCounter": {
        "intent_tags": ("metric", "result", "proof"),
        "required_data_hints": ("statValue",),
        "audio_roles": ("data_tick", "milestone_hit"),
    },
    "Bars3D": {
        "intent_tags": ("comparison", "data", "ranking"),
        "required_data_hints": ("bars",),
        "audio_roles": ("data_tick", "whoosh"),
    },
    "VersusSplit": {
        "intent_tags": ("comparison", "versus", "choice"),
        "required_data_hints": ("left", "right"),
        "audio_roles": ("impact", "whoosh"),
    },
    "CodeReveal": {
        "intent_tags": ("code", "tutorial", "implementation"),
        "required_data_hints": ("code",),
        "audio_roles": ("typing", "ui_click"),
    },
    "DecisionGrid": {
        "intent_tags": ("choice", "routing", "comparison", "decision"),
        "required_data_hints": ("cards",),
        "audio_roles": ("data_tick", "soft_hit", "success_chime"),
    },
    "StepList": {
        "intent_tags": ("how_to", "process", "checklist"),
        "required_data_hints": ("steps",),
        "audio_roles": ("step_tick", "success_chime"),
    },
    "BeforeAfter": {
        "intent_tags": ("before_after", "transformation", "comparison"),
        "required_data_hints": ("before", "after"),
        "audio_roles": ("whoosh", "success_chime"),
    },
    "MetricTrend": {
        "intent_tags": ("metric", "trend", "growth"),
        "required_data_hints": ("points",),
        "audio_roles": ("data_tick", "riser", "milestone_hit"),
    },
    "ScreenGuide": {
        "intent_tags": ("tutorial", "screen_demo", "how_to", "click_path"),
        "required_data_hints": ("src or images[0]", "cursorSteps"),
        "audio_roles": ("ui_click", "focus_ping", "soft_whoosh"),
    },
    "ScreenRecord": {
        "intent_tags": ("screen_demo", "product", "walkthrough"),
        "required_data_hints": ("src or images[0]",),
        "audio_roles": ("ui_click", "ambient_tech"),
    },
    "YouTubeCard": {
        "intent_tags": ("video_insert", "creator", "longform"),
        "required_data_hints": ("src or images[0]",),
        "audio_roles": ("play_click", "soft_whoosh"),
    },
    "ImageSpotlight": {
        "intent_tags": ("image_insert", "evidence", "creator_story"),
        "required_data_hints": ("src or images[0]",),
        "audio_roles": ("camera_shutter", "soft_whoosh"),
    },
    "TelegramVoiceRound": {
        "intent_tags": ("telegram", "voice_message", "social_proof"),
        "required_data_hints": ("contactName", "duration"),
        "audio_roles": ("message", "voice_wave", "ui_click"),
    },
    # v2.3 narrative, proof and conversion expansion
    "HookStack": {"intent_tags": ("hook", "announcement", "retention"), "required_data_hints": ("headline", "subhead"), "audio_roles": ("intro_hit", "riser", "impact")},
    "KineticPhrase": {"intent_tags": ("hook", "chapter", "emphasis"), "required_data_hints": ("phrase",), "audio_roles": ("impact", "stinger")},
    "ProblemSolution": {"intent_tags": ("problem_solution", "comparison", "explain"), "required_data_hints": ("problem", "solution"), "audio_roles": ("whoosh", "success_chime")},
    "FeatureSpotlight": {"intent_tags": ("feature", "product", "benefit"), "required_data_hints": ("feature", "benefit"), "audio_roles": ("focus_ping", "riser")},
    "CaseStudyBoard": {"intent_tags": ("case_study", "workflow", "result"), "required_data_hints": ("context", "action", "result"), "audio_roles": ("step_tick", "success_chime")},
    "MythFact": {"intent_tags": ("myth_fact", "education", "correction"), "required_data_hints": ("myth", "fact"), "audio_roles": ("impact", "reveal_flash")},
    "QuoteEvidence": {"intent_tags": ("quote", "evidence", "primary_source"), "required_data_hints": ("quote", "source"), "audio_roles": ("paper_tick", "soft_hit")},
    "StatsBand": {"intent_tags": ("data", "stats", "proof"), "required_data_hints": ("stats",), "audio_roles": ("data_tick", "milestone_hit")},
    "SourceStack": {"intent_tags": ("evidence", "sources", "research"), "required_data_hints": ("sources",), "audio_roles": ("paper_tick", "success_chime")},
    "CountdownRing": {"intent_tags": ("countdown", "deadline", "release"), "required_data_hints": ("value",), "audio_roles": ("tick", "riser", "impact")},
    # v2.3 social, tutorial, media and overlay expansion
    "PromptComposer": {"intent_tags": ("prompt", "agent", "input"), "required_data_hints": ("prompt",), "audio_roles": ("typing", "ui_click")},
    "ProviderChat": {"intent_tags": ("provider_chat", "dialogue", "reasoning"), "required_data_hints": ("provider", "prompt", "answer"), "audio_roles": ("message", "ui_click")},
    "NotificationStack": {"intent_tags": ("notification", "update", "overlay"), "required_data_hints": ("notifications",), "audio_roles": ("notification_ping", "soft_whoosh")},
    "CommentThread": {"intent_tags": ("comments", "social_proof", "community"), "required_data_hints": ("comments",), "audio_roles": ("message", "soft_hit")},
    "PollResult": {"intent_tags": ("poll", "choice", "data"), "required_data_hints": ("options",), "audio_roles": ("data_tick", "milestone_hit")},
    "BrowserTour": {"intent_tags": ("browser", "tutorial", "walkthrough"), "required_data_hints": ("url", "steps"), "audio_roles": ("ui_click", "focus_ping")},
    "ScreenMagnifier": {"intent_tags": ("screen_demo", "zoom", "tutorial"), "required_data_hints": ("mediaUrl", "focus"), "audio_roles": ("focus_ping", "soft_whoosh")},
    "DeviceShowcase": {"intent_tags": ("device", "app_demo", "media"), "required_data_hints": ("mediaUrl", "device"), "audio_roles": ("whoosh", "ui_click")},
    "VoiceWave": {"intent_tags": ("voice_message", "audio", "testimonial"), "required_data_hints": ("speaker", "caption"), "audio_roles": ("voice_wave", "message")},
    "VideoFrame": {"intent_tags": ("video_insert", "reel", "creator"), "required_data_hints": ("mediaUrl", "title"), "audio_roles": ("play_click", "soft_whoosh")},
}


# v2.4 universal scene expansion: all entries carry explicit discovery intent and
# sound roles, so no new preset falls through to generic explainer routing.
SCENE_METADATA.update({
    "BenchmarkArena": {"intent_tags": ("benchmark", "comparison", "model"), "required_data_hints": ("models",), "audio_roles": ("intro_hit", "data_tick")},
    "BenchmarkHeatmap": {"intent_tags": ("benchmark", "heatmap", "evidence"), "required_data_hints": ("rows", "columns"), "audio_roles": ("data_tick",)},
    "LeaderboardRace": {"intent_tags": ("ranking", "benchmark", "change"), "required_data_hints": ("rankBefore", "rankAfter"), "audio_roles": ("riser", "milestone_hit")},
    "CostQualityScatter": {"intent_tags": ("cost", "quality", "comparison"), "required_data_hints": ("scatterPoints",), "audio_roles": ("data_tick", "focus_ping")},
    "CapabilityRadar": {"intent_tags": ("capabilities", "comparison", "radar"), "required_data_hints": ("axes", "series"), "audio_roles": ("data_tick",)},
    "ContextWindowLadder": {"intent_tags": ("context", "capacity", "comparison"), "required_data_hints": ("items",), "audio_roles": ("step_tick",)},
    "TrueCostCalculator": {"intent_tags": ("cost", "calculator", "workload"), "required_data_hints": ("lineItems",), "audio_roles": ("data_tick", "success_chime")},
    "TokenFlowSankey": {"intent_tags": ("tokens", "flow", "diagram"), "required_data_hints": ("flowNodes",), "audio_roles": ("soft_whoosh", "data_tick")},
    "ClaimEvidenceChain": {"intent_tags": ("research", "evidence", "claim"), "required_data_hints": ("claim", "evidence"), "audio_roles": ("paper_tick", "soft_hit")},
    "EvidenceConflictBoard": {"intent_tags": ("research", "conflict", "sources"), "required_data_hints": ("sourceA", "sourceB"), "audio_roles": ("impact", "focus_ping")},
    "ExperimentProtocol": {"intent_tags": ("experiment", "method", "how_to"), "required_data_hints": ("steps",), "audio_roles": ("step_tick",)},
    "ReleaseDelta": {"intent_tags": ("release", "changelog", "update"), "required_data_hints": ("deltas",), "audio_roles": ("notification_ping", "soft_hit")},
    "TelegramChannelPost": {"intent_tags": ("telegram", "channel_post", "cta"), "required_data_hints": ("channel", "postText"), "audio_roles": ("message", "ui_click")},
    "TelegramFeedScroll": {"intent_tags": ("telegram", "feed", "social"), "required_data_hints": ("posts",), "audio_roles": ("soft_whoosh", "ui_click")},
    "TelegramForwardChain": {"intent_tags": ("telegram", "forward", "distribution"), "required_data_hints": ("origin", "forwards"), "audio_roles": ("message", "whoosh")},
    "ReactionPulse": {"intent_tags": ("social_proof", "reactions", "community"), "required_data_hints": ("reactions",), "audio_roles": ("notification_ping", "data_tick")},
    "QuoteRepost": {"intent_tags": ("quote", "repost", "commentary"), "required_data_hints": ("original", "commentary"), "audio_roles": ("message", "soft_hit")},
    "CommunityFAQ": {"intent_tags": ("faq", "community", "education"), "required_data_hints": ("questions", "answers"), "audio_roles": ("message", "success_chime")},
    "ChangelogTerminal": {"intent_tags": ("changelog", "terminal", "release"), "required_data_hints": ("changes",), "audio_roles": ("typing", "soft_hit")},
    "PromptABLab": {"intent_tags": ("prompt", "comparison", "agent"), "required_data_hints": ("promptA", "promptB"), "audio_roles": ("typing", "impact")},
    "AgentRunConsole": {"intent_tags": ("agent", "pipeline", "debug"), "required_data_hints": ("steps",), "audio_roles": ("step_tick", "success_chime")},
    "BrowserDecisionTable": {"intent_tags": ("browser", "table", "decision"), "required_data_hints": ("columns", "rows"), "audio_roles": ("ui_click", "focus_ping")},
    "ThreePhoto360Drift": {"intent_tags": ("photos", "story", "cinematic"), "required_data_hints": ("images",), "audio_roles": ("ambient_swell", "soft_whoosh")},
    "PhotoConstellation": {"intent_tags": ("photos", "gallery", "cinematic"), "required_data_hints": ("images",), "audio_roles": ("ambient_swell",)},
    "DeepZoomStory": {"intent_tags": ("image", "zoom", "evidence"), "required_data_hints": ("image", "stops"), "audio_roles": ("focus_ping", "soft_whoosh")},
    "BeforeAfterLens": {"intent_tags": ("before_after", "image", "transformation"), "required_data_hints": ("beforeUrl", "afterUrl"), "audio_roles": ("whoosh", "success_chime")},
    "VideoChapterRail": {"intent_tags": ("video", "chapters", "creator"), "required_data_hints": ("videoUrl", "chapters"), "audio_roles": ("play_click", "soft_whoosh")},
    "VoiceNotePullQuote": {"intent_tags": ("voice", "quote", "telegram"), "required_data_hints": ("speaker", "quote"), "audio_roles": ("voice_wave", "message")},
    "DocumentMarginNotes": {"intent_tags": ("document", "annotation", "research"), "required_data_hints": ("documentUrl", "notes"), "audio_roles": ("paper_tick", "focus_ping")},
    "AppScreenGallery": {"intent_tags": ("app_demo", "screens", "product"), "required_data_hints": ("screens",), "audio_roles": ("ui_click", "soft_whoosh")},
    "LayeredWindowStack": {"intent_tags": ("workflow", "windows", "productivity"), "required_data_hints": ("windows",), "audio_roles": ("whoosh", "ui_click")},
    "ImageEvidenceCompare": {"intent_tags": ("screenshots", "evidence", "comparison"), "required_data_hints": ("leftImage", "rightImage"), "audio_roles": ("camera_shutter", "focus_ping")},
    "AssetOrbit3D": {"intent_tags": ("3d", "orbit", "product"), "required_data_hints": ("assetUrl or fallbackShape",), "audio_roles": ("ambient_swell", "whoosh")},
    "ExplodedProductView": {"intent_tags": ("3d", "exploded", "explain"), "required_data_hints": ("parts",), "audio_roles": ("impact", "soft_whoosh")},
    "WorkflowFlyThrough3D": {"intent_tags": ("3d", "workflow", "pipeline"), "required_data_hints": ("workflowNodes",), "audio_roles": ("ambient_swell", "step_tick")},
    "DataCube": {"intent_tags": ("3d", "data", "comparison"), "required_data_hints": ("x", "y", "z"), "audio_roles": ("data_tick", "impact")},
    "LogoSculpture3D": {"intent_tags": ("3d", "logo", "brand"), "audio_roles": ("logo_hit", "ambient_swell")},
    "DeviceConveyor3D": {"intent_tags": ("3d", "devices", "product"), "required_data_hints": ("devices",), "audio_roles": ("whoosh", "ui_click")},
    "ParticleDataField": {"intent_tags": ("3d", "particles", "data"), "required_data_hints": ("groups",), "audio_roles": ("ambient_swell", "data_tick")},
    "IsometricWorkflowCity": {"intent_tags": ("3d", "workflow", "isometric"), "required_data_hints": ("zones",), "audio_roles": ("ambient_tech", "step_tick")},
    "GlobeSignalMap": {"intent_tags": ("3d", "globe", "locations"), "required_data_hints": ("locations",), "audio_roles": ("ambient_swell", "signal_ping")},
    "MilestoneCorridor3D": {"intent_tags": ("3d", "timeline", "milestones"), "required_data_hints": ("milestones",), "audio_roles": ("whoosh", "milestone_hit")},
    "ColdOpenContradiction": {"intent_tags": ("hook", "contradiction", "retention"), "required_data_hints": ("claimA", "claimB"), "audio_roles": ("impact", "riser")},
    "CounterfactualSplit": {"intent_tags": ("choice", "outcomes", "comparison"), "required_data_hints": ("choiceA", "choiceB"), "audio_roles": ("whoosh", "impact")},
    "MemoryTimeline": {"intent_tags": ("story", "timeline", "chapter"), "required_data_hints": ("past", "present", "next"), "audio_roles": ("ambient_swell", "step_tick")},
    "DecisionTree": {"intent_tags": ("decision", "tree", "routing"), "required_data_hints": ("decisionNodes",), "audio_roles": ("step_tick", "success_chime")},
    "TradeoffSliders": {"intent_tags": ("tradeoff", "decision", "data"), "required_data_hints": ("dimensions",), "audio_roles": ("data_tick", "focus_ping")},
    "CalendarLaunchWindow": {"intent_tags": ("date", "launch", "deadline"), "required_data_hints": ("date",), "audio_roles": ("tick", "riser")},
    "ProofBackedCTA": {"intent_tags": ("cta", "proof", "conversion"), "required_data_hints": ("proof", "action"), "audio_roles": ("success_chime", "impact")},
    "BrandOutroMosaic": {"intent_tags": ("outro", "brand", "cta"), "required_data_hints": ("brandName", "handle"), "audio_roles": ("logo_hit", "ambient_swell")},
})

DEFAULT_INTENTS: Tuple[str, ...] = ("explainer",)
DEFAULT_AUDIO_ROLES: Tuple[str, ...] = ("transition_whoosh",)
