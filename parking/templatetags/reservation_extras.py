from django import template

register = template.Library()


@register.filter
def get_index(sequence, index):
    try:
        idx = int(index) - 1
        if idx < 0:
            idx = 0
        return sequence[idx % len(sequence)]
    except Exception:
        return {}

