import pytest
from PIL import Image

from trademarkimage.analyzer import analyze, check_image
from trademarkimage.converter import (ConversionError, ConversionSettings, convert_image, default_save_format,
                                      format_for_extension, is_compatible)
from trademarkimage.criteria import Criteria

MB = 1024 * 1024


def settings(**kw):
    values = dict(width=1000, height=1000, dpi=300, image_type="RGB", max_file_size=2 * MB,
                  min_width=945, min_height=945)
    values.update(kw)
    return ConversionSettings(**values)


def test_format_helpers():
    assert format_for_extension("x.JPG") == "JPEG"
    assert format_for_extension("x.tiff") == "TIFF"
    assert format_for_extension("x.xyz") is None
    assert is_compatible("PNG", "B&W") and not is_compatible("PNG", "CMYK")
    assert not is_compatible("JPEG", "B&W")
    assert default_save_format("PNG", "RGB") == "PNG"
    assert default_save_format("PNG", "CMYK") == "JPEG"
    assert default_save_format("GIF", "RGB") == "JPEG"
    assert default_save_format("JPEG", "B&W") == "PNG"


def test_resize_and_set_dpi(make_image, tmp_path):
    src = make_image("in.png", size=(3000, 3000), dpi=(72, 72))
    result = convert_image(src, settings(width=2000, height=2000), tmp_path / "out.jpg")
    info = analyze(result.path)
    assert result.format == "JPEG"
    assert (info.width, info.height) == (2000, 2000)
    assert info.resolution == 300
    assert check_image(info, Criteria()) == []


@pytest.mark.parametrize("image_type, mode, ext", [
    ("greyscale", "L", ".jpg"), ("B&W", "1", ".png"), ("CMYK", "CMYK", ".jpg"),
    ("CMYK", "CMYK", ".tif"), ("greyscale", "L", ".bmp"),("B&W", "1", ".tif"), ("palette", "P", ".png"),
])
def test_type_conversion(make_image, tmp_path, image_type, mode, ext):
    src = make_image("in.png", size=(1000, 1000), mode="RGBA")
    result = convert_image(src, settings(image_type=image_type), tmp_path / f"out{ext}")
    with Image.open(result.path) as img:
        assert img.mode == mode
    assert analyze(result.path).resolution == 300


def test_transparency_is_flattened_to_white(tmp_path):
    img =Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
    src = tmp_path / "transparent.png"
    img.save(src)
    result = convert_image(src, settings(), tmp_path / "out.png")
    with Image.open(result.path) as out:
        assert out.getpixel((10, 10)) == (255, 255, 255)


def test_incompatible_format_rejected(make_image, tmp_path):
    src = make_image("in.png")
    with pytest.raises(ConversionError, match="cannot store"):
        convert_image(src, settings(image_type="CMYK"), tmp_path / "out.png")
    with pytest.raises(ConversionError, match="Unsupported"):
        convert_image(src, settings(), tmp_path / "out.xyz")


def test_jpeg_quality_lowered_to_fit(make_image, tmp_path):
    src = make_image("noise.png", size=(1500, 1500), noise=True)
    limit = int(0.8 * MB)
    result = convert_image(src, settings(width=1500, height=1500, max_file_size=limit), tmp_path / "out.jpg")
    assert result.file_size <= limit
    assert result.path.stat().st_size == result.file_size
    assert result.quality < 95
    assert (result.width, result.height) == (1500, 1500)


def test_lossless_scaled_down_to_fit(make_image, tmp_path):
    src = make_image("noise.png", size=(2000, 2000), noise=True)
    limit = 4 * MB
    result = convert_image(src, settings(width=2000, height=2000, max_file_size=limit), tmp_path / "out.png")
    assert result.file_size <= limit
    assert 945 <= result.width < 2000


def test_cannot_fit_without_going_below_minimum(make_image, tmp_path):
    src = make_image("noise.png", size=(1000, 1000), noise=True)
    with pytest.raises(ConversionError, match="minimum size"):
        convert_image(src, settings(max_file_size=100 * 1024), tmp_path / "out.png")


def test_jpeg_output_is_always_baseline(make_image, tmp_path):
    src = make_image("progressive.jpg", progressive=True)
    assert analyze(src).jpeg_encoding == "progressive"
    result = convert_image(src, settings(), tmp_path / "out.jpg")
    assert analyze(result.path).jpeg_encoding == "baseline"


def test_separate_x_and_y_dpi(make_image, tmp_path):
    result = convert_image(make_image("in.png"), settings(dpi=(300, 350)), tmp_path / "out.tif")
    assert analyze(result.path).dpi == (300, 350)


def test_exif_orientation_applied(make_image, tmp_path):
    exif = Image.Exif()
    exif[0x0112] = 6
    src = make_image("rot.jpg", size=(1200, 1000), exif=exif)
    result = convert_image(src, settings(width=1000, height=1200), tmp_path / "out.jpg")
    with Image.open(result.path) as img:
        assert img.size == (1000, 1200)
