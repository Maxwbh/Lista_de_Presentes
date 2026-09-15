from django.apps import AppConfig
from django.conf import settings
from django.db.backends.signals import connection_created


def _forcar_search_path(sender, connection, **kwargs):
    """
    Garante que TODA conexão PostgreSQL use apenas o schema lista_presentes.

    Necessário porque poolers em modo transação (PgBouncer/Supabase pooler)
    ignoram as startup options da connection string. Sem isso, tabelas
    poderiam ser criadas no schema public.

    Em teste também cria o schema: o banco de teste é criado do zero pelo
    Django, sem o schema, e a primeira coisa que ele faz é criar a tabela
    django_migrations — que falharia com "no schema has been selected".
    """
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            if getattr(settings, 'TESTING', False):
                cursor.execute('CREATE SCHEMA IF NOT EXISTS lista_presentes')
            cursor.execute('SET search_path TO lista_presentes')


class PresentesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'presentes'

    def ready(self):
        connection_created.connect(_forcar_search_path)
