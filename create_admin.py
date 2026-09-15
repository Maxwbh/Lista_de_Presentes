#!/usr/bin/env python
"""
Script para criar superusuário admin no Render.com

Uso:
    python create_admin.py

Ou via shell do Django:
    python manage.py shell < create_admin.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lista_presentes.settings')
django.setup()

from presentes.models import Usuario

# Dados do superusuário
EMAIL = 'maxwbh@gmail.com'
USERNAME = 'maxwbh'
PASSWORD = 'a'

def create_admin():
    """Criar superusuário se não existir"""

    # Verificar se já existe
    if Usuario.objects.filter(email=EMAIL).exists():
        print(f"⚠️  Usuário com email {EMAIL} já existe!")
        user = Usuario.objects.get(email=EMAIL)
        print(f"✅ Usuário: {user.username}")
        print(f"✅ Email: {user.email}")
        print(f"📊 Superuser ANTES: {user.is_superuser}")
        print(f"📊 Staff ANTES: {user.is_staff}")

        # Atualizar senha E permissões
        user.set_password(PASSWORD)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()

        print(f"🔄 Senha atualizada!")
        print(f"👑 Superuser DEPOIS: {user.is_superuser}")
        print(f"👔 Staff DEPOIS: {user.is_staff}")
        print(f"✅ Permissões de admin concedidas!")
        return user

    # Criar novo superusuário
    print(f"📝 Criando superusuário...")
    user = Usuario.objects.create_superuser(
        email=EMAIL,
        username=USERNAME,
        password=PASSWORD,
        first_name='Max',
        last_name='WBH'
    )

    print(f"✅ Superusuário criado com sucesso!")
    print(f"")
    print(f"👤 Username: {user.username}")
    print(f"📧 Email: {user.email}")
    print(f"🔑 Senha: {PASSWORD}")
    print(f"👑 Superuser: {user.is_superuser}")
    print(f"👔 Staff: {user.is_staff}")
    print(f"")
    print(f"🌐 Acesse: https://lista-presentes-im4b.onrender.com/admin/")
    print(f"")

    return user

if __name__ == '__main__':
    try:
        create_admin()
        print("✅ Concluído!")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
