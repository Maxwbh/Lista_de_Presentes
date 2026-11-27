"""
Reducao das imagens antes de gravar no banco.

As imagens ficam em base64 no Postgres e cada leitura conta no egress do
Supabase; uma foto de celular de 5 MB vira ~7 MB de texto. Aqui toda imagem
aceita e redimensionada (no maximo 800 px no lado maior), tem a orientacao
EXIF aplicada e e regravada em WebP, mirando menos de 100 KB.
"""
import io

from .rede import TIPOS_IMAGEM

LADO_MAXIMO = 800
TAMANHO_ALVO = 100 * 1024
# Limite do arquivo recebido (a imagem gravada fica bem menor)
TAMANHO_MAXIMO_ENTRADA = 15 * 1024 * 1024
QUALIDADES = (80, 70, 60, 50)


def otimizar_imagem(dados, lado_maximo=LADO_MAXIMO, tamanho_alvo=TAMANHO_ALVO):
    """
    Devolve (bytes, mime) da imagem otimizada, ou (None, None) se o conteudo
    nao for JPEG, PNG, GIF ou WEBP. Se a imagem original ja for pequena, sem
    rotacao e menor que a versao recomprimida, ela e mantida como esta.
    """
    if not dados or len(dados) > TAMANHO_MAXIMO_ENTRADA:
        return None, None
    try:
        from PIL import Image, ImageOps
        with Image.open(io.BytesIO(dados)) as original:
            formato = original.format
            if formato not in TIPOS_IMAGEM:
                return None, None
            largura, altura = original.size
            orientacao = original.getexif().get(0x0112, 1)
            # JPEG grande: decodifica ja reduzida (menos memoria no Render Free)
            original.draft('RGB', (lado_maximo * 2, lado_maximo * 2))
            imagem = ImageOps.exif_transpose(original)
            imagem.thumbnail((lado_maximo, lado_maximo), Image.Resampling.LANCZOS)

            if imagem.mode in ('RGBA', 'LA', 'PA') or (imagem.mode == 'P' and 'transparency' in imagem.info):
                imagem = imagem.convert('RGBA')
            elif imagem.mode != 'RGB':
                imagem = imagem.convert('RGB')

            saida = b''
            for qualidade in QUALIDADES:
                buffer = io.BytesIO()
                imagem.save(buffer, format='WEBP', quality=qualidade, method=4)
                saida = buffer.getvalue()
                if len(saida) <= tamanho_alvo:
                    break
    except Exception:
        return None, None

    ja_pequena = max(largura, altura) <= lado_maximo and orientacao == 1
    if ja_pequena and len(dados) <= len(saida):
        return dados, TIPOS_IMAGEM[formato]
    return saida, 'image/webp'


def recomprimir_registros(alvos, simular=False, escrever=print):
    """
    Reduz as imagens ja gravadas. Usado pelo comando recomprimir_imagens e
    pela migracao que roda no deploy (o Render Free nao tem console).

    alvos: tuplas (modelo, coluna base64, coluna do tipo, coluna da versao,
    coluna do nome ou None). Le uma linha por vez, so a coluna da imagem, e
    so grava quando a versao nova e menor. Devolve um dicionario com os totais.
    """
    import base64
    from .models import versao_da_imagem
    from .rede import EXTENSOES

    totais = {'antes': 0, 'depois': 0, 'alteradas': 0, 'mantidas': 0}
    for modelo, campo, campo_tipo, campo_versao, campo_nome in alvos:
        com_imagem = modelo.objects.exclude(**{f'{campo}__isnull': True}).exclude(**{campo: ''})
        pks = list(com_imagem.order_by('pk').values_list('pk', flat=True))
        escrever(f'{modelo.__name__}: {len(pks)} imagem(ns)')
        colunas = [campo] + ([campo_nome] if campo_nome else [])
        for pk in pks:
            linha = modelo.objects.filter(pk=pk).values(*colunas).first()
            if not linha:
                continue
            texto = linha[campo]
            try:
                novos, tipo = otimizar_imagem(base64.b64decode(texto))
            except Exception:
                novos, tipo = None, None
            if not tipo:
                totais['mantidas'] += 1
                escrever(f'  #{pk}: não é JPEG/PNG/GIF/WEBP ({len(texto) // 1024} KB), mantido')
                continue
            novo_texto = base64.b64encode(novos).decode('ascii')
            antes, depois = len(texto), len(novo_texto)
            totais['antes'] += antes
            if depois >= antes:
                totais['depois'] += antes
                continue
            totais['depois'] += depois
            totais['alteradas'] += 1
            escrever(f'  #{pk}: {antes // 1024} KB -> {depois // 1024} KB')
            if simular:
                continue
            valores = {campo: novo_texto, campo_tipo: tipo, campo_versao: versao_da_imagem(novo_texto)}
            if campo_nome:
                nome = (linha[campo_nome] or 'imagem').rsplit('.', 1)[0][:200] or 'imagem'
                valores[campo_nome] = f'{nome}.{EXTENSOES[tipo]}'
            modelo.objects.filter(pk=pk).update(**valores)
    return totais
