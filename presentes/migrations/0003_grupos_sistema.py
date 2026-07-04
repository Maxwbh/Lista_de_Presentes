# Generated manually for groups system

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import secrets


def generate_invite_code():
    return secrets.token_urlsafe(24)


class Migration(migrations.Migration):

    dependencies = [
        ('presentes', '0002_presente_imagem_base64_presente_imagem_nome_and_more'),
    ]

    operations = [
        # Criar modelo Grupo
        migrations.CreateModel(
            name='Grupo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200)),
                ('descricao', models.TextField(blank=True, null=True)),
                ('codigo_convite', models.CharField(default=generate_invite_code, editable=False, max_length=32, unique=True)),
                ('ativo', models.BooleanField(default=True)),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('imagem_base64', models.TextField(blank=True, null=True)),
                ('imagem_nome', models.CharField(blank=True, max_length=255, null=True)),
                ('imagem_tipo', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'verbose_name': 'Grupo',
                'verbose_name_plural': 'Grupos',
                'ordering': ['-data_criacao'],
                'indexes': [
                    models.Index(fields=['ativo', '-data_criacao'], name='grupo_ativo_data_idx'),
                    models.Index(fields=['codigo_convite'], name='grupo_codigo_idx'),
                ],
            },
        ),
        # Criar modelo GrupoMembro
        migrations.CreateModel(
            name='GrupoMembro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('e_mantenedor', models.BooleanField(default=False)),
                ('data_entrada', models.DateTimeField(auto_now_add=True)),
                ('grupo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='membros', to='presentes.grupo')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grupos_membro', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Membro de Grupo',
                'verbose_name_plural': 'Membros de Grupos',
                'ordering': ['-data_entrada'],
                'unique_together': {('grupo', 'usuario')},
                'indexes': [
                    models.Index(fields=['grupo', 'usuario'], name='grupomembro_grupo_user_idx'),
                    models.Index(fields=['usuario', '-data_entrada'], name='grupomembro_user_data_idx'),
                ],
            },
        ),
        # Adicionar campo grupo_ativo ao Usuario
        migrations.AddField(
            model_name='usuario',
            name='grupo_ativo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuarios_ativos', to='presentes.grupo'),
        ),
        # Adicionar campo grupo ao Presente
        migrations.AddField(
            model_name='presente',
            name='grupo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='presentes', to='presentes.grupo'),
        ),
        # Adicionar campo grupo ao Compra
        migrations.AddField(
            model_name='compra',
            name='grupo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='compras', to='presentes.grupo'),
        ),
        # Adicionar campo grupo ao SugestaoCompra
        migrations.AddField(
            model_name='sugestaocompra',
            name='grupo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sugestoes', to='presentes.grupo'),
        ),
        # Adicionar campo grupo ao Notificacao
        migrations.AddField(
            model_name='notificacao',
            name='grupo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notificacoes', to='presentes.grupo'),
        ),
        # Atualizar índices do Presente
        migrations.AddIndex(
            model_name='presente',
            index=models.Index(fields=['grupo', 'usuario', 'status'], name='presente_grp_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='presente',
            index=models.Index(fields=['grupo', 'status', '-data_cadastro'], name='presente_grupo_status_data_idx'),
        ),
        migrations.AddIndex(
            model_name='presente',
            index=models.Index(fields=['grupo', '-data_cadastro'], name='presente_grupo_data_idx'),
        ),
        # Atualizar índices do Compra
        migrations.AddIndex(
            model_name='compra',
            index=models.Index(fields=['grupo', 'comprador', '-data_compra'], name='compra_grp_comprador_data_idx'),
        ),
        migrations.AddIndex(
            model_name='compra',
            index=models.Index(fields=['grupo', '-data_compra'], name='compra_grupo_data_idx'),
        ),
        # Atualizar índices do SugestaoCompra
        migrations.AddIndex(
            model_name='sugestaocompra',
            index=models.Index(fields=['grupo', 'presente', 'preco_sugerido'], name='sugestao_grp_pres_preco_idx'),
        ),
        migrations.AddIndex(
            model_name='sugestaocompra',
            index=models.Index(fields=['grupo', '-data_busca'], name='sugestao_grupo_data_idx'),
        ),
        # Atualizar índices do Notificacao
        migrations.AddIndex(
            model_name='notificacao',
            index=models.Index(fields=['grupo', 'usuario', 'lida', '-data_notificacao'], name='notif_grp_user_lida_data_idx'),
        ),
        migrations.AddIndex(
            model_name='notificacao',
            index=models.Index(fields=['grupo', 'lida', '-data_notificacao'], name='notif_grupo_lida_data_idx'),
        ),
    ]
