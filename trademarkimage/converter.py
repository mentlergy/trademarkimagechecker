"""Converting an image to the chosen target properties and saving it."""

from __future__ import annotations

import io
import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

from .criteria import IMAGE_TYPES


class ConversionError(Exception):
    """Raised when the image cannot be converted or saved as requested."""


@dataclass(frozen=True)
class SaveFormat:
    name: str  # Pillow format name
    description: str
    extensions: tuple[str, ...]
    types: tuple[str, ...]  # image types the format can store
    lossy: bool = False


SAVE_FORMATS: dict[str, SaveFormat] = {
    "JPEG": SaveFormat("JPEG", "JPEG image", (".jpg", ".jpeg"), ("RGB", "greyscale", "CMYK"), lossy=True),
    "PNG": SaveFormat("PNG", "PNG image", (".png",), ("RGB", "RGBA", "greyscale", "B&W", "palette")),
    "TIFF": SaveFormat("TIFF", "TIFF image", (".tif", ".tiff"),
                       ("RGB", "RGBA", "greyscale", "B&W", "CMYK", "palette")),
    "BMP": SaveFormat("BMP", "Windows bitmap", (".bmp",), ("RGB", "greyscale", "B&W", "palette")),
}

# Lowest JPEG quality tried when the file has to be made smaller.
MIN_QUALITY = 40
MAX_QUALITY = 95


def format_for_extension(path: str | Path) -> str | None:
    ext = Path(path).suffix.lower()
    for fmt in SAVE_FORMATS.values():
        if ext in fmt.extensions:
            return fmt.name
    return None


def is_compatible(fmt: str, image_type: str) -> bool:
    return fmt in SAVE_FORMATS and image_type in SAVE_FORMATS[fmt].types


def default_save_format(original_format: str | None, image_type: str) -> str:
    """The original format if it can be written and can store the type, else a fallback."""
    candidates = [original_format, "JPEG", "PNG", "TIFF"]
    for fmt in candidates:
        if fmt and is_compatible(fmt, image_type):
            return fmt
    return "TIFF"


@dataclass(frozen=True)
class ConversionSettings:
    width: int
    height: int
    dpi: int
    image_type: str
    max_file_size: int  # bytes
    # Lower limits used when the image has to be scaled down to fit the file size.
    min_width: int = 1
    min_height: int = 1


@dataclass(frozen=True)
class ConversionResult:
    path: Path
    format: str
    file_size: int
    width: int
    height: int
    quality: int | None


def _flatten_alpha(img: Image.Image) -> Image.Image:
    """Composite an image with transparency onto a white background."""
    has_alpha = img.mode in ("RGBA", "LA", "RGBa", "La", "PA")
    if has_alpha or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        return Image.alpha_composite(background, rgba).convert("RGB")
    return img


def prepare_image(img: Image.Image, settings: ConversionSettings) -> Image.Image:
    """Return a new image with the target size and type (without saving it)."""
    if settings.image_type not in IMAGE_TYPES:
        raise ConversionError(f"Unknown image type: {settings.image_type}")
    target_mode = IMAGE_TYPES[settings.image_type]

    img = ImageOps.exif_transpose(img)
    if target_mode != "RGBA":
        img = _flatten_alpha(img)

    # Resize in a continuous-tone working mode so resampling gives good quality.
    if target_mode in ("1", "L"):
        work_mode = "L"
    elif target_mode == "CMYK" and img.mode == "CMYK":
        work_mode = "CMYK"
    elif target_mode == "RGBA":
        work_mode = "RGBA"
    else:
        work_mode = "RGB"
    if img.mode != work_mode:
        img = img.convert(work_mode)

    if img.size != (settings.width, settings.height):
        img = img.resize((settings.width, settings.height), Image.Resampling.LANCZOS)

    if target_mode == "1":
        # Plain threshold keeps logos crisp; dithering would add noise to edges.
        img = img.point(lambda v: 255 if v >= 128 else 0).convert("1", dither=Image.Dither.NONE)
    elif target_mode == "P":
        img = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
    elif img.mode != target_mode:
        img = img.convert(target_mode)
    return img


def _encode(img: Image.Image, fmt: str, dpi: int, quality: int | None) -> bytes:
    options: dict = {"dpi": (dpi, dpi)}
    if fmt == "JPEG":
        options.update(quality=quality, optimize=True)
    elif fmt == "PNG":
        options.update(optimize=True)
    elif fmt == "TIFF":
        options.update(compression="group4" if img.mode == "1" else "tiff_lzw")
    buffer = io.BytesIO()
    img.save(buffer, format=fmt, **options)
    return buffer.getvalue()


def _encode_within_limit(img: Image.Image, fmt: str, settings: ConversionSettings) -> tuple[bytes, int | None]:
    """Encode the image; for lossy formats pick the highest quality that fits."""
    if not SAVE_FORMATS[fmt].lossy:
        return _encode(img, fmt, settings.dpi, None), None

    data = _encode(img, fmt, settings.dpi, MAX_QUALITY)
    if len(data) <= settings.max_file_size:
        return data, MAX_QUALITY
    low, high = MIN_QUALITY, MAX_QUALITY - 1
    best = None
    while low <= high:
        quality = (low + high) // 2
        candidate = _encode(img, fmt, settings.dpi, quality)
        if len(candidate) <= settings.max_file_size:
            best = (candidate, quality)
            low = quality + 1
        else:
            high = quality - 1
    if best:
        return best
    return _encode(img, fmt, settings.dpi, MIN_QUALITY), MIN_QUALITY


def convert_image(source: str | Path, settings: ConversionSettings, destination: str | Path,
                  fmt: str | None = None) -> ConversionResult:
    """Convert the source image according to the settings and write it to destination.

    If the encoded file is larger than the allowed size, lossy formats first
    lower the quality, then the image is scaled down (keeping its aspect ratio)
    but never below the minimum width and height.
    """
    destination = Path(destination)
    fmt = fmt or format_for_extension(destination)
    if fmt not in SAVE_FORMATS:
        raise ConversionError(f"Unsupported output format: {destination.suffix or fmt}")
    if not is_compatible(fmt, settings.image_type):
        allowed = ", ".join(f for f in SAVE_FORMATS if is_compatible(f, settings.image_type))
        raise ConversionError(
            f"The {fmt} format cannot store '{settings.image_type}' images. Use one of: {allowed}.")

    try:
        with Image.open(source) as src:
            src.load()
            original = src.copy()
        img = prepare_image(original, settings)
    except OSError as exc:
        raise ConversionError(f"Cannot read source image: {exc}") from exc

    data, quality = _encode_within_limit(img, fmt, settings)
    width, height = img.size
    while len(data) > settings.max_file_size:
        factor = math.sqrt(settings.max_file_size / len(data)) * 0.95
        new_w = max(settings.min_width, int(width * factor))
        new_h = max(settings.min_height, int(height * factor))
        if (new_w, new_h) == (width, height) or new_w > width or new_h > height:
            raise ConversionError(
                f"The image cannot be saved as {fmt} under {settings.max_file_size / (1024 * 1024):.2f} MB "
                f"without going below the minimum size. Try the JPEG format or another image type.")
        width, height = new_w, new_h
        smaller = prepare_image(original, ConversionSettings(width, height, settings.dpi, settings.image_type,
                                                        settings.max_file_size))
        data, quality = _encode_within_limit(smaller, fmt, settings)

    try:
        destination.write_bytes(data)
    except OSError as exc:
        raise ConversionError(f"Cannot write '{destination}': {exc}") from exc
    return ConversionResult(destination, fmt, len(data), width, height, quality)
