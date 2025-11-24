"""
Utilities that help the front-end determine RTL/LTR classes.
"""

from __future__ import annotations

from typing import Iterable

from django.utils import translation

RTL_LANG_CODES: Iterable[str] = (
    "ar",
    "fa",
    "he",
    "ur",
    "ps",
)


def is_rtl(language_code: str | None = None) -> bool:
    """
    Return True when the provided language code (or current active language)
    represents a right-to-left language.
    """

    code = (language_code or translation.get_language() or "en").split("-")[0]
    try:
        lang_info = translation.get_language_info(code)
        return bool(lang_info.get("bidi"))
    except KeyError:
        return code in RTL_LANG_CODES


def direction(language_code: str | None = None) -> str:
    """
    Return 'rtl' or 'ltr' for the supplied language code.
    """

    return "rtl" if is_rtl(language_code) else "ltr"


def html_class(language_code: str | None = None) -> str:
    """
    Return a CSS class that can be added to the <html> element
    to toggle RTL-specific styling.
    """

    return "rtl" if is_rtl(language_code) else ""

