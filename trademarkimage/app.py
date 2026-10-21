"""Command line handling and program start."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import __version__, i18n
from .about import about_text
from .analyzer import ImageError, analyze
from .criteria import DEFAULT_CONFIG_NAME, Criteria, CriteriaError, load_criteria
from .i18n import LOCALS_FILE_NAME, LocalizationError, tr

EXIT_OK = 0
EXIT_USAGE = 2

# Parameters that take a value, with the localization key describing the value.
VALUE_OPTIONS = {"--config": "cli.value.file", "--lang": "cli.value.code", "--locals": "cli.value.file"}
HELP_OPTIONS = ("-h", "--help", "/?")


@dataclass
class Options:
    config: str | None = None
    lang: str | None = None
    locals: str | None = None
    image: str | None = None
    help: bool = False
    version: bool = False
    # Problems found while parsing, as (localization key, values) pairs.
    errors: list[tuple[str, dict]] = field(default_factory=list)


@dataclass
class Startup:
    """The result of processing the command line."""

    action: str  # "run", "help", "version" or "error"
    message: str = ""
    exit_code: int = EXIT_OK
    criteria: Criteria = field(default_factory=Criteria)
    config_path: Path | None = None
    image: str | None = None
    warnings: list[str] = field(default_factory=list)


def program_name() -> str:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).name
    return "python -m trademarkimage"


def parse_args(argv: list[str]) -> Options:
    """Split the command line into options. Errors are collected, not raised, so they can be
    reported in the language selected by --lang even if --lang comes later."""
    options = Options()
    seen = set()
    i = 0
    while i < len(argv):
        arg = argv[i]
        i += 1
        if not arg.strip():  # e.g. an empty "" in a shortcut
            continue
        if arg in HELP_OPTIONS:
            options.help = True
            continue
        if arg == "--version":
            options.version = True
            continue
        name, has_equals, value = arg.partition("=")
        if name in VALUE_OPTIONS:
            if not has_equals:
                value = ""
                if i < len(argv) and not argv[i].startswith("-"):
                    value = argv[i]
                    i += 1
            if not value.strip():
                options.errors.append(("cli.error.missing_value", {"option": name, "expected": VALUE_OPTIONS[name]}))
            elif name in seen:
                options.errors.append(("cli.error.duplicate", {"option": name}))
            else:
                seen.add(name)
                setattr(options, name[2:], value)
            continue
        if arg.startswith("-") and arg != "-":
            options.errors.append(("cli.error.unknown_option", {"option": arg}))
        elif options.image is None:
            options.image = arg
        else:
            options.errors.append(("cli.error.extra_argument", {"argument": arg}))
    return options


def _check_file(option: str, path: Path, errors: list) -> bool:
    if not path.exists():
        errors.append(("cli.error.file_not_found", {"option": option, "path": path}))
        return False
    if not path.is_file():
        errors.append(("cli.error.not_a_file", {"option": option, "path": path}))
        return False
    return True


def _setup_localization(options: Options, cwd: Path, errors: list, warnings: list) -> None:
    language = options.lang.strip().lower() if options.lang else None
    if language in i18n.languages():
        # Messages about the text file itself are already shown in the requested language.
        i18n.set_language(language)
    if options.locals:
        path = Path(options.locals)
        if _check_file("--locals", path, errors):
            try:
                i18n.load_extra(path)
            except LocalizationError as exc:
                errors.append(("cli.error.locals_invalid", {"path": path, "error": exc}))
    elif (cwd / LOCALS_FILE_NAME).is_file():
        try:
            i18n.load_extra(cwd / LOCALS_FILE_NAME)
        except LocalizationError as exc:
            warnings.append(("startup.locals_invalid", {"path": cwd / LOCALS_FILE_NAME, "error": exc}))
    if language:
        try:
            i18n.set_language(language)
        except LocalizationError:
            errors.append(("cli.error.unknown_language",
                           {"code": options.lang, "languages": ", ".join(i18n.languages())}))


def load_startup_criteria(config: str | None, cwd: Path, errors: list, warnings: list) -> tuple[Criteria, Path]:
    """Criteria from --config (problems are errors) or from criterias.json in the startup
    directory (problems are warnings; a missing file means the default criteria)."""
    if config:
        path = Path(config)
        if _check_file("--config", path, errors):
            try:
                return load_criteria(path), path
            except CriteriaError as exc:
                errors.append(("cli.error.config_invalid", {"path": path, "error": exc}))
        return Criteria(), path
    path = cwd / DEFAULT_CONFIG_NAME
    if path.is_file():
        try:
            return load_criteria(path), path
        except CriteriaError as exc:
            warnings.append(("startup.config_invalid", {"error": exc}))
    return Criteria(), path


def help_text() -> str:
    return tr("cli.help", title=tr("app.title"), version=__version__, prog=program_name(),
              config=DEFAULT_CONFIG_NAME, locals=LOCALS_FILE_NAME, languages=", ".join(i18n.languages()),
              default=i18n.default_language())


def process_command_line(argv: list[str], cwd: Path | None = None) -> Startup:
    """Parse and check the command line, set up the localization and load the criteria."""
    cwd = Path(cwd or Path.cwd())
    options = parse_args(argv)
    errors = list(options.errors)
    warnings: list = []
    _setup_localization(options, cwd, errors, warnings)

    if options.help:
        return Startup("help", help_text())
    if options.version:
        return Startup("version", about_text())

    criteria, config_path = load_startup_criteria(options.config, cwd, errors, warnings)
    if options.image:
        try:
            analyze(options.image)
        except ImageError as exc:
            errors.append(("cli.error.image", {"error": exc}))

    if errors:
        lines = [tr(key, **_expand(values)) for key, values in errors]
        lines += ["", tr("cli.error.see_help", prog=program_name())]
        return Startup("error", "\n".join(lines), EXIT_USAGE)
    return Startup("run", criteria=criteria, config_path=config_path, image=options.image,
                   warnings=[tr(key, **values) for key, values in warnings])


def _expand(values: dict) -> dict:
    """Translate values that are localization keys (the expected kind of a missing value)."""
    return {k: tr(v) if k == "expected" else v for k, v in values.items()}


def report(startup: Startup) -> None:
    """Show help, version or error output: on the console if there is one, otherwise in a window
    (the Windows exe is a GUI program without a console)."""
    stream = sys.stderr if startup.action == "error" else sys.stdout
    if stream is not None:
        print(startup.message, file=stream)
        return
    from .gui import show_about_window, show_message, show_text_window

    if startup.action == "help":
        show_text_window(tr("cli.help.title"), startup.message)
    elif startup.action == "version":
        show_about_window()
    else:
        show_message("error", tr("cli.error.title"), startup.message)


def main(argv: list[str] | None = None) -> None:
    startup = process_command_line(sys.argv[1:] if argv is None else argv)
    if startup.action != "run":
        report(startup)
        sys.exit(startup.exit_code)

    from tkinter import messagebox

    from .gui import App, create_root

    root = create_root()
    app = App(root, startup.criteria, startup.config_path)
    if startup.warnings:
        root.after(100, lambda: messagebox.showwarning(tr("startup.title"), "\n\n".join(startup.warnings),
                                                       parent=root))
    if startup.image:
        root.after(200, lambda: app.open_image(startup.image))
    root.mainloop()
