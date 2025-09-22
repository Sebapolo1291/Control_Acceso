from django import template
import base64

register = template.Library()

@register.filter
def b64encode(value):
    """
    Codifica un valor binario en base64 para mostrarlo en una plantilla
    """
    if value is None:
        return ''
    return base64.b64encode(value).decode('utf-8')