# Trademark Image Checker

_Technical documentation - design, installation and operation (version 1.2.0)_

## 1. Purpose

Trademark Image Checker is a Windows desktop program that examines a raster image against a configurable set of criteria (file size, pixel dimensions, resolution and image type), shows the result in a GUI, lets the user choose valid target values for the failing properties and converts the image accordingly. Its default criteria correspond to typical trademark office image upload requirements. The user interface is localized (Hungarian by default, English included) and further languages can be added by editing a JSON file.

## 2. Requirements

### 2.1 Running the compiled program

- Windows 10 or Windows 11, 64-bit (x64).
- No Python installation is needed: dist\TrademarkImage.exe is a self-contained single file.
- Write access to the folder of the converted images and, optionally, to the folder of the criteria file.

### 2.2 Running from source

| Component | Version | Purpose |
|---|---|---|
| Python | 3.10 or newer (developed and tested with 3.14.0) | Runtime; must include tkinter (Tk 8.6) |
| Pillow | >= 11.0 (tested 13.0.0) | Image reading, conversion and writing |
| tkinterdnd2 | >= 0.4 (tested 0.6.4) | Drag and drop of files into the Tk window (bundles tkdnd 2.9/2.10) |
| pytest | >= 8.0 (tested 9.1.1) | Automated tests (development only) |
| PyInstaller | >= 6.16 (tested 6.22.3) | Building the Windows executable (development only) |
| python-docx | >= 1.1 (tested 1.2.0) | Regenerating this documentation (development only) |

Runtime dependencies are listed in requirements.txt, development dependencies in requirements-dev.txt.

### 2.3 Installation from source

