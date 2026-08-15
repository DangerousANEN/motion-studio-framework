"""Integration smoke check for the Studio v2 FastAPI surface."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from msf.panel.server import app
from msf.studio.contracts import StoryboardDraft, StoryboardScene


EXPANSION_SCENES = {
    "HookStack", "KineticPhrase", "ProblemSolution", "FeatureSpotlight", "CaseStudyBoard",
    "MythFact", "QuoteEvidence", "StatsBand", "SourceStack", "CountdownRing",
    "PromptComposer", "ProviderChat", "NotificationStack", "CommentThread", "PollResult",
    "BrowserTour", "ScreenMagnifier", "DeviceShowcase", "VoiceWave", "VideoFrame",
}
V24_SCENES = {
    "BenchmarkArena", "BenchmarkHeatmap", "LeaderboardRace", "CostQualityScatter", "CapabilityRadar", "ContextWindowLadder", "TrueCostCalculator", "TokenFlowSankey", "ClaimEvidenceChain", "EvidenceConflictBoard", "ExperimentProtocol", "ReleaseDelta",
    "TelegramChannelPost", "TelegramFeedScroll", "TelegramForwardChain", "ReactionPulse", "QuoteRepost", "CommunityFAQ", "ChangelogTerminal", "PromptABLab", "AgentRunConsole", "BrowserDecisionTable",
    "ThreePhoto360Drift", "PhotoConstellation", "DeepZoomStory", "BeforeAfterLens", "VideoChapterRail", "VoiceNotePullQuote", "DocumentMarginNotes", "AppScreenGallery", "LayeredWindowStack", "ImageEvidenceCompare",
    "AssetOrbit3D", "ExplodedProductView", "WorkflowFlyThrough3D", "DataCube", "LogoSculpture3D", "DeviceConveyor3D", "ParticleDataField", "IsometricWorkflowCity", "GlobeSignalMap", "MilestoneCorridor3D",
    "ColdOpenContradiction", "CounterfactualSplit", "MemoryTimeline", "DecisionTree", "TradeoffSliders", "CalendarLaunchWindow", "ProofBackedCTA", "BrandOutroMosaic",
}
EXPANSION_SCENES |= V24_SCENES
EXPANSION_STYLES = {
    "aurora_flux", "cobalt_command", "infrared_alert", "violet_luxe", "porcelain",
    "liquid_chrome", "kinetic_poster", "midnight_orbit", "pixel_arcade", "coral_creator",
}


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[1]
    packs = json.loads((repo / "projects" / "llm_hubs" / "evidence_packs.json").read_text(encoding="utf-8"))["packs"]
    research = packs[0]
    claim_id = research["claims"][0]["claim_id"]
    draft = StoryboardDraft(
        title="API integration check",
        research_id=research["research_id"],
        scenes=[StoryboardScene(
            preset="QuoteCard",
            text="Ollama документирует локальный запуск на поддерживаемых системах.",
            duration_in_frames=360,
            evidence_claim_ids=[claim_id],
        )],
    )
    client = TestClient(app)
    catalog = client.get("/api/studio/catalog", params={"tier": "preset", "limit": 200})
    assert catalog.status_code == 200, catalog.text
    catalog_names = {item["name"] for item in catalog.json()["items"]}
    assert catalog.json()["total"] == 117, catalog.text
    assert {"DecisionGrid", "AgentRunConsole", "AssetOrbit3D", "BenchmarkArena", "TelegramChannelPost"} <= catalog_names, catalog.text
    styles = client.get("/api/studio/styles")
    assert styles.status_code == 200, styles.text
    style_ids = {item["id"] for item in styles.json()["families"]}
    assert "product_tutorial" in style_ids, styles.text
    assert EXPANSION_STYLES <= style_ids, (
        f"style catalog missing expansion families: {sorted(EXPANSION_STYLES - style_ids)}"
    )
    evidence = client.post("/api/studio/research/validate", json={"research": research})
    assert evidence.status_code == 200 and evidence.json()["valid"], evidence.text
    storyboard = client.post("/api/studio/storyboards/validate", json={"storyboard": draft.model_dump(mode="json"), "research": research, "tier": "preset"})
    assert storyboard.status_code == 200 and storyboard.json()["valid"], storyboard.text
    run = client.post("/api/studio/runs/prepare", json={
        "topic": "Endpoint smoke video", "preset": "HookStack", "style": "aurora_flux",
        "style_config": {"palette": {"neon": "#37D9FF"}, "effects": {"bloom": 0.3, "vignette": 0.2}, "motion": {"damping": 20}},
    })
    assert run.status_code == 200 and run.json()["run"]["status"] == "draft", run.text
    assert run.json()["request"]["style"] == "aurora_flux", run.text
    assert run.json()["request"]["style_config"]["palette"]["neon"] == "#37D9FF", run.text
    assert run.json()["request"]["style_config"]["effects"]["vignette"] == 0.2, run.text
    print("studio_api=catalog(117),styles(+10),evidence,storyboard,run_prepare OK")
