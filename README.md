# Trademark Image Checker

Windows GUI tool that checks an image against configurable criteria (file size, pixel size,
resolution, image type) and converts it to meet them.

- Drag and drop an image into the window (or click to browse).
- Green **OK** button: the image meets every criterion; click to exit.
- Red buttons: failing criteria. Click one to enter a valid value; it turns white. When all are
  white, the program asks for a file name and format and saves the converted image.
- Criteria are edited on the left panel, saved to / loaded from JSON. At start-up
  `criterias.json` in the current directory (or the file given with `--config`) is loaded.

## Run from source

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m trademarkimage [--config FILE] [IMAGE]
```

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

- `docs/TrademarkImage_Technical_Documentation_EN.docx` - design, requirements, installation (English)
- `docs/TrademarkImage_Felhasznaloi_kezikonyv_HU.docx` - user guide (Hungarian)

Regenerate them with `.venv\Scripts\python.exe docs\make_docs.py`.
