# Trademark Image Checker

_User manual (version 1.1.0)_

This manual has two parts. Part I describes the everyday use of the program. Part II covers the advanced options: command line parameters, the language setting and the language file, and the structure of the criteria file.

## I. Basic usage

### 1. What is the program for?

Trademark Image Checker examines an image file and tells whether it meets the configured criteria (file size, image size in pixels, resolution, image type), for example the requirements for an image uploaded with a trademark application. If the image does not meet them, the program helps you set suitable values, then creates and saves the converted image.

### 2. Starting the program

- Double-click TrademarkImage.exe. Python does not need to be installed.
- The first start may take a few seconds because the program unpacks itself.
- If Windows SmartScreen shows a warning, choose "More info" and then "Run anyway" (the program is not digitally signed).
- If you drag an image file onto the exe icon, the program starts with that image.

**Note: **The program starts in Hungarian by default. To switch to English, select English in the Nyelv list in the top right corner of the window; the loaded image and the values already set are kept. To start in English every time, see section 11.

### 3. The main window

| Area | Description |
|---|---|
| Language (top right corner) | Selects the language of the user interface (Magyar / English). |
| Criteria (left side) | Setting the criteria, with the Apply, Load criteria... and Save criteria as... buttons. The bottom line shows which file the criteria come from. |
| Image area (top right) | Drop the image here; after loading, a preview of the image is shown. |
| Image data | File, format, mode, size in pixels, resolution (DPI), file size. |
| Result (bottom right) | A green OK button, or red buttons for the criteria that are not met and the Convert and save... button. |

### 4. Loading an image

1. Drag the image file from Windows Explorer onto the area labelled "Drag and drop an image here", or
2. click the area and select the image in the dialog that opens.

Readable formats: JPEG, PNG, TIFF, BMP, GIF, WebP and other formats known by the Pillow library. If the file is not an image, an error message is shown.

### 5. The result of the check

#### 5.1 The image meets the criteria

If every criterion is met, a green button appears: "OK - the image meets all criteria (click to exit)". Clicking it closes the program without changing the image.

#### 5.2 The image does not meet the criteria

There is a red button for every criterion that is not met. It shows the name of the criterion, the current value of the image and the requirement in brackets, for example: "Width: 4000 px (945-2835 px)". The possible buttons are File size, Width, Height, Resolution and Image type. For the resolution, "not set" is shown if the file does not store a DPI value.

### 6. Fixing the values

1. Click a red button. A dialog opens showing the current value and the requirement; the New value field is filled in with a suitable suggestion.
2. Type (or accept) the desired value and press OK.
3. If the value meets the criterion, the button turns white and shows the new value (e.g. "Width: 4000 px -> 2800 px"). If not, an error message is shown and the dialog stays open. Cancel discards the change and the button stays red.

- **Width, height:** when the "Keep aspect ratio" check box is on (default), the other dimension is changed proportionally so the image is not distorted. If this moves the other dimension out of the allowed range, a red button appears for it too. The suggested values keep the aspect ratio whenever possible.
- **Resolution:** a whole number in DPI. The resolution is only information stored in the file; it does not change the pixel size.
- **File size:** the largest allowed size in MB (both decimal point and comma are accepted). When saving, the program lowers the JPEG quality or the image size if needed, so that the file fits.
- **Image type:** choose one of the allowed types from the list.

### 7. Converting and saving

When the last red button turns white, the program opens the save dialog automatically. If you cancel it, you can start it again later with the "Convert and save..." button.

- The default format is the format of the original file (if it can store the selected image type); the default file name is "\<original name>_converted" ("_atalakitott" in Hungarian).
- The format can be chosen in the file type list or with the extension (.jpg, .png, .tif, .bmp).
- If the format cannot store the image type (e.g. a CMYK image as PNG), the program lists the suitable formats and opens the save dialog again.
- After saving, the program checks the new file again, shows the result (size, file size, JPEG quality) and loads the new image - if everything is fine, the green OK button appears.

| Format | Image types it can store | Note |
|---|---|---|
| JPEG (.jpg) | RGB, greyscale, CMYK | Lossy, small files - usually recommended |
| PNG (.png) | RGB, RGBA, greyscale, B&W, palette | Lossless |
| TIFF (.tif) | all | Lossless compression |
| BMP (.bmp) | RGB, greyscale, B&W, palette | Uncompressed, large files |

During conversion transparent areas get a white background (except for the RGBA type), the black and white conversion uses a 50% threshold, and the image is rotated according to the orientation stored by the camera.

### 8. Setting the criteria

| Field | Default |
|---|---|
| Maximum file size (MB) | 2 (1 MB = 1 048 576 bytes) |
| Minimum width (px) | 945 |
| Minimum height (px) | 945 |
| Maximum width (px) | 2835 |
| Maximum height (px) | 2010 |
| Minimum resolution (DPI) | 96 |
| Allowed image types | RGB, greyscale, B&W, CMYK |

| Image type | Meaning |
|---|---|
| RGB | Colour image |
| RGBA | Colour image with transparency |
| greyscale | Greyscale image |
| B&W | Two-colour (black and white) image |
| CMYK | Image in the printing colour model |
| palette | Image with at most 256 colours, e.g. GIF |

1. Change the fields, then press Apply.
2. If the criteria have changed, the program asks whether you want to save them to a file. If you answer Yes, the save dialog offers the current criteria file (criterias.json by default).
3. The loaded image is checked again with the new criteria automatically.

