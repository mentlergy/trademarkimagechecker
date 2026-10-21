import json

import pytest

from trademarkimage.app import load_startup_criteria, parse_args
from trademarkimage.criteria import (DEFAULT_CONFIG_NAME, Criteria, CriteriaError, load_criteria,
                                     save_criteria)


def test_defaults_match_specification():
    c = Criteria()
    assert c.max_file_size_mb == 2
    assert c.max_file_size_bytes == 2 * 1024 * 1024
    assert (c.min_width, c.min_height, c.max_width, c.max_height) == (945, 945, 2835, 2010)
    assert c.min_dpi == 96
    assert c.allowed_types == ["RGB", "greyscale", "B&W", "CMYK"]
    assert c.errors() == []


def test_save_and_load_roundtrip(tmp_path):
    c = Criteria(max_file_size_mb=1.5, min_width=500, min_dpi=300, allowed_types=["RGB"])
    path = tmp_path / "c.json"
    save_criteria(c, path)
    assert json.loads(path.read_text(encoding="utf-8"))["min_width"] == 500
    assert load_criteria(path) == c


def test_partial_file_uses_defaults(tmp_path):
    path = tmp_path / "c.json"
    path.write_text('{"min_dpi": 300}', encoding="utf-8")
    c = load_criteria(path)
    assert c.min_dpi == 300
    assert c.max_width == 2835


@pytest.mark.parametrize("content, message", [
    ("not json", "Invalid JSON"),
    ("[1, 2]", "JSON object"),
    ('{"min_widht": 3}', "Unknown key"),
    ('{"min_width": "big"}', "whole number"),
    ('{"min_width": 1.5}', "whole number"),
    ('{"max_file_size_mb": true}', "number"),
    ('{"allowed_types": "RGB"}', "list of strings"),
    ('{"allowed_types": ["XYZ"]}', "Unknown image type"),
    ('{"allowed_types": []}', "At least one"),
    ('{"min_width": 3000}', "greater than maximum width"),
    ('{"max_file_size_mb": 0}', "greater than 0"),
])
def test_invalid_files_are_rejected(tmp_path, content, message):
    path = tmp_path / "c.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(CriteriaError, match=message):
        load_criteria(path)


def test_missing_file(tmp_path):
    with pytest.raises(CriteriaError, match="Cannot read"):
        load_criteria(tmp_path / "missing.json")


def test_startup_loads_default_file_from_directory(tmp_path):
    save_criteria(Criteria(min_dpi=150), tmp_path / DEFAULT_CONFIG_NAME)
    criteria, path, warning = load_startup_criteria(None, cwd=tmp_path)
    assert criteria.min_dpi == 150
    assert path == tmp_path / DEFAULT_CONFIG_NAME
    assert warning is None


def test_startup_without_file_uses_defaults_silently(tmp_path):
    criteria, path, warning = load_startup_criteria(None, cwd=tmp_path)
    assert criteria == Criteria()
    assert warning is None


def test_startup_with_config_parameter(tmp_path):
    custom = tmp_path / "other.json"
    save_criteria(Criteria(min_width=100), custom)
    args = parse_args(["--config", str(custom), "image.png"])
    assert args.image == "image.png"
    criteria, path, warning = load_startup_criteria(args.config)
    assert criteria.min_width == 100 and path == custom and warning is None


def test_startup_with_missing_or_broken_config(tmp_path):
    criteria, _, warning = load_startup_criteria(str(tmp_path / "nope.json"))
    assert criteria == Criteria() and "not found" in warning
    broken = tmp_path / "broken.json"
    broken.write_text("{", encoding="utf-8")
    criteria, _, warning = load_startup_criteria(str(broken))
    assert criteria == Criteria() and "default criteria" in warning
