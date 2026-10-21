"""Tkinter user interface."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from PIL import Image, ImageOps, ImageTk

from . import APP_NAME
from .analyzer import ImageError, Prop, analyze, check_image, describe_requirement, format_value
from .converter import (SAVE_FORMATS, ConversionError, convert_image, default_save_format,
                        format_for_extension, is_compatible)
from .criteria import BYTES_PER_MB, IMAGE_TYPES, Criteria, CriteriaError, load_criteria, save_criteria
from .session import Session

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:  # pragma: no cover - the program still works with the Open button
    TkinterDnD = None
    DND_FILES = None

RED = "#c62828"
GREEN = "#2e7d32"
PREVIEW_SIZE = 280
IMAGE_FILETYPES = [("Images", "*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.gif *.webp"), ("All files", "*.*")]
JSON_FILETYPES = [("JSON files", "*.json"), ("All files", "*.*")]


def create_root() -> tk.Tk:
    """Create the main window, with drag-and-drop support when tkinterdnd2 is available."""
    if TkinterDnD is not None:
        try:
            return TkinterDnD.Tk()
        except (tk.TclError, RuntimeError):
            pass
    return tk.Tk()


def same_criteria(a: Criteria, b: Criteria) -> bool:
    da, db = a.to_dict(), b.to_dict()
    da["allowed_types"] = sorted(da["allowed_types"])
    db["allowed_types"] = sorted(db["allowed_types"])
    return da == db


class ValueDialog(simpledialog.Dialog):
    """Asks for a new target value of one property and validates it."""

    def __init__(self, parent, session: Session, prop: Prop):
        self.session = session
        self.prop = prop
        self.value_var = tk.StringVar(parent)
        self.keep_aspect = tk.BooleanVar(parent, value=True)
        self.result = None
        super().__init__(parent, title=f"Set {prop.label.lower()}")

    def body(self, master):
        prop, session = self.prop, self.session
        current = format_value(prop, session.info.value(prop))
        ttk.Label(master, text=f"Current value: {current}").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(master, text=f"Requirement: {describe_requirement(prop, session.criteria)}").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        unit = {Prop.FILE_SIZE: "MB", Prop.WIDTH: "px", Prop.HEIGHT: "px", Prop.RESOLUTION: "DPI"}.get(prop, "")
        ttk.Label(master, text="New value:").grid(row=2, column=0, sticky="w")
        suggestion = session.suggestion(prop)
        if prop is Prop.IMAGE_TYPE:
            self.value_var.set(suggestion)
            widget = ttk.Combobox(master, textvariable=self.value_var, state="readonly",
                                  values=session.criteria.allowed_types, width=14)
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
            ttk.Checkbutton(master, text="Keep aspect ratio (also changes the other dimension)",
                            variable=self.keep_aspect).grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        if prop is Prop.FILE_SIZE:
            ttk.Label(master, text="The converter lowers the quality or the size to stay under this limit.",
                      foreground="gray").grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        return widget

    def validate(self):
        try:
            self._value = self.session.parse_value(self.prop, self.value_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc), parent=self)
            return False
        return True

    def apply(self):
        self.result = (self._value, self.keep_aspect.get())


class CriteriaPanel(ttk.LabelFrame):
    FIELDS = [
        ("max_file_size_mb", "Maximum file size (MB)"),
        ("min_width", "Minimum width (px)"),
        ("min_height", "Minimum height (px)"),
        ("max_width", "Maximum width (px)"),
        ("max_height", "Maximum height (px)"),
        ("min_dpi", "Minimum resolution (DPI)"),
    ]

    def __init__(self, parent, app: App):
        super().__init__(parent, text="Criteria", padding=8)
        self.app = app
        self.vars = {name: tk.StringVar(self) for name, _ in self.FIELDS}
        self.type_vars = {name: tk.BooleanVar(self) for name in IMAGE_TYPES}

        for row, (name, label) in enumerate(self.FIELDS):
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=2)
            ttk.Entry(self, textvariable=self.vars[name], width=10).grid(row=row, column=1, sticky="e", pady=2)

        types = ttk.LabelFrame(self, text="Allowed image types", padding=4)
        types.grid(row=len(self.FIELDS), column=0, columnspan=2, sticky="ew", pady=(8, 4))
        for i, name in enumerate(IMAGE_TYPES):
            ttk.Checkbutton(types, text=name, variable=self.type_vars[name]).grid(
                row=i // 2, column=i % 2, sticky="w", padx=(0, 12))

        buttons = ttk.Frame(self)
        buttons.grid(row=len(self.FIELDS) + 1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(buttons, text="Apply", command=app.apply_criteria).pack(fill="x")
        ttk.Button(buttons, text="Load criteria...", command=app.load_criteria_file).pack(fill="x", pady=(4, 0))
        ttk.Button(buttons, text="Save criteria as...", command=app.save_criteria_file).pack(fill="x", pady=(4, 0))

        self.source_label = ttk.Label(self, text="", foreground="gray", wraplength=220)
        self.source_label.grid(row=len(self.FIELDS) + 2, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def show(self, criteria: Criteria, source: str) -> None:
        for name, _ in self.FIELDS:
            self.vars[name].set(f"{getattr(criteria, name):g}")
        for name, var in self.type_vars.items():
            var.set(name in criteria.allowed_types)
        self.source_label.config(text=source)

    def read(self) -> Criteria:
        """Build criteria from the input fields; raise CriteriaError if they are invalid."""
        data = {}
        for name, label in self.FIELDS:
            text = self.vars[name].get().strip().replace(",", ".")
            try:
                number = float(text)
            except ValueError:
                raise CriteriaError(f"{label}: '{text}' is not a number.") from None
            if name not in ("max_file_size_mb", "min_dpi"):
                if number != int(number):
                    raise CriteriaError(f"{label} must be a whole number.")
                number = int(number)
            data[name] = number
        data["allowed_types"] = [name for name, var in self.type_vars.items() if var.get()]
        return Criteria.from_dict(data)


class App:
    def __init__(self, root: tk.Tk, criteria: Criteria, config_path: Path):
        self.root = root
        self.criteria = criteria
        self.config_path = Path(config_path)
        self.session: Session | None = None
        self._preview = None

        root.title(APP_NAME)
        root.minsize(820, 560)
        main = ttk.Frame(root, padding=10)
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        self.criteria_panel = CriteriaPanel(main, self)
        self.criteria_panel.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        self.criteria_panel.show(criteria, self._source_text())

        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        self.drop_zone = tk.Label(right, text=self._drop_text(), relief="groove", bd=2, bg="#f4f4f4",
                                  height=14, compound="top", cursor="hand2")
        self.drop_zone.grid(row=0, column=0, sticky="ew")
        self.drop_zone.bind("<Button-1>", lambda _e: self.choose_image())
        if DND_FILES is not None and hasattr(root, "drop_target_register"):
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self._on_drop)

        self.info_label = ttk.Label(right, text="", justify="left", wraplength=560)
        self.info_label.grid(row=1, column=0, sticky="ew", pady=(8, 8))

        self.result_frame = ttk.Frame(right)
        self.result_frame.grid(row=2, column=0, sticky="nsew")
        self.prop_buttons: dict[Prop, tk.Button] = {}
        self.ok_button: tk.Button | None = None
        self.convert_button: ttk.Button | None = None

    # ----- dialogs (separate methods so tests can replace them) -----

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
            parent=self.root, title="Save converted image", initialdir=str(source.parent),
            initialfile=f"{source.stem}_converted{ext}", defaultextension=ext,
            filetypes=filetypes, typevariable=type_var)
        chosen = next((f for f in order if SAVE_FORMATS[f].description == type_var.get()), default_format)
        return path, chosen

    # ----- image handling -----

    def _drop_text(self) -> str:
        if DND_FILES is not None and hasattr(self.root, "drop_target_register"):
            return "Drag and drop an image here\n(or click to browse)"
        return "Click here to open an image"

    def _source_text(self) -> str:
        if self.config_path.exists():
            return f"Criteria file: {self.config_path}"
        return f"Default criteria (save file: {self.config_path.name})"

    def _on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        if files:
            self.open_image(files[0])
        return event.action

    def choose_image(self) -> None:
        path = filedialog.askopenfilename(parent=self.root, title="Open image", filetypes=IMAGE_FILETYPES)
        if path:
            self.open_image(path)

    def open_image(self, path) -> bool:
        try:
            info = analyze(path)
        except ImageError as exc:
            self.show_error("Cannot open image", str(exc))
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
        dpi = f"{info.dpi[0]:g} x {info.dpi[1]:g} DPI" if info.dpi else "not set"
        self.info_label.config(text=(
            f"File: {info.path}\n"
            f"Format: {info.format or 'unknown'}    Mode: {info.mode} ({info.image_type})\n"
            f"Size: {info.width} x {info.height} px    Resolution: {dpi}    "
            f"File size: {format_value(Prop.FILE_SIZE, info.file_size)}"))

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
                self.result_frame, text="OK - the image meets all criteria (click to exit)",
                bg=GREEN, fg="white", activebackground=GREEN, activeforeground="white",
                font=("Segoe UI", 12, "bold"), command=self.root.destroy, pady=10)
            self.ok_button.pack(fill="x")
            return

        ttk.Label(self.result_frame, text="The image does not meet these criteria. "
                                          "Click a red button to set a valid value:").pack(anchor="w", pady=(0, 4))
        for prop in session.flagged:
            button = tk.Button(self.result_frame, anchor="w", padx=8, pady=4,
                               command=lambda p=prop: self.on_prop_button(p))
            button.pack(fill="x", pady=2)
            self.prop_buttons[prop] = button
        self.convert_button = ttk.Button(self.result_frame, text="Convert and save...", command=self.convert_and_save)
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
            self.show_error("Invalid value", str(exc))
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
            allowed = ", ".join(f for f in SAVE_FORMATS if is_compatible(f, settings.image_type))
            self.show_error("Unsuitable format",
                            f"The {fmt} format cannot store '{settings.image_type}' images.\n"
                            f"Please choose one of: {allowed}.")
            default_format = default_save_format(None, settings.image_type)

        try:
            result = convert_image(session.info.path, settings, path, fmt)
            new_info = analyze(result.path)
        except (ConversionError, ImageError) as exc:
            self.show_error("Conversion failed", str(exc))
            return

        failures = check_image(new_info, self.criteria)
        quality = f", JPEG quality {result.quality}" if result.quality else ""
        summary = (f"Saved: {result.path}\n{result.width} x {result.height} px, "
                   f"{format_value(Prop.FILE_SIZE, result.file_size)}{quality}")
        if failures:
            self.show_error("Converted image still fails",
                            summary + "\n\nNot met: " + ", ".join(p.label for p in failures))
        else:
            self.show_info("Conversion done", summary + "\n\nThe converted image meets all criteria.")
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
            self.show_error("Invalid criteria", str(exc))
            return
        if same_criteria(criteria, self.criteria):
            return
        self._set_criteria(criteria)
        if self.ask_yes_no("Save criteria", "The criteria have changed. Do you want to save them to a file?"):
            self.save_criteria_file()

    def ask_criteria_save_path(self) -> str:
        return filedialog.asksaveasfilename(
            parent=self.root, title="Save criteria", initialdir=str(self.config_path.parent),
            initialfile=self.config_path.name, defaultextension=".json", filetypes=JSON_FILETYPES)

    def ask_criteria_open_path(self) -> str:
        return filedialog.askopenfilename(parent=self.root, title="Load criteria",
                                          initialdir=str(self.config_path.parent), filetypes=JSON_FILETYPES)

    def save_criteria_file(self) -> None:
        try:
            criteria = self.criteria_panel.read()
        except CriteriaError as exc:
            self.show_error("Invalid criteria", str(exc))
            return
        path = self.ask_criteria_save_path()
        if not path:
            return
        try:
            save_criteria(criteria, path)
        except (OSError, CriteriaError) as exc:
            self.show_error("Cannot save criteria", str(exc))
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
            self.show_error("Cannot load criteria", str(exc))
            return
        self.config_path = Path(path)
        self._set_criteria(criteria)
