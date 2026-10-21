"""Localisation. All user visible texts are stored in locals.json.

The built-in locals.json (next to this module) is always loaded. A locals.json
in the startup directory, or a file given with --locals, is merged over it, so
texts can be changed and new languages added without rebuilding the program.
"""

from __future__ import annotations

import json
import string
from pathlib import Path

LOCALS_FILE_NAME = "locals.json"
BUILTIN_LOCALS = Path(__file__).with_name(LOCALS_FILE_NAME)
# Used for texts that are missing from the selected language.
FALLBACK_LANGUAGE = "en"


class LocalizationError(Exception):
    """Raised when a localization file cannot be read or has a wrong structure."""


class Localization:
    def __init__(self, default_language: str | None, languages: dict[str, dict[str, str]]):
        self.default_language = default_language
        self.languages = languages

    @classmethod
    def from_dict(cls, data: dict) -> Localization:
        if not isinstance(data, dict) or not isinstance(data.get("languages"), dict):
            raise LocalizationError("The file must contain a JSON object with a \"languages\" object.")
        languages = {}
        for code, texts in data["languages"].items():
            if not isinstance(texts, dict) or not all(isinstance(v, str) for v in texts.values()):
                raise LocalizationError(f"Language \"{code}\" must be an object of text values.")
            languages[code] = dict(texts)
        default = data.get("default_language")
        if default is not None and not isinstance(default, str):
            raise LocalizationError("\"default_language\" must be a language code.")
        return cls(default, languages)

    @classmethod
    def load(cls, path: str | Path) -> Localization:
        path = Path(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise LocalizationError(f"Cannot read '{path}': {exc}") from exc
        except json.JSONDecodeError as exc:
            raise LocalizationError(f"Invalid JSON in '{path}': {exc}") from exc
        return cls.from_dict(data)

    def merge(self, other: Localization) -> None:
        """Add or override languages and texts from another localization."""
        for code, texts in other.languages.items():
            self.languages.setdefault(code, {}).update(texts)
        if other.default_language in self.languages:
            self.default_language = other.default_language

    def language_names(self) -> dict[str, str]:
        return {code: texts.get("language_name", code) for code, texts in self.languages.items()}

    def text(self, language: str, key: str) -> str:
        for code in (language, FALLBACK_LANGUAGE):
            value = self.languages.get(code, {}).get(key)
            if value is not None:
                return value
        return key


def placeholders(text: str) -> set[str]:
    """The names of the {placeholders} used in a text."""
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def _load_builtin() -> Localization:
    localization = Localization.load(BUILTIN_LOCALS)
    localization.default_language = localization.default_language or FALLBACK_LANGUAGE
    return localization


_localization = _load_builtin()
_language = _localization.default_language


def load_extra(path: str | Path) -> None:
    """Merge an additional localization file over the built-in texts.
    Its default_language, if given, becomes the current language."""
    global _language
    _localization.merge(Localization.load(path))
    _language = _localization.default_language


def reset() -> None:
    """Return to the built-in texts and default language."""
    global _localization, _language
    _localization = _load_builtin()
    _language = _localization.default_language


def languages() -> dict[str, str]:
    """Available languages as {code: name}."""
    return _localization.language_names()


def default_language() -> str:
    return _localization.default_language


def get_language() -> str:
    return _language


def set_language(code: str) -> None:
    global _language
    if code not in _localization.languages:
        raise LocalizationError(f"Unknown language: {code}")
    _language = code


def tr(key: str, **values) -> str:
    """Return the text for key in the current language, with {placeholders} filled in."""
    text = _localization.text(_language, key)
    if not values:
        return text
    try:
        return text.format(**values)
    except (KeyError, IndexError, ValueError):
        # A mistake in an edited translation must not break the program.
        fallback = _localization.text(FALLBACK_LANGUAGE, key)
        try:
            return fallback.format(**values)
        except (KeyError, IndexError, ValueError):
            return fallback
