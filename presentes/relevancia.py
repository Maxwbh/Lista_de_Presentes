"""
Verificacao de relevancia entre o presente e o resultado de uma busca de preco.

Os buscadores de preco (Zoom, Buscape) devolvem o que a pagina de resultados
mostrar - inclusive carrosseis de recomendacao e produtos sem nenhuma relacao
com o que foi pesquisado. Sem conferir o titulo do resultado, um "Mata Formigas
Formicel de R$ 28" acaba com a melhor oferta apontando para um serum facial de
R$ 219, e esse preco ainda entra no historico e estoura a temperatura do card.

Este modulo compara a descricao do presente com o titulo do resultado e diz se
sao o mesmo produto.
"""
import re
import unicodedata

# Fracao minima de palavras em comum para aceitar um resultado.
RELEVANCIA_MINIMA = 0.5

# Minimo de palavras em comum quando os dois lados tem vocabulario suficiente.
# Evita que uma unica palavra generica ("kit", "gel") valide o resultado.
MINIMO_PALAVRAS_EM_COMUM = 2

# Palavras que nao ajudam a distinguir um produto de outro.
PALAVRAS_IGNORADAS = {
    # conectivos e artigos
    'de', 'da', 'do', 'das', 'dos', 'com', 'sem', 'para', 'por', 'em', 'no',
    'na', 'nos', 'nas', 'ao', 'aos', 'um', 'uma', 'uns', 'umas', 'the', 'and',
    # embalagem e quantidade
    'kit', 'unidade', 'unidades', 'und', 'pct', 'pacote', 'caixa', 'cx',
    'pecas', 'peca', 'pcs', 'par', 'conjunto', 'combo', 'novo', 'nova',
    'original', 'oficial', 'promocao', 'frete', 'gratis',
    # unidades de medida
    'ml', 'litro', 'litros', 'lt', 'kg', 'gr', 'gramas', 'grama', 'mg',
    'cm', 'mm', 'metros', 'metro', 'polegadas', 'pol', 'w', 'v',
}


# Palavras que denunciam um acessorio, e nao o produto em si. Um resultado que
# traz uma delas sem que o presente peca aquilo e quase sempre "pulseira para
# Huawei Watch" no lugar do relogio - e, por ser mais barato, o acessorio ainda
# venceria a ordenacao por menor preco.
PALAVRAS_DE_ACESSORIO = {
    'pulseira', 'correia', 'capa', 'capinha', 'case', 'pelicula', 'protetor',
    'suporte', 'carregador', 'cabo', 'adaptador', 'refil', 'estojo', 'bolsa',
    'base', 'skin', 'adesivo', 'grip', 'dock',
}


def normalizar(texto):
    """Minusculas, sem acento e sem pontuacao."""
    if not texto:
        return ''
    texto = unicodedata.normalize('NFKD', str(texto))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower()
    return re.sub(r'[^a-z0-9]+', ' ', texto).strip()


def palavras_significativas(texto):
    """
    Palavras que realmente identificam o produto.

    Descarta as palavras da lista de ignoradas, as muito curtas e os numeros
    soltos - "10g" e "2 unidades" nao distinguem nada sozinhos, e um numero
    igual por coincidencia nao deve aproximar dois produtos diferentes.
    """
    palavras = set()
    for palavra in normalizar(texto).split():
        if len(palavra) < 3:
            continue
        if palavra in PALAVRAS_IGNORADAS:
            continue
        if palavra.isdigit():
            continue
        # formatos tipo 10g, 30ml, 500gr
        if re.fullmatch(r'\d+(g|gr|kg|ml|l|lt|mg|cm|mm|w|v)', palavra):
            continue
        palavras.add(palavra)
    return palavras


def calcular_relevancia(descricao, titulo):
    """
    Fracao de palavras em comum, de 0 a 1.

    O denominador e o menor dos dois vocabularios: titulos de loja costumam
    trazer muito ruido a mais ("Perfume Masculino Importado Lacrado ..."), e
    dividir pelo maior puniria um resultado correto so por ser verborragico.
    """
    palavras_presente = palavras_significativas(descricao)
    palavras_resultado = palavras_significativas(titulo)
    if not palavras_presente or not palavras_resultado:
        return 0.0

    em_comum = palavras_presente & palavras_resultado
    return len(em_comum) / min(len(palavras_presente), len(palavras_resultado))


def resultado_relevante(descricao, titulo):
    """
    Diz se o resultado da busca e o mesmo produto do presente.

    Sem titulo o resultado e recusado: e exatamente o caso que deixava passar
    produto errado, porque nao havia nada para conferir.
    """
    if not titulo or not str(titulo).strip():
        return False

    palavras_presente = palavras_significativas(descricao)
    palavras_resultado = palavras_significativas(titulo)
    em_comum = palavras_presente & palavras_resultado

    if len(palavras_presente) >= MINIMO_PALAVRAS_EM_COMUM and \
            len(palavras_resultado) >= MINIMO_PALAVRAS_EM_COMUM and \
            len(em_comum) < MINIMO_PALAVRAS_EM_COMUM:
        return False

    # Acessorio do produto certo nao e o produto certo
    acessorio = (palavras_resultado & PALAVRAS_DE_ACESSORIO) - palavras_presente
    if acessorio:
        return False

    return calcular_relevancia(descricao, titulo) >= RELEVANCIA_MINIMA
