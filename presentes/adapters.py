"""
Adapters do django-allauth para integrar o login social ao fluxo do app.
"""
import logging

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


class SocialAdapter(DefaultSocialAccountAdapter):
    """Comportamentos customizados para login via Google/Facebook/LinkedIn/Apple."""

    def pre_social_login(self, request, sociallogin):
        """
        Conecta a conta social a um usuário local já cadastrado com o mesmo
        e-mail, em vez de cair no fluxo de "conta já existe". O e-mail vem
        verificado pelo provedor (Google/Apple), então a associação é segura.
        """
        if sociallogin.is_existing:
            return

        email = (getattr(sociallogin.user, 'email', '') or '').strip().lower()
        if not email:
            return

        User = get_user_model()
        try:
            usuario = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return

        logger.info(f"[SOCIAL] Conectando conta {sociallogin.account.provider} ao usuário existente {email}")
        sociallogin.connect(request, usuario)

    def populate_user(self, request, sociallogin, data):
        """Garante nome e avatar padrão para usuários criados via login social."""
        user = super().populate_user(request, sociallogin, data)
        if not getattr(user, 'avatar', ''):
            user.avatar = 'avatar-1'
        return user
