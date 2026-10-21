import os
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def make_image(tmp_path):
    """Create an image file: make_image(name, size, mode, dpi=..., fmt=..., noise=False)."""

    def _make(name="img.jpg", size=(1000, 1000), mode="RGB", dpi=(300, 300), fmt=None, noise=False, **save):
        path = tmp_path / name
        if noise:
            img = Image.frombytes("RGB", size, os.urandom(size[0] * size[1] * 3))
            if mode != "RGB":
                img = img.convert(mode)
        else:
            color = {"1": 1, "L": 128, "LA": (128, 255), "P": 3, "RGBA": (200, 30, 30, 128),
                     "CMYK": (0, 100, 100, 0)}.get(mode, (200, 30, 30))
            img = Image.new(mode, size, color)
        if dpi is not None:
            save["dpi"] = dpi
        img.save(path, format=fmt, **save)
        return path

    return _make
