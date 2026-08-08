"""MSF Colored Console Logging Utilities.

Provides colored stage-prefixed console logging for framework components.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Optional

COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_CYAN = "\033[36m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_MAGENTA = "\033[35m"
COLOR_BLUE = "\033[34m"

STAGE_COLORS: dict[str, str] = {
    "BRIEF": COLOR_CYAN,
    "RESEARCH": COLOR_BLUE,
    "SCRIPT": COLOR_MAGENTA,
    "STORYBOARD": COLOR_CYAN,
    "COMPOSITION": COLOR_GREEN,
    "ASSET": COLOR_YELLOW,
    "VOICE": COLOR_MAGENTA,
    "SUBTITLE": COLOR_BLUE,
    "RENDER": COLOR_CYAN,
    "AUDIO": COLOR_GREEN,
    "QC": COLOR_YELLOW,
    "REVIEW": COLOR_YELLOW,
    "PIPELINE": COLOR_BOLD + COLOR_GREEN,
}

LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: COLOR_CYAN,
    logging.INFO: COLOR_GREEN,
    logging.WARNING: COLOR_YELLOW,
    logging.ERROR: COLOR_RED,
    logging.CRITICAL: COLOR_BOLD + COLOR_RED,
}


class MSFFormatter(logging.Formatter):
    """Custom logging formatter adding colored stage prefixes."""

    def __init__(self, use_color: bool = True):
        super().__init__()
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        stage = getattr(record, "stage", None)
        timestamp = self.formatTime(record, "%H:%M:%S")

        if self.use_color and hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
            level_color = LEVEL_COLORS.get(record.levelno, COLOR_RESET)
            level_str = f"{level_color}{record.levelname:<7}{COLOR_RESET}"

            if stage:
                stage_color = STAGE_COLORS.get(str(stage).upper(), COLOR_CYAN)
                stage_str = f" {stage_color}[{str(stage).upper()}]{COLOR_RESET}"
            else:
                stage_str = ""

            msg = f"{COLOR_CYAN}{timestamp}{COLOR_RESET} | {level_str}{stage_str} {record.getMessage()}"
        else:
            stage_str = f" [{str(stage).upper()}]" if stage else ""
            msg = f"{timestamp} | {record.levelname:<7}{stage_str} {record.getMessage()}"

        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)
        return msg


class StageLogger(logging.LoggerAdapter):
    """LoggerAdapter providing stage-prefix context and convenience logging methods."""

    def __init__(self, logger: logging.Logger, default_stage: Optional[str] = None):
        super().__init__(logger, extra={"stage": default_stage})
        self.default_stage = default_stage

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        extra = kwargs.get("extra", {})
        if "stage" not in extra:
            extra["stage"] = self.default_stage
        kwargs["extra"] = extra
        return msg, kwargs

    def with_stage(self, stage: str) -> StageLogger:
        """Return a new StageLogger adapter bound to the specified stage."""
        return StageLogger(self.logger, default_stage=stage)

    def stage(self, stage_name: str, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an INFO message with an explicit stage prefix override."""
        extra = kwargs.get("extra", {})
        extra["stage"] = stage_name
        kwargs["extra"] = extra
        self.info(msg, *args, **kwargs)


def setup_logger(
    name: str = "msf",
    level: int = logging.INFO,
    default_stage: Optional[str] = None,
    use_color: bool = True,
) -> StageLogger:
    """Initialize and configure a logger instance with MSFFormatter."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(MSFFormatter(use_color=use_color))
        logger.addHandler(handler)

    return StageLogger(logger, default_stage=default_stage)


def get_logger(name: str = "msf", stage: Optional[str] = None) -> StageLogger:
    """Retrieve an existing logger wrapped in StageLogger adapter."""
    logger = logging.getLogger(name)
    return StageLogger(logger, default_stage=stage)
