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

@register.filter
def format_miles(value):
    try:
        from decimal import Decimal, InvalidOperation
        # Si viene como string con coma decimal
        if isinstance(value, str):
            value = value.replace(",", ".")
        # Aqui fuerzo a float por si es tipo Decimal raro de base de datos
        value = float(value)
        value = Decimal(value).quantize(Decimal('1'))  # redondeo sin decimales
        return "{:,.0f}".format(value).replace(",", ".")
    except (InvalidOperation, ValueError, TypeError):
        return value
