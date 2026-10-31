"""
Conversao de precos lidos de sites, APIs e IA para numero.

Os precos chegam em formatos diferentes e o separador decimal precisa ser
identificado em cada caso:
  - formato brasileiro:      'R$ 1.371,60', '254,00', '1.371'
  - formato de maquina/EUA:  '254.00', '1371.6', '1,371.60'
  - numero:                  254, 1371.6
"""
import re
from decimal import Decimal, InvalidOperation


def converter_preco(valor):
    """
    Converte o preco para float, ou None se nao for um preco valido.

    Regra do separador decimal:
      - com ponto e virgula, o ultimo que aparece e o decimal ('1.371,60', '1,371.60');
      - so com um separador, ele e decimal quando tem 1 ou 2 digitos depois
        ('254,00', '254.0'); com 3 digitos depois, ou repetido, e de milhar
        ('1.371', '1,371', '1.371.600').
    """
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float, Decimal)):
        numero = float(valor)
        return numero if numero > 0 else None

    texto = re.sub(r'[^\d,.]', '', str(valor))
    texto = texto.strip('.,')
    if not texto or not re.search(r'\d', texto):
        return None

    if ',' in texto and '.' in texto:
        decimal = ',' if texto.rfind(',') > texto.rfind('.') else '.'
        milhar = '.' if decimal == ',' else ','
        texto = texto.replace(milhar, '').replace(decimal, '.')
    elif ',' in texto or '.' in texto:
        separador = ',' if ',' in texto else '.'
        partes = texto.split(separador)
        if len(partes) == 2 and 1 <= len(partes[1]) <= 2:
            texto = f"{partes[0]}.{partes[1]}"
        else:
            texto = ''.join(partes)

    try:
        numero = float(texto)
    except ValueError:
        return None
    return numero if numero > 0 else None


def converter_preco_decimal(valor):
    """Como converter_preco, mas em Decimal com 2 casas (para DecimalField), ou None"""
    numero = converter_preco(valor)
    if numero is None:
        return None
    try:
        return Decimal(str(numero)).quantize(Decimal('0.01'))
    except InvalidOperation:
        return None