```powershell
git clone <repository> Trademarkimage
cd Trademarkimage
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

### 2.4 Running

```powershell
.venv\Scripts\python.exe -m trademarkimage [--config FILE] [--lang CODE] [--locals FILE] [IMAGE]
.venv\Scripts\python.exe run_trademarkimage.py [options] [IMAGE]
dist\TrademarkImage.exe [options] [IMAGE]
```

| Argument | Meaning |
|---|---|
| --config FILE | Criteria JSON file. Default: criterias.json in the current (startup) directory. |
| --lang CODE | User interface language, e.g. hu or en (case-insensitive). Default: default_language of locals.json (hu). |
| --locals FILE | Additional localization file merged over the built-in texts. Default: locals.json in the current directory, if it exists. |
| IMAGE | Optional image file opened at start (also works by dropping a file on the exe icon). |
| -h, --help, /? | Shows the description of the parameters in the selected language (e.g. --lang en --help) and exits. |
| --version | Shows the version window (name, version, copyright, source URL) and exits. |

### 2.5 Command line checking and messages

The command line is parsed by app.parse_args (not argparse, so that every message can be localized). Values can be given as '--config FILE' or '--config=FILE', also with spaces around the equals sign ('--config= FILE', '--config =FILE', '--config = FILE'); parameter names are case-insensitive, values are kept as given. app.process_command_line then checks it and returns a Startup object (run, help, version or error):

- Missing value (e.g. --config at the end, or followed by another parameter), a parameter given twice, an unknown parameter or more than one image file are errors.
- --config and --locals must name an existing file that can be loaded as a criteria file / localization file; an incompatible file (e.g. an image, or a localization file given as --config) is an error that includes the reason.
- --lang must be one of the available language codes (including languages from --locals).
- The IMAGE must exist and be a readable image.
- All errors are reported together, in the selected language, followed by a hint to use --help. The program then exits with exit code 2 without opening the window. Help and version exit with code 0.
- Problems with the implicit criterias.json / locals.json of the startup directory are not command line errors: they produce a warning in the window and the defaults are used.

Output: when the program has a console (run from source with python), help and version are printed to standard output and errors to standard error. The Windows exe is a GUI program without a console, so there the help is shown in a window (fixed-width font), the version in the same window as the About button (gui.AboutDialog) and the errors in message boxes.

## 3. Architecture

The program is a Python package (trademarkimage) with a strict separation between the image logic, the workflow model and the user interface. Everything except gui.py can be used and tested without a display.

| Module | Responsibility |
|---|---|
| criteria.py | Criteria dataclass with defaults, validation, JSON load/save (load_criteria, save_criteria), the list of image types and their Pillow modes. |
| analyzer.py | analyze(path) -> ImageInfo (format, file size, displayed width/height, DPI, mode); Prop enum of checked properties; check_value / check_image; value formatting. |
| converter.py | Output formats and their capabilities (SAVE_FORMATS), prepare_image (orientation, transparency, resize, type conversion) and convert_image (encoding with file size limit). |
| session.py | Session: GUI independent state of one examined image - the failing (flagged) properties, the target values chosen by the user, input parsing, suggestions, keep-aspect logic and building ConversionSettings. |
| gui.py | Tkinter UI: App main window (with language selector), CriteriaPanel, ValueDialog; drag and drop via tkinterdnd2. |
| i18n.py | Localization: loads locals.json, merges extra files, keeps the current language, tr(key, \*\*values) returns a translated text with its placeholders filled in. |
| locals.json | All user visible texts of every language (package data, also bundled into the exe). |
| about.py | Program identity: name and version, localized copyright line, source URL; used by the About button and --version. |
| app.py | Command line parsing and checking, help/version/error output, localization set-up and loading of the startup criteria; creates the window. |
| __main__.py, run_trademarkimage.py | Entry points (python -m trademarkimage, PyInstaller). |

### 3.1 Data flow

1. app.main() parses the arguments and loads the criteria file (or the defaults).
2. The user drops or opens an image; App.open_image() calls analyzer.analyze() and creates a Session.
3. If Session.passed is true, a green OK button is shown; pressing it closes the program.
4. Otherwise one red button per flagged property is shown. Pressing it opens a ValueDialog; the input is validated by Session.parse_value() and stored with Session.set_target(). Valid buttons turn white.
5. When every property has a valid target value (Session.all_valid), App.convert_and_save() asks for the output file and format and calls converter.convert_image() with Session.conversion_settings().
6. The written file is analysed again and checked against the criteria; the result is reported and the converted image is loaded into the window (which then shows the green OK button).

### 3.2 Testability of the GUI

All dialogs used by App are wrapped in overridable methods (ask_value, ask_save_path, ask_yes_no, show_error, show_info, ask_criteria_save_path, ask_criteria_open_path). The GUI tests replace them with scripted answers and drive the real Tk widgets (button.invoke()).

## 4. Criteria and the criteria file

| JSON key | Default | Meaning |
|---|---|---|
| max_file_size_mb | 2.0 | Maximum file size in MB (1 MB = 1 048 576 bytes). |
| min_width | 945 | Minimum width in pixels. |
| min_height | 945 | Minimum height in pixels. |
| max_width | 2835 | Maximum width in pixels. |
| max_height | 2010 | Maximum height in pixels. |
| min_dpi | 96.0 | Minimum resolution in DPI (the smaller of the horizontal and vertical value is used). |
| max_dpi | 600.0 | Maximum resolution in DPI (the larger of the horizontal and vertical value is used). |
| allowed_types | ["RGB", "greyscale", "B&W", "CMYK"] | Allowed image types. Known types: RGB, RGBA, greyscale, B&W, CMYK, palette. |
| allow_progressive_jpeg | false | If false, progressive JPEG files fail the check (baseline JPEG required). Other formats are not affected. |

Example (criterias.example.json):

```json
{
  "max_file_size_mb": 2.0,
  "min_width": 945,
  "min_height": 945,
  "max_width": 2835,
  "max_height": 2010,
  "min_dpi": 96.0,
  "max_dpi": 600.0,
  "allowed_types": ["RGB", "greyscale", "B&W", "CMYK"],
  "allow_progressive_jpeg": false
}
```

- Missing keys take their default value, so a file may contain only the values that differ.
- Unknown keys, wrong value types, non-integer pixel values, min > max, an empty or unknown type list are rejected with a descriptive error (CriteriaError).
- At start-up the program loads criterias.json from the current directory, or the file given with --config. A missing default file silently means default criteria; a missing --config file or an invalid file produces a warning and the defaults are used.
- When the user applies changed criteria in the GUI, the program asks whether to save them; the save dialog proposes the current criteria file. The 'Load criteria...' button loads an alternative file.
- Changing or loading criteria re-examines the current image.

## 5. Checking rules

| Property | Source | Passes when |
|---|---|---|
| File size | Size of the file on disk | 0 \< size \<= max_file_size_mb x 1 048 576 |
| Width / Height | Pixel size after applying the EXIF orientation tag | min \<= value \<= max |
| Resolution | dpi info (JPEG JFIF/EXIF, PNG pHYs, TIFF, BMP); JFIF dots/cm converted; rounded to 0.1 DPI | smaller of x/y DPI >= min_dpi and larger \<= max_dpi; a missing value fails |
| Image type | Pillow mode mapped to a type name | type is in allowed_types |
| JPEG encoding | JPEG files only: Pillow reports 'progressive' for a progressive (SOF2) file | baseline, or allow_progressive_jpeg is true; other formats always pass |

| Pillow mode(s) | Image type |
|---|---|
| 1 | B&W |
| L, LA, I, I;16, F | greyscale |
| RGB, RGBX, YCbCr | RGB |
| RGBA | RGBA |
| CMYK | CMYK |
| P, PA | palette |
| others (e.g. LAB, HSV) | other - never allowed |

## 6. Workflow model (Session)

- **Flagged properties:** the properties that failed the initial check, plus any property that becomes invalid later (e.g. height after changing the width with 'keep aspect ratio').
- **Target values:** initialised from the image; a button is red while its target is invalid and white after a valid value is entered. Invalid input is rejected and the dialog stays open.
- **Keep aspect ratio:** setting width or height also sets the other dimension from the original ratio.
- **Suggestions:** the dialogs are pre-filled with a valid value; for the dimensions the scale factor closest to 1 that brings both dimensions into range is used, so the default keeps the aspect ratio when possible.
- **File size target:** only limits the output if file size was flagged; otherwise the criteria maximum applies.
- **Automatic conversion:** when the last red button turns white the save dialog opens automatically; if cancelled, the 'Convert and save...' button can be used later.

## 7. Conversion

1. The image is rotated according to the EXIF orientation tag.
2. Transparency is composited onto a white background unless the target type is RGBA.
3. The image is resized with the Lanczos filter in a continuous-tone working mode (L, RGB, RGBA or CMYK).
4. The type is converted: B&W uses a fixed threshold of 128 (no dithering, keeps logos crisp); palette uses an adaptive 256 colour palette; CMYK uses Pillow's plain RGB->CMYK conversion (no ICC colour management).
5. The image is encoded in memory with the chosen DPI (the original x/y values are kept when the resolution was not changed). JPEG is always written as baseline (not progressive) and uses the highest quality between 95 and 40 that fits under the size limit (binary search). If the file is still too big, the image is scaled down proportionally, but never below the minimum width/height; if that is not enough an error is shown.
6. The data is written to the chosen file, then the file is analysed and checked again.

| Format | Extensions | Image types it can store | Notes |
|---|---|---|---|
| JPEG | .jpg .jpeg | RGB, greyscale, CMYK | Lossy; quality adjusted to the size limit |
| PNG | .png | RGB, RGBA, greyscale, B&W, palette | Lossless, optimize=True |
| TIFF | .tif .tiff | all six types | LZW, Group 4 for B&W |
| BMP | .bmp | RGB, greyscale, B&W, palette | Uncompressed - large files |

The default output format is the format of the original file if it is writable and can store the target type; otherwise JPEG, PNG or TIFF (the first that fits). If the user selects an incompatible format, an error lists the suitable formats and the save dialog is shown again. A file name without extension gets the extension of the file type selected in the dialog.

## 8. Localization

Every user visible text (window texts, buttons, dialogs, error messages, command line help) is stored in trademarkimage\locals.json and looked up by a key with i18n.tr(key, \*\*values). Texts may contain {placeholders} (Python str.format syntax, e.g. {value:.2f}); \n in a text starts a new line.

```json
{
  "default_language": "hu",
  "languages": {
    "hu": { "language_name": "Magyar",  "prop.width": "Szélesség", ... },
    "en": { "language_name": "English", "prop.width": "Width", ... }
  }
}
```

- **Default language:** Hungarian (default_language = hu). It can be changed with --lang, by setting default_language in a locals.json in the startup directory, or at run time with the Language (Nyelv) selector in the top right corner of the main window. Switching rebuilds the window; the loaded image and the chosen target values are kept.
- **Loading order:** the built-in file (inside the package / exe) is always loaded; then a locals.json in the startup directory, or the file given with --locals, is merged over it key by key. Such a file may contain only the changed texts or only a new language.
- **Fallback:** a text missing from the selected language is taken from English; an unknown key is shown as the key itself. If an edited text has a wrong placeholder, the English text is used instead, so a translation mistake cannot crash the program.
- **Image type names:** the JSON criteria file and the code use fixed type ids (RGB, greyscale, B&W ...); only their display names (type.\* keys) are translated.
- **Errors:** an invalid file given with --locals or an unknown --lang code is a command line error (see 2.5); an invalid locals.json in the startup directory only produces a warning and the built-in texts are used.

Adding a language: copy the "en" block in locals.json, change its code (e.g. "de"), set language_name and translate the values without changing the keys or placeholders. With the exe, edit the locals.json placed next to TrademarkImage.exe; no rebuild is needed. The test test_translation_is_complete checks that the built-in languages have the same keys and placeholders (add a new built-in language code to its parameter list).

## 9. Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```

