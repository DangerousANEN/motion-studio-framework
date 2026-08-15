"""Stable style-family discovery for MSF Studio operators and agents.

The renderer owns the visual implementation; this module exposes a compact,
versioned description so a weak agent chooses valid defaults instead of inventing
CSS or colour values without context.
"""
from __future__ import annotations

from typing import Any

STYLE_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "id": "llm_hubs_neon",
        "label": "LLM Hubs Neon",
        "summary": "Near-black glass with configurable neon action colour and aqua data accent; release-safe, readable motion.",
        "recommended_intents": ["launch", "model_news", "comparison", "cta"],
        "recommended_scenes": ["HeroKinetic", "MetricTrend", "DecisionGrid", "LlmHubsCTA", "ImageSpotlight"],
        "defaults": {"palette": {"bg": "#030807", "surface": "#091512", "neon": "#00F0A8", "cyan": "#58E6D2"}, "backdrop": "grid", "surface": "glass", "effects": {"bloom": 0.5, "chromatic": 0}},
    },
    {
        "id": "product_tutorial",
        "label": "Product Tutorial",
        "summary": "Blueprint UI system for screen walkthroughs, click paths and precise product explanations.",
        "recommended_intents": ["tutorial", "onboarding", "screen_demo", "how_to"],
        "recommended_scenes": ["ScreenGuide", "ScreenRecord", "StepList", "CodeReveal", "FocusOverlay"],
        "defaults": {"backdrop": "grid", "surface": "soft", "effects": {"bloom": 0.24, "chromatic": 0}},
    },
    {
        "id": "terminal",
        "label": "Terminal",
        "summary": "Lime command-line language for coding, API and agent implementation demos.",
        "recommended_intents": ["code", "api", "agent_workflow", "debug"],
        "recommended_scenes": ["CodeReveal", "ScreenGuide", "AiChatStream", "FlowDiagram", "StatCounter"],
        "defaults": {"backdrop": "dots", "surface": "glass", "effects": {"bloom": 0.46, "chromatic": 0}},
    },
    {
        "id": "creator_glass",
        "label": "Creator Glass",
        "summary": "Premium mesh-light and glass framing for image, video and creator-story inserts.",
        "recommended_intents": ["creator_story", "media_insert", "launch", "testimonial"],
        "recommended_scenes": ["ImageSpotlight", "YouTubeCard", "VideoEmbed", "TelegramVoiceRound", "SubscribeCTA"],
        "defaults": {"backdrop": "mesh", "surface": "glass", "effects": {"bloom": 0.6, "chromatic": 0.035}},
    },
    {
        "id": "social_native",
        "label": "Social Native",
        "summary": "Compact, restrained feed-like UI for chats, posts, social proof and notification moments.",
        "recommended_intents": ["social_proof", "chat", "community", "announcement"],
        "recommended_scenes": ["TgChat", "TelegramVoiceRound", "PostCard", "CommentWall", "NotificationOverlay"],
        "defaults": {"backdrop": "plain", "surface": "flat", "effects": {"bloom": 0.16, "chromatic": 0}},
    },
    {
        "id": "editorial",
        "label": "Editorial",
        "summary": "High-contrast text-first explainer system for research and evidence-heavy breakdowns.",
        "recommended_intents": ["research", "evidence", "analysis", "timeline"],
        "recommended_scenes": ["QuoteCard", "TimelineReveal", "BeforeAfter", "MetricTrend", "DefinitionCard"],
        "defaults": {"backdrop": "plain", "surface": "flat", "effects": {"bloom": 0.1, "chromatic": 0}},
    },
    {
        "id": "aurora_flux", "label": "Aurora Flux",
        "summary": "Luminous teal-violet mesh for premium technology launches and abstract innovation narratives.",
        "recommended_intents": ["launch", "innovation", "premium", "feature"],
        "recommended_scenes": ["HookStack", "FeatureSpotlight", "KineticPhrase", "DeviceShowcase", "VideoFrame"],
        "defaults": {"palette": {"bg": "#07111E", "surface": "#10243A", "neon": "#5CE1E6", "cyan": "#B794F4"}, "backdrop": "mesh", "surface": "glass", "motion": {"damping": 19}, "effects": {"grain": 0.02, "bloom": 0.68, "chromatic": 0.025}},
    },
    {
        "id": "cobalt_command", "label": "Cobalt Command",
        "summary": "Controlled enterprise-blue system for browser tours, B2B proof and operational explainers.",
        "recommended_intents": ["b2b", "data", "tutorial", "system"],
        "recommended_scenes": ["BrowserTour", "ScreenMagnifier", "CaseStudyBoard", "StatsBand", "SourceStack"],
        "defaults": {"palette": {"bg": "#07152F", "surface": "#0E2851", "neon": "#4EA1FF", "cyan": "#8CCBFF"}, "backdrop": "grid", "surface": "soft", "motion": {"damping": 23}, "effects": {"grain": 0.015, "bloom": 0.28, "chromatic": 0}},
    },
    {
        "id": "infrared_alert", "label": "Infrared Alert",
        "summary": "Urgent red update language for release windows, deadlines, breaking changes and warnings.",
        "recommended_intents": ["breaking_news", "deadline", "alert", "release"],
        "recommended_scenes": ["KineticPhrase", "CountdownRing", "NotificationStack", "HookStack", "MythFact"],
        "defaults": {"palette": {"bg": "#180609", "surface": "#360D14", "neon": "#FF4D57", "cyan": "#FFB18A"}, "backdrop": "dots", "surface": "flat", "motion": {"damping": 18}, "effects": {"grain": 0.045, "bloom": 0.52, "chromatic": 0.05}},
    },
    {
        "id": "violet_luxe", "label": "Violet Luxe",
        "summary": "Cinematic violet-and-ice glass for premium creator narratives, testimonials and product reveals.",
        "recommended_intents": ["premium", "creator_story", "testimonial", "launch"],
        "recommended_scenes": ["QuoteEvidence", "VideoFrame", "DeviceShowcase", "FeatureSpotlight", "CommentThread"],
        "defaults": {"palette": {"bg": "#130C28", "surface": "#2B1D4D", "neon": "#B48CFF", "cyan": "#C9F5FF"}, "backdrop": "mesh", "surface": "glass", "motion": {"damping": 20}, "effects": {"grain": 0.028, "bloom": 0.58, "chromatic": 0.02}},
    },
    {
        "id": "porcelain", "label": "Porcelain",
        "summary": "Light high-legibility educational system with calm ink typography and almost no visual noise.",
        "recommended_intents": ["education", "research", "how_to", "evidence"],
        "recommended_scenes": ["ProblemSolution", "MythFact", "SourceStack", "StatsBand", "QuoteEvidence"],
        "defaults": {"palette": {"bg": "#F5F1E9", "surface": "#FFFFFF", "neon": "#1A5C78", "cyan": "#D3834C"}, "backdrop": "plain", "surface": "flat", "motion": {"damping": 25}, "effects": {"grain": 0.01, "bloom": 0, "chromatic": 0}},
    },
    {
        "id": "liquid_chrome", "label": "Liquid Chrome",
        "summary": "Graphite-and-cyan reflective product surfaces for demos, hardware-like reveals and feature showcases.",
        "recommended_intents": ["product", "feature", "demo", "launch"],
        "recommended_scenes": ["DeviceShowcase", "FeatureSpotlight", "ScreenMagnifier", "VideoFrame", "PromptComposer"],
        "defaults": {"palette": {"bg": "#091013", "surface": "#1A292E", "neon": "#61E5EA", "cyan": "#E2F8FF"}, "backdrop": "mesh", "surface": "glass", "motion": {"damping": 18}, "effects": {"grain": 0.035, "bloom": 0.62, "chromatic": 0.04}},
    },
    {
        "id": "kinetic_poster", "label": "Kinetic Poster",
        "summary": "Acid poster-scale hierarchy with high-contrast panels built for fast but stable opening hooks.",
        "recommended_intents": ["hook", "announcement", "challenge", "chapter"],
        "recommended_scenes": ["HookStack", "KineticPhrase", "ProblemSolution", "CountdownRing", "PollResult"],
        "defaults": {"palette": {"bg": "#101010", "surface": "#F6F3E8", "neon": "#D9FF3F", "cyan": "#FF6B3D"}, "backdrop": "plain", "surface": "brutal", "motion": {"damping": 19}, "effects": {"grain": 0.035, "bloom": 0.35, "chromatic": 0}},
    },
    {
        "id": "midnight_orbit", "label": "Midnight Orbit",
        "summary": "Deep-navy orbital depth for model ecosystems, roadmaps, research maps and deliberate analysis.",
        "recommended_intents": ["ecosystem", "roadmap", "research", "analysis"],
        "recommended_scenes": ["SourceStack", "CaseStudyBoard", "StatsBand", "ProviderChat", "QuoteEvidence"],
        "defaults": {"palette": {"bg": "#050B1C", "surface": "#101B36", "neon": "#73A7FF", "cyan": "#A3E8FF"}, "backdrop": "noise", "surface": "glass", "motion": {"damping": 24}, "effects": {"grain": 0.022, "bloom": 0.48, "chromatic": 0.015}},
    },
    {
        "id": "pixel_arcade", "label": "Pixel Arcade",
        "summary": "Playful lime-purple challenge language for onboarding, polls, playful education and gamified moments.",
        "recommended_intents": ["onboarding", "challenge", "poll", "playful"],
        "recommended_scenes": ["PollResult", "CountdownRing", "KineticPhrase", "PromptComposer", "NotificationStack"],
        "defaults": {"palette": {"bg": "#140C2F", "surface": "#2B185A", "neon": "#B9FF3B", "cyan": "#C795FF"}, "backdrop": "dots", "surface": "brutal", "motion": {"damping": 18}, "effects": {"grain": 0.04, "bloom": 0.58, "chromatic": 0.08}},
    },
    {
        "id": "coral_creator", "label": "Coral Creator",
        "summary": "Warm coral creator-story cards for community discussion, testimonials, social proof and friendly explainers.",
        "recommended_intents": ["creator_story", "social_proof", "community", "testimonial"],
        "recommended_scenes": ["CommentThread", "VoiceWave", "ProviderChat", "VideoFrame", "NotificationStack"],
        "defaults": {"palette": {"bg": "#24131C", "surface": "#482433", "neon": "#FF8D72", "cyan": "#FFD2B8"}, "backdrop": "noise", "surface": "soft", "motion": {"damping": 21}, "effects": {"grain": 0.025, "bloom": 0.48, "chromatic": 0.015}},
    },
)

