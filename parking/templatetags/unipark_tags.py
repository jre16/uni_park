from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django import template
from django.urls import resolve, reverse, Resolver404
from django.utils import translation

register = template.Library()


@dataclass
class NavMatch:
    """
    Helper dataclass used to describe a navigation match result.
    """

    is_active: bool
    url_name: str | None = None


def _resolve_url_name(path: str) -> NavMatch:
    """
    Safely resolve the current path to a URL name.

    Returns:
        NavMatch: information about the resolved URL.
    """

    try:
        match = resolve(path)
    except Resolver404:
        return NavMatch(is_active=False, url_name=None)

    return NavMatch(is_active=True, url_name=match.url_name)


@register.simple_tag(takes_context=True)
def nav_active(context: dict[str, Any], url_name: str, *args: Any, **kwargs: Any) -> str:
    """
    Return the CSS class `is-active` when the current resolved URL matches.

    Usage:
        class="{% nav_active 'parking:home' %}"
    """

    request = context.get("request")
    if not request:
        return ""

    match = _resolve_url_name(request.path)
    if not match.url_name:
        return ""

    target = url_name
    # Allow passing fully qualified names or local ones
    if ":" not in target and request.resolver_match:
        target = f"{request.resolver_match.namespace}:{target}" if request.resolver_match.namespace else target

    if match.url_name == target:
        return "is-active"

    try:
        target_path = reverse(url_name, args=args, kwargs=kwargs)
    except Exception:  # pragma: no cover - defensive
        return ""

    if request.path == target_path:
        return "is-active"

    return ""


@register.filter
def currency(amount: Any, code: str = "USD") -> str:
    """
    Format a number as currency with the supplied ISO code.

    Falls back to the current locale's decimal separator when possible.
    """

    if amount is None:
        return ""

    value = amount
    if not isinstance(amount, (int, float, Decimal)):
        try:
            value = Decimal(str(amount))
        except Exception:  # pragma: no cover - defensive
            return str(amount)

    locale = translation.get_language()
    formatted = f"{value:,.2f}"
    if locale and locale.startswith("fr"):
        formatted = formatted.replace(",", " ").replace(".", ",")

    return f"{formatted} {code}"


@register.simple_tag
def gradient_text(text: str) -> str:
    """
    Wrap the provided text with a gradient span utility class.
    """

    return f'<span class="text-gradient">{text}</span>'


@register.filter(name="sub")
def subtract(value: Any, arg: Any) -> Any:
    """
    Subtract ``arg`` from ``value`` in templates.

    Example::
        {{ 10|sub:3 }}  -> 7
    """

    try:
        return float(value) - float(arg)
    except (TypeError, ValueError):
        try:
            return Decimal(str(value)) - Decimal(str(arg))
        except Exception:
            return value


@register.filter(name="add_class")
def add_class(field, css: str):
    """
    Add CSS classes to a bound field widget without mutating the original widget.
    """

    if not hasattr(field, "as_widget"):
        return field

    attrs = field.field.widget.attrs.copy()
    existing = attrs.get("class", "")
    combined = f"{existing} {css}".strip() if existing else css
    attrs["class"] = combined
    return field.as_widget(attrs=attrs)


@register.filter(name="attr")
def set_attr(field, arg: str):
    """
    Update arbitrary attributes on a bound field widget using a comma-separated list.

    Example::
        {{ field|attr:"aria-invalid:true,data-foo:bar" }}
    """

    if not hasattr(field, "as_widget"):
        return field

    attrs = field.field.widget.attrs.copy()
    pairs = [item.strip() for item in arg.split(",") if item.strip()]
    for pair in pairs:
        if ":" not in pair:
            continue
        key, value = pair.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "class":
            existing = attrs.get("class", "")
            combined = f"{existing} {value}".strip() if existing else value
            attrs["class"] = combined
        else:
            attrs[key] = value

    return field.as_widget(attrs=attrs)