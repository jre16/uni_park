from __future__ import annotations

from typing import Any

from django.conf import settings
from django.http import HttpRequest
from django.urls import resolve, reverse, Resolver404
from django.utils import translation

from .utils.rtl import direction, html_class, is_rtl


def active_namespace(request: HttpRequest) -> str | None:
    try:
        match = resolve(request.path)
    except Resolver404:
        return None
    return match.namespace


def ui_settings(request: HttpRequest) -> dict[str, Any]:
    """
    Inject global UI-related context into every template.
    """

    lang_code = translation.get_language() or settings.LANGUAGE_CODE
    bidi = translation.get_language_info(lang_code.split("-")[0]).get("bidi", False)

    theme = request.COOKIES.get("unipark_theme", "dark")

    return {
        "LANGUAGE_CODE": lang_code,
        "LANGUAGE_BIDI": bidi,
        "IS_RTL": is_rtl(lang_code),
        "HTML_DIR": direction(lang_code),
        "HTML_CLASS": html_class(lang_code),
        "ACTIVE_NAMESPACE": active_namespace(request),
        "UNIPARK_THEME": theme,
        "LANGUAGE_SWITCH_URL": reverse("parking:toggle_language"),
    }

