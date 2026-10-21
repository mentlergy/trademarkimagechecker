"""GUI independent model of the check-and-fix workflow for one image."""

from __future__ import annotations

import math

from .analyzer import ImageInfo, Prop, check_image, check_value, describe_requirement, format_value
from .converter import ConversionSettings
from .criteria import BYTES_PER_MB, Criteria


class Session:
    """Holds an analysed image, the criteria and the target values chosen by the user.

    ``flagged`` contains the properties shown as buttons: the ones that failed
    the check, plus any that became invalid later (e.g. through keeping the
    aspect ratio). A button is red while its target value is invalid and white
    once a valid value is set.
    """

    def __init__(self, info: ImageInfo, criteria: Criteria):
        self.info = info
        self.criteria = criteria
        self.targets = {prop: info.value(prop) for prop in Prop}
        self._flagged = set(check_image(info, criteria))

    @property
    def passed(self) -> bool:
        """True if the original image meets all criteria."""
        return not check_image(self.info, self.criteria)

    @property
    def flagged(self) -> list[Prop]:
        return [prop for prop in Prop if prop in self._flagged]

    def is_valid(self, prop: Prop) -> bool:
        return check_value(prop, self.targets[prop], self.criteria)

    @property
    def all_valid(self) -> bool:
        return all(self.is_valid(prop) for prop in Prop)

    def button_text(self, prop: Prop) -> str:
        original = format_value(prop, self.info.value(prop))
        if self.is_valid(prop):
            if prop is Prop.FILE_SIZE:
                return f"{prop.label}: {original} -> at most {self.targets[prop] / BYTES_PER_MB:.2f} MB"
            return f"{prop.label}: {original} -> {format_value(prop, self.targets[prop])}"
        return f"{prop.label}: {original}  ({describe_requirement(prop, self.criteria)})"

    def parse_value(self, prop: Prop, text: str):
        """Convert user input into a target value; raise ValueError with a message if invalid."""
        text = text.strip()
        try:
            if prop is Prop.FILE_SIZE:
                value = round(float(text.replace(",", ".")) * BYTES_PER_MB)
            elif prop is Prop.IMAGE_TYPE:
                value = text
            else:
                value = int(text)
        except ValueError:
            raise ValueError(f"'{text}' is not a valid number.") from None
        if not check_value(prop, value, self.criteria):
            raise ValueError(f"{prop.label} must be {describe_requirement(prop, self.criteria)}.")
        return value

    def set_target(self, prop: Prop, value, keep_aspect: bool = False) -> None:
        """Set a valid target value. With keep_aspect, changing width or height
        also changes the other dimension proportionally."""
        if not check_value(prop, value, self.criteria):
            raise ValueError(f"{prop.label} must be {describe_requirement(prop, self.criteria)}.")
        self.targets[prop] = value
        if keep_aspect and prop in (Prop.WIDTH, Prop.HEIGHT):
            other = Prop.HEIGHT if prop is Prop.WIDTH else Prop.WIDTH
            ratio = self.info.height / self.info.width if prop is Prop.WIDTH else self.info.width / self.info.height
            self.targets[other] = max(1, round(value * ratio))
            if not self.is_valid(other):
                self._flagged.add(other)

    def suggestion(self, prop: Prop):
        """A valid value to pre-fill the input dialog with."""
        c = self.criteria
        if prop is Prop.FILE_SIZE:
            return c.max_file_size_bytes
        if prop in (Prop.WIDTH, Prop.HEIGHT):
            scale = self.fit_scale()
            if scale is not None:
                w, h = self.scaled_size(scale)
                return w if prop is Prop.WIDTH else h
            current = self.targets[prop]
            low, high = (c.min_width, c.max_width) if prop is Prop.WIDTH else (c.min_height, c.max_height)
            return min(max(current, low), high)
        if prop is Prop.RESOLUTION:
            return max(math.ceil(c.min_dpi), 1)
        current = self.targets[Prop.IMAGE_TYPE]
        if current in ("RGBA", "palette") and "RGB" in c.allowed_types:
            return "RGB"
        return c.allowed_types[0]

    def fit_scale(self) -> float | None:
        """Scale factor closest to 1 that brings both dimensions into range, or None."""
        c, w, h = self.criteria, self.info.width, self.info.height
        low = max(c.min_width / w, c.min_height / h)
        high = min(c.max_width / w, c.max_height / h)
        if low > high:
            return None
        return min(max(1.0, low), high)

    def scaled_size(self, scale: float) -> tuple[int, int]:
        c = self.criteria
        w = min(max(round(self.info.width * scale), c.min_width), c.max_width)
        h = min(max(round(self.info.height * scale), c.min_height), c.max_height)
        return w, h

    def conversion_settings(self) -> ConversionSettings:
        if not self.all_valid:
            raise ValueError("Not all properties have valid target values.")
        resolution = self.targets[Prop.RESOLUTION]
        dpi = round(resolution)
        if dpi < self.criteria.min_dpi:
            dpi = math.ceil(resolution)
        # The file size only limits the output if the user chose a target for it;
        # otherwise the original size must not restrict the converted image.
        max_size = self.criteria.max_file_size_bytes
        if Prop.FILE_SIZE in self._flagged:
            max_size = min(self.targets[Prop.FILE_SIZE], max_size)
        return ConversionSettings(
            width=self.targets[Prop.WIDTH],
            height=self.targets[Prop.HEIGHT],
            dpi=dpi,
            image_type=self.targets[Prop.IMAGE_TYPE],
            max_file_size=max_size,
            min_width=self.criteria.min_width,
            min_height=self.criteria.min_height,
        )