162 automated tests (tests directory) cover:

- test_criteria.py - defaults, JSON round trip, partial files, every validation error.
- test_analyzer.py - mode classification, DPI reading and rounding, missing DPI, EXIF orientation, invalid files, boundary values of every criterion.
- test_converter.py - format helpers, resizing, DPI, conversion to every type and format, transparency flattening, JPEG quality reduction, down-scaling of lossless formats, impossible size limits.
- test_session.py - flagged properties, input parsing and validation, keep aspect ratio, suggestions, conversion settings.
- test_gui.py - drag and drop registration, green OK button and exit, red/white buttons, the full fix-and-convert workflow, incompatible format retry, criteria apply/save prompt, loading alternative criteria. These tests need a Windows desktop session (Tk) and are skipped when Tk is unavailable.
- test_i18n.py - Hungarian default, completeness of the translations (same keys and placeholders), every key used in the code exists, English fallback, merging extra files and adding a language, invalid files, translated messages, and in the GUI: Hungarian start-up, live language switch keeping the session, translated image type names in the value dialog.
- test_cli.py - parsing (both value forms, missing values, duplicates, unknown parameters, extra arguments), help in Hungarian and English, version, every kind of invalid --config / --locals / --lang / image value, errors in the selected language, defaults from the startup directory, exit codes, and output to the console or - without a console, as in the exe - to a window.

