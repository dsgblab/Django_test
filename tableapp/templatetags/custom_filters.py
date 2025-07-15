from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Permite acceder a un valor de un diccionario desde la plantilla"""
    return dictionary.get(key, '')

@register.filter
def get_attr(obj, attr_name):
    """Accede dinámicamente a un atributo de un objeto"""
    return getattr(obj, attr_name, None)
