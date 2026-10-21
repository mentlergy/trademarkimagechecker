"""Criteria definition, validation and JSON persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from .i18n import tr

DEFAULT_CONFIG_NAME = "criterias.json"

BYTES_PER_MB = 1024 * 1024

# Image types the program can recognise and produce. The keys are the names
# used in the GUI and in the JSON file; the values are the Pillow modes used
# when converting to that type.
IMAGE_TYPES: dict[str, str] = {
    "RGB": "RGB",
    "RGBA": "RGBA",
    "greyscale": "L",
    "B&W": "1",
    "CMYK": "CMYK",
    "palette": "P",
}
DEFAULT_ALLOWED_TYPES = ("RGB", "greyscale", "B&W", "CMYK")


def type_label(image_type: str) -> str:
    """The localized display name of an image type."""
    return tr(f"type.{image_type}")


class CriteriaError(ValueError):
    """Raised when criteria are invalid or a criteria file cannot be read."""


@dataclass
class Criteria:
    max_file_size_mb: float = 2.0
    min_width: int = 945
    min_height: int = 945
    max_width: int = 2835
    max_height: int = 2010
    min_dpi: float = 96.0
    max_dpi: float = 600.0
    allowed_types: list[str] = field(default_factory=lambda: list(DEFAULT_ALLOWED_TYPES))
    allow_progressive_jpeg: bool = False

    @property
    def max_file_size_bytes(self) -> int:
        return int(self.max_file_size_mb * BYTES_PER_MB)

    def errors(self) -> list[str]:
        """Return a list of human readable problems; empty if the criteria are valid."""
        problems = []
        if self.max_file_size_mb <= 0:
            problems.append(tr("criteria.error.max_size"))
        for name in ("min_width", "min_height", "max_width", "max_height"):
            if getattr(self, name) < 1:
                problems.append(tr("criteria.error.min_pixel", field=tr(f"criteria.field.{name}")))
        if self.min_width > self.max_width:
            problems.append(tr("criteria.error.width_range"))
        if self.min_height > self.max_height:
            problems.append(tr("criteria.error.height_range"))
        if self.min_dpi < 0:
            problems.append(tr("criteria.error.negative_dpi"))
        if self.max_dpi <= 0:
            problems.append(tr("criteria.error.max_dpi"))
        elif self.min_dpi > self.max_dpi:
            problems.append(tr("criteria.error.dpi_range"))
        if not self.allowed_types:
            problems.append(tr("criteria.error.no_types"))
        unknown = [t for t in self.allowed_types if t not in IMAGE_TYPES]
        if unknown:
            problems.append(tr("criteria.error.unknown_types", types=", ".join(unknown)))
        return problems

    def validate(self) -> None:
        problems = self.errors()
        if problems:
            raise CriteriaError(" ".join(problems))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Criteria:
        """Build criteria from a dict. Missing keys fall back to the defaults."""
        if not isinstance(data, dict):
            raise CriteriaError(tr("criteria.error.not_object"))
        known = {f.name: f for f in fields(cls)}
        unknown = sorted(set(data) - set(known))
        if unknown:
            raise CriteriaError(tr("criteria.error.unknown_keys", keys=", ".join(unknown)))

        values = {}
        for name, value in data.items():
            if name == "allowed_types":
                if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                    raise CriteriaError(tr("criteria.error.types_list"))
                values[name] = list(value)
            elif name == "allow_progressive_jpeg":
                if not isinstance(value, bool):
                    raise CriteriaError(tr("criteria.error.not_bool", name=name))
                values[name] = value
            elif name in ("max_file_size_mb", "min_dpi", "max_dpi"):
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise CriteriaError(tr("criteria.error.not_number", name=name))
                values[name] = float(value)
            else:
                if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
                    raise CriteriaError(tr("criteria.error.not_whole", name=name))
                values[name] = int(value)
        criteria = cls(**values)
        criteria.validate()
        return criteria


def load_criteria(path: str | Path) -> Criteria:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CriteriaError(tr("criteria.error.read", path=path, error=exc)) from exc
    except UnicodeDecodeError as exc:  # e.g. an image file
        raise CriteriaError(tr("criteria.error.json", path=path, error=exc)) from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CriteriaError(tr("criteria.error.json", path=path, error=exc)) from exc
    return Criteria.from_dict(data)


def save_criteria(criteria: Criteria, path: str | Path) -> None:
    criteria.validate()
    Path(path).write_text(json.dumps(criteria.to_dict(), indent=2) + "\n", encoding="utf-8")