The tests run in English (an autouse fixture in conftest.py selects it) except the localization tests.

## 10. Building the Windows executable

The build uses a separate, minimal virtual environment (.venv-build) so that development packages are not bundled. Run from the project directory:

```powershell
powershell -ExecutionPolicy Bypass -File build_exe.ps1 [-Python <python.exe>] [-SkipTests]
```

1. Creates .venv-build with the given Python (default: python on PATH) if it does not exist.
2. Installs requirements.txt, pytest and PyInstaller into it.
3. Runs the test suite; the build stops if any test fails.
4. Runs PyInstaller with TrademarkImage.spec: one-file, windowed (no console), tkinterdnd2 data and the native tkdnd library (Windows builds only) collected, locals.json bundled as package data, development packages excluded.
5. Result: dist\TrademarkImage.exe (about 19 MB) plus dist\criterias.example.json and an editable dist\locals.json.

Deployment: copy TrademarkImage.exe (and optionally locals.json) to the target machine. To use custom criteria, place a criterias.json next to the exe (when started by double click the startup directory is the exe folder) or start it with --config. The exe works without locals.json, using its built-in texts. The one-file exe unpacks itself into a temporary folder at start, so the first start takes a few seconds. Unsigned executables may trigger a Windows SmartScreen warning.

## 11. Known limitations

- Only the first frame of multi-frame images (animated GIF, multi-page TIFF) is processed.
- CMYK conversion is not colour managed; embedded ICC profiles are not carried over.
- Metadata (EXIF, ICC, XMP) is not copied to the converted image; only the DPI is written.
- Changing the DPI only changes the stored metadata; pixel dimensions are controlled by width/height.
- Numbers are always shown with a decimal point; input accepts both decimal point and comma.
- The language chosen in the window is not remembered; use --lang or default_language in locals.json to change the start-up language permanently.

## 12. Regenerating the documentation

This technical documentation and the user manuals (English and Hungarian) are generated by docs\make_docs.py from a single source, in Word (.docx) and Markdown (.md) format, so the two formats always have the same content. Edit the texts there, not in the generated files.

```powershell
.venv\Scripts\python.exe docs\make_docs.py
```
