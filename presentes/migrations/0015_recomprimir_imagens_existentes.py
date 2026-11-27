"""
Reduz uma vez as imagens que ja estavam no banco (no maximo 800 px, WebP).

Roda no deploy, junto com o migrate do build.sh, porque o Render Free nao tem
console para rodar o comando recomprimir_imagens a mao. Le uma linha por vez
e so grava quando a imagem fica menor; o que nao for imagem aceita fica como
esta. Desfazer a migracao nao restaura as imagens originais.
"""
from django.db import migrations


def recomprimir(apps, schema_editor):
    try:
        from presentes.imagens import recomprimir_registros
    except ImportError:  # codigo reorganizado no futuro: nada a fazer
        return
    alvos = (
        (apps.get_model('presentes', 'Presente'), 'imagem_base64', 'imagem_tipo', 'imagem_versao', 'imagem_nome'),
        (apps.get_model('presentes', 'Grupo'), 'imagem_base64', 'imagem_tipo', 'imagem_versao', 'imagem_nome'),
        (apps.get_model('presentes', 'Usuario'), 'foto_base64', 'foto_tipo', 'foto_versao', None),
    )
    linhas = []
    totais = recomprimir_registros(alvos, escrever=linhas.append)
    if totais['antes'] or totais['mantidas']:  # banco vazio (ex.: testes): sem log
        for linha in linhas:
            print(f'    {linha}')
        print(f"    Imagens reduzidas: {totais['alteradas']} "
              f"({totais['antes'] // 1024} KB -> {totais['depois'] // 1024} KB)")


class Migration(migrations.Migration):

    dependencies = [
        ('presentes', '0014_imagens_fora_das_consultas'),
    ]

    operations = [
        migrations.RunPython(recomprimir, migrations.RunPython.noop),
    ]
