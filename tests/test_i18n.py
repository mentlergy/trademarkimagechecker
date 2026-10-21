import json
import re
import tkinter as tk
from pathlib import Path

import pytest

from trademarkimage import i18n
from trademarkimage.analyzer import Prop, analyze
from trademarkimage.app import setup_localization
from trademarkimage.converter import SAVE_FORMATS
from trademarkimage.criteria import IMAGE_TYPES, Criteria, CriteriaError
from trademarkimage.gui import CriteriaPanel, ValueDialog
from trademarkimage.i18n import BUILTIN_LOCALS, LocalizationError, placeholders, tr
from trademarkimage.session import Session

PACKAGE = Path(i18n.__file__).parent


def builtin_languages():
    return json.loads(BUILTIN_LOCALS.read_text(encoding="utf-8"))["languages"]


def test_hungarian_is_the_default():
    i18n.reset()
    assert i18n.default_language() == "hu"
    assert i18n.get_language() == "hu"
    assert tr("prop.width") == "Szélesség"


def test_available_languages():
    assert i18n.languages() == {"hu": "Magyar", "en": "English"}


@pytest.mark.parametrize("code", ["hu"])
def test_translation_is_complete(code):
    languages = builtin_languages()
    english, other = languages["en"], languages[code]
    assert set(other) == set(english)
    for key, text in english.items():
        assert placeholders(other[key]) == placeholders(text), key


def test_every_used_key_exists():
    english = builtin_languages()["en"]
    used = set()
    for source in PACKAGE.glob("*.py"):
        used.update(re.findall(r"""tr\(\s*["']([a-z_.&A-Z]+)["']""", source.read_text(encoding="utf-8")))
    used.update(f"prop.{p.value}" for p in Prop)
    used.update(f"type.{t}" for t in list(IMAGE_TYPES) + ["other"])
    used.update(f"format.{f}" for f in SAVE_FORMATS)
    used.update(f"criteria.field.{f}" for f in CriteriaPanel.FIELDS)
    assert len(used) > 100
    assert sorted(used - set(english)) == []


def test_fallback_to_english_and_key():
    loc =i18n.Localization("hu", {"hu": {"a": "magyar"}, "en": {"a": "english", "b": "only english"}})
    assert loc.text("hu", "a") == "magyar"
    assert loc.text("hu", "b") == "only english"
    assert loc.text("hu", "missing.key") == "missing.key"


def test_broken_translation_falls_back(tmp_path):
    extra = tmp_path / "locals.json"
    extra.write_text(json.dumps({"languages": {"hu": {"value.px": "{wrong} px"}}}), encoding="utf-8")
    i18n.load_extra(extra)
    i18n.set_language("hu")
    assert tr("value.px", value=5) == "5 px"


def test_unknown_language():
    with pytest.raises(LocalizationError):
        i18n.set_language("xx")


def test_add_language_with_extra_file(tmp_path):
    extra = tmp_path / "locals.json"
    extra.write_text(json.dumps({
        "default_language": "de",
        "languages": {
            "de": {"language_name": "Deutsch", "prop.width": "Breite"},
            "hu": {"prop.height": "Képmagasság"},
        },
    }, ensure_ascii=False), encoding="utf-8")
    i18n.load_extra(extra)
    assert i18n.get_language() == "de"
    assert i18n.languages()["de"] == "Deutsch"
    assert tr("prop.width") == "Breite"
    assert tr("prop.height") == "Height"  # not translated -> English
    i18n.set_language("hu")
    assert tr("prop.height") == "Képmagasság"
    assert tr("prop.width") == "Szélesség"  # built-in text kept


@pytest.mark.parametrize("content", ["{", "[]", '{"languages": {"de": {"a": 1}}}', '{"languages": {}, '
                                                                                  '"default_language": 5}'])
def test_invalid_localization_file(tmp_path, content):
    path = tmp_path / "locals.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(LocalizationError):
        i18n.load_extra(path)


