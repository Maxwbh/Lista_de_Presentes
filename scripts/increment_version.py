#!/usr/bin/env python3
"""
Script para incrementar versão automaticamente a cada commit
Atualiza os arquivos VERSION e version.py
"""
import re
import subprocess
from pathlib import Path

def get_git_commit_hash():
    """Obtém o hash curto do último commit"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return "unknown"

def read_version_file(version_txt_path):
    """Lê a versão do arquivo VERSION"""
    try:
        with open(version_txt_path, 'r', encoding='utf-8') as f:
            version = f.read().strip()
            match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version)
            if match:
                return int(match.group(1)), int(match.group(2)), int(match.group(3))
    except:
        pass
    return 1, 0, 0

def write_version_file(version_txt_path, major, minor, patch):
    """Escreve a nova versão no arquivo VERSION"""
    with open(version_txt_path, 'w', encoding='utf-8') as f:
        f.write(f"{major}.{minor}.{patch}\n")

def update_version_py(version_py_path, major, minor, patch, build, commit_hash):
    """Atualiza o arquivo version.py"""
    new_version = f"{major}.{minor}.{patch}"

    # Ler arquivo atual se existir
    if version_py_path.exists():
        with open(version_py_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Atualizar valores
        content = re.sub(
            r'__version__\s*=\s*["\'][^"\']*["\']',
            f'__version__ = "{new_version}"',
            content
        )
        content = re.sub(
            r'__build__\s*=\s*\d+',
            f'__build__ = {build}',
            content
        )
        content = re.sub(
            r'__commit__\s*=\s*["\'][^"\']*["\']',
            f'__commit__ = "{commit_hash}"',
            content
        )
    else:
        # Criar novo arquivo
        content = f'''"""
Sistema de Versionamento Automático
Este arquivo é atualizado automaticamente a cada commit
"""

__version__ = "{new_version}"
__build__ = {build}
__commit__ = "{commit_hash}"
'''

    with open(version_py_path, 'w', encoding='utf-8') as f:
        f.write(content)

def increment_build(version_py_path):
    """Lê o build atual do version.py"""
    if version_py_path.exists():
        with open(version_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        build_match = re.search(r'__build__\s*=\s*(\d+)', content)
        if build_match:
            return int(build_match.group(1)) + 1
    return 1

def main():
    # Caminhos dos arquivos
    project_root = Path(__file__).parent.parent
    version_txt = project_root / 'VERSION'
    version_py = project_root / 'version.py'

    # Ler versão atual do arquivo VERSION
    major, minor, patch = read_version_file(version_txt)

    # Incrementar patch
    patch += 1

    # Incrementar build
    build = increment_build(version_py)

    # Obter hash do commit
    commit_hash = get_git_commit_hash()

    # Atualizar arquivo VERSION
    write_version_file(version_txt, major, minor, patch)
    print(f"✓ VERSION atualizado: {major}.{minor}.{patch}")

    # Atualizar arquivo version.py
    update_version_py(version_py, major, minor, patch, build, commit_hash)
    print(f"✓ version.py atualizado: {major}.{minor}.{patch} (build {build}, commit {commit_hash})")

    # Adicionar arquivos ao git
    try:
        subprocess.run(['git', 'add', str(version_txt)], check=True)
        subprocess.run(['git', 'add', str(version_py)], check=True)
        print(f"✓ Arquivos adicionados ao commit")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro ao adicionar arquivos ao git: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
