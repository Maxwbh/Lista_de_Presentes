#!/usr/bin/env python3
"""
Script para gerar ícones PWA básicos para o projeto Lista de Presentes.
Cria ícones SVG simples que funcionam perfeitamente como PWA icons.
"""

import os
from pathlib import Path

# Definir diretório
BASE_DIR = Path(__file__).resolve().parent
ICONS_DIR = BASE_DIR / 'static' / 'icons'

# Criar diretório se não existir
ICONS_DIR.mkdir(parents=True, exist_ok=True)

# SVG template com ícone de presente
SVG_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">
  <!-- Background -->
  <rect width="{size}" height="{size}" fill="#667eea"/>

  <!-- Gift box -->
  <g transform="translate({center}, {center})">
    <!-- Box body -->
    <rect x="-{box_half}" y="-{box_quarter}" width="{box}" height="{box_half}" fill="#ffffff" rx="8"/>

    <!-- Box lid -->
    <rect x="-{box_half}" y="-{box_half}" width="{box}" height="{box_quarter}" fill="#f5f5f5" rx="8"/>

    <!-- Ribbon vertical -->
    <rect x="-{ribbon_half}" y="-{box_half}" width="{ribbon}" height="{box}" fill="#764ba2" rx="4"/>

    <!-- Ribbon horizontal -->
    <rect x="-{box_half}" y="-{ribbon_half}" width="{box}" height="{ribbon}" fill="#764ba2" rx="4"/>

    <!-- Bow -->
    <circle cx="-{bow_offset}" cy="-{box_half}" r="{bow_radius}" fill="#f093fb"/>
    <circle cx="{bow_offset}" cy="-{box_half}" r="{bow_radius}" fill="#f093fb"/>
    <circle cx="0" cy="-{box_half}" r="{bow_center}" fill="#f5576c"/>
  </g>

  <!-- Text (optional for larger icons) -->
  {text}
</svg>"""

def generate_icon(size, filename):
    """Gera um ícone SVG com o tamanho especificado."""

    # Calcular proporções
    center = size // 2
    box = int(size * 0.5)
    box_half = box // 2
    box_quarter = box // 4
    ribbon = box // 6
    ribbon_half = ribbon // 2
    bow_radius = box // 8
    bow_center = box // 10
    bow_offset = box // 6

    # Adicionar texto apenas para ícones maiores
    text = ""
    if size >= 512:
        font_size = size // 10
        text = f'<text x="{center}" y="{size - font_size}" text-anchor="middle" font-family="Arial, sans-serif" font-size="{font_size}" font-weight="bold" fill="#ffffff">LISTA</text>'

    # Gerar SVG
    svg_content = SVG_TEMPLATE.format(
        size=size,
        center=center,
        box=box,
        box_half=box_half,
        box_quarter=box_quarter,
        box_half_total=box_half,
        ribbon=ribbon,
        ribbon_half=ribbon_half,
        bow_radius=bow_radius,
        bow_center=bow_center,
        bow_offset=bow_offset,
        text=text
    )

    # Salvar arquivo
    filepath = ICONS_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    print(f"✅ Criado: {filepath}")

def main():
    """Gera todos os ícones necessários."""
    print("🎨 Gerando ícones PWA...")
    print(f"📁 Diretório: {ICONS_DIR}")
    print()

    # Criar ícones em diferentes tamanhos
    icons = [
        (192, 'icon-192x192.svg'),
        (512, 'icon-512x512.svg'),
        (72, 'icon-72x72.svg'),      # Android
        (96, 'icon-96x96.svg'),      # Android
        (128, 'icon-128x128.svg'),   # Android
        (144, 'icon-144x144.svg'),   # Android
        (152, 'icon-152x152.svg'),   # iOS
        (180, 'icon-180x180.svg'),   # iOS
        (384, 'icon-384x384.svg'),   # Adicional
    ]

    for size, filename in icons:
        generate_icon(size, filename)

    print()
    print("✨ Todos os ícones foram gerados com sucesso!")
    print()
    print("📝 Próximos passos:")
    print("1. Os ícones SVG funcionam perfeitamente para PWA")
    print("2. Se quiser converter para PNG, use:")
    print("   - Online: https://cloudconvert.com/svg-to-png")
    print("   - Ou instale: pip install cairosvg")
    print("   - E rode: python convert_svg_to_png.py")
    print()
    print("3. Atualize settings.py se necessário (já está configurado)")
    print()
    print("🎉 Pronto para usar!")

if __name__ == '__main__':
    main()
