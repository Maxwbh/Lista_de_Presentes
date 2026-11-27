from django import template
from django.utils.html import format_html

from ..rede import TIPOS_IMAGEM_PERMITIDOS

register = template.Library()

AVATAR_MAP = {
    'avatar-1': '👩', 'avatar-2': '👨', 'avatar-3': '👩‍🦰', 'avatar-4': '👨‍🦱',
    'avatar-5': '👩‍🦳', 'avatar-6': '👨‍🦳', 'avatar-7': '🧑', 'avatar-8': '👧',
    'avatar-9': '👦', 'avatar-10': '🧔', 'avatar-11': '👩‍🦲', 'avatar-12': '🧑‍🦱',
    'avatar-13': '👴', 'avatar-14': '👵', 'avatar-15': '🧑‍🎄', 'avatar-16': '🤶',
    'avatar-17': '🦸', 'avatar-18': '🦸‍♀️', 'avatar-19': '🧙', 'avatar-20': '🧝',
}


@register.filter
def avatar_emoji(avatar_id):
    """Converte avatar ID em emoji. Ex: {{ user.avatar|avatar_emoji }}"""
    return AVATAR_MAP.get(avatar_id or 'avatar-1', '👩')


@register.simple_tag
def user_avatar_html(user, size='w-8 h-8', text_size='text-lg'):
    """
    Renderiza avatar do usuario como HTML (foto ou emoji).
    Uso: {% user_avatar_html user "w-10 h-10" "text-xl" %}

    Nome, classes e tipo passam por format_html (escapados): o nome e
    digitado pelo proprio usuario e aparece para o grupo inteiro.
    """
    content_type = (getattr(user, 'foto_tipo', None) or 'image/jpeg').lower()
    if getattr(user, 'foto_base64', None) and content_type in TIPOS_IMAGEM_PERMITIDOS:
        return format_html(
            '<img src="data:{};base64,{}" alt="{}" class="{} rounded-xl object-cover">',
            content_type, user.foto_base64, user.get_full_name(), size,
        )
    emoji = AVATAR_MAP.get(getattr(user, 'avatar', '') or 'avatar-1', '👩')
    return format_html(
        '<div class="{} rounded-xl bg-base-200 flex items-center justify-center {}">{}</div>',
        size, text_size, emoji,
    )
