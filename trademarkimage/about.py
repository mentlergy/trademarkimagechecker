"""Program identity shown by the About button and the --version parameter."""

from __future__ import annotations

from . import __version__
from .i18n import tr

SOURCE_URL = "https://github.com/mentlergy/trademarkimagechecker.git"


def about_lines() -> list[str]:
    """Name and version, copyright (the author's name order depends on the language), source URL."""
    return [f"{tr('app.title')} {__version__}", tr("about.copyright"), f"{tr('about.source')} {SOURCE_URL}"]


def about_text() -> str:
    return "\n".join(about_lines())
