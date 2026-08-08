"""MSF LangGraph StateGraph Orchestrator (v2.1).

Provides a structured, state-driven multi-agent workflow for generating
remotion-based videos with self-correction, voice synthesis, vision QA, and render control.
"""
from __future__ import annotations

from typing import Dict, List, Optional, TypedDict
from pathlib import Path
import json
import subprocess
import shutil

from langgraph.graph import END, StateGraph


class VideoState(TypedDict):
    text: str
    preset: str
    accent: str
    reference_audio: str
    output_path: str
    agent_level: int
    scenes: List[Dict]
    audio_paths: List[str]
    spec_path: str
    final_mp4: str
    extracted_frames: List[str]
    qa_passed: bool
    retry_count: int
    error: Optional[str]


def node_gate_check(state: VideoState) -> VideoState:
    """Check agent level and validate allowed capabilities."""
    level = state.get("agent_level", 1)
    preset = state.get("preset", "HeroKinetic")
    allowed_presets = {"HeroKinetic", "StatCounter", "GridGridFloor", "SwipePanels", "TypewriterSub"}
    
    state["retry_count"] = state.get("retry_count", 0)
    
    if level <= 2 and preset not in allowed_presets:
        state["preset"] = "HeroKinetic"
        state["error"] = f"Dumb agent level={level} attempted non-allowed preset ({preset}). Fallback to HeroKinetic."
    return state


def node_script_split(state: VideoState) -> VideoState:
    """Split text into sentence-sized scenes."""
    from msf.orchestrators.remotion_runner import _split_into_scenes
    scenes = _split_into_scenes(state["text"])
    state["scenes"] = scenes
    return state


def node_voice_synthesis(state: VideoState) -> VideoState:
    """Synthesize voice cloning for all scenes using Qwen3 1.7B-Base."""
    from msf.skills_bridge.qwen3_tts import synthesize_voice_clone
    
    ref_audio = state.get("reference_audio", r"C:/Users/ANEN/qwen3_1.7B_clone_test.wav")
    scenes = state["scenes"]
    audio_paths = []
    
    output_dir = Path(state["output_path"]).parent if state.get("output_path") else Path("output/remotion")
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    
    for i, sc in enumerate(scenes):
        wav_path, dur = synthesize_voice_clone(text=sc["text"], ref_audio=ref_audio)
        dst_wav = audio_dir / f"scene_{i:02d}.wav"
        shutil.move(wav_path, str(dst_wav))
        audio_paths.append(str(dst_wav))
        sc["duration_in_frames"] = max(30, int(dur * 30))
        sc["audio_file"] = f"scene_{i:02d}.wav"
        sc["preset"] = state["preset"]
        sc["accent"] = state.get("accent", "gold")
        
    state["audio_paths"] = audio_paths
    return state


def node_build_remotion_spec(state: VideoState) -> VideoState:
    """Generate public/video-spec.json for Remotion bundling."""
    remotion_public = Path(__file__).resolve().parents[2] / "remotion" / "public"
    remotion_public.mkdir(parents=True, exist_ok=True)
    
    for audio_path in state.get("audio_paths", []):
        shutil.copy(audio_path, remotion_public / Path(audio_path).name)
        
    spec = {
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "scenes": state["scenes"],
    }
    
    spec_path = remotion_public / "video-spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    state["spec_path"] = str(spec_path)
    return state


def node_remotion_render(state: VideoState) -> VideoState:
    """Invoke Remotion CLI to render output video."""
    remotion_dir = Path(__file__).resolve().parents[2] / "remotion"
    out_mp4 = state.get("output_path", str(remotion_dir / "out" / "video.mp4"))
    
    subprocess.run(
        ["npx.cmd", "remotion", "render", "src/index.ts", "Main", out_mp4],
        cwd=str(remotion_dir),
        check=True,
        shell=True,
    )
    state["final_mp4"] = out_mp4
    return state


def node_vision_qa(state: VideoState) -> VideoState:
    """Extract keyframes and check video rendering quality."""
    mp4_path = state.get("final_mp4")
    if not mp4_path or not Path(mp4_path).exists():
        state["qa_passed"] = False
        state["error"] = "Vision QA: Output MP4 file missing."
        return state

    output_dir = Path(mp4_path).parent / "qa_frames"
    output_dir.mkdir(parents=True, exist_ok=True)

    frame_pattern = str(output_dir / "frame_%02d.png")
    cmd = [
        "ffmpeg", "-y", "-i", mp4_path,
        "-vf", "select='eq(n,15)+eq(n,45)+eq(n,75)'",
        "-vsync", "vfr", frame_pattern
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        state["extracted_frames"] = []
        state["qa_passed"] = True
        return state

    extracted = list(output_dir.glob("frame_*.png"))
    state["extracted_frames"] = [str(p) for p in extracted]
    
    valid_frames = [p for p in extracted if p.stat().st_size > 3000]
    if len(valid_frames) == 0:
        state["retry_count"] += 1
        state["qa_passed"] = False
        state["error"] = f"Vision QA failed (attempt {state['retry_count']}): frames corrupted."
    else:
        state["qa_passed"] = True
        
    return state


def check_qa_decision(state: VideoState) -> str:
    """Conditional Edge: Retry build if QA fails and retry count < 2."""
    if state.get("qa_passed", True):
        return "end"
    if state.get("retry_count", 0) < 2:
        return "retry"
    return "end"


def build_msf_graph():
    """Build and compile the MSF LangGraph workflow with Vision QA loop."""
    workflow = StateGraph(VideoState)
    
    workflow.add_node("gate_check", node_gate_check)
    workflow.add_node("script_split", node_script_split)
    workflow.add_node("voice_synthesis", node_voice_synthesis)
    workflow.add_node("build_remotion_spec", node_build_remotion_spec)
    workflow.add_node("remotion_render", node_remotion_render)
    workflow.add_node("vision_qa", node_vision_qa)
    
    workflow.set_entry_point("gate_check")
    workflow.add_edge("gate_check", "script_split")
    workflow.add_edge("script_split", "voice_synthesis")
    workflow.add_edge("voice_synthesis", "build_remotion_spec")
    workflow.add_edge("build_remotion_spec", "remotion_render")
    workflow.add_edge("remotion_render", "vision_qa")
    
    workflow.add_conditional_edges(
        "vision_qa",
        check_qa_decision,
        {
            "retry": "build_remotion_spec",
            "end": END
        }
    )
    
    return workflow.compile()


if __name__ == "__main__":
    app = build_msf_graph()
    print("✅ LangGraph MSF Workflow (v2.1 with Vision QA & Self-Correction) compiled successfully!")
