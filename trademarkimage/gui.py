"""Tkinter user interface."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from PIL import Image, ImageOps, ImageTk

from . import i18n
from .about import SOURCE_URL, about_lines
from .analyzer import ImageError, Prop, analyze, check_image, describe_requirement, format_value
from .converter import (SAVE_FORMATS, ConversionError, compatible_formats, convert_image, default_save_format,
                        format_for_extension, is_compatible)
from .criteria import (BYTES_PER_MB, IMAGE_TYPES, Criteria, CriteriaError, load_criteria, save_criteria,
                       type_label)
from .i18n import tr
from .session import CHOICE_PROPS, Session

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:  # pragma: no cover - the program still works with the Open button
    TkinterDnD = None
    DND_FILES = None

RED = "#c62828"
GREEN = "#2e7d32"
PREVIEW_SIZE = 280
IMAGE_PATTERNS = "*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.gif *.webp"


def create_root() -> tk.Tk:
    """Create the main window, with drag-and-drop support when tkinterdnd2 is available."""
    if TkinterDnD is not None:
        try:
            return TkinterDnD.Tk()
        except (tk.TclError, RuntimeError):
            pass
    return tk.Tk()


def show_message(kind: str, title: str, text: str) -> None:
    """Show a message box without a main window (kind: 'info' or 'error')."""
    root = tk.Tk()
    root.withdraw()
    show = messagebox.showerror if kind == "error" else messagebox.showinfo
    show(title, text, parent=root)
    root.destroy()


def show_text_window(title: str, text: str) -> None:
    """Show a longer, preformatted text (the command line help) in a fixed-width font."""
    root = tk.Tk()
    root.title(title)
    lines = text.splitlines() or [""]
    view = tk.Text(root, font=("Consolas", 10), wrap="none", padx=12, pady=10, relief="flat",
                   width=max(len(line) for line in lines) + 2, height=len(lines) + 1)
    view.insert("1.0", text)
    view.config(state="disabled")
    view.pack(fill="both", expand=True)
    close = ttk.Button(root, text=tr("button.ok"), command=root.destroy)
    close.pack(pady=(0, 10))
    close.focus_set()
    for key in ("<Return>", "<Escape>"):
        root.bind(key, lambda _e: root.destroy())
    root.mainloop()


class AboutDialog(tk.Toplevel):
    """The version window: name and version, copyright and a clickable source link."""

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.title(tr("cli.version.title"))
        self.resizable(False, False)
        if parent.winfo_viewable():
            self.transient(parent)
        name, copyright_line, _ = about_lines()
        body = ttk.Frame(self, padding=(20, 16, 20, 8))
        body.pack(fill="both")
        ttk.Label(body, text=name, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(body, text=copyright_line).pack(anchor="w", pady=(8, 0))
        source = ttk.Frame(body)
        source.pack(anchor="w", pady=(2, 0))
        ttk.Label(source, text=tr("about.source")).pack(side="left")
        self.link = tk.Label(source, text=SOURCE_URL, fg="#0645ad", cursor="hand2", font=("Segoe UI", 9, "underline"))
        self.link.pack(side="left", padx=(4, 0))
        self.link.bind("<Button-1>", lambda _e: webbrowser.open(SOURCE_URL))
        ok = ttk.Button(self, text=tr("button.ok"), command=self.destroy)
        ok.pack(pady=(4, 12))
        ok.focus_set()
        for key in ("<Return>", "<Escape>"):
            self.bind(key, lambda _e: self.destroy())

    def show(self) -> None:
        """Wait until the window is closed."""
        self.grab_set()
        self.wait_window()


def show_about_window() -> None:
    """The version window without a main window (--version in the exe, which has no console)."""
    root = tk.Tk()
    root.withdraw()
    AboutDialog(root).show()
    root.destroy()


def same_criteria(a: Criteria, b: Criteria) -> bool:
    da, db = a.to_dict(), b.to_dict()
    da["allowed_types"] = sorted(da["allowed_types"])
    db["allowed_types"] = sorted(db["allowed_types"])
    return da == db


def json_filetypes():
    return [(tr("filetype.json"), "*.json"), (tr("filetype.all"), "*.*")]


class ValueDialog(simpledialog.Dialog):
    """Asks for a new target value of one property and validates it."""

    def __init__(self, parent, session: Session, prop: Prop):
        self.session = session
        self.prop = prop
        self.value_var = tk.StringVar(parent)
        self.keep_aspect = tk.BooleanVar(parent, value=True)
        self.result = None
        super().__init__(parent, title=tr("dialog.value.title", label=prop.label))

    def body(self, master):
        prop, session = self.prop, self.session
        current = format_value(prop, session.info.value(prop))
        ttk.Label(master, text=tr("dialog.value.current", value=current)).grid(
            row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(master, text=tr("dialog.value.requirement",
                                  requirement=describe_requirement(prop, session.criteria))).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(0, 8))

        unit = {Prop.FILE_SIZE: "MB", Prop.WIDTH: "px", Prop.HEIGHT: "px", Prop.RESOLUTION: "DPI"}.get(prop, "")
        ttk.Label(master, text=tr("dialog.value.new")).grid(row=2, column=0, sticky="w")
        suggestion = session.suggestion(prop)
        if prop in CHOICE_PROPS:
            # The list shows the localized names; they are mapped back to the ids in validate().
            self.choice_ids = {format_value(prop, c): c for c in session.choices(prop)}
            self.value_var.set(format_value(prop, suggestion))
            widget = ttk.Combobox(master, textvariable=self.value_var, state="readonly",
                                  values=list(self.choice_ids), width=24)
        else:
            if prop is Prop.FILE_SIZE:
                self.value_var.set(f"{suggestion / BYTES_PER_MB:g}")
            else:
                self.value_var.set(str(suggestion))
            widget = ttk.Entry(master, textvariable=self.value_var, width=16)
        widget.grid(row=2, column=1, sticky="w")
        if unit:
            ttk.Label(master, text=unit).grid(row=2, column=2, sticky="w", padx=(4, 0))
        if prop in (Prop.WIDTH, Prop.HEIGHT):
            ttk.Checkbutton(master, text=tr("dialog.value.keep_aspect"), variable=self.keep_aspect).grid(
                row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        hint = {Prop.FILE_SIZE: "dialog.value.file_size_hint",
                Prop.JPEG_ENCODING: "dialog.value.jpeg_hint"}.get(prop)
        if hint:
            ttk.Label(master, text=tr(hint), foreground="gray").grid(
                row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        return widget

    def buttonbox(self):
        box = ttk.Frame(self)
        ttk.Button(box, text=tr("button.ok"), width=10, command=self.ok, default="active").pack(
            side="left", padx=5, pady=5)
        ttk.Button(box, text=tr("button.cancel"), width=10, command=self.cancel).pack(side="left", padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

    def validate(self):
        text = self.value_var.get()
        if self.prop in CHOICE_PROPS:
            text = self.choice_ids.get(text, text)
        try:
            self._value = self.session.parse_value(self.prop, text)
        except ValueError as exc:
            messagebox.showerror(tr("dialog.value.invalid_title"), str(exc), parent=self)
            return False
        return True

    def apply(self):
        self.result = (self._value, self.keep_aspect.get())


class CriteriaPanel(ttk.LabelFrame):
    FIELDS = ["max_file_size_mb", "min_width", "min_height", "max_width", "max_height", "min_dpi", "max_dpi"]
    DECIMAL_FIELDS = ("max_file_size_mb", "min_dpi", "max_dpi")

    def __init__(self, parent, app: App):
        super().__init__(parent, text=tr("criteria.title"), padding=8)
        self.app = app
        self.vars = {name: tk.StringVar(self) for name in self.FIELDS}
        self.type_vars = {name: tk.BooleanVar(self) for name in IMAGE_TYPES}
        self.progressive_var = tk.BooleanVar(self)

        for row, name in enumerate(self.FIELDS):
            ttk.Label(self, text=tr(f"criteria.field.{name}")).grid(row=row, column=0, sticky="w", pady=2)
            ttk.Entry(self, textvariable=self.vars[name], width=10).grid(row=row, column=1, sticky="e", pady=2)

        types = ttk.LabelFrame(self, text=tr("criteria.types_title"), padding=4)
        types.grid(row=len(self.FIELDS), column=0, columnspan=2, sticky="ew", pady=(8, 4))
        for i, name in enumerate(IMAGE_TYPES):
            ttk.Checkbutton(types, text=type_label(name), variable=self.type_vars[name]).grid(
                row=i, column=0, sticky="w")
        ttk.Checkbutton(self, text=tr("criteria.allow_progressive"), variable=self.progressive_var).grid(
            row=len(self.FIELDS) + 1, column=0, columnspan=2, sticky="w")

        buttons = ttk.Frame(self)
        buttons.grid(row=len(self.FIELDS) + 2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(buttons, text=tr("criteria.apply"), command=app.apply_criteria).pack(fill="x")
        ttk.Button(buttons, text=tr("criteria.load"), command=app.load_criteria_file).pack(fill="x", pady=(4, 0))
        ttk.Button(buttons, text=tr("criteria.save"), command=app.save_criteria_file).pack(fill="x", pady=(4, 0))

        self.source_label = ttk.Label(self, text="", foreground="gray", wraplength=240)
        self.source_label.grid(row=len(self.FIELDS) + 3, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def show(self, criteria: Criteria, source: str) -> None:
        for name in self.FIELDS:
            self.vars[name].set(f"{getattr(criteria, name):g}")
        for name, var in self.type_vars.items():
            var.set(name in criteria.allowed_types)
        self.progressive_var.set(criteria.allow_progressive_jpeg)
        self.source_label.config(text=source)

    def read(self) -> Criteria:
        """Build criteria from the input fields; raise CriteriaError if they are invalid."""
        data = {}
        for name in self.FIELDS:
            label = tr(f"criteria.field.{name}")
            text = self.vars[name].get().strip().replace(",", ".")
            try:
                number = float(text)
            except ValueError:
                raise CriteriaError(tr("criteria.input.not_number", label=label, text=text)) from None
            if name not in self.DECIMAL_FIELDS:
                if number != int(number):
                    raise CriteriaError(tr("criteria.input.not_whole", label=label))
                number = int(number)
            data[name] = number
        data["allowed_types"] = [name for name, var in self.type_vars.items() if var.get()]
        data["allow_progressive_jpeg"] = self.progressive_var.get()
        return Criteria.from_dict(data)


class App:
    def __init__(self, root: tk.Tk, criteria: Criteria, config_path: Path):
        self.root = root
        self.criteria = criteria
        self.config_path = Path(config_path)
        self.session: Session | None = None
        self._preview = None
        self.main: ttk.Frame | None = None
        root.minsize(860, 640)
        self.build_ui()

    def build_ui(self) -> None:
        """Create all widgets with the texts of the current language."""
        if self.main is not None:
            self.main.destroy()
        root = self.root
        root.title(tr("app.title"))
        self.main = main = ttk.Frame(root, padding=10)
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)

        self.about_button = ttk.Button(main, text=tr("about.button"), command=self.show_about)
        self.about_button.grid(row=0, column=0, sticky="w", pady=(0, 6))
        language_bar = ttk.Frame(main)
        language_bar.grid(row=0, column=1, sticky="e", pady=(0, 6))
        ttk.Label(language_bar, text=tr("language.label")).pack(side="left", padx=(0, 4))
        self.language_names = i18n.languages()
        self.language_var = tk.StringVar(main, value=self.language_names.get(i18n.get_language(), ""))
        self.language_box = ttk.Combobox(language_bar, textvariable=self.language_var, state="readonly",
                                         values=list(self.language_names.values()), width=14)
        self.language_box.pack(side="left")
        self.language_box.bind("<<ComboboxSelected>>", self._on_language_selected)

        self.criteria_panel = CriteriaPanel(main, self)
        self.criteria_panel.grid(row=1, column=0, sticky="ns", padx=(0, 10))
        self.criteria_panel.show(self.criteria, self._source_text())

        right = ttk.Frame(main)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        self.drop_zone = tk.Label(right, text=self._drop_text(), relief="groove", bd=2, bg="#f4f4f4",
                                  height=14, compound="top", cursor="hand2")
        self.drop_zone.grid(row=0, column=0, sticky="ew")
        self.drop_zone.bind("<Button-1>", lambda _e: self.choose_image())
        if self._dnd_available():
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self._on_drop)

        self.info_label = ttk.Label(right, text="", justify="left", wraplength=560)
        self.info_label.grid(row=1, column=0, sticky="ew", pady=(8, 8))

        self.result_frame = ttk.Frame(right)
        self.result_frame.grid(row=2, column=0, sticky="nsew")
        self.prop_buttons: dict[Prop, tk.Button] = {}
        self.ok_button: tk.Button | None = None
        self.convert_button: ttk.Button | None = None

        if self.session is not None:
            self._show_preview(self.session.info.path)
            self._show_info()
            self.render_result()

    # ----- language -----

    def _on_language_selected(self, _event=None) -> None:
        name = self.language_var.get()
        code = next((c for c, n in self.language_names.items() if n == name), None)
        if code:
            self.set_language(code)

    def set_language(self, code: str) -> None:
        """Switch the user interface language; the current image and target values are kept."""
        if code == i18n.get_language():
            return
        i18n.set_language(code)
        self.build_ui()

    # ----- dialogs (separate methods so tests can replace them) -----

    def show_about(self) -> None:
        AboutDialog(self.root).show()

    def ask_yes_no(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message, parent=self.root)

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message, parent=self.root)

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message, parent=self.root)

    def ask_value(self, prop: Prop):
        return ValueDialog(self.root, self.session, prop).result

    def ask_save_path(self, default_format: str) -> tuple[str, str | None]:
        """Ask for the output file. Returns (path, format chosen in the file type list)."""
        order = [default_format] + [f for f in SAVE_FORMATS if f != default_format]
        filetypes = [(SAVE_FORMATS[f].description, " ".join("*" + e for e in SAVE_FORMATS[f].extensions))
                     for f in order]
        type_var = tk.StringVar(self.root, value=filetypes[0][0])
        source = self.session.info.path
        ext = SAVE_FORMATS[default_format].extensions[0]
        path = filedialog.asksaveasfilename(
            parent=self.root, title=tr("save.title"), initialdir=str(source.parent),
            initialfile=f"{source.stem}{tr('save.suffix')}{ext}", defaultextension=ext,
            filetypes=filetypes, typevariable=type_var)
        chosen = next((f for f in order if SAVE_FORMATS[f].description == type_var.get()), default_format)
        return path, chosen

    # ----- image handling -----

    def _dnd_available(self) -> bool:
        return DND_FILES is not None and hasattr(self.root, "drop_target_register")

    def _drop_text(self) -> str:
        return tr("drop.dnd") if self._dnd_available() else tr("drop.click")

    def _source_text(self) -> str:
        if self.config_path.exists():
            return tr("criteria.source_file", path=self.config_path)
        return tr("criteria.source_default", name=self.config_path.name)

    def _on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        if files:
            self.open_image(files[0])
        return event.action

    def choose_image(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root, title=tr("dialog.open_image.title"),
            filetypes=[(tr("filetype.images"), IMAGE_PATTERNS), (tr("filetype.all"), "*.*")])
        if path:
            self.open_image(path)

    def open_image(self, path) -> bool:
        try:
            info = analyze(path)
        except ImageError as exc:
            self.show_error(tr("image.error.title"), str(exc))
            return False
        self.session = Session(info, self.criteria)
        self._show_preview(info.path)
        self._show_info()
        self.render_result()
        return True

    def _show_preview(self, path: Path) -> None:
        try:
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img)
                img.thumbnail((PREVIEW_SIZE, PREVIEW_SIZE))
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA" if "A" in img.mode or "transparency" in img.info else "RGB")
                self._preview = ImageTk.PhotoImage(img, master=self.root)
        except OSError:
            self._preview = None
        self.drop_zone.config(image=self._preview or "", text=path.name, height=0 if self._preview else 14)

    def _show_info(self) -> None:
        info = self.session.info
        dpi = tr("info.dpi", x=info.dpi[0], y=info.dpi[1]) if info.dpi else tr("value.not_set")
        fmt = info.format or tr("info.unknown_format")
        if info.jpeg_encoding:
            fmt = f"{fmt} ({format_value(Prop.JPEG_ENCODING, info.jpeg_encoding)})"
        self.info_label.config(text=tr(
            "info.text", path=info.path, format=fmt, mode=info.mode,
            type=type_label(info.image_type), width=info.width, height=info.height, dpi=dpi,
            size=format_value(Prop.FILE_SIZE, info.file_size)))

    def render_result(self) -> None:
        for child in self.result_frame.winfo_children():
            child.destroy()
        self.prop_buttons.clear()
        self.ok_button = None
        self.convert_button = None
        session = self.session
        if session is None:
            return

        if session.passed:
            self.ok_button = tk.Button(
                self.result_frame, text=tr("result.ok"), bg=GREEN, fg="white", activebackground=GREEN,
                activeforeground="white", font=("Segoe UI", 12, "bold"), command=self.root.destroy, pady=10)
            self.ok_button.pack(fill="x")
            return

        ttk.Label(self.result_frame, text=tr("result.failing"), wraplength=560).pack(anchor="w", pady=(0, 4))
        for prop in session.flagged:
            button = tk.Button(self.result_frame, anchor="w", padx=8, pady=4,
                               command=lambda p=prop: self.on_prop_button(p))
            button.pack(fill="x", pady=2)
            self.prop_buttons[prop] = button
        self.convert_button = ttk.Button(self.result_frame, text=tr("result.convert"), command=self.convert_and_save)
        self.convert_button.pack(anchor="e", pady=(8, 0))
        self.update_buttons()

    def update_buttons(self) -> None:
        session = self.session
        for prop in session.flagged:
            if prop not in self.prop_buttons:  # became invalid through another change
                self.render_result()
                return
        for prop, button in self.prop_buttons.items():
            if session.is_valid(prop):
                button.config(bg="white", fg="black", activebackground="#eeeeee", activeforeground="black")
            else:
                button.config(bg=RED, fg="white", activebackground=RED, activeforeground="white")
            button.config(text=session.button_text(prop))
        if self.convert_button is not None:
            self.convert_button.config(state="normal" if session.all_valid else "disabled")

    def on_prop_button(self, prop: Prop) -> None:
        result = self.ask_value(prop)
        if result is None:
            return
        value, keep_aspect = result
        try:
            self.session.set_target(prop, value, keep_aspect)
        except ValueError as exc:
            self.show_error(tr("dialog.value.invalid_title"), str(exc))
            return
        self.update_buttons()
        if self.session.all_valid:
            self.convert_and_save()

    def convert_and_save(self) -> None:
        session = self.session
        settings = session.conversion_settings()
        default_format = default_save_format(session.info.format, settings.image_type)
        while True:
            path, chosen = self.ask_save_path(default_format)
            if not path:
                return
            path = Path(path)
            fmt = format_for_extension(path)
            if fmt is None:
                fmt = chosen or default_format
                path = path.with_name(path.name + SAVE_FORMATS[fmt].extensions[0])
            if is_compatible(fmt, settings.image_type):
                break
            self.show_error(tr("save.unsuitable.title"),
                            tr("save.unsuitable.text", format=fmt, type=type_label(settings.image_type),
                               formats=", ".join(compatible_formats(settings.image_type))))
            default_format = default_save_format(None, settings.image_type)

        try:
            result = convert_image(session.info.path, settings, path, fmt)
            new_info = analyze(result.path)
        except (ConversionError, ImageError) as exc:
            self.show_error(tr("convert.failed.title"), str(exc))
            return

        failures = check_image(new_info, self.criteria)
        quality = tr("convert.quality", quality=result.quality) if result.quality else ""
        summary = tr("convert.summary", path=result.path, width=result.width, height=result.height,
                     size=format_value(Prop.FILE_SIZE, result.file_size), quality=quality)
        if failures:
            self.show_error(tr("convert.still_fails.title"),
                            tr("convert.still_fails.text", summary=summary,
                               props=", ".join(p.label for p in failures)))
        else:
            self.show_info(tr("convert.done.title"), tr("convert.done.text", summary=summary))
        self.open_image(result.path)

    # ----- criteria handling -----

    def _set_criteria(self, criteria: Criteria) -> None:
        self.criteria = criteria
        self.criteria_panel.show(criteria, self._source_text())
        if self.session is not None:
            self.open_image(self.session.info.path)

    def apply_criteria(self) -> None:
        try:
            criteria = self.criteria_panel.read()
        except CriteriaError as exc:
            self.show_error(tr("criteria.invalid.title"), str(exc))
            return
        if same_criteria(criteria, self.criteria):
            return
        self._set_criteria(criteria)
        if self.ask_yes_no(tr("criteria.save_question.title"), tr("criteria.save_question.text")):
            self.save_criteria_file()

    def ask_criteria_save_path(self) -> str:
        return filedialog.asksaveasfilename(
            parent=self.root, title=tr("criteria.save_dialog.title"), initialdir=str(self.config_path.parent),
            initialfile=self.config_path.name, defaultextension=".json", filetypes=json_filetypes())

    def ask_criteria_open_path(self) -> str:
        return filedialog.askopenfilename(parent=self.root, title=tr("criteria.load_dialog.title"),
                                          initialdir=str(self.config_path.parent), filetypes=json_filetypes())

    def save_criteria_file(self) -> None:
        try:
            criteria = self.criteria_panel.read()
        except CriteriaError as exc:
            self.show_error(tr("criteria.invalid.title"), str(exc))
            return
        path = self.ask_criteria_save_path()
        if not path:
            return
        try:
            save_criteria(criteria, path)
        except (OSError, CriteriaError) as exc:
            self.show_error(tr("criteria.save_error.title"), str(exc))
            return
        self.config_path = Path(path)
        self._set_criteria(criteria)

    def load_criteria_file(self) -> None:
        path = self.ask_criteria_open_path()
        if not path:
            return
        try:
            criteria = load_criteria(path)
        except CriteriaError as exc:
            self.show_error(tr("criteria.load_error.title"), str(exc))
            return
        self.config_path = Path(path)
        self._set_criteria(criteria)
