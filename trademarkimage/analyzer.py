"""Reading image properties and checking them against the criteria."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from .criteria import BYTES_PER_MB, Criteria, type_label
from .i18n import tr

_MODE_TYPES = {
    "1": "B&W",
    "L": "greyscale",
    "LA": "greyscale",
    "La": "greyscale",
    "I": "greyscale",
    "I;16": "greyscale",
    "I;16B": "greyscale",
    "I;16L": "greyscale",
    "F": "greyscale",
    "RGB": "RGB",
    "RGBX": "RGB",
    "YCbCr": "RGB",
    "RGBA": "RGBA",
    "RGBa": "RGBA",
    "CMYK": "CMYK",
    "P": "palette",
    "PA": "palette",
}


class Prop(str, Enum):
    """The checked image properties, in display order."""

    FILE_SIZE = "file_size"
    WIDTH = "width"
    HEIGHT = "height"
    RESOLUTION = "resolution"
    IMAGE_TYPE = "image_type"

    @property
    def label(self) -> str:
        return tr(f"prop.{self.value}")


class ImageError(Exception):
    """Raised when a file cannot be opened as an image."""


def classify_mode(mode: str) -> str:
    """Map a Pillow mode to one of the image type names (or 'other')."""
    return _MODE_TYPES.get(mode, "other")


def read_dpi(img: Image.Image) -> tuple[float, float] | None:
    """Return the (x, y) resolution in DPI, or None if the file does not store one."""
    dpi = img.info.get("dpi")
    if dpi is None and img.info.get("jfif_unit") == 2:  # dots per cm
        density = img.info.get("jfif_density")
        if density:
            dpi = (density[0] * 2.54, density[1] * 2.54)
    if dpi is None:
        return None
    try:
        x, y = (float(v) for v in dpi)
    except (TypeError, ValueError):
        return None
    if x <= 0 or y <= 0:
        return None
    # PNG stores pixels per metre, so 300 DPI reads back as 299.9994.
    return round(x, 1), round(y, 1)


@dataclass(frozen=True)
class ImageInfo:
    path: Path
    format: str | None
    file_size: int
    width: int
    height: int
    dpi: tuple[float, float] | None
    mode: str

    @property
    def image_type(self) -> str:
        return classify_mode(self.mode)

    @property
    def resolution(self) -> float | None:
        """The smaller of the horizontal and vertical resolution."""
        return min(self.dpi) if self.dpi else None

    def value(self, prop: Prop):
        return {
            Prop.FILE_SIZE: self.file_size,
            Prop.WIDTH: self.width,
            Prop.HEIGHT: self.height,
            Prop.RESOLUTION: self.resolution,
            Prop.IMAGE_TYPE: self.image_type,
        }[prop]


def analyze(path: str | Path) -> ImageInfo:
    """Open an image file and collect the properties that are checked.

    Width and height are reported as displayed, i.e. after applying the EXIF
    orientation, which is also what the converter produces.
    """
    path = Path(path)
    try:
        file_size = path.stat().st_size
        with Image.open(path) as img:
            img.load()
            dpi = read_dpi(img)
            fmt = img.format
            mode = img.mode
            oriented = ImageOps.exif_transpose(img)
            width, height = oriented.size
    except FileNotFoundError as exc:
        raise ImageError(tr("image.error.not_found", path=path)) from exc
    except UnidentifiedImageError as exc:
        raise ImageError(tr("image.error.unrecognised", name=path.name)) from exc
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ImageError(tr("image.error.read", name=path.name, error=exc)) from exc
    return ImageInfo(path, fmt, file_size, width, height, dpi, mode)


def check_value(prop: Prop, value, criteria: Criteria) -> bool:
    """Return True if a single property value satisfies the criteria."""
    if prop is Prop.FILE_SIZE:
        return value is not None and 0 < value <= criteria.max_file_size_bytes
    if prop is Prop.WIDTH:
        return value is not None and criteria.min_width <= value <= criteria.max_width
    if prop is Prop.HEIGHT:
        return value is not None and criteria.min_height <= value <= criteria.max_height
    if prop is Prop.RESOLUTION:
        return value is not None and value >= criteria.min_dpi
    if prop is Prop.IMAGE_TYPE:
        return value in criteria.allowed_types
    raise ValueError(f"Unknown property {prop!r}")


def check_image(info: ImageInfo, criteria: Criteria) -> list[Prop]:
    """Return the properties of the image that do not meet the criteria."""
    return [prop for prop in Prop if not check_value(prop, info.value(prop), criteria)]


def format_value(prop: Prop, value) -> str:
    if value is None:
        return tr("value.not_set")
    if prop is Prop.FILE_SIZE:
        return tr("value.mb", value=value / BYTES_PER_MB)
    if prop in (Prop.WIDTH, Prop.HEIGHT):
        return tr("value.px", value=value)
    if prop is Prop.RESOLUTION:
        return tr("value.dpi", value=value)
    return type_label(value)


def describe_requirement(prop: Prop, criteria: Criteria) -> str:
    if prop is Prop.FILE_SIZE:
        return tr("requirement.file_size", max=criteria.max_file_size_mb)
    if prop is Prop.WIDTH:
        return tr("requirement.range_px", min=criteria.min_width, max=criteria.max_width)
    if prop is Prop.HEIGHT:
        return tr("requirement.range_px", min=criteria.min_height, max=criteria.max_height)
    if prop is Prop.RESOLUTION:
        return tr("requirement.resolution", min=criteria.min_dpi)
    return tr("requirement.types", types=", ".join(type_label(t) for t in criteria.allowed_types))
