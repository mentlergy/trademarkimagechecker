# Trademark Image Checker

Windows GUI tool that checks an image against configurable criteria (file size, pixel size,
resolution, image type) and converts it to meet them.

- Drag and drop an image into the window (or click to browse).
- Green **OK** button: the image meets every criterion; click to exit.
- Red buttons: failing criteria. Click one to enter a valid value; it turns white. When all are
  white, the program asks for a file name and format and saves the converted image.
- Criteria are edited on the left panel, saved to / loaded from JSON. At start-up
  `criterias.json` in the current directory (or the file given with `--config`) is loaded.

## Localization

All texts are in [`trademarkimage/locals.json`](trademarkimage/locals.json) (Hungarian and English).
Hungarian is the default; switch with the language selector in the window, with `--lang en`, or by
changing `default_language`. To add a language, copy the `"en"` block under a new code and translate
the values (keep the keys and `{placeholders}`). A `locals.json` in the startup directory (or the file
given with `--locals`) is merged over the built-in texts, so the exe can be re-translated without
rebuilding; missing texts fall back to English.

## Run from source

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m trademarkimage [--config FILE] [--lang CODE] [--locals FILE] [IMAGE]
.venv\Scripts\python.exe -m trademarkimage --help              # Hungarian help
.venv\Scripts\python.exe -m trademarkimage --lang en --help    # English help
```

Invalid parameters (missing value, missing/incompatible file, unknown language code, bad image) are
reported together and the program exits with code 2. The exe has no console, so help, version and
errors are shown in a window there.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```

## Build the Windows executable

```powershell
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

Produces `dist\TrademarkImage.exe`, which runs on Windows without Python.

## Documentation

| Document | Markdown | Word |
|---|---|---|
| Technical documentation - design, requirements, installation (English) | [md](docs/TrademarkImage_Technical_Documentation_EN.md) | [docx](docs/TrademarkImage_Technical_Documentation_EN.docx) |
| User manual (English) | [md](docs/TrademarkImage_User_Manual_EN.md) | [docx](docs/TrademarkImage_User_Manual_EN.docx) |
| Felhasználói kézikönyv - user manual (Hungarian) | [md](docs/TrademarkImage_Felhasznaloi_kezikonyv_HU.md) | [docx](docs/TrademarkImage_Felhasznaloi_kezikonyv_HU.docx) |

Both formats are generated from the same source; edit `docs/make_docs.py` and regenerate them with
`.venv\Scripts\python.exe docs\make_docs.py`.
