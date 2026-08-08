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
def cli(
    topic: str,
    duration: float,
    style: str,
    output: Optional[str],
    config: Optional[str],
) -> None:
    """Motion Studio Framework (MSF) - Automated Viral Video Generation Pipeline."""
    click.echo(f"🎬 Motion Studio Framework CLI")
    click.echo(f"Topic: {topic}")
    click.echo(f"Target Duration: {duration}s | Style: {style}")

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
