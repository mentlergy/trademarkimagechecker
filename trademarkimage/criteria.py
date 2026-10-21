"""Criteria definition, validation and JSON persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

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
    allowed_types: list[str] = field(default_factory=lambda: list(DEFAULT_ALLOWED_TYPES))

    @property
    def max_file_size_bytes(self) -> int:
        return int(self.max_file_size_mb * BYTES_PER_MB)

    def errors(self) -> list[str]:
        """Return a list of human readable problems; empty if the criteria are valid."""
        problems = []
        if self.max_file_size_mb <= 0:
            problems.append("Maximum file size must be greater than 0.")
        for name in ("min_width", "min_height", "max_width", "max_height"):
            if getattr(self, name) < 1:
                problems.append(f"{name} must be at least 1 pixel.")
        if self.min_width > self.max_width:
            problems.append("Minimum width is greater than maximum width.")
        if self.min_height > self.max_height:
            problems.append("Minimum height is greater than maximum height.")
        if self.min_dpi < 0:
            problems.append("Minimum resolution cannot be negative.")
        if not self.allowed_types:
            problems.append("At least one image type must be allowed.")
        unknown = [t for t in self.allowed_types if t not in IMAGE_TYPES]
        if unknown:
            problems.append(f"Unknown image type(s): {', '.join(unknown)}.")
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
            raise CriteriaError("The criteria file must contain a JSON object.")
        known = {f.name: f for f in fields(cls)}
        unknown = sorted(set(data) - set(known))
        if unknown:
            raise CriteriaError(f"Unknown key(s) in criteria: {', '.join(unknown)}.")

        values = {}
        for name, value in data.items():
            if name == "allowed_types":
                if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                    raise CriteriaError("allowed_types must be a list of strings.")
                values[name] = list(value)
            elif name in ("max_file_size_mb", "min_dpi"):
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise CriteriaError(f"{name} must be a number.")
                values[name] = float(value)
            else:
                if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
                    raise CriteriaError(f"{name} must be a whole number.")
                values[name] = int(value)
        criteria = cls(**values)
        criteria.validate()
        return criteria


def load_criteria(path: str | Path) -> Criteria:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CriteriaError(f"Cannot read criteria file '{path}': {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CriteriaError(f"Invalid JSON in '{path}': {exc}") from exc
    return Criteria.from_dict(data)


def save_criteria(criteria: Criteria, path: str | Path) -> None:
    criteria.validate()
    Path(path).write_text(json.dumps(criteria.to_dict(), indent=2) + "\n", encoding="utf-8")
