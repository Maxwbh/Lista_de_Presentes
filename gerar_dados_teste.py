#!/usr/bin/env python
"""
Script para gerar dados de teste no Render.
Copie e cole este código inteiro no Shell do Render (https://dashboard.render.com)

IMPORTANTE: Execute este script apenas uma vez!
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lista_presentes.settings')
django.setup()

from django.core.management import call_command

print("=" * 60)
print("GERANDO DADOS DE TESTE")
print("=" * 60)
print("\nCriando 4 usuários com 4 presentes cada...")
print("Aguarde...\n")

# Executar comando
call_command('populate_test_data', users=4, gifts_per_user=4)

print("\n" + "=" * 60)
print("CONCLUÍDO!")
print("=" * 60)

# Verificar dados criados
from presentes.models import Usuario, Presente

print(f"\n📊 ESTATÍSTICAS:")
print(f"   Total de usuários: {Usuario.objects.count()}")
print(f"   Total de presentes: {Presente.objects.count()}")
print(f"   Presentes ativos: {Presente.objects.filter(status='ATIVO').count()}")
print(f"   Presentes comprados: {Presente.objects.filter(status='COMPRADO').count()}")

print(f"\n👥 USUÁRIOS CRIADOS (senha: senha123):")
usuarios = Usuario.objects.all().order_by('-id')[:4]
for u in usuarios:
    qtd_presentes = Presente.objects.filter(usuario=u).count()
    print(f"   ✓ {u.first_name} {u.last_name} - {u.email} ({qtd_presentes} presentes)")

print("\n" + "=" * 60)
