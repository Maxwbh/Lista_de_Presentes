from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('presentes', '0006_usuario_avatar'),
    ]

    operations = [
        migrations.CreateModel(
            name='PesquisaPrecoLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('origem', models.CharField(choices=[('automatica', 'Automática (semanal)'), ('manual', 'Manual (admin)'), ('comando', 'Comando (cron)')], default='automatica', max_length=20)),
                ('data_inicio', models.DateTimeField(auto_now_add=True)),
                ('data_fim', models.DateTimeField(blank=True, null=True)),
                ('total_presentes', models.IntegerField(default=0)),
                ('sucessos', models.IntegerField(default=0)),
                ('erros', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Pesquisa de Preços',
                'verbose_name_plural': 'Pesquisas de Preços',
                'ordering': ['-data_inicio'],
            },
        ),
        migrations.CreateModel(
            name='PrecoHistorico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preco', models.DecimalField(decimal_places=2, max_digits=10)),
                ('loja', models.CharField(blank=True, default='', max_length=200)),
                ('fonte', models.CharField(default='sistema', help_text='Origem do registro: cadastro, sugestao, aplicado, pesquisa_semanal', max_length=30)),
                ('data', models.DateTimeField(auto_now_add=True)),
                ('presente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historico_precos', to='presentes.presente')),
            ],
            options={
                'verbose_name': 'Histórico de Preço',
                'verbose_name_plural': 'Histórico de Preços',
                'ordering': ['data'],
            },
        ),
        migrations.AddIndex(
            model_name='precohistorico',
            index=models.Index(fields=['presente', 'data'], name='precohist_presente_data_idx'),
        ),
    ]
