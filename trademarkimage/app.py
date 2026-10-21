"""Command line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__, i18n
from .criteria import DEFAULT_CONFIG_NAME, Criteria, CriteriaError, load_criteria
from .i18n import LOCALS_FILE_NAME, LocalizationError, tr


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="trademarkimage", description=tr("app.title"))
    parser.add_argument("--config", metavar="FILE", help=tr("cli.config_help", name=DEFAULT_CONFIG_NAME))
    parser.add_argument("--lang", metavar="CODE",
                        help=tr("cli.lang_help", languages=", ".join(i18n.languages()),
                                default=i18n.default_language()))
    parser.add_argument("--locals", metavar="FILE", help=tr("cli.locals_help", name=LOCALS_FILE_NAME))
    parser.add_argument("image", nargs="?", help=tr("cli.image_help"))
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def setup_localization(locals_file: str | None, language: str | None, cwd: Path | None = None) -> list[str]:
    """Load the extra localization file and select the language. Returns warning messages.

    The extra file is the one given with --locals, or locals.json in the
    startup directory if it exists. Without --lang the default_language of the
    files is used (built-in: Hungarian).
    """
    problems = []
    path = Path(locals_file) if locals_file else Path(cwd or Path.cwd()) / LOCALS_FILE_NAME
    if locals_file or path.exists():
        try:
            i18n.load_extra(path)
        except LocalizationError as exc:
            problems.append(("startup.locals_invalid", {"path": path, "error": exc}))
    if language:
        try:
            i18n.set_language(language)
        except LocalizationError:
            problems.append(("startup.unknown_language",
                             {"code": language, "languages": ", ".join(i18n.languages())}))
    # Format the messages only now, in the finally selected language.
    return [tr(key, **values) for key, values in problems]


def load_startup_criteria(config: str | None, cwd: Path | None = None) -> tuple[Criteria, Path, str | None]:
    """Return (criteria, config file path, warning message or None).

    The config file is used when it exists; otherwise the defaults are used and
    the path is remembered as the default target for saving.
    """
    path = Path(config) if config else Path(cwd or Path.cwd()) / DEFAULT_CONFIG_NAME
    if not path.exists():
        warning = tr("startup.config_missing", path=path) if config else None
        return Criteria(), path, warning
    try:
        return load_criteria(path), path, None
    except CriteriaError as exc:
        return Criteria(), path, tr("startup.config_invalid", error=exc)


def main(argv=None) -> None:
    args = parse_args(argv)
    warnings = setup_localization(args.locals, args.lang)
    criteria, config_path, warning = load_startup_criteria(args.config)
    if warning:
        warnings.append(warning)

    from tkinter import messagebox

    from .gui import App, create_root

    root = create_root()
    app = App(root, criteria, config_path)
    if warnings:
        root.after(100, lambda: messagebox.showwarning(tr("startup.title"), "\n\n".join(warnings), parent=root))
    if args.image:
        root.after(200, lambda: app.open_image(args.image))
    root.mainloop()
