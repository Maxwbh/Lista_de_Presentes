"""
Lista de Presentes de Natal
============================

Aplicacao web Django para gerenciar listas de presentes de Natal em familia.

Autor: Maxwell da Silva Oliveira
Empresa: M&S do Brasil LTDA
Email: maxwbh@gmail.com
LinkedIn: linkedin.com/in/maxwbh
GitHub: @Maxwbh
"""

import os
from pathlib import Path

# Versao do projeto
__version__ = '1.0.2'
__author__ = 'Maxwell da Silva Oliveira'
__email__ = 'maxwbh@gmail.com'
__company__ = 'M&S do Brasil LTDA'
__license__ = 'MIT'

# Ler versao do arquivo VERSION se existir
VERSION_FILE = Path(__file__).parent.parent / 'VERSION'
if VERSION_FILE.exists():
    with open(VERSION_FILE, 'r', encoding='utf-8') as f:
        __version__ = f.read().strip()
