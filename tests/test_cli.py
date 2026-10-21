"""Command line parsing, checking, help/version output and error messages."""

import json
import sys

import pytest

from trademarkimage import __version__, app, i18n
from trademarkimage.app import EXIT_USAGE, main, parse_args, process_command_line
from trademarkimage.criteria import DEFAULT_CONFIG_NAME, Criteria, save_criteria


@pytest.fixture
def hungarian():
    """Start like the real program: built-in texts, Hungarian default."""
    i18n.reset()


@pytest.fixture
def files(tmp_path, make_image):
    criteria = tmp_path / "strict.json"
    save_criteria(Criteria(min_dpi=300), criteria)
    texts = tmp_path / "texts.json"
    texts.write_text(json.dumps({"languages": {"de": {"language_name": "Deutsch", "app.title": "Markenbild"}}}),
                     encoding="utf-8")
    return {"criteria": criteria, "texts": texts, "image": make_image("logo.png"), "dir": tmp_path}


# ----- parsing -----

def test_parse_all_options():
    options = parse_args(["--config", "c.json", "--lang", "en", "--locals", "l.json", "img.png"])
    assert (options.config, options.lang, options.locals, options.image) == ("c.json", "en", "l.json", "img.png")
    assert options.errors == []


def test_parse_equals_form_and_flags():
    options = parse_args(["--config=c d.json", "--lang=hu", "-h", "--version"])
    assert options.config == "c d.json" and options.lang == "hu"
    assert options.help and options.version
    assert parse_args(["/?"]).help


@pytest.mark.parametrize("argv, option", [
    (["--config"], "--config"),
    (["--config", "--lang", "en"], "--config"),
    (["--locals="], "--locals"),
    (["--lang", ""], "--lang"),
    (["--lang", "-h"], "--lang"),
])
def test_parse_missing_value(argv, option):
    errors = parse_args(argv).errors
    assert ("cli.error.missing_value", {"option": option, "expected": app.VALUE_OPTIONS[option]}) in errors


def test_parse_ignores_blank_arguments():
    options = parse_args(["", "  ", "img.png"])
    assert options.image == "img.png" and options.errors == []


def test_parse_other_errors():
    errors = parse_args(["--lang", "en", "--lang", "hu", "-x", "--configg", "a.png", "b.png"]).errors
    assert [key for key, _ in errors] == ["cli.error.duplicate", "cli.error.unknown_option",
                                          "cli.error.unknown_option", "cli.error.extra_argument"]


# ----- help and version -----

def test_help_is_hungarian_by_default(hungarian, files):
    result = process_command_line(["--help"], cwd=files["dir"])
    assert result.action == "help" and result.exit_code == 0
    assert "Használat:" in result.message and "--config FÁJL" in result.message
    assert __version__ in result.message
    assert "English help:" in result.message


@pytest.mark.parametrize("argv", [["--lang", "en", "--help"], ["-h", "--lang=EN"]])
def test_help_in_english(hungarian, files, argv):
    result = process_command_line(argv, cwd=files["dir"])
    assert result.action == "help"
    assert "Usage:" in result.message and "--config FILE" in result.message
    assert "Magyar súgó:" in result.message


def test_help_wins_over_errors(hungarian, files):
    assert process_command_line(["--config", "--help"], cwd=files["dir"]).action == "help"


def test_version(hungarian, files):
    result = process_command_line(["--version"], cwd=files["dir"])
    assert result.action == "version" and result.exit_code == 0
    assert result.message == (f"Védjegykép-ellenőrző {__version__}\n"
                              "(c) Mentler Gyula SBGK.HU\n"
                              "forrás: https://github.com/mentlergy/trademarkimagechecker.git")
    assert process_command_line(["--version", "--lang", "en"], cwd=files["dir"]).message == (
        f"Trademark Image Checker {__version__}\n"
        "(c) Gyula Mentler SBGK.HU\n"
        "source: https://github.com/mentlergy/trademarkimagechecker.git")


# ----- checking the values -----

def error_of(argv, cwd):
    result = process_command_line(argv, cwd=cwd)
    assert result.action == "error" and result.exit_code == EXIT_USAGE
    return result.message


def test_config_errors(files, tmp_path):
    assert "--config: the file does not exist" in error_of(["--config", "nope.json"], tmp_path)
    assert "--config: not a file" in error_of(["--config", str(tmp_path)], tmp_path)
    # Incompatible files: an image and a localization file.
    assert "is not a valid criteria file" in error_of(["--config", str(files["image"])], tmp_path)
    assert "Unknown key(s)" in error_of(["--config", str(files["texts"])], tmp_path)