STYLE_CONFIG_FIELDS: tuple[dict[str, Any], ...] = (
    {"path": "palette.neon", "type": "color", "label": "Neon / action", "description": "Primary interactive accent used by theme-adaptive scenes."},
    {"path": "palette.bg", "type": "color", "label": "Background", "description": "Scene canvas background."},
    {"path": "palette.surface", "type": "color", "label": "Surface", "description": "Cards, frames and device surfaces."},
    {"path": "palette.cyan", "type": "color", "label": "Data accent", "description": "Secondary visual/data accent."},
    {"path": "palette.text", "type": "color", "label": "Primary text", "description": "High-contrast text colour; preview dense copy after a change."},
    {"path": "palette.muted", "type": "color", "label": "Muted text", "description": "Secondary labels and metadata."},
    {"path": "backdrop", "type": "enum", "values": ["grid", "mesh", "noise", "dots", "scanlines", "plain"]},
    {"path": "surface", "type": "enum", "values": ["brutal", "soft", "glass", "flat"]},
    {"path": "effects.bloom", "type": "range", "min": 0, "max": 1},
    {"path": "effects.grain", "type": "range", "min": 0, "max": 1},
    {"path": "effects.vignette", "type": "range", "min": 0, "max": 1},
    {"path": "effects.scanlines", "type": "range", "min": 0, "max": 1, "caution": "Use only when the scene does not contain small UI text."},
    {"path": "effects.chromatic", "type": "range", "min": 0, "max": 1, "caution": "Keep at 0 for dense reading text."},
    {"path": "motion.damping", "type": "range", "min": 8, "max": 30, "caution": "Use >=18 for stable text dwell."},
    {"path": "motion.stiffness", "type": "range", "min": 80, "max": 240, "caution": "Higher values must be previewed; do not use them to create text jitter."},
    {"path": "motion.staggerScale", "type": "range", "min": 0.7, "max": 1.5},
)


def style_catalog_payload() -> dict[str, Any]:
    return {
        "contract_version": "2.3",
        "families": list(STYLE_FAMILIES),
        "config_fields": list(STYLE_CONFIG_FIELDS),
        "safety": {
            "text_motion": "Prefer damping >= 18 and chromatic = 0 for fact-heavy scenes.",
            "asset_scope": "StyleConfig accepts tokens only; it cannot inject arbitrary CSS or scripts.",
        },
    }
