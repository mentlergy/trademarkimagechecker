"""Generates the Word documentation (requires python-docx).

    python docs/make_docs.py
"""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

HERE = Path(__file__).resolve().parent


class Doc:
    def __init__(self, title, subtitle):
        self.doc = Document()
        style = self.doc.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(11)
        heading = self.doc.add_paragraph()
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = heading.add_run(title)
        run.bold = True
        run.font.size = Pt(24)
        run.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
        sub = self.doc.add_paragraph()
        sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub_run = sub.add_run(subtitle)
        sub_run.font.size = Pt(12)
        sub_run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    def h1(self, text):
        self.doc.add_heading(text, level=1)

    def h2(self, text):
        self.doc.add_heading(text, level=2)

    def p(self, text, bold_prefix=None):
        para = self.doc.add_paragraph()
        if bold_prefix:
            para.add_run(bold_prefix).bold = True
        para.add_run(text)
        return para

    def bullets(self, items, style="List Bullet"):
        for item in items:
            para = self.doc.add_paragraph(style=style)
            if isinstance(item, tuple):
                para.add_run(item[0]).bold = True
                para.add_run(item[1])
            else:
                para.add_run(item)

    def steps(self, items):
        self.bullets(items, style="List Number")

    def code(self, text):
        for line in text.strip("\n").splitlines():
            para = self.doc.add_paragraph()
            para.paragraph_format.space_after = Pt(0)
            para.paragraph_format.left_indent = Pt(18)
            run = para.add_run(line)
            run.font.name = "Consolas"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
            run.font.size = Pt(9.5)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(0)

    def table(self, header, rows, widths=None):
        table = self.doc.add_table(rows=1, cols=len(header))
        table.style = "Table Grid"
        for cell, text in zip(table.rows[0].cells, header):
            cell.text = ""
            cell.paragraphs[0].add_run(text).bold = True
            shading = OxmlElement("w:shd")
            shading.set(qn("w:val"), "clear")
            shading.set(qn("w:color"), "auto")
            shading.set(qn("w:fill"), "D9E2F3")
            cell._element.get_or_add_tcPr().append(shading)
        for row in rows:
            cells = table.add_row().cells
            for cell, text in zip(cells, row):
                cell.text = str(text)
        if widths:
            table.autofit = False
            for column, width in zip(table.columns, widths):
                column.width = Pt(width)
            for row in table.rows:
                for cell, width in zip(row.cells, widths):
                    cell.width = Pt(width)
        self.doc.add_paragraph()

    def save(self, name):
        path = HERE / name
        self.doc.save(path)
        print(f"Written: {path}")