def test_locals_errors(files, tmp_path):
    assert "--locals: the file does not exist" in error_of(["--locals", "nope.json"], tmp_path)
    message = error_of(["--locals", str(files["criteria"])], tmp_path)
    assert "is not a valid text file" in message and "\"languages\"" in message
    bad_default = tmp_path / "bad_default.json"
    bad_default.write_text('{"default_language": "xx", "languages": {}}', encoding="utf-8")
    assert "no such language" in error_of(["--locals", str(bad_default)], tmp_path)


def test_language_errors(files, tmp_path):
    message = error_of(["--lang", "xx"], tmp_path)
    assert "--lang: unknown language code 'xx'" in message and "hu, en" in message
    assert "must be followed by a language code" in error_of(["--lang"], tmp_path)


def test_image_errors(files, tmp_path):
    assert "Image file: File not found" in error_of(["missing.png"], tmp_path)
    assert "Not a recognised image" in error_of([str(files["criteria"])], tmp_path)


def test_all_errors_reported_together_with_help_hint(files, tmp_path):
    message = error_of(["--config", "--lang", "xx", "-q", "missing.png"], tmp_path)
    assert message.count("\n") >= 4
    assert message.rstrip().endswith("--help")


def test_errors_follow_the_language(hungarian, files):
    message = error_of(["--config", "nincs.json"], files["dir"])
    assert "--config: a fájl nem létezik" in message and "A paraméterek leírása" in message
    message = error_of(["--lang", "en", "--locals", str(files["criteria"])], files["dir"])
    assert "is not a valid text file" in message and "\"languages\"" in message


# ----- successful start -----

def test_valid_command_line(hungarian, files):
    result = process_command_line(["--config", str(files["criteria"]), "--locals", str(files["texts"]),
                                   "--lang", "de", str(files["image"])], cwd=files["dir"])
    assert result.action == "run" and result.warnings == []
    assert result.criteria.min_dpi == 300 and result.config_path == files["criteria"]
    assert result.image == str(files["image"])
    assert i18n.get_language() == "de" and i18n.tr("app.title") == "Markenbild"


def test_defaults_from_startup_directory(hungarian, tmp_path):
    save_criteria(Criteria(min_dpi=150), tmp_path / DEFAULT_CONFIG_NAME)
    (tmp_path / "locals.json").write_text('{"default_language": "en", "languages": {}}', encoding="utf-8")
    result = process_command_line([], cwd=tmp_path)
    assert result.action == "run" and result.warnings == []
    assert result.criteria.min_dpi == 150 and result.config_path == tmp_path / DEFAULT_CONFIG_NAME
    assert i18n.get_language() == "en"


def test_no_files_in_startup_directory(hungarian, tmp_path):
    result = process_command_line([], cwd=tmp_path)
    assert result.action == "run" and result.criteria == Criteria() and result.warnings == []
    assert result.config_path == tmp_path / DEFAULT_CONFIG_NAME
    assert i18n.get_language() == "hu"


def test_broken_files_in_startup_directory_only_warn(hungarian, tmp_path):
    (tmp_path / DEFAULT_CONFIG_NAME).write_text("{", encoding="utf-8")
    (tmp_path / "locals.json").write_text("[]", encoding="utf-8")
    result = process_command_line([], cwd=tmp_path)
    assert result.action == "run" and len(result.warnings) == 2
    assert result.criteria == Criteria()


# ----- output -----

def test_main_version_prints_and_exits(files, monkeypatch, capsys):
    monkeypatch.chdir(files["dir"])
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    out = capsys.readouterr().out
    assert out.startswith(f"Trademark Image Checker {__version__}\n") and "(c) Gyula Mentler SBGK.HU" in out


def test_main_error_goes_to_stderr(files, monkeypatch, capsys):
    monkeypatch.chdir(files["dir"])
    with pytest.raises(SystemExit) as exit_info:
        main(["--lang", "en", "--config"])
    assert exit_info.value.code == EXIT_USAGE
    captured = capsys.readouterr()
    assert captured.out == "" and "--config parameter must be followed by a file name" in captured.err


@pytest.mark.parametrize("argv, expected", [
    (["--help"], ("text", "Command line parameters")),
    (["--version"], ("about", "")),
    (["--lang", "xx"], ("error", "Command line error")),
])
def test_without_console_output_goes_to_a_window(files, monkeypatch, argv, expected):
    """The exe has no console (sys.stdout and sys.stderr are None); the output is shown in a window."""
    import trademarkimage.gui as gui

    shown = []
    monkeypatch.setattr(gui, "show_text_window", lambda title, text: shown.append(("text", title, text)))
    monkeypatch.setattr(gui, "show_message", lambda kind, title, text: shown.append((kind, title, text)))
    monkeypatch.setattr(gui, "show_about_window", lambda: shown.append(("about", "", "")))
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.chdir(files["dir"])
    with pytest.raises(SystemExit):
        main(["--lang", "en"] + argv if argv[0] != "--lang" else argv)
    assert len(shown) == 1 and shown[0][:2] == expected
