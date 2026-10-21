"""Command line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import APP_NAME, __version__
from .criteria import DEFAULT_CONFIG_NAME, Criteria, CriteriaError, load_criteria


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="trademarkimage", description=APP_NAME)
    parser.add_argument("--config", metavar="FILE",
                        help=f"criteria JSON file (default: {DEFAULT_CONFIG_NAME} in the current directory)")
    parser.add_argument("image", nargs="?", help="image file to open at start")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def load_startup_criteria(config: str | None, cwd: Path | None = None) -> tuple[Criteria, Path, str | None]:
    """Return (criteria, config file path, warning message or None).

    The config file is used when it exists; otherwise the defaults are used and
    the path is remembered as the default target for saving.
    """
    path = Path(config) if config else Path(cwd or Path.cwd()) / DEFAULT_CONFIG_NAME
    if not path.exists():
        warning = f"Criteria file '{path}' not found, using the default criteria." if config else None
        return Criteria(), path, warning
    try:
        return load_criteria(path), path, None
    except CriteriaError as exc:
        return Criteria(), path, f"{exc}\n\nThe default criteria are used."


def main(argv=None) -> None:
    args = parse_args(argv)
    criteria, config_path, warning = load_startup_criteria(args.config)

    from tkinter import messagebox

    from .gui import App, create_root

    root = create_root()
    app = App(root, criteria, config_path)
    if warning:
        root.after(100, lambda: messagebox.showwarning("Criteria", warning, parent=root))
    if args.image:
        root.after(200, lambda: app.open_image(args.image))
    root.mainloop()