def technical_en():
    d = Doc("Trademark Image Checker", "Technical documentation - design, installation and operation (version 1.0.0)")

    d.h1("1. Purpose")
    d.p("Trademark Image Checker is a Windows desktop program that examines a raster image against a "
        "configurable set of criteria (file size, pixel dimensions, resolution and image type), shows "
        "the result in a GUI, lets the user choose valid target values for the failing properties and "
        "converts the image accordingly. Its default criteria correspond to typical trademark office "
        "image upload requirements.")

    d.h1("2. Requirements")
    d.h2("2.1 Running the compiled program")
    d.bullets([
        "Windows 10 or Windows 11, 64-bit (x64).",
        "No Python installation is needed: dist\\TrademarkImage.exe is a self-contained single file.",
        "Write access to the folder of the converted images and, optionally, to the folder of the criteria file.",
    ])
    d.h2("2.2 Running from source")
    d.table(["Component", "Version", "Purpose"], [
        ["Python", "3.10 or newer (developed and tested with 3.14.0)", "Runtime; must include tkinter (Tk 8.6)"],
        ["Pillow", ">= 11.0 (tested 13.0.0)", "Image reading, conversion and writing"],
        ["tkinterdnd2", ">= 0.4 (tested 0.6.4)", "Drag and drop of files into the Tk window (bundles tkdnd 2.9/2.10)"],
        ["pytest", ">= 8.0 (tested 9.1.1)", "Automated tests (development only)"],
        ["PyInstaller", ">= 6.16 (tested 6.22.3)", "Building the Windows executable (development only)"],
        ["python-docx", ">= 1.1 (tested 1.2.0)", "Regenerating this documentation (development only)"],
    ], widths=[90, 150, 230])
    d.p("Runtime dependencies are listed in requirements.txt, development dependencies in requirements-dev.txt.")

    d.h2("2.3 Installation from source")
    d.code("""
git clone <repository> Trademarkimage
cd Trademarkimage
python -m venv .venv
.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt
""")
    d.h2("2.4 Running")
    d.code("""
.venv\\Scripts\\python.exe -m trademarkimage [--config FILE] [IMAGE]
.venv\\Scripts\\python.exe run_trademarkimage.py [--config FILE] [IMAGE]
dist\\TrademarkImage.exe [--config FILE] [IMAGE]
""")
    d.table(["Argument", "Meaning"], [
        ["--config FILE", "Criteria JSON file. Default: criterias.json in the current (startup) directory."],
        ["IMAGE", "Optional image file opened at start (also works by dropping a file on the exe icon)."],
        ["--version", "Prints the version number."],
    ], widths=[100, 370])

    d.h1("3. Architecture")
    d.p("The program is a Python package (trademarkimage) with a strict separation between the "
        "image logic, the workflow model and the user interface. Everything except gui.py can be used "
        "and tested without a display.")
    d.table(["Module", "Responsibility"], [
        ["criteria.py", "Criteria dataclass with defaults, validation, JSON load/save (load_criteria, save_criteria), "
                        "the list of image types and their Pillow modes."],
        ["analyzer.py", "analyze(path) -> ImageInfo (format, file size, displayed width/height, DPI, mode); "
                        "Prop enum of checked properties; check_value / check_image; value formatting."],
        ["converter.py", "Output formats and their capabilities (SAVE_FORMATS), prepare_image (orientation, "
                         "transparency, resize, type conversion) and convert_image (encoding with file size limit)."],
        ["session.py", "Session: GUI independent state of one examined image - the failing (flagged) properties, "
                       "the target values chosen by the user, input parsing, suggestions, keep-aspect logic and "
                       "building ConversionSettings."],
        ["gui.py", "Tkinter UI: App main window, CriteriaPanel, ValueDialog; drag and drop via tkinterdnd2."],
        ["app.py", "Command line parsing and loading of the startup criteria; creates the window."],
        ["__main__.py, run_trademarkimage.py", "Entry points (python -m trademarkimage, PyInstaller)."],
    ], widths=[120, 350])
    d.h2("3.1 Data flow")
    d.steps([
        "app.main() parses the arguments and loads the criteria file (or the defaults).",
        "The user drops or opens an image; App.open_image() calls analyzer.analyze() and creates a Session.",
        "If Session.passed is true, a green OK button is shown; pressing it closes the program.",
        "Otherwise one red button per flagged property is shown. Pressing it opens a ValueDialog; the input is "
        "validated by Session.parse_value() and stored with Session.set_target(). Valid buttons turn white.",
        "When every property has a valid target value (Session.all_valid), App.convert_and_save() asks for the "
        "output file and format and calls converter.convert_image() with Session.conversion_settings().",
        "The written file is analysed again and checked against the criteria; the result is reported and the "
        "converted image is loaded into the window (which then shows the green OK button).",
    ])
    d.h2("3.2 Testability of the GUI")
    d.p("All dialogs used by App are wrapped in overridable methods (ask_value, ask_save_path, ask_yes_no, "
        "show_error, show_info, ask_criteria_save_path, ask_criteria_open_path). The GUI tests replace them "
        "with scripted answers and drive the real Tk widgets (button.invoke()).")

    d.h1("4. Criteria and the criteria file")
    d.table(["JSON key", "Default", "Meaning"], [
        ["max_file_size_mb", "2.0", "Maximum file size in MB (1 MB = 1 048 576 bytes)."],
        ["min_width", "945", "Minimum width in pixels."],
        ["min_height", "945", "Minimum height in pixels."],
        ["max_width", "2835", "Maximum width in pixels."],
        ["max_height", "2010", "Maximum height in pixels."],
        ["min_dpi", "96.0", "Minimum resolution in DPI (the smaller of the horizontal and vertical value is used)."],
        ["allowed_types", '["RGB", "greyscale", "B&W", "CMYK"]',
         "Allowed image types. Known types: RGB, RGBA, greyscale, B&W, CMYK, palette."],
    ], widths=[100, 130, 240])
    d.p("Example (criterias.example.json):")
    d.code("""
{
  "max_file_size_mb": 2.0,
  "min_width": 945,
  "min_height": 945,
  "max_width": 2835,
  "max_height": 2010,
  "min_dpi": 96.0,
  "allowed_types": ["RGB", "greyscale", "B&W", "CMYK"]
}
""")
    d.bullets([
        "Missing keys take their default value, so a file may contain only the values that differ.",
        "Unknown keys, wrong value types, non-integer pixel values, min > max, an empty or unknown type list "
        "are rejected with a descriptive error (CriteriaError).",
        "At start-up the program loads criterias.json from the current directory, or the file given with "
        "--config. A missing default file silently means default criteria; a missing --config file or an "
        "invalid file produces a warning and the defaults are used.",
        "When the user applies changed criteria in the GUI, the program asks whether to save them; the save "
        "dialog proposes the current criteria file. The 'Load criteria...' button loads an alternative file.",
        "Changing or loading criteria re-examines the current image.",
    ])

    d.h1("5. Checking rules")
    d.table(["Property", "Source", "Passes when"], [
        ["File size", "Size of the file on disk", "0 < size <= max_file_size_mb x 1 048 576"],
        ["Width / Height", "Pixel size after applying the EXIF orientation tag", "min <= value <= max"],
        ["Resolution", "dpi info (JPEG JFIF/EXIF, PNG pHYs, TIFF, BMP); JFIF dots/cm converted; "
                       "rounded to 0.1 DPI", "smaller of x/y DPI >= min_dpi; a missing value fails"],
        ["Image type", "Pillow mode mapped to a type name", "type is in allowed_types"],
    ], widths=[85, 210, 175])
    d.table(["Pillow mode(s)", "Image type"], [
        ["1", "B&W"],
        ["L, LA, I, I;16, F", "greyscale"],
        ["RGB, RGBX, YCbCr", "RGB"],
        ["RGBA", "RGBA"],
        ["CMYK", "CMYK"],
        ["P, PA", "palette"],
        ["others (e.g. LAB, HSV)", "other - never allowed"],
    ], widths=[200, 270])

    d.h1("6. Workflow model (Session)")
    d.bullets([
        ("Flagged properties: ", "the properties that failed the initial check, plus any property that becomes "
                                 "invalid later (e.g. height after changing the width with 'keep aspect ratio')."),
        ("Target values: ", "initialised from the image; a button is red while its target is invalid and white "
                            "after a valid value is entered. Invalid input is rejected and the dialog stays open."),
        ("Keep aspect ratio: ", "setting width or height also sets the other dimension from the original ratio."),
        ("Suggestions: ", "the dialogs are pre-filled with a valid value; for the dimensions the scale factor "
                          "closest to 1 that brings both dimensions into range is used, so the default keeps "
                          "the aspect ratio when possible."),
        ("File size target: ", "only limits the output if file size was flagged; otherwise the criteria maximum "
                               "applies."),
        ("Automatic conversion: ", "when the last red button turns white the save dialog opens automatically; "
                                   "if cancelled, the 'Convert and save...' button can be used later."),
    ])

    d.h1("7. Conversion")
    d.steps([
        "The image is rotated according to the EXIF orientation tag.",
        "Transparency is composited onto a white background unless the target type is RGBA.",
        "The image is resized with the Lanczos filter in a continuous-tone working mode (L, RGB, RGBA or CMYK).",
        "The type is converted: B&W uses a fixed threshold of 128 (no dithering, keeps logos crisp); palette "
        "uses an adaptive 256 colour palette; CMYK uses Pillow's plain RGB->CMYK conversion (no ICC colour "
        "management).",
        "The image is encoded in memory with the chosen DPI. JPEG uses the highest quality between 95 and 40 "
        "that fits under the size limit (binary search). If the file is still too big, the image is scaled down "
        "proportionally, but never below the minimum width/height; if that is not enough an error is shown.",
        "The data is written to the chosen file, then the file is analysed and checked again.",
    ])
    d.table(["Format", "Extensions", "Image types it can store", "Notes"], [
        ["JPEG", ".jpg .jpeg", "RGB, greyscale, CMYK", "Lossy; quality adjusted to the size limit"],
        ["PNG", ".png", "RGB, RGBA, greyscale, B&W, palette", "Lossless, optimize=True"],
        ["TIFF", ".tif .tiff", "all six types", "LZW, Group 4 for B&W"],
        ["BMP", ".bmp", "RGB, greyscale, B&W, palette", "Uncompressed - large files"],
    ], widths=[50, 75, 175, 170])
    d.p("The default output format is the format of the original file if it is writable and can store the "
        "target type; otherwise JPEG, PNG or TIFF (the first that fits). If the user selects an incompatible "
        "format, an error lists the suitable formats and the save dialog is shown again. A file name without "
        "extension gets the extension of the file type selected in the dialog.")

    d.h1("8. Tests")
    d.code(".venv\\Scripts\\python.exe -m pytest -q")
    d.p("86 automated tests (tests directory) cover:")
    d.bullets([
        "test_criteria.py - defaults, JSON round trip, partial files, every validation error, start-up loading "
        "and the --config parameter.",
        "test_analyzer.py - mode classification, DPI reading and rounding, missing DPI, EXIF orientation, "
        "invalid files, boundary values of every criterion.",
        "test_converter.py - format helpers, resizing, DPI, conversion to every type and format, transparency "
        "flattening, JPEG quality reduction, down-scaling of lossless formats, impossible size limits.",
        "test_session.py - flagged properties, input parsing and validation, keep aspect ratio, suggestions, "
        "conversion settings.",
        "test_gui.py - drag and drop registration, green OK button and exit, red/white buttons, the full "
        "fix-and-convert workflow, incompatible format retry, criteria apply/save prompt, loading alternative "
        "criteria. These tests need a Windows desktop session (Tk) and are skipped when Tk is unavailable.",
    ])

    d.h1("9. Building the Windows executable")
    d.p("The build uses a separate, minimal virtual environment (.venv-build) so that development packages are "
        "not bundled. Run from the project directory:")
    d.code("powershell -ExecutionPolicy Bypass -File build_exe.ps1 [-Python <python.exe>] [-SkipTests]")
    d.steps([
        "Creates .venv-build with the given Python (default: python on PATH) if it does not exist.",
        "Installs requirements.txt, pytest and PyInstaller into it.",
        "Runs the test suite; the build stops if any test fails.",
        "Runs PyInstaller with TrademarkImage.spec: one-file, windowed (no console), tkinterdnd2 data and the "
        "native tkdnd library collected with collect_all, development packages excluded.",
        "Result: dist\\TrademarkImage.exe (about 19 MB) plus dist\\criterias.example.json.",
    ])
    d.p("Deployment: copy TrademarkImage.exe to the target machine. To use custom criteria, place a "
        "criterias.json next to the exe (when started by double click the startup directory is the exe folder) "
        "or start it with --config. The one-file exe unpacks itself into a temporary folder at start, so the "
        "first start takes a few seconds. Unsigned executables may trigger a Windows SmartScreen warning.")

    d.h1("10. Known limitations")
    d.bullets([
        "Only the first frame of multi-frame images (animated GIF, multi-page TIFF) is processed.",
        "CMYK conversion is not colour managed; embedded ICC profiles are not carried over.",
        "Metadata (EXIF, ICC, XMP) is not copied to the converted image; only the DPI is written.",
        "Changing the DPI only changes the stored metadata; pixel dimensions are controlled by width/height.",
        "The GUI language is English; the user guide is available in Hungarian.",
    ])

    d.h1("11. Regenerating the documentation")
    d.code(".venv\\Scripts\\python.exe docs\\make_docs.py")
    d.save("TrademarkImage_Technical_Documentation_EN.docx")


