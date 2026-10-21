import pytest
from PIL import Image

from trademarkimage.analyzer import (ImageError, Prop, analyze, check_image, check_value, classify_mode,
                                     describe_requirement, format_value)
from trademarkimage.criteria import Criteria


@pytest.mark.parametrize("mode, expected", [
    ("1", "B&W"), ("L", "greyscale"), ("I;16", "greyscale"), ("RGB", "RGB"), ("RGBA", "RGBA"),
    ("CMYK", "CMYK"), ("P", "palette"), ("LAB", "other"),
])
def test_classify_mode(mode, expected):
    assert classify_mode(mode) == expected


def test_analyze_jpeg(make_image):
    path = make_image("a.jpg", size=(1200, 1000), dpi=(300, 300))
    info = analyze(path)
    assert info.format == "JPEG"
    assert (info.width, info.height) == (1200, 1000)
    assert info.resolution == 300
    assert info.image_type == "RGB"
    assert info.file_size == path.stat().st_size


def test_png_dpi_is_rounded(make_image):
    info = analyze(make_image("a.png", dpi=(300, 300)))
    assert info.resolution == 300


def test_missing_dpi(make_image):
    info = analyze(make_image("a.png", dpi=None))
    assert info.dpi is None and info.resolution is None
    assert Prop.RESOLUTION in check_image(info, Criteria())


def test_uses_smaller_dpi(make_image):
    assert analyze(make_image("a.tif", dpi=(300, 72))).resolution == 72


def test_exif_orientation_swaps_dimensions(make_image):
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90 degrees
    info = analyze(make_image("a.jpg", size=(1200, 1000), exif=exif))
    assert (info.width, info.height) == (1000, 1200)


def test_not_an_image(tmp_path):
    path = tmp_path / "x.jpg"
    path.write_text("hello")
    with pytest.raises(ImageError, match="Not a recognised image"):
        analyze(path)
    with pytest.raises(ImageError, match="not found"):
        analyze(tmp_path / "missing.png")


def test_good_image_passes(make_image):
    assert check_image(analyze(make_image("ok.jpg", size=(1000, 1000), dpi=(96, 96))), Criteria()) == []


def test_all_failures_detected(make_image):
    path = make_image("bad.png", size=(3000, 500), mode="RGBA", dpi=(72, 72), noise=True)
    criteria = Criteria(max_file_size_mb=0.5)
    failed = check_image(analyze(path), criteria)
    assert failed == [Prop.FILE_SIZE, Prop.WIDTH, Prop.HEIGHT, Prop.RESOLUTION, Prop.IMAGE_TYPE]


@pytest.mark.parametrize("prop, value, ok", [
    (Prop.WIDTH, 944, False), (Prop.WIDTH, 945, True), (Prop.WIDTH, 2835, True), (Prop.WIDTH, 2836, False),
    (Prop.HEIGHT, 2010, True), (Prop.HEIGHT, 2011, False),
    (Prop.FILE_SIZE, 2 * 1024 * 1024, True), (Prop.FILE_SIZE, 2 * 1024 * 1024 + 1, False),
    (Prop.RESOLUTION, 96, True), (Prop.RESOLUTION, 95.9, False), (Prop.RESOLUTION, None, False),
    (Prop.IMAGE_TYPE, "CMYK", True), (Prop.IMAGE_TYPE, "RGBA", False),
])
def test_check_value_limits(prop, value, ok):
    assert check_value(prop, value, Criteria()) is ok


def test_progressive_jpeg_detected(make_image):
    progressive = analyze(make_image("p.jpg", progressive=True))
    baseline = analyze(make_image("b.jpg"))
    png = analyze(make_image("x.png"))
    assert progressive.jpeg_encoding == "progressive"
    assert baseline.jpeg_encoding == "baseline"
    assert png.jpeg_encoding is None
    assert check_image(progressive, Criteria()) == [Prop.JPEG_ENCODING]
    assert check_image(progressive, Criteria(allow_progressive_jpeg=True)) == []
    assert check_image(baseline, Criteria()) == [] and check_image(png, Criteria()) == []


def test_resolution_upper_limit(make_image):
    assert check_image(analyze(make_image("hi.jpg", dpi=(700, 700))), Criteria()) == [Prop.RESOLUTION]
    # The larger of the two values must not exceed the maximum.
    assert check_image(analyze(make_image("mixed.png", dpi=(300, 700))), Criteria()) == [Prop.RESOLUTION]
    assert check_image(analyze(make_image("ok.jpg", dpi=(600, 600))), Criteria()) == []


@pytest.mark.parametrize("value, ok", [
    (95.9, False), (96, True), (600, True), (600.1, False), ((96, 600), True), ((95, 300), False),
    ((300, 601), False), (None, False),
])
def test_resolution_range(value, ok):
    assert check_value(Prop.RESOLUTION, value, Criteria()) is ok


def test_formatting():
    c = Criteria()
    assert format_value(Prop.FILE_SIZE, 3 * 1024 * 1024) == "3.00 MB"
    assert format_value(Prop.RESOLUTION, None) == "not set"
    assert format_value(Prop.RESOLUTION, (300.0, 300.0)) == "300 DPI"
    assert format_value(Prop.RESOLUTION, (300.0, 72.0)) == "300 x 72 DPI"
    assert format_value(Prop.JPEG_ENCODING, "progressive") == "progressive"
    assert describe_requirement(Prop.RESOLUTION, c) == "96-600 DPI"
    assert describe_requirement(Prop.JPEG_ENCODING, c) == "baseline only, not progressive"
    assert describe_requirement(Prop.WIDTH, c) == "945-2835 px"
    assert describe_requirement(Prop.IMAGE_TYPE, c) == "allowed: RGB, greyscale, B&W, CMYK"
