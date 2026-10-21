import pytest

from trademarkimage.analyzer import Prop, analyze
from trademarkimage.criteria import Criteria
from trademarkimage.session import Session

MB = 1024 * 1024


@pytest.fixture
def bad_session(make_image):
    # Too wide, too low resolution, alpha channel.
    path = make_image("bad.png", size=(4000, 2000), mode="RGBA", dpi=(72, 72))
    return Session(analyze(path), Criteria())


def test_passing_image(make_image):
    session = Session(analyze(make_image("ok.jpg", size=(1000, 1000))), Criteria())
    assert session.passed and session.flagged == [] and session.all_valid


def test_flagged_properties(bad_session):
    assert not bad_session.passed
    assert bad_session.flagged == [Prop.WIDTH, Prop.RESOLUTION, Prop.IMAGE_TYPE]
    assert not any(bad_session.is_valid(p) for p in bad_session.flagged)
    assert "Width: 4000 px" in bad_session.button_text(Prop.WIDTH)
    assert "945-2835" in bad_session.button_text(Prop.WIDTH)


def test_parse_value_validates(bad_session):
    assert bad_session.parse_value(Prop.WIDTH, " 2000 ") == 2000
    assert bad_session.parse_value(Prop.FILE_SIZE, "1,5") == int(1.5 * MB)
    with pytest.raises(ValueError, match="945-2835"):
        bad_session.parse_value(Prop.WIDTH, "3000")
    with pytest.raises(ValueError, match="not a valid number"):
        bad_session.parse_value(Prop.RESOLUTION, "abc")
    with pytest.raises(ValueError, match="allowed"):
        bad_session.parse_value(Prop.IMAGE_TYPE, "RGBA")


def test_set_values_until_valid(bad_session):
    bad_session.set_target(Prop.WIDTH, 2000)
    assert bad_session.is_valid(Prop.WIDTH)
    assert "-> 2000 px" in bad_session.button_text(Prop.WIDTH)
    assert not bad_session.all_valid
    bad_session.set_target(Prop.RESOLUTION, 300)
    bad_session.set_target(Prop.IMAGE_TYPE, "RGB")
    assert bad_session.all_valid
    s = bad_session.conversion_settings()
    assert (s.width, s.height, s.dpi, s.image_type) == (2000, 2000, 300, "RGB")
    # File size was not flagged, so only the criteria limit applies.
    assert s.max_file_size == 2 * MB


def test_set_invalid_value_rejected(bad_session):
    with pytest.raises(ValueError):
        bad_session.set_target(Prop.WIDTH, 5000)
    assert bad_session.targets[Prop.WIDTH] == 4000


def test_keep_aspect_ratio(bad_session):
    bad_session.set_target(Prop.WIDTH, 2800, keep_aspect=True)
    assert bad_session.targets[Prop.HEIGHT] == 1400
    assert bad_session.is_valid(Prop.HEIGHT)


def test_keep_aspect_ratio_can_flag_other_dimension(bad_session):
    bad_session.set_target(Prop.WIDTH, 1000, keep_aspect=True)
    assert bad_session.targets[Prop.HEIGHT] == 500
    assert Prop.HEIGHT in bad_session.flagged
    assert not bad_session.is_valid(Prop.HEIGHT)


def test_suggestions_are_valid(bad_session):
    for prop in Prop:
        value = bad_session.suggestion(prop)
        bad_session.set_target(prop, value)
    assert bad_session.all_valid
    # Aspect preserving suggestion: 4000x2000 scaled into range.
    assert bad_session.targets[Prop.WIDTH] == 2835
    assert bad_session.targets[Prop.HEIGHT] == 1418


def test_file_size_target_limits_conversion(make_image):
    path = make_image("big.png", size=(1000, 1000), noise=True)
    session = Session(analyze(path), Criteria(max_file_size_mb=1))
    assert session.flagged == [Prop.FILE_SIZE]
    session.set_target(Prop.FILE_SIZE, session.parse_value(Prop.FILE_SIZE, "0.5"))
    assert session.conversion_settings().max_file_size == MB // 2


def test_conversion_settings_require_valid_values(bad_session):
    with pytest.raises(ValueError):
        bad_session.conversion_settings()
