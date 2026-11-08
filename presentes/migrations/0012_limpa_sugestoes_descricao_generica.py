"""
Limpa as sugestoes e o historico de precos dos presentes com descricao
generica (ex.: 'Pronta Entrega!').

A busca de precos usava a descricao do presente como termo de busca. Com
'Pronta Entrega!' ela trazia produtos sem relacao (ex.: um barbeador), que
viravam sugestao, entravam no historico e deixavam o card com uma temperatura
de preco falsa. A busca nova nao procura em outras lojas com descricao
generica; esta migracao desfaz o que ja foi gravado.

Mantem os precos que vieram do cadastro e do proprio site do link.
"""
import re

from django.db import migrations

# Mesma regra de presentes.services.IAService.descricao_generica (copiada:
# migracoes nao devem depender do codigo atual do app)
CHAMADA_DE_VENDA_RE = re.compile(
    r'pronta\s+entrega|envio\s+(imediato|r[aá]pido|no\s+mesmo\s+dia)|frete\s+gr[aá]tis|aten[cç][aã]o|'
    r'promo[cç][aã]o|oferta|lan[cç]amento|produto\s+novo|novo\s+e\s+original|original|garantia|'
    r'nota\s+fiscal|estoque|leia\s+(a\s+)?descri[cç][aã]o|aproveite|imperd[ií]vel',
    re.IGNORECASE,
)
FONTES_MANTIDAS = ('cadastro', 'site')


def descricao_generica(texto):
    texto = (texto or '').strip()
    if not texto:
        return True
    return bool(CHAMADA_DE_VENDA_RE.search(texto)) and len(re.findall(r'\w+', texto)) < 6


def limpar(apps, schema_editor):
    Presente = apps.get_model('presentes', 'Presente')
    SugestaoCompra = apps.get_model('presentes', 'SugestaoCompra')
    PrecoHistorico = apps.get_model('presentes', 'PrecoHistorico')

    ids = [p.pk for p in Presente.objects.only('pk', 'descricao') if descricao_generica(p.descricao)]
    if not ids:
        return
    SugestaoCompra.objects.filter(presente_id__in=ids).delete()
    PrecoHistorico.objects.filter(presente_id__in=ids).exclude(fonte__in=FONTES_MANTIDAS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('presentes', '0011_busca_imagem'),
    ]

    operations = [
        migrations.RunPython(limpar, migrations.RunPython.noop),
    ]
