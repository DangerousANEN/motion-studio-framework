"""MSF Click-based Command Line Interface.

Provides CLI commands and progress indicators for running the Motion Studio Framework
pipeline from the terminal.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import click

from msf.config import MSFConfig
from msf.pipeline.orchestrator import PipelineOrchestrator


STAGES = [
    ("brief", "Briefing"),
    ("research", "Topic Research"),
    ("script", "Script Generation"),
    ("storyboard", "Storyboard Creation"),
    ("scenes", "Scene Assembly & Rendering"),
    ("assemble", "Final Video Assembly"),
    ("qc", "Quality Control"),
]


@click.command(name="msf")
@click.option(
    "--topic",
    "-t",
    required=True,
    type=str,
    help="Topic or prompt for the video content generation.",
)
@click.option(
    "--duration",
    "-d",
    type=float,
    default=45.0,
    help="Target video duration in seconds (default: 45.0).",
)
@click.option(
    "--style",
    "-s",
    type=str,
    default="viral_shorts",
    help="Visual or narrative style preset (default: viral_shorts).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Destination file path for the final MP4 video.",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Path to YAML configuration file.",
)
@click.option(
    "--research-to-script",
    is_flag=True,
    default=False,
    help="Research the topic and write a validated Russian storyboard JSON without rendering video.",
)
@click.option("--cta-handle", default="@llm_hubs", show_default=True, help="Telegram handle for the final CTA.")
@click.option("--cta-asset", default="готовый чек-лист и ссылки на источники", show_default=True, help="Concrete Telegram asset promised by CTA.")
@click.option("--style-family", default=None, help="One existing MSF renderer style family for the entire storyboard.")
@click.option("--research-provider", type=click.Choice(["duckduckgo", "searxng"]), default="duckduckgo", show_default=True)
@click.option("--release-topic", is_flag=True, default=False, help="Apply strict release freshness and primary-source requirements.")
@click.option("--comparison-mode", type=click.Choice(["none", "observed", "proposed"]), default="none", show_default=True, help="Request a cited side-by-side comparison or a proposed test plan.")
@click.option("--compare-model", "comparison_models", multiple=True, help="Model label to include in a side-by-side proof; pass twice for two models.")
@click.option("--visual-evidence-mode", type=click.Choice(["code_test", "ui_build", "game_build", "data_viz", "research_answer", "incident", "safety_failure"]), default=None, help="Preferred visual proof format.")
@click.option("--require-observed-comparison", is_flag=True, default=False, help="Fail rather than create a proposed comparison when reproducible proof is absent.")
def cli(
    topic: str,
    duration: float,
    style: str,
    output: Optional[str],
    config: Optional[str],
    research_to_script: bool,
    cta_handle: str,
    cta_asset: str,
    style_family: Optional[str],
    research_provider: str,
    release_topic: bool,
    comparison_mode: str,
    comparison_models: tuple[str, ...],
    visual_evidence_mode: Optional[str],
    require_observed_comparison: bool,
) -> None:
    """Motion Studio Framework (MSF) - Automated Viral Video Generation Pipeline."""
    click.echo(f"🎬 Motion Studio Framework CLI")
    click.echo(f"Topic: {topic}")
    click.echo(f"Target Duration: {duration}s | Style: {style}")

    if research_to_script:
        from msf.studio.contracts import ResearchToScriptRequest
        from msf.studio.research_to_script import ResearchToScriptError, ResearchToScriptWorkflow
        try:
            result = ResearchToScriptWorkflow().run(ResearchToScriptRequest(
                topic=topic,
                cta_handle=cta_handle,
                cta_asset=cta_asset,
                style_family=style_family,
                provider=research_provider,
                release_topic=release_topic,
                comparison_mode=comparison_mode,
                comparison_models=list(comparison_models),
                visual_evidence_mode=visual_evidence_mode,
                require_observed_comparison=require_observed_comparison,
            ))
        except ResearchToScriptError as err:
            click.echo(f"Research-to-script failed: {err}", err=True)
            raise click.Abort() from err
        serialized = result.model_dump_json(indent=2)
        if output:
            Path(output).write_text(serialized, encoding="utf-8")
            click.echo(f"Research-to-script draft saved: {output}")
        else:
            click.echo(serialized)
        return

    # Load configuration
    if config:
        cfg = MSFConfig.from_yaml(config)
    else:
        default_yml = Path("config/default.yml")
        if default_yml.exists():
            cfg = MSFConfig.from_yaml(default_yml)
        else:
            cfg = MSFConfig()

    orchestrator = PipelineOrchestrator(cfg)

    # Setup progress bar
    total_stages = len(STAGES)
    current_stage_idx = [0]

    with click.progressbar(
        length=total_stages,
        label="Pipeline Progress",
        item_show_func=lambda item: f"Stage: {item}" if item else "",
    ) as bar:

        def progress_callback(stage_name: str) -> None:
            # Match stage index
            for idx, (stage_key, label) in enumerate(STAGES):
                if stage_key == stage_name:
                    diff = (idx + 1) - current_stage_idx[0]
                    if diff > 0:
                        bar.update(diff, label)
                        current_stage_idx[0] = idx + 1
                    break

        try:
            state = orchestrator.run(
                topic=topic,
                duration=duration,
                style=style,
                output=output,
                progress_callback=progress_callback,
            )
            # Ensure bar fills on completion
            if current_stage_idx[0] < total_stages:
                bar.update(total_stages - current_stage_idx[0], "Completed")

            click.echo("\n✨ Video Generation Complete!")
            click.echo(f"Project ID: {state.project_id}")
            click.echo(f"Final Output: {state.output_path}")

        except Exception as err:
            click.echo(f"\n❌ Pipeline execution failed: {err}", err=True)
            raise click.Abort() from err


if __name__ == "__main__":
    cli()
