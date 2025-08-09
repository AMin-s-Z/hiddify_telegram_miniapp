from django import template

register = template.Library()

@register.filter
def toman(value):
    try:
        n = int(value)
    except Exception:
        return value
    return n // 10 