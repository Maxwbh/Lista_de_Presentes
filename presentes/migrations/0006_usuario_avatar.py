from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('presentes', '0005_pushsubscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='avatar',
            field=models.CharField(blank=True, default='avatar-1', help_text='ID do avatar pre-definido', max_length=50),
        ),
        migrations.AddField(
            model_name='usuario',
            name='foto_base64',
            field=models.TextField(blank=True, help_text='Foto do usuario em base64', null=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='foto_tipo',
            field=models.CharField(blank=True, help_text='MIME type da foto', max_length=50, null=True),
        ),
    ]
