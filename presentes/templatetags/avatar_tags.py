from django import template
from django.utils.safestring import mark_safe

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
    """
    if hasattr(user, 'foto_base64') and user.foto_base64:
        content_type = user.foto_tipo or 'image/jpeg'
        return mark_safe(
            f'<img src="data:{content_type};base64,{user.foto_base64}" '
            f'alt="{user.get_full_name()}" '
            f'class="{size} rounded-xl object-cover">'
        )
    emoji = AVATAR_MAP.get(getattr(user, 'avatar', '') or 'avatar-1', '👩')
    return mark_safe(
        f'<div class="{size} rounded-xl bg-base-200 flex items-center justify-center {text_size}">'
        f'{emoji}</div>'
    )
