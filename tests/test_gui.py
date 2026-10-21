"""GUI workflow tests. Dialogs are replaced with scripted answers."""

import tkinter as tk

import pytest

from trademarkimage.analyzer import Prop, analyze
from trademarkimage.criteria import Criteria, load_criteria
from trademarkimage.gui import GREEN, RED, App, create_root


@pytest.fixture
def app(tmp_path):
    try:
        root = create_root()
    except tk.TclError as exc:
        pytest.skip(f"Tk not available: {exc}")
    root.withdraw()
    application = App(root, Criteria(), tmp_path / "criterias.json")
    application.messages = []
    application.show_error = lambda title, msg: application.messages.append(("error", title, msg))
    application.show_info = lambda title, msg: application.messages.append(("info", title, msg))
    application.ask_yes_no = lambda title, msg: False
    yield application
    try:
        root.destroy()
    except tk.TclError:
        pass


def test_drag_and_drop_is_available(app):
    assert hasattr(app.root, "drop_target_register")
    assert "Drag and drop" in app.drop_zone.cget("text")


def test_good_image_shows_green_ok_button(app, make_image):
    assert app.open_image(make_image("ok.jpg", size=(1000, 1000)))
    assert app.ok_button is not None
    assert app.ok_button.cget("bg").lower() == GREEN
    assert app.prop_buttons == {}


def test_ok_button_exits(app, make_image):
    app.open_image(make_image("ok.jpg"))
    app.ok_button.invoke()
    with pytest.raises(tk.TclError):
        app.root.winfo_exists()


def test_bad_image_shows_red_buttons(app, make_image):
    app.open_image(make_image("bad.png", size=(4000, 2000), mode="RGBA", dpi=(72, 72)))
    assert app.ok_button is None
    assert list(app.prop_buttons) == [Prop.WIDTH, Prop.RESOLUTION, Prop.IMAGE_TYPE]
    for button in app.prop_buttons.values():
        assert button.cget("bg").lower() == RED
    assert "4000 px" in app.prop_buttons[Prop.WIDTH].cget("text")
    assert str(app.convert_button.cget("state")) == "disabled"


def test_invalid_file_reports_error(app, tmp_path):
    path = tmp_path / "x.png"
    path.write_text("nope")
    assert not app.open_image(path)
    assert app.messages[0][0] == "error"


def test_full_fix_and_convert_workflow(app, make_image, tmp_path):
    app.open_image(make_image("bad.png", size=(4000, 2000), mode="RGBA", dpi=(72, 72)))
    answers = {Prop.WIDTH: (2800, True), Prop.RESOLUTION: (300, False), Prop.IMAGE_TYPE: ("RGB", False)}
    app.ask_value = lambda prop: answers[prop]
    out = tmp_path / "fixed"  # no extension: the chosen file type adds it
    saved = []

    def ask_save_path(default_format):
        saved.append(default_format)
        return str(out), default_format

    app.ask_save_path = ask_save_path

    app.prop_buttons[Prop.WIDTH].invoke()
    assert app.prop_buttons[Prop.WIDTH].cget("bg").lower() == "white"
    assert app.prop_buttons[Prop.RESOLUTION].cget("bg").lower() == RED
    app.prop_buttons[Prop.RESOLUTION].invoke()
    assert saved == []
    app.prop_buttons[Prop.IMAGE_TYPE].invoke()  # last one -> conversion starts automatically

    assert saved == ["PNG"]  # default format follows the original file format
    result = tmp_path / "fixed.png"
    info = analyze(result)
    assert (info.width, info.height, info.resolution, info.image_type) == (2800, 1400, 300, "RGB")
    assert app.messages[-1][0] == "info"
    # The converted image is loaded and passes.
    assert app.session.info.path == result
    assert app.ok_button is not None


def test_cancel_value_dialog_keeps_red(app, make_image):
    app.open_image(make_image("bad.png", size=(4000, 2000)))
    app.ask_value = lambda prop: None
    app.prop_buttons[Prop.WIDTH].invoke()
    assert app.prop_buttons[Prop.WIDTH].cget("bg").lower() == RED


def test_keep_aspect_adds_new_red_button(app, make_image):
    app.open_image(make_image("wide.jpg", size=(4000, 2000)))
    assert list(app.prop_buttons) == [Prop.WIDTH]
    app.ask_value = lambda prop: (1000, True)
    app.prop_buttons[Prop.WIDTH].invoke()
    assert list(app.prop_buttons) == [Prop.WIDTH, Prop.HEIGHT]
    assert app.prop_buttons[Prop.HEIGHT].cget("bg").lower() == RED


def test_incompatible_save_format_asks_again(app, make_image, tmp_path):
    app.open_image(make_image("cmyk.jpg", size=(4000, 2000), mode="CMYK"))
    answers = iter([(str(tmp_path / "out.png"), "PNG"), (str(tmp_path / "out.tif"), "TIFF")])
    app.ask_save_path = lambda fmt: next(answers)
    app.ask_value = lambda prop: (2000, True)
    app.prop_buttons[Prop.WIDTH].invoke()
    assert any("cannot store" in m[2] for m in app.messages if m[0] == "error")
    assert analyze(tmp_path / "out.tif").image_type == "CMYK"


def test_apply_changed_criteria_asks_to_save(app, make_image, tmp_path):
    app.open_image(make_image("ok.jpg", size=(1000, 1000), dpi=(96, 96)))
    asked = []
    app.ask_yes_no = lambda title, msg: asked.append(msg) or True
    target = tmp_path / "saved.json"
    app.ask_criteria_save_path = lambda: str(target)

    app.apply_criteria()  # nothing changed -> no question
    assert asked == []

    app.criteria_panel.vars["min_dpi"].set("300")
    app.apply_criteria()
    assert len(asked) == 1
    assert load_criteria(target).min_dpi == 300
    assert app.config_path == target
    # The image is re-examined with the new criteria.
    assert list(app.prop_buttons) == [Prop.RESOLUTION]


def test_invalid_criteria_input(app):
    app.criteria_panel.vars["min_width"].set("abc")
    app.apply_criteria()
    assert app.messages[-1][1] == "Invalid criteria"
    assert app.criteria == Criteria()


def test_load_alternative_criteria(app, make_image, tmp_path):
    alt = tmp_path / "alt.json"
    alt.write_text('{"allowed_types": ["B&W"]}', encoding="utf-8")
    app.open_image(make_image("ok.jpg"))
    app.ask_criteria_open_path = lambda: str(alt)
    app.load_criteria_file()
    assert app.criteria.allowed_types == ["B&W"]
    assert app.criteria_panel.type_vars["B&W"].get() and not app.criteria_panel.type_vars["RGB"].get()
    assert list(app.prop_buttons) == [Prop.IMAGE_TYPE]