def user_guide_hu():
    d = Doc("Trademark Image Checker", "Felhasználói kézikönyv (1.0.0 verzió)")

    d.h1("1. Mire való a program?")
    d.p("A Trademark Image Checker egy képfájlról megállapítja, hogy megfelel-e a beállított "
        "feltételeknek (fájlméret, képméret pixelben, felbontás, képtípus), például egy védjegybejelentéshez "
        "feltöltendő kép követelményeinek. Ha a kép nem felel meg, a program segít beállítani a megfelelő "
        "értékeket, majd elkészíti és elmenti az átalakított képet.")

    d.h1("2. A program indítása")
    d.bullets([
        "Kattintson duplán a TrademarkImage.exe fájlra. Python telepítésére nincs szükség.",
        "Az első indítás néhány másodpercig tarthat, mert a program kicsomagolja magát.",
        "Ha a Windows SmartScreen figyelmeztet, válassza a „További információ”, majd a „Futtatás mindenképp” "
        "lehetőséget (a program nincs digitálisan aláírva).",
        "Egy képfájlt az exe ikonjára húzva a program azonnal azzal a képpel indul.",
    ])
    d.p("Parancssorból további lehetőségek is vannak:")
    d.code("""
TrademarkImage.exe
TrademarkImage.exe kep.jpg
TrademarkImage.exe --config sajat_feltetelek.json kep.jpg
""")
    d.p("Ha az indítási könyvtárban van criterias.json nevű fájl, a program induláskor abból tölti be a "
        "feltételeket. A --config paraméterrel más fájl is megadható. Ha nincs ilyen fájl, a program az "
        "alapértelmezett feltételekkel dolgozik.")

    d.h1("3. A főablak részei")
    d.table(["Terület", "Leírás"], [
        ["Criteria (bal oldal)", "A feltételek beállítása, az Apply (alkalmaz), Load criteria... (betöltés) és "
                                 "Save criteria as... (mentés másként) gombok. Alul látható, melyik fájlból "
                                 "származnak a feltételek."],
        ["Képterület (jobb felül)", "Ide kell behúzni a képet; betöltés után a kép előnézete látszik."],
        ["Képadatok", "Fájlnév, formátum, mód, méret pixelben, felbontás (DPI), fájlméret."],
        ["Eredmény (jobb alul)", "Zöld OK gomb vagy a nem teljesülő feltételek piros gombjai és a "
                                 "Convert and save... (átalakítás és mentés) gomb."],
    ], widths=[130, 340])

    d.h1("4. Kép betöltése")
    d.steps([
        "Húzza a képfájlt a Windows Intézőből a „Drag and drop an image here” feliratú területre, vagy",
        "kattintson a területre, és válassza ki a képet a megnyíló ablakban.",
    ])
    d.p("Olvasható formátumok: JPEG, PNG, TIFF, BMP, GIF, WebP és a Pillow könyvtár által ismert egyéb "
        "formátumok. Ha a fájl nem kép, hibaüzenet jelenik meg.")

    d.h1("5. Az ellenőrzés eredménye")
    d.h2("5.1 A kép megfelel")
    d.p("Ha minden feltétel teljesül, egy zöld gomb jelenik meg: „OK - the image meets all criteria (click to "
        "exit)”. Erre kattintva a program bezárul, a képen nem változtat semmit.")
    d.h2("5.2 A kép nem felel meg")
    d.p("Minden nem teljesülő feltételhez egy piros gomb tartozik, amelyen a feltétel neve, a kép jelenlegi "
        "értéke és zárójelben a követelmény olvasható, például: „Width: 4000 px (945-2835 px)”.")
    d.table(["Gomb felirata", "Jelentése"], [
        ["File size", "Fájlméret (MB)"],
        ["Width", "Szélesség (pixel)"],
        ["Height", "Magasság (pixel)"],
        ["Resolution", "Felbontás (DPI); „not set”, ha a fájl nem tartalmaz felbontást"],
        ["Image type", "Képtípus (színmód)"],
    ], widths=[130, 340])

    d.h1("6. A hibás értékek javítása")
    d.steps([
        "Kattintson egy piros gombra. Megnyílik egy ablak, amely mutatja a jelenlegi értéket és a "
        "követelményt, az új érték mezője pedig egy megfelelő javaslattal van kitöltve.",
        "Írja be (vagy fogadja el) a kívánt értéket, és nyomja meg az OK gombot.",
        "Ha az érték megfelel a feltételnek, a gomb fehér lesz, és az új értéket mutatja (pl. „Width: 4000 px "
        "-> 2800 px”). Ha nem felel meg, hibaüzenet jelenik meg, és az ablak nyitva marad. A Cancel gombbal "
        "a változtatás elvethető, a gomb piros marad.",
    ])
    d.bullets([
        ("Szélesség, magasság: ", "a „Keep aspect ratio” jelölőnégyzet bekapcsolva (alapértelmezés) a másik "
                                  "méretet is arányosan módosítja, így a kép nem torzul. Ha emiatt a másik "
                                  "méret kerül a megengedett tartományon kívülre, arra is megjelenik egy piros "
                                  "gomb. A felajánlott értékek - ha lehetséges - megtartják a képarányt."),
        ("Felbontás: ", "egész szám DPI-ben. A felbontás csak a fájlban tárolt adat, a pixelméretet nem változtatja."),
        ("Fájlméret: ", "a megengedett legnagyobb méret MB-ban (tizedesvessző és -pont is használható). A program "
                        "a mentéskor szükség esetén csökkenti a JPEG minőséget, illetve a képméretet, hogy a "
                        "fájl beleférjen."),
        ("Képtípus: ", "a listából választható ki a megengedett típusok egyike."),
    ])

    d.h1("7. Átalakítás és mentés")
    d.p("Amikor az utolsó piros gomb is fehér lesz, a program automatikusan megnyitja a mentési ablakot. Ha ezt "
        "megszakítja, később a „Convert and save...” gombbal indíthatja újra.")
    d.bullets([
        "Az alapértelmezett formátum az eredeti fájl formátuma (ha az a választott képtípust tárolni tudja), "
        "az alapértelmezett fájlnév „<eredeti név>_converted”.",
        "A formátumot a fájltípus-listából vagy a kiterjesztéssel (.jpg, .png, .tif, .bmp) lehet megadni.",
        "Ha a formátum nem tudja tárolni a képtípust (pl. CMYK képet PNG-be), a program jelzi, mely formátumok "
        "megfelelőek, és újra megnyitja a mentési ablakot.",
        "Mentés után a program újra ellenőrzi az elkészült fájlt, kiírja az eredményt (méret, fájlméret, "
        "JPEG minőség), és betölti az új képet - ha minden rendben, megjelenik a zöld OK gomb.",
    ])
    d.table(["Formátum", "Tárolható képtípusok", "Megjegyzés"], [
        ["JPEG (.jpg)", "RGB, greyscale, CMYK", "Veszteséges, kis fájlméret - általában ez ajánlott"],
        ["PNG (.png)", "RGB, RGBA, greyscale, B&W, palette", "Veszteségmentes"],
        ["TIFF (.tif)", "mind", "Veszteségmentes tömörítés"],
        ["BMP (.bmp)", "RGB, greyscale, B&W, palette", "Tömörítetlen, nagy fájlok"],
    ], widths=[85, 175, 210])
    d.p("Átalakításkor az átlátszó részek fehér hátteret kapnak (kivéve RGBA típus esetén), a fekete-fehér "
        "(B&W) átalakítás 50%-os küszöbbel történik, a kép pedig a fényképezőgép által tárolt tájolás szerint "
        "elforgatásra kerül.")

    d.h1("8. A feltételek beállítása")
    d.table(["Mező", "Jelentés", "Alapérték"], [
        ["Maximum file size (MB)", "Legnagyobb fájlméret (1 MB = 1 048 576 bájt)", "2"],
        ["Minimum width (px)", "Legkisebb szélesség", "945"],
        ["Minimum height (px)", "Legkisebb magasság", "945"],
        ["Maximum width (px)", "Legnagyobb szélesség", "2835"],
        ["Maximum height (px)", "Legnagyobb magasság", "2010"],
        ["Minimum resolution (DPI)", "Legkisebb felbontás", "96"],
        ["Allowed image types", "Megengedett képtípusok", "RGB, greyscale, B&W, CMYK"],
    ], widths=[140, 220, 110])
    d.table(["Képtípus", "Jelentése"], [
        ["RGB", "Színes kép"],
        ["RGBA", "Színes kép átlátszósággal"],
        ["greyscale", "Szürkeárnyalatos kép"],
        ["B&W", "Fekete-fehér (kétszínű) kép"],
        ["CMYK", "Nyomdai színmodellű kép"],
        ["palette", "Palettás (legfeljebb 256 színű) kép, pl. GIF"],
    ], widths=[130, 340])
    d.steps([
        "Módosítsa a mezőket, majd nyomja meg az Apply gombot.",
        "Ha a feltételek változtak, a program megkérdezi, el akarja-e menteni őket fájlba. Igen válasz esetén "
        "a mentési ablak a jelenlegi feltételfájlt (alapesetben criterias.json) ajánlja fel.",
        "A betöltött kép ellenőrzése az új feltételekkel automatikusan megismétlődik.",
    ])
    d.p("Más feltételkészlet betöltése: Load criteria... gomb, majd a JSON fájl kiválasztása. "
        "Mentés tetszőleges néven: Save criteria as... gomb.")
    d.p("Ha azt szeretné, hogy a program mindig a saját feltételeivel induljon, mentse őket criterias.json "
        "néven az exe mellé. A fájl egyszerű JSON szöveg, Jegyzettömbbel is szerkeszthető:")
    d.code("""
{
  "max_file_size_mb": 2.0,
  "min_width": 945,
  "min_height": 945,
  "max_width": 2835,
  "max_height": 2010,
  "min_dpi": 96.0,
  "allowed_types": ["RGB", "greyscale", "B&W", "CMYK"]
}
""")

    d.h1("9. Gyakori kérdések és hibaüzenetek")
    d.table(["Üzenet / helyzet", "Teendő"], [
        ["Cannot open image / Not a recognised image file", "A fájl nem kép vagy sérült - válasszon másik fájlt."],
        ["Invalid value", "A beírt érték nem szám vagy kívül esik a megengedett tartományon."],
        ["Invalid criteria", "A Criteria panel valamelyik mezője hibás (pl. a minimum nagyobb a maximumnál, "
                             "vagy nincs megengedett képtípus)."],
        ["Unsuitable format", "A választott fájlformátum nem tudja tárolni a képtípust - válasszon a felsorolt "
                              "formátumok közül."],
        ["Conversion failed ... minimum size", "A kép a megadott fájlméretbe a minimális képméret alatt sem fér "
                                               "bele. Válasszon JPEG formátumot vagy más képtípust."],
        ["A felbontás „not set”", "A fájl nem tárol DPI értéket; állítson be egyet a Resolution gombbal."],
        ["Figyelmeztetés indításkor a criteria fájlról", "A fájl hibás vagy nem található; a program az "
                                                         "alapértelmezett feltételeket használja."],
    ], widths=[170, 300])
    d.save("TrademarkImage_Felhasznaloi_kezikonyv_HU.docx")


if __name__ == "__main__":
    technical_en()
    user_guide_hu()
