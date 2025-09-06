from django import template

register = template.Library()

@register.filter
def cents_to_reais(value):
    """Converte centavos para reais (R$ X,XX)"""
    if value is None:
        return "0,00"
    return f"{value / 100:.2f}".replace('.', ',')

@register.filter
def cents_to_reais_with_sign(value):
    """Converte centavos para reais com sinal (+/-)"""
    if value is None:
        return "0,00"
    if value > 0:
        return f"+{value / 100:.2f}".replace('.', ',')
    else:
        return f"{value / 100:.2f}".replace('.', ',')