To load another set of criteria, press Load criteria... and select the JSON file. To save under any name, press Save criteria as.... Criteria files are described in section 12.

### 9. Frequently asked questions and error messages

| Message / situation | What to do |
|---|---|
| Cannot open image / Not a recognised image file | The file is not an image or it is damaged - choose another file. |
| Invalid value | The value entered is not a number or is outside the allowed range. |
| Invalid criteria | A field of the Criteria panel is wrong (e.g. the minimum is greater than the maximum, or no image type is allowed). |
| Unsuitable format | The selected file format cannot store the image type - choose one of the listed formats. |
| Conversion failed ... minimum size | The image does not fit into the given file size even at the minimum image size. Choose the JPEG format or another image type. |
| Resolution is "not set" | The file does not store a DPI value; set one with the Resolution button. |
| The window is in Hungarian | Select English in the Nyelv list in the top right corner. |

---

## II. Advanced usage and customization

### 10. Command line parameters

The program can also be started from the command line (or from a shortcut) with parameters:

```powershell
TrademarkImage.exe
TrademarkImage.exe image.jpg
TrademarkImage.exe --config my_criteria.json image.jpg
TrademarkImage.exe --lang en
TrademarkImage.exe --locals my_texts.json
```

| Parameter | Meaning |
|---|---|
| --config FILE | JSON file containing the criteria (default: criterias.json in the startup folder). See section 12. |
| --lang CODE | Language of the user interface: hu (Hungarian) or en (English), or the code of any other language added to locals.json. See section 11. |
| --locals FILE | Your own text file (default: locals.json in the startup folder, if present). |
| IMAGE | Image file to open at start. |
| --version | Prints the version number of the program. |

When the program is started by double-click, the startup folder is the folder of the exe. For a shortcut it is the "Start in" field of the shortcut.

### 11. Language setting and the language file

#### 11.1 Choosing the language

- **While running:** in the Language (Nyelv) list in the top right corner of the main window. The choice is valid for the current run only.
- **At start:** with the --lang parameter, e.g. TrademarkImage.exe --lang en.
- **Permanently:** by changing the "default_language" value in locals.json (e.g. to "en").

#### 11.2 Structure of locals.json

All texts of the program are in the locals.json file next to the exe. It can be edited with Notepad (save it with UTF-8 encoding). Its structure:

```json
{
  "default_language": "hu",
  "languages": {
    "hu": { "language_name": "Magyar",  "prop.width": "Szélesség", ... },
    "en": { "language_name": "English", "prop.width": "Width", ... }
  }
}
```

- To change a text, edit the value in quotation marks after the colon. Do not change the key (the part before the colon).
- Parts in curly brackets (e.g. {value}, {path}) are filled in by the program - leave them unchanged. \n starts a new line.
- If a text is missing from a language, the program shows the English text. If the file is invalid, the program shows a warning and uses its built-in texts.
- It is enough to put a file containing only the changed texts next to the exe: the program adds it to its built-in texts and overrides them with it.

#### 11.3 Adding a language

1. Open locals.json and copy the "en" block.
2. Give it a new code (e.g. "de") and change "language_name" (e.g. "Deutsch").
3. Translate the texts, then save the file with UTF-8 encoding.
4. The new language appears in the Language list the next time the program starts.

### 12. The criteria file

At start the program loads the criteria from criterias.json in the startup folder, or from the file given with the --config parameter. If you want the program to always start with your own criteria, save them as criterias.json next to the exe (Save criteria as... button). The criteria file is plain JSON text and can also be edited with Notepad:

```json
{
  "max_file_size_mb": 2.0,
  "min_width": 945,
  "min_height": 945,
  "max_width": 2835,
  "max_height": 2010,
  "min_dpi": 96.0,
  "allowed_types": ["RGB", "greyscale", "B&W", "CMYK"]
}
```

| Key | Field in the window | Default |
|---|---|---|
| max_file_size_mb | Maximum file size (MB) | 2.0 |
| min_width | Minimum width (px) | 945 |
| min_height | Minimum height (px) | 945 |
| max_width | Maximum width (px) | 2835 |
| max_height | Maximum height (px) | 2010 |
| min_dpi | Minimum resolution (DPI) | 96.0 |
| allowed_types | Allowed image types | ["RGB", "greyscale", "B&W", "CMYK"] |

Image types must be given by their id in the file:

| Id in the file | Image type in the window (English / Hungarian) |
|---|---|
| RGB | RGB / RGB (színes) |
| RGBA | RGBA / RGBA (színes, átlátszó) |
| greyscale | greyscale / szürkeárnyalatos |
| B&W | B&W / fekete-fehér |
| CMYK | CMYK / CMYK |
| palette | palette / palettás |

- Missing keys get their default value, so it is enough to list the values that differ.
- Use a decimal point (2.5); pixel values are whole numbers.
- If there is an unknown key, a wrong value or a contradiction (e.g. the minimum is greater than the maximum), the program shows a warning and starts with the default criteria.

### 13. Troubleshooting the advanced settings

| Message / situation | What to do |
|---|---|
| Warning at start | The criteria file or locals.json is invalid / not found, or the --lang language code is unknown. The program runs with the default settings. |
| English text in another language | The text is missing from that language in locals.json - add the missing key. |
| A key such as prop.width is shown instead of a text | The text is missing from English as well - add it. |
| Strange characters instead of accented letters | Save locals.json with UTF-8 encoding. |
