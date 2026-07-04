import re

from django import template

register = template.Library()


@register.filter
def loja_limpa(nome):
    """
    Normaliza nome de loja vindo dos scrapers para exibição:
    'Via KaBuM! (Buscapé)' -> 'KaBuM!' | 'Zoom (Zoom)' -> 'Zoom'
    Também limpa registros antigos salvos antes da normalização.
    """
    nome = (nome or '').strip()
    nome = re.sub(r'^via\s+', '', nome, flags=re.IGNORECASE)
    nome = re.sub(r'\s*\([^)]*\)\s*$', '', nome).strip()
    return nome or '--'


@register.filter
def menos(a, b):
    """Subtração para valores Decimal/float em templates: {{ a|menos:b }}"""
    try:
        return (a or 0) - (b or 0)
    except TypeError:
        return ''