def test_setup_localization(tmp_path):
    i18n.reset()
    assert setup_localization(None, None, cwd=tmp_path) == []
    assert i18n.get_language() == "hu"

    assert setup_localization(None, "en", cwd=tmp_path) == []
    assert i18n.get_language() == "en"

    warnings = setup_localization(None, "xx", cwd=tmp_path)
    assert "xx" in warnings[0] and "hu" in warnings[0]


def test_setup_localization_reads_startup_directory(tmp_path):
    i18n.reset()
    (tmp_path / "locals.json").write_text('{"default_language": "en", "languages": {}}', encoding="utf-8")
    assert setup_localization(None, None, cwd=tmp_path) == []
    assert i18n.get_language() == "en"


def test_setup_localization_reports_bad_file(tmp_path):
    i18n.reset()
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    warnings = setup_localization(str(bad), None)
    assert len(warnings) == 1 and "bad.json" in warnings[0]
    assert i18n.get_language() == "hu"


def test_messages_follow_language(make_image):
    i18n.set_language("hu")
    with pytest.raises(CriteriaError, match="min_width értékének egész számnak"):
        Criteria.from_dict({"min_width": 1.5})
    assert "Legalább egy képtípust" in " ".join(Criteria(allowed_types=[]).errors())
    session = Session(analyze(make_image("wide.jpg", size=(4000, 1000))), Criteria())
    assert session.button_text(Prop.WIDTH) == "Szélesség: 4000 px  (945-2835 px)"
    with pytest.raises(ValueError, match="az elvárt érték 945-2835 px"):
        session.parse_value(Prop.WIDTH, "5000")
    i18n.set_language("en")
    assert session.button_text(Prop.WIDTH) == "Width: 4000 px  (945-2835 px)"


# ----- GUI -----

@pytest.fixture
def app(tmp_path):
    from trademarkimage.gui import App, create_root
    try:
        root = create_root()
    except tk.TclError as exc:
        pytest.skip(f"Tk not available: {exc}")
    root.withdraw()
    i18n.reset()  # Hungarian, like a normal start
    application = App(root, Criteria(), tmp_path / "criterias.json")
    yield application
    try:
        root.destroy()
    except tk.TclError:
        pass


def test_gui_starts_in_hungarian(app):
    assert app.root.title() == "Védjegykép-ellenőrző"
    assert app.drop_zone.cget("text").startswith("Húzzon ide egy képet")
    assert app.criteria_panel.cget("text") == "Feltételek"
    assert app.language_var.get() == "Magyar"


def test_gui_language_switch_keeps_state(app, make_image):
    app.open_image(make_image("bad.png", size=(4000, 2000), dpi=(72, 72)))
    app.session.set_target(Prop.WIDTH, 2000)
    app.update_buttons()
    assert app.prop_buttons[Prop.WIDTH].cget("text") == "Szélesség: 4000 px -> 2000 px"

    app.language_var.set("English")
    app._on_language_selected()

    assert i18n.get_language() == "en"
    assert app.root.title() == "Trademark Image Checker"
    assert app.prop_buttons[Prop.WIDTH].cget("text") == "Width: 4000 px -> 2000 px"
    assert app.prop_buttons[Prop.WIDTH].cget("bg").lower() == "white"
    assert app.prop_buttons[Prop.RESOLUTION].cget("bg").lower() == "#c62828"
    assert app.criteria_panel.cget("text") == "Criteria"
    assert app.drop_zone.cget("text") == "bad.png"


def test_gui_type_dialog_uses_translated_names(app, make_image):
    app.open_image(make_image("alpha.png", size=(1000, 1000), mode="RGBA"))

    def answer():
        dialog = next(w for w in app.root.winfo_children() if isinstance(w, ValueDialog))
        assert "fekete-fehér" in dialog.type_ids
        dialog.value_var.set("fekete-fehér")
        dialog.ok()

    app.root.after(300, answer)
    assert app.ask_value(Prop.IMAGE_TYPE) == ("B&W", True)
